#!/usr/bin/env python3
"""
本番環境設定スクリプト

USD/JPY特化の本番環境設定スクリプト
設計書参照: /app/note/database_implementation_design_2025.md

使用方法:
    python scripts/deployment/production_setup.py
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.data_cleanup_service import (
        DataCleanupService,
    )
    from src.infrastructure.database.services.system_config_service import (
        SystemConfigService,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class ProductionSetup:
    """
    本番環境設定クラス

    責任:
    - データベース設定
    - 環境変数設定
    - ログ設定
    - セキュリティ設定

    特徴:
    - USD/JPY特化設計
    - 包括的設定管理
    - 安全性重視
    - 監視機能
    """

    def __init__(self):
        """
        初期化
        """
        self.session = None
        self.config_service = None
        self.cleanup_service = None

        # 本番環境設定
        self.production_config = {
            "environment": "production",
            "currency_pair": "USD/JPY",
            "data_fetch_interval_minutes": 5,
            "technical_analysis_interval_minutes": 10,
            "data_retention_days": 90,
            "min_confidence_threshold": 0.7,
            "min_priority_threshold": 70,
            "max_notifications_per_run": 5,
            "duplicate_check_window_hours": 1,
        }

        logger.info("Initialized ProductionSetup")

    async def setup_production_environment(self):
        """
        本番環境を設定
        """
        try:
            logger.info("Setting up production environment...")

            # 1. 環境変数チェック
            await self._check_environment_variables()

            # 2. データベース接続テスト
            await self._test_database_connection()

            # 3. システム設定初期化
            await self._initialize_system_configs()

            # 4. データベース最適化
            await self._optimize_database()

            # 5. セキュリティ設定
            await self._setup_security()

            # 6. 監視設定
            await self._setup_monitoring()

            logger.info("Production environment setup completed successfully")

        except Exception as e:
            logger.error(f"Error setting up production environment: {e}")
            raise

    async def _check_environment_variables(self):
        """
        環境変数をチェック
        """
        logger.info("Checking environment variables...")

        required_vars = [
            "DATABASE_URL",
            "DISCORD_WEBHOOK_URL",
            "YAHOO_FINANCE_API_KEY",
            "LOG_LEVEL",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            error_msg = f"Missing required environment variables: {missing_vars}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("All required environment variables are set")

    async def _test_database_connection(self):
        """
        データベース接続をテスト
        """
        logger.info("Testing database connection...")

        try:
            # セッション取得
            self.session = await get_async_session().__anext__()

            # 接続テスト
            await self.session.execute("SELECT 1")
            await self.session.commit()

            logger.info("Database connection test successful")

        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise

    async def _initialize_system_configs(self):
        """
        システム設定を初期化
        """
        logger.info("Initializing system configurations...")

        try:
            # 設定サービス初期化
            self.config_service = SystemConfigService(self.session)

            # デフォルト設定を初期化
            await self.config_service.initialize_default_configs()

            # 本番環境設定を適用
            for key, value in self.production_config.items():
                if key != "environment" and key != "currency_pair":
                    await self.config_service.set_config(key, value)

            logger.info("System configurations initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing system configs: {e}")
            raise

    async def _optimize_database(self):
        """
        データベースを最適化
        """
        logger.info("Optimizing database...")

        try:
            # クリーンアップサービス初期化
            self.cleanup_service = DataCleanupService(self.session)

            # データ統計を取得
            stats = await self.cleanup_service.get_data_statistics()
            logger.info(f"Database statistics: {stats}")

            # クリーンアップ影響を推定
            impact = await self.cleanup_service.estimate_cleanup_impact()
            logger.info(f"Cleanup impact estimation: {impact}")

            logger.info("Database optimization completed")

        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            raise

    async def _setup_security(self):
        """
        セキュリティ設定
        """
        logger.info("Setting up security configurations...")

        try:
            # セキュリティ関連設定
            security_configs = {
                "max_retry_attempts": 3,
                "rate_limit_per_minute": 60,
                "session_timeout_minutes": 30,
                "enable_ssl": True,
                "enable_audit_logging": True,
            }

            for key, value in security_configs.items():
                await self.config_service.set_config(key, value)

            logger.info("Security configurations set successfully")

        except Exception as e:
            logger.error(f"Error setting up security: {e}")
            raise

    async def _setup_monitoring(self):
        """
        監視設定
        """
        logger.info("Setting up monitoring configurations...")

        try:
            # 監視関連設定
            monitoring_configs = {
                "enable_health_checks": True,
                "health_check_interval_seconds": 300,
                "enable_performance_monitoring": True,
                "enable_error_tracking": True,
                "alert_threshold_error_rate": 0.05,
                "alert_threshold_response_time_ms": 5000,
            }

            for key, value in monitoring_configs.items():
                await self.config_service.set_config(key, value)

            logger.info("Monitoring configurations set successfully")

        except Exception as e:
            logger.error(f"Error setting up monitoring: {e}")
            raise

    async def verify_production_setup(self):
        """
        本番環境設定を検証
        """
        logger.info("Verifying production setup...")

        try:
            # 1. 設定値の検証
            await self._verify_configurations()

            # 2. データベース接続の検証
            await self._verify_database_connection()

            # 3. サービスの検証
            await self._verify_services()

            logger.info("Production setup verification completed successfully")

        except Exception as e:
            logger.error(f"Error verifying production setup: {e}")
            raise

    async def _verify_configurations(self):
        """
        設定値を検証
        """
        logger.info("Verifying configurations...")

        try:
            # 全設定を取得
            configs = await self.config_service.get_all_configs()

            # 重要な設定をチェック
            important_configs = [
                "data_fetch_interval_minutes",
                "technical_indicators_enabled",
                "pattern_detection_enabled",
                "notification_enabled",
                "data_retention_days",
            ]

            for config_key in important_configs:
                if config_key not in configs:
                    raise ValueError(f"Missing important config: {config_key}")

            logger.info("Configuration verification completed")

        except Exception as e:
            logger.error(f"Error verifying configurations: {e}")
            raise

    async def _verify_database_connection(self):
        """
        データベース接続を検証
        """
        logger.info("Verifying database connection...")

        try:
            # 接続テスト
            await self.session.execute("SELECT 1")
            await self.session.commit()

            logger.info("Database connection verification completed")

        except Exception as e:
            logger.error(f"Error verifying database connection: {e}")
            raise

    async def _verify_services(self):
        """
        サービスを検証
        """
        logger.info("Verifying services...")

        try:
            # 設定サービス統計
            config_stats = await self.config_service.get_system_statistics()
            logger.info(f"Config service stats: {config_stats}")

            # クリーンアップサービス統計
            cleanup_stats = await self.cleanup_service.get_data_statistics()
            logger.info(f"Cleanup service stats: {cleanup_stats}")

            logger.info("Service verification completed")

        except Exception as e:
            logger.error(f"Error verifying services: {e}")
            raise

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Production setup cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting production environment setup...")

    setup = ProductionSetup()

    try:
        # 本番環境設定
        await setup.setup_production_environment()

        # 設定検証
        await setup.verify_production_setup()

        logger.info("Production environment setup completed successfully!")

    except Exception as e:
        logger.error(f"Production setup failed: {e}")
        sys.exit(1)
    finally:
        await setup.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
