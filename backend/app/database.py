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
# las migraciones necesarias para evolucionar el esquema sin perder datos.
#
# IMPORTANTE — dos categorias de migracion con requisitos distintos:
#
# 1. MIGRACIONES_COLUMNAS (ADD COLUMN IF NOT EXISTS)
#    Corren dentro de una transaccion normal (engine.begin()).
#
# 2. Valores de ENUM: PostgreSQL NO permite ALTER TYPE ADD VALUE dentro de
#    ninguna transaccion, ni siquiera implicita.
#    SQLAlchemy 2.x inicia una transaccion implicita en cada conexion antes
#    de ejecutar el primer statement, por lo que execution_options(
#    isolation_level="AUTOCOMMIT") aplicado sobre la conexion ya creada
#    no tiene el efecto esperado.
#    Solucion: usar engine.raw_connection() para obtener la conexion psycopg2
#    subyacente directamente y setear isolation_level=0 (AUTOCOMMIT) antes
#    de cualquier statement. Esta es la forma mas confiable y portable.
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

# Lista de (nombre_tipo, valor) que deben existir en la BD.
MIGRACIONES_ENUM_VALORES = [
    ("rolususario", "docente"),
]


def aplicar_migraciones_pendientes() -> None:
    """Aplica todas las migraciones idempotentes al arrancar la app.

    Fase 1 — columnas: dentro de una transaccion normal (engine.begin()).
    Si falla alguna sentencia el bloque completo hace rollback y la excepcion
    sube para que el proceso no arranque con el esquema a medias.

    Fase 2 — tipos ENUM: via psycopg2 raw_connection() en AUTOCOMMIT puro.
    PostgreSQL exige que ALTER TYPE ADD VALUE corra fuera de cualquier
    transaccion (ni siquiera implicita). SQLAlchemy 2.x no permite garantizar
    esto a traves de la capa ORM de forma confiable, asi que obtenemos la
    conexion psycopg2 subyacente directamente y seteamos isolation_level=0
    antes del primer statement.
    """
    # Fase 1: columnas (transaccional)
    with engine.begin() as conn:
        for sql in MIGRACIONES_COLUMNAS:
            conn.execute(text(sql))

    # Fase 2: valores de enum (psycopg2 raw en AUTOCOMMIT)
    raw_conn = engine.raw_connection()
    try:
        # isolation_level=0 equivale a psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT
        # Debe setearse ANTES del primer execute para que no haya transaccion abierta.
        raw_conn.set_isolation_level(0)
        cur = raw_conn.cursor()
        for tipo, valor in MIGRACIONES_ENUM_VALORES:
            # 1. Si el tipo no existe en pg_type: create_all() lo creara con
            #    todos los valores actuales del enum Python (incl. el nuevo).
            cur.execute("SELECT 1 FROM pg_type WHERE typname = %s", (tipo,))
            if not cur.fetchone():
                continue
            # 2. Si el valor ya existe: idempotente, no hacer nada.
            cur.execute(
                "SELECT 1 FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "WHERE t.typname = %s AND e.enumlabel = %s",
                (tipo, valor),
            )
            if not cur.fetchone():
                # ALTER TYPE ADD VALUE no acepta parametros — el nombre
                # del tipo y el valor son identifiers/literales, no user input.
                cur.execute(f"ALTER TYPE {tipo} ADD VALUE '{valor}'")
        cur.close()
    finally:
        raw_conn.close()
