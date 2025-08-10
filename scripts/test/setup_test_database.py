#!/usr/bin/env python3
"""
テスト用データベースセットアップスクリプト

USD/JPY特化のテスト用データベースセットアップスクリプト
実際の運用テスト用のデータベースを準備します

使用方法:
    python scripts/test/setup_test_database.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.database.connection import get_async_session, init_database
    from src.infrastructure.database.models.data_fetch_history_model import (
        DataFetchHistoryModel,
    )
    from src.infrastructure.database.models.pattern_detection_model import (
        PatternDetectionModel,
    )
    from src.infrastructure.database.models.price_data_model import PriceDataModel
    from src.infrastructure.database.models.system_config_model import SystemConfigModel
    from src.infrastructure.database.models.technical_indicator_model import (
        TechnicalIndicatorModel,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class TestDatabaseSetup:
    """
    テスト用データベースセットアップクラス

    責任:
    - テスト用データベースの初期化
    - テーブル作成
    - 初期データ投入
    - テスト環境の準備

    特徴:
    - USD/JPY特化設計
    - テスト用データ投入
    - 安全なセットアップ
    - クリーンアップ機能
    """

    def __init__(self):
        """
        初期化
        """
        self.session = None
        self.database_url = "sqlite+aiosqlite:///./test_app.db"

        logger.info("Initialized TestDatabaseSetup")

    async def setup_test_database(self):
        """
        テスト用データベースをセットアップ
        """
        try:
            logger.info("Setting up test database...")

            # 1. データベース初期化
            await self._initialize_database()

            # 2. テーブル作成
            await self._create_tables()

            # 3. 初期データ投入
            await self._insert_initial_data()

            # 4. セットアップ確認
            await self._verify_setup()

            logger.info("Test database setup completed successfully!")

        except Exception as e:
            logger.error(f"Test database setup failed: {e}")
            raise

    async def _initialize_database(self):
        """
        データベースを初期化
        """
        logger.info("Initializing database...")

        try:
            # データベース初期化
            await init_database(self.database_url, echo=False)

            # セッション取得
            self.session = await get_async_session()

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def _create_tables(self):
        """
        テーブルを作成
        """
        logger.info("Creating tables...")

        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine

            # エンジンを作成（SQLite用設定）
            engine = create_async_engine(
                self.database_url,
                echo=False,
                connect_args=(
                    {"check_same_thread": False}
                    if "sqlite" in self.database_url
                    else {}
                ),
            )

            # 各モデルのテーブルを作成
            models = [
                PriceDataModel,
                TechnicalIndicatorModel,
                PatternDetectionModel,
                DataFetchHistoryModel,
                SystemConfigModel,
            ]

            # メタデータを収集
            from sqlalchemy import MetaData

            metadata = MetaData()

            # メタデータを収集してテーブルを作成
            from sqlalchemy import MetaData

            metadata = MetaData()

            # 全モデルのテーブルをメタデータに追加
            for model in models:
                logger.info(f"Adding table for {model.__name__}")
                # SQLite用にJSONBをTEXTに変更、BigIntegerをIntegerに変更
                from sqlalchemy import Integer, Text

                # モデルのテーブル定義を一時的に修正
                original_columns = {}
                for column_name, column in model.__table__.columns.items():
                    # JSONBをTEXTに変更
                    if hasattr(column.type, "__class__") and "JSONB" in str(
                        column.type.__class__
                    ):
                        original_columns[column_name] = column.type
                        column.type = Text()
                    # BigIntegerをIntegerに変更（SQLite用）
                    elif hasattr(column.type, "__class__") and "BigInteger" in str(
                        column.type.__class__
                    ):
                        original_columns[column_name] = column.type
                        column.type = Integer()

                # テーブルをメタデータに追加
                model.__table__.to_metadata(metadata)

                # 元の型に戻す
                for column_name, original_type in original_columns.items():
                    model.__table__.columns[column_name].type = original_type

            # 全テーブルを作成
            async with engine.begin() as conn:
                await conn.run_sync(metadata.create_all)

            # 基本的なテーブル作成確認
            await self.session.execute(text("SELECT 1"))
            await self.session.commit()

            logger.info("Tables created successfully")

        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise

    async def _insert_initial_data(self):
        """
        初期データを投入
        """
        logger.info("Inserting initial data...")

        try:
            # 1. 価格データの投入
            await self._insert_sample_price_data()

            # 2. テクニカル指標の投入
            await self._insert_sample_indicators()

            # 3. システム設定の投入
            await self._insert_system_configs()

            # 4. データ取得履歴の投入
            await self._insert_sample_fetch_history()

            logger.info("Initial data inserted successfully")

        except Exception as e:
            logger.error(f"Initial data insertion failed: {e}")
            raise

    async def _insert_sample_price_data(self):
        """
        サンプル価格データを投入
        """
        logger.info("Inserting sample price data...")

        try:
            # 過去24時間分のサンプルデータを作成
            base_time = datetime.now() - timedelta(hours=24)

            for i in range(288):  # 5分間隔で24時間 = 288件
                timestamp = base_time + timedelta(minutes=5 * i)

                # SQLite用に直接SQLで挿入
                from sqlalchemy import text

                await self.session.execute(
                    text(
                        """
                        INSERT INTO price_data 
                        (id, currency_pair, timestamp, open_price, high_price, low_price, close_price, volume, data_source, created_at, updated_at, uuid, version)
                        VALUES 
                        (:id, :currency_pair, :timestamp, :open_price, :high_price, :low_price, :close_price, :volume, :data_source, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                    """
                    ),
                    {
                        "id": i + 1,
                        "currency_pair": "USD/JPY",
                        "timestamp": timestamp,
                        "open_price": 150.00 + (i * 0.01),
                        "high_price": 150.05 + (i * 0.01),
                        "low_price": 149.95 + (i * 0.01),
                        "close_price": 150.02 + (i * 0.01),
                        "volume": 1000000 + (i * 1000),
                        "data_source": "Yahoo Finance",
                        "uuid": f"test-uuid-{i}",
                        "version": 1,
                    },
                )

            await self.session.commit()
            logger.info("Sample price data inserted")

        except Exception as e:
            logger.error(f"Sample price data insertion failed: {e}")
            raise

    async def _insert_sample_indicators(self):
        """
        サンプルテクニカル指標を投入
        """
        logger.info("Inserting sample technical indicators...")

        try:
            # 過去24時間分のサンプル指標を作成
            base_time = datetime.now() - timedelta(hours=24)

            for i in range(288):  # 5分間隔で24時間 = 288件
                timestamp = base_time + timedelta(minutes=5 * i)

                # RSI指標を直接SQLで挿入
                import json

                from sqlalchemy import text

                await self.session.execute(
                    text(
                        """
                        INSERT INTO technical_indicators 
                        (id, currency_pair, timestamp, indicator_type, timeframe, value, additional_data, parameters, created_at, updated_at, uuid, version)
                        VALUES 
                        (:id, :currency_pair, :timestamp, :indicator_type, :timeframe, :value, :additional_data, :parameters, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                    """
                    ),
                    {
                        "id": (i * 2) + 1,
                        "currency_pair": "USD/JPY",
                        "timestamp": timestamp,
                        "indicator_type": "RSI",
                        "timeframe": "5m",
                        "value": 50.0 + (i % 40),
                        "additional_data": json.dumps({"period": 14}),
                        "parameters": json.dumps({"period": 14}),
                        "uuid": f"rsi-uuid-{i}",
                        "version": 1,
                    },
                )

                # MACD指標を直接SQLで挿入
                await self.session.execute(
                    text(
                        """
                        INSERT INTO technical_indicators 
                        (id, currency_pair, timestamp, indicator_type, timeframe, value, additional_data, parameters, created_at, updated_at, uuid, version)
                        VALUES 
                        (:id, :currency_pair, :timestamp, :indicator_type, :timeframe, :value, :additional_data, :parameters, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                    """
                    ),
                    {
                        "id": (i * 2) + 2,
                        "currency_pair": "USD/JPY",
                        "timestamp": timestamp,
                        "indicator_type": "MACD",
                        "timeframe": "5m",
                        "value": 0.001 + (i * 0.0001),
                        "additional_data": json.dumps(
                            {
                                "macd_line": 0.001 + (i * 0.0001),
                                "signal_line": 0.0005 + (i * 0.0001),
                                "histogram": 0.0005 + (i * 0.0001),
                            }
                        ),
                        "parameters": json.dumps(
                            {
                                "fast_period": 12,
                                "slow_period": 26,
                                "signal_period": 9,
                            }
                        ),
                        "uuid": f"macd-uuid-{i}",
                        "version": 1,
                    },
                )

            await self.session.commit()
            logger.info("Sample technical indicators inserted")

        except Exception as e:
            logger.error(f"Sample indicators insertion failed: {e}")
            raise

    async def _insert_system_configs(self):
        """
        システム設定を投入
        """
        logger.info("Inserting system configurations...")

        try:
            # 基本的なシステム設定
            configs = [
                SystemConfigModel(
                    config_key="data_fetch_interval_minutes",
                    config_category="data_fetch",
                    config_value={"interval_minutes": 5},
                    config_type="integer",
                    description="データ取得間隔（分）",
                ),
                SystemConfigModel(
                    config_key="technical_indicators_enabled",
                    config_category="analysis",
                    config_value={"enabled": True},
                    config_type="boolean",
                    description="テクニカル指標計算有効化",
                ),
                SystemConfigModel(
                    config_key="pattern_detection_enabled",
                    config_category="analysis",
                    config_value={"enabled": True},
                    config_type="boolean",
                    description="パターン検出有効化",
                ),
                SystemConfigModel(
                    config_key="notification_enabled",
                    config_category="notification",
                    config_value={"enabled": True},
                    config_type="boolean",
                    description="通知機能有効化",
                ),
                SystemConfigModel(
                    config_key="data_retention_days",
                    config_category="data_management",
                    config_value={"retention_days": 90},
                    config_type="integer",
                    description="データ保持期間（日）",
                ),
            ]

            # システム設定を直接SQLで挿入
            import json

            from sqlalchemy import text

            for i, config in enumerate(configs):
                await self.session.execute(
                    text(
                        """
                        INSERT INTO system_config 
                        (id, config_key, config_category, config_value, description, is_active, config_type, default_value, validation_rules, created_at, updated_at, uuid, version)
                        VALUES 
                        (:id, :config_key, :config_category, :config_value, :description, :is_active, :config_type, :default_value, :validation_rules, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                    """
                    ),
                    {
                        "id": i + 1,
                        "config_key": config.config_key,
                        "config_category": config.config_category,
                        "config_value": json.dumps(config.config_value),
                        "description": config.description,
                        "is_active": config.is_active,
                        "config_type": config.config_type,
                        "default_value": (
                            json.dumps(config.default_value)
                            if config.default_value
                            else "{}"
                        ),
                        "validation_rules": "{}",
                        "uuid": f"config-uuid-{i}",
                        "version": 1,
                    },
                )

            await self.session.commit()
            logger.info("System configurations inserted")

        except Exception as e:
            logger.error(f"System configs insertion failed: {e}")
            raise

    async def _insert_sample_fetch_history(self):
        """
        サンプルデータ取得履歴を投入
        """
        logger.info("Inserting sample fetch history...")

        try:
            # 過去24時間分のサンプル履歴を作成
            base_time = datetime.now() - timedelta(hours=24)

            for i in range(288):  # 5分間隔で24時間 = 288件
                timestamp = base_time + timedelta(minutes=5 * i)

                # データ取得履歴を直接SQLで挿入
                from sqlalchemy import text

                await self.session.execute(
                    text(
                        """
                        INSERT INTO data_fetch_history 
                        (id, currency_pair, fetch_timestamp, data_source, fetch_type, success, response_time_ms, http_status_code, data_count, cache_used, created_at, updated_at, uuid, version)
                        VALUES 
                        (:id, :currency_pair, :fetch_timestamp, :data_source, :fetch_type, :success, :response_time_ms, :http_status_code, :data_count, :cache_used, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, :uuid, :version)
                    """
                    ),
                    {
                        "id": i + 1,
                        "currency_pair": "USD/JPY",
                        "fetch_timestamp": timestamp,
                        "data_source": "Yahoo Finance",
                        "fetch_type": "price_data",
                        "success": True,
                        "response_time_ms": int((0.5 + (i * 0.01)) * 1000),
                        "http_status_code": 200,
                        "data_count": 1,
                        "cache_used": False,
                        "uuid": f"fetch-uuid-{i}",
                        "version": 1,
                    },
                )

            await self.session.commit()
            logger.info("Sample fetch history inserted")

        except Exception as e:
            logger.error(f"Sample fetch history insertion failed: {e}")
            raise

    async def _verify_setup(self):
        """
        セットアップを確認
        """
        logger.info("Verifying setup...")

        try:
            from sqlalchemy import text

            # 各テーブルのレコード数を確認
            tables = [
                "price_data",
                "technical_indicators",
                "system_config",
                "data_fetch_history",
            ]

            for table in tables:
                result = await self.session.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                count = result.scalar()
                logger.info(f"Table {table}: {count} records")

            logger.info("Setup verification completed")

        except Exception as e:
            logger.error(f"Setup verification failed: {e}")
            raise

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Test database setup cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting test database setup...")

    # 環境変数の設定（テスト用）
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"
        logger.info("Set default DATABASE_URL for testing")

    if not os.getenv("DISCORD_WEBHOOK_URL"):
        os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test"
        logger.info("Set default DISCORD_WEBHOOK_URL for testing")

    if not os.getenv("YAHOO_FINANCE_API_KEY"):
        os.environ["YAHOO_FINANCE_API_KEY"] = "test_api_key"
        logger.info("Set default YAHOO_FINANCE_API_KEY for testing")

    setup = TestDatabaseSetup()

    try:
        # テスト用データベースセットアップ実行
        await setup.setup_test_database()

        logger.info("Test database setup completed successfully!")

    except Exception as e:
        logger.error(f"Test database setup failed: {e}")
        sys.exit(1)
    finally:
        await setup.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
