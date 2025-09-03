"""
Alembic environment configuration
マイグレーション実行環境の設定
"""

import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# パスにプロジェクトルートを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..', '..'))

# モデルのインポート
from src.infrastructure.database.models.economic_event.economic_event_model import EconomicEventModel, Base as EconomicEventBase
from src.infrastructure.database.models.ai_report.ai_report_model import AIReportModel, Base as AIReportBase
from src.infrastructure.database.models.notification_log.notification_log_model import NotificationLogModel, Base as NotificationLogBase

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# メタデータの統合
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# 全てのモデルのテーブルを統合
target_metadata = Base.metadata
for model_class in [EconomicEventModel, AIReportModel, NotificationLogModel]:
    for table in model_class.metadata.tables.values():
        table.tometadata(target_metadata)


def get_database_url():
    """環境変数からデータベースURLを取得"""
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "economic_calendar")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "password")
    
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # 設定からデータベースURLを取得
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_database_url()
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
