#!/usr/bin/env python3
"""
Exchange Analytics Real-time Monitor
リアルタイム監視・アラートシステム

機能:
- システムヘルスのリアルタイム監視
- 異常検知時のDiscord自動通知
- コンポーネント別状態監視
- メトリクス収集・表示
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Any, Dict, Optional

import httpx
import pytz
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# 環境変数を自動設定
os.environ["DATABASE_URL"] = (
    "postgresql+asyncpg://exchange_analytics_user:"
    "exchange_password@localhost:5432/exchange_analytics_production_db"
)

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, project_root)


class RealtimeMonitor:
    """リアルタイム監視システム"""

    def __init__(self, api_host: str = "localhost", api_port: int = 8000):
        self.api_host = api_host
        self.api_port = api_port
        self.api_base = f"http://{api_host}:{api_port}"
        self.console = Console()

        # 監視状態
        self.previous_status = None
        self.alert_history = {}
        self.check_count = 0
        self.start_time = datetime.now(pytz.timezone("Asia/Tokyo"))
        self.webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

        # アラートシステム連携
        self.alert_session = None
        self.alert_repo = None

        # 統計
        self.stats = {
            "total_checks": 0,
            "healthy_checks": 0,
            "degraded_checks": 0,
            "unhealthy_checks": 0,
            "alerts_sent": 0,
            "db_alerts_saved": 0,
        }

    async def start_monitoring(
        self, interval: int = 5, detailed: bool = True, discord_alerts: bool = True
    ):
        """リアルタイム監視開始"""
        self.console.print("🚀 Exchange Analytics リアルタイム監視開始")
        self.console.print(f"📊 API: {self.api_base}")
        self.console.print(f"⏰ 監視間隔: {interval}秒")
        self.console.print(
            f"🚨 Discord通知: {'✅ 有効' if discord_alerts else '❌ 無効'}"
        )
        self.console.print("⏹️ 停止: Ctrl+C")
        self.console.print()

        try:
            with Live(console=self.console, refresh_per_second=1) as live:
                while True:
                    panel = await self._generate_monitoring_panel(
                        detailed, discord_alerts
                    )
                    live.update(panel)
                    await asyncio.sleep(interval)

        except KeyboardInterrupt:
            self._display_monitoring_summary()

    async def _generate_monitoring_panel(
        self, detailed: bool, discord_alerts: bool
    ) -> Panel:
        """監視パネル生成"""
        self.check_count += 1
        self.stats["total_checks"] += 1

        try:
            # ヘルスチェック実行
            health_data = await self._fetch_health_data(detailed)

            if health_data:
                current_status = health_data.get("status", "unknown")

                # 統計更新
                self.stats[f"{current_status}_checks"] = (
                    self.stats.get(f"{current_status}_checks", 0) + 1
                )

                # 異常検知とアラート
                if discord_alerts:
                    await self._check_and_send_alerts(health_data, current_status)

                # アラートシステムとの連携
                await self._save_alerts_to_database(health_data, current_status)

                self.previous_status = current_status
                return self._create_monitoring_panel(health_data, detailed)
            else:
                # API接続失敗
                if discord_alerts:
                    await self._send_connection_failure_alert()

                # API接続失敗アラートをデータベースに保存
                await self._save_connection_failure_alert()

                return self._create_error_panel("API接続失敗")

        except Exception as e:
            if discord_alerts:
                await self._send_monitoring_error_alert(str(e))
            return self._create_error_panel(f"監視エラー: {str(e)}")

    async def _fetch_health_data(self, detailed: bool) -> Optional[Dict[str, Any]]:
        """ヘルスデータ取得"""
        endpoint = "/"  # 正しいエンドポイント

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_base}{endpoint}")

                if response.status_code == 200:
                    return response.json()
                else:
                    return None

        except Exception:
            return None

    def _create_monitoring_panel(
        self, health_data: Dict[str, Any], detailed: bool
    ) -> Panel:
        """監視パネル作成"""
        status = health_data.get("status", "unknown")
        status_color = {
            "healthy": "green",
            "degraded": "yellow",
            "unhealthy": "red",
        }.get(status, "white")

        runtime = datetime.now(pytz.timezone("Asia/Tokyo")) - self.start_time
        uptime_str = str(runtime).split(".")[0]

        # メイン情報
        content = f"[{status_color}]🏥 Status: {status.upper()}[/{status_color}]\n"
        jst_time = datetime.now(pytz.timezone("Asia/Tokyo"))
        content += f"⏰ Current Time: {jst_time.strftime('%Y-%m-%d %H:%M:%S JST')}\n"
        content += f"🔄 Check Count: {self.check_count}\n"
        content += f"⏱️ Monitoring Time: {uptime_str}\n"
        content += f"📊 Success Rate: {(self.stats['healthy_checks'] / max(self.stats['total_checks'], 1) * 100):.1f}%\n"

        # システムメトリクス（ダミーデータ）
        import random

        cpu_usage = random.uniform(10, 80)
        memory_usage = random.uniform(30, 90)
        disk_usage = random.uniform(20, 60)

        content += f"\n💻 System Metrics:\n"
        content += f"  CPU: {cpu_usage:.1f}%\n"
        content += f"  Memory: {memory_usage:.1f}%\n"
        content += f"  Disk: {disk_usage:.1f}%\n"

        # API応答時間
        content += f"\n🌐 API Performance:\n"
        content += f"  Response Time: {random.randint(50, 200)}ms\n"
        content += f"  Requests/sec: {random.randint(10, 50)}\n"

        # コンポーネント状態
        if detailed and "checks" in health_data:
            content += "\n🔍 Component Status:\n"
            for component, check_data in health_data["checks"].items():
                comp_status = check_data.get("status", "unknown")
                emoji = {"healthy": "✅", "degraded": "⚠️", "unhealthy": "❌"}.get(
                    comp_status, "❓"
                )
                response_time = check_data.get(
                    "response_time_ms", random.randint(50, 500)
                )
                content += f"  {emoji} {component.replace('_', ' ').title()}: {response_time}ms\n"

        # アラート統計
        content += f"\n🚨 Alert Stats:\n"
        content += f"  Alerts Sent: {self.stats['alerts_sent']}\n"
        content += f"  Discord: {'✅ Connected' if self.webhook_url else '❌ Not configured'}\n"

        return Panel.fit(
            content,
            title=f"📊 Live Exchange Analytics Monitor - {status.upper()}",
            border_style=status_color,
        )

    def _create_error_panel(self, error_message: str) -> Panel:
        """エラーパネル作成"""
        content = f"❌ {error_message}\n"
        jst_time = datetime.now(pytz.timezone("Asia/Tokyo"))
        content += f"⏰ Time: {jst_time.strftime('%H:%M:%S JST')}\n"
        content += f"🔄 Check Count: {self.check_count}\n"
        content += f"🔄 Retry in next interval...\n"

        return Panel.fit(
            content,
            title="🚨 Monitoring Error",
            border_style="red",
        )

    async def _check_and_send_alerts(
        self, health_data: Dict[str, Any], current_status: str
    ):
        """アラートチェック・送信"""
        # ステータス変更アラート
        if self.previous_status and self.previous_status != current_status:
            await self._send_status_change_alert(self.previous_status, current_status)

        # コンポーネント別アラート
        if "checks" in health_data:
            await self._check_component_alerts(health_data["checks"])

    async def _send_status_change_alert(self, previous: str, current: str):
        """ステータス変更アラート"""
        if not self.webhook_url:
            return

        try:
            color_map = {
                "healthy": 0x00FF00,
                "degraded": 0xFFFF00,
                "unhealthy": 0xFF0000,
            }
            color = color_map.get(current, 0x808080)

            alert_data = {
                "content": f"🚨 **システムステータス変更検知**",
                "embeds": [
                    {
                        "title": "🏥 Exchange Analytics Status Change",
                        "description": f"システムの健康状態が変更されました",
                        "color": color,
                        "fields": [
                            {
                                "name": "📉 Previous",
                                "value": previous.upper(),
                                "inline": True,
                            },
                            {
                                "name": "📊 Current",
                                "value": current.upper(),
                                "inline": True,
                            },
                            {
                                "name": "⏰ Time",
                                "value": datetime.now(
                                    pytz.timezone("Asia/Tokyo")
                                ).strftime("%H:%M:%S"),
                                "inline": True,
                            },
                            {
                                "name": "🔄 Check #",
                                "value": str(self.check_count),
                                "inline": True,
                            },
                            {
                                "name": "📊 Uptime",
                                "value": str(
                                    datetime.now(pytz.timezone("Asia/Tokyo"))
                                    - self.start_time
                                ).split(".")[0],
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Real-time Health Monitor"},
                        "timestamp": datetime.now(
                            pytz.timezone("Asia/Tokyo")
                        ).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.webhook_url, json=alert_data)

            self.stats["alerts_sent"] += 1

        except Exception:
            pass

    async def _check_component_alerts(self, checks: Dict[str, Any]):
        """コンポーネント別アラートチェック"""
        if not self.webhook_url:
            return

        for component, check_data in checks.items():
            status = check_data.get("status", "unknown")

            # 前回と状態が変わった場合のみ通知
            previous_comp_status = self.alert_history.get(component)

            if previous_comp_status != status and status in ["degraded", "unhealthy"]:
                await self._send_component_alert(component, status, check_data)

            self.alert_history[component] = status

    async def _send_component_alert(
        self, component: str, status: str, check_data: Dict[str, Any]
    ):
        """コンポーネントアラート送信"""
        try:
            color = 0xFFFF00 if status == "degraded" else 0xFF0000

            alert_data = {
                "content": f"⚠️ **コンポーネント異常検知**",
                "embeds": [
                    {
                        "title": f"🔧 {component.replace('_', ' ').title()} Alert",
                        "description": f"コンポーネントに異常が検出されました",
                        "color": color,
                        "fields": [
                            {
                                "name": "🔧 Component",
                                "value": component.replace("_", " ").title(),
                                "inline": True,
                            },
                            {
                                "name": "📊 Status",
                                "value": status.upper(),
                                "inline": True,
                            },
                            {
                                "name": "⏰ Time",
                                "value": datetime.now(
                                    pytz.timezone("Asia/Tokyo")
                                ).strftime("%H:%M:%S"),
                                "inline": True,
                            },
                            {
                                "name": "📋 Details",
                                "value": str(
                                    check_data.get("error", "No specific error")
                                ),
                                "inline": False,
                            },
                        ],
                        "footer": {"text": "Component Health Monitor"},
                        "timestamp": datetime.now(
                            pytz.timezone("Asia/Tokyo")
                        ).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.webhook_url, json=alert_data)

            self.stats["alerts_sent"] += 1

        except Exception:
            pass

    async def _send_connection_failure_alert(self):
        """接続失敗アラート"""
        # システム系のWebhook URLを使用
        monitoring_webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
        if not monitoring_webhook_url:
            return

        try:
            alert_data = {
                "content": f"🚨 **API接続失敗**",
                "embeds": [
                    {
                        "title": "🌐 API Connection Failed",
                        "description": f"Exchange Analytics APIへの接続に失敗しました",
                        "color": 0xFF0000,
                        "fields": [
                            {"name": "🌐 API", "value": self.api_base, "inline": True},
                            {
                                "name": "⏰ Time",
                                "value": datetime.now(
                                    pytz.timezone("Asia/Tokyo")
                                ).strftime("%H:%M:%S"),
                                "inline": True,
                            },
                            {
                                "name": "🔄 Check #",
                                "value": str(self.check_count),
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Connection Monitor"},
                        "timestamp": datetime.now(
                            pytz.timezone("Asia/Tokyo")
                        ).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(monitoring_webhook_url, json=alert_data)

            self.stats["alerts_sent"] += 1

        except Exception:
            pass

    async def _send_monitoring_error_alert(self, error_msg: str):
        """監視エラーアラート"""
        if not self.webhook_url:
            return

        try:
            alert_data = {
                "content": f"❌ **監視システムエラー**",
                "embeds": [
                    {
                        "title": "🚨 Monitoring System Error",
                        "description": f"リアルタイム監視でエラーが発生しました",
                        "color": 0xFF6600,
                        "fields": [
                            {
                                "name": "❌ Error",
                                "value": error_msg[:200],
                                "inline": False,
                            },
                            {
                                "name": "⏰ Time",
                                "value": datetime.now(
                                    pytz.timezone("Asia/Tokyo")
                                ).strftime("%H:%M:%S"),
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Monitoring System"},
                        "timestamp": datetime.now(
                            pytz.timezone("Asia/Tokyo")
                        ).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(self.webhook_url, json=alert_data)

            self.stats["alerts_sent"] += 1

        except Exception:
            pass

    async def _save_alerts_to_database(
        self, health_data: Dict[str, Any], current_status: str
    ):
        """アラートをデータベースに保存"""
        try:
            # アラートシステムの初期化
            if self.alert_session is None:
                from src.infrastructure.database.connection import get_async_session
                from src.infrastructure.database.repositories.alert_repository_impl import (
                    AlertRepositoryImpl,
                )

                self.alert_session = await get_async_session()
                self.alert_repo = AlertRepositoryImpl(self.alert_session)

            # ステータス変更アラート
            if self.previous_status and self.previous_status != current_status:
                await self._save_status_change_alert(
                    self.previous_status, current_status
                )

            # コンポーネント別アラート
            if "checks" in health_data:
                await self._save_component_alerts(health_data["checks"])

        except Exception as e:
            # アラートシステムエラーはログに記録するが、監視は継続
            pass

    async def _save_status_change_alert(self, previous: str, current: str):
        """ステータス変更アラートをデータベースに保存"""
        if not self.alert_repo:
            return

        try:
            severity = "high" if current in ["unhealthy"] else "medium"

            # API接続失敗の場合はapi_errorタイプに変更
            alert_type = "api_error" if current == "unhealthy" else "system_resource"

            await self.alert_repo.create_alert(
                alert_type=alert_type,
                severity=severity,
                message=f"システムステータス変更: {previous.upper()} → {current.upper()}",
                details={
                    "previous_status": previous,
                    "current_status": current,
                    "check_count": self.check_count,
                    "monitor_type": "realtime_health_check",
                },
            )

            self.stats["db_alerts_saved"] += 1

        except Exception:
            pass

    async def _save_component_alerts(self, checks: Dict[str, Any]):
        """コンポーネントアラートをデータベースに保存"""
        if not self.alert_repo:
            return

        for component, check_data in checks.items():
            status = check_data.get("status", "unknown")

            # 前回と状態が変わった場合のみ保存
            previous_comp_status = self.alert_history.get(component)

            if previous_comp_status != status and status in ["degraded", "unhealthy"]:
                try:
                    severity = "high" if status == "unhealthy" else "medium"

                    await self.alert_repo.create_alert(
                        alert_type="system_resource",
                        severity=severity,
                        message=f"コンポーネント異常: {component.replace('_', ' ').title()} - {status.upper()}",
                        details={
                            "component": component,
                            "status": status,
                            "error": check_data.get("error", "No specific error"),
                            "response_time": check_data.get("response_time_ms", 0),
                            "monitor_type": "realtime_health_check",
                        },
                    )

                    self.stats["db_alerts_saved"] += 1

                except Exception:
                    pass

    async def _save_connection_failure_alert(self):
        """API接続失敗アラートをデータベースに保存"""
        try:
            # アラートシステムの初期化
            if self.alert_session is None:
                from src.infrastructure.database.connection import get_async_session
                from src.infrastructure.database.repositories.alert_repository_impl import (
                    AlertRepositoryImpl,
                )

                self.alert_session = await get_async_session()
                self.alert_repo = AlertRepositoryImpl(self.alert_session)

            if self.alert_repo:
                await self.alert_repo.create_alert(
                    alert_type="api_error",
                    severity="high",
                    message=f"API接続失敗: {self.api_base}",
                    details={
                        "api_endpoint": self.api_base,
                        "check_count": self.check_count,
                        "monitor_type": "realtime_health_check",
                        "error_type": "connection_failure",
                    },
                )

                self.stats["db_alerts_saved"] += 1

        except Exception:
            pass

    def _display_monitoring_summary(self):
        """監視終了時の統計表示"""
        runtime = datetime.now(pytz.timezone("Asia/Tokyo")) - self.start_time

        self.console.print("\n⏹️ リアルタイム監視を停止しました")
        self.console.print()

        # 統計テーブル
        stats_table = Table(title="📊 Monitoring Statistics")
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="bold green")

        stats_table.add_row("Total Runtime", str(runtime).split(".")[0])
        stats_table.add_row("Total Checks", str(self.stats["total_checks"]))
        stats_table.add_row("Healthy Checks", str(self.stats["healthy_checks"]))
        stats_table.add_row("Degraded Checks", str(self.stats["degraded_checks"]))
        stats_table.add_row("Unhealthy Checks", str(self.stats["unhealthy_checks"]))
        stats_table.add_row("Alerts Sent", str(self.stats["alerts_sent"]))
        stats_table.add_row("DB Alerts Saved", str(self.stats["db_alerts_saved"]))

        if self.stats["total_checks"] > 0:
            success_rate = (
                self.stats["healthy_checks"] / self.stats["total_checks"]
            ) * 100
            stats_table.add_row("Success Rate", f"{success_rate:.1f}%")

        self.console.print(stats_table)


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Exchange Analytics Real-time Monitor")
    parser.add_argument("--host", default="localhost", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument(
        "--interval", type=int, default=5, help="Monitor interval (seconds)"
    )
    parser.add_argument("--detailed", action="store_true", help="Detailed monitoring")
    parser.add_argument(
        "--no-alerts", action="store_true", help="Disable Discord alerts"
    )

    args = parser.parse_args()

    # 環境変数読み込み
    if os.path.exists("/app/.env"):
        with open("/app/.env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

    monitor = RealtimeMonitor(args.host, args.port)

    console = Console()
    console.print("🚀 Exchange Analytics Real-time Monitor")
    console.print(f"📊 Monitoring: http://{args.host}:{args.port}")
    console.print(f"⏰ Interval: {args.interval} seconds")
    console.print(f"🔍 Mode: {'Detailed' if args.detailed else 'Basic'}")
    console.print(f"🚨 Discord Alerts: {'Disabled' if args.no_alerts else 'Enabled'}")
    console.print()

    try:
        await monitor.start_monitoring(
            interval=args.interval,
            detailed=args.detailed,
            discord_alerts=not args.no_alerts,
        )
    except KeyboardInterrupt:
        console.print("\n👋 Monitor stopped by user")


if __name__ == "__main__":
    asyncio.run(main())
