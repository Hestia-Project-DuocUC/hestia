from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario, RolUsuario
from app.utils.security import verificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    """Cualquier usuario autenticado con token de acceso completo.
    Rechaza pre_tokens del flujo 2FA para evitar acceso parcial.
    Rechaza usuarios desactivados (soft-delete): si un admin desactiva la
    cuenta mientras hay un JWT en uso, la sesion deja de ser valida en la
    siguiente request en lugar de esperar la expiracion del token."""
    excepcion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalido o expirado",
        headers={"WWW-Authenticate": "Bearer"}
    )
    payload = verificar_token(token)
    if payload is None:
        raise excepcion

    # Los pre_tokens solo sirven para /auth/2fa/completar-login.
    # Si alguien intenta usarlos para acceder a endpoints protegidos, se rechaza.
    if payload.get("tipo") == "pre_auth":
        raise excepcion

    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise excepcion

    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise excepcion
    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta inactiva. Contacta al administrador.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return usuario


def require_operador(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    """Requiere rol admin u operador. Usado en endpoints de escritura general."""
    if usuario.rol not in [RolUsuario.admin, RolUsuario.operador]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol operador o superior para esta accion"
        )
    return usuario


def require_admin(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    """Requiere rol admin. Usado en endpoints destructivos y gestion de usuarios."""
    if usuario.rol != RolUsuario.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere rol administrador para esta accion"
        )
    return usuario
