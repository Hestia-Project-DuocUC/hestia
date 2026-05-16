from sqlalchemy import (
    Column, Integer, Text, DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class EstadoSolicitud(str, enum.Enum):
    pendiente = "pendiente"        # Docente la creo, nadie la tomo aun
    en_preparacion = "en_preparacion"  # Operador la tomo y esta preparando
    completada = "completada"      # Operador despacho; stock descontado


class SolicitudRetiro(Base):
    """Solicitud de retiro de insumos creada por un docente.

    Representa la intencion de retirar uno o varios insumos para una clase
    especifica. El stock NO se descuenta al crear la solicitud — solo cuando
    el operador la marca como 'completada', momento en que se registran los
    movimientos de salida correspondientes.

    Campos de tiempo:
    - fecha_clase: datetime de inicio de la clase (requerido). Permite al
      operador ordenar solicitudes por urgencia y preparar con anticipacion.
    - fecha_creacion: timestamp automatico de cuando el docente la creo.
    - fecha_completada: timestamp de cuando el operador la marco completada.
    """
    __tablename__ = "solicitudes_retiro"

    id = Column(Integer, primary_key=True, index=True)
    docente_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    sala_id = Column(Integer, ForeignKey("salas.id"), nullable=False)
    fecha_clase = Column(DateTime(timezone=True), nullable=False)
    estado = Column(
        Enum(EstadoSolicitud),
        default=EstadoSolicitud.pendiente,
        nullable=False,
    )
    notas = Column(Text, nullable=True)           # Notas del docente
    notas_operador = Column(Text, nullable=True)  # Observaciones del operador
    fecha_creacion = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    fecha_completada = Column(DateTime(timezone=True), nullable=True)

    docente = relationship("Usuario", back_populates="solicitudes_retiro")
    sala = relationship("Sala")
    items = relationship(
        "SolicitudItem",
        back_populates="solicitud",
        cascade="all, delete-orphan",  # Los items se borran con la solicitud
    )


class SolicitudItem(Base):
    """Linea de una solicitud de retiro: un insumo y la cantidad solicitada.

    cascade="all, delete-orphan" en la relacion padre garantiza que si la
    solicitud se elimina, sus items tambien se eliminan automaticamente.
    """
    __tablename__ = "solicitudes_items"

    id = Column(Integer, primary_key=True, index=True)
    solicitud_id = Column(
        Integer, ForeignKey("solicitudes_retiro.id"), nullable=False
    )
    insumo_id = Column(Integer, ForeignKey("insumos.id"), nullable=False)
    cantidad_solicitada = Column(Integer, nullable=False)

    solicitud = relationship("SolicitudRetiro", back_populates="items")
    insumo = relationship("Insumo")
