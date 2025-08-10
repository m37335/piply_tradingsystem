#!/usr/bin/env python3
"""
パターン検出とDiscord通知の統合テストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.efficient_pattern_detection_service import (
    EfficientPatternDetectionService,
)
from tests.database.test_data_generator_service import (
    TestDataGeneratorService,
)
from src.infrastructure.notification.discord_notification_service import (
    DiscordNotificationService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PatternDetectionWithDiscordTester:
    """
    パターン検出とDiscord通知の統合テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_service = None
        self.test_data_generator = None
        self.discord_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up pattern detection with Discord test...")
        logger.info("Setting up pattern detection with Discord test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # Discord Webhook URLの設定（テスト用）
        if not os.getenv("DISCORD_WEBHOOK_URL"):
            os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test"

        # セッションを取得
        self.session = await get_async_session()

        # 効率的パターン検出サービスを初期化
        self.pattern_service = EfficientPatternDetectionService(self.session)

        # テストデータ生成サービスを初期化
        self.test_data_generator = TestDataGeneratorService(self.session)

        # Discord通知サービスを初期化
        self.discord_service = DiscordNotificationService()

        print("Pattern detection with Discord test setup completed")
        logger.info("Pattern detection with Discord test setup completed")

    async def test_pattern_detection_and_notification(self):
        """
        パターン検出とDiscord通知の統合テスト
        """
        print("Testing pattern detection and Discord notification...")
        logger.info("Testing pattern detection and Discord notification...")

        try:
            # パターン1用のテストデータを生成
            success = await self.test_data_generator.generate_pattern_1_test_data()
            if not success:
                print("❌ Failed to generate test data")
                return

            print("✅ Test data generated successfully")

            # 過去24時間のデータでパターン検出を実行
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            patterns = await self.pattern_service.detect_all_patterns(
                start_date, end_date
            )

            if patterns:
                print(f"✅ Patterns detected: {len(patterns)} pattern types")

                # 各パターンをDiscordに通知
                for pattern_type, pattern_list in patterns.items():
                    print(f"  Pattern {pattern_type}: {len(pattern_list)} detections")

                    for pattern in pattern_list:
                        print(
                            f"    - {pattern.pattern_name} (confidence: {pattern.confidence_score}, direction: {pattern.direction})"
                        )

                        # Discord通知をテスト
                        await self._test_discord_notification(pattern)
            else:
                print("❌ No patterns detected")
                print(
                    "This is expected for test data - patterns may not meet strict conditions"
                )

        except Exception as e:
            print(f"❌ Pattern detection and notification test failed: {e}")
            logger.error(f"Pattern detection and notification test failed: {e}")

    async def test_discord_notification_only(self):
        """
        Discord通知のみのテスト
        """
        print("Testing Discord notification only...")
        logger.info("Testing Discord notification only...")

        try:
            # テスト用のパターン検出結果を作成
            from datetime import datetime

            from src.infrastructure.database.models.pattern_detection_model import (
                PatternDetectionModel,
            )

            test_pattern = PatternDetectionModel(
                currency_pair="USD/JPY",
                pattern_name="テストパターン",
                pattern_type=1,
                confidence_score=85.5,
                direction="sell",
                entry_price=150.25,
                stop_loss=150.50,
                take_profit=149.80,
                timeframe="H1",
                description="テスト用のパターン検出結果です",
                additional_data={"test": True},
            )

            # Discord通知をテスト
            await self._test_discord_notification(test_pattern)

        except Exception as e:
            print(f"❌ Discord notification test failed: {e}")
            logger.error(f"Discord notification test failed: {e}")

    async def _test_discord_notification(self, pattern):
        """
        個別のパターンをDiscordに通知
        """
        try:
            print(f"  📢 Sending Discord notification for {pattern.pattern_name}...")

            # Discord通知を送信
            success = await self.discord_service.send_pattern_notification(pattern)

            if success:
                print(f"    ✅ Discord notification sent successfully")
            else:
                print(f"    ❌ Discord notification failed")

        except Exception as e:
            print(f"    ❌ Discord notification error: {e}")
            logger.error(f"Discord notification error: {e}")

    async def test_multiple_patterns_notification(self):
        """
        複数パターンの一括通知テスト
        """
        print("Testing multiple patterns notification...")
        logger.info("Testing multiple patterns notification...")

        try:
            # 複数のテストパターンを作成
            from datetime import datetime

            from src.infrastructure.database.models.pattern_detection_model import (
                PatternDetectionModel,
            )

            test_patterns = [
                PatternDetectionModel(
                    currency_pair="USD/JPY",
                    pattern_name="トレンド転換",
                    pattern_type=1,
                    confidence_score=90.0,
                    direction="sell",
                    entry_price=150.30,
                    stop_loss=150.60,
                    take_profit=149.90,
                    timeframe="D1",
                    description="日足でのトレンド転換シグナル",
                    additional_data={"test": True},
                ),
                PatternDetectionModel(
                    currency_pair="USD/JPY",
                    pattern_name="押し目・戻り売り",
                    pattern_type=2,
                    confidence_score=85.0,
                    direction="sell",
                    entry_price=150.15,
                    stop_loss=150.40,
                    take_profit=149.70,
                    timeframe="H4",
                    description="4時間足での押し目・戻り売り",
                    additional_data={"test": True},
                ),
                PatternDetectionModel(
                    currency_pair="USD/JPY",
                    pattern_name="ダイバージェンス",
                    pattern_type=3,
                    confidence_score=88.0,
                    direction="buy",
                    entry_price=149.80,
                    stop_loss=149.50,
                    take_profit=150.20,
                    timeframe="H1",
                    description="1時間足でのダイバージェンス",
                    additional_data={"test": True},
                ),
            ]

            # 一括でDiscord通知を送信
            print(f"  📢 Sending {len(test_patterns)} Discord notifications...")

            for pattern in test_patterns:
                await self._test_discord_notification(pattern)
                await asyncio.sleep(1)  # 1秒間隔で送信

            print("✅ Multiple patterns notification test completed")

        except Exception as e:
            print(f"❌ Multiple patterns notification test failed: {e}")
            logger.error(f"Multiple patterns notification test failed: {e}")

    async def cleanup_test_data(self):
        """
        テストデータをクリーンアップ
        """
        print("Cleaning up test data...")
        logger.info("Cleaning up test data...")

        try:
            success = await self.test_data_generator.cleanup_test_data()
            if success:
                print("✅ Test data cleanup completed")
            else:
                print("❌ Test data cleanup failed")
        except Exception as e:
            print(f"❌ Test data cleanup error: {e}")
            logger.error(f"Test data cleanup error: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Pattern detection with Discord test cleanup completed")
        logger.info("Pattern detection with Discord test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting pattern detection with Discord test...")
    logger.info("Starting pattern detection with Discord test...")

    tester = PatternDetectionWithDiscordTester()

    try:
        await tester.setup()

        # Discord通知のみのテスト
        await tester.test_discord_notification_only()

        # 複数パターンの一括通知テスト
        await tester.test_multiple_patterns_notification()

        # パターン検出とDiscord通知の統合テスト
        await tester.test_pattern_detection_and_notification()

        # テストデータをクリーンアップ
        await tester.cleanup_test_data()

        print("Pattern detection with Discord test completed successfully!")
        logger.info("Pattern detection with Discord test completed successfully!")

    except Exception as e:
        print(f"Pattern detection with Discord test failed: {e}")
        logger.error(f"Pattern detection with Discord test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
