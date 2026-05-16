from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.solicitud import EstadoSolicitud


# ---------------------------------------------------------------------------
# Items
# ---------------------------------------------------------------------------

class SolicitudItemCreate(BaseModel):
    insumo_id: int = Field(..., gt=0)
    cantidad_solicitada: int = Field(..., gt=0, description="Debe ser mayor a 0")


class SolicitudItemResponse(BaseModel):
    id: int
    insumo_id: int
    insumo_nombre: str
    stock_actual: int  # Stock al momento de consultar (no al momento de pedir)
    cantidad_solicitada: int

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Solicitud
# ---------------------------------------------------------------------------

class SolicitudCreate(BaseModel):
    """Payload que envia el docente al crear una solicitud.

    fecha_clase debe ser un datetime con timezone (ISO 8601). El frontend
    siempre envia con offset (ej. 2025-05-26T13:00:00-04:00). Validacion
    de que fecha_clase sea futura se hace en el route handler para poder
    devolver un mensaje claro en espanol.
    """
    sala_id: int = Field(..., gt=0)
    fecha_clase: datetime
    notas: Optional[str] = None
    items: list[SolicitudItemCreate] = Field(
        ..., min_length=1, description="Debe tener al menos un insumo"
    )


class SolicitudResponse(BaseModel):
    """Representacion completa de una solicitud, incluyendo items enriquecidos.

    docente_nombre y sala_nombre se resuelven desde las relaciones SQLAlchemy
    en el route handler; no vienen directamente del modelo.
    """
    id: int
    docente_id: int
    docente_nombre: str
    sala_id: int
    sala_nombre: str
    fecha_clase: datetime
    estado: EstadoSolicitud
    notas: Optional[str]
    notas_operador: Optional[str]
    fecha_creacion: datetime
    fecha_completada: Optional[datetime]
    items: list[SolicitudItemResponse]
    minutos_hasta_clase: int  # Calculado: util para indicador de urgencia

    class Config:
        from_attributes = True


class SolicitudUpdateEstado(BaseModel):
    """Payload del operador para actualizar el estado o agregar notas."""
    notas_operador: Optional[str] = None
