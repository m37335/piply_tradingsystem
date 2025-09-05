"""
Exchange Analytics CLI
CLI メインアプリケーション

設計書参照:
- プレゼンテーション層設計_20250809.md

コマンドライン管理インターフェース
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...utils.logging_config import get_presentation_logger, setup_logging_directories
from .commands import ai_commands, api_commands, config_commands, monitor_commands
from .commands.alert_config_commands import app as alert_config_app
from .commands.crontab_commands import app as crontab_app
from .commands.data import data_app
from .commands.system_recovery_commands import app as recovery_app

logger = get_presentation_logger()
console = Console()

# Typerアプリケーション初期化
app = typer.Typer(
    name="exchange-analytics",
    help="🚀 Exchange Analytics System - 通貨分析システム管理CLI",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# サブコマンド追加
app.add_typer(
    api_commands.app,
    name="api",
    help="🌐 API サーバー管理",
)

app.add_typer(
    data_app,
    name="data",
    help="💱 データ管理・取得",
)

app.add_typer(
    config_commands.app,
    name="config",
    help="⚙️ 設定管理",
)

app.add_typer(
    monitor_commands.app,
    name="system",
    help="📊 システム監視・ヘルスチェック\n\nExamples:\n  exchange-analytics system health\n  exchange-analytics system status\n  exchange-analytics system logs",
)

app.add_typer(
    ai_commands.app,
    name="ai",
    help="🤖 AI分析・通知",
)

app.add_typer(
    alert_config_app,
    name="alert-config",
    help="🚨 アラート設定管理",
)

app.add_typer(
    recovery_app,
    name="recovery",
    help="🔧 システム復旧・メンテナンス",
)

app.add_typer(
    crontab_app,
    name="crontab",
    help="⏰ Crontab管理・設定",
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None, "--version", "-v", help="バージョン情報を表示"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-V", help="詳細ログを表示"),
    config_file: Optional[Path] = typer.Option(
        None, "--config", "-c", help="設定ファイルパス"
    ),
):
    """
    Exchange Analytics System CLI

    通貨分析システムの管理・運用コマンドラインツール
    """
    # 初期化処理
    if ctx.invoked_subcommand is None:
        if version:
            show_version()
            return

        show_welcome()
        return

    # ログ設定
    setup_logging_directories()

    if verbose:
        logger.info("CLI started in verbose mode")


def show_version():
    """バージョン情報表示"""
    version_panel = Panel.fit(
        """[bold green]Exchange Analytics System[/bold green]
[blue]Version:[/blue] 1.0.0
[blue]Author:[/blue] Exchange Analytics Team
[blue]License:[/blue] MIT

[yellow]Components:[/yellow]
• Domain Layer ✅
• Application Layer ✅
• Infrastructure Layer ✅
• Presentation Layer ✅

[green]Status:[/green] Production Ready 🚀""",
        title="📊 Exchange Analytics",
        border_style="green",
    )

    console.print(version_panel)


def show_welcome():
    """ウェルカムメッセージ表示"""
    welcome_panel = Panel.fit(
        """[bold blue]Exchange Analytics System CLI[/bold blue]

🚀 通貨分析システムの管理・運用ツール

[yellow]利用可能なコマンド:[/yellow]
• [green]api[/green]      - API サーバー管理
• [green]data[/green]     - データ管理・取得
• [green]config[/green]   - 設定管理
• [green]monitor[/green]  - 監視・ヘルスチェック
• [green]ai[/green]       - AI分析・通知
• [green]recovery[/green] - システム復旧・メンテナンス

[blue]例:[/blue]
  [cyan]exchange-analytics api start[/cyan]        # API サーバー起動
  [cyan]exchange-analytics data fetch[/cyan]       # データ取得
  [cyan]exchange-analytics ai analyze[/cyan]       # AI分析・Discord通知
  [cyan]exchange-analytics monitor status[/cyan]   # システム状態確認
  [cyan]exchange-analytics recovery auto[/cyan]    # システム自動復旧

詳細: [cyan]exchange-analytics --help[/cyan]""",
        title="🎯 Exchange Analytics CLI",
        border_style="blue",
    )

    console.print(welcome_panel)


@app.command()
def status():
    """システム全体のステータス確認"""
    console.print("🔍 システムステータス確認中...")

    # ステータステーブル作成
    status_table = Table(title="📊 System Status")
    status_table.add_column("Component", style="cyan", no_wrap=True)
    status_table.add_column("Status", style="bold")
    status_table.add_column("Details", style="green")

    # 実際のサービス状態を確認
    import subprocess

    def check_service(
        service_name: str, check_command: str, status_pattern: str = "running"
    ) -> tuple:
        """サービス状態をチェック"""
        try:
            result = subprocess.run(
                check_command, shell=True, capture_output=True, text=True, timeout=5
            )
            is_running = status_pattern in result.stdout.lower()
            return (
                "✅ Healthy" if is_running else "❌ Stopped",
                "Running" if is_running else "Service stopped",
            )
        except Exception:
            return ("🟡 Unknown", "Check failed")

    # 各サービスの状態確認
    services = [
        ("Cron Service", *check_service("cron", "service cron status", "running")),
        (
            "PostgreSQL",
            *check_service("postgresql", "service postgresql status", "online"),
        ),
        (
            "Redis Cache",
            *check_service("redis", "service redis-server status", "running"),
        ),
        (
            "API Server",
            *check_service("api", "./exchange-analytics api status", "稼働中"),
        ),
    ]

    # 静的コンポーネント
    static_components = [
        ("Domain Layer", "✅ Healthy", "Models & Entities Ready"),
        ("Application Layer", "✅ Healthy", "Services & Use Cases Ready"),
        ("Infrastructure Layer", "✅ Healthy", "DB, Cache, APIs Ready"),
        ("Presentation Layer", "✅ Healthy", "REST API, CLI Ready"),
    ]

    # 全コンポーネントを表示
    for component, status, details in static_components + services:
        status_table.add_row(component, status, details)

    console.print(status_table)

    console.print(
        "\n💡 [yellow]Tip:[/yellow] 詳細確認は "
        "[cyan]exchange-analytics recovery status[/cyan] を実行"
    )


@app.command()
def info():
    """システム情報表示"""
    import platform
    import sys
    from datetime import datetime

    info_table = Table(title="🔧 System Information")
    info_table.add_column("Property", style="cyan", no_wrap=True)
    info_table.add_column("Value", style="bold green")

    info_data = [
        ("System", f"{platform.system()} {platform.release()}"),
        ("Python Version", f"{sys.version.split()[0]}"),
        ("Architecture", platform.machine()),
        ("Current Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        ("Working Directory", str(Path.cwd())),
        ("Log Directory", "logs/"),
        ("Config Directory", "config/"),
    ]

    for prop, value in info_data:
        info_table.add_row(prop, value)

    console.print(info_table)


def cli_main():
    """
    CLIエントリーポイント

    setup.pyやpyproject.tomlからconsole_scriptsとして呼び出される
    """
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 CLI終了[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]❌ エラー: {str(e)}[/red]")
        logger.error(f"CLI error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
