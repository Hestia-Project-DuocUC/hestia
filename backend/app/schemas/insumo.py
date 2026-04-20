from pydantic import BaseModel
from app.models.movimiento import TipoMovimiento

class InsumoCreate(BaseModel):
    nombre: str
    descripcion: str | None = None
    stock_actual: int = 0
    stock_minimo: int = 0
    sala_id: int | None = None
    categoria_id: int | None = None

class InsumoUpdate(BaseModel):
    nombre: str | None = None
    descripcion: str | None = None
    stock_actual: int | None = None
    stock_minimo: int | None = None
    sala_id: int | None = None
    categoria_id: int | None = None

class InsumoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    stock_actual: int
    stock_minimo: int
    sala_id: int | None = None
    categoria_id: int | None = None

    class Config:
        from_attributes = True