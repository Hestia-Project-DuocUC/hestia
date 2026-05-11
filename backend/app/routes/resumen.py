from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from pydantic import BaseModel
from datetime import date

from app.database import get_db
from app.models.insumo import Insumo
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.sala import Sala
from app.models.usuario import Usuario
from app.utils.deps import get_usuario_actual

router = APIRouter(prefix="/resumen", tags=["Resumen"])


# --- Schema de respuesta ---

class ResumenResponse(BaseModel):
    # Inventario
    total_insumos: int
    insumos_bajo_stock: int     # cuantos estan en alerta
    # Actividad de hoy
    movimientos_hoy: int
    entradas_hoy: int
    salidas_hoy: int
    # Estructura
    total_salas: int
    total_usuarios: int


@router.get("/", response_model=ResumenResponse)
def obtener_resumen(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)  # cualquier rol
):
    """Devuelve una fotografia general del sistema.
    Pensado para alimentar el dashboard principal del frontend.

    Todas las consultas van en una sola llamada para minimizar roundtrips.
    """

    # --- Inventario ---
    total_insumos = db.query(Insumo).count()

    insumos_bajo_stock = (
        db.query(Insumo)
        .filter(Insumo.stock_actual <= Insumo.stock_minimo)
        .count()
    )

    # --- Movimientos de hoy ---
    # cast(fecha, Date) extrae solo la fecha del timestamp (ignora la hora).
    # Esto permite comparar con date.today() sin importar la hora exacta.
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
            Movimiento.tipo == TipoMovimiento.entrada
        )
        .count()
    )

    salidas_hoy = (
        db.query(Movimiento)
        .filter(
            cast(Movimiento.fecha, Date) == hoy,
            Movimiento.tipo == TipoMovimiento.salida
        )
        .count()
    )

    # --- Estructura ---
    total_salas = db.query(Sala).count()
    total_usuarios = db.query(Usuario).count()

    return ResumenResponse(
        total_insumos=total_insumos,
        insumos_bajo_stock=insumos_bajo_stock,
        movimientos_hoy=movimientos_hoy,
        entradas_hoy=entradas_hoy,
        salidas_hoy=salidas_hoy,
        total_salas=total_salas,
        total_usuarios=total_usuarios,
    )
