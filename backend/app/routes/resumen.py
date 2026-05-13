from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date, case
from pydantic import BaseModel
from datetime import date, datetime, timedelta, timezone
from typing import List

from app.database import get_db
from app.models.insumo import Insumo
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.utils.deps import get_usuario_actual

router = APIRouter(prefix="/resumen", tags=["Resumen"])


# --- Schemas ---

class ResumenResponse(BaseModel):
    total_insumos: int
    insumos_bajo_stock: int
    insumos_agotados: int
    movimientos_hoy: int
    entradas_hoy: int
    salidas_hoy: int
    total_salas: int
    total_usuarios: int


class DiaMovimiento(BaseModel):
    fecha: str
    entradas: int
    salidas: int


@router.get("/", response_model=ResumenResponse)
def obtener_resumen(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Fotografia general del sistema para el dashboard."""
    total_insumos = db.query(Insumo).count()

    insumos_bajo_stock = (
        db.query(Insumo)
        .filter(Insumo.stock_actual <= Insumo.stock_minimo)
        .count()
    )

    insumos_agotados = (
        db.query(Insumo)
        .filter(Insumo.stock_actual == 0)
        .count()
    )

    hoy = date.today()

    movimientos_hoy = (
        db.query(Movimiento)
        .filter(cast(Movimiento.fecha, Date) == hoy)
        .count()
    )
    entradas_hoy = (
        db.query(Movimiento)
        .filter(
            cast(Movimiento.fecha, Date) == hoy,
            Movimiento.tipo == TipoMovimiento.entrada,
        )
        .count()
    )
    salidas_hoy = (
        db.query(Movimiento)
        .filter(
            cast(Movimiento.fecha, Date) == hoy,
            Movimiento.tipo == TipoMovimiento.salida,
        )
        .count()
    )

    total_salas = db.query(Sala).count()
    total_usuarios = db.query(Usuario).count()

    return ResumenResponse(
        total_insumos=total_insumos,
        insumos_bajo_stock=insumos_bajo_stock,
        insumos_agotados=insumos_agotados,
        movimientos_hoy=movimientos_hoy,
        entradas_hoy=entradas_hoy,
        salidas_hoy=salidas_hoy,
        total_salas=total_salas,
        total_usuarios=total_usuarios,
    )


@router.get("/grafico-semana", response_model=List[DiaMovimiento])
def grafico_semana(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual),
):
    """Movimientos de los ultimos 7 dias agrupados por dia.

    Siempre devuelve exactamente 7 elementos (dias sin actividad = 0).
    Usa agregacion condicional con CASE para contar entradas y salidas
    en una sola query en vez de dos queries separadas.
    """
    desde = datetime.now(timezone.utc) - timedelta(days=7)

    resultados = (
        db.query(
            cast(Movimiento.fecha, Date).label("dia"),
            func.sum(
                case((Movimiento.tipo == TipoMovimiento.entrada, 1), else_=0)
            ).label("entradas"),
            func.sum(
                case((Movimiento.tipo == TipoMovimiento.salida, 1), else_=0)
            ).label("salidas"),
        )
        .filter(Movimiento.fecha >= desde)
        .group_by(cast(Movimiento.fecha, Date))
        .order_by(cast(Movimiento.fecha, Date))
        .all()
    )

    # Construir serie completa de 7 dias rellenando los que no tienen actividad
    hoy = date.today()
    serie: dict[str, dict] = {
        (hoy - timedelta(days=i)).isoformat(): {"entradas": 0, "salidas": 0}
        for i in range(6, -1, -1)   # de mas antiguo a mas reciente
    }

    for r in resultados:
        clave = r.dia.isoformat()
        if clave in serie:
            serie[clave] = {
                "entradas": int(r.entradas or 0),
                "salidas": int(r.salidas or 0),
            }

    return [
        DiaMovimiento(fecha=fecha, entradas=v["entradas"], salidas=v["salidas"])
        for fecha, v in serie.items()
    ]
