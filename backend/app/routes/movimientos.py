from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.database import get_db
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.insumo import Insumo
from app.models.usuario import Usuario
from app.models.sala import Sala
from app.schemas.movimiento import MovimientoCreate, MovimientoResponse, MovimientoEnriquecido
from app.utils.deps import get_usuario_actual, require_admin

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])

@router.get("/", response_model=list[MovimientoEnriquecido])
def listar_movimientos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    movimientos = (
        db.query(Movimiento)
        .options(
            joinedload(Movimiento.insumo).joinedload(Insumo.sala),
            joinedload(Movimiento.usuario)
        )
        .order_by(desc(Movimiento.fecha))
        .all()
    )

    return [
        MovimientoEnriquecido(
            id=m.id,
            tipo=m.tipo,
            cantidad=m.cantidad,
            motivo=m.motivo,
            fecha=m.fecha,
            insumo=m.insumo.nombre if m.insumo else "Desconocido",
            sala=m.insumo.sala.nombre if m.insumo and m.insumo.sala else None,
            usuario=m.usuario.nombre if m.usuario else "Desconocido"
        )
        for m in movimientos
    ]

@router.post("/", response_model=MovimientoResponse)
def registrar_movimiento(
    mov: MovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
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

@router.get("/insumo/{insumo_id}", response_model=list[MovimientoEnriquecido])
def historial_por_insumo(
    insumo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    movimientos = (
        db.query(Movimiento)
        .options(
            joinedload(Movimiento.insumo).joinedload(Insumo.sala),
            joinedload(Movimiento.usuario)
        )
        .filter(Movimiento.insumo_id == insumo_id)
        .order_by(desc(Movimiento.fecha))
        .all()
    )

    return [
        MovimientoEnriquecido(
            id=m.id,
            tipo=m.tipo,
            cantidad=m.cantidad,
            motivo=m.motivo,
            fecha=m.fecha,
            insumo=m.insumo.nombre if m.insumo else "Desconocido",
            sala=m.insumo.sala.nombre if m.insumo and m.insumo.sala else None,
            usuario=m.usuario.nombre if m.usuario else "Desconocido"
        )
        for m in movimientos
    ]

@router.get("/sala/{sala_id}", response_model=list[MovimientoEnriquecido])
def historial_por_sala(
    sala_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    sala = db.query(Sala).filter(Sala.id == sala_id).first()
    if not sala:
        raise HTTPException(status_code=404, detail="Sala no encontrada")

    movimientos = (
        db.query(Movimiento)
        .join(Insumo, Movimiento.insumo_id == Insumo.id)
        .options(
            joinedload(Movimiento.insumo).joinedload(Insumo.sala),
            joinedload(Movimiento.usuario)
        )
        .filter(Insumo.sala_id == sala_id)
        .order_by(desc(Movimiento.fecha))
        .all()
    )

    return [
        MovimientoEnriquecido(
            id=m.id,
            tipo=m.tipo,
            cantidad=m.cantidad,
            motivo=m.motivo,
            fecha=m.fecha,
            insumo=m.insumo.nombre if m.insumo else "Desconocido",
            sala=m.insumo.sala.nombre if m.insumo and m.insumo.sala else None,
            usuario=m.usuario.nombre if m.usuario else "Desconocido"
        )
        for m in movimientos
    ]