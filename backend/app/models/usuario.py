from sqlalchemy import Column, Integer, String, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RolUsuario(str, enum.Enum):
    admin    = "admin"
    operador = "operador"
    visor    = "visor"
    docente  = "docente"  # Puede crear solicitudes de retiro de insumos


class Usuario(Base):
    __tablename__ = "usuarios"

    id            = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String, nullable=False)
    email         = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol           = Column(Enum(RolUsuario), default=RolUsuario.visor)

    # Soft-delete: una cuenta inactiva no puede iniciar sesion, pero su fila
    # se conserva para no romper la trazabilidad de movimientos historicos
    # (movimientos.usuario_id es FK NOT NULL). Reactivable via PUT activo=true.
    activo = Column(Boolean, default=True, nullable=False, server_default="true")

    # Foto de perfil almacenada como data URL base64 (data:image/<tipo>;base64,...).
    # El frontend redimensiona a max 256x256 antes de enviar (~30-80 KB).
    avatar_b64 = Column(Text, nullable=True)

    # 2FA TOTP
    totp_secret       = Column(String, nullable=True)
    totp_habilitado   = Column(Boolean, default=False, nullable=False)

    # Codigos de recuperacion: JSON list de {"hash": str, "usado": bool}
    # Los hashes son SHA-256 de los codigos en texto plano.
    totp_recovery_codes = Column(Text, nullable=True)

    movimientos         = relationship("Movimiento",       back_populates="usuario")
    solicitudes_retiro  = relationship("SolicitudRetiro",  back_populates="docente")
