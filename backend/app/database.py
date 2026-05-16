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
# 2. Valores de ENUM: PostgreSQL prohíbe ALTER TYPE ADD VALUE dentro de
#    cualquier bloque de transaccion, incluso implicito.
#    Ambos enfoques anteriores (execution_options y raw_connection con
#    set_isolation_level) fallaron porque SQLAlchemy 2.x inicia una
#    transaccion implicita antes de que el cambio de isolation surta efecto.
#    Solucion definitiva: conectar con psycopg2 directamente usando la DSN
#    y setear conn.autocommit = True ANTES de cualquier statement. Esto
#    garantiza que no existe ninguna transaccion cuando se ejecuta el ALTER.
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

    Fase 1 — columnas: engine.begin() transaccional. Si falla, rollback
    automatico y la excepcion sube para que el proceso no arranque con
    el esquema a medias.

    Fase 2 — valores de enum: psycopg2 directo con autocommit=True.
    Es la unica forma fiable de ejecutar ALTER TYPE ADD VALUE en PostgreSQL
    independientemente de la version de SQLAlchemy, porque evita cualquier
    transaccion implicita que la capa ORM pueda abrir.
    """
    # Fase 1: columnas (transaccional via SQLAlchemy)
    with engine.begin() as conn:
        for sql in MIGRACIONES_COLUMNAS:
            conn.execute(text(sql))

    # Fase 2: valores de enum (psycopg2 puro en autocommit)
    _aplicar_enum_autocommit()


def _aplicar_enum_autocommit() -> None:
    """Agrega valores faltantes a tipos ENUM usando psycopg2 directo.

    Por que psycopg2 directo y no SQLAlchemy:
    - SQLAlchemy 2.x abre una transaccion implicita en cada conexion antes
      de ejecutar el primer statement, incluso con execution_options o
      set_isolation_level en raw_connection.
    - psycopg2 con conn.autocommit = True establecido ANTES de cualquier
      cursor/execute garantiza que no existe ningun BEGIN implicito cuando
      se corre el ALTER TYPE ADD VALUE.

    El DATABASE_URL de SQLAlchemy usa el prefijo postgresql+psycopg2://
    que psycopg2 no entiende nativamente; se normaliza a postgresql://.
    """
    import psycopg2

    # psycopg2 acepta DSN en formato URL pero sin el driver suffix
    dsn = (DATABASE_URL or "").replace("postgresql+psycopg2://", "postgresql://")

    conn = psycopg2.connect(dsn)
    # CRITICO: autocommit debe setearse ANTES de abrir cualquier cursor
    # o ejecutar cualquier statement. Si se setea despues, puede haber
    # ya una transaccion implicita abierta.
    conn.autocommit = True
    try:
        cur = conn.cursor()
        for tipo, valor in MIGRACIONES_ENUM_VALORES:
            # Si el tipo no existe aun (BD nueva antes de create_all):
            # create_all() lo creara con todos los valores del enum Python.
            cur.execute("SELECT 1 FROM pg_type WHERE typname = %s", (tipo,))
            if not cur.fetchone():
                continue
            # Si el valor ya existe: idempotente, no hacer nada.
            cur.execute(
                "SELECT 1 FROM pg_enum e "
                "JOIN pg_type t ON e.enumtypid = t.oid "
                "WHERE t.typname = %s AND e.enumlabel = %s",
                (tipo, valor),
            )
            if not cur.fetchone():
                # tipo y valor son constantes del codigo, no user input.
                cur.execute(f"ALTER TYPE {tipo} ADD VALUE '{valor}'")
        cur.close()
    finally:
        conn.close()
