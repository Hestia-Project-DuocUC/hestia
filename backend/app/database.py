from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no esta configurada. "
        "Crea backend/.env con DATABASE_URL=postgresql://..."
    )

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
# El tipo de columna 'rol' depende de como SQLAlchemy creo la tabla:
#
# A) Enum nativo PostgreSQL (pg_type tiene 'rolususario'):
#    -> ALTER TYPE rolususario ADD VALUE 'docente'
#    -> Requiere AUTOCOMMIT (psycopg2 directo con conn.autocommit = True)
#
# B) VARCHAR con CHECK constraint (pg_type NO tiene 'rolususario'):
#    -> La constraint bloquea insertar 'docente'
#    -> Solucion: DROP CONSTRAINT y dejar que Python valide los valores
#    -> La validacion de Pydantic/SQLAlchemy en la app es suficiente
#    -> Nombre tipico de SQLAlchemy: {tabla}_{columna}_check
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

# Lista de (tabla, columna, valores_permitidos) para migraciones de enum/check.
MIGRACIONES_ROL = [
    ("usuarios", "rolususario", "rol", ("admin", "operador", "visor", "docente")),
]


def aplicar_migraciones_pendientes() -> None:
    """Aplica todas las migraciones idempotentes al arrancar la app.

    Fase 1: columnas nuevas (transaccional via SQLAlchemy).
    Fase 2: valores de rol — maneja tanto enum nativo como VARCHAR+CHECK.
    """
    # Fase 1: columnas (transaccional)
    with engine.begin() as conn:
        for sql in MIGRACIONES_COLUMNAS:
            conn.execute(text(sql))

    # Fase 2: rol enum/check (psycopg2 puro en autocommit)
    _aplicar_migracion_rol()


def _aplicar_migracion_rol() -> None:
    """Migra el campo 'rol' para aceptar el nuevo valor 'docente'.

    Detecta automaticamente si la BD usa:
    - Enum nativo PostgreSQL ('rolususario' en pg_type): ADD VALUE
    - VARCHAR con CHECK constraint: DROP CONSTRAINT (Python valida)
    - VARCHAR sin constraint: no hace nada (ya funciona)

    Usa psycopg2 directo con conn.autocommit = True para evitar cualquier
    transaccion implicita que bloquee el ALTER TYPE ADD VALUE en PostgreSQL.
    """
    import psycopg2

    dsn = (DATABASE_URL or "").replace("postgresql+psycopg2://", "postgresql://")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    try:
        cur = conn.cursor()

        for tabla, tipo_enum, columna, valores in MIGRACIONES_ROL:
            # ----------------------------------------------------------------
            # Caso A: enum nativo PostgreSQL
            # ----------------------------------------------------------------
            cur.execute(
                "SELECT 1 FROM pg_type WHERE typname = %s", (tipo_enum,)
            )
            if cur.fetchone():
                for valor in valores:
                    cur.execute(
                        "SELECT 1 FROM pg_enum e "
                        "JOIN pg_type t ON e.enumtypid = t.oid "
                        "WHERE t.typname = %s AND e.enumlabel = %s",
                        (tipo_enum, valor),
                    )
                    if not cur.fetchone():
                        cur.execute(
                            f"ALTER TYPE {tipo_enum} ADD VALUE '{valor}'"
                        )
                continue

            # ----------------------------------------------------------------
            # Caso B: VARCHAR con CHECK constraint
            # Busca constraints de tipo CHECK sobre la tabla que mencionen
            # la columna, y los elimina si no incluyen todos los valores
            # requeridos. La validacion queda en Python/Pydantic.
            # ----------------------------------------------------------------
            cur.execute(
                "SELECT conname, pg_get_constraintdef(oid) "
                "FROM pg_constraint "
                "WHERE conrelid = %s::regclass AND contype = 'c'",
                (tabla,),
            )
            constraints = cur.fetchall()
            for conname, condef in constraints:
                # Solo tocar constraints que involucren la columna
                if columna not in (condef or ""):
                    continue
                # Si la constraint ya incluye todos los valores requeridos,
                # no hacer nada.
                if all(v in (condef or "") for v in valores):
                    continue
                # DROP: eliminar la constraint restrictiva.
                # Los valores permitidos los controla Python/Pydantic.
                cur.execute(
                    f"ALTER TABLE {tabla} DROP CONSTRAINT IF EXISTS {conname}"
                )

        cur.close()
    finally:
        conn.close()
