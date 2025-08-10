#!/usr/bin/env python3
"""
Discord Webhook設定確認テスト
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender


class WebhookConfigTester:
    def __init__(self):
        self.config_manager = None

    async def setup(self):
        """テスト環境のセットアップ"""
        print("Webhook設定確認テストを開始...")
        
        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager()
        
        print("✅ 設定マネージャーの初期化完了")

    async def test_webhook_configuration(self):
        """Webhook設定の確認"""
        print("\n=== Webhook設定確認 ===")
        
        # 通常のDiscord Webhook URL
        discord_webhook = self.config_manager.get("notifications.discord.webhook_url")
        print(f"通常のDiscord Webhook URL: {discord_webhook[:50]}..." if discord_webhook else "設定されていません")
        
        # システム監視用Discord Webhook URL
        monitoring_webhook = self.config_manager.get("notifications.discord_monitoring.webhook_url")
        print(f"システム監視用Webhook URL: {monitoring_webhook[:50]}..." if monitoring_webhook else "設定されていません")
        
        # 環境変数から直接確認
        env_discord = os.getenv("DISCORD_WEBHOOK_URL")
        env_monitoring = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
        
        print(f"\n環境変数 DISCORD_WEBHOOK_URL: {env_discord[:50]}..." if env_discord else "設定されていません")
        print(f"環境変数 DISCORD_MONITORING_WEBHOOK_URL: {env_monitoring[:50]}..." if env_monitoring else "設定されていません")
        
        # 設定が正しく読み込まれているか確認
        if monitoring_webhook and monitoring_webhook != discord_webhook:
            print("✅ システム監視用Webhook URLが正しく設定されています")
            return True
        else:
            print("❌ システム監視用Webhook URLが正しく設定されていません")
            return False

    async def test_monitoring_webhook_send(self):
        """システム監視用Webhookでの送信テスト"""
        print("\n=== システム監視用Webhook送信テスト ===")
        
        monitoring_webhook = self.config_manager.get("notifications.discord_monitoring.webhook_url")
        if not monitoring_webhook:
            print("❌ システム監視用Webhook URLが設定されていません")
            return False
        
        try:
            async with DiscordWebhookSender(monitoring_webhook) as sender:
                # システム監視用のテストメッセージを送信
                embed = {
                    "title": "🔧 システム監視テスト",
                    "description": "システム監視・ログ管理システムチャンネルへの配信テストです",
                    "color": 0x00ff00,  # 緑色
                    "fields": [
                        {
                            "name": "テスト項目",
                            "value": "Webhook設定確認",
                            "inline": True
                        },
                        {
                            "name": "ステータス",
                            "value": "✅ 成功",
                            "inline": True
                        }
                    ],
                    "timestamp": "2025-08-10T15:30:00.000Z"
                }
                
                await sender.send_embed(embed)
                print("✅ システム監視用Webhookでの送信テスト成功")
                return True
                
        except Exception as e:
            print(f"❌ システム監視用Webhookでの送信テスト失敗: {e}")
            return False

    async def test_regular_webhook_send(self):
        """通常のWebhookでの送信テスト"""
        print("\n=== 通常のWebhook送信テスト ===")
        
        discord_webhook = self.config_manager.get("notifications.discord.webhook_url")
        if not discord_webhook:
            print("❌ 通常のDiscord Webhook URLが設定されていません")
            return False
        
        try:
            async with DiscordWebhookSender(discord_webhook) as sender:
                # 通常のテストメッセージを送信
                embed = {
                    "title": "📊 パターン検出テスト",
                    "description": "一般チャンネルへの配信テストです",
                    "color": 0x0000ff,  # 青色
                    "fields": [
                        {
                            "name": "テスト項目",
                            "value": "パターン検出通知",
                            "inline": True
                        },
                        {
                            "name": "ステータス",
                            "value": "✅ 成功",
                            "inline": True
                        }
                    ],
                    "timestamp": "2025-08-10T15:30:00.000Z"
                }
                
                await sender.send_embed(embed)
                print("✅ 通常のWebhookでの送信テスト成功")
                return True
                
        except Exception as e:
            print(f"❌ 通常のWebhookでの送信テスト失敗: {e}")
            return False

    async def run_tests(self):
        """全テストを実行"""
        await self.setup()
        
        # Webhook設定確認
        config_ok = await self.test_webhook_configuration()
        
        if config_ok:
            # システム監視用Webhook送信テスト
            monitoring_ok = await self.test_monitoring_webhook_send()
            
            # 通常のWebhook送信テスト
            regular_ok = await self.test_regular_webhook_send()
            
            if monitoring_ok and regular_ok:
                print("\n🎉 全てのテストが成功しました！")
                print("✅ システム監視用Webhook: #システム監視・ログ管理システムチャンネル")
                print("✅ 通常のWebhook: #一般チャンネル")
            else:
                print("\n⚠️ 一部のテストが失敗しました")
        else:
            print("\n❌ Webhook設定に問題があります")


async def main():
    tester = WebhookConfigTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
