#!/usr/bin/env python3
"""
Discord配信機能テストスクリプト
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

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.monitoring.log_manager import LogManager
from src.infrastructure.monitoring.system_monitor import SystemMonitor
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DiscordMonitoringTester:
    """
    Discord配信機能テストクラス
    """

    def __init__(self):
        self.config_manager = None
        self.system_monitor = None
        self.log_manager = None
        self.temp_config_file = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up Discord monitoring test...")
        logger.info("Setting up Discord monitoring test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # 実際のDiscord Webhook URLを設定
        actual_webhook_url = (
            "https://canary.discord.com/api/webhooks/1403643478361116672/"
            "nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ"
        )

        # システム監視用のDiscord Webhook URLを設定
        monitoring_webhook_url = (
            "https://canary.discord.com/api/webhooks/1404124259520876595/"
            "NV4t96suXeoQN6fvOnpKRNpDdBVBESRvChWLp3cZ3TMWuWwJvYX9VfmDWEBzbI9DoX_d"
        )

        # テスト用の設定を書き込み（実際のDiscord Webhook URLを使用）
        test_config = {
            "database": {
                "url": "sqlite+aiosqlite:///./test_discord_monitoring.db",
            },
            "logging": {
                "level": "DEBUG",
                "file_path": "./logs/test_discord_monitoring.log",
                "max_file_size": 1048576,
                "backup_count": 3,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "system": {
                "health_check_interval": 5,
            },
            "performance": {
                "max_cpu_usage": 80.0,
                "max_memory_usage": 2147483648,
            },
            "notifications": {
                "discord": {
                    "webhook_url": actual_webhook_url,
                    "enabled": True,
                },
                "discord_monitoring": {
                    "webhook_url": monitoring_webhook_url,
                    "enabled": True,
                },
            },
        }

        import json

        with open(self.temp_config_file.name, "w") as f:
            json.dump(test_config, f, indent=2)

        # 環境変数の設定
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_discord_monitoring.db"

        # 実際のDiscord Webhook URLを設定
        actual_webhook_url = "https://canary.discord.com/api/webhooks/1403643478361116672/nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ"
        os.environ["DISCORD_WEBHOOK_URL"] = actual_webhook_url

        # システム監視用のDiscord Webhook URLを設定
        monitoring_webhook_url = "https://canary.discord.com/api/webhooks/1404124259520876595/NV4t96suXeoQN6fvOnpKRNpDdBVBESRvChWLp3cZ3TMWuWwJvYX9VfmDWEBzbI9DoX_d"
        os.environ["DISCORD_MONITORING_WEBHOOK_URL"] = monitoring_webhook_url

        os.environ["LOG_LEVEL"] = "DEBUG"

        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager(self.temp_config_file.name)

        print("Discord monitoring test setup completed")
        logger.info("Discord monitoring test setup completed")

    async def test_system_monitor_discord(self):
        """
        システムモニターのDiscord配信テスト
        """
        print("Testing system monitor Discord integration...")
        logger.info("Testing system monitor Discord integration...")

        try:
            # システムモニターを初期化
            self.system_monitor = SystemMonitor(self.config_manager)

            # システムメトリクスを収集
            await self.system_monitor._collect_system_metrics()

            # システム状態をDiscordに送信
            await self.system_monitor.send_system_status_to_discord()
            print("✅ System status sent to Discord")

            # パフォーマンスレポートをDiscordに送信
            await self.system_monitor.send_performance_report_to_discord()
            print("✅ Performance report sent to Discord")

            # アラートをDiscordに送信
            await self.system_monitor._send_alert("TEST_ALERT", "テストアラート")
            print("✅ Alert sent to Discord")

            print("✅ System monitor Discord test passed")
            logger.info("System monitor Discord test passed")

        except Exception as e:
            print(f"❌ System monitor Discord test failed: {e}")
            logger.error(f"System monitor Discord test failed: {e}")
            raise

    async def test_log_manager_discord(self):
        """
        ログマネージャーのDiscord配信テスト
        """
        print("Testing log manager Discord integration...")
        logger.info("Testing log manager Discord integration...")

        try:
            # ログマネージャーを初期化
            self.log_manager = LogManager(self.config_manager)

            # テストログを記録
            await self.log_manager.log_system_event(
                "DISCORD_TEST", "Discord配信テスト", "INFO", {"test": True}
            )
            await self.log_manager.log_system_event(
                "DISCORD_ERROR", "Discord配信エラーテスト", "ERROR", {"error_code": 500}
            )
            await self.log_manager.log_system_event(
                "DISCORD_WARNING",
                "Discord配信警告テスト",
                "WARNING",
                {"warning_type": "test"},
            )

            # ログサマリーをDiscordに送信
            await self.log_manager.send_log_summary_to_discord(hours=1)
            print("✅ Log summary sent to Discord")

            # エラーアラートをDiscordに送信
            await self.log_manager.send_error_alert_to_discord(
                "TEST_ERROR", "テストエラーアラート", {"test_data": "value"}
            )
            print("✅ Error alert sent to Discord")

            print("✅ Log manager Discord test passed")
            logger.info("Log manager Discord test passed")

        except Exception as e:
            print(f"❌ Log manager Discord test failed: {e}")
            logger.error(f"Log manager Discord test failed: {e}")
            raise

    async def test_integrated_discord_monitoring(self):
        """
        統合Discord監視テスト
        """
        print("Testing integrated Discord monitoring...")
        logger.info("Testing integrated Discord monitoring...")

        try:
            # システムモニターとログマネージャーを統合
            if not self.system_monitor:
                self.system_monitor = SystemMonitor(self.config_manager)
            if not self.log_manager:
                self.log_manager = LogManager(self.config_manager)

            # システムイベントをログに記録
            await self.log_manager.log_system_event(
                "DISCORD_INTEGRATION", "Discord統合テスト開始", "INFO"
            )

            # システムメトリクスを収集
            await self.system_monitor._collect_system_metrics()

            # システム状態をログに記録
            status = self.system_monitor.get_system_status()
            await self.log_manager.log_system_event(
                "SYSTEM_STATUS",
                f"システム状態: CPU={status['monitoring_data'].get('cpu_percent', 'N/A')}%",
                "INFO",
                status["monitoring_data"],
            )

            # 統合レポートをDiscordに送信
            await self.system_monitor.send_system_status_to_discord()
            await self.log_manager.send_log_summary_to_discord(hours=1)

            print("✅ Integrated Discord monitoring test passed")
            logger.info("Integrated Discord monitoring test passed")

        except Exception as e:
            print(f"❌ Integrated Discord monitoring test failed: {e}")
            logger.error(f"Integrated Discord monitoring test failed: {e}")
            raise

    async def test_discord_webhook_configuration(self):
        """
        Discord Webhook設定テスト
        """
        print("Testing Discord webhook configuration...")
        logger.info("Testing Discord webhook configuration...")

        try:
            # Webhook URLを取得
            webhook_url = self.config_manager.get("notifications.discord.webhook_url")
            assert webhook_url, "Discord webhook URL should be configured"
            assert (
                "discord.com" in webhook_url
            ), "Webhook URL should be valid Discord URL"

            # 通知設定を確認
            discord_enabled = self.config_manager.get("notifications.discord.enabled")
            assert discord_enabled, "Discord notifications should be enabled"

            print("✅ Discord webhook configuration test passed")
            logger.info("Discord webhook configuration test passed")

        except Exception as e:
            print(f"❌ Discord webhook configuration test failed: {e}")
            logger.error(f"Discord webhook configuration test failed: {e}")
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        try:
            # 一時ファイルを削除
            if self.temp_config_file and os.path.exists(self.temp_config_file.name):
                os.unlink(self.temp_config_file.name)

            # テストデータベースを削除
            test_db_path = Path("./test_discord_monitoring.db")
            if test_db_path.exists():
                test_db_path.unlink()

            # テストログファイルを削除
            test_log_path = Path("./logs/test_discord_monitoring.log")
            if test_log_path.exists():
                test_log_path.unlink()

            print("Discord monitoring test cleanup completed")
            logger.info("Discord monitoring test cleanup completed")

        except Exception as e:
            print(f"Cleanup error: {e}")
            logger.error(f"Cleanup error: {e}")


async def main():
    """
    メイン関数
    """
    print("Starting Discord monitoring test...")
    logger.info("Starting Discord monitoring test...")

    tester = DiscordMonitoringTester()

    try:
        await tester.setup()

        # 各テストを実行
        await tester.test_discord_webhook_configuration()
        await tester.test_system_monitor_discord()
        await tester.test_log_manager_discord()
        await tester.test_integrated_discord_monitoring()

        print("Discord monitoring test completed successfully!")
        logger.info("Discord monitoring test completed successfully!")

    except Exception as e:
        print(f"Discord monitoring test failed: {e}")
        logger.error(f"Discord monitoring test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
