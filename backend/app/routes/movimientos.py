from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.insumo import Insumo
from app.schemas.movimiento import MovimientoCreate, MovimientoResponse

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])

@router.get("/", response_model=list[MovimientoResponse])
def listar_movimientos(db: Session = Depends(get_db)):
    return db.query(Movimiento).all()

@router.post("/", response_model=MovimientoResponse)
def registrar_movimiento(mov: MovimientoCreate, db: Session = Depends(get_db)):
    insumo = db.query(Insumo).filter(Insumo.id == mov.insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    if mov.tipo == TipoMovimiento.salida:
        if insumo.stock_actual < mov.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente. Disponible: {insumo.stock_actual}"
            )
        insumo.stock_actual -= mov.cantidad
    else:
        insumo.stock_actual += mov.cantidad

    nuevo_mov = Movimiento(**mov.model_dump())
    db.add(nuevo_mov)
    db.commit()
    db.refresh(nuevo_mov)
    return nuevo_mov

@router.get("/insumo/{insumo_id}", response_model=list[MovimientoResponse])
def historial_por_insumo(insumo_id: int, db: Session = Depends(get_db)):
    return db.query(Movimiento).filter(Movimiento.insumo_id == insumo_id).all()