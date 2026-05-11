"""Agrega campos TOTP al modelo Usuario para soporte de 2FA.

Revision ID: 0001
Revises: aaf389229667
Create Date: 2026-05-11

Esta migracion es defensiva: verifica si las columnas ya existen antes
de intentar crearlas. Esto es necesario porque las tablas base se crean
mediante Base.metadata.create_all() en crear_admin.py, y en DBs nuevas
el modelo actualizado ya incluye estas columnas desde el inicio.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '0001'
down_revision = 'aaf389229667'  # encadenada despues de la migracion inicial
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    columnas_existentes = {col['name'] for col in inspector.get_columns('usuarios')}

    if 'totp_secret' not in columnas_existentes:
        op.add_column('usuarios', sa.Column('totp_secret', sa.String(), nullable=True))

    if 'totp_habilitado' not in columnas_existentes:
        op.add_column(
            'usuarios',
            sa.Column('totp_habilitado', sa.Boolean(), nullable=False, server_default='false')
        )


def downgrade() -> None:
    op.drop_column('usuarios', 'totp_habilitado')
    op.drop_column('usuarios', 'totp_secret')
