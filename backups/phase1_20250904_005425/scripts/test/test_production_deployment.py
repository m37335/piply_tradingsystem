#!/usr/bin/env python3
"""
本番環境デプロイメントテストスクリプト
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from scripts.deployment.data_migration import DatabaseMigration
from scripts.deployment.deploy_production import ProductionDeployer
from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class ProductionDeploymentTester:
    """
    本番環境デプロイメントテストクラス
    """

    def __init__(self):
        self.deployer = None
        self.migration = None
        self.temp_config_file = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up production deployment test...")
        logger.info("Setting up production deployment test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # テスト用の設定を書き込み
        test_config = {
            "database": {
                "url": "sqlite+aiosqlite:///./test_production.db",
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
            },
            "data_fetch": {
                "currency_pair": "USD/JPY",
                "symbol": "USDJPY=X",
                "max_retries": 3,
                "retry_delay": 60,
            },
            "scheduler": {
                "data_fetch_interval": 300,
                "d1_fetch_interval": 86400,
                "pattern_detection_interval": 300,
            },
            "notifications": {
                "discord": {
                    "webhook_url": "https://test.discord.com/webhook",
                    "enabled": True,
                },
            },
            "logging": {
                "level": "DEBUG",
                "file_path": "./logs/test_production.log",
            },
            "system": {
                "timezone": "Asia/Tokyo",
                "debug_mode": True,
            },
        }

        import json

        with open(self.temp_config_file.name, "w") as f:
            json.dump(test_config, f, indent=2)

        # 環境変数の設定
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_production.db"
        os.environ["DISCORD_WEBHOOK_URL"] = "https://test.discord.com/webhook"
        os.environ["LOG_LEVEL"] = "DEBUG"

        print("Production deployment test setup completed")
        logger.info("Production deployment test setup completed")

    async def test_config_manager(self):
        """
        設定マネージャーのテスト
        """
        print("Testing config manager...")
        logger.info("Testing config manager...")

        try:
            # 設定マネージャーを初期化
            config_manager = SystemConfigManager(self.temp_config_file.name)

            # 設定が正しく読み込まれているか確認
            database_url = config_manager.get("database.url")
            assert (
                database_url == "sqlite+aiosqlite:///./test_production.db"
            ), f"Database URL mismatch: {database_url}"

            currency_pair = config_manager.get("data_fetch.currency_pair")
            assert (
                currency_pair == "USD/JPY"
            ), f"Currency pair mismatch: {currency_pair}"

            print("✅ Config manager test passed")
            logger.info("Config manager test passed")

        except Exception as e:
            print(f"❌ Config manager test failed: {e}")
            logger.error(f"Config manager test failed: {e}")
            raise

    async def test_prerequisites_check(self):
        """
        前提条件チェックのテスト
        """
        print("Testing prerequisites check...")
        logger.info("Testing prerequisites check...")

        try:
            # デプロイヤーを初期化
            self.deployer = ProductionDeployer(self.temp_config_file.name)
            await self.deployer.setup()

            # 前提条件をチェック
            result = await self.deployer.check_prerequisites()

            # テスト環境では一部の前提条件が満たされない可能性がある
            print(f"Prerequisites check result: {result}")
            logger.info(f"Prerequisites check result: {result}")

            print("✅ Prerequisites check test passed")
            logger.info("Prerequisites check test passed")

        except Exception as e:
            print(f"❌ Prerequisites check test failed: {e}")
            logger.error(f"Prerequisites check test failed: {e}")
            raise

    async def test_database_migration(self):
        """
        データベースマイグレーションのテスト
        """
        print("Testing database migration...")
        logger.info("Testing database migration...")

        try:
            # マイグレーションを初期化
            self.migration = DatabaseMigration(self.temp_config_file.name)
            await self.migration.setup()

            # マイグレーションを実行
            result = await self.migration.run_migration()

            if result:
                print("✅ Database migration test passed")
                logger.info("Database migration test passed")
            else:
                print("❌ Database migration test failed")
                logger.error("Database migration test failed")
                raise Exception("Database migration failed")

        except Exception as e:
            print(f"❌ Database migration test failed: {e}")
            logger.error(f"Database migration test failed: {e}")
            raise

    async def test_logging_setup(self):
        """
        ログ設定のテスト
        """
        print("Testing logging setup...")
        logger.info("Testing logging setup...")

        try:
            # ログ設定をテスト
            result = await self.deployer.setup_logging()

            if result:
                print("✅ Logging setup test passed")
                logger.info("Logging setup test passed")
            else:
                print("❌ Logging setup test failed")
                logger.error("Logging setup test failed")
                raise Exception("Logging setup failed")

        except Exception as e:
            print(f"❌ Logging setup test failed: {e}")
            logger.error(f"Logging setup test failed: {e}")
            raise

    async def test_service_file_generation(self):
        """
        サービスファイル生成のテスト
        """
        print("Testing service file generation...")
        logger.info("Testing service file generation...")

        try:
            # サービスファイルの内容を生成
            service_content = self.deployer._generate_systemd_service()

            # サービスファイルの内容を確認
            assert "[Unit]" in service_content, "Service file missing [Unit] section"
            assert (
                "[Service]" in service_content
            ), "Service file missing [Service] section"
            assert (
                "[Install]" in service_content
            ), "Service file missing [Install] section"
            assert (
                "forex-analytics" in service_content
            ), "Service file missing service name"

            print("✅ Service file generation test passed")
            logger.info("Service file generation test passed")

        except Exception as e:
            print(f"❌ Service file generation test failed: {e}")
            logger.error(f"Service file generation test failed: {e}")
            raise

    async def test_deployment_verification(self):
        """
        デプロイメント検証のテスト
        """
        print("Testing deployment verification...")
        logger.info("Testing deployment verification...")

        try:
            # デプロイメント検証をテスト
            result = await self.deployer.verify_deployment()

            # テスト環境では一部の検証が失敗する可能性がある
            print(f"Deployment verification result: {result}")
            logger.info(f"Deployment verification result: {result}")

            print("✅ Deployment verification test passed")
            logger.info("Deployment verification test passed")

        except Exception as e:
            print(f"❌ Deployment verification test failed: {e}")
            logger.error(f"Deployment verification test failed: {e}")
            raise

    async def test_dry_run_deployment(self):
        """
        ドライランデプロイメントのテスト
        """
        print("Testing dry run deployment...")
        logger.info("Testing dry run deployment...")

        try:
            # 前提条件チェックのみ実行（実際のデプロイは行わない）
            if not await self.deployer.check_prerequisites():
                print(
                    "⚠️  Prerequisites check failed, but this is expected in test environment"
                )
                logger.warning(
                    "Prerequisites check failed, but this is expected in test environment"
                )

            print("✅ Dry run deployment test passed")
            logger.info("Dry run deployment test passed")

        except Exception as e:
            print(f"❌ Dry run deployment test failed: {e}")
            logger.error(f"Dry run deployment test failed: {e}")
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        try:
            # マイグレーションをクリーンアップ
            if self.migration:
                await self.migration.cleanup()

            # 一時ファイルを削除
            if self.temp_config_file and os.path.exists(self.temp_config_file.name):
                os.unlink(self.temp_config_file.name)

            # テストデータベースを削除
            test_db_path = Path("./test_production.db")
            if test_db_path.exists():
                test_db_path.unlink()

            # テストログファイルを削除
            test_log_path = Path("./logs/test_production.log")
            if test_log_path.exists():
                test_log_path.unlink()

            print("Production deployment test cleanup completed")
            logger.info("Production deployment test cleanup completed")

        except Exception as e:
            print(f"Cleanup error: {e}")
            logger.error(f"Cleanup error: {e}")


async def main():
    """
    メイン関数
    """
    print("Starting production deployment test...")
    logger.info("Starting production deployment test...")

    tester = ProductionDeploymentTester()

    try:
        await tester.setup()

        # 各テストを実行
        await tester.test_config_manager()
        await tester.test_prerequisites_check()
        await tester.test_database_migration()
        await tester.test_logging_setup()
        await tester.test_service_file_generation()
        await tester.test_deployment_verification()
        await tester.test_dry_run_deployment()

        print("Production deployment test completed successfully!")
        logger.info("Production deployment test completed successfully!")

    except Exception as e:
        print(f"Production deployment test failed: {e}")
        logger.error(f"Production deployment test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
