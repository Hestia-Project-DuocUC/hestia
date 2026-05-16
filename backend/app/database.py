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
#    una transaccion. Se manejan con _agregar_valor_enum() en modo AUTOCOMMIT,
#    con verificacion previa de existencia via pg_type / pg_enum.
#    RAZON del chequeo previo: en BD nueva, create_all() ya crea el tipo con
#    todos los valores actuales del enum Python, por lo que intentar ALTER
#    sobre un tipo inexistente (si create_all() aun no corrio en esta sesion)
#    lanzaria UndefinedObject. La funcion detecta ese caso y lo omite de
#    forma segura: create_all() se encargara de crearlo correctamente.
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


def _agregar_valor_enum(conn, tipo: str, valor: str) -> None:
    """Agrega un valor a un enum PostgreSQL de forma segura e idempotente.

    Logica:
    1. Si el tipo NO existe en pg_type: no hace nada. Esto ocurre en BD nueva
       antes de que create_all() haya corrido, o si el tipo fue creado con
       un nombre distinto. En BD nueva, create_all() lo creara con todos los
       valores actuales del enum Python, incluyendo el que queremos agregar.
    2. Si el tipo existe y el valor YA esta: no hace nada (idempotente).
    3. Si el tipo existe y el valor FALTA: ejecuta ALTER TYPE ADD VALUE.
       Requiere AUTOCOMMIT (restriccion de PostgreSQL para esta sentencia).
    """
    tipo_existe = conn.execute(
        text("SELECT 1 FROM pg_type WHERE typname = :t"),
        {"t": tipo},
    ).fetchone()

    if not tipo_existe:
        # BD nueva o tipo con nombre diferente: create_all() lo resolvera.
        return

    valor_existe = conn.execute(
        text(
            "SELECT 1 FROM pg_enum e "
            "JOIN pg_type t ON e.enumtypid = t.oid "
            "WHERE t.typname = :t AND e.enumlabel = :v"
        ),
        {"t": tipo, "v": valor},
    ).fetchone()

    if not valor_existe:
        conn.execute(text(f"ALTER TYPE {tipo} ADD VALUE '{valor}'"))


def aplicar_migraciones_pendientes() -> None:
    """Aplica todas las migraciones idempotentes al arrancar la app.

    Fase 1: columnas (transaccional via engine.begin()).
    Fase 2: valores de enum (AUTOCOMMIT con verificacion previa).
    """
    # Fase 1: columnas (transaccional)
    with engine.begin() as conn:
        for sql in MIGRACIONES_COLUMNAS:
            conn.execute(text(sql))

    # Fase 2: valores de enum (AUTOCOMMIT — PostgreSQL lo exige)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        for tipo, valor in MIGRACIONES_ENUM_VALORES:
            _agregar_valor_enum(conn, tipo, valor)
