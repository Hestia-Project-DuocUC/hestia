from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import pyotp
import csv
import io

from app.database import get_db
from app.models.insumo import Insumo
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.usuario import Usuario, RolUsuario
from app.schemas.insumo import InsumoCreate, InsumoUpdate, InsumoResponse
from app.schemas.comun import PaginatedResponse
from app.utils.deps import get_usuario_actual, require_operador, require_admin
from app.utils.auditoria import registrar, get_ip

router = APIRouter(prefix="/insumos", tags=["Insumos"])

TOTP_VALID_WINDOW = 1


class InsumoAlerta(BaseModel):
    id: int
    nombre: str
    stock_actual: int
    stock_minimo: int
    deficit: int
    sala: str | None
    categoria: str | None

    class Config:
        from_attributes = True


def _build_query(db: Session,
                 nombre: Optional[str] = None,
                 sala_id: Optional[int] = None,
                 categoria_id: Optional[int] = None,
                 bajo_stock: Optional[bool] = None,
                 incluir_inactivos: bool = False):
    """Construye la query base con filtros opcionales reutilizable.
    Por defecto excluye insumos desactivados (soft-delete).
    """
    q = db.query(Insumo)
    if not incluir_inactivos:
        q = q.filter(Insumo.activo.is_(True))
    if nombre:
        q = q.filter(Insumo.nombre.ilike(f"%{nombre}%"))
    if sala_id is not None:
        q = q.filter(Insumo.sala_id == sala_id)
    if categoria_id is not None:
        q = q.filter(Insumo.categoria_id == categoria_id)
    if bajo_stock:
        q = q.filter(Insumo.stock_actual <= Insumo.stock_minimo)
    return q


# ---------------------------------------------------------------------------
# IMPORTANTE: rutas estaticas (/alertas, /alertas-resueltas, /exportar)
# deben ir ANTES de la ruta dinamica /{insumo_id}, o FastAPI las interpreta
# como un entero y devuelve 422 Unprocessable Entity.
# ---------------------------------------------------------------------------

