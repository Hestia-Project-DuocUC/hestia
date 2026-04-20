from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sala import Sala
from app.schemas.sala import SalaCreate, SalaResponse

router = APIRouter(prefix="/salas", tags=["Salas"])

@router.get("/", response_model=list[SalaResponse])
def listar_salas(db: Session = Depends(get_db)):
    return db.query(Sala).all()

@router.post("/", response_model=SalaResponse)
def crear_sala(sala: SalaCreate, db: Session = Depends(get_db)):
    nueva = Sala(**sala.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.get("/{sala_id}", response_model=SalaResponse)
def obtener_sala(sala_id: int, db: Session = Depends(get_db)):
    sala = db.query(Sala).filter(Sala.id == sala_id).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    return sala

@router.delete("/{sala_id}")
def eliminar_sala(sala_id: int, db: Session = Depends(get_db)):
    sala = db.query(Sala).filter(Sala.id == sala_id).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    db.delete(sala)
    db.commit()
    return {"mensaje": "Sala eliminada"}