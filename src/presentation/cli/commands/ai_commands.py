"""
AI Commands
AI分析・通知コマンド

責任:
- AI分析レポート生成・管理
- Discord通知連携
- 自動分析スケジューリング
"""

import asyncio
import os
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="ai",
    help="🤖 AI分析・通知コマンド",
    no_args_is_help=True,
)


@app.command()
def analyze(
    currency_pair: str = typer.Argument("USD/JPY", help="通貨ペア (例: USD/JPY, EUR/USD)"),
    period: str = typer.Option("1d", "--period", "-p", help="分析期間 (1h, 1d, 1w, 1m)"),
    discord: bool = typer.Option(True, "--discord/--no-discord", help="Discord通知送信"),
    real_data: bool = typer.Option(True, "--real/--demo", help="実データ使用"),
    force: bool = typer.Option(False, "--force", "-f", help="確認をスキップ"),
):
    """
    AI分析レポートを生成

    Examples:
        exchange-analytics ai analyze USD/JPY
        exchange-analytics ai analyze EUR/USD --period 1w
        exchange-analytics ai analyze GBP/JPY --no-discord
    """
    console.print(f"🤖 AI分析レポート生成...")
    console.print(f"📊 通貨ペア: {currency_pair}")
    console.print(f"⏰ 期間: {period}")
    console.print(f"💬 Discord通知: {'✅ 有効' if discord else '❌ 無効'}")
    console.print(f"📊 データ: {'🌐 実データ' if real_data else '🧪 デモデータ'}")

    if not force:
        data_type = "実データ" if real_data else "デモデータ"
        confirm = typer.confirm(f"{currency_pair} の AI分析を{data_type}で実行しますか？")
        if not confirm:
            console.print("❌ AI分析をキャンセルしました")
            return

    # AI分析実行
    success = _run_ai_analysis(currency_pair, period, discord, real_data)

    if success:
        console.print("✅ AI分析レポート生成完了")
        if discord:
            console.print("💬 Discord通知も送信しました")
    else:
        console.print("❌ AI分析に失敗しました")


@app.command()
def reports(
    limit: int = typer.Option(10, "--limit", "-n", help="表示件数"),
    currency_pair: Optional[str] = typer.Option(None, "--pair", "-p", help="通貨ペアフィルタ"),
):
    """
    AI分析レポート一覧表示

    Examples:
        exchange-analytics ai reports
        exchange-analytics ai reports --limit 5
        exchange-analytics ai reports --pair USD/JPY
    """
    console.print(f"📋 AI分析レポート一覧 (最新 {limit} 件)")

    if currency_pair:
        console.print(f"🔍 フィルタ: {currency_pair}")

    # ダミーレポートデータ
    reports_data = [
        {
            "report_id": "ai_report_003",
            "currency_pair": "USD/JPY",
            "title": "USD/JPY 週次分析レポート",
            "confidence_score": 0.92,
            "generated_at": "2025-08-09 15:30:00",
            "status": "✅ 完了",
        },
        {
            "report_id": "ai_report_002",
            "currency_pair": "EUR/USD",
            "title": "EUR/USD 日次分析レポート",
            "confidence_score": 0.78,
            "generated_at": "2025-08-09 12:15:00",
            "status": "✅ 完了",
        },
        {
            "report_id": "ai_report_001",
            "currency_pair": "USD/JPY",
            "title": "USD/JPY 日次分析レポート",
            "confidence_score": 0.85,
            "generated_at": "2025-08-09 09:00:00",
            "status": "✅ 完了",
        },
    ]

    # フィルタ適用
    if currency_pair:
        reports_data = [r for r in reports_data if r["currency_pair"] == currency_pair]

    # 表示件数制限
    reports_data = reports_data[:limit]

    # テーブル表示
    reports_table = Table(title="🤖 AI Analysis Reports")
    reports_table.add_column("Report ID", style="cyan", no_wrap=True)
    reports_table.add_column("通貨ペア", style="bold")
    reports_table.add_column("タイトル", style="green")
    reports_table.add_column("信頼度", style="yellow")
    reports_table.add_column("生成時刻", style="blue")
    reports_table.add_column("ステータス", style="bold")

    for report in reports_data:
        confidence = report["confidence_score"]
        confidence_color = (
            "green" if confidence >= 0.8 else "yellow" if confidence >= 0.6 else "red"
        )
        confidence_text = f"[{confidence_color}]{confidence:.1%}[/{confidence_color}]"

        reports_table.add_row(
            report["report_id"],
            report["currency_pair"],
            report["title"],
            confidence_text,
            report["generated_at"],
            report["status"],
        )

    console.print(reports_table)

    if not reports_data:
        console.print("📭 レポートが見つかりませんでした")


