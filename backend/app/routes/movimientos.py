from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from app.database import get_db
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.insumo import Insumo
from app.models.usuario import Usuario
from app.models.sala import Sala
from app.schemas.movimiento import MovimientoCreate, MovimientoResponse, MovimientoEnriquecido
from app.schemas.comun import PaginatedResponse
from app.utils.deps import get_usuario_actual, require_operador

router = APIRouter(prefix="/movimientos", tags=["Movimientos"])


def _enriquecer(m: Movimiento) -> MovimientoEnriquecido:
    return MovimientoEnriquecido(
        id=m.id,
        tipo=m.tipo,
        cantidad=m.cantidad,
        motivo=m.motivo,
        fecha=m.fecha,
        insumo=m.insumo.nombre if m.insumo else "Desconocido",
        sala=m.insumo.sala.nombre if m.insumo and m.insumo.sala else None,
        usuario=m.usuario.nombre if m.usuario else "Desconocido"
    )


def _query_enriquecida(db: Session):
    return (
        db.query(Movimiento)
        .options(
            joinedload(Movimiento.insumo).joinedload(Insumo.sala),
            joinedload(Movimiento.usuario)
        )
        .order_by(desc(Movimiento.fecha))
    )


@router.get("/", response_model=PaginatedResponse[MovimientoEnriquecido])
def listar_movimientos(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)  # visor, operador y admin
):
    total = db.query(Movimiento).count()
    movimientos = _query_enriquecida(db).offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_enriquecer(m) for m in movimientos]
    }


@router.post("/", response_model=MovimientoResponse)
def registrar_movimiento(
    mov: MovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operador)  # operador y admin
):
    insumo = db.query(Insumo).filter(Insumo.id == mov.insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    # No se permiten movimientos sobre insumos desactivados (soft-deleted).
    # El admin debe reactivar el insumo primero si quiere registrar stock.
    if not insumo.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"'{insumo.nombre}' esta inactivo. Reactivalo antes de "
                "registrar movimientos."
            ),
        )

    if mov.tipo == TipoMovimiento.salida:
        if insumo.stock_actual < mov.cantidad:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuficiente. Disponible: {insumo.stock_actual}"
            )
        insumo.stock_actual -= mov.cantidad
    else:
        insumo.stock_actual += mov.cantidad

    nuevo_mov = Movimiento(**mov.model_dump(), usuario_id=usuario.id)
    db.add(nuevo_mov)
    db.commit()
    db.refresh(nuevo_mov)
    return nuevo_mov


@router.get("/insumo/{insumo_id}", response_model=PaginatedResponse[MovimientoEnriquecido])
def historial_por_insumo(
    insumo_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)  # visor, operador y admin
):
    if not db.query(Insumo).filter(Insumo.id == insumo_id).first():
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    total = db.query(Movimiento).filter(Movimiento.insumo_id == insumo_id).count()
    movimientos = (
        _query_enriquecida(db)
        .filter(Movimiento.insumo_id == insumo_id)
        .offset(skip).limit(limit).all()
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_enriquecer(m) for m in movimientos]
    }


@router.get("/sala/{sala_id}", response_model=PaginatedResponse[MovimientoEnriquecido])
def historial_por_sala(
    sala_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)  # visor, operador y admin
):
    if not db.query(Sala).filter(Sala.id == sala_id).first():
        raise HTTPException(status_code=404, detail="Sala no encontrada")
    total = (
        db.query(Movimiento)
        .join(Insumo, Movimiento.insumo_id == Insumo.id)
        .filter(Insumo.sala_id == sala_id)
        .count()
    )
    movimientos = (
        _query_enriquecida(db)
        .join(Insumo, Movimiento.insumo_id == Insumo.id)
        .filter(Insumo.sala_id == sala_id)
        .offset(skip).limit(limit).all()
    )
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [_enriquecer(m) for m in movimientos]
    }
