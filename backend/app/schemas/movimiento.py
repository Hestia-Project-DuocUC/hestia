from pydantic import BaseModel
from app.models.movimiento import TipoMovimiento
from datetime import datetime

class MovimientoCreate(BaseModel):
    tipo: TipoMovimiento
    cantidad: int
    motivo: str | None = None
    insumo_id: int
    usuario_id: int

class MovimientoResponse(BaseModel):
    id: int
    tipo: TipoMovimiento
    cantidad: int
    motivo: str | None = None
    fecha: datetime
    insumo_id: int
    usuario_id: int

    class Config:
        from_attributes = True