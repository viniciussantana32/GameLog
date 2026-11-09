"""initial migration with usuarios and jogos tables

Revision ID: 001_initial_jogos
Revises: 
Create Date: 2026-11-03 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial_jogos'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Tabela de Usuários / Perfis
    op.create_table(
        'usuarios',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('senha_hash', sa.String(length=255), nullable=False),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_username'), 'usuarios', ['username'], unique=True)
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)

    # 2. Tabela de Jogos
    op.create_table(
        'jogos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('titulo', sa.String(length=150), nullable=False),
        sa.Column('plataforma', sa.String(length=80), nullable=False),
        sa.Column('genero', sa.String(length=80), nullable=True),
        sa.Column('ano_lancamento', sa.Integer(), nullable=True),
        sa.Column('data_zeramento', sa.Date(), nullable=True),
        sa.Column('tempo_jogado_horas', sa.Float(), nullable=True),
        sa.Column('nota', sa.Float(), nullable=True),
        sa.Column('dificuldade', sa.String(length=50), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jogos_titulo'), 'jogos', ['titulo'], unique=False)
    op.create_index(op.f('ix_jogos_plataforma'), 'jogos', ['plataforma'], unique=False)
    op.create_index(op.f('ix_jogos_usuario_id'), 'jogos', ['usuario_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_jogos_usuario_id'), table_name='jogos')
    op.drop_index(op.f('ix_jogos_plataforma'), table_name='jogos')
    op.drop_index(op.f('ix_jogos_titulo'), table_name='jogos')
    op.drop_table('jogos')
    op.drop_index(op.f('ix_usuarios_email'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_username'), table_name='usuarios')
    op.drop_table('usuarios')
