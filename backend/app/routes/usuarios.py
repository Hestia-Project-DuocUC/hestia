from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioResponse

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/", response_model=list[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()

@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if existente:
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    # Por ahora guardamos el password directamente
    # En el paso de autenticación esto cambia por un hash real
    nuevo = Usuario(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=usuario.password,
        rol=usuario.rol
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo