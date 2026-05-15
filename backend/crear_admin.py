import sys
import os
sys.path.append(".")

from app.database import SessionLocal, Base, engine, aplicar_migraciones_pendientes
from app.models.usuario import Usuario, RolUsuario
from app.utils.security import hashear_password
from app.models.sala import Sala
from app.models.categoria import Categoria
from app.models.insumo import Insumo
from app.models.movimiento import Movimiento

# --- Leer credenciales desde el entorno, sin defaults ---
# Si alguna variable falta, el script falla con un mensaje claro.
# Nunca escribir contrasenas en el codigo fuente.
admin_email = os.getenv("ADMIN_EMAIL")
admin_password = os.getenv("ADMIN_PASSWORD")

if not admin_email or not admin_password:
    print("[ERROR] Las variables ADMIN_EMAIL y ADMIN_PASSWORD deben estar definidas en el .env")
    print("        Copia backend/.env.example a backend/.env y completa los valores.")
    sys.exit(1)

# 1) Crear tablas que no existen (basado en los modelos SQLAlchemy actuales)
Base.metadata.create_all(bind=engine)

# 2) Aplicar migraciones idempotentes (ALTER TABLE para columnas nuevas en
#    tablas ya existentes). Es seguro llamarlo aqui aunque uvicorn lo llame
#    de nuevo despues: cada ALTER TABLE IF EXISTS ... ADD COLUMN IF NOT EXISTS
#    no hace nada si la columna ya existe.
#    Sin este paso, en una BD nueva este script crea la tabla y luego intenta
#    consultarla con el ORM, que ya incluye las columnas nuevas en el SELECT,
#    causando un error de "columna no existe".
aplicar_migraciones_pendientes()

db = SessionLocal()

admin_existente = db.query(Usuario).filter(Usuario.email == admin_email).first()

if admin_existente:
    print(f"[Hestia] Admin ya existe: {admin_email}")
    if admin_existente.rol != RolUsuario.admin:
        admin_existente.rol = RolUsuario.admin
        db.commit()
        print(f"[Hestia] Rol actualizado a admin")
else:
    admin = Usuario(
        nombre="Administrador Hestia",
        email=admin_email,
        password_hash=hashear_password(admin_password),
        rol=RolUsuario.admin,
    )
    db.add(admin)
    db.commit()
    print(f"[Hestia] Admin creado: {admin_email}")

db.close()
