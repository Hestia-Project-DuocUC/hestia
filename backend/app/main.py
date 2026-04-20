from fastapi import FastAPI
from app.database import Base, engine
from app.models import sala, categoria, usuario, movimiento, insumo
from app.routes import salas, categorias, usuarios, movimientos, insumos

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hestia",
    description="Sistema de gestión de insumos — DuocUC",
    version="0.1.0"
)

app.include_router(salas.router)
app.include_router(categorias.router)
app.include_router(usuarios.router)
app.include_router(movimientos.router)
app.include_router(insumos.router)

@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a Hestia", "estado": "activo"}