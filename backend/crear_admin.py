import sys
sys.path.append(".")

from app.database import SessionLocal, Base, engine
from app.models.usuario import Usuario, RolUsuario
from app.utils.security import hashear_password

# Importar todos los modelos para que SQLAlchemy los registre
from app.models.sala import Sala
from app.models.categoria import Categoria
from app.models.insumo import Insumo
from app.models.movimiento import Movimiento

# Crear las tablas si no existen
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Verificar si el admin ya existe
email = "gutierrezluis2203@hestia.cl"
admin_existente = db.query(Usuario).filter(Usuario.email == email).first()

if admin_existente:
    print(f"El admin con email {email} ya existe")
    # Actualizar rol a admin si no lo es
    if admin_existente.rol != RolUsuario.admin:
        admin_existente.rol = RolUsuario.admin
        db.commit()
        print(f"Rol actualizado a admin")
else:
    admin = Usuario(
        nombre="Luis Gutiérrez",
        email=email,
        password_hash=hashear_password("admin123"),
        rol=RolUsuario.admin
    )
    
    db.add(admin)
    db.commit()
    print(f"Admin creado: {admin.email}")

db.close()