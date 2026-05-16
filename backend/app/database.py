from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Mini-migraciones idempotentes
# ---------------------------------------------------------------------------
# Base.metadata.create_all() solo crea tablas nuevas; NO agrega columnas a
# tablas ya existentes. Mientras el proyecto no use Alembic, declaramos aqui
# sentencias ALTER TABLE / ALTER TYPE idempotentes para evolucionar el esquema
# sin perder datos ni necesitar un down/up.
#
# IMPORTANTE — dos categorias de migracion con requisitos distintos:
#
# 1. MIGRACIONES_COLUMNAS (ADD COLUMN IF NOT EXISTS)
#    Corren dentro de una transaccion normal (engine.begin()).
#    Si algo falla, el bloque completo hace rollback.
#
# 2. MIGRACIONES_ENUM (ALTER TYPE ... ADD VALUE IF NOT EXISTS)
#    PostgreSQL NO permite ejecutar ALTER TYPE ADD VALUE dentro de un bloque
#    de transaccion explicito (lanza "ALTER TYPE ... ADD VALUE cannot run
#    inside a transaction block"). Por eso se ejecutan en modo AUTOCOMMIT:
#    cada sentencia se confirma de inmediato, sin transaccion envolvente.
#    IF NOT EXISTS garantiza idempotencia: si el valor ya existe, no falla.
#    Requiere Postgres 9.6+ para IF NOT EXISTS; el proyecto usa Postgres 16.
# ---------------------------------------------------------------------------

MIGRACIONES_COLUMNAS = [
    # Soft-delete de usuarios e insumos
    "ALTER TABLE IF EXISTS usuarios "
    "ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE IF EXISTS insumos "
    "ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
    # Foto de perfil (data URL base64, max ~3 MB de string)
    "ALTER TABLE IF EXISTS usuarios "
    "ADD COLUMN IF NOT EXISTS avatar_b64 TEXT",
]

MIGRACIONES_ENUM = [
    # Agrega el valor 'docente' al tipo ENUM rolususario si no existe.
    # Nombre del tipo en Postgres: SQLAlchemy lo genera como 'rolususario'
    # a partir de la clase RolUsuario (minusculas, sin guiones bajos).
    "ALTER TYPE rolususario ADD VALUE IF NOT EXISTS 'docente'",
]


def aplicar_migraciones_pendientes() -> None:
    """Aplica todas las migraciones idempotentes al arrancar la app.

    Fase 1 — columnas: dentro de una transaccion. Si falla alguna sentencia
    el bloque completo hace rollback y la excepcion sube para que el proceso
    no arranque con el esquema a medias.

    Fase 2 — tipos ENUM: fuera de transaccion (AUTOCOMMIT). ALTER TYPE ADD
    VALUE no puede correr dentro de un bloque de transaccion explicito en
    PostgreSQL; usar AUTOCOMMIT resuelve esa restriccion sin perder
    idempotencia (IF NOT EXISTS).
    """
    # Fase 1: columnas (transaccional)
    with engine.begin() as conn:
        for sql in MIGRACIONES_COLUMNAS:
            conn.execute(text(sql))

    # Fase 2: tipos ENUM (autocommit — sin transaccion)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for sql in MIGRACIONES_ENUM:
            conn.execute(text(sql))
