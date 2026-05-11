#!/bin/sh
# =============================================================================
# Hestia — Script de arranque del contenedor
#
# Este script corre automáticamente al levantar el contenedor con Docker.
# Orden de ejecución:
#   1. Alembic aplica las migraciones pendientes (crea/actualiza tablas)
#   2. crear_admin.py crea el usuario admin si no existe
#   3. Uvicorn levanta la API
#
# Si cualquiera de los pasos falla, el contenedor se detiene.
# =============================================================================

set -e   # Detener si cualquier comando falla

echo "[Hestia] Aplicando migraciones..."
alembic upgrade head

echo "[Hestia] Ejecutando seed de admin..."
python crear_admin.py

echo "[Hestia] Levantando API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
