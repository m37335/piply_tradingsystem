"""Create economic_events table

Revision ID: 001
Revises: 
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 重要度のEnum型を作成
    importance_enum = ENUM('low', 'medium', 'high', name='importance_enum')
    importance_enum.create(op.get_bind())
    
    # economic_eventsテーブルを作成
    op.create_table(
        'economic_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('date_utc', sa.DateTime(), nullable=False),
        sa.Column('time_utc', sa.Time(), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('zone', sa.String(length=100), nullable=True),
        sa.Column('event_name', sa.Text(), nullable=False),
        sa.Column('importance', importance_enum, nullable=False),
        sa.Column('actual_value', sa.DECIMAL(precision=15, scale=6), nullable=True),
        sa.Column('forecast_value', sa.DECIMAL(precision=15, scale=6), nullable=True),
        sa.Column('previous_value', sa.DECIMAL(precision=15, scale=6), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', name='uq_event_id')
    )
    
    # インデックスを作成
    op.create_index('idx_date_country', 'economic_events', ['date_utc', 'country'])
    op.create_index('idx_importance_date', 'economic_events', ['importance', 'date_utc'])
    op.create_index('idx_event_name', 'economic_events', ['event_name'])
    op.create_index(op.f('ix_economic_events_event_id'), 'economic_events', ['event_id'], unique=True)
    op.create_index(op.f('ix_economic_events_date_utc'), 'economic_events', ['date_utc'])
    op.create_index(op.f('ix_economic_events_country'), 'economic_events', ['country'])
    op.create_index(op.f('ix_economic_events_importance'), 'economic_events', ['importance'])


def downgrade() -> None:
    # インデックスを削除
    op.drop_index(op.f('ix_economic_events_importance'), table_name='economic_events')
    op.drop_index(op.f('ix_economic_events_country'), table_name='economic_events')
    op.drop_index(op.f('ix_economic_events_date_utc'), table_name='economic_events')
    op.drop_index(op.f('ix_economic_events_event_id'), table_name='economic_events')
    op.drop_index('idx_event_name', table_name='economic_events')
    op.drop_index('idx_importance_date', table_name='economic_events')
    op.drop_index('idx_date_country', table_name='economic_events')
    
    # テーブルを削除
    op.drop_table('economic_events')
    
    # Enum型を削除
    importance_enum = ENUM('low', 'medium', 'high', name='importance_enum')
    importance_enum.drop(op.get_bind())
