"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'datasets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('label_names', postgresql.JSONB(), nullable=False),
        sa.Column('records_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        comment='Загруженные датасеты с эталонными полями.',
    )
    op.create_index('ix_datasets_created_at', 'datasets', ['created_at'])

    op.create_table(
        'dataset_records',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=256), nullable=False),
        sa.Column('fields', postgresql.JSONB(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='Эталонные записи датасета (id + поля по меткам).',
    )
    op.create_index('ix_dataset_records_dataset_id', 'dataset_records', ['dataset_id'])

    op.create_table(
        'models',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=256), nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('label_names', postgresql.JSONB(), nullable=False),
        sa.Column('artifact_path', sa.String(length=512), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='Реестр обученных NER-моделей.',
    )
    op.create_index('ix_models_created_at', 'models', ['created_at'])
    op.create_index('ix_models_dataset_id', 'models', ['dataset_id'])

    op.create_table(
        'training_jobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('samples_per_record', sa.Integer(), nullable=False),
        sa.Column('metrics', postgresql.JSONB(), nullable=True),
        sa.Column('model_id', sa.Integer(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.id']),
        sa.ForeignKeyConstraint(['model_id'], ['models.id']),
        sa.PrimaryKeyConstraint('id'),
        comment='Задачи обучения NER-моделей.',
    )
    op.create_index('ix_training_jobs_created_at', 'training_jobs', ['created_at'])
    op.create_index('ix_training_jobs_dataset_id', 'training_jobs', ['dataset_id'])


def downgrade() -> None:
    op.drop_table('training_jobs')
    op.drop_table('models')
    op.drop_table('dataset_records')
    op.drop_table('datasets')
