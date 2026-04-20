from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaResponse

router = APIRouter(prefix="/categorias", tags=["Categorías"])

@router.get("/", response_model=list[CategoriaResponse])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(Categoria).all()

@router.post("/", response_model=CategoriaResponse)
def crear_categoria(categoria: CategoriaCreate, db: Session = Depends(get_db)):
    existente = db.query(Categoria).filter(Categoria.nombre == categoria.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")
    nueva = Categoria(**categoria.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.delete("/{categoria_id}")
def eliminar_categoria(categoria_id: int, db: Session = Depends(get_db)):
    categoria = db.query(Categoria).filter(Categoria.id == categoria_id).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    db.delete(categoria)
    db.commit()
    return {"mensaje": "Categoría eliminada"}