from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
import pyotp

from app.database import get_db
from app.models.insumo import Insumo
from app.models.usuario import Usuario
from app.schemas.insumo import InsumoCreate, InsumoUpdate, InsumoResponse
from app.schemas.comun import PaginatedResponse
from app.utils.deps import get_usuario_actual, require_operador, require_admin

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


class EliminarInsumoRequest(BaseModel):
    codigo_totp: str


# IMPORTANTE: /alertas debe ir ANTES de /{insumo_id} para evitar conflicto de rutas.

@router.get("/alertas", response_model=list[InsumoAlerta])
def alertas_stock(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    """Insumos cuyo stock_actual es menor o igual al stock_minimo."""
    insumos = (
        db.query(Insumo)
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


@router.get("/", response_model=PaginatedResponse[InsumoResponse])
def listar_insumos(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)
):
    total = db.query(Insumo).count()
    insumos = db.query(Insumo).offset(skip).limit(limit).all()
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
    datos: InsumoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operador)
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(insumo, campo, valor)
    db.commit()
    db.refresh(insumo)
    return insumo


@router.delete("/{insumo_id}")
def eliminar_insumo(
    insumo_id: int,
    datos: EliminarInsumoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    """Elimina un insumo. Requiere rol admin + codigo TOTP valido.
    Si el admin no tiene 2FA activo, debe activarlo antes de poder eliminar.
    """
    if not usuario.totp_habilitado or not usuario.totp_secret:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debes tener el 2FA activado para eliminar insumos."
        )
    totp = pyotp.TOTP(usuario.totp_secret)
    if not totp.verify(datos.codigo_totp, valid_window=TOTP_VALID_WINDOW):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Codigo 2FA incorrecto. El insumo no fue eliminado."
        )
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    db.delete(insumo)
    db.commit()
    return {"mensaje": "Insumo eliminado"}