@app.command()
def discord_test():
    """
    Discord通知テスト
    """
    console.print("🧪 Discord通知テスト実行...")

    # テスト通知送信
    success = _send_discord_test()

    if success:
        console.print("✅ Discord通知テスト成功")
        console.print("💬 Discordチャンネルを確認してください")
    else:
        console.print("❌ Discord通知テスト失敗")


@app.command()
def schedule(
    currency_pairs: str = typer.Option(
        "USD/JPY,EUR/USD", "--pairs", "-p", help="通貨ペア (カンマ区切り)"
    ),
    interval: int = typer.Option(3600, "--interval", "-i", help="実行間隔 (秒)"),
    period: str = typer.Option("1d", "--period", help="分析期間"),
    discord: bool = typer.Option(True, "--discord/--no-discord", help="Discord通知"),
):
    """
    定期AI分析スケジュール設定

    Examples:
        exchange-analytics ai schedule
        exchange-analytics ai schedule --pairs "USD/JPY,EUR/USD,GBP/JPY"
        exchange-analytics ai schedule --interval 7200 --period 1w
    """
    pairs_list = [pair.strip() for pair in currency_pairs.split(",")]

    console.print("📅 定期AI分析スケジュール設定...")
    console.print(f"💱 通貨ペア: {', '.join(pairs_list)}")
    console.print(f"⏰ 実行間隔: {interval}秒 ({interval//3600}時間)")
    console.print(f"📊 分析期間: {period}")
    console.print(f"💬 Discord通知: {'✅ 有効' if discord else '❌ 無効'}")

    confirm = typer.confirm("定期分析スケジュールを開始しますか？")
    if not confirm:
        console.print("❌ スケジュール設定をキャンセルしました")
        return

    console.print("🚀 定期AI分析スケジュール開始...")
    console.print("⏹️ 停止: Ctrl+C")

    try:
        import time

        while True:
            for pair in pairs_list:
                console.print(f"🤖 定期分析実行: {pair}")
                success = _run_ai_analysis(pair, period, discord)

                if success:
                    console.print(f"✅ {pair} 分析完了")
                else:
                    console.print(f"❌ {pair} 分析失敗")

                time.sleep(5)  # ペア間の間隔

            console.print(f"⏰ 次回実行まで {interval}秒待機...")
            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n⏹️ 定期AI分析スケジュールを停止しました")


def _run_ai_analysis(
    currency_pair: str, period: str, discord: bool, real_data: bool = True
) -> bool:
    """AI分析実行"""
    try:
        # AI分析統合スクリプト実行
        import subprocess

        if real_data and discord:
            # 実データ + Discord配信
            cmd = ["python", "real_ai_discord.py", currency_pair]
        elif discord:
            # デモデータ + Discord配信
            cmd = [
                "python",
                "ai_discord_integration.py",
                "analyze",
                currency_pair,
                period,
            ]
        else:
            # Discord通知なしの場合はAPI直接呼び出し
            cmd = [
                "python",
                "ai_discord_integration.py",
                "analyze",
                currency_pair,
                period,
            ]

        result = subprocess.run(cmd, capture_output=True, text=True, cwd="/app")

        if result.returncode == 0:
            return True
        else:
            logger.error(f"AI analysis failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        return False


def _send_discord_test() -> bool:
    """Discord通知テスト"""
    try:
        import subprocess

        result = subprocess.run(
            ["python", "ai_discord_integration.py", "test"],
            capture_output=True,
            text=True,
            cwd="/app",
        )

        return result.returncode == 0

    except Exception as e:
        logger.error(f"Discord test error: {str(e)}")
        return False