@router.get("/alertas", response_model=list[InsumoAlerta])
def alertas_stock(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Insumos activos cuyo stock_actual es menor o igual al stock_minimo."""
    insumos = (
        db.query(Insumo)
        .filter(Insumo.activo.is_(True))
        .filter(Insumo.stock_actual <= Insumo.stock_minimo)
        .order_by(Insumo.stock_actual.asc())
        .all()
    )
    return [
        InsumoAlerta(
            id=i.id,
            nombre=i.nombre,
            stock_actual=i.stock_actual,
            stock_minimo=i.stock_minimo,
            deficit=i.stock_minimo - i.stock_actual,
            sala=i.sala.nombre if i.sala else None,
            categoria=i.categoria.nombre if i.categoria else None,
        )
        for i in insumos
    ]


@router.get("/alertas-resueltas", response_model=list[InsumoAlerta])
def alertas_resueltas(
    dias: int = 30,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Insumos activos que YA superaron el stock minimo y ademas tuvieron al
    menos una entrada en los ultimos `dias` dias.

    Por que subquery y no JOIN:
    Un JOIN con Movimiento duplicaria filas si un insumo tiene multiples
    entradas en el periodo. La subquery devuelve insumo_ids unicos (DISTINCT),
    y luego filtramos Insumo sobre esa lista: limpio y eficiente.

    Por que timezone.utc:
    Movimiento.fecha es DateTime(timezone=True) en PostgreSQL, lo que
    almacena timestamps con offset. Comparar con datetime.utcnow() (naive)
    puede causar errores en algunas versiones de SQLAlchemy/psycopg2.
    datetime.now(timezone.utc) es timezone-aware y compatibe de forma segura.
    """
    desde = datetime.now(timezone.utc) - timedelta(days=dias)

    subq = (
        db.query(Movimiento.insumo_id)
        .filter(
            Movimiento.tipo == TipoMovimiento.entrada,
            Movimiento.fecha >= desde,
        )
        .distinct()
        .subquery()
    )

    insumos = (
        db.query(Insumo)
        .filter(
            Insumo.activo.is_(True),
            Insumo.stock_actual > Insumo.stock_minimo,
            Insumo.id.in_(subq),
        )
        .order_by(Insumo.nombre)
        .all()
    )

    return [
        InsumoAlerta(
            id=i.id,
            nombre=i.nombre,
            stock_actual=i.stock_actual,
            stock_minimo=i.stock_minimo,
            deficit=i.stock_minimo - i.stock_actual,
            sala=i.sala.nombre if i.sala else None,
            categoria=i.categoria.nombre if i.categoria else None,
        )
        for i in insumos
    ]


@router.get("/exportar")
def exportar_insumos(
    nombre: Optional[str] = None,
    sala_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    bajo_stock: Optional[bool] = None,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Exporta el inventario como CSV con los mismos filtros del listado.
    Por defecto solo incluye insumos activos. El archivo se abre directamente
    en Excel gracias al BOM UTF-8.
    """
    insumos = _build_query(
        db, nombre, sala_id, categoria_id, bajo_stock, incluir_inactivos
    ).order_by(Insumo.nombre).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "nombre", "descripcion", "stock_actual",
        "stock_minimo", "sala", "categoria", "estado"
    ])
    for i in insumos:
        if not i.activo:
            estado = "inactivo"
        elif i.stock_actual == 0:
            estado = "agotado"
        elif i.stock_actual <= i.stock_minimo:
            estado = "bajo_stock"
        else:
            estado = "ok"
        writer.writerow([
            i.nombre,
            i.descripcion or "",
            i.stock_actual,
            i.stock_minimo,
            i.sala.nombre if i.sala else "",
            i.categoria.nombre if i.categoria else "",
            estado
        ])
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=inventario_hestia.csv"}
    )


@router.get("/", response_model=PaginatedResponse[InsumoResponse])
def listar_insumos(
    skip: int = 0,
    limit: int = 20,
    nombre: Optional[str] = None,
    sala_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    bajo_stock: Optional[bool] = None,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Lista insumos con filtros opcionales: nombre, sala, categoria,
    bajo_stock, incluir_inactivos. Por defecto excluye desactivados.
    """
    q = _build_query(
        db, nombre, sala_id, categoria_id, bajo_stock, incluir_inactivos
    )
    total = q.count()
    insumos = q.offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "data": insumos}


@router.get("/{insumo_id}", response_model=InsumoResponse)
def obtener_insumo(
    insumo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    return insumo


@router.post("/", response_model=InsumoResponse)
def crear_insumo(
    insumo: InsumoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operador)
):
    nuevo = Insumo(**insumo.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{insumo_id}", response_model=InsumoResponse)
def actualizar_insumo(
    insumo_id: int,
    request: Request,
    datos: InsumoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operador)
):
    """Actualiza campos del insumo. Operador puede editar todo excepto
    'activo'; solo admin puede reactivar/desactivar via PUT. El cambio de
    estado queda registrado en audit_log."""
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")

    cambio_activo: str | None = None
    if datos.activo is not None and datos.activo != insumo.activo:
        if usuario.rol != RolUsuario.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Solo administradores pueden cambiar el estado activo.",
            )
        cambio_activo = (
            "REACTIVAR_INSUMO" if datos.activo else "DESACTIVAR_INSUMO"
        )

    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(insumo, campo, valor)
    db.commit()
    db.refresh(insumo)

    if cambio_activo:
        registrar(
            db, cambio_activo, usuario=usuario,
            entidad="insumo", entidad_id=insumo.id,
            detalle=insumo.nombre, ip=get_ip(request),
        )
    return insumo


@router.delete("/{insumo_id}")
def eliminar_insumo(
    insumo_id: int,
    request: Request,
    codigo_totp: str = Header(alias="x-totp-code"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Soft-delete: marca el insumo como inactivo (activo=false).

    Antes este endpoint hacia DELETE fisico y fallaba con FK violation cuando
    el insumo tenia movimientos asociados (movimientos.insumo_id es NOT NULL
    sin ON DELETE policy). El resultado era un 500 sin JSON y el frontend
    mostraba un generico 'Error al eliminar' sin detalle.

    Ahora la fila se conserva: el insumo desaparece de listados, alertas y
    exportaciones, pero el historial de movimientos sigue siendo trazable.
    Reactivable via PUT /insumos/{id} con activo=true (solo admin).

    Requiere rol admin + codigo TOTP valido (header x-totp-code).
    """
    if not usuario.totp_habilitado or not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes tener el 2FA activado para desactivar insumos."
        )
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(codigo_totp, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Codigo 2FA incorrecto. El insumo no fue desactivado."
        )
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    if not insumo.activo:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{insumo.nombre}' ya esta inactivo",
        )
    insumo.activo = False
    db.commit()
    registrar(
        db, "DESACTIVAR_INSUMO", usuario=usuario,
        entidad="insumo", entidad_id=insumo.id,
        detalle=insumo.nombre, ip=get_ip(request),
    )
    return {"mensaje": f"Insumo '{insumo.nombre}' desactivado"}
