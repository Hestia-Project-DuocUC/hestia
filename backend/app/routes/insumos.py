from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.insumo import Insumo
from app.models.usuario import Usuario
from app.schemas.insumo import InsumoCreate, InsumoUpdate, InsumoResponse
from app.schemas.comun import PaginatedResponse
from app.utils.deps import get_usuario_actual, require_operador, require_admin

router = APIRouter(prefix="/insumos", tags=["Insumos"])


@router.get("/", response_model=PaginatedResponse[InsumoResponse])
def listar_insumos(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)  # visor, operador y admin
):
    total = db.query(Insumo).count()
    insumos = db.query(Insumo).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "data": insumos}


@router.get("/{insumo_id}", response_model=InsumoResponse)
def obtener_insumo(
    insumo_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_usuario_actual)  # visor, operador y admin
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    return insumo


@router.post("/", response_model=InsumoResponse)
def crear_insumo(
    insumo: InsumoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operador)  # operador y admin
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
    usuario: Usuario = Depends(require_operador)  # operador y admin
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
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)  # solo admin
):
    insumo = db.query(Insumo).filter(Insumo.id == insumo_id).first()
    if not insumo:
        raise HTTPException(status_code=404, detail="Insumo no encontrado")
    db.delete(insumo)
    db.commit()
    return {"mensaje": "Insumo eliminado"}
