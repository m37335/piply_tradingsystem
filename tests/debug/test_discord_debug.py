#!/usr/bin/env python3
"""
Discord通知の詳細デバッグテスト
"""

import asyncio
import os

import aiohttp
from dotenv import load_dotenv

load_dotenv()


async def test_discord_debug():
    """Discord通知の詳細デバッグテスト"""
    print("🔍 Discord通知の詳細デバッグテスト")
    print("=" * 60)

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    print(f"Webhook URL: {webhook_url}")

    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URLが設定されていません")
        return

    # テストメッセージ
    test_message = {
        "content": "🧪 Discord通知デバッグテスト",
        "embeds": [
            {
                "title": "🚨 最適化アラートシステム",
                "description": "🟢 **買いエントリー**\n📈 **上昇トレンドシグナル検出**",
                "color": 0x00FF00,  # 緑色
                "fields": [
                    {
                        "name": "📊 シグナル詳細",
                        "value": (
                            "時刻: 2025-01-14 00:00:00\n"
                            "エントリー方向: 🟢 買いエントリー\n"
                            "RSI: 37.3\n"
                            "現在価格: 146.959"
                        ),
                        "inline": False,
                    },
                    {
                        "name": "🎯 エントリー戦略",
                        "value": "エントリー価格: 147.289\n利確目標: 147.289\n損切り: 147.289",
                        "inline": True,
                    },
                    {
                        "name": "💰 期待値",
                        "value": "期待利益: 66.1pips\n期待リスク: 106.2pips\nリスク/リワード比: 0.62",
                        "inline": True,
                    },
                ],
                "footer": {"text": "最適化された移動平均線戦略による自動アラート"},
            }
        ],
    }

    try:
        print("📤 Discordに直接HTTPリクエストを送信中...")

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=test_message) as response:
                print(f"📊 HTTP Status: {response.status}")
                print(f"📊 Response Headers: {dict(response.headers)}")

                response_text = await response.text()
                print(f"📊 Response Body: {response_text}")

                if response.status == 204:
                    print("✅ Discord通知成功！(HTTP 204)")
                elif response.status == 200:
                    print("✅ Discord通知成功！(HTTP 200)")
                else:
                    print(f"❌ Discord通知失敗！(HTTP {response.status})")

    except Exception as e:
        print(f"❌ Discord通知エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_discord_debug())
