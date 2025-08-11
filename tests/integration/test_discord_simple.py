#!/usr/bin/env python3
"""
Discord Webhook Sender 直接テスト
"""

import asyncio
import os

from src.infrastructure.discord_webhook_sender import DiscordWebhookSender


async def test_discord():
    """Discord Webhook Sender を直接テスト"""

    # .envファイルからWebhook URLを取得
    webhook_url = "https://canary.discord.com/api/webhooks/1403643478361116672/nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ"

    print(f"Testing Discord Webhook: {webhook_url}")

    # DiscordWebhookSenderを初期化
    sender = DiscordWebhookSender(webhook_url)

    try:
        # コンテキストマネージャーを使用
        async with sender:
            print("✅ Session created successfully")

            # シンプルメッセージを送信
            print("📝 Sending simple message...")
            success = await sender.send_simple_message("🧪 直接テスト - シンプルメッセージ")

            if success:
                print("✅ Simple message sent successfully")
            else:
                print("❌ Simple message failed")

            # Embedメッセージを送信
            print("📝 Sending embed message...")
            test_embed = {
                "title": "🧪 直接テスト",
                "description": "DiscordWebhookSenderの直接テストです",
                "color": 0x00FF00,
                "fields": [
                    {
                        "name": "テスト結果",
                        "value": "✅ 正常に動作しています",
                        "inline": True,
                    }
                ],
            }

            success = await sender.send_embed(test_embed)

            if success:
                print("✅ Embed message sent successfully")
            else:
                print("❌ Embed message failed")

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_discord())
