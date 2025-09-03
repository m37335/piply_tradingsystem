#!/usr/bin/env python3
"""
Exchange Analytics Data Scheduler
定期的な通貨データ取得・分析・通知システム

機能:
- 設定可能な間隔での自動データ取得
- Alpha Vantage API レート制限対応
- AI分析結果の自動Discord配信
- 失敗時の自動リトライ・エラー通知
- 統計・ログ記録
"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


class DataScheduler:
    """定期データ取得・分析スケジューラー"""

    def __init__(self):
        self.console = Console()
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone("Asia/Tokyo"))
        self.jst = pytz.timezone("Asia/Tokyo")

        # 設定
        self.currency_pairs = [
            "USD/JPY",
            "EUR/USD",
            "GBP/USD",
            "AUD/USD",
            "EUR/JPY",
            "GBP/JPY",
        ]
        self.fetch_interval_minutes = 15  # Alpha Vantage制限考慮
        self.ai_analysis_interval_hours = 1  # AI分析間隔

        # 統計
        self.stats = {
            "total_fetches": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "ai_analyses": 0,
            "discord_notifications": 0,
            "last_successful_fetch": None,
            "last_error": None,
            "start_time": datetime.now(self.jst),
        }

        # ロガー設定
        self.logger = self._setup_logger()

        # 実行中フラグ
        self.running = False

        # シグナルハンドラ設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _setup_logger(self) -> logging.Logger:
        """ロガー設定"""
        logger = logging.getLogger("data_scheduler")
        logger.setLevel(logging.INFO)

        # ファイルハンドラ
        os.makedirs("logs", exist_ok=True)
        file_handler = logging.FileHandler("logs/data_scheduler.log")
        file_handler.setLevel(logging.INFO)

        # コンソールハンドラ
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # フォーマッター
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _signal_handler(self, signum, frame):
        """シグナルハンドラ"""
        self.logger.info(f"Signal {signum} received. Shutting down...")
        self.stop_scheduler()
        sys.exit(0)

    async def start_scheduler(self):
        """スケジューラー開始"""
        self.console.print("🚀 Exchange Analytics Data Scheduler 開始")
        self.console.print(
            f"🕘 日本時間: {datetime.now(self.jst).strftime('%Y-%m-%d %H:%M:%S JST')}"
        )
        self.console.print(f"💱 監視通貨ペア: {', '.join(self.currency_pairs)}")
        self.console.print(f"⏰ データ取得間隔: {self.fetch_interval_minutes}分")
        self.console.print(f"🤖 AI分析間隔: {self.ai_analysis_interval_hours}時間")
        self.console.print()

        self.running = True

        # スケジュール設定
        await self._setup_schedules()

        # スケジューラー開始
        self.scheduler.start()
        self.logger.info("Data scheduler started")

        # 初回実行
        await self._initial_data_fetch()

        # ライブ監視表示
        await self._run_live_monitoring()

    async def _setup_schedules(self):
        """スケジュール設定"""
        # データ取得スケジュール（5分間隔）
        self.scheduler.add_job(
            self._scheduled_data_fetch,
            IntervalTrigger(minutes=self.fetch_interval_minutes),
            id="data_fetch",
            name="定期データ取得",
            max_instances=1,
            coalesce=True,
        )

        # AI分析スケジュール（1時間間隔）
        self.scheduler.add_job(
            self._scheduled_ai_analysis,
            IntervalTrigger(hours=self.ai_analysis_interval_hours),
            id="ai_analysis",
            name="定期AI分析",
            max_instances=1,
            coalesce=True,
        )

        # 統計リセット（毎日0時）
        self.scheduler.add_job(
            self._daily_stats_reset,
            CronTrigger(hour=0, minute=0),
            id="daily_reset",
            name="日次統計リセット",
        )

        # ヘルスチェック（5分間隔）
        self.scheduler.add_job(
            self._health_check,
            IntervalTrigger(minutes=5),
            id="health_check",
            name="ヘルスチェック",
        )

        self.logger.info("Schedules configured")

    async def _initial_data_fetch(self):
        """初回データ取得"""
        self.console.print("📊 初回データ取得を実行中...")
        await self._scheduled_data_fetch()

    async def _scheduled_data_fetch(self):
        """定期データ取得"""
        self.logger.info("Starting scheduled data fetch")

        for pair in self.currency_pairs:
            try:
                self.stats["total_fetches"] += 1

                # Alpha Vantage API呼び出し
                success = await self._fetch_currency_data(pair)

                if success:
                    self.stats["successful_fetches"] += 1
                    self.stats["last_successful_fetch"] = datetime.now(self.jst)
                    self.logger.info(f"Successfully fetched data for {pair}")
                else:
                    self.stats["failed_fetches"] += 1
                    self.logger.warning(f"Failed to fetch data for {pair}")

                # API制限対応（通貨ペア間の間隔）
                await asyncio.sleep(15)  # 1分間5回制限対応

            except Exception as e:
                self.stats["failed_fetches"] += 1
                self.stats["last_error"] = str(e)
                self.logger.error(f"Error fetching data for {pair}: {str(e)}")

                # エラー通知
                await self._send_error_notification(pair, str(e))

        self.logger.info("Scheduled data fetch completed")

    async def _fetch_currency_data(self, currency_pair: str) -> bool:
        """通貨データ取得"""
        try:
            import subprocess

            # 環境変数を設定してAlpha Vantageテストスクリプト実行
            env = os.environ.copy()
            # .envファイルから環境変数を読み込み
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            env[key] = value

            result = subprocess.run(
                ["python", "tests/api/test_alphavantage.py", "--test", "fx"],
                capture_output=True,
                text=True,
                cwd="/app",
                timeout=30,
                env=env,
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Currency data fetch error: {str(e)}")
            return False

    async def _scheduled_ai_analysis(self):
        """定期AI分析"""
        self.logger.info("Starting scheduled AI analysis")

        # 主要通貨ペアのAI分析
        analysis_pairs = ["USD/JPY", "EUR/USD", "GBP/USD"]

        for pair in analysis_pairs:
            try:
                # AI分析 + Discord配信
                success = await self._run_ai_analysis(pair)

                if success:
                    self.stats["ai_analyses"] += 1
                    self.stats["discord_notifications"] += 1
                    self.logger.info(f"AI analysis completed for {pair}")

                # 分析間隔（API制限考慮）
                await asyncio.sleep(10)

            except Exception as e:
                self.logger.error(f"AI analysis error for {pair}: {str(e)}")

        self.logger.info("Scheduled AI analysis completed")

    async def _run_ai_analysis(self, currency_pair: str) -> bool:
        """AI分析実行"""
        try:
            import subprocess

            # 環境変数を設定してAI分析実行
            env = os.environ.copy()
            # .envファイルから環境変数を読み込み
            if os.path.exists(".env"):
                with open(".env", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            key, value = line.split("=", 1)
                            env[key] = value

            # 実データAI分析実行
            result = subprocess.run(
                ["python", "scripts/cron/integrated_ai_discord.py", currency_pair],
                capture_output=True,
                text=True,
                cwd="/app",
                timeout=60,
                env=env,
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"AI analysis execution error: {str(e)}")
            return False

    async def _health_check(self):
        """ヘルスチェック"""
        try:
            # 長時間データ取得なしチェック
            if self.stats["last_successful_fetch"]:
                time_since_last = (
                    datetime.now(self.jst) - self.stats["last_successful_fetch"]
                )
                if time_since_last > timedelta(hours=2):
                    await self._send_health_alert(
                        "長時間データ取得なし", time_since_last
                    )

            # 失敗率チェック
            total = self.stats["total_fetches"]
            if total > 10:
                failure_rate = (self.stats["failed_fetches"] / total) * 100
                if failure_rate > 50:
                    await self._send_health_alert("高い失敗率", f"{failure_rate:.1f}%")

        except Exception as e:
            self.logger.error(f"Health check error: {str(e)}")

    async def _send_error_notification(self, currency_pair: str, error_msg: str):
        """エラー通知"""
        try:
            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                return

            import httpx

            alert_data = {
                "content": f"⚠️ **データ取得エラー**",
                "embeds": [
                    {
                        "title": "📊 Data Fetch Error",
                        "description": f"{currency_pair}のデータ取得でエラーが発生しました",
                        "color": 0xFF6600,
                        "fields": [
                            {
                                "name": "💱 通貨ペア",
                                "value": currency_pair,
                                "inline": True,
                            },
                            {
                                "name": "❌ エラー",
                                "value": error_msg[:100],
                                "inline": False,
                            },
                            {
                                "name": "🕘 時刻（JST）",
                                "value": datetime.now(self.jst).strftime("%H:%M:%S"),
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Data Scheduler"},
                        "timestamp": datetime.now(self.jst).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(webhook_url, json=alert_data)

        except Exception as e:
            self.logger.error(f"Error notification failed: {str(e)}")

    async def _send_health_alert(self, issue_type: str, details):
        """ヘルスアラート"""
        try:
            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                return

            import httpx

            alert_data = {
                "content": f"🚨 **スケジューラーヘルスアラート**",
                "embeds": [
                    {
                        "title": "⚕️ Scheduler Health Alert",
                        "description": f"データスケジューラーで問題が検出されました",
                        "color": 0xFF0000,
                        "fields": [
                            {"name": "🚨 問題", "value": issue_type, "inline": True},
                            {"name": "📊 詳細", "value": str(details), "inline": True},
                            {
                                "name": "🕘 時刻（JST）",
                                "value": datetime.now(self.jst).strftime("%H:%M:%S"),
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Data Scheduler Health Monitor"},
                        "timestamp": datetime.now(self.jst).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(webhook_url, json=alert_data)

        except Exception as e:
            self.logger.error(f"Health alert failed: {str(e)}")

    async def _daily_stats_reset(self):
        """日次統計リセット"""
        self.logger.info("Daily stats reset")

        # 日次レポート送信
        await self._send_daily_report()

        # 統計リセット
        self.stats.update(
            {
                "total_fetches": 0,
                "successful_fetches": 0,
                "failed_fetches": 0,
                "ai_analyses": 0,
                "discord_notifications": 0,
                "last_error": None,
            }
        )

    async def _send_daily_report(self):
        """日次レポート送信"""
        try:
            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                return

            import httpx

            runtime = datetime.now(self.jst) - self.stats["start_time"]
            success_rate = 0
            if self.stats["total_fetches"] > 0:
                success_rate = (
                    self.stats["successful_fetches"] / self.stats["total_fetches"]
                ) * 100

            report_data = {
                "content": f"📊 **日次レポート**",
                "embeds": [
                    {
                        "title": "📈 Daily Data Scheduler Report",
                        "description": f"過去24時間のスケジューラー統計",
                        "color": 0x00FF00,
                        "fields": [
                            {
                                "name": "📊 総取得回数",
                                "value": str(self.stats["total_fetches"]),
                                "inline": True,
                            },
                            {
                                "name": "✅ 成功回数",
                                "value": str(self.stats["successful_fetches"]),
                                "inline": True,
                            },
                            {
                                "name": "❌ 失敗回数",
                                "value": str(self.stats["failed_fetches"]),
                                "inline": True,
                            },
                            {
                                "name": "🤖 AI分析回数",
                                "value": str(self.stats["ai_analyses"]),
                                "inline": True,
                            },
                            {
                                "name": "💬 Discord通知",
                                "value": str(self.stats["discord_notifications"]),
                                "inline": True,
                            },
                            {
                                "name": "📈 成功率",
                                "value": f"{success_rate:.1f}%",
                                "inline": True,
                            },
                            {
                                "name": "⏱️ 稼働時間",
                                "value": str(runtime).split(".")[0],
                                "inline": False,
                            },
                        ],
                        "footer": {"text": "Data Scheduler Daily Report"},
                        "timestamp": datetime.now(self.jst).isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(webhook_url, json=report_data)

        except Exception as e:
            self.logger.error(f"Daily report failed: {str(e)}")

    async def _run_live_monitoring(self):
        """ライブ監視表示"""
        try:
            with Live(console=self.console, refresh_per_second=1) as live:
                while self.running:
                    panel = self._create_monitoring_panel()
                    live.update(panel)
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.stop_scheduler()

    def _create_monitoring_panel(self) -> Panel:
        """監視パネル作成"""
        current_time = datetime.now(self.jst)
        runtime = current_time - self.stats["start_time"]

        # 成功率計算
        success_rate = 0
        if self.stats["total_fetches"] > 0:
            success_rate = (
                self.stats["successful_fetches"] / self.stats["total_fetches"]
            ) * 100

        # 次回実行時刻
        next_jobs = []
        for job in self.scheduler.get_jobs():
            if job.next_run_time:
                next_jobs.append(
                    f"{job.name}: {job.next_run_time.strftime('%H:%M:%S')}"
                )

        content = f"""[bold green]🚀 Data Scheduler Status[/bold green]

