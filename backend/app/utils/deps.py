from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.utils.security import verificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_usuario_actual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:
    excepcion = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"}
    )
    payload = verificar_token(token)
    if payload is None:
        raise excepcion
    usuario_id = payload.get("sub")
    if usuario_id is None:
        raise excepcion
    usuario = db.query(Usuario).filter(Usuario.id == int(usuario_id)).first()
    if usuario is None:
        raise excepcion
    return usuario

def require_admin(usuario: Usuario = Depends(get_usuario_actual)) -> Usuario:
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para esta acción"
        )
    return usuario