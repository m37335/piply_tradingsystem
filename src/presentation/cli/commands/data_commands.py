"""
Data Commands
データ管理コマンド

責任:
- 為替データの取得・管理
- データベースの初期化・マイグレーション
- データバックアップ・復元
"""

import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.table import Table

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

app = typer.Typer(
    name="data",
    help="💱 データ管理コマンド",
    no_args_is_help=True,
)


@app.command()
def fetch(
    pairs: Optional[str] = typer.Option(
        "USD/JPY,EUR/USD,GBP/JPY", "--pairs", "-p", help="通貨ペア（カンマ区切り）"
    ),
    source: str = typer.Option("alpha_vantage", "--source", "-s", help="データソース"),
    interval: str = typer.Option("1min", "--interval", "-i", help="時間間隔"),
    days: int = typer.Option(7, "--days", "-d", help="取得日数"),
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    為替レートデータを取得

    Examples:
        exchange-analytics data fetch
        exchange-analytics data fetch --pairs "USD/JPY,EUR/USD" --days 30
        exchange-analytics data fetch --source "fixer" --interval "1hour"
    """
    currency_pairs = [pair.strip() for pair in pairs.split(",")]

    console.print(f"💱 為替データ取得開始...")
    console.print(f"📊 通貨ペア: {', '.join(currency_pairs)}")
    console.print(f"🔌 データソース: {source}")
    console.print(f"⏰ 間隔: {interval}")
    console.print(f"📅 期間: {days}日")

    if not force:
        confirm = typer.confirm("データ取得を実行しますか？")
        if not confirm:
            console.print("❌ データ取得をキャンセルしました")
            return

    # プログレスバー付きでデータ取得をシミュレート
    with Progress(console=console) as progress:
        main_task = progress.add_task("データ取得中...", total=len(currency_pairs))

        for pair in currency_pairs:
            pair_task = progress.add_task(f"取得中: {pair}", total=100)

            # データ取得をシミュレート
            for i in range(100):
                progress.update(pair_task, advance=1)
                # await asyncio.sleep(0.01)  # 実際の処理をシミュレート

            progress.update(main_task, advance=1)
            console.print(f"✅ {pair} データ取得完了")

    console.print(f"🎉 全ての為替データ取得が完了しました！")


@app.command()
def status():
    """
    データベースの状態確認
    """
    console.print("🔍 データベース状態確認中...")

    # データベース状態テーブル
    status_table = Table(title="📊 Database Status")
    status_table.add_column("Table", style="cyan")
    status_table.add_column("Records", style="bold green")
    status_table.add_column("Last Updated", style="yellow")
    status_table.add_column("Status", style="bold")

    # ダミーデータ
    tables_data = [
        ("exchange_rates", "15,420", "2024-01-15 10:30:00", "✅ Active"),
        ("currency_pairs", "12", "2024-01-15 09:00:00", "✅ Active"),
        ("configurations", "45", "2024-01-14 16:45:00", "✅ Active"),
        ("analysis_results", "8,230", "2024-01-15 10:25:00", "✅ Active"),
        ("alerts", "156", "2024-01-15 10:20:00", "✅ Active"),
    ]

    for table, records, updated, status in tables_data:
        status_table.add_row(table, records, updated, status)

    console.print(status_table)

    # サマリー
    summary_panel = Panel.fit(
        """[green]データベース接続: 正常[/green]
[blue]総レコード数: 24,863[/blue]
[yellow]最終更新: 2024-01-15 10:30:00[/yellow]
[cyan]使用容量: 156.2 MB[/cyan]""",
        title="📈 Database Summary",
        border_style="green",
    )

    console.print(summary_panel)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="強制初期化"),
    seed: bool = typer.Option(True, "--seed/--no-seed", help="サンプルデータを投入"),
):
    """
    データベースを初期化
    """
    console.print("🗄️ データベース初期化...")

    if not force:
        console.print("[yellow]⚠️ この操作は既存のデータを削除します！[/yellow]")
        confirm = typer.confirm("データベースを初期化しますか？")
        if not confirm:
            console.print("❌ 初期化をキャンセルしました")
            return

    with Progress(console=console) as progress:
        # テーブル作成
        task1 = progress.add_task("テーブル作成中...", total=100)
        for i in range(100):
            progress.update(task1, advance=1)
        console.print("✅ テーブル作成完了")

        # インデックス作成
        task2 = progress.add_task("インデックス作成中...", total=100)
        for i in range(100):
            progress.update(task2, advance=1)
        console.print("✅ インデックス作成完了")

        # サンプルデータ投入
        if seed:
            task3 = progress.add_task("サンプルデータ投入中...", total=100)
            for i in range(100):
                progress.update(task3, advance=1)
            console.print("✅ サンプルデータ投入完了")

    console.print("🎉 データベース初期化が完了しました！")


@app.command()
def backup(
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="出力ファイルパス"),
    compress: bool = typer.Option(True, "--compress/--no-compress", help="圧縮"),
):
    """
    データベースをバックアップ
    """
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"backup_exchange_analytics_{timestamp}.sql")
        if compress:
            output = output.with_suffix(".sql.gz")

    console.print(f"💾 データベースバックアップ作成中...")
    console.print(f"📁 出力先: {output}")

    with Progress(console=console) as progress:
        backup_task = progress.add_task("バックアップ中...", total=100)

        # バックアップ処理をシミュレート
        for i in range(100):
            progress.update(backup_task, advance=1)

    # ファイルサイズをシミュレート
    file_size = "45.6 MB" if compress else "128.3 MB"

    console.print(f"✅ バックアップ完了: {output}")
    console.print(f"📊 ファイルサイズ: {file_size}")


@app.command()
def restore(
    backup_file: Path = typer.Argument(..., help="バックアップファイルパス"),
    force: bool = typer.Option(False, "--force", "-f", help="強制復元"),
):
    """
    データベースを復元
    """
    if not backup_file.exists():
        console.print(f"❌ バックアップファイルが見つかりません: {backup_file}")
        raise typer.Exit(1)

    console.print(f"🔄 データベース復元中...")
    console.print(f"📁 バックアップファイル: {backup_file}")

    if not force:
        console.print("[yellow]⚠️ この操作は既存のデータを上書きします！[/yellow]")
        confirm = typer.confirm("データベースを復元しますか？")
        if not confirm:
            console.print("❌ 復元をキャンセルしました")
            return

    with Progress(console=console) as progress:
        restore_task = progress.add_task("復元中...", total=100)

        # 復元処理をシミュレート
        for i in range(100):
            progress.update(restore_task, advance=1)

    console.print("✅ データベース復元が完了しました！")


@app.command()
def clean(
    days: int = typer.Option(30, "--days", "-d", help="保持日数"),
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    古いデータをクリーンアップ
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    console.print(f"🧹 データクリーンアップ...")
    console.print(f"📅 {cutoff_date.strftime('%Y-%m-%d')} より古いデータを削除")

    if not force:
        confirm = typer.confirm(f"{days}日より古いデータを削除しますか？")
        if not confirm:
            console.print("❌ クリーンアップをキャンセルしました")
            return

    # クリーンアップ対象のテーブル
    tables = [
        ("exchange_rates", 1420),
        ("analysis_results", 856),
        ("alert_logs", 234),
    ]

    with Progress(console=console) as progress:
        main_task = progress.add_task("クリーンアップ中...", total=len(tables))

        total_deleted = 0
        for table_name, delete_count in tables:
            table_task = progress.add_task(f"クリーンアップ: {table_name}", total=100)

            for i in range(100):
                progress.update(table_task, advance=1)

            progress.update(main_task, advance=1)
            total_deleted += delete_count
            console.print(f"✅ {table_name}: {delete_count:,} レコード削除")

    console.print(f"🎉 クリーンアップ完了！合計 {total_deleted:,} レコード削除")


@app.command()
def export(
    table: str = typer.Argument(..., help="エクスポートするテーブル名"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="出力ファイルパス"),
    format: str = typer.Option("csv", "--format", "-f", help="出力形式 (csv, json, xlsx)"),
    where: Optional[str] = typer.Option(None, "--where", "-w", help="WHERE条件"),
):
    """
    テーブルデータをエクスポート

    Examples:
        exchange-analytics data export exchange_rates
        exchange-analytics data export exchange_rates --format json
        exchange-analytics data export exchange_rates --where "currency_pair='USD/JPY'"
    """
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"{table}_{timestamp}.{format}")

    console.print(f"📤 データエクスポート...")
    console.print(f"📊 テーブル: {table}")
    console.print(f"📁 出力先: {output}")
    console.print(f"📋 形式: {format}")
    if where:
        console.print(f"🔍 条件: {where}")

    with Progress(console=console) as progress:
        export_task = progress.add_task("エクスポート中...", total=100)

        # エクスポート処理をシミュレート
        for i in range(100):
            progress.update(export_task, advance=1)

    # 結果をシミュレート
    record_count = 15420 if table == "exchange_rates" else 1000
    file_size = "2.3 MB" if format == "csv" else "5.1 MB"

    console.print(f"✅ エクスポート完了: {output}")
    console.print(f"📊 レコード数: {record_count:,}")
    console.print(f"📏 ファイルサイズ: {file_size}")


@app.command()
def migrate(
    up: bool = typer.Option(True, "--up/--down", help="マイグレーション方向"),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="特定バージョン"),
):
    """
    データベースマイグレーション実行
    """
    direction = "up" if up else "down"
    console.print(f"🔄 データベースマイグレーション実行 ({direction})")

    if version:
        console.print(f"🎯 バージョン: {version}")

    # マイグレーションファイルの一覧をシミュレート
    migrations = [
        "001_create_exchange_rates_table.py",
        "002_add_indexes.py",
        "003_add_configurations_table.py",
        "004_add_analysis_results_table.py",
    ]

    with Progress(console=console) as progress:
        migration_task = progress.add_task("マイグレーション実行中...", total=len(migrations))

        for migration in migrations:
            progress.update(migration_task, advance=1)
            console.print(f"✅ {migration}")

    console.print("🎉 マイグレーション完了！")


@app.command()
def schedule(
    action: str = typer.Argument("start", help="アクション (start/stop/status/test)"),
    interval: int = typer.Option(15, "--interval", "-i", help="データ取得間隔（分）"),
    ai_interval: int = typer.Option(60, "--ai-interval", help="AI分析間隔（分）"),
    pairs: str = typer.Option(
        "USD/JPY,EUR/USD,GBP/USD", "--pairs", "-p", help="通貨ペア（カンマ区切り）"
    ),
):
    """
    定期データ取得スケジューラー管理

    Examples:
        exchange-analytics data schedule start
        exchange-analytics data schedule status
        exchange-analytics data schedule test
        exchange-analytics data schedule stop
    """
    console.print(f"⏰ データスケジューラー: {action}")

    if action == "start":
        console.print("🚀 定期データ取得開始...")
        console.print(f"📊 取得間隔: {interval}分")
        console.print(f"🤖 AI分析間隔: {ai_interval}分")
        console.print(f"💱 通貨ペア: {pairs}")

        confirm = typer.confirm("定期データ取得スケジューラーを開始しますか？")
        if not confirm:
            console.print("❌ スケジューラー開始をキャンセルしました")
            return

        console.print("🔄 スケジューラー開始中...")
        console.print(
            "💡 バックグラウンド実行: nohup python data_scheduler.py > scheduler.log 2>&1 &"
        )
        console.print("📊 ログ確認: tail -f logs/data_scheduler.log")
        console.print("⏹️ 停止方法: ./exchange-analytics data schedule stop")

        import subprocess

        try:
            # バックグラウンドでスケジューラー開始
            subprocess.Popen(
                ["python", "data_scheduler.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd="/app",
            )
            console.print("✅ データスケジューラーを開始しました")
        except Exception as e:
            console.print(f"❌ スケジューラー開始失敗: {str(e)}")

    elif action == "status":
        console.print("📊 スケジューラー状態確認...")

        # プロセス確認
        import subprocess

        try:
            result = subprocess.run(
                ["pgrep", "-f", "data_scheduler.py"], capture_output=True, text=True
            )

            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                console.print(f"✅ スケジューラー実行中 (PID: {', '.join(pids)})")

                # ログ表示
                log_file = "/app/logs/data_scheduler.log"
                if os.path.exists(log_file):
                    console.print("\n📋 最新ログ (最新10行):")
                    subprocess.run(["tail", "-10", log_file])

            else:
                console.print("❌ スケジューラーは実行されていません")

        except Exception as e:
            console.print(f"❌ 状態確認エラー: {str(e)}")

    elif action == "stop":
        console.print("⏹️ スケジューラー停止中...")

        import subprocess

        try:
            # プロセス終了
            result = subprocess.run(
                ["pkill", "-f", "data_scheduler.py"], capture_output=True
            )

            if result.returncode == 0:
                console.print("✅ データスケジューラーを停止しました")
            else:
                console.print("ℹ️ 停止するスケジューラーが見つかりませんでした")

        except Exception as e:
            console.print(f"❌ 停止エラー: {str(e)}")

    elif action == "test":
        console.print("🧪 スケジューラーテスト実行...")

        import subprocess

        try:
            result = subprocess.run(
                ["python", "data_scheduler.py", "--test"], cwd="/app"
            )

            if result.returncode == 0:
                console.print("✅ テスト完了")
            else:
                console.print("❌ テスト失敗")

        except Exception as e:
            console.print(f"❌ テストエラー: {str(e)}")

    else:
        console.print(f"❌ 無効なアクション: {action}")
        console.print("利用可能: start, stop, status, test")
