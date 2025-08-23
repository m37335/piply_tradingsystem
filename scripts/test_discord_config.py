"""
Discord設定と経済指標専用Webhook URLのテストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.infrastructure.config.notification import DiscordConfig
from src.infrastructure.external.discord import DiscordClient


async def test_discord_config():
    """Discord設定のテスト"""
    print("=== Discord設定テスト ===")

    try:
        # 設定の読み込み
        config = DiscordConfig.from_env()
        print("✅ Discord設定読み込み完了")
        
        # 設定の検証
        if config.validate():
            print("✅ Discord設定検証完了")
        else:
            print("❌ Discord設定検証失敗")
            return False
        
        # 設定サマリーの表示
        summary = config.get_config_summary()
        print(f"📊 設定サマリー: {summary}")
        
        # Webhook URLの確認
        default_url = config.get_webhook_url("default")
        economic_url = config.get_webhook_url("economic_indicators")
        
        print(f"🔗 デフォルトWebhook URL: {default_url[:50]}...")
        print(f"🔗 経済指標専用Webhook URL: {economic_url[:50]}...")
        
        # 経済指標専用URLが設定されているか確認
        if economic_url and economic_url != default_url:
            print("✅ 経済指標専用Webhook URLが正しく設定されています")
        else:
            print("⚠️ 経済指標専用Webhook URLが設定されていません")
        
        return True

    except Exception as e:
        print(f"❌ Discord設定テストエラー: {e}")
        return False


async def test_discord_client():
    """Discordクライアントのテスト"""
    print("\n=== Discordクライアントテスト ===")

    try:
        # 設定の読み込み
        config = DiscordConfig.from_env()
        
        # クライアントの作成
        client = DiscordClient(
            webhook_url=config.webhook_url,
            config=config
        )
        print("✅ Discordクライアント作成完了")
        
        # 接続テスト
        connected = await client.connect()
        if connected:
            print("✅ Discord接続完了")
        else:
            print("❌ Discord接続失敗")
            return False
        
        # 接続テスト
        test_result = await client.test_connection()
        if test_result:
            print("✅ Discord接続テスト成功")
        else:
            print("❌ Discord接続テスト失敗")
        
        # 状態情報の取得
        status = client.get_status()
        print(f"📊 クライアント状態: {status}")
        
        # 接続終了
        await client.disconnect()
        print("✅ Discord接続終了")
        
        return True

    except Exception as e:
        print(f"❌ Discordクライアントテストエラー: {e}")
        return False


async def test_webhook_url_selection():
    """Webhook URL選択のテスト"""
    print("\n=== Webhook URL選択テスト ===")

    try:
        # 設定の読み込み
        config = DiscordConfig.from_env()
        
        # クライアントの作成
        client = DiscordClient(
            webhook_url=config.webhook_url,
            config=config
        )
        
        # 異なるチャンネルタイプでのWebhook URL取得
        default_url = client._get_webhook_url("default")
        economic_url = client._get_webhook_url("economic_indicators")
        
        print(f"🔗 デフォルトチャンネル: {default_url[:50]}...")
        print(f"🔗 経済指標チャンネル: {economic_url[:50]}...")
        
        # 経済指標専用URLが使用されることを確認
        if economic_url and economic_url != default_url:
            print("✅ 経済指標専用Webhook URLが正しく選択されます")
            return True
        else:
            print("⚠️ 経済指標専用Webhook URLが設定されていません")
            return False

    except Exception as e:
        print(f"❌ Webhook URL選択テストエラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("Discord設定と経済指標専用Webhook URLテスト")
    print("=" * 60)

    # 各テストの実行
    config_ok = await test_discord_config()
    client_ok = await test_discord_client()
    webhook_ok = await test_webhook_url_selection()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  Discord設定: {'✅' if config_ok else '❌'}")
    print(f"  Discordクライアント: {'✅' if client_ok else '❌'}")
    print(f"  Webhook URL選択: {'✅' if webhook_ok else '❌'}")

    if all([config_ok, client_ok, webhook_ok]):
        print("\n🎉 全てのDiscordテストが成功しました！")
        print("📢 経済指標専用チャンネルへの配信準備完了！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
