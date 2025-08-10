#!/usr/bin/env python3
"""
完全なパターン検出テストスクリプト（既存のDiscordWebhookSender使用）
"""

import asyncio
import os
import sys
from pathlib import Path

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
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class CompletePatternDetectionTester:
    """
    完全なパターン検出テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_repo = None
        self.discord_sender = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up complete pattern detection test...")
        logger.info("Setting up complete pattern detection test...")

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

        # .envファイルからDiscord Webhook URLを読み込み
        from dotenv import load_dotenv

        load_dotenv()

        # 実際のWebhook URLを設定
        self.webhook_url = "https://canary.discord.com/api/webhooks/1403643478361116672/nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ"
        print(f"Discord Webhook URL: {self.webhook_url}")

        print("Complete pattern detection test setup completed")
        logger.info("Complete pattern detection test setup completed")

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
                    timestamp=datetime.now(),
                    pattern_type="Pattern 1",
                    pattern_name="トレンド転換",
                    confidence_score=90.0,
                    direction="SELL",
                    detection_data={
                        "entry_price": 150.30,
                        "stop_loss": 150.60,
                        "take_profit": 149.90,
                        "timeframe": "D1",
                        "description": "日足でのトレンド転換シグナル - テスト用",
                        "test": True,
                        "source": "complete_test",
                    },
                    indicator_data={
                        "rsi": 75.0,
                        "macd": -0.2,
                        "bollinger_bands": "upper_touch",
                    },
                ),
                PatternDetectionModel(
                    currency_pair="USD/JPY",
                    timestamp=datetime.now(),
                    pattern_type="Pattern 2",
                    pattern_name="押し目・戻り売り",
                    confidence_score=85.0,
                    direction="SELL",
                    detection_data={
                        "entry_price": 150.15,
                        "stop_loss": 150.40,
                        "take_profit": 149.70,
                        "timeframe": "H4",
                        "description": "4時間足での押し目・戻り売り - テスト用",
                        "test": True,
                        "source": "complete_test",
                    },
                    indicator_data={
                        "rsi": 65.0,
                        "macd": -0.1,
                        "bollinger_bands": "middle_touch",
                    },
                ),
                PatternDetectionModel(
                    currency_pair="USD/JPY",
                    timestamp=datetime.now(),
                    pattern_type="Pattern 3",
                    pattern_name="ダイバージェンス",
                    confidence_score=88.0,
                    direction="BUY",
                    detection_data={
                        "entry_price": 149.80,
                        "stop_loss": 149.50,
                        "take_profit": 150.20,
                        "timeframe": "H1",
                        "description": "1時間足でのダイバージェンス - テスト用",
                        "test": True,
                        "source": "complete_test",
                    },
                    indicator_data={
                        "rsi": 35.0,
                        "macd": 0.1,
                        "bollinger_bands": "lower_touch",
                    },
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

            # DiscordWebhookSenderを正しく初期化して使用
            discord_sender = DiscordWebhookSender(self.webhook_url)

            async with discord_sender:
                for pattern in saved_patterns:
                    await self._test_discord_notification_with_sender(
                        pattern, discord_sender
                    )
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
        個別のパターンをDiscordに通知（旧メソッド）
        """
        try:
            print(f"  📢 Sending Discord notification for {pattern.pattern_name}...")

            # パターン情報をDiscord Embed形式で作成
            embed = self._create_pattern_embed(pattern)

            # Discord通知を送信
            success = await self.discord_sender.send_embed(embed)

            if success:
                print(f"    ✅ Discord notification sent successfully")
            else:
                print(f"    ❌ Discord notification failed")

        except Exception as e:
            print(f"    ❌ Discord notification error: {e}")
            logger.error(f"Discord notification error: {e}")

    async def _test_discord_notification_with_sender(self, pattern, discord_sender):
        """
        個別のパターンをDiscordに通知（新しいメソッド）
        """
        try:
            print(f"  📢 Sending Discord notification for {pattern.pattern_name}...")

            # パターン情報をDiscord Embed形式で作成
            embed = self._create_pattern_embed(pattern)

            # Discord通知を送信
            success = await discord_sender.send_embed(embed)

            if success:
                print(f"    ✅ Discord notification sent successfully")
            else:
                print(f"    ❌ Discord notification failed")

        except Exception as e:
            print(f"    ❌ Discord notification error: {e}")
            logger.error(f"Discord notification error: {e}")

    def _create_pattern_embed(self, pattern):
        """
        パターン検出結果のDiscord Embedを作成
        """
        from datetime import datetime

        # 方向に応じた色と絵文字を設定
        direction_config = {
            "BUY": {"color": 0x00FF00, "emoji": "🟢", "text": "買い"},
            "SELL": {"color": 0xFF0000, "emoji": "🔴", "text": "売り"},
            "hold": {"color": 0xFFFF00, "emoji": "🟡", "text": "ホールド"},
        }

        config = direction_config.get(pattern.direction, direction_config["hold"])

        # 信頼度に応じた評価
        confidence_emoji = (
            "🟢"
            if pattern.confidence_score >= 80
            else "🟡" if pattern.confidence_score >= 60 else "🔴"
        )

        # detection_dataから値を取得
        detection_data = pattern.detection_data or {}
        entry_price = detection_data.get("entry_price", 0.0)
        stop_loss = detection_data.get("stop_loss", 0.0)
        take_profit = detection_data.get("take_profit", 0.0)
        timeframe = detection_data.get("timeframe", "Unknown")
        description = detection_data.get("description", "パターンが検出されました")

        # 埋め込みデータを作成
        embed = {
            "title": f"{config['emoji']} {pattern.pattern_name}",
            "description": description,
            "color": config["color"],
            "fields": [
                {"name": "通貨ペア", "value": pattern.currency_pair, "inline": True},
                {
                    "name": "方向",
                    "value": f"{config['emoji']} {config['text']}",
                    "inline": True,
                },
                {
                    "name": "信頼度",
                    "value": f"{confidence_emoji} {pattern.confidence_score:.1f}%",
                    "inline": True,
                },
                {"name": "時間軸", "value": timeframe, "inline": True},
                {
                    "name": "エントリー価格",
                    "value": f"¥{entry_price:.2f}",
                    "inline": True,
                },
                {
                    "name": "損切り",
                    "value": f"¥{stop_loss:.2f}",
                    "inline": True,
                },
                {
                    "name": "利確",
                    "value": f"¥{take_profit:.2f}",
                    "inline": True,
                },
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "USD/JPY パターン検出システム"},
        }

        # リスク/リワード比を計算
        if entry_price and stop_loss and take_profit:
            if pattern.direction == "BUY":
                risk = entry_price - stop_loss
                reward = take_profit - entry_price
            else:
                risk = stop_loss - entry_price
                reward = entry_price - take_profit

            if risk > 0:
                rr_ratio = reward / risk
                embed["fields"].append(
                    {
                        "name": "リスク/リワード比",
                        "value": f"{rr_ratio:.2f}",
                        "inline": True,
                    }
                )

        return embed

    async def test_discord_only(self):
        """
        Discord通知のみのテスト
        """
        print("Testing Discord notification only...")
        logger.info("Testing Discord notification only...")

        try:
            # DiscordWebhookSenderを正しく初期化して使用
            discord_sender = DiscordWebhookSender(self.webhook_url)

            async with discord_sender:
                # シンプルメッセージでテスト
                print("  📝 Testing simple message...")
                success = await discord_sender.send_simple_message(
                    "🧪 パターン検出システムテスト - シンプルメッセージ"
                )

                if success:
                    print("    ✅ Simple message sent successfully")
                else:
                    print("    ❌ Simple message failed")

                # テスト通知を送信
                print("  📝 Testing embed notification...")
                success = await discord_sender.send_test_notification()

                if success:
                    print("✅ Discord test notification sent successfully")
                else:
                    print("❌ Discord test notification failed")

        except Exception as e:
            print(f"❌ Discord notification test failed: {e}")
            logger.error(f"Discord notification test failed: {e}")

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
                PatternDetectionModel.detection_data.contains({"test": True})
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
        print("Complete pattern detection test cleanup completed")
        logger.info("Complete pattern detection test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting complete pattern detection test...")
    logger.info("Starting complete pattern detection test...")

    tester = CompletePatternDetectionTester()

    try:
        await tester.setup()

        # Discord通知のみのテスト
        await tester.test_discord_only()

        # パターン作成とDiscord通知のテスト
        await tester.test_pattern_creation_and_notification()

        # テストデータをクリーンアップ
        await tester.cleanup_test_data()

        print("Complete pattern detection test completed successfully!")
        logger.info("Complete pattern detection test completed successfully!")

    except Exception as e:
        print(f"Complete pattern detection test failed: {e}")
        logger.error(f"Complete pattern detection test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
