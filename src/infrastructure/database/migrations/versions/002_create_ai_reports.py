"""Create ai_reports table

Revision ID: 002
Revises: 001
Create Date: 2025-01-08 12:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, JSONB

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # レポートタイプのEnum型を作成
    report_type_enum = ENUM('pre_event', 'post_event', 'forecast_change', name='report_type_enum')
    report_type_enum.create(op.get_bind())
    
    # ai_reportsテーブルを作成
    op.create_table(
        'ai_reports',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('report_type', report_type_enum, nullable=False),
        sa.Column('report_content', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('usd_jpy_prediction', JSONB, nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(precision=3, scale=2), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['economic_events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # インデックスを作成
    op.create_index('idx_event_id_type', 'ai_reports', ['event_id', 'report_type'])
    op.create_index('idx_report_type_generated', 'ai_reports', ['report_type', 'generated_at'])
    op.create_index('idx_confidence_score', 'ai_reports', ['confidence_score'])
    op.create_index('idx_generated_at', 'ai_reports', ['generated_at'])
    op.create_index(op.f('ix_ai_reports_event_id'), 'ai_reports', ['event_id'])
    op.create_index(op.f('ix_ai_reports_report_type'), 'ai_reports', ['report_type'])


def downgrade() -> None:
    # インデックスを削除
    op.drop_index(op.f('ix_ai_reports_report_type'), table_name='ai_reports')
    op.drop_index(op.f('ix_ai_reports_event_id'), table_name='ai_reports')
    op.drop_index('idx_generated_at', table_name='ai_reports')
    op.drop_index('idx_confidence_score', table_name='ai_reports')
    op.drop_index('idx_report_type_generated', table_name='ai_reports')
    op.drop_index('idx_event_id_type', table_name='ai_reports')
    
    # テーブルを削除
    op.drop_table('ai_reports')
    
    # Enum型を削除
    report_type_enum = ENUM('pre_event', 'post_event', 'forecast_change', name='report_type_enum')
    report_type_enum.drop(op.get_bind())
