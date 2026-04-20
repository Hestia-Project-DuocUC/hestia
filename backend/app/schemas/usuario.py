from pydantic import BaseModel, EmailStr
from app.models.usuario import RolUsuario

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolUsuario = RolUsuario.visor

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: RolUsuario

    class Config:
        from_attributes = True