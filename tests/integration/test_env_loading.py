#!/usr/bin/env python3
"""
Environment Loading Test
.envファイルからの環境変数読み込みテスト
"""

import os
import sys
from datetime import datetime

import pytz


def test_env_loading():
    """環境変数読み込みテスト"""
    print("🧪 環境変数読み込みテスト")
    print(
        f"⏰ 実行時刻: {datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M:%S JST')}"
    )
    print("")

    # 重要な環境変数をチェック
    env_vars = [
        "ALPHA_VANTAGE_API_KEY",
        "OPENAI_API_KEY",
        "DISCORD_WEBHOOK_URL",
        "JWT_SECRET",
    ]

    print("📋 環境変数確認:")
    all_loaded = True

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # セキュリティのため最初の10文字のみ表示
            masked_value = value[:10] + "..." if len(value) > 10 else value
            print(f"  ✅ {var}: {masked_value}")
        else:
            print(f"  ❌ {var}: 未設定")
            all_loaded = False

    print("")

    if all_loaded:
        print("✅ すべての環境変数が正常に読み込まれました")

        # Alpha Vantage API制限チェック
        api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
        if api_key == "demo" or api_key == "1UOV5KWV9ETG6WCK":
            print("ℹ️ Alpha Vantage: デモ/制限キーを使用中")
            print("   本格運用には有料プランが必要です")
            print("   📋 https://www.alphavantage.co/premium/")

        return True
    else:
        print("❌ 環境変数の設定を確認してください")
        return False


def test_discord_connection():
    """Discord Webhook接続テスト"""
    webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_MONITORING_WEBHOOK_URL が設定されていません")
        return False

    try:
        import asyncio

        import httpx

        async def send_test():
            message = {
                "content": "🧪 **Cron環境変数テスト**",
                "embeds": [
                    {
                        "title": "✅ Environment Test Success",
                        "description": "crontabから.envファイルの読み込みが成功しました",
                        "color": 0x00FF00,
                        "fields": [
                            {
                                "name": "⏰ 時刻",
                                "value": datetime.now(
                                    pytz.timezone("Asia/Tokyo")
                                ).strftime("%H:%M:%S JST"),
                                "inline": True,
                            },
                            {
                                "name": "🔧 実行元",
                                "value": "cron環境変数テスト",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Environment Loading Test"},
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(webhook_url, json=message)
                return response.status_code == 204

        result = asyncio.run(send_test())
        if result:
            print("✅ Discord通知テスト成功")
        else:
            print("❌ Discord通知テスト失敗")
        return result

    except Exception as e:
        print(f"❌ Discord接続エラー: {str(e)}")
        return False


def main():
    """メイン実行"""
    print("🔧 Exchange Analytics 環境変数テスト")
    print("=" * 50)

    # 環境変数読み込みテスト
    env_ok = test_env_loading()

    print("")

    # Discord接続テスト
    if env_ok:
        discord_ok = test_discord_connection()

        print("")
        print("📊 テスト結果サマリー:")
        print(f"  環境変数読み込み: {'✅' if env_ok else '❌'}")
        print(f"  Discord通知: {'✅' if discord_ok else '❌'}")

        if env_ok and discord_ok:
            print("")
            print("🎉 すべてのテストが成功しました！")
            print("crontabから正常に.envファイルが読み込まれています")
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
