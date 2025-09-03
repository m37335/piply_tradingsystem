"""
Discord通知サービス

パターン検出結果をDiscordに通知するサービス
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp

from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DiscordNotificationService:
    """Discord通知サービス"""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url or os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL", "")
        self.session = None
        self.logger = logger

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()

    async def send_pattern_notification(self, pattern: PatternDetectionModel) -> bool:
        """
        パターン検出結果をDiscordに通知

        Args:
            pattern: パターン検出結果

        Returns:
            送信成功時はTrue
        """
        if not self.webhook_url:
            self.logger.warning("Discord Webhook URLが設定されていません")
            return False

        try:
            # Discord Embedを作成
            embed = self._create_pattern_embed(pattern)

            # 送信
            success = await self._send_embed(embed)

            if success:
                self.logger.info(f"パターン通知を送信しました: {pattern.pattern_name}")
            else:
                self.logger.error(f"パターン通知の送信に失敗しました: {pattern.pattern_name}")

            return success

        except Exception as e:
            self.logger.error(f"パターン通知エラー: {e}")
            return False

    def _create_pattern_embed(self, pattern: PatternDetectionModel) -> Dict[str, Any]:
        """
        パターン検出結果のDiscord Embedを作成

        Args:
            pattern: パターン検出結果

        Returns:
            Discord Embed形式のデータ
        """
        # 方向に応じた色と絵文字を設定
        direction_config = {
            "buy": {"color": 0x00FF00, "emoji": "🟢", "text": "買い"},
            "sell": {"color": 0xFF0000, "emoji": "🔴", "text": "売り"},
            "hold": {"color": 0xFFFF00, "emoji": "🟡", "text": "ホールド"},
        }

        config = direction_config.get(pattern.direction, direction_config["hold"])

        # 信頼度に応じた評価
        confidence_emoji = (
            "🟢"
            if pattern.confidence_score >= 80
            else "🟡"
            if pattern.confidence_score >= 60
            else "🔴"
        )

        # 埋め込みデータを作成
        embed = {
            "title": f"{config['emoji']} {pattern.pattern_name}",
            "description": pattern.description or "パターンが検出されました",
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
                {"name": "時間軸", "value": pattern.timeframe, "inline": True},
                {
                    "name": "エントリー価格",
                    "value": f"¥{pattern.entry_price:.2f}",
                    "inline": True,
                },
                {
                    "name": "損切り",
                    "value": f"¥{pattern.stop_loss:.2f}",
                    "inline": True,
                },
                {
                    "name": "利確",
                    "value": f"¥{pattern.take_profit:.2f}",
                    "inline": True,
                },
            ],
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "USD/JPY パターン検出システム"},
        }

        # リスク/リワード比を計算
        if pattern.entry_price and pattern.stop_loss and pattern.take_profit:
            if pattern.direction == "buy":
                risk = pattern.entry_price - pattern.stop_loss
                reward = pattern.take_profit - pattern.entry_price
            else:
                risk = pattern.stop_loss - pattern.entry_price
                reward = pattern.entry_price - pattern.take_profit

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

    async def _send_embed(self, embed: Dict[str, Any]) -> bool:
        """
        Discord Embedを送信

        Args:
            embed: Discord Embed形式のデータ

        Returns:
            送信成功時はTrue
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {"embeds": [embed]}

        try:
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 204:
                    return True
                else:
                    self.logger.error(f"Discord送信エラー: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Discord送信エラー: {e}")
            return False

    async def send_simple_message(self, message: str) -> bool:
        """
        シンプルメッセージを送信

        Args:
            message: 送信するメッセージ

        Returns:
            送信成功時はTrue
        """
        if not self.webhook_url:
            self.logger.warning("Discord Webhook URLが設定されていません")
            return False

        if not self.session:
            self.session = aiohttp.ClientSession()

        payload = {"content": message}

        try:
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                if response.status == 204:
                    return True
                else:
                    self.logger.error(f"Discord送信エラー: {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Discord送信エラー: {e}")
            return False

    async def send_test_notification(self) -> bool:
        """
        テスト通知を送信

        Returns:
            送信成功時はTrue
        """
        test_message = "🧪 USD/JPY パターン検出システムのテスト通知です"
        return await self.send_simple_message(test_message)

    def set_webhook_url(self, webhook_url: str):
        """
        Webhook URLを設定

        Args:
            webhook_url: Discord Webhook URL
        """
        self.webhook_url = webhook_url
        self.logger.info("Discord Webhook URLを設定しました")


async def test_discord_notification():
    """
    Discord通知のテスト関数
    """
    print("Discord通知のテストを開始します...")

    # テスト用のパターン検出結果を作成
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

    # Discord通知サービスを初期化
    async with DiscordNotificationService() as discord_service:
        # テスト通知を送信
        success = await discord_service.send_pattern_notification(test_pattern)

        if success:
            print("✅ Discord通知テストが成功しました")
        else:
            print("❌ Discord通知テストが失敗しました")

    print("Discord通知のテストが完了しました")


if __name__ == "__main__":
    asyncio.run(test_discord_notification())
