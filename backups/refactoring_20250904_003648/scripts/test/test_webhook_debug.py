#!/usr/bin/env python3
"""
Discord Webhook詳細デバッグテスト
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


class WebhookDebugTester:
    def __init__(self):
        self.config_manager = None
        self.system_monitor = None
        self.log_manager = None

    async def setup(self):
        """テスト環境のセットアップ"""
        print("=== Discord Webhook詳細デバッグテスト ===")

        # 設定マネージャーを初期化
        self.config_manager = SystemConfigManager()

        # システム監視とログ管理を初期化
        self.system_monitor = SystemMonitor(self.config_manager)
        self.log_manager = LogManager(self.config_manager)

        print("✅ 初期化完了")

    async def debug_webhook_usage(self):
        """Webhook使用状況の詳細デバッグ"""
        print("\n=== Webhook使用状況デバッグ ===")

        # 環境変数から直接取得
        env_discord = os.getenv("DISCORD_WEBHOOK_URL")
        env_monitoring = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")

        print(f"環境変数:")
        print(f"  DISCORD_WEBHOOK_URL: {env_discord}")
        print(f"  DISCORD_MONITORING_WEBHOOK_URL: {env_monitoring}")

        # 設定マネージャーから取得
        config_discord = self.config_manager.get("notifications.discord.webhook_url")
        config_monitoring = self.config_manager.get(
            "notifications.discord_monitoring.webhook_url"
        )

        print(f"\n設定マネージャー:")
        print(f"  notifications.discord.webhook_url: {config_discord}")
        print(f"  notifications.discord_monitoring.webhook_url: {config_monitoring}")

        # システム監視が実際に使用するWebhook URLを確認
        print(f"\n=== システム監視の実際の使用状況 ===")

        # send_system_status_to_discordメソッドの動作をシミュレート
        webhook_url = self.config_manager.get(
            "notifications.discord_monitoring.webhook_url"
        )
        if not webhook_url:
            webhook_url = self.config_manager.get("notifications.discord.webhook_url")

        print(f"システム監視が使用するWebhook URL: {webhook_url}")
        print(f"これは通常のWebhookと同じか: {webhook_url == env_discord}")
        print(f"これは監視用Webhookと同じか: {webhook_url == env_monitoring}")

        # ログ管理が実際に使用するWebhook URLを確認
        print(f"\n=== ログ管理の実際の使用状況 ===")

        # send_log_summary_to_discordメソッドの動作をシミュレート
        log_webhook_url = self.config_manager.get(
            "notifications.discord_monitoring.webhook_url"
        )
        if not log_webhook_url:
            log_webhook_url = self.config_manager.get(
                "notifications.discord.webhook_url"
            )

        print(f"ログ管理が使用するWebhook URL: {log_webhook_url}")
        print(f"これは通常のWebhookと同じか: {log_webhook_url == env_discord}")
        print(f"これは監視用Webhookと同じか: {log_webhook_url == env_monitoring}")

        return webhook_url, log_webhook_url

    async def test_actual_system_monitor_methods(self):
        """実際のシステム監視メソッドをテスト"""
        print(f"\n=== 実際のシステム監視メソッドテスト ===")

        # システム監視のメソッドを実際に呼び出してWebhook URLを確認
        try:
            # システム監視のメソッド内で使用されるWebhook URLを確認
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )

            print(f"send_system_status_to_discordが使用するWebhook URL: {webhook_url}")

            # 実際に送信テスト
            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "🔍 システム監視デバッグテスト",
                    "description": f"このメッセージが送信されるチャンネルを確認してください\n使用URL: {webhook_url}",
                    "color": 0xFF0000,  # 赤色
                    "fields": [
                        {
                            "name": "デバッグ情報",
                            "value": f"Webhook URL: {webhook_url[:50]}...",
                            "inline": False,
                        }
                    ],
                }

                await sender.send_embed(embed)
                print("✅ システム監視デバッグメッセージを送信しました")

        except Exception as e:
            print(f"❌ エラー: {e}")

    async def test_actual_log_manager_methods(self):
        """実際のログ管理メソッドをテスト"""
        print(f"\n=== 実際のログ管理メソッドテスト ===")

        try:
            # ログ管理のメソッド内で使用されるWebhook URLを確認
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )

            print(f"send_log_summary_to_discordが使用するWebhook URL: {webhook_url}")

            # 実際に送信テスト
            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "📝 ログ管理デバッグテスト",
                    "description": f"このメッセージが送信されるチャンネルを確認してください\n使用URL: {webhook_url}",
                    "color": 0x00FF00,  # 緑色
                    "fields": [
                        {
                            "name": "デバッグ情報",
                            "value": f"Webhook URL: {webhook_url[:50]}...",
                            "inline": False,
                        }
                    ],
                }

                await sender.send_embed(embed)
                print("✅ ログ管理デバッグメッセージを送信しました")

        except Exception as e:
            print(f"❌ エラー: {e}")

    async def run_debug(self):
        """デバッグを実行"""
        await self.setup()

        # Webhook使用状況の詳細デバッグ
        system_webhook, log_webhook = await self.debug_webhook_usage()

        # 実際のメソッドをテスト
        await self.test_actual_system_monitor_methods()
        await self.test_actual_log_manager_methods()

        print(f"\n=== デバッグ結果 ===")
        print(f"システム監視Webhook: {system_webhook}")
        print(f"ログ管理Webhook: {log_webhook}")
        print(f"両方が同じWebhookを使用しているか: {system_webhook == log_webhook}")

        env_discord = os.getenv("DISCORD_WEBHOOK_URL")
        env_monitoring = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")

        print(f"\n期待される動作:")
        print(f"通常のWebhook ({env_discord[:50]}...): #一般チャンネル")
        print(f"監視用Webhook ({env_monitoring[:50]}...): #システム監視・ログ管理システムチャンネル")

        print(f"\n実際の動作:")
        print(
            f"システム監視: {'#一般' if system_webhook == env_discord else '#システム監視・ログ管理システム'}"
        )
        print(f"ログ管理: {'#一般' if log_webhook == env_discord else '#システム監視・ログ管理システム'}")


async def main():
    tester = WebhookDebugTester()
    await tester.run_debug()


if __name__ == "__main__":
    asyncio.run(main())
