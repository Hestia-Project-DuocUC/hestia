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
# sentencias ALTER TABLE idempotentes para evolucionar el esquema sin perder
# datos.
#
# - ALTER TABLE IF EXISTS: evita error si create_all() todavia no corrio.
# - ADD COLUMN IF NOT EXISTS: evita error si la columna ya fue agregada en
#   un arranque anterior.
# Soportado por PostgreSQL 9.6+; el proyecto usa Postgres 16.
# ---------------------------------------------------------------------------

MIGRACIONES_IDEMPOTENTES = [
    "ALTER TABLE IF EXISTS usuarios "
    "ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
    "ALTER TABLE IF EXISTS insumos "
    "ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE",
]


def aplicar_migraciones_pendientes() -> None:
    """Aplica ALTER TABLE idempotentes al arrancar la app.

    Cada sentencia es segura para correr en cada arranque: si la columna
    ya existe, Postgres no hace nada. engine.begin() abre una transaccion
    y hace commit automatico al salir del context manager.
    """
    with engine.begin() as conn:
        for sql in MIGRACIONES_IDEMPOTENTES:
            conn.execute(text(sql))
