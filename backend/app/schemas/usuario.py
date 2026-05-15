from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.usuario import RolUsuario


class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: RolUsuario = RolUsuario.visor


class UsuarioUpdate(BaseModel):
    """Actualiza un usuario existente.

    password es opcional: si se omite o es None, se conserva el actual.
    activo es opcional: permite reactivar (true) o desactivar (false) sin
    pasar por el flujo DELETE con TOTP. Por seguridad, un admin no puede
    desactivarse a si mismo via este endpoint (validacion en el route).
    La validacion de longitud minima se hace en el route handler para
    distinguir 'no enviado' de 'enviado vacio'.
    """
    nombre: str
    email: EmailStr
    rol: RolUsuario
    password: Optional[str] = None
    activo: Optional[bool] = None


class AvatarUpdate(BaseModel):
    """Actualiza la foto de perfil del usuario autenticado.

    avatar_b64 debe ser un data URL completo: data:image/<tipo>;base64,...
    El frontend redimensiona la imagen a max 256x256 con Canvas antes de
    enviarla, por lo que el string resultante ocupa aprox. 30-80 KB.
    El backend rechaza strings que superen 3 MB (~2 MB de imagen original).
    """
    avatar_b64: str


class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    rol: RolUsuario
    totp_habilitado: bool = False
    activo: bool = True
    avatar_b64: Optional[str] = None

    class Config:
        from_attributes = True


class CambiarPassword(BaseModel):
    """Schema para cambiar la contrasena del usuario autenticado.
    Pydantic valida min_length=8 antes de que el endpoint se ejecute.
    """
    password_actual: str
    password_nueva: str = Field(min_length=8, description="Minimo 8 caracteres")
