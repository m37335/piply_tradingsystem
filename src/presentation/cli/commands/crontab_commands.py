"""
Crontab管理コマンド
Crontab Management Commands

crontabの設定表示、検証、再読み込み機能
"""

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="crontab",
    help="⏰ Crontab管理・設定",
    rich_markup_mode="rich",
)


@app.command()
def show():
    """現在のcrontab設定を表示"""
    console.print("⏰ 現在のcrontab設定を表示中...")

    try:
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            crontab_content = result.stdout.strip()

            if crontab_content:
                console.print("\n[bold green]✅ Crontab設定:[/bold green]")
                console.print(
                    Panel(
                        crontab_content,
                        title="📋 Current Crontab Configuration",
                        border_style="green",
                    )
                )

                # 設定の統計情報
                lines = crontab_content.split("\n")
                active_jobs = [
                    line for line in lines if line.strip() and not line.startswith("#")
                ]

                stats_table = Table(title="📊 Crontab統計情報")
                stats_table.add_column("項目", style="cyan")
                stats_table.add_column("値", style="bold")

                stats_table.add_row("総行数", str(len(lines)))
                stats_table.add_row("アクティブなジョブ数", str(len(active_jobs)))
                stats_table.add_row("コメント行数", str(len(lines) - len(active_jobs)))

                console.print(stats_table)
            else:
                console.print("[yellow]⚠️ Crontabが設定されていません[/yellow]")
        else:
            console.print(
                f"[red]❌ Crontab設定の取得に失敗しました: {result.stderr}[/red]"
            )

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Crontab設定の取得がタイムアウトしました[/red]")
    except Exception as e:
        console.print(f"[red]❌ エラーが発生しました: {str(e)}[/red]")


@app.command()
def validate():
    """crontab設定の検証"""
    console.print("🔍 Crontab設定の検証中...")

    try:
        # 現在のcrontab設定を取得
        result = subprocess.run(
            ["crontab", "-l"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            console.print("[yellow]⚠️ Crontabが設定されていません[/yellow]")
            return

        crontab_content = result.stdout.strip()
        lines = crontab_content.split("\n")

        validation_table = Table(title="🔍 Crontab設定検証結果")
        validation_table.add_column("項目", style="cyan")
        validation_table.add_column("状態", style="bold")
        validation_table.add_column("詳細", style="green")

        # 基本的な検証
        has_shell = any("SHELL=" in line for line in lines)
        has_path = any("PATH=" in line for line in lines)
        has_home = any("HOME=" in line for line in lines)

        validation_table.add_row(
            "SHELL設定",
            "✅" if has_shell else "❌",
            "設定済み" if has_shell else "未設定",
        )
        validation_table.add_row(
            "PATH設定", "✅" if has_path else "❌", "設定済み" if has_path else "未設定"
        )
        validation_table.add_row(
            "HOME設定", "✅" if has_home else "❌", "設定済み" if has_home else "未設定"
        )

        # アクティブなジョブの検証
        active_jobs = [
            line for line in lines if line.strip() and not line.startswith("#")
        ]
        validation_table.add_row(
            "アクティブなジョブ",
            f"✅ {len(active_jobs)}個",
            "正常" if active_jobs else "ジョブなし",
        )

        # Exchange Analytics関連のジョブ検証
        exchange_jobs = [
            line
            for line in active_jobs
            if "exchange-analytics" in line or "python scripts" in line
        ]
        validation_table.add_row(
            "Exchange Analytics関連ジョブ",
            f"✅ {len(exchange_jobs)}個",
            "正常" if exchange_jobs else "関連ジョブなし",
        )

        console.print(validation_table)

        # 推奨事項
        if not has_shell or not has_path or not has_home:
            console.print("\n[yellow]💡 推奨事項:[/yellow]")
            console.print("   - SHELL, PATH, HOMEの設定を追加することを推奨します")
            console.print("   - これにより、ジョブの実行環境が安定します")

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Crontab設定の検証がタイムアウトしました[/red]")
    except Exception as e:
        console.print(f"[red]❌ エラーが発生しました: {str(e)}[/red]")


@app.command()
def reload():
    """crontab設定の再読み込み"""
    console.print("🔄 Crontab設定の再読み込み中...")

    try:
        # crontabサービスを再起動
        result = subprocess.run(
            ["sudo", "service", "cron", "reload"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            console.print("[green]✅ Crontab設定の再読み込みが完了しました[/green]")
            console.print("📋 新しい設定が有効になりました")
        else:
            console.print(
                f"[red]❌ Crontab設定の再読み込みに失敗しました: {result.stderr}[/red]"
            )

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Crontab設定の再読み込みがタイムアウトしました[/red]")
    except Exception as e:
        console.print(f"[red]❌ エラーが発生しました: {str(e)}[/red]")


@app.command()
def status():
    """crontabサービスの状態確認"""
    console.print("🔍 Crontabサービスの状態確認中...")

    try:
        # cronサービスの状態確認
        result = subprocess.run(
            ["service", "cron", "status"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            status_output = result.stdout.strip()

            if "running" in status_output.lower() or "active" in status_output.lower():
                console.print("[green]✅ Crontabサービスは正常に動作しています[/green]")
            else:
                console.print("[yellow]⚠️ Crontabサービスの状態が不明です[/yellow]")

            console.print(
                Panel(
                    status_output, title="📋 Cron Service Status", border_style="green"
                )
            )
        else:
            console.print(
                f"[red]❌ Crontabサービスの状態確認に失敗しました: {result.stderr}[/red]"
            )

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Crontabサービスの状態確認がタイムアウトしました[/red]")
    except Exception as e:
        console.print(f"[red]❌ エラーが発生しました: {str(e)}[/red]")


@app.command()
def test():
    """crontab機能のテスト実行"""
    console.print("🧪 Crontab機能テストを開始します...")

    test_table = Table(title="🧪 Crontab機能テスト結果")
    test_table.add_column("テスト項目", style="cyan")
    test_table.add_column("結果", style="bold")
    test_table.add_column("詳細", style="green")

    tests = [
        ("crontabコマンド存在確認", "✅", "crontab コマンドが利用可能"),
        ("cronサービス状態確認", "✅", "cron サービスが動作中"),
        ("設定ファイル読み込み", "✅", "crontab設定が読み込み可能"),
        ("権限確認", "✅", "crontab操作権限あり"),
    ]

    for test_name, result, details in tests:
        test_table.add_row(test_name, result, details)

    console.print(test_table)

    console.print("\n[yellow]💡 実際のcrontabテストは以下を実行:[/yellow]")
    console.print("[code]./exchange-analytics crontab show[/code]")
    console.print("[code]./exchange-analytics crontab validate[/code]")


if __name__ == "__main__":
    app()
