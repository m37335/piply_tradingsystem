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
    test: bool = typer.Option(False, "--test", help="テストモード（Discord送信なし）"),
    no_optimization: bool = typer.Option(
        False, "--no-optimization", help="最適化機能を無効にする"
    ),
    chart: bool = typer.Option(False, "--chart", help="H1チャートを生成する"),
    force: bool = typer.Option(False, "--force", "-f", help="確認をスキップ"),
):
    """
    統合AI分析レポートを生成（TA-Lib標準版）

    Examples:
        exchange-analytics ai analyze
        exchange-analytics ai analyze --test
        exchange-analytics ai analyze --no-optimization
        exchange-analytics ai analyze --chart
    """
    console.print("🤖 統合AI分析レポート生成（TA-Lib標準版）...")
    console.print(f"🧪 テストモード: {'✅ 有効' if test else '❌ 無効'}")
    console.print(f"⚡ 最適化機能: {'❌ 無効' if no_optimization else '✅ 有効'}")
    console.print(f"📊 チャート生成: {'✅ 有効' if chart else '❌ 無効'}")
    console.print("📊 TA-Lib標準使用")

    if not force:
        confirm = typer.confirm("統合AI分析を実行しますか？")
        if not confirm:
            console.print("❌ AI分析をキャンセルしました")
            return

    # AI分析実行
    success = _run_ai_analysis(test, no_optimization, chart)

    if success:
        console.print("✅ 統合AI分析レポート生成完了")
        if not test:
            console.print("💬 Discord通知も送信しました")
    else:
        console.print("❌ AI分析に失敗しました")


@app.command()
def reports(
    limit: int = typer.Option(10, "--limit", "-n", help="表示件数"),
    currency_pair: Optional[str] = typer.Option(
        None, "--pair", "-p", help="通貨ペアフィルタ"
    ),
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


def _run_ai_analysis(
    test: bool = False,
    no_optimization: bool = False,
    chart: bool = False,
) -> bool:
    """統合AI分析実行（TA-Lib標準版）"""
    try:
        # モジュール化されたAI分析スクリプト実行
        import subprocess

        # 基本コマンド
        cmd = ["python", "scripts/cron/integrated_ai_discord/main.py"]

        # オプション追加
        if test:
            # テストモード
            cmd.append("--test")

        if no_optimization:
            # 最適化機能無効
            cmd.append("--no-optimization")

        if chart:
            # チャート生成
            cmd.append("--chart")

        console.print(f"🚀 実行コマンド: {' '.join(cmd)}")

        # リアルタイムで出力を表示
        result = subprocess.run(cmd, cwd="/app")

        if result.returncode == 0:
            return True
        else:
            logger.error(f"AI analysis failed with return code: {result.returncode}")
            return False

    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        return False


def _send_discord_test() -> bool:
    """Discord通知テスト（モジュール化版）"""
    try:
        import subprocess

        # モジュール化されたスクリプトでテスト実行（リアルタイム出力）
        result = subprocess.run(
            ["python", "scripts/cron/integrated_ai_discord/main.py", "--test"],
            cwd="/app",
        )

        return result.returncode == 0

    except Exception as e:
        logger.error(f"Discord test error: {str(e)}")
        return False
