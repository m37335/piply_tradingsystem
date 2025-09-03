"""
Discord Webhook送信

実際のDiscord Webhookを使用して通知を送信するクラス
"""

import asyncio
import json
import logging
from typing import Any, Dict, Optional

import aiohttp


class DiscordWebhookSender:
    """Discord Webhook送信クラス"""

    def __init__(self, webhook_url: str = ""):
        self.webhook_url = webhook_url
        self.session = None
        self.setup_logging()

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        if self.session:
            await self.session.close()

    async def send_embed(self, embed: Dict[str, Any]) -> bool:
        """
        Discord Embedを送信
        
        Args:
            embed: Discord Embed形式のデータ
            
        Returns:
            送信成功時はTrue
        """
        if not self.webhook_url:
            self.logger.warning("Webhook URLが設定されていません")
            return False

        payload = {
            "embeds": [embed]
        }

        try:
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 204:
                    self.logger.info("Discord通知を送信しました")
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
            self.logger.warning("Webhook URLが設定されていません")
            return False

        payload = {
            "content": message
        }

        try:
            async with self.session.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 204:
                    self.logger.info("Discordメッセージを送信しました")
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
        test_embed = {
            "title": "🧪 テスト通知",
            "description": "Discord通知システムのテストです",
            "color": 0x00FF00,
            "fields": [
                {
                    "name": "テスト項目",
                    "value": "✅ 正常に動作しています",
                    "inline": True
                },
                {
                    "name": "時刻",
                    "value": "2025-08-10 08:00:00",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Discord通知パターンシステム"
            }
        }

        return await self.send_embed(test_embed)

    def set_webhook_url(self, webhook_url: str):
        """Webhook URLを設定"""
        self.webhook_url = webhook_url
        self.logger.info("Webhook URLを設定しました")


# テスト用の関数
async def test_discord_webhook():
    """Discord Webhookテスト"""
    # テスト用のWebhook URL（実際のURLに置き換えてください）
    test_webhook_url = "YOUR_DISCORD_WEBHOOK_URL_HERE"
    
    async with DiscordWebhookSender(test_webhook_url) as sender:
        # テスト通知を送信
        success = await sender.send_test_notification()
        
        if success:
            print("✅ Discordテスト通知を送信しました")
        else:
            print("❌ Discordテスト通知の送信に失敗しました")


if __name__ == "__main__":
    asyncio.run(test_discord_webhook())
