from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
import json

from app.database import get_db
from app.models.usuario import Usuario
from app.utils.security import (
    verificar_password, crear_token, crear_pre_token, verificar_token
)
from app.utils.deps import get_usuario_actual, oauth2_scheme
from app.utils.rate_limit import verificar_limite, registrar_fallo, limpiar, intentos_restantes
from app.utils.auditoria import registrar, get_ip
from app.utils.token_blacklist import revocar

router = APIRouter(prefix="/auth", tags=["Autenticacion"])

TOTP_VALID_WINDOW = 1
NUM_RECOVERY_CODES = 10

CUENTA_INACTIVA_DETALLE = "Cuenta inactiva. Contacta al administrador."


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------

class LoginResponse(BaseModel):
    requires_2fa: bool = False
    access_token: Optional[str] = None
    token_type: str = "bearer"
    usuario: Optional[str] = None
    rol: Optional[str] = None
    pre_token: Optional[str] = None


class Setup2FAResponse(BaseModel):
    qr_code: str
    secret: str


class ActivarResponse(BaseModel):
    mensaje: str
    recovery_codes: list[str]


class Completar2FARequest(BaseModel):
    pre_token: str
    codigo: str


class RecuperoRequest(BaseModel):
    pre_token: str
    recovery_code: str


class CodigoTOTPRequest(BaseModel):
    codigo: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _generar_qr_base64(uri: str) -> str:
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def _generar_recovery_codes() -> tuple[list[str], str]:
    """Genera NUM_RECOVERY_CODES codigos aleatorios.
    Devuelve (lista_plana, json_con_hashes).
    Los codigos planos se muestran al usuario UNA sola vez.
    """
    codigos: list[str] = []
    registros: list[dict] = []
    for _ in range(NUM_RECOVERY_CODES):
        parte1 = secrets.token_hex(4).upper()
        parte2 = secrets.token_hex(4).upper()
        codigo = f"{parte1}-{parte2}"
        hash_hex = hashlib.sha256(codigo.encode()).hexdigest()
        codigos.append(codigo)
        registros.append({"hash": hash_hex, "usado": False})
    return codigos, json.dumps(registros)


def _verificar_y_consumir_recovery_code(
    usuario: Usuario, codigo: str, db: Session
) -> bool:
    if not usuario.totp_recovery_codes:
        return False
    registros = json.loads(usuario.totp_recovery_codes)
    hash_input = hashlib.sha256(codigo.upper().encode()).hexdigest()
    for reg in registros:
        if not reg["usado"] and reg["hash"] == hash_input:
            reg["usado"] = True
            usuario.totp_recovery_codes = json.dumps(registros)
            db.commit()
            return True
    return False


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Paso 1 del login con rate limiting y audit log.

    Flujo:
    1. verificar_limite() antes de tocar la BD (no revela si el email existe).
    2. Credenciales incorrectas -> registrar_fallo() + audit LOGIN_FALLIDO.
    3. Cuenta inactiva (soft-deleted) -> 403 + audit LOGIN_BLOQUEADO_INACTIVO.
    4. Exito -> limpiar() + audit LOGIN_EXITOSO.
    Sin 2FA: devuelve JWT completo.
    Con 2FA: devuelve pre_token de vida corta.
    """
    verificar_limite(form_data.username)

    usuario = db.query(Usuario).filter(
        Usuario.email == form_data.username
    ).first()

    if not usuario or not verificar_password(
        form_data.password, usuario.password_hash
    ):
        registrar_fallo(form_data.username)
        restantes = intentos_restantes(form_data.username)
        registrar(
            db, "LOGIN_FALLIDO",
            usuario=usuario,
            detalle=form_data.username,
            ip=get_ip(request),
        )
        if restantes > 0:
            s = 's' if restantes != 1 else ''
            n = 'n' if restantes != 1 else ''
            detail = (
                f"Email o contrasena incorrectos. "
                f"Te queda{n} {restantes} intento{s} antes del bloqueo."
            )
        else:
            detail = "Email o contrasena incorrectos."
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )

    # Credenciales validas pero la cuenta esta desactivada (soft-deleted).
    # Se chequea DESPUES del password para no revelar existencia de cuentas.
    if not usuario.activo:
        registrar(
            db, "LOGIN_BLOQUEADO_INACTIVO",
            usuario=usuario,
            detalle=usuario.email,
            ip=get_ip(request),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CUENTA_INACTIVA_DETALLE,
        )

    limpiar(form_data.username)
    registrar(db, "LOGIN_EXITOSO", usuario=usuario, ip=get_ip(request))

    if usuario.totp_habilitado:
        pre_token = crear_pre_token({"sub": str(usuario.id)})
        return LoginResponse(requires_2fa=True, pre_token=pre_token)

    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return LoginResponse(
        requires_2fa=False,
        access_token=token,
        usuario=usuario.nombre,
        rol=usuario.rol.value,
    )


@router.post("/logout")
def logout(
    token: str = Depends(oauth2_scheme),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Revoca el JWT activo del usuario. Efecto inmediato en todas las requests."""
    payload = verificar_token(token)
    if payload:
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti and exp:
            revocar(jti, float(exp))
    return {"mensaje": "Sesion cerrada correctamente"}


