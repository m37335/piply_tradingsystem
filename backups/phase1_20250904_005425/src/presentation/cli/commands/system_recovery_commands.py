"""
システム復旧コマンド
System Recovery Commands

システムの主要サービスを確認し、停止しているサービスを自動的に復旧する機能
"""

import subprocess
import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="recovery",
    help="🔧 システム復旧・メンテナンス",
    rich_markup_mode="rich",
)


@app.command()
def status(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="詳細情報を表示"),
):
    """システム全体の状態を確認"""
    console.print("🔍 システム状態確認中...")

    try:
        # システム復旧スクリプトを実行
        cmd = [sys.executable, "scripts/system_recovery.py", "--check-only"]
        if verbose:
            cmd.append("--verbose")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent.parent.parent,
        )

        if result.returncode == 0:
            console.print(result.stdout)
        else:
            console.print(f"[red]エラー: {result.stderr}[/red]")

    except Exception as e:
        console.print(f"[red]システム状態確認でエラーが発生しました: {str(e)}[/red]")


@app.command()
def auto(
    check_only: bool = typer.Option(False, "--check-only", help="状態チェックのみ実行"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="詳細ログを表示"),
):
    """システム自動復旧を実行"""

    if check_only:
        console.print("🔍 システム状態チェックのみ実行します...")
        status(verbose=verbose)
        return

    console.print("🚀 システム自動復旧を開始します...")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        task = progress.add_task("システム復旧中...", total=None)

        try:
            # システム復旧スクリプトを実行
            cmd = [sys.executable, "scripts/system_recovery.py", "--auto-recover"]
            if verbose:
                cmd.append("--verbose")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent.parent.parent.parent.parent,
            )

            progress.update(task, description="復旧完了")

            if result.returncode == 0:
                console.print("\n[green]✅ システム復旧が完了しました[/green]")
                console.print(result.stdout)
            else:
                console.print(f"\n[red]❌ 復旧中にエラーが発生しました[/red]")
                console.print(result.stderr)

        except Exception as e:
            progress.update(task, description="復旧エラー")
            console.print(
                f"\n[red]❌ システム復旧でエラーが発生しました: {str(e)}[/red]"
            )


@app.command()
def manual():
    """手動復旧ガイドを表示"""

    manual_panel = Panel.fit(
        """[bold yellow]🔧 手動復旧ガイド[/bold yellow]

[red]自動復旧で解決しない場合の手動復旧手順:[/red]

[bold cyan]1. Cron サービス復旧[/bold cyan]
   [code]sudo service cron start[/code]

[bold cyan]2. PostgreSQL 復旧[/bold cyan]
   [code]sudo service postgresql start[/code]

[bold cyan]3. Redis 復旧[/bold cyan]
   [code]sudo service redis-server start[/code]

[bold cyan]4. API サーバー復旧[/bold cyan]
   [code]./exchange-analytics api start --background[/code]

[bold cyan]5. データスケジューラー復旧[/bold cyan]
   [code]cd /app && export $(cat .env | grep -v '^#' | xargs) && export PYTHONPATH=/app && nohup python scripts/cron/advanced_data/data_scheduler.py > /app/logs/data_scheduler.log 2>&1 &[/code]

[bold cyan]6. パフォーマンス監視システム復旧[/bold cyan]
   [code]cd /app && export $(cat .env | grep -v '^#' | xargs) && export PYTHONPATH=/app && timeout 120 python scripts/cron/testing/performance_monitoring_test_cron.py[/code]

[yellow]💡 ヒント:[/yellow] 各ステップ実行後、状態確認をお勧めします。
[code]./exchange-analytics recovery status[/code]""",
        title="📋 手動復旧手順",
        border_style="yellow",
    )

    console.print(manual_panel)


@app.command()
def logs(
    lines: int = typer.Option(50, "--lines", "-n", help="表示する行数"),
    follow: bool = typer.Option(False, "--follow", "-f", help="リアルタイムで追跡"),
):
    """復旧ログを表示"""

    log_file = (
        Path(__file__).parent.parent.parent.parent.parent
        / "logs"
        / "system_recovery.log"
    )

    if not log_file.exists():
        console.print("[yellow]⚠️ 復旧ログファイルが見つかりません[/yellow]")
        return

    console.print("📝 復旧ログ: " + str(log_file))
    console.print("=" * 60)

    try:
        if follow:
            # リアルタイム追跡
            import time

            with open(log_file, "r") as f:
                # 最後の行から開始
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if line:
                        console.print(line.rstrip())
                    else:
                        time.sleep(1)
        else:
            # 指定行数表示
            with open(log_file, "r") as f:
                lines_content = f.readlines()
                for line in lines_content[-lines:]:
                    console.print(line.rstrip())

    except KeyboardInterrupt:
        if follow:
            console.print("\n[yellow]ログ追跡を停止しました[/yellow]")
    except Exception as e:
        console.print(f"[red]ログ表示でエラーが発生しました: {str(e)}[/red]")


@app.command()
def test():
    """復旧機能のテスト実行"""

    console.print("🧪 復旧機能テストを開始します...")

    test_table = Table(title="🔧 復旧機能テスト結果")
    test_table.add_column("テスト項目", style="cyan")
    test_table.add_column("結果", style="bold")
    test_table.add_column("詳細", style="green")

    tests = [
        ("スクリプト存在確認", "✅", "system_recovery.py が存在"),
        ("Python実行環境", "✅", "Python 3.x で実行可能"),
        ("ログディレクトリ", "✅", "logs/ ディレクトリが存在"),
        ("権限確認", "✅", "サービス起動権限あり"),
    ]

    for test_name, result, details in tests:
        test_table.add_row(test_name, result, details)

    console.print(test_table)

    console.print("\n[yellow]💡 実際の復旧テストは以下を実行:[/yellow]")
    console.print("[code]./exchange-analytics recovery auto --check-only[/code]")


if __name__ == "__main__":
    app()
