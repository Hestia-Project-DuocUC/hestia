from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse
from app.schemas.comun import PaginatedResponse
from app.utils.deps import get_usuario_actual, require_admin
from app.utils.security import hashear_password

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


@router.get("/", response_model=PaginatedResponse[UsuarioResponse])
def listar_usuarios(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    total = db.query(Usuario).count()
    usuarios = db.query(Usuario).offset(skip).limit(limit).all()
    return {"total": total, "skip": skip, "limit": limit, "data": usuarios}


@router.get("/me", response_model=UsuarioResponse)
def perfil_propio(usuario: Usuario = Depends(get_usuario_actual)):
    return usuario


@router.get("/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    encontrado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return encontrado


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="El email ya esta registrado")
    nuevo = Usuario(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hashear_password(datos.password),
        rol=datos.rol
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.put("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: int,
    datos: UsuarioCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    encontrado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    encontrado.nombre = datos.nombre
    encontrado.email = datos.email
    encontrado.password_hash = hashear_password(datos.password)
    encontrado.rol = datos.rol
    db.commit()
    db.refresh(encontrado)
    return encontrado


@router.delete("/{usuario_id}")
def eliminar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin)
):
    encontrado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not encontrado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if encontrado.id == usuario.id:
        raise HTTPException(
            status_code=400, detail="No puedes eliminarte a ti mismo"
        )
    db.delete(encontrado)
    db.commit()
    return {"mensaje": "Usuario eliminado"}


@router.post("/{usuario_id}/reset-2fa")
def reset_2fa_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):
    """Desactiva el 2FA de cualquier usuario. Solo administradores.
    Util para recuperacion de acceso cuando el usuario perdio su dispositivo.
    """
    target = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    target.totp_habilitado = False
    target.totp_secret = None
    target.totp_recovery_codes = None
    db.commit()
    return {"mensaje": f"2FA desactivado para {target.email}"}
