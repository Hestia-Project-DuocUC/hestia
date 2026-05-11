from sqlalchemy import Column, Integer, String, Enum, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RolUsuario(str, enum.Enum):
    admin = "admin"
    operador = "operador"
    visor = "visor"


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol = Column(Enum(RolUsuario), default=RolUsuario.visor)

    # 2FA (TOTP compatible con Google Authenticator)
    totp_secret = Column(String, nullable=True)        # secreto compartido, se guarda cifrado en DB
    totp_habilitado = Column(Boolean, default=False, nullable=False)

    movimientos = relationship("Movimiento", back_populates="usuario")
