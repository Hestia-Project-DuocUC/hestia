from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.insumo import Insumo
from app.schemas.insumo import InsumoCreate, InsumoUpdate, InsumoResponse

router = APIRouter(prefix="/insumos", tags=["Insumos"])

@router.get("/", response_model=list[InsumoResponse])
def listar_insumos(db: Session = Depends(get_db)):
    return db.query(Insumo).all()

@router.post("/", response_model=InsumoResponse)
def crear_insumo(insumo: InsumoCreate, db: Session = Depends(get_db)):
    nuevo = Insumo(**insumo.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo

@router.get("/{insumo_id}", response_model=InsumoResponse)
def obtener_insumo(insumo_id: int, db: Session = Depends(get_db)):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    return insumo

@router.put("/{insumo_id}", response_model=InsumoResponse)
def actualizar_insumo(insumo_id: int, datos: InsumoUpdate, db: Session = Depends(get_db)):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(insumo, campo, valor)
    db.commit()
    db.refresh(insumo)
    return insumo

@router.delete("/{insumo_id}")
def eliminar_insumo(insumo_id: int, db: Session = Depends(get_db)):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    db.delete(insumo)
    db.commit()
    return {"mensaje": "Insumo eliminado"}