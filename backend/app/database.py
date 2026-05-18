from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import logging
import os

load_dotenv()

log = logging.getLogger(__name__)

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
#    -> ALTER TYPE rolususario ADD VALUE IF NOT EXISTS 'docente'
#    -> Requiere AUTOCOMMIT (psycopg2 directo con conn.autocommit = True)
#       En PG 12+ ADD VALUE IF NOT EXISTS es transaccional; en PG <12 no.
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

# Lista de (tabla, tipo_enum, columna, valores_permitidos)
MIGRACIONES_ROL = [
    ("usuarios", "rolususario", "rol", ("admin", "operador", "visor", "docente")),
]


def aplicar_migraciones_pendientes() -> None:
    """Aplica todas las migraciones idempotentes al arrancar la app.

    Fase 1: columnas nuevas (transaccional via SQLAlchemy).
    Fase 2: valores de rol — maneja tanto enum nativo como VARCHAR+CHECK.

    Cualquier error en la migracion de rol se loguea con detalle y
    re-lanza para que el servidor NO arranque con un esquema incompleto.
    """
    # Fase 1: columnas (transaccional)
    with engine.begin() as conn:
        for sql in MIGRACIONES_COLUMNAS:
            conn.execute(text(sql))

    # Fase 2: rol enum/check
    try:
        _aplicar_migracion_rol()
    except Exception as exc:
        log.critical(
            "[Hestia] FALLO EN MIGRACION DE ROL. "
            "El servidor se detiene para evitar inconsistencias. "
            "Ejecuta manualmente en la BD:\n"
            "  ALTER TYPE rolususario ADD VALUE IF NOT EXISTS 'docente';\n"
            "  -- O si usas VARCHAR+CHECK:\n"
            "  ALTER TABLE usuarios DROP CONSTRAINT IF EXISTS usuarios_rol_check;\n"
            "Error original: %s",
            exc,
        )
        raise


def _aplicar_migracion_rol() -> None:
    """Migra el campo 'rol' para aceptar el nuevo valor 'docente'.

    Detecta automaticamente si la BD usa:
    - Enum nativo PostgreSQL ('rolususario' en pg_type): ADD VALUE IF NOT EXISTS
    - VARCHAR con CHECK constraint: DROP CONSTRAINT (Python valida)
    - VARCHAR sin constraint: no hace nada (ya funciona)

    Usa psycopg2 directo con conn.autocommit = True para evitar cualquier
    transaccion implicita que bloquee el ALTER TYPE ADD VALUE en PostgreSQL.

    'IF NOT EXISTS' (Postgres 9.6+) hace la operacion completamente idempotente:
    si el valor ya existe, no lanza error ni hace nada.
    """
    import psycopg2

    # psycopg2 acepta 'postgresql://' pero NO 'postgresql+psycopg2://'
    dsn = (DATABASE_URL or "").replace("postgresql+psycopg2://", "postgresql://")

    log.info("[Hestia] Iniciando migracion de enum 'rol'...")
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    try:
        cur = conn.cursor()

        for tabla, tipo_enum, columna, valores in MIGRACIONES_ROL:
            # ----------------------------------------------------------------
            # Caso A: enum nativo PostgreSQL
            # ADD VALUE IF NOT EXISTS es idempotente (PG 9.6+).
            # ----------------------------------------------------------------
            cur.execute(
                "SELECT 1 FROM pg_type WHERE typname = %s", (tipo_enum,)
            )
            if cur.fetchone():
                log.info(
                    "[Hestia] Enum nativo '%s' detectado — verificando valores...",
                    tipo_enum,
                )
                for valor in valores:
                    cur.execute(
                        "SELECT 1 FROM pg_enum e "
                        "JOIN pg_type t ON e.enumtypid = t.oid "
                        "WHERE t.typname = %s AND e.enumlabel = %s",
                        (tipo_enum, valor),
                    )
                    if not cur.fetchone():
                        log.info(
                            "[Hestia] Agregando valor '%s' al enum '%s'.",
                            valor, tipo_enum,
                        )
                        # IF NOT EXISTS evita error si otra instancia ya lo agrego
                        cur.execute(
                            f"ALTER TYPE {tipo_enum} ADD VALUE IF NOT EXISTS '{valor}'"
                        )
                    else:
                        log.info(
                            "[Hestia] Valor '%s' ya existe en '%s' — sin cambios.",
                            valor, tipo_enum,
                        )
                continue

            # ----------------------------------------------------------------
            # Caso B: VARCHAR con CHECK constraint
            # Busca constraints de tipo CHECK sobre la tabla que mencionen
            # la columna, y los elimina si no incluyen todos los valores
            # requeridos. La validacion queda en Python/Pydantic.
            # ----------------------------------------------------------------
            log.info(
                "[Hestia] No se encontro enum nativo '%s' — revisando CHECK constraints...",
                tipo_enum,
            )
            cur.execute(
                "SELECT conname, pg_get_constraintdef(oid) "
                "FROM pg_constraint "
                "WHERE conrelid = %s::regclass AND contype = 'c'",
                (tabla,),
            )
            constraints = cur.fetchall()
            for conname, condef in constraints:
                if columna not in (condef or ""):
                    continue
                if all(v in (condef or "") for v in valores):
                    log.info(
                        "[Hestia] Constraint '%s' ya incluye todos los valores — sin cambios.",
                        conname,
                    )
                    continue
                log.info(
                    "[Hestia] Eliminando constraint restrictiva '%s' (no incluia todos los roles).",
                    conname,
                )
                cur.execute(
                    f"ALTER TABLE {tabla} DROP CONSTRAINT IF EXISTS {conname}"
                )

        cur.close()
        log.info("[Hestia] Migracion de enum 'rol' completada correctamente.")
    finally:
        conn.close()
