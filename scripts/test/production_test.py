#!/usr/bin/env python3
"""
本番運用テストスクリプト

USD/JPY特化の本番運用テストスクリプト
実際の運用環境での動作確認を行います

使用方法:
    python scripts/test/production_test.py
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
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.data_cleanup_service import (
        DataCleanupService,
    )
    from src.infrastructure.database.services.data_fetcher_service import (
        DataFetcherService,
    )
    from src.infrastructure.database.services.notification_integration_service import (
        NotificationIntegrationService,
    )
    from src.infrastructure.database.services.pattern_detection_service import (
        PatternDetectionService,
    )
    from src.infrastructure.database.services.system_config_service import (
        SystemConfigService,
    )
    from src.infrastructure.database.services.technical_indicator_service import (
        TechnicalIndicatorService,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class ProductionTest:
    """
    本番運用テストクラス

    責任:
    - 環境チェック
    - 段階的テスト実行
    - 実際のデータ取得テスト
    - システム統合テスト

    特徴:
    - USD/JPY特化設計
    - 段階的テスト実行
    - 詳細な結果報告
    - 安全性重視
    """

    def __init__(self):
        """
        初期化
        """
        self.session = None
        self.services = {}
        self.test_results = []

        # テスト設定
        self.test_config = {
            "currency_pair": "USD/JPY",
            "test_duration_minutes": 10,
            "max_test_retries": 3,
            "enable_notifications": False,  # テスト時は無効
        }

        logger.info("Initialized ProductionTest")

    async def run_full_production_test(self):
        """
        完全な本番運用テストを実行
        """
        try:
            logger.info("=== Starting Full Production Test ===")

            # 1. 環境チェック
            await self._test_environment()

            # 2. データベース接続テスト
            await self._test_database_connection()

            # 3. サービス初期化テスト
            await self._test_service_initialization()

            # 4. データ取得テスト
            await self._test_data_fetching()

            # 5. テクニカル指標計算テスト
            await self._test_technical_indicators()

            # 6. パターン検出テスト
            await self._test_pattern_detection()

            # 7. 通知システムテスト
            await self._test_notification_system()

            # 8. 設定管理テスト
            await self._test_configuration_management()

            # 9. データクリーンアップテスト
            await self._test_data_cleanup()

            # 10. 統合テスト
            await self._test_integration()

            # テスト結果レポート
            await self._generate_test_report()

            logger.info("=== Full Production Test Completed Successfully ===")

        except Exception as e:
            logger.error(f"Production test failed: {e}")
            await self._handle_test_failure(e)
            raise

    async def _test_environment(self):
        """
        環境をテスト
        """
        logger.info("--- Testing Environment ---")

        try:
            # 必要な環境変数チェック
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
                self._record_test_result("Environment Check", "FAILED", error_msg)
                raise ValueError(error_msg)

            # ディレクトリ権限チェック
            required_dirs = ["logs", "data", "config"]
            for dir_name in required_dirs:
                dir_path = Path(dir_name)
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created directory: {dir_name}")

            self._record_test_result("Environment Check", "PASSED")
            logger.info("Environment check passed")

        except Exception as e:
            self._record_test_result("Environment Check", "FAILED", str(e))
            raise

    async def _test_database_connection(self):
        """
        データベース接続をテスト
        """
        logger.info("--- Testing Database Connection ---")

        try:
            # データベースセッション作成
            self.session = await get_async_session()

            # 接続テスト
            from sqlalchemy import text

            await self.session.execute(text("SELECT 1"))
            await self.session.commit()

            self._record_test_result("Database Connection", "PASSED")
            logger.info("Database connection test passed")

        except Exception as e:
            self._record_test_result("Database Connection", "FAILED", str(e))
            logger.error(f"Database connection test failed: {e}")
            raise

    async def _test_service_initialization(self):
        """
        サービス初期化をテスト
        """
        logger.info("--- Testing Service Initialization ---")

        try:
            # サービス初期化
            self.services = {
                "data_fetcher": DataFetcherService(self.session),
                "indicator_service": TechnicalIndicatorService(self.session),
                "pattern_service": PatternDetectionService(self.session),
                "notification_service": NotificationIntegrationService(self.session),
                "config_service": SystemConfigService(self.session),
                "cleanup_service": DataCleanupService(self.session),
            }

            # 各サービスの初期化確認
            for service_name, service in self.services.items():
                logger.info(f"Initialized {service_name}")

            self._record_test_result("Service Initialization", "PASSED")
            logger.info("Service initialization test passed")

        except Exception as e:
            self._record_test_result("Service Initialization", "FAILED", str(e))
            logger.error(f"Service initialization test failed: {e}")
            raise

    async def _test_data_fetching(self):
        """
        データ取得をテスト
        """
        logger.info("--- Testing Data Fetching ---")

        try:
            # 最新の価格データを取得
            latest_data_list = await self.services[
                "data_fetcher"
            ].get_latest_price_data()

            if latest_data_list:
                latest_data = latest_data_list[0]
                logger.info(f"Latest price data: {latest_data.timestamp}")
            else:
                logger.info("No existing price data found")

            # 新しいデータを取得（テスト用）
            logger.info("Fetching new price data...")
            new_data = await self.services["data_fetcher"].fetch_current_price_data()

            if new_data:
                logger.info(f"Successfully fetched new data: {new_data.timestamp}")
            else:
                logger.warning("No new data fetched")

            self._record_test_result("Data Fetching", "PASSED")
            logger.info("Data fetching test passed")

        except Exception as e:
            self._record_test_result("Data Fetching", "FAILED", str(e))
            logger.error(f"Data fetching test failed: {e}")
            raise

    async def _test_technical_indicators(self):
        """
        テクニカル指標計算をテスト
        """
        logger.info("--- Testing Technical Indicators ---")

        try:
            # 5分間隔の指標を計算
            logger.info("Calculating technical indicators for 5m timeframe...")
            indicators_5m = await self.services[
                "indicator_service"
            ].calculate_all_indicators(timeframe="5m")

            if indicators_5m:
                logger.info(f"Calculated {len(indicators_5m)} indicators for 5m")
            else:
                logger.info("No indicators calculated for 5m")

            # 1時間間隔の指標を計算
            logger.info("Calculating technical indicators for 1h timeframe...")
            indicators_1h = await self.services[
                "indicator_service"
            ].calculate_all_indicators(timeframe="1h")

            if indicators_1h:
                logger.info(f"Calculated {len(indicators_1h)} indicators for 1h")
            else:
                logger.info("No indicators calculated for 1h")

            self._record_test_result("Technical Indicators", "PASSED")
            logger.info("Technical indicators test passed")

        except Exception as e:
            self._record_test_result("Technical Indicators", "FAILED", str(e))
            logger.error(f"Technical indicators test failed: {e}")
            raise

    async def _test_pattern_detection(self):
        """
        パターン検出をテスト
        """
        logger.info("--- Testing Pattern Detection ---")

        try:
            # パターン検出を実行
            logger.info("Running pattern detection...")
            patterns = await self.services["pattern_service"].detect_all_patterns()

            if patterns:
                logger.info(f"Detected {len(patterns)} patterns")
                for pattern in patterns[:3]:  # 最初の3つを表示
                    logger.info(
                        f"Pattern: {pattern.pattern_name} - Confidence: {pattern.confidence}"
                    )
            else:
                logger.info("No patterns detected")

            self._record_test_result("Pattern Detection", "PASSED")
            logger.info("Pattern detection test passed")

        except Exception as e:
            self._record_test_result("Pattern Detection", "FAILED", str(e))
            logger.error(f"Pattern detection test failed: {e}")
            raise

    async def _test_notification_system(self):
        """
        通知システムをテスト
        """
        logger.info("--- Testing Notification System ---")

        try:
            if not self.test_config["enable_notifications"]:
                logger.info("Notifications disabled for testing")
                self._record_test_result(
                    "Notification System", "SKIPPED", "Disabled for testing"
                )
                return

            # 通知システムテスト
            logger.info("Testing notification system...")
            test_result = await self.services[
                "notification_service"
            ].test_notification_system()

            if test_result:
                logger.info("Notification system test successful")
                self._record_test_result("Notification System", "PASSED")
            else:
                logger.warning("Notification system test failed")
                self._record_test_result(
                    "Notification System", "FAILED", "Test returned False"
                )

        except Exception as e:
            self._record_test_result("Notification System", "FAILED", str(e))
            logger.error(f"Notification system test failed: {e}")

    async def _test_configuration_management(self):
        """
        設定管理をテスト
        """
        logger.info("--- Testing Configuration Management ---")

        try:
            # 設定の取得
            configs = await self.services["config_service"].get_all_configs()

            if configs:
                logger.info(f"Retrieved {len(configs)} configurations")

                # 重要な設定をチェック
                important_configs = [
                    "data_fetch_interval_minutes",
                    "technical_indicators_enabled",
                    "pattern_detection_enabled",
                    "notification_enabled",
                ]

                for config_key in important_configs:
                    if config_key in configs:
                        logger.info(f"Config {config_key}: {configs[config_key]}")
                    else:
                        logger.warning(f"Missing config: {config_key}")

            else:
                logger.warning("No configurations found")

            self._record_test_result("Configuration Management", "PASSED")
            logger.info("Configuration management test passed")

        except Exception as e:
            self._record_test_result("Configuration Management", "FAILED", str(e))
            logger.error(f"Configuration management test failed: {e}")
            raise

    async def _test_data_cleanup(self):
        """
        データクリーンアップをテスト
        """
        logger.info("--- Testing Data Cleanup ---")

        try:
            # データ統計を取得
            stats = await self.services["cleanup_service"].get_data_statistics()

            if stats:
                logger.info("Current data statistics:")
                for table, count in stats.items():
                    logger.info(f"  {table}: {count} records")

            # クリーンアップ影響を推定（ドライラン）
            impact = await self.services["cleanup_service"].estimate_cleanup_impact()

            if impact:
                logger.info("Cleanup impact estimation:")
                for table, count in impact.items():
                    logger.info(f"  {table}: {count} records would be deleted")

            self._record_test_result("Data Cleanup", "PASSED")
            logger.info("Data cleanup test passed")

        except Exception as e:
            self._record_test_result("Data Cleanup", "FAILED", str(e))
            logger.error(f"Data cleanup test failed: {e}")
            raise

    async def _test_integration(self):
        """
        統合テストを実行
        """
        logger.info("--- Testing Integration ---")

        try:
            # エンドツーエンドテスト
            logger.info("Running end-to-end integration test...")

            # 1. データ取得
            price_data = await self.services["data_fetcher"].fetch_and_save_price_data()

            # 2. 指標計算
            if price_data:
                indicators = await self.services[
                    "indicator_service"
                ].calculate_all_indicators(timeframe="5m")

                # 3. パターン検出
                if indicators:
                    patterns = await self.services[
                        "pattern_service"
                    ].detect_all_patterns()

                    # 4. 通知処理（無効化）
                    if patterns and self.test_config["enable_notifications"]:
                        notifications = await self.services[
                            "notification_service"
                        ].process_patterns(patterns)
                        logger.info(f"Processed {len(notifications)} notifications")

            self._record_test_result("Integration", "PASSED")
            logger.info("Integration test passed")

        except Exception as e:
            self._record_test_result("Integration", "FAILED", str(e))
            logger.error(f"Integration test failed: {e}")
            raise

    def _record_test_result(
        self, test_name: str, status: str, error_message: str = None
    ):
        """
        テスト結果を記録

        Args:
            test_name: テスト名
            status: ステータス
            error_message: エラーメッセージ
        """
        result = {
            "test_name": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        if error_message:
            result["error"] = error_message

        self.test_results.append(result)

    async def _generate_test_report(self):
        """
        テストレポートを生成
        """
        logger.info("--- Generating Test Report ---")

        try:
            total_tests = len(self.test_results)
            passed_tests = len(
                [r for r in self.test_results if r["status"] == "PASSED"]
            )
            failed_tests = len(
                [r for r in self.test_results if r["status"] == "FAILED"]
            )
            skipped_tests = len(
                [r for r in self.test_results if r["status"] == "SKIPPED"]
            )

            success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

            # レポートを表示
            logger.info("=== Production Test Report ===")
            logger.info(f"Total Tests: {total_tests}")
            logger.info(f"Passed: {passed_tests}")
            logger.info(f"Failed: {failed_tests}")
            logger.info(f"Skipped: {skipped_tests}")
            logger.info(f"Success Rate: {success_rate:.1f}%")

            # 失敗したテストを表示
            if failed_tests > 0:
                logger.warning("Failed Tests:")
                for result in self.test_results:
                    if result["status"] == "FAILED":
                        logger.warning(
                            f"  {result['test_name']}: {result.get('error', 'Unknown error')}"
                        )

            # レポートファイルを保存
            report_file = Path("logs/production_test_report.log")
            report_file.parent.mkdir(exist_ok=True)

            with open(report_file, "w") as f:
                f.write("=== Production Test Report ===\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n")
                f.write(f"Total Tests: {total_tests}\n")
                f.write(f"Passed: {passed_tests}\n")
                f.write(f"Failed: {failed_tests}\n")
                f.write(f"Skipped: {skipped_tests}\n")
                f.write(f"Success Rate: {success_rate:.1f}%\n\n")

                for result in self.test_results:
                    f.write(f"Test: {result['test_name']}\n")
                    f.write(f"Status: {result['status']}\n")
                    f.write(f"Timestamp: {result['timestamp']}\n")
                    if "error" in result:
                        f.write(f"Error: {result['error']}\n")
                    f.write("\n")

            logger.info(f"Test report saved to: {report_file}")

        except Exception as e:
            logger.error(f"Error generating test report: {e}")

    async def _handle_test_failure(self, error):
        """
        テスト失敗を処理
        """
        logger.error("=== Test Failure Handling ===")

        try:
            # 失敗ログを記録
            self._record_test_result("Test Failure", "FAILED", str(error))

            # 失敗レポートを生成
            await self._generate_test_report()

            logger.error("Test failure handling completed")

        except Exception as e:
            logger.error(f"Error in test failure handling: {e}")

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Production test cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting production test...")

    # 環境変数の設定（テスト用）
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost/testdb"
        logger.info("Set default DATABASE_URL for testing")

    if not os.getenv("DISCORD_WEBHOOK_URL"):
        os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test"
        logger.info("Set default DISCORD_WEBHOOK_URL for testing")

    if not os.getenv("YAHOO_FINANCE_API_KEY"):
        os.environ["YAHOO_FINANCE_API_KEY"] = "test_api_key"
        logger.info("Set default YAHOO_FINANCE_API_KEY for testing")

    if not os.getenv("LOG_LEVEL"):
        os.environ["LOG_LEVEL"] = "INFO"
        logger.info("Set default LOG_LEVEL for testing")

    test = ProductionTest()

    try:
        # 完全な本番運用テスト実行
        await test.run_full_production_test()

        logger.info("Production test completed successfully!")

    except Exception as e:
        logger.error(f"Production test failed: {e}")
        sys.exit(1)
    finally:
        await test.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