🕘 現在時刻: {current_time.strftime('%Y-%m-%d %H:%M:%S JST')}
⏱️ 稼働時間: {str(runtime).split('.')[0]}
🔄 スケジューラー: {'✅ 実行中' if self.scheduler.running else '❌ 停止'}

📊 **統計**:
  総取得回数: {self.stats["total_fetches"]}
  成功回数: {self.stats["successful_fetches"]}
  失敗回数: {self.stats["failed_fetches"]}
  成功率: {success_rate:.1f}%
  AI分析回数: {self.stats["ai_analyses"]}
  Discord通知: {self.stats["discord_notifications"]}

⏰ **次回実行予定**:
{chr(10).join(f"  {job}" for job in next_jobs[:4])}

💱 **監視中通貨ペア**: {', '.join(self.currency_pairs)}

{f'❌ 最新エラー: {self.stats["last_error"]}' if self.stats["last_error"] else '✅ エラーなし'}
{f'✅ 最終成功: {self.stats["last_successful_fetch"].strftime("%H:%M:%S")}' if self.stats["last_successful_fetch"] else ''}
"""

        color = (
            "green" if success_rate > 90 else "yellow" if success_rate > 70 else "red"
        )

        return Panel.fit(
            content, title="📊 Exchange Analytics Data Scheduler", border_style=color
        )

    def stop_scheduler(self):
        """スケジューラー停止"""
        self.running = False
        if self.scheduler.running:
            self.scheduler.shutdown()
        self.logger.info("Data scheduler stopped")
        self.console.print("\n⏹️ Data Scheduler を停止しました")


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description="Exchange Analytics Data Scheduler")
    parser.add_argument("--config", help="設定ファイルパス")
    parser.add_argument("--test", action="store_true", help="テストモード")

    args = parser.parse_args()

    # 環境変数読み込み
    if os.path.exists("/app/.env"):
        with open("/app/.env", "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value

    scheduler = DataScheduler()

    if args.test:
        console = Console()
        console.print("🧪 テストモード - 1回のデータ取得を実行")
        await scheduler._scheduled_data_fetch()
        console.print("✅ テスト完了")
    else:
        await scheduler.start_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
