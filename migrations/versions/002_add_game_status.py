"""add explicit status to games

Revision ID: 002_add_game_status
Revises: 001_initial_jogos
Create Date: 2026-11-09 19:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = '002_add_game_status'
down_revision = '001_initial_jogos'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('jogos', sa.Column('status', sa.String(length=20), nullable=True))
    op.execute(
        "UPDATE jogos SET status = 'zerado' WHERE data_zeramento IS NOT NULL"
    )
    op.create_index(
        op.f('ix_jogos_status'),
        'jogos',
        ['status'],
        unique=False
    )


def downgrade():
    op.drop_index(op.f('ix_jogos_status'), table_name='jogos')
    op.drop_column('jogos', 'status')