@router.post("/2fa/completar-login", response_model=LoginResponse)
def completar_login_2fa(
    datos: Completar2FARequest, db: Session = Depends(get_db)
):
    """Paso 2 con codigo TOTP. Devuelve JWT completo."""
    payload = verificar_token(datos.pre_token)
    if payload is None or payload.get("tipo") != "pre_auth":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="pre_token invalido o expirado",
        )
    usuario = db.query(Usuario).filter(
        Usuario.id == int(payload["sub"])
    ).first()
    if not usuario or not usuario.totp_habilitado or not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o configuracion 2FA no valida",
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CUENTA_INACTIVA_DETALLE,
        )
    verificar_limite(usuario.email)
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo, valid_window=TOTP_VALID_WINDOW):
        registrar_fallo(usuario.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo 2FA incorrecto",
        )
    limpiar(usuario.email)
    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return LoginResponse(
        requires_2fa=False,
        access_token=token,
        usuario=usuario.nombre,
        rol=usuario.rol.value,
    )


@router.post("/2fa/recuperar-acceso", response_model=LoginResponse)
def recuperar_acceso_2fa(
    datos: RecuperoRequest, db: Session = Depends(get_db)
):
    """Paso 2 alternativo usando un codigo de recuperacion de un solo uso."""
    payload = verificar_token(datos.pre_token)
    if payload is None or payload.get("tipo") != "pre_auth":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="pre_token invalido o expirado",
        )
    usuario = db.query(Usuario).filter(
        Usuario.id == int(payload["sub"])
    ).first()
    if not usuario or not usuario.totp_habilitado:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o configuracion 2FA no valida",
        )
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CUENTA_INACTIVA_DETALLE,
        )
    if not _verificar_y_consumir_recovery_code(usuario, datos.recovery_code, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo de recuperacion invalido o ya utilizado",
        )
    usuario.totp_habilitado = False
    usuario.totp_secret = None
    usuario.totp_recovery_codes = None
    db.commit()
    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return LoginResponse(
        requires_2fa=False,
        access_token=token,
        usuario=usuario.nombre,
        rol=usuario.rol.value,
    )


# ---------------------------------------------------------------------------
# Gestion 2FA
# ---------------------------------------------------------------------------

@router.post("/2fa/setup", response_model=Setup2FAResponse)
def setup_2fa(
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    if not usuario.totp_secret:
        usuario.totp_secret = pyotp.random_base32()
        db.commit()
    totp = pyotp.TOTP(usuario.totp_secret)
    uri = totp.provisioning_uri(name=usuario.email, issuer_name="Hestia")
    return Setup2FAResponse(
        qr_code=_generar_qr_base64(uri),
        secret=usuario.totp_secret,
    )


@router.post("/2fa/activar", response_model=ActivarResponse)
def activar_2fa(
    datos: CodigoTOTPRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    """Confirma el QR y activa 2FA. Devuelve 10 codigos de recuperacion."""
    if usuario.totp_habilitado:
        raise HTTPException(status_code=400, detail="El 2FA ya esta habilitado")
    if not usuario.totp_secret:
        raise HTTPException(status_code=400, detail="Primero llama a /auth/2fa/setup")
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo incorrecto. Asegurate de haber escaneado el QR.",
        )
    codigos_planos, json_hashes = _generar_recovery_codes()
    usuario.totp_habilitado = True
    usuario.totp_recovery_codes = json_hashes
    db.commit()
    return ActivarResponse(
        mensaje="2FA activado correctamente.",
        recovery_codes=codigos_planos,
    )


@router.post("/2fa/desactivar")
def desactivar_2fa(
    datos: CodigoTOTPRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db),
):
    if not usuario.totp_habilitado:
        raise HTTPException(status_code=400, detail="El 2FA no esta habilitado")
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo incorrecto",
        )
    usuario.totp_habilitado = False
    usuario.totp_secret = None
    usuario.totp_recovery_codes = None
    db.commit()
    return {"mensaje": "2FA desactivado correctamente"}
