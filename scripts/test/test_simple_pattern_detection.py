#!/usr/bin/env python3
"""
簡単なパターン検出テストスクリプト
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
from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)
from src.infrastructure.database.repositories.pattern_detection_repository_impl import (
    PatternDetectionRepositoryImpl,
)
from src.infrastructure.notification.discord_notification_service import (
    DiscordNotificationService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class SimplePatternDetectionTester:
    """
    簡単なパターン検出テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_repo = None
        self.discord_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up simple pattern detection test...")
        logger.info("Setting up simple pattern detection test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # Discord Webhook URLの設定（テスト用）
        if not os.getenv("DISCORD_WEBHOOK_URL"):
            os.environ["DISCORD_WEBHOOK_URL"] = "https://discord.com/api/webhooks/test"

        # セッションを取得
        self.session = await get_async_session()

        # パターン検出リポジトリを初期化
        self.pattern_repo = PatternDetectionRepositoryImpl(self.session)

        # Discord通知サービスを初期化
        self.discord_service = DiscordNotificationService()

        print("Simple pattern detection test setup completed")
        logger.info("Simple pattern detection test setup completed")

    async def test_pattern_creation_and_notification(self):
        """
        パターン検出結果の作成とDiscord通知のテスト
        """
        print("Testing pattern creation and Discord notification...")
        logger.info("Testing pattern creation and Discord notification...")

        try:
            # テスト用のパターン検出結果を作成
            from datetime import datetime

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
                    description="日足でのトレンド転換シグナル - テスト用",
                    additional_data={"test": True, "source": "simple_test"},
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
                    description="4時間足での押し目・戻り売り - テスト用",
                    additional_data={"test": True, "source": "simple_test"},
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
                    description="1時間足でのダイバージェンス - テスト用",
                    additional_data={"test": True, "source": "simple_test"},
                ),
            ]

            # パターンをデータベースに保存
            saved_patterns = []
            for pattern in test_patterns:
                saved_pattern = await self.pattern_repo.save(pattern)
                saved_patterns.append(saved_pattern)
                print(
                    f"✅ Pattern saved: {pattern.pattern_name} (ID: {saved_pattern.id})"
                )

            # 各パターンをDiscordに通知
            print(f"\n📢 Sending {len(saved_patterns)} Discord notifications...")

            for pattern in saved_patterns:
                await self._test_discord_notification(pattern)
                await asyncio.sleep(1)  # 1秒間隔で送信

            # 保存されたパターンを取得して確認
            print(f"\n📊 Retrieving saved patterns...")
            latest_patterns = await self.pattern_repo.find_latest(limit=5)

            if latest_patterns:
                print(f"✅ Retrieved {len(latest_patterns)} patterns from database")
                for pattern in latest_patterns:
                    print(
                        f"  - {pattern.pattern_name} (confidence: {pattern.confidence_score}, direction: {pattern.direction})"
                    )
            else:
                print("❌ No patterns retrieved from database")

            print("✅ Pattern creation and notification test completed")

        except Exception as e:
            print(f"❌ Pattern creation and notification test failed: {e}")
            logger.error(f"Pattern creation and notification test failed: {e}")

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

    async def cleanup_test_data(self):
        """
        テストデータをクリーンアップ
        """
        print("Cleaning up test data...")
        logger.info("Cleaning up test data...")

        try:
            # テスト用のパターンを削除
            from sqlalchemy import delete

            from src.infrastructure.database.models.pattern_detection_model import (
                PatternDetectionModel,
            )

            delete_query = delete(PatternDetectionModel).where(
                PatternDetectionModel.additional_data.contains({"test": True})
            )

            result = await self.session.execute(delete_query)
            await self.session.commit()

            deleted_count = result.rowcount
            print(f"✅ Deleted {deleted_count} test patterns")

        except Exception as e:
            print(f"❌ Test data cleanup error: {e}")
            logger.error(f"Test data cleanup error: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Simple pattern detection test cleanup completed")
        logger.info("Simple pattern detection test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting simple pattern detection test...")
    logger.info("Starting simple pattern detection test...")

    tester = SimplePatternDetectionTester()

    try:
        await tester.setup()

        # パターン作成とDiscord通知のテスト
        await tester.test_pattern_creation_and_notification()

        # テストデータをクリーンアップ
        await tester.cleanup_test_data()

        print("Simple pattern detection test completed successfully!")
        logger.info("Simple pattern detection test completed successfully!")

    except Exception as e:
        print(f"Simple pattern detection test failed: {e}")
        logger.error(f"Simple pattern detection test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
