"""Create calendar_fetch_logs table

Revision ID: 004
Revises: 003
Create Date: 2025-01-08 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 取得タイプのEnum型を作成
    fetch_type_enum = ENUM(
        'weekly', 'daily', 'realtime',
        name='fetch_type_enum'
    )
    fetch_type_enum.create(op.get_bind())
    
    # 取得ステータスのEnum型を作成
    fetch_status_enum = ENUM(
        'success', 'partial', 'failed',
        name='fetch_status_enum'
    )
    fetch_status_enum.create(op.get_bind())
    
    # calendar_fetch_logsテーブルを作成
    op.create_table(
        'calendar_fetch_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('fetch_type', fetch_type_enum, nullable=False),
        sa.Column('fetch_start', sa.DateTime(), nullable=False),
        sa.Column('fetch_end', sa.DateTime(), nullable=True),
        sa.Column('records_fetched', sa.Integer(), nullable=False, default=0),
        sa.Column('records_updated', sa.Integer(), nullable=False, default=0),
        sa.Column('records_new', sa.Integer(), nullable=False, default=0),
        sa.Column('status', fetch_status_enum, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # インデックスを作成
    op.create_index('idx_fetch_type_start', 'calendar_fetch_logs', ['fetch_type', 'fetch_start'])
    op.create_index('idx_status_created', 'calendar_fetch_logs', ['status', 'created_at'])
    op.create_index(op.f('ix_calendar_fetch_logs_fetch_type'), 'calendar_fetch_logs', ['fetch_type'])
    op.create_index(op.f('ix_calendar_fetch_logs_status'), 'calendar_fetch_logs', ['status'])


def downgrade() -> None:
    # インデックスを削除
    op.drop_index(op.f('ix_calendar_fetch_logs_status'), table_name='calendar_fetch_logs')
    op.drop_index(op.f('ix_calendar_fetch_logs_fetch_type'), table_name='calendar_fetch_logs')
    op.drop_index('idx_status_created', table_name='calendar_fetch_logs')
    op.drop_index('idx_fetch_type_start', table_name='calendar_fetch_logs')
    
    # テーブルを削除
    op.drop_table('calendar_fetch_logs')
    
    # Enum型を削除
    fetch_status_enum = ENUM('success', 'partial', 'failed', name='fetch_status_enum')
    fetch_status_enum.drop(op.get_bind())
    
    fetch_type_enum = ENUM('weekly', 'daily', 'realtime', name='fetch_type_enum')
    fetch_type_enum.drop(op.get_bind())
