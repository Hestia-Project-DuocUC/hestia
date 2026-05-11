from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
import pyotp
import qrcode
import io
import base64

from app.database import get_db
from app.models.usuario import Usuario
from app.utils.security import (
    verificar_password, crear_token, crear_pre_token, verificar_token
)
from app.utils.deps import get_usuario_actual

router = APIRouter(prefix="/auth", tags=["Autenticacion"])


# ---------------------------------------------------------------------------
# Modelos de request / response
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


class Completar2FARequest(BaseModel):
    pre_token: str
    codigo: str


class CodigoTOTPRequest(BaseModel):
    codigo: str


# ---------------------------------------------------------------------------
# Helper interno
# ---------------------------------------------------------------------------

def _generar_qr_base64(uri: str) -> str:
    """Convierte una URI otpauth:// en PNG codificado en base64."""
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Paso 1 del login.
    Sin 2FA: devuelve JWT completo.
    Con 2FA: devuelve pre_token + requires_2fa=True para continuar en /2fa/completar-login.
    """
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()

    if not usuario or not verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contrasena incorrectos"
        )

    if usuario.totp_habilitado:
        pre_token = crear_pre_token({"sub": str(usuario.id)})
        return LoginResponse(requires_2fa=True, pre_token=pre_token)

    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return LoginResponse(
        requires_2fa=False,
        access_token=token,
        usuario=usuario.nombre,
        rol=usuario.rol.value
    )


@router.post("/2fa/completar-login", response_model=LoginResponse)
def completar_login_2fa(datos: Completar2FARequest, db: Session = Depends(get_db)):
    """Paso 2 del login con 2FA. Recibe pre_token + codigo TOTP, devuelve JWT completo."""
    payload = verificar_token(datos.pre_token)
    if payload is None or payload.get("tipo") != "pre_auth":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="pre_token invalido o expirado"
        )

    usuario = db.query(Usuario).filter(Usuario.id == int(payload["sub"])).first()
    if not usuario or not usuario.totp_habilitado or not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o configuracion 2FA no valida"
        )

    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo 2FA incorrecto"
        )

    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol.value})
    return LoginResponse(
        requires_2fa=False,
        access_token=token,
        usuario=usuario.nombre,
        rol=usuario.rol.value
    )


# ---------------------------------------------------------------------------
# Gestion del 2FA
# ---------------------------------------------------------------------------

@router.post("/2fa/setup", response_model=Setup2FAResponse)
def setup_2fa(
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    """Genera el secreto TOTP y devuelve el QR. El 2FA no queda activo hasta /2fa/activar."""
    if not usuario.totp_secret:
        usuario.totp_secret = pyotp.random_base32()
        db.commit()

    totp = pyotp.TOTP(usuario.totp_secret)
    uri = totp.provisioning_uri(name=usuario.email, issuer_name="Hestia")
    return Setup2FAResponse(qr_code=_generar_qr_base64(uri), secret=usuario.totp_secret)


@router.post("/2fa/activar")
def activar_2fa(
    datos: CodigoTOTPRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    """Confirma el escaneo del QR con un codigo valido y activa el 2FA."""
    if usuario.totp_habilitado:
        raise HTTPException(status_code=400, detail="El 2FA ya esta habilitado")
    if not usuario.totp_secret:
        raise HTTPException(
            status_code=400,
            detail="Primero llama a /auth/2fa/setup para generar el QR"
        )

    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo incorrecto. Asegurate de haber escaneado el QR."
        )

    usuario.totp_habilitado = True
    db.commit()
    return {"mensaje": "2FA activado. Guarda tu clave de respaldo en un lugar seguro."}


@router.post("/2fa/desactivar")
def desactivar_2fa(
    datos: CodigoTOTPRequest,
    usuario: Usuario = Depends(get_usuario_actual),
    db: Session = Depends(get_db)
):
    """Desactiva el 2FA. Requiere un codigo TOTP valido como confirmacion."""
    if not usuario.totp_habilitado:
        raise HTTPException(status_code=400, detail="El 2FA no esta habilitado")

    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo incorrecto"
        )

    usuario.totp_habilitado = False
    usuario.totp_secret = None
    db.commit()
    return {"mensaje": "2FA desactivado correctamente"}
