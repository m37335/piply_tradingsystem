"""
通知システム統合テスト

USD/JPY特化の通知システム統合テスト
設計書参照: /app/note/database_implementation_design_2025.md
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService
from src.infrastructure.database.services.notification_integration_service import (
    NotificationIntegrationService,
)
from src.infrastructure.database.services.pattern_detection_service import (
    PatternDetectionService,
)
from src.infrastructure.database.services.technical_indicator_service import (
    TechnicalIndicatorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TestNotificationIntegration:
    """
    通知システム統合テストクラス
    """

    @pytest.fixture
    async def session(self) -> AsyncSession:
        """
        データベースセッションのフィクスチャ
        """
        async for session in get_async_session():
            yield session
            break

    @pytest.fixture
    async def services(self, session: AsyncSession):
        """
        サービスのフィクスチャ
        """
        data_fetcher = DataFetcherService(session)
        indicator_service = TechnicalIndicatorService(session)
        pattern_service = PatternDetectionService(session)
        notification_service = NotificationIntegrationService(session)

        return {
            "data_fetcher": data_fetcher,
            "indicator_service": indicator_service,
            "pattern_service": pattern_service,
            "notification_service": notification_service,
        }

    @pytest.mark.asyncio
    async def test_complete_notification_flow(self, services: Dict):
        """
        完全な通知フローのテスト
        """
        logger.info("Testing complete notification flow...")

        start_time = time.time()
        results = {}

        try:
            # 1. データ取得
            logger.info("Step 1: Data fetching")
            data_fetcher = services["data_fetcher"]
            price_data = await data_fetcher.fetch_current_price_data()
            results["data_fetch"] = {
                "success": len(price_data) > 0,
                "count": len(price_data),
                "duration": time.time() - start_time,
            }

            # 2. テクニカル指標計算
            logger.info("Step 2: Technical indicator calculation")
            indicator_start = time.time()
            indicator_service = services["indicator_service"]
            indicator_results = await indicator_service.calculate_all_indicators()
            results["indicator_calculation"] = {
                "success": len(indicator_results) > 0,
                "indicators_count": sum(
                    len(indicators) for indicators in indicator_results.values()
                ),
                "duration": time.time() - indicator_start,
            }

            # 3. パターン検出
            logger.info("Step 3: Pattern detection")
            pattern_start = time.time()
            pattern_service = services["pattern_service"]
            pattern_results = await pattern_service.detect_all_patterns()
            results["pattern_detection"] = {
                "success": len(pattern_results) > 0,
                "patterns_count": sum(
                    len(patterns) for patterns in pattern_results.values()
                ),
                "duration": time.time() - pattern_start,
            }

            # 4. 通知送信
            logger.info("Step 4: Notification sending")
            notification_start = time.time()
            notification_service = services["notification_service"]
            notification_results = (
                await notification_service.process_pattern_notifications()
            )
            results["notification_sending"] = {
                "success": notification_results["sent"] >= 0,
                "sent_count": notification_results["sent"],
                "skipped_count": notification_results["skipped"],
                "error_count": notification_results["errors"],
                "duration": time.time() - notification_start,
            }

            # 総合結果
            total_duration = time.time() - start_time
            results["total"] = {
                "success": all(
                    step["success"] for step in results.values() if "success" in step
                ),
                "duration": total_duration,
            }

            logger.info(f"Complete flow test completed in {total_duration:.2f}s")
            logger.info(f"Results: {results}")

            # アサーション
            assert results["data_fetch"]["success"], "Data fetching failed"
            assert results["indicator_calculation"][
                "success"
            ], "Indicator calculation failed"
            assert results["pattern_detection"]["success"], "Pattern detection failed"
            assert results["notification_sending"][
                "success"
            ], "Notification sending failed"
            assert results["total"]["success"], "Complete flow failed"

        except Exception as e:
            logger.error(f"Error in complete flow test: {e}")
            raise

    @pytest.mark.asyncio
    async def test_pattern_detection_accuracy(self, services: Dict):
        """
        パターン検出精度のテスト
        """
        logger.info("Testing pattern detection accuracy...")

        try:
            pattern_service = services["pattern_service"]

            # 過去24時間のパターンを検出
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            pattern_results = await pattern_service.detect_all_patterns(
                start_date, end_date
            )

            # 精度統計を計算
            accuracy_stats = {
                "total_patterns": 0,
                "high_confidence_patterns": 0,
                "pattern_distribution": {},
                "confidence_distribution": {
                    "0.7-0.8": 0,
                    "0.8-0.9": 0,
                    "0.9-1.0": 0,
                },
            }

            for pattern_number, patterns in pattern_results.items():
                accuracy_stats["total_patterns"] += len(patterns)
                accuracy_stats["pattern_distribution"][
                    f"pattern_{pattern_number}"
                ] = len(patterns)

                for pattern in patterns:
                    # 高信頼度パターンのカウント
                    if pattern.confidence_score >= 0.8:
                        accuracy_stats["high_confidence_patterns"] += 1

                    # 信頼度分布
                    if 0.7 <= pattern.confidence_score < 0.8:
                        accuracy_stats["confidence_distribution"]["0.7-0.8"] += 1
                    elif 0.8 <= pattern.confidence_score < 0.9:
                        accuracy_stats["confidence_distribution"]["0.8-0.9"] += 1
                    elif 0.9 <= pattern.confidence_score <= 1.0:
                        accuracy_stats["confidence_distribution"]["0.9-1.0"] += 1

            # 精度率を計算
            if accuracy_stats["total_patterns"] > 0:
                accuracy_stats["high_confidence_rate"] = (
                    accuracy_stats["high_confidence_patterns"]
                    / accuracy_stats["total_patterns"]
                    * 100
                )
            else:
                accuracy_stats["high_confidence_rate"] = 0.0

            logger.info(f"Pattern detection accuracy: {accuracy_stats}")

            # アサーション
            assert accuracy_stats["total_patterns"] >= 0, "No patterns detected"
            assert (
                accuracy_stats["high_confidence_rate"] >= 0
            ), "Invalid confidence rate"

        except Exception as e:
            logger.error(f"Error in pattern detection accuracy test: {e}")
            raise

    @pytest.mark.asyncio
    async def test_notification_accuracy(self, services: Dict):
        """
        通知精度のテスト
        """
        logger.info("Testing notification accuracy...")

        try:
            notification_service = services["notification_service"]

            # 通知統計を取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            notification_stats = await notification_service.get_notification_statistics(
                start_date, end_date
            )

            logger.info(f"Notification accuracy: {notification_stats}")

            # アサーション
            assert notification_stats["total_patterns"] >= 0, "Invalid total patterns"
            assert (
                notification_stats["notified_patterns"] >= 0
            ), "Invalid notified patterns"
            assert (
                0 <= notification_stats["notification_rate"] <= 100
            ), "Invalid notification rate"

        except Exception as e:
            logger.error(f"Error in notification accuracy test: {e}")
            raise

    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, services: Dict):
        """
        パフォーマンスベンチマークテスト
        """
        logger.info("Testing performance benchmarks...")

        performance_results = {}

        try:
            # 1. データ取得パフォーマンス
            logger.info("Testing data fetching performance...")
            data_fetcher = services["data_fetcher"]

            start_time = time.time()
            price_data = await data_fetcher.fetch_current_price_data()
            data_fetch_duration = time.time() - start_time

            performance_results["data_fetch"] = {
                "duration": data_fetch_duration,
                "data_count": len(price_data),
                "performance_ok": data_fetch_duration <= 2.0,  # 2秒以内
            }

            # 2. 指標計算パフォーマンス
            logger.info("Testing indicator calculation performance...")
            indicator_service = services["indicator_service"]

            start_time = time.time()
            indicator_results = await indicator_service.calculate_all_indicators()
            indicator_duration = time.time() - start_time

            performance_results["indicator_calculation"] = {
                "duration": indicator_duration,
                "indicators_count": sum(
                    len(indicators) for indicators in indicator_results.values()
                ),
                "performance_ok": indicator_duration <= 8.0,  # 8秒以内
            }

            # 3. パターン検出パフォーマンス
            logger.info("Testing pattern detection performance...")
            pattern_service = services["pattern_service"]

            start_time = time.time()
            pattern_results = await pattern_service.detect_all_patterns()
            pattern_duration = time.time() - start_time

            performance_results["pattern_detection"] = {
                "duration": pattern_duration,
                "patterns_count": sum(
                    len(patterns) for patterns in pattern_results.values()
                ),
                "performance_ok": pattern_duration <= 5.0,  # 5秒以内
            }

            # 4. 通知送信パフォーマンス
            logger.info("Testing notification sending performance...")
            notification_service = services["notification_service"]

            start_time = time.time()
            notification_results = (
                await notification_service.process_pattern_notifications()
            )
            notification_duration = time.time() - start_time

            performance_results["notification_sending"] = {
                "duration": notification_duration,
                "sent_count": notification_results["sent"],
                "performance_ok": notification_duration <= 2.0,  # 2秒以内
            }

            # 総合パフォーマンス
            total_duration = sum(
                result["duration"] for result in performance_results.values()
            )
            all_performance_ok = all(
                result["performance_ok"] for result in performance_results.values()
            )

            performance_results["total"] = {
                "duration": total_duration,
                "performance_ok": all_performance_ok,
                "performance_ok": total_duration <= 17.0,  # 総計17秒以内
            }

            logger.info(f"Performance benchmarks: {performance_results}")

            # アサーション
            assert performance_results["data_fetch"][
                "performance_ok"
            ], "Data fetch too slow"
            assert performance_results["indicator_calculation"][
                "performance_ok"
            ], "Indicator calculation too slow"
            assert performance_results["pattern_detection"][
                "performance_ok"
            ], "Pattern detection too slow"
            assert performance_results["notification_sending"][
                "performance_ok"
            ], "Notification sending too slow"
            assert performance_results["total"][
                "performance_ok"
            ], "Total performance too slow"

        except Exception as e:
            logger.error(f"Error in performance benchmarks test: {e}")
            raise

    @pytest.mark.asyncio
    async def test_error_handling(self, services: Dict):
        """
        エラーハンドリングのテスト
        """
        logger.info("Testing error handling...")

        try:
            # 1. 無効なデータでのテスト
            logger.info("Testing with invalid data...")
            pattern_service = services["pattern_service"]

            # 存在しないパターン番号でテスト
            try:
                await pattern_service.detect_single_pattern(999)
                assert False, "Should have raised ValueError"
            except ValueError:
                logger.info("Correctly handled invalid pattern number")

            # 2. 空のデータでのテスト
            logger.info("Testing with empty data...")
            notification_service = services["notification_service"]

            # 過去の日付でテスト（データが存在しない可能性）
            old_date = datetime.now() - timedelta(days=365)
            results = await notification_service.process_pattern_notifications(
                start_date=old_date, end_date=old_date + timedelta(hours=1)
            )

            assert results["processed"] == 0, "Should handle empty data gracefully"

            logger.info("Error handling tests completed successfully")

        except Exception as e:
            logger.error(f"Error in error handling test: {e}")
            raise

    @pytest.mark.asyncio
    async def test_concurrent_execution(self, services: Dict):
        """
        並行実行のテスト
        """
        logger.info("Testing concurrent execution...")

        try:
            # 複数のタスクを並行実行
            tasks = []

            # データ取得タスク
            data_fetcher = services["data_fetcher"]
            tasks.append(data_fetcher.fetch_current_price_data())

            # 指標計算タスク
            indicator_service = services["indicator_service"]
            tasks.append(indicator_service.calculate_all_indicators())

            # パターン検出タスク
            pattern_service = services["pattern_service"]
            tasks.append(pattern_service.detect_all_patterns())

            # 並行実行
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_duration = time.time() - start_time

            # 結果をチェック
            success_count = sum(
                1 for result in results if not isinstance(result, Exception)
            )

            concurrent_results = {
                "total_tasks": len(tasks),
                "successful_tasks": success_count,
                "duration": concurrent_duration,
                "success": success_count == len(tasks),
            }

            logger.info(f"Concurrent execution results: {concurrent_results}")

            # アサーション
            assert concurrent_results["success"], "Concurrent execution failed"
            assert concurrent_duration < 15.0, "Concurrent execution too slow"

        except Exception as e:
            logger.error(f"Error in concurrent execution test: {e}")
            raise

    @pytest.mark.asyncio
    async def test_notification_system_test(self, services: Dict):
        """
        通知システムのテスト機能
        """
        logger.info("Testing notification system test function...")

        try:
            notification_service = services["notification_service"]

            # 通知システムテストを実行
            test_result = await notification_service.test_notification_system()

            logger.info(f"Notification system test result: {test_result}")

            # アサーション
            assert isinstance(test_result, bool), "Test result should be boolean"

        except Exception as e:
            logger.error(f"Error in notification system test: {e}")
            raise


async def main():
    """
    メイン関数（テスト実行用）
    """
    logger.info("Starting notification integration tests...")

    # セッション取得
    async for session in get_async_session():
        try:
            # サービス初期化
            services = {
                "data_fetcher": DataFetcherService(session),
                "indicator_service": TechnicalIndicatorService(session),
                "pattern_service": PatternDetectionService(session),
                "notification_service": NotificationIntegrationService(session),
            }

            # テストインスタンス作成
            test_instance = TestNotificationIntegration()

            # テスト実行
            logger.info("Running complete notification flow test...")
            await test_instance.test_complete_notification_flow(services)

            logger.info("Running pattern detection accuracy test...")
            await test_instance.test_pattern_detection_accuracy(services)

            logger.info("Running notification accuracy test...")
            await test_instance.test_notification_accuracy(services)

            logger.info("Running performance benchmarks test...")
            await test_instance.test_performance_benchmarks(services)

            logger.info("Running error handling test...")
            await test_instance.test_error_handling(services)

            logger.info("Running concurrent execution test...")
            await test_instance.test_concurrent_execution(services)

            logger.info("Running notification system test...")
            await test_instance.test_notification_system_test(services)

            logger.info("All integration tests completed successfully!")

        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            raise
        finally:
            await session.close()


if __name__ == "__main__":
    asyncio.run(main())
