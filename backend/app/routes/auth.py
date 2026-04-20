from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.utils.security import verificar_password, crear_token
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["Autenticación"])

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: str
    rol: str

@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    usuario = db.query(Usuario).filter(
        Usuario.email == form_data.username
    ).first()

    if not usuario or not verificar_password(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )

    token = crear_token({"sub": str(usuario.id), "rol": usuario.rol})

    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": usuario.nombre,
        "rol": usuario.rol
    }