from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
import pyotp

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import (
    UsuarioCreate, UsuarioUpdate, UsuarioResponse, CambiarPassword
)
from app.schemas.comun import PaginatedResponse
from app.utils.deps import get_usuario_actual, require_admin
from app.utils.security import hashear_password, verificar_password
from app.utils.auditoria import registrar, get_ip

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

TOTP_VALID_WINDOW = 1


@router.get("/", response_model=PaginatedResponse[UsuarioResponse])
def listar_usuarios(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    total = db.query(Usuario).count()
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "data": usuarios}


@router.get("/me", response_model=UsuarioResponse)
def perfil_propio(usuario: Usuario = Depends(get_usuario_actual)):
    return usuario


@router.post("/me/cambiar-password")
def cambiar_password(
    datos: CambiarPassword,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Permite al usuario autenticado cambiar su propia contrasena."""
    if not verificar_password(datos.password_actual, usuario.password_hash):
        raise HTTPException(status_code=400, detail="Contrasena actual incorrecta")
    usuario.password_hash = hashear_password(datos.password_nueva)
    db.commit()
    return {"mensaje": "Contrasena actualizada correctamente"}


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(
    request: Request,
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    nuevo = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    registrar(
        db, "CREAR_USUARIO", usuario=admin,
        entidad="usuario", entidad_id=nuevo.id,
        detalle=nuevo.email, ip=get_ip(request),
    )
    return nuevo


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    encontrado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return encontrado


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    request: Request,
    datos: UsuarioUpdate,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Actualiza nombre, email y rol. La contrasena solo cambia si se envia.

    Validacion de email: si cambia, verifica que no exista en otro usuario.
    Validacion de password: si se envia, debe tener minimo 8 caracteres.
    """
    encontrado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if datos.email != encontrado.email:
        colision = db.query(Usuario).filter(Usuario.email == datos.email).first()
        if colision:
            raise HTTPException(status_code=400, detail="El email ya esta registrado")

    if datos.password is not None and len(datos.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="La contrasena nueva debe tener al menos 8 caracteres",
        )

    encontrado.nombre = datos.nombre
    encontrado.email = datos.email
    encontrado.rol = datos.rol
    if datos.password:
        encontrado.password_hash = hashear_password(datos.password)

    db.commit()
    db.refresh(encontrado)
    registrar(
        db, "EDITAR_USUARIO", usuario=admin,
        entidad="usuario", entidad_id=encontrado.id,
        detalle=encontrado.email, ip=get_ip(request),
    )
    return encontrado


@router.delete("/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    request: Request,
    codigo_totp: str = Header(alias="x-totp-code"),
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Requiere rol admin + codigo TOTP valido (header x-totp-code)."""
    if not admin.totp_habilitado or not admin.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes tener el 2FA activado para eliminar usuarios."
        )
    totp = pyotp.TOTP(admin.totp_secret)
    if not totp.verify(codigo_totp, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codigo 2FA incorrecto. El usuario no fue eliminado."
        )
    encontrado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if encontrado.id == admin.id:
        raise HTTPException(
            status_code=400, detail="No puedes eliminarte a ti mismo"
        )
    email_eliminado = encontrado.email
    db.delete(encontrado)
    db.commit()
    registrar(
        db, "ELIMINAR_USUARIO", usuario=admin,
        entidad="usuario",
        detalle=email_eliminado, ip=get_ip(request),
    )
    return {"mensaje": "Usuario eliminado"}


@router.post("/{usuario_id}/reset-2fa")
def reset_2fa_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin),
):
    """Desactiva el 2FA de cualquier usuario. Solo administradores."""
    target = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target.totp_habilitado = False
    target.totp_secret = None
    target.totp_recovery_codes = None
    db.commit()
    registrar(
        db, "RESET_2FA_USUARIO", usuario=admin,
        entidad="usuario", entidad_id=target.id,
        detalle=target.email, ip=get_ip(request),
    )
    return {"mensaje": f"2FA desactivado para {target.email}"}
