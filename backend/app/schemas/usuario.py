from pydantic import BaseModel, EmailStr, Field
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
    totp_habilitado: bool = False  # expone estado 2FA (nunca el secret)

    class Config:
        from_attributes = True


class CambiarPassword(BaseModel):
    """Schema para cambiar la contraseña del usuario autenticado.
    Pydantic valida min_length=8 antes de que el endpoint siquiera se ejecute.
    """
    password_actual: str
    password_nueva: str = Field(min_length=8, description="Mínimo 8 caracteres")
