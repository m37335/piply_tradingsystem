#!/usr/bin/env python3
"""
システム設定管理テストスクリプト
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.config.system_config_manager import (
    SystemConfigManager,
    get_config,
    get_config_manager,
    set_config,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class SystemConfigManagerTester:
    """
    システム設定管理テストクラス
    """

    def __init__(self):
        self.config_manager = None
        self.temp_config_file = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up system config manager test...")
        logger.info("Setting up system config manager test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # 環境変数の設定
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_config.db"
        os.environ["DISCORD_WEBHOOK_URL"] = "https://test.discord.com/webhook"
        os.environ["LOG_LEVEL"] = "DEBUG"
        os.environ["DEBUG_MODE"] = "true"

        # システム設定管理を初期化
        self.config_manager = SystemConfigManager(self.temp_config_file.name)

        print("System config manager test setup completed")
        logger.info("System config manager test setup completed")

    async def test_config_initialization(self):
        """
        設定初期化のテスト
        """
        print("Testing config initialization...")
        logger.info("Testing config initialization...")

        try:
            # 設定が正しく初期化されているか確認
            assert self.config_manager is not None, "Config manager not initialized"

            # デフォルト設定が読み込まれているか確認
            default_config = self.config_manager.get_all_config()
            assert "database" in default_config, "Database config not found"
            assert "data_fetch" in default_config, "Data fetch config not found"
            assert "scheduler" in default_config, "Scheduler config not found"

            print("✅ Config initialization test passed")
            logger.info("Config initialization test passed")

        except Exception as e:
            print(f"❌ Config initialization test failed: {e}")
            logger.error(f"Config initialization test failed: {e}")
            raise

    async def test_environment_variable_loading(self):
        """
        環境変数読み込みのテスト
        """
        print("Testing environment variable loading...")
        logger.info("Testing environment variable loading...")

        try:
            # 環境変数から読み込まれた設定を確認
            database_url = self.config_manager.get("database.url")
            assert (
                database_url == "sqlite+aiosqlite:///./test_config.db"
            ), f"Database URL mismatch: {database_url}"

            discord_webhook = self.config_manager.get(
                "notifications.discord.webhook_url"
            )
            assert (
                discord_webhook == "https://test.discord.com/webhook"
            ), f"Discord webhook mismatch: {discord_webhook}"

            log_level = self.config_manager.get("logging.level")
            assert log_level == "DEBUG", f"Log level mismatch: {log_level}"

            debug_mode = self.config_manager.get("system.debug_mode")
            assert debug_mode is True, f"Debug mode mismatch: {debug_mode}"

            print("✅ Environment variable loading test passed")
            logger.info("Environment variable loading test passed")

        except Exception as e:
            print(f"❌ Environment variable loading test failed: {e}")
            logger.error(f"Environment variable loading test failed: {e}")
            raise

    async def test_config_get_set(self):
        """
        設定の取得・設定のテスト
        """
        print("Testing config get/set operations...")
        logger.info("Testing config get/set operations...")

        try:
            # 設定値を設定
            self.config_manager.set("test.new_value", "test_value")
            self.config_manager.set("scheduler.data_fetch_interval", 600)

            # 設定値を取得して確認
            test_value = self.config_manager.get("test.new_value")
            assert test_value == "test_value", f"Test value mismatch: {test_value}"

            fetch_interval = self.config_manager.get("scheduler.data_fetch_interval")
            assert fetch_interval == 600, f"Fetch interval mismatch: {fetch_interval}"

            # デフォルト値のテスト
            non_existent = self.config_manager.get("non.existent", "default_value")
            assert (
                non_existent == "default_value"
            ), f"Default value mismatch: {non_existent}"

            print("✅ Config get/set operations test passed")
            logger.info("Config get/set operations test passed")

        except Exception as e:
            print(f"❌ Config get/set operations test failed: {e}")
            logger.error(f"Config get/set operations test failed: {e}")
            raise

    async def test_config_sections(self):
        """
        設定セクションのテスト
        """
        print("Testing config sections...")
        logger.info("Testing config sections...")

        try:
            # 各設定セクションを取得
            database_config = self.config_manager.get_database_config()
            assert "url" in database_config, "Database config missing url"

            data_fetch_config = self.config_manager.get_data_fetch_config()
            assert (
                "currency_pair" in data_fetch_config
            ), "Data fetch config missing currency_pair"

            scheduler_config = self.config_manager.get_scheduler_config()
            assert (
                "data_fetch_interval" in scheduler_config
            ), "Scheduler config missing data_fetch_interval"

            technical_config = self.config_manager.get_technical_indicators_config()
            assert "rsi" in technical_config, "Technical indicators config missing rsi"

            pattern_config = self.config_manager.get_pattern_detection_config()
            assert (
                "confidence_threshold" in pattern_config
            ), "Pattern detection config missing confidence_threshold"

            notifications_config = self.config_manager.get_notifications_config()
            assert (
                "discord" in notifications_config
            ), "Notifications config missing discord"

            logging_config = self.config_manager.get_logging_config()
            assert "level" in logging_config, "Logging config missing level"

            system_config = self.config_manager.get_system_config()
            assert "timezone" in system_config, "System config missing timezone"

            performance_config = self.config_manager.get_performance_config()
            assert (
                "max_memory_usage" in performance_config
            ), "Performance config missing max_memory_usage"

            print("✅ Config sections test passed")
            logger.info("Config sections test passed")

        except Exception as e:
            print(f"❌ Config sections test failed: {e}")
            logger.error(f"Config sections test failed: {e}")
            raise

    async def test_config_validation(self):
        """
        設定検証のテスト
        """
        print("Testing config validation...")
        logger.info("Testing config validation...")

        try:
            # 無効な設定値を設定して検証エラーをテスト
            original_interval = self.config_manager.get("scheduler.data_fetch_interval")

            # 正の値のテスト
            self.config_manager.set("scheduler.data_fetch_interval", 300)
            # エラーが発生しないことを確認

            # 負の値のテスト（検証を無効にして設定）
            self.config_manager.set("scheduler.data_fetch_interval", -1, validate=False)

            # 検証を手動で実行してエラーを確認
            try:
                self.config_manager._validate_config()
                assert False, "Validation should have failed for negative value"
            except ValueError:
                # 期待されるエラー
                pass

            # 元の値に戻す
            self.config_manager.set("scheduler.data_fetch_interval", original_interval)

            print("✅ Config validation test passed")
            logger.info("Config validation test passed")

        except Exception as e:
            print(f"❌ Config validation test failed: {e}")
            logger.error(f"Config validation test failed: {e}")
            raise

    async def test_config_persistence(self):
        """
        設定永続化のテスト
        """
        print("Testing config persistence...")
        logger.info("Testing config persistence...")

        try:
            # 設定を変更
            self.config_manager.set("test.persistence", "persistent_value")

            # 設定をファイルに保存
            self.config_manager.save_config()

            # 新しい設定マネージャーを作成して設定を読み込み
            new_config_manager = SystemConfigManager(self.temp_config_file.name)

            # 保存された設定が正しく読み込まれているか確認
            persisted_value = new_config_manager.get("test.persistence")
            assert (
                persisted_value == "persistent_value"
            ), f"Persisted value mismatch: {persisted_value}"

            print("✅ Config persistence test passed")
            logger.info("Config persistence test passed")

        except Exception as e:
            print(f"❌ Config persistence test failed: {e}")
            logger.error(f"Config persistence test failed: {e}")
            raise

    async def test_config_import_export(self):
        """
        設定インポート・エクスポートのテスト
        """
        print("Testing config import/export...")
        logger.info("Testing config import/export...")

        try:
            # エクスポート用の設定を追加
            self.config_manager.set("test.export", "export_value")

            # 一時的なエクスポートファイルを作成
            export_file = tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            )
            export_file.close()

            # 設定をエクスポート
            self.config_manager.export_config(export_file.name)

            # 新しい設定マネージャーを作成
            import_config_manager = SystemConfigManager()

            # 設定をインポート
            import_config_manager.import_config(export_file.name)

            # インポートされた設定を確認
            imported_value = import_config_manager.get("test.export")
            assert (
                imported_value == "export_value"
            ), f"Imported value mismatch: {imported_value}"

            # 一時ファイルを削除
            os.unlink(export_file.name)

            print("✅ Config import/export test passed")
            logger.info("Config import/export test passed")

        except Exception as e:
            print(f"❌ Config import/export test failed: {e}")
            logger.error(f"Config import/export test failed: {e}")
            raise

    async def test_global_functions(self):
        """
        グローバル関数のテスト
        """
        print("Testing global functions...")
        logger.info("Testing global functions...")

        try:
            # グローバル設定マネージャーを取得
            global_manager = get_config_manager()
            assert global_manager is not None, "Global config manager not initialized"

            # グローバル関数で設定を設定・取得
            set_config("test.global", "global_value")
            global_value = get_config("test.global")
            assert (
                global_value == "global_value"
            ), f"Global value mismatch: {global_value}"

            # デフォルト値のテスト
            default_value = get_config("test.non_existent", "default")
            assert (
                default_value == "default"
            ), f"Global default value mismatch: {default_value}"

            print("✅ Global functions test passed")
            logger.info("Global functions test passed")

        except Exception as e:
            print(f"❌ Global functions test failed: {e}")
            logger.error(f"Global functions test failed: {e}")
            raise

    async def test_config_summary(self):
        """
        設定サマリーのテスト
        """
        print("Testing config summary...")
        logger.info("Testing config summary...")

        try:
            # 設定サマリーを取得
            summary = self.config_manager.get_config_summary()

            # サマリーに必要な項目が含まれているか確認
            assert "database_url" in summary, "Summary missing database_url"
            assert "currency_pair" in summary, "Summary missing currency_pair"
            assert (
                "data_fetch_interval" in summary
            ), "Summary missing data_fetch_interval"
            assert "discord_enabled" in summary, "Summary missing discord_enabled"
            assert "debug_mode" in summary, "Summary missing debug_mode"
            assert "log_level" in summary, "Summary missing log_level"
            assert "timezone" in summary, "Summary missing timezone"

            # 値が正しく設定されているか確認
            assert (
                summary["database_url"] == "sqlite+aiosqlite:///./test_config.db"
            ), f"Summary database_url mismatch: {summary['database_url']}"
            assert (
                summary["currency_pair"] == "USD/JPY"
            ), f"Summary currency_pair mismatch: {summary['currency_pair']}"
            assert (
                summary["log_level"] == "DEBUG"
            ), f"Summary log_level mismatch: {summary['log_level']}"

            print("✅ Config summary test passed")
            logger.info("Config summary test passed")

        except Exception as e:
            print(f"❌ Config summary test failed: {e}")
            logger.error(f"Config summary test failed: {e}")
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.temp_config_file and os.path.exists(self.temp_config_file.name):
            os.unlink(self.temp_config_file.name)
        print("System config manager test cleanup completed")
        logger.info("System config manager test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting system config manager test...")
    logger.info("Starting system config manager test...")

    tester = SystemConfigManagerTester()

    try:
        await tester.setup()

        # 各テストを実行
        await tester.test_config_initialization()
        await tester.test_environment_variable_loading()
        await tester.test_config_get_set()
        await tester.test_config_sections()
        await tester.test_config_validation()
        await tester.test_config_persistence()
        await tester.test_config_import_export()
        await tester.test_global_functions()
        await tester.test_config_summary()

        print("System config manager test completed successfully!")
        logger.info("System config manager test completed successfully!")

    except Exception as e:
        print(f"System config manager test failed: {e}")
        logger.error(f"System config manager test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
