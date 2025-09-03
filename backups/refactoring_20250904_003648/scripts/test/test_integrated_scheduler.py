#!/usr/bin/env python3
"""
統合スケジューラーテストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.schedulers.integrated_scheduler import IntegratedScheduler
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class IntegratedSchedulerTester:
    """
    統合スケジューラーテストクラス
    """

    def __init__(self):
        self.scheduler = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up integrated scheduler test...")
        logger.info("Setting up integrated scheduler test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # Discord Webhook URLの設定
        if not os.getenv("DISCORD_WEBHOOK_URL"):
            os.environ[
                "DISCORD_WEBHOOK_URL"
            ] = "https://canary.discord.com/api/webhooks/1403643478361116672/nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ"

        # 統合スケジューラーを初期化
        self.scheduler = IntegratedScheduler()

        print("Integrated scheduler test setup completed")
        logger.info("Integrated scheduler test setup completed")

    async def test_scheduler_initialization(self):
        """
        スケジューラーの初期化テスト
        """
        print("Testing scheduler initialization...")
        logger.info("Testing scheduler initialization...")

        try:
            # スケジューラーを初期化
            await self.scheduler.setup()

            # 各サービスが正しく初期化されているか確認
            assert (
                self.scheduler.session is not None
            ), "Database session not initialized"
            assert (
                self.scheduler.data_fetcher is not None
            ), "Data fetcher not initialized"
            assert (
                self.scheduler.technical_indicator_service is not None
            ), "Technical indicator service not initialized"
            assert (
                self.scheduler.pattern_detection_service is not None
            ), "Pattern detection service not initialized"
            assert (
                self.scheduler.discord_sender is not None
            ), "Discord sender not initialized"

            print("✅ Scheduler initialization test passed")
            logger.info("Scheduler initialization test passed")

        except Exception as e:
            print(f"❌ Scheduler initialization test failed: {e}")
            logger.error(f"Scheduler initialization test failed: {e}")
            raise

    async def test_data_fetch_services(self):
        """
        データ取得サービスのテスト
        """
        print("Testing data fetch services...")
        logger.info("Testing data fetch services...")

        try:
            # 5分足データ取得をテスト
            print("  📊 Testing 5m data fetch...")
            await self.scheduler._fetch_5m_data_with_retry()
            print("    ✅ 5m data fetch test passed")

            # 日足データ取得をテスト
            print("  📊 Testing D1 data fetch...")
            await self.scheduler._fetch_d1_data_with_retry()
            print("    ✅ D1 data fetch test passed")

            print("✅ Data fetch services test passed")
            logger.info("Data fetch services test passed")

        except Exception as e:
            print(f"❌ Data fetch services test failed: {e}")
            logger.error(f"Data fetch services test failed: {e}")
            raise

    async def test_pattern_detection_service(self):
        """
        パターン検出サービスのテスト
        """
        print("Testing pattern detection service...")
        logger.info("Testing pattern detection service...")

        try:
            # パターン検出をテスト
            print("  🔍 Testing pattern detection...")
            await self.scheduler._detect_patterns_with_retry()
            print("    ✅ Pattern detection test passed")

            print("✅ Pattern detection service test passed")
            logger.info("Pattern detection service test passed")

        except Exception as e:
            print(f"❌ Pattern detection service test failed: {e}")
            logger.error(f"Pattern detection service test failed: {e}")
            raise

    async def test_discord_notification(self):
        """
        Discord通知のテスト
        """
        print("Testing Discord notification...")
        logger.info("Testing Discord notification...")

        try:
            # テスト用のパターンを作成
            from datetime import datetime

            from src.infrastructure.database.models.pattern_detection_model import (
                PatternDetectionModel,
            )

            test_pattern = PatternDetectionModel(
                currency_pair="USD/JPY",
                timestamp=datetime.now(),
                pattern_type="Pattern 1",
                pattern_name="テストパターン",
                confidence_score=85.0,
                direction="SELL",
                detection_data={
                    "entry_price": 150.30,
                    "stop_loss": 150.60,
                    "take_profit": 149.90,
                    "timeframe": "D1",
                    "description": "統合スケジューラーテスト用パターン",
                },
                indicator_data={
                    "rsi": 75.0,
                    "macd": -0.2,
                    "bollinger_bands": "upper_touch",
                },
            )

            # Discord通知をテスト
            print("  📢 Testing Discord notification...")
            await self.scheduler._send_pattern_notifications([test_pattern])
            print("    ✅ Discord notification test passed")

            print("✅ Discord notification test passed")
            logger.info("Discord notification test passed")

        except Exception as e:
            print(f"❌ Discord notification test failed: {e}")
            logger.error(f"Discord notification test failed: {e}")
            raise

    async def test_scheduler_short_run(self):
        """
        スケジューラーの短時間実行テスト
        """
        print("Testing scheduler short run...")
        logger.info("Testing scheduler short run...")

        try:
            # スケジューラーを短時間実行
            print("  🚀 Starting scheduler for short test...")

            # 実行フラグを設定
            self.scheduler.is_running = True

            # 各サービスを開始
            await self.scheduler.start_data_collection()
            await self.scheduler.start_pattern_detection()
            await self.scheduler.start_notification_service()

            # 10秒間実行
            print("  ⏱️  Running scheduler for 10 seconds...")
            await asyncio.sleep(10)

            # スケジューラーを停止
            print("  🛑 Stopping scheduler...")
            await self.scheduler.stop()

            print("    ✅ Scheduler short run test passed")
            print("✅ Scheduler short run test passed")
            logger.info("Scheduler short run test passed")

        except Exception as e:
            print(f"❌ Scheduler short run test failed: {e}")
            logger.error(f"Scheduler short run test failed: {e}")
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.scheduler:
            await self.scheduler.stop()
        print("Integrated scheduler test cleanup completed")
        logger.info("Integrated scheduler test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting integrated scheduler test...")
    logger.info("Starting integrated scheduler test...")

    tester = IntegratedSchedulerTester()

    try:
        await tester.setup()

        # 各テストを実行
        await tester.test_scheduler_initialization()
        await tester.test_data_fetch_services()
        await tester.test_pattern_detection_service()
        await tester.test_discord_notification()
        await tester.test_scheduler_short_run()

        print("Integrated scheduler test completed successfully!")
        logger.info("Integrated scheduler test completed successfully!")

    except Exception as e:
        print(f"Integrated scheduler test failed: {e}")
        logger.error(f"Integrated scheduler test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
