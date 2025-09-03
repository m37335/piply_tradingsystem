"""Create notification_logs table

Revision ID: 003
Revises: 002
Create Date: 2025-01-08 12:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 通知タイプのEnum型を作成
    notification_type_enum = ENUM(
        'new_event', 'forecast_change', 'actual_announcement', 'ai_report',
        name='notification_type_enum'
    )
    notification_type_enum.create(op.get_bind())
    
    # 通知ステータスのEnum型を作成
    notification_status_enum = ENUM(
        'sent', 'failed', 'pending',
        name='notification_status_enum'
    )
    notification_status_enum.create(op.get_bind())
    
    # notification_logsテーブルを作成
    op.create_table(
        'notification_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('notification_type', notification_type_enum, nullable=False),
        sa.Column('discord_message_id', sa.String(length=255), nullable=True),
        sa.Column('message_content', sa.Text(), nullable=True),
        sa.Column('status', notification_status_enum, nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['economic_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # インデックスを作成
    op.create_index('idx_event_notification_type', 'notification_logs', ['event_id', 'notification_type'])
    op.create_index('idx_status_sent_at', 'notification_logs', ['status', 'sent_at'])
    op.create_index('idx_notification_type_created', 'notification_logs', ['notification_type', 'created_at'])
    op.create_index(op.f('ix_notification_logs_event_id'), 'notification_logs', ['event_id'])
    op.create_index(op.f('ix_notification_logs_notification_type'), 'notification_logs', ['notification_type'])


def downgrade() -> None:
    # インデックスを削除
    op.drop_index(op.f('ix_notification_logs_notification_type'), table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_event_id'), table_name='notification_logs')
    op.drop_index('idx_notification_type_created', table_name='notification_logs')
    op.drop_index('idx_status_sent_at', table_name='notification_logs')
    op.drop_index('idx_event_notification_type', table_name='notification_logs')
    
    # テーブルを削除
    op.drop_table('notification_logs')
    
    # Enum型を削除
    notification_status_enum = ENUM('sent', 'failed', 'pending', name='notification_status_enum')
    notification_status_enum.drop(op.get_bind())
    
    notification_type_enum = ENUM(
        'new_event', 'forecast_change', 'actual_announcement', 'ai_report',
        name='notification_type_enum'
    )
    notification_type_enum.drop(op.get_bind())
