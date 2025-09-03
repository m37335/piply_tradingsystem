#!/usr/bin/env python3
"""
Discord Webhook詳細確認テスト
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.infrastructure.monitoring.log_manager import LogManager
from src.infrastructure.monitoring.system_monitor import SystemMonitor


class WebhookVerificationTester:
    def __init__(self):
        self.config_manager = None
        self.system_monitor = None
        self.log_manager = None

    async def setup(self):
        """テスト環境のセットアップ"""
        print("=== Discord Webhook詳細確認テスト ===")

        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager()

        # システム監視とログ管理を初期化
        self.system_monitor = SystemMonitor(self.config_manager)
        self.log_manager = LogManager(self.config_manager)

        print("✅ 初期化完了")

    async def verify_webhook_urls(self):
        """Webhook URLの詳細確認"""
        print("\n=== Webhook URL詳細確認 ===")

        # 環境変数から直接取得
        env_discord = os.getenv("DISCORD_WEBHOOK_URL")
        env_monitoring = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")

        print(f"環境変数 DISCORD_WEBHOOK_URL:")
        print(f"  {env_discord}")
        print(f"環境変数 DISCORD_MONITORING_WEBHOOK_URL:")
        print(f"  {env_monitoring}")

        # 設定マネージャーから取得
        config_discord = self.config_manager.get("notifications.discord.webhook_url")
        config_monitoring = self.config_manager.get(
            "notifications.discord_monitoring.webhook_url"
        )

        print(f"\n設定マネージャー notifications.discord.webhook_url:")
        print(f"  {config_discord}")
        print(f"設定マネージャー notifications.discord_monitoring.webhook_url:")
        print(f"  {config_monitoring}")

        # 比較
        print(f"\n=== 比較結果 ===")
        print(f"通常のWebhook URL一致: {env_discord == config_discord}")
        print(f"監視用Webhook URL一致: {env_monitoring == config_monitoring}")

        return env_discord, env_monitoring

    async def test_system_monitor_webhook_usage(self):
        """システム監視が使用するWebhook URLの確認"""
        print("\n=== システム監視Webhook使用確認 ===")

        # システム監視のメソッド内で使用されるWebhook URLを確認
        try:
            # システム監視の設定を確認
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )

            print(f"システム監視が使用するWebhook URL:")
            print(f"  {webhook_url}")

            # 実際に送信テスト
            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "🔍 Webhook確認テスト",
                    "description": "このメッセージが送信されるチャンネルを確認してください",
                    "color": 0xFF0000,  # 赤色
                    "fields": [
                        {
                            "name": "テスト種別",
                            "value": "システム監視Webhook確認",
                            "inline": True,
                        },
                        {
                            "name": "使用URL",
                            "value": f"`{webhook_url[:50]}...`",
                            "inline": False,
                        },
                    ],
                }

                await sender.send_embed(embed)
                print("✅ システム監視Webhook確認メッセージを送信しました")
                print("📱 Discordでどちらのチャンネルに送信されたか確認してください")

        except Exception as e:
            print(f"❌ エラー: {e}")

    async def test_log_manager_webhook_usage(self):
        """ログ管理が使用するWebhook URLの確認"""
        print("\n=== ログ管理Webhook使用確認 ===")

        try:
            # ログ管理の設定を確認
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )

            print(f"ログ管理が使用するWebhook URL:")
            print(f"  {webhook_url}")

            # 実際に送信テスト
            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "📝 ログ管理確認テスト",
                    "description": "このメッセージが送信されるチャンネルを確認してください",
                    "color": 0x00FF00,  # 緑色
                    "fields": [
                        {
                            "name": "テスト種別",
                            "value": "ログ管理Webhook確認",
                            "inline": True,
                        },
                        {
                            "name": "使用URL",
                            "value": f"`{webhook_url[:50]}...`",
                            "inline": False,
                        },
                    ],
                }

                await sender.send_embed(embed)
                print("✅ ログ管理Webhook確認メッセージを送信しました")
                print("📱 Discordでどちらのチャンネルに送信されたか確認してください")

        except Exception as e:
            print(f"❌ エラー: {e}")

    async def run_verification(self):
        """詳細確認を実行"""
        await self.setup()

        # Webhook URLの詳細確認
        discord_url, monitoring_url = await self.verify_webhook_urls()

        print(f"\n=== 期待される動作 ===")
        print(f"通常のWebhook ({discord_url[:50]}...): #一般チャンネル")
        print(f"監視用Webhook ({monitoring_url[:50]}...): #システム監視・ログ管理システムチャンネル")

        # システム監視のWebhook使用確認
        await self.test_system_monitor_webhook_usage()

        # ログ管理のWebhook使用確認
        await self.test_log_manager_webhook_usage()

        print(f"\n=== 確認手順 ===")
        print("1. Discordで#一般チャンネルを確認")
        print("2. Discordで#システム監視・ログ管理システムチャンネルを確認")
        print("3. どちらのチャンネルにメッセージが送信されているか確認")


async def main():
    tester = WebhookVerificationTester()
    await tester.run_verification()


if __name__ == "__main__":
    asyncio.run(main())
