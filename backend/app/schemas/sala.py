from pydantic import BaseModel

class SalaCreate(BaseModel):
    nombre: str
    tipo: str | None = None
    descripcion: str | None = None

class SalaResponse(BaseModel):
    id: int
    nombre: str
    tipo: str | None = None

    class Config:
        from_attributes = True