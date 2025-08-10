#!/usr/bin/env python3
"""
監視・ログシステムテストスクリプト
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

from src.infrastructure.monitoring.system_monitor import SystemMonitor
from src.infrastructure.monitoring.log_manager import LogManager
from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class MonitoringSystemTester:
    """
    監視・ログシステムテストクラス
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
        print("Setting up monitoring system test...")
        logger.info("Setting up monitoring system test...")

        # 一時的な設定ファイルを作成
        self.temp_config_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self.temp_config_file.close()

        # テスト用の設定を書き込み
        test_config = {
            "database": {
                "url": "sqlite+aiosqlite:///./test_monitoring.db",
            },
            "logging": {
                "level": "DEBUG",
                "file_path": "./logs/test_monitoring.log",
                "max_file_size": 1048576,
                "backup_count": 3,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
                    "webhook_url": "https://test.discord.com/webhook",
                    "enabled": True,
                },
            },
        }

        import json
        with open(self.temp_config_file.name, "w") as f:
            json.dump(test_config, f, indent=2)

        # 環境変数の設定
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_monitoring.db"
        os.environ["DISCORD_WEBHOOK_URL"] = "https://test.discord.com/webhook"
        os.environ["LOG_LEVEL"] = "DEBUG"

        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager(self.temp_config_file.name)

        print("Monitoring system test setup completed")
        logger.info("Monitoring system test setup completed")

    async def test_log_manager(self):
        """
        ログマネージャーのテスト
        """
        print("Testing log manager...")
        logger.info("Testing log manager...")

        try:
            # ログマネージャーを初期化
            self.log_manager = LogManager(self.config_manager)

            # システムイベントをログに記録
            await self.log_manager.log_system_event(
                "TEST_EVENT", "テストイベント", "INFO", {"test_data": "value"}
            )
            await self.log_manager.log_system_event(
                "ERROR_EVENT", "テストエラー", "ERROR", {"error_code": 500}
            )
            await self.log_manager.log_system_event(
                "WARNING_EVENT", "テスト警告", "WARNING", {"warning_type": "performance"}
            )

            # ログ統計を取得
            stats = await self.log_manager.get_log_statistics(hours=1)
            assert stats["total_entries"] >= 3, f"Expected at least 3 entries, got {stats['total_entries']}"
            assert stats["error_count"] >= 1, f"Expected at least 1 error, got {stats['error_count']}"
            assert stats["warning_count"] >= 1, f"Expected at least 1 warning, got {stats['warning_count']}"

            # ログ検索をテスト
            search_results = await self.log_manager.search_logs("テスト", level="ERROR")
            assert len(search_results) >= 1, "Expected at least 1 error log in search results"

            # エラーサマリーを取得
            error_summary = await self.log_manager.get_error_summary(hours=1)
            assert error_summary["total_errors"] >= 1, "Expected at least 1 error in summary"

            # ログファイル情報を取得
            log_file_info = self.log_manager.get_log_file_info()
            assert log_file_info["exists"], "Log file should exist"

            print("✅ Log manager test passed")
            logger.info("Log manager test passed")

        except Exception as e:
            print(f"❌ Log manager test failed: {e}")
            logger.error(f"Log manager test failed: {e}")
            raise

    async def test_system_monitor(self):
        """
        システムモニターのテスト
        """
        print("Testing system monitor...")
        logger.info("Testing system monitor...")

        try:
            # システムモニターを初期化
            self.system_monitor = SystemMonitor(self.config_manager)

            # システムメトリクスを収集
            await self.system_monitor._collect_system_metrics()

            # システム状態を取得
            status = self.system_monitor.get_system_status()
            assert "cpu_percent" in status["monitoring_data"], "CPU metrics should be collected"
            assert "memory_percent" in status["monitoring_data"], "Memory metrics should be collected"
            assert "disk_percent" in status["monitoring_data"], "Disk metrics should be collected"

            # ヘルスレポートを生成
            health_report = await self.system_monitor.get_health_report()
            assert "system_healthy" in health_report, "Health report should contain system_healthy"
            assert "issues" in health_report, "Health report should contain issues"

            # アラート機能をテスト
            await self.system_monitor._send_alert("TEST_ALERT", "テストアラート")
            assert len(self.system_monitor.alert_history) >= 1, "Alert should be added to history"

            print("✅ System monitor test passed")
            logger.info("System monitor test passed")

        except Exception as e:
            print(f"❌ System monitor test failed: {e}")
            logger.error(f"System monitor test failed: {e}")
            raise

    async def test_monitoring_integration(self):
        """
        監視システム統合テスト
        """
        print("Testing monitoring integration...")
        logger.info("Testing monitoring integration...")

        try:
            # ログマネージャーとシステムモニターを統合
            if not self.log_manager:
                self.log_manager = LogManager(self.config_manager)
            if not self.system_monitor:
                self.system_monitor = SystemMonitor(self.config_manager)

            # システムイベントをログに記録
            await self.log_manager.log_system_event(
                "MONITORING_START", "監視システム開始", "INFO"
            )

            # システムメトリクスを収集
            await self.system_monitor._collect_system_metrics()

            # システム状態をログに記録
            status = self.system_monitor.get_system_status()
            await self.log_manager.log_system_event(
                "SYSTEM_STATUS", 
                f"システム状態: CPU={status['monitoring_data'].get('cpu_percent', 'N/A')}%", 
                "INFO",
                status["monitoring_data"]
            )

            # ヘルスレポートをログに記録
            health_report = await self.system_monitor.get_health_report()
            await self.log_manager.log_system_event(
                "HEALTH_REPORT",
                f"ヘルスレポート: {'正常' if health_report['system_healthy'] else '異常'}",
                "INFO" if health_report["system_healthy"] else "WARNING",
                health_report
            )

            # 統合結果を確認
            stats = await self.log_manager.get_log_statistics(hours=1)
            assert stats["total_entries"] >= 3, "Expected at least 3 log entries from integration"

            print("✅ Monitoring integration test passed")
            logger.info("Monitoring integration test passed")

        except Exception as e:
            print(f"❌ Monitoring integration test failed: {e}")
            logger.error(f"Monitoring integration test failed: {e}")
            raise

    async def test_short_monitoring_run(self):
        """
        短時間監視実行テスト
        """
        print("Testing short monitoring run...")
        logger.info("Testing short monitoring run...")

        try:
            # 監視タスクを作成
            monitoring_task = asyncio.create_task(
                self._run_short_monitoring()
            )

            # 5秒間監視を実行
            await asyncio.sleep(5)

            # 監視を停止
            if self.system_monitor:
                await self.system_monitor.stop_monitoring()

            # タスクが完了するまで待機
            await monitoring_task

            # 監視結果を確認
            status = self.system_monitor.get_system_status()
            assert status["is_running"] == False, "Monitoring should be stopped"

            print("✅ Short monitoring run test passed")
            logger.info("Short monitoring run test passed")

        except Exception as e:
            print(f"❌ Short monitoring run test failed: {e}")
            logger.error(f"Short monitoring run test failed: {e}")
            raise

    async def _run_short_monitoring(self):
        """
        短時間監視を実行
        """
        try:
            if self.system_monitor:
                await self.system_monitor.start_monitoring()
        except asyncio.CancelledError:
            # タスクがキャンセルされた場合
            pass
        except Exception as e:
            logger.error(f"Short monitoring run error: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        try:
            # システムモニターを停止
            if self.system_monitor:
                await self.system_monitor.stop_monitoring()

            # 一時ファイルを削除
            if self.temp_config_file and os.path.exists(self.temp_config_file.name):
                os.unlink(self.temp_config_file.name)

            # テストデータベースを削除
            test_db_path = Path("./test_monitoring.db")
            if test_db_path.exists():
                test_db_path.unlink()

            # テストログファイルを削除
            test_log_path = Path("./logs/test_monitoring.log")
            if test_log_path.exists():
                test_log_path.unlink()

            print("Monitoring system test cleanup completed")
            logger.info("Monitoring system test cleanup completed")

        except Exception as e:
            print(f"Cleanup error: {e}")
            logger.error(f"Cleanup error: {e}")


async def main():
    """
    メイン関数
    """
    print("Starting monitoring system test...")
    logger.info("Starting monitoring system test...")

    tester = MonitoringSystemTester()

    try:
        await tester.setup()

        # 各テストを実行
        await tester.test_log_manager()
        await tester.test_system_monitor()
        await tester.test_monitoring_integration()
        await tester.test_short_monitoring_run()

        print("Monitoring system test completed successfully!")
        logger.info("Monitoring system test completed successfully!")

    except Exception as e:
        print(f"Monitoring system test failed: {e}")
        logger.error(f"Monitoring system test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
