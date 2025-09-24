"""
データベース初期化

データベースの初期セットアップとテーブル作成を提供します。
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml
except ImportError:
    yaml = None

from .connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class DatabaseInitializer:
    """データベース初期化"""

    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager

    async def initialize_database(self, database_name: str) -> None:
        """データベースを初期化"""
        try:
            # 1. データベースを作成
            await self.connection_manager.create_database(database_name)

            # 2. 接続プールを初期化
            await self.connection_manager.initialize()

            # 3. TimescaleDB拡張を作成
            await self.connection_manager.create_timescaledb_extension()

            # 4. テーブルを作成
            await self._create_tables()

            # 5. ハイパーテーブルを作成
            await self._create_hypertables()

            # 6. インデックスを作成
            await self._create_indexes()

            # 7. ビューを作成
            await self._create_views()

            logger.info("Database initialization completed successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def _create_tables(self) -> None:
        """テーブルを作成"""
        tables = [
            # 価格データテーブル（TimescaleDB対応）
            """
            CREATE TABLE IF NOT EXISTS price_data (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                timestamp TIMESTAMPTZ NOT NULL,
                open DECIMAL(20, 8) NOT NULL,
                close DECIMAL(20, 8) NOT NULL,
                high DECIMAL(20, 8) NOT NULL,
                low DECIMAL(20, 8) NOT NULL,
                volume BIGINT NOT NULL,
                source TEXT DEFAULT 'yahoo_finance',
                data_quality_score DECIMAL(3,2) DEFAULT 1.0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (symbol, timeframe, timestamp)
            )
            """,
            # データ収集ログテーブル（TimescaleDB対応）
            """
            CREATE TABLE IF NOT EXISTS data_collection_log (
                provider TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                start_time TIMESTAMPTZ NOT NULL,
                end_time TIMESTAMPTZ NOT NULL,
                records_collected INTEGER NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                execution_time_seconds DECIMAL(10, 3),
                created_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (provider, symbol, timeframe, created_at)
            )
            """,
            # LLM分析結果テーブル（TimescaleDB対応）
            """
            CREATE TABLE IF NOT EXISTS llm_analysis_results (
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                analysis_type TEXT NOT NULL,
                analysis_timestamp TIMESTAMPTZ NOT NULL,
                input_data_hash TEXT NOT NULL,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL,
                analysis_result JSONB NOT NULL,
                confidence_score DECIMAL(5, 2),
                processing_time_seconds DECIMAL(10, 3),
                created_at TIMESTAMPTZ DEFAULT NOW(),
                PRIMARY KEY (symbol, timeframe, analysis_type, analysis_timestamp)
            )
            """,
        ]

        for table_sql in tables:
            await self.connection_manager.execute_command(table_sql)

        logger.info("All tables created successfully")

    async def _create_hypertables(self) -> None:
        """ハイパーテーブルを作成"""
        hypertables = [
            ("price_data", "timestamp"),
            ("data_collection_log", "created_at"),
            ("llm_analysis_results", "analysis_timestamp"),
        ]

        for table_name, time_column in hypertables:
            await self.connection_manager.create_hypertable(
                table_name, time_column
            )

        # 時間足別の圧縮設定を最適化
        await self._optimize_compression_settings()

        logger.info("All hypertables created successfully")

    async def _create_indexes(self) -> None:
        """インデックスを作成"""
        indexes = [
            # 基本インデックス
            "CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timeframe ON price_data (symbol, timeframe)",
            "CREATE INDEX IF NOT EXISTS idx_price_data_timestamp ON price_data (timestamp DESC)",
            "CREATE INDEX IF NOT EXISTS idx_price_data_symbol_timestamp ON price_data (symbol, timestamp DESC)",
            # 時間足別の最適化インデックス
            "CREATE INDEX IF NOT EXISTS idx_price_data_5m ON price_data (symbol, timestamp DESC) WHERE timeframe = '5m'",
            "CREATE INDEX IF NOT EXISTS idx_price_data_15m ON price_data (symbol, timestamp DESC) WHERE timeframe = '15m'",
            "CREATE INDEX IF NOT EXISTS idx_price_data_1h ON price_data (symbol, timestamp DESC) WHERE timeframe = '1h'",
            "CREATE INDEX IF NOT EXISTS idx_price_data_4h ON price_data (symbol, timestamp DESC) WHERE timeframe = '4h'",
            "CREATE INDEX IF NOT EXISTS idx_price_data_1d ON price_data (symbol, timestamp DESC) WHERE timeframe = '1d'",
            # LLM分析結果のインデックス
            "CREATE INDEX IF NOT EXISTS idx_llm_analysis_results_symbol ON llm_analysis_results (symbol)",
            "CREATE INDEX IF NOT EXISTS idx_llm_analysis_results_type ON llm_analysis_results (analysis_type)",
            "CREATE INDEX IF NOT EXISTS idx_llm_analysis_results_timestamp ON llm_analysis_results (analysis_timestamp DESC)",
        ]

        for index_sql in indexes:
            await self.connection_manager.execute_command(index_sql)

        logger.info("All indexes created successfully")

    async def _create_views(self) -> None:
        """ビューを作成"""
        views = [
            """
            CREATE OR REPLACE VIEW llm_analysis_summary_view AS
            SELECT 
                symbol,
                timeframe,
                analysis_type,
                COUNT(*) as total_analyses,
                AVG(confidence_score) as avg_confidence,
                MAX(analysis_timestamp) as latest_analysis
            FROM llm_analysis_results
            GROUP BY symbol, timeframe, analysis_type
            """
        ]

        for view_sql in views:
            await self.connection_manager.execute_command(view_sql)

        logger.info("All views created successfully")

    async def _optimize_compression_settings(self) -> None:
        """圧縮設定を最適化"""
        try:
            # 時間足別の圧縮設定
            compression_settings = [
                # 5分足: 1日で圧縮（高頻度データ）
                "SELECT add_compression_policy('price_data', INTERVAL '1 day') WHERE EXISTS (SELECT 1 FROM price_data WHERE timeframe = '5m' LIMIT 1)",
                # 15分足: 3日で圧縮
                "SELECT add_compression_policy('price_data', INTERVAL '3 days') WHERE EXISTS (SELECT 1 FROM price_data WHERE timeframe = '15m' LIMIT 1)",
                # 1時間足: 7日で圧縮
                "SELECT add_compression_policy('price_data', INTERVAL '7 days') WHERE EXISTS (SELECT 1 FROM price_data WHERE timeframe = '1h' LIMIT 1)",
                # 4時間足: 30日で圧縮
                "SELECT add_compression_policy('price_data', INTERVAL '30 days') WHERE EXISTS (SELECT 1 FROM price_data WHERE timeframe = '4h' LIMIT 1)",
                # 日足: 90日で圧縮（長期データ）
                "SELECT add_compression_policy('price_data', INTERVAL '90 days') WHERE EXISTS (SELECT 1 FROM price_data WHERE timeframe = '1d' LIMIT 1)",
            ]

            for setting in compression_settings:
                try:
                    await self.connection_manager.execute_command(setting)
                except Exception as e:
                    logger.warning(f"Compression policy setting failed: {e}")

            # データ保持期間の設定
            retention_settings = [
                "SELECT add_retention_policy('price_data', INTERVAL '2 years')",
                "SELECT add_retention_policy('data_collection_log', INTERVAL '1 year')",
                "SELECT add_retention_policy('llm_analysis_results', INTERVAL '1 year')",
            ]

            for setting in retention_settings:
                try:
                    await self.connection_manager.execute_command(setting)
                except Exception as e:
                    logger.warning(f"Retention policy setting failed: {e}")

            logger.info("Compression and retention policies configured successfully")

        except Exception as e:
            logger.error(f"Failed to optimize compression settings: {e}")
            raise
