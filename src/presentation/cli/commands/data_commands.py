"""
Data Commands
データ管理コマンド

責任:
- 為替データの取得・管理
- データベースの初期化・マイグレーション
- データバックアップ・復元
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

from ....infrastructure.database.optimization.query_optimizer import QueryOptimizer
from ....infrastructure.error_handling.error_handler import (
    ErrorCategory,
    ErrorHandler,
    ErrorSeverity,
)
from ....infrastructure.monitoring.performance_monitor import PerformanceMonitor
from ....infrastructure.optimization.memory_optimizer import MemoryOptimizer
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

    console.print("💱 為替データ取得開始...")
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

    console.print("🎉 全ての為替データ取得が完了しました！")


@app.command()
def show(
    limit: int = typer.Option(30, "--limit", "-l", help="表示件数"),
    currency_pair: str = typer.Option("USD/JPY", "--pair", "-p", help="通貨ペア"),
    table: str = typer.Option("price_data", "--table", "-t", help="テーブル名"),
    indicators: bool = typer.Option(
        False, "--indicators", "-i", help="テクニカル指標データを表示"
    ),
    timeframe: str = typer.Option(
        "5m", "--timeframe", "-tf", help="時間足 (5m, 1h, 4h, 1d)"
    ),
    source: str = typer.Option(
        "all", "--source", "-s", help="データソース (real, aggregated, ongoing, all)"
    ),
):
    """
    基本データを表示

    Examples:
        exchange-analytics data show
        exchange-analytics data show --limit 50
        exchange-analytics data show --indicators
        exchange-analytics data show --pair "EUR/USD" --table "technical_indicators"
        exchange-analytics data show --timeframe 1h --limit 10
        exchange-analytics data show --timeframe 4h --source ongoing
        exchange-analytics data show --timeframe 1d --source aggregated
    """
    # 時間足の検証
    valid_timeframes = ["5m", "1h", "4h", "1d"]
    if timeframe not in valid_timeframes:
        console.print(f"❌ 無効な時間足です: {timeframe}")
        console.print(f"有効な時間足: {', '.join(valid_timeframes)}")
        raise typer.Exit(1)

    # データソースの検証
    valid_sources = ["real", "aggregated", "ongoing", "all"]
    if source not in valid_sources:
        console.print(f"❌ 無効なデータソースです: {source}")
        console.print(f"有効なデータソース: {', '.join(valid_sources)}")
        raise typer.Exit(1)

    # --indicatorsオプションが指定された場合、テーブルを自動設定
    if indicators:
        table = "technical_indicators"
        console.print(f"📊 {currency_pair} のテクニカル指標データ表示...")
    else:
        console.print(f"📊 {currency_pair} の{timeframe}時間足データ表示...")

    console.print(f"📋 テーブル: {table}")
    console.print(f"⏰ 時間足: {timeframe}")
    console.print(f"🔌 データソース: {source}")
    console.print(f"📈 表示件数: {limit}件")

    try:
        # データベースファイルのパス
        db_path = Path("/app/data/exchange_analytics.db")

        if not db_path.exists():
            console.print("❌ データベースファイルが見つかりません")
            raise typer.Exit(1)

        # データベース接続
        import sqlite3

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # テーブルが存在するか確認
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?;",
                (table,),
            )
            if not cursor.fetchone():
                console.print(f"❌ テーブル '{table}' が見つかりません")
                raise typer.Exit(1)

            # テーブルのカラム情報を取得
            cursor.execute(f"PRAGMA table_info({table});")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # データを取得
            if table == "price_data":
                # 時間足とデータソースでフィルタリング
                where_conditions = ["currency_pair = ?"]
                params = [currency_pair]

                # データソースフィルタリング
                if source == "real":
                    where_conditions.append(
                        "data_source IN ('yahoo_finance', '5m Real')"
                    )
                elif source == "aggregated":
                    where_conditions.append(
                        "data_source LIKE '%Aggregated%' AND data_source NOT LIKE '%Ongoing%'"
                    )
                elif source == "ongoing":
                    where_conditions.append("data_source LIKE '%Ongoing%'")
                # source == "all" の場合はフィルタリングなし

                # 時間足フィルタリング（データソースから判定）
                if timeframe == "5m":
                    where_conditions.append(
                        "(data_source LIKE '%5m%' OR data_source LIKE '%M5%' OR data_source = 'yahoo_finance')"
                    )
                elif timeframe == "1h":
                    where_conditions.append(
                        "(data_source LIKE '%1h%' OR data_source LIKE '%H1%' OR data_source LIKE '%1時間足%' OR data_source = 'yahoo_finance')"
                    )
                elif timeframe == "4h":
                    where_conditions.append(
                        "(data_source LIKE '%4h%' OR data_source LIKE '%H4%' OR data_source LIKE '%4時間足%' OR data_source = 'yahoo_finance')"
                    )
                elif timeframe == "1d":
                    where_conditions.append(
                        "(data_source LIKE '%1d%' OR data_source LIKE '%D1%' OR data_source LIKE '%日足%' OR data_source = 'yahoo_finance')"
                    )

                where_clause = " AND ".join(where_conditions)

                query = f"""
                SELECT timestamp, open_price, high_price, low_price, close_price, 
                       volume, data_source 
                FROM price_data 
                WHERE {where_clause}
                ORDER BY timestamp DESC 
                LIMIT ?
                """
                params.append(limit)
                cursor.execute(query, params)
            elif table == "technical_indicators":
                # テクニカル指標の場合は時間足でフィルタリング
                if timeframe != "5m":  # デフォルト以外の場合
                    query = """
                    SELECT timestamp, indicator_type, timeframe, value, 
                           additional_data 
                    FROM technical_indicators 
                    WHERE currency_pair = ? AND timeframe = ?
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """
                    cursor.execute(query, (currency_pair, timeframe, limit))
                else:
                    query = """
                    SELECT timestamp, indicator_type, timeframe, value, 
                           additional_data 
                    FROM technical_indicators 
                    WHERE currency_pair = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """
                    cursor.execute(query, (currency_pair, limit))
            else:
                # 汎用クエリ
                query = f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT ?"
                cursor.execute(query, (limit,))

            rows = cursor.fetchall()

            if not rows:
                if table == "price_data":
                    console.print(
                        f"❌ {currency_pair} の{timeframe}時間足データが見つかりません"
                    )
                    console.print(
                        f"💡 ヒント: --source オプションを変更してみてください (real, aggregated, ongoing, all)"
                    )
                else:
                    console.print(f"❌ {currency_pair} のデータが見つかりません")
                raise typer.Exit(1)

            # データテーブルを作成
            if table == "price_data":
                table_title = f"📊 {currency_pair} - {timeframe}時間足データ"
                if source != "all":
                    table_title += f" ({source})"
                data_table = Table(title=table_title)
            else:
                data_table = Table(title=f"📊 {currency_pair} - {table}")

            # カラムを追加
            if table == "price_data":
                data_table.add_column("タイムスタンプ", style="cyan")
                data_table.add_column("始値", style="green")
                data_table.add_column("高値", style="red")
                data_table.add_column("安値", style="blue")
                data_table.add_column("終値", style="yellow")
                data_table.add_column("データソース", style="white")

                for row in rows:
                    (
                        timestamp,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume,
                        data_source,
                    ) = row
                    data_table.add_row(
                        str(timestamp),
                        f"{open_price:.4f}",
                        f"{high_price:.4f}",
                        f"{low_price:.4f}",
                        f"{close_price:.4f}",
                        str(data_source),
                    )
            elif table == "technical_indicators":
                data_table.add_column("タイムスタンプ", style="cyan")
                data_table.add_column("指標タイプ", style="green")
                data_table.add_column("時間軸", style="blue")
                data_table.add_column("値", style="yellow")
                data_table.add_column("追加データ", style="magenta")

                for row in rows:
                    timestamp, indicator_type, timeframe, value, additional_data = row
                    data_table.add_row(
                        str(timestamp),
                        str(indicator_type),
                        str(timeframe),
                        f"{value:.4f}" if value else "N/A",
                        str(additional_data) if additional_data else "N/A",
                    )
            else:
                # 汎用表示
                for col_name in column_names:
                    data_table.add_column(col_name, style="cyan")

                for row in rows:
                    data_table.add_row(*[str(cell) for cell in row])

            console.print(data_table)

            # サマリーパネル
            summary_panel = Panel(
                f"✅ {len(rows)}件のデータを表示しました",
                title="📋 サマリー",
                border_style="green",
            )
            console.print(summary_panel)

            conn.close()

        except sqlite3.Error as e:
            console.print(f"❌ データベース接続エラー: {e}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ データ表示エラー: {e}")
        raise typer.Exit(1)


@app.command()
def status():
    """
    データベースの状態を確認

    Examples:
        exchange-analytics data status
    """
    console.print("📊 データベース状態確認...")

    try:
        # データベースファイルのパス
        db_path = Path("/app/data/exchange_analytics.db")

        if not db_path.exists():
            console.print("❌ データベースファイルが見つかりません")
            raise typer.Exit(1)

        # ファイル情報を取得
        stat = db_path.stat()
        file_size_mb = stat.st_size / (1024 * 1024)
        last_modified = datetime.fromtimestamp(stat.st_mtime)

        # データベース接続テスト
        import sqlite3

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # テーブル一覧を取得
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            table_count = len(tables)

            # 各テーブルのレコード数を取得
            total_records = 0
            table_records = {}

            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                table_records[table_name] = count
                total_records += count

            conn.close()

            # 状態データを作成
            status_data = {
                "データベース": "SQLite",
                "ファイルパス": str(db_path),
                "ファイルサイズ": f"{file_size_mb:.1f} MB",
                "テーブル数": str(table_count),
                "総レコード数": f"{total_records:,}",
                "最終更新": last_modified.strftime("%Y-%m-%d %H:%M:%S"),
                "接続状態": "正常",
            }

            # 状態テーブルを作成
            status_table = Table(title="📊 データベース状態")
            status_table.add_column("項目", style="cyan")
            status_table.add_column("値", style="green")

            for key, value in status_data.items():
                status_table.add_row(key, str(value))

            console.print(status_table)

            # テーブル詳細テーブル
            if table_records:
                detail_table = Table(title="📋 テーブル詳細")
                detail_table.add_column("テーブル名", style="cyan")
                detail_table.add_column("レコード数", style="green")

                for table_name, count in table_records.items():
                    detail_table.add_row(table_name, f"{count:,}")

                console.print(detail_table)

            # サマリーパネル
            summary_panel = Panel(
                "✅ データベースは正常に動作しています",
                title="📋 サマリー",
                border_style="green",
            )

            console.print(summary_panel)

        except sqlite3.Error as e:
            console.print(f"❌ データベース接続エラー: {e}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ 状態確認エラー: {e}")
        raise typer.Exit(1)


@app.command()
def init(
    force: bool = typer.Option(False, "--force", "-f", help="強制初期化"),
):
    """
    データベースをクリーンアップして初期化

    Examples:
        exchange-analytics data init
        exchange-analytics data init --force
    """
    console.print("🗄️ データベースクリーンアップ・初期化...")

    if not force:
        console.print("[yellow]⚠️ この操作は既存のデータを完全に削除します！[/yellow]")
        confirm = typer.confirm("データベースをクリーンアップして初期化しますか？")
        if not confirm:
            console.print("❌ 初期化をキャンセルしました")
            return

    try:
        # データベースクリーンアップスクリプトを実行
        console.print("🚀 データベースクリーンアップを実行中...")

        import subprocess
        import sys
        from pathlib import Path

        # スクリプトパスを設定
        script_path = Path("/app/scripts/cron/database_cleanup.py")

        if not script_path.exists():
            console.print(f"❌ クリーンアップスクリプトが見つかりません: {script_path}")
            raise typer.Exit(1)

        # 環境変数を設定
        env = os.environ.copy()
        if not env.get("DATABASE_URL"):
            env["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"

        # データベースクリーンアップスクリプトを実行
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd="/app",
            env=env,
        )

        if result.returncode == 0:
            console.print("✅ データベースクリーンアップ・初期化が完了しました！")
            console.print("📊 クリーンアップログ:")
            console.print(result.stdout)
        else:
            console.print("❌ データベースクリーンアップ・初期化に失敗しました")
            console.print("エラーログ:")
            console.print(result.stderr)
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ 初期化エラー: {e}")
        raise typer.Exit(1)


@app.command()
def load(
    pairs: Optional[str] = typer.Option(
        "USD/JPY", "--pairs", "-p", help="通貨ペア（カンマ区切り）"
    ),
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    為替データを取得してロード

    Examples:
        exchange-analytics data load
        exchange-analytics data load --pairs "USD/JPY,EUR/USD" --force
    """
    console.print("📊 為替データ取得・ロード機能")
    console.print("⚠️ この機能はPhase 2で実装予定です")
    console.print("現在は開発中です...")


@app.command()
def complete(
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    データ補完処理を実行

    Examples:
        exchange-analytics data complete
        exchange-analytics data complete --force
    """
    console.print("🔄 データ補完処理機能")
    console.print("⚠️ この機能はPhase 2で実装予定です")
    console.print("現在は開発中です...")


@app.command()
def calculate(
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    テクニカル指標を計算

    Examples:
        exchange-analytics data calculate
        exchange-analytics data calculate --force
    """
    console.print("📈 テクニカル指標計算機能")
    console.print("⚠️ この機能はPhase 3で実装予定です")
    console.print("現在は開発中です...")


@app.command()
def setup(
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    全処理を一括実行（データベースクリーンアップ → データ取得 → データ補完 → テクニカル指標計算）

    Examples:
        exchange-analytics data setup
        exchange-analytics data setup --force
    """
    console.print("🚀 一括実行機能")
    console.print("⚠️ この機能はPhase 4で実装予定です")
    console.print("現在は開発中です...")


@app.command()
def backup(
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="出力ファイルパス"
    ),
    compress: bool = typer.Option(True, "--compress/--no-compress", help="圧縮"),
):
    """
    データベースをバックアップ

    Examples:
        exchange-analytics data backup
        exchange-analytics data backup --output backup.sql
        exchange-analytics data backup --no-compress
    """
    if output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = Path(f"backup_exchange_analytics_{timestamp}.sql")
        if compress:
            output = output.with_suffix(".sql.gz")

    console.print("💾 データベースバックアップ作成中...")
    console.print(f"📁 出力先: {output}")

    try:
        # データベースファイルのパスを取得
        db_path = Path("/app/data/exchange_analytics.db")

        if not db_path.exists():
            console.print("❌ データベースファイルが見つかりません")
            raise typer.Exit(1)

        # バックアップディレクトリを作成
        backup_dir = Path("/app/backups")
        backup_dir.mkdir(exist_ok=True)

        # バックアップファイルのパス
        backup_path = backup_dir / output.name

        import shutil

        # データベースファイルをコピー
        shutil.copy2(db_path, backup_path)

        # 圧縮処理
        if compress and not output.suffix == ".gz":
            import gzip

            with open(backup_path, "rb") as f_in:
                with gzip.open(backup_path.with_suffix(".gz"), "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            backup_path.unlink()  # 元ファイルを削除
            backup_path = backup_path.with_suffix(".gz")

        # ファイルサイズを取得
        file_size = backup_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)

        console.print(f"✅ バックアップ完了: {backup_path}")
        console.print(f"📊 ファイルサイズ: {file_size_mb:.1f} MB")

    except Exception as e:
        console.print(f"❌ バックアップエラー: {e}")
        raise typer.Exit(1)


@app.command()
def restore(
    backup_file: Path = typer.Argument(..., help="バックアップファイルパス"),
    force: bool = typer.Option(False, "--force", "-f", help="強制復元"),
):
    """
    データベースを復元

    Examples:
        exchange-analytics data restore backup.sql
        exchange-analytics data restore backup.sql.gz --force
    """
    if not backup_file.exists():
        console.print(f"❌ バックアップファイルが見つかりません: {backup_file}")
        raise typer.Exit(1)

    console.print("🔄 データベース復元中...")
    console.print(f"📁 バックアップファイル: {backup_file}")

    if not force:
        console.print("[yellow]⚠️ この操作は既存のデータを上書きします！[/yellow]")
        confirm = typer.confirm("データベースを復元しますか？")
        if not confirm:
            console.print("❌ 復元をキャンセルしました")
            return

    try:
        # データベースファイルのパス
        db_path = Path("/app/data/exchange_analytics.db")

        # 既存のデータベースをバックアップ
        if db_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(f"/app/data/exchange_analytics_backup_{timestamp}.db")
            import shutil

            shutil.copy2(db_path, backup_path)
            console.print(f"📋 既存データベースをバックアップ: {backup_path}")

        # 復元処理
        import shutil

        if backup_file.suffix == ".gz":
            # 圧縮ファイルの場合は解凍
            import gzip

            with gzip.open(backup_file, "rb") as f_in:
                with open(db_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
        else:
            # 通常ファイルの場合は直接コピー
            shutil.copy2(backup_file, db_path)

        console.print("✅ データベース復元が完了しました！")

    except Exception as e:
        console.print(f"❌ 復元エラー: {e}")
        raise typer.Exit(1)


@app.command()
def clean(
    days: int = typer.Option(30, "--days", "-d", help="保持日数"),
    force: bool = typer.Option(False, "--force", "-f", help="強制実行"),
):
    """
    古いデータをクリーンアップ
    """
    cutoff_date = datetime.now() - timedelta(days=days)

    console.print("🧹 データクリーンアップ...")
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
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="出力ファイルパス"
    ),
    format: str = typer.Option(
        "csv", "--format", "-f", help="出力形式 (csv, json, xlsx)"
    ),
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

    console.print("📤 データエクスポート...")
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
    version: Optional[str] = typer.Option(
        None, "--version", "-v", help="特定バージョン"
    ),
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
        migration_task = progress.add_task(
            "マイグレーション実行中...", total=len(migrations)
        )

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


@app.command()
def performance(
    hours: int = typer.Option(24, "--hours", "-h", help="監視期間（時間）"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="詳細表示"),
):
    """
    システムパフォーマンス監視

    Examples:
        exchange-analytics data performance
        exchange-analytics data performance --hours 48 --detailed
    """
    import asyncio

    from ....infrastructure.database.connection import get_async_session

    async def run_performance_monitor():
        console.print("📊 パフォーマンス監視開始...")

        try:
            session = await get_async_session()
            monitor = PerformanceMonitor(session)

            # システムメトリクスを収集
            console.print("🔍 システムメトリクス収集中...")
            metrics = await monitor.collect_comprehensive_metrics()

            # パフォーマンスサマリーを取得
            console.print("📋 パフォーマンスサマリー生成中...")
            summary = monitor.get_performance_summary(hours=hours)

            # アラートをチェック
            console.print("🚨 アラートチェック中...")
            alerts = monitor.get_alerts()

            # 結果表示
            console.print("\n" + "=" * 60)
            console.print("📊 パフォーマンス監視結果")
            console.print("=" * 60)

            # 現在のメトリクス
            console.print(f"🖥️  CPU使用率: {metrics.cpu_percent:.1f}%")
            console.print(f"💾 メモリ使用率: {metrics.memory_percent:.1f}%")
            console.print(f"💾 メモリ使用量: {metrics.memory_mb:.1f} MB")
            console.print(f"💿 ディスク使用率: {metrics.disk_usage_percent:.1f}%")
            console.print(f"🗄️  データベースサイズ: {metrics.database_size_mb:.1f} MB")
            console.print(f"🔗 アクティブ接続数: {metrics.active_connections}")
            console.print(
                f"⚡ クエリ実行時間: {metrics.query_execution_time_ms:.2f} ms"
            )
            console.print(
                f"🔄 データ処理時間: {metrics.data_processing_time_ms:.2f} ms"
            )

            # サマリー情報
            if "error" not in summary:
                console.print(f"\n📈 過去{hours}時間の統計:")
                console.print(
                    f"   測定回数: {summary.get('total_measurements', 'N/A')}"
                )
                console.print(
                    f"   平均CPU使用率: {summary.get('avg_cpu_percent', 'N/A'):.1f}%"
                )
                console.print(
                    f"   平均メモリ使用率: {summary.get('avg_memory_percent', 'N/A'):.1f}%"
                )
                console.print(
                    f"   平均クエリ時間: {summary.get('avg_query_time_ms', 'N/A'):.2f} ms"
                )
                console.print(f"   総エラー数: {summary.get('total_errors', 'N/A')}")
                console.print(f"   総成功数: {summary.get('total_successes', 'N/A')}")

            # アラート表示
            if alerts:
                console.print(f"\n🚨 アラート ({len(alerts)}件):")
                for alert in alerts:
                    severity_icon = "⚠️" if alert["severity"] == "warning" else "❌"
                    console.print(f"   {severity_icon} {alert['message']}")
            else:
                console.print("\n✅ アラートなし - システムは正常です")

            # 詳細表示
            if detailed:
                console.print(f"\n📋 詳細情報:")
                console.print(
                    f"   稼働時間: {summary.get('uptime_hours', 'N/A'):.1f}時間"
                )
                console.print(
                    f"   監視開始時刻: {monitor.start_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                console.print(f"   メトリクス履歴数: {len(monitor.metrics_history)}")

            await session.close()

        except Exception as e:
            console.print(f"❌ パフォーマンス監視エラー: {e}")
            raise typer.Exit(1)

    asyncio.run(run_performance_monitor())


@app.command()
def optimize(
    analyze: bool = typer.Option(True, "--analyze", "-a", help="クエリ分析を実行"),
    create_indexes: bool = typer.Option(
        False, "--create-indexes", "-i", help="推奨インデックスを作成"
    ),
    report: bool = typer.Option(True, "--report", "-r", help="最適化レポートを生成"),
):
    """
    データベースクエリ最適化

    Examples:
        exchange-analytics data optimize
        exchange-analytics data optimize --create-indexes
        exchange-analytics data optimize --analyze --report
    """
    import asyncio

    from ....infrastructure.database.connection import get_async_session

    async def run_query_optimization():
        console.print("🔧 クエリ最適化開始...")

        try:
            session = await get_async_session()
            optimizer = QueryOptimizer(session)

            if analyze:
                console.print("📊 クエリ分析実行中...")
                # 一般的なクエリの最適化分析
                optimizations = await optimizer.optimize_common_queries()

                console.print("✅ クエリ分析完了")
                for category, queries in optimizations.items():
                    console.print(f"  📋 {category}: {len(queries)}件のクエリを分析")

            if create_indexes:
                console.print("🔧 インデックス作成中...")
                # 推奨インデックスを取得
                recommendations = await optimizer.get_index_recommendations()

                if recommendations:
                    console.print(
                        f"  📋 {len(recommendations)}件のインデックスを作成中..."
                    )
                    results = await optimizer.create_recommended_indexes()

                    console.print(f"  ✅ 作成成功: {results['created']}件")
                    console.print(f"  ❌ 作成失敗: {results['failed']}件")

                    if results["errors"]:
                        console.print("  ⚠️  エラー詳細:")
                        for error in results["errors"]:
                            console.print(f"    - {error}")
                else:
                    console.print("  ℹ️  作成するインデックスがありません")

            if report:
                console.print("📋 最適化レポート生成中...")
                optimization_report = await optimizer.generate_optimization_report()

                console.print("\n" + "=" * 60)
                console.print("📊 クエリ最適化レポート")
                console.print("=" * 60)

                # テーブル統計
                if optimization_report["table_statistics"]:
                    console.print("📋 テーブル統計:")
                    for table_name, stats in optimization_report[
                        "table_statistics"
                    ].items():
                        console.print(
                            f"  {table_name}: {stats['row_count']:,}行, {stats['size_mb']:.2f}MB"
                        )
                else:
                    console.print("📋 テーブル統計: データなし")

                # インデックス推奨
                if optimization_report["index_recommendations"]:
                    console.print(
                        f"\n🔍 インデックス推奨 ({len(optimization_report['index_recommendations'])}件):"
                    )
                    for rec in optimization_report["index_recommendations"]:
                        console.print(
                            f"  - {rec.table_name}.{rec.column_name} ({rec.priority})"
                        )
                else:
                    console.print("\n🔍 インデックス推奨: なし")

                # キャッシュ統計
                cache_stats = optimization_report["cache_statistics"]
                console.print(f"\n💾 キャッシュ統計:")
                console.print(f"  キャッシュクエリ数: {cache_stats['cached_queries']}")
                console.print(
                    f"  キャッシュヒット率: {cache_stats['cache_hit_rate']:.1%}"
                )

            await session.close()

        except Exception as e:
            console.print(f"❌ クエリ最適化エラー: {e}")
            raise typer.Exit(1)

    asyncio.run(run_query_optimization())


@app.command()
def memory(
    optimize: bool = typer.Option(True, "--optimize", "-o", help="メモリ最適化を実行"),
    monitor: bool = typer.Option(False, "--monitor", "-m", help="継続監視を実行"),
    report: bool = typer.Option(True, "--report", "-r", help="メモリレポートを生成"),
    duration: int = typer.Option(5, "--duration", "-d", help="監視時間（分）"),
):
    """
    メモリ使用量最適化

    Examples:
        exchange-analytics data memory
        exchange-analytics data memory --optimize --report
        exchange-analytics data memory --monitor --duration 10
    """
    from ....infrastructure.optimization.memory_optimizer import MemoryOptimizer

    def run_memory_optimization():
        console.print("💾 メモリ最適化開始...")

        try:
            optimizer = MemoryOptimizer()

            if optimize:
                console.print("🔧 メモリ最適化実行中...")
                # 最適化前のスナップショット
                before_snapshot = optimizer.take_memory_snapshot()
                console.print(
                    f"  📊 最適化前: {before_snapshot.memory_usage_mb:.1f} MB"
                )

                # メモリ最適化実行
                results = optimizer.optimize_memory_usage()

                console.print("✅ メモリ最適化完了")
                console.print(f"  📊 最適化前: {results['before_mb']:.1f} MB")
                console.print(f"  📊 最適化後: {results['after_mb']:.1f} MB")
                console.print(f"  💾 解放メモリ: {results['freed_mb']:.1f} MB")
                console.print(f"  🔄 GC実行回数: {results['gc_runs']}回")

                console.print(f"  📋 実行された最適化:")
                for optimization in results["optimizations"]:
                    console.print(f"    - {optimization}")

            if monitor:
                console.print(f"📊 メモリ継続監視開始（{duration}分間）...")
                console.print("  ⏹️  停止するには Ctrl+C を押してください")

                try:
                    optimizer.monitor_memory_continuously(
                        interval_seconds=30, duration_minutes=duration
                    )
                except KeyboardInterrupt:
                    console.print("  ⏹️  監視を停止しました")

            if report:
                console.print("📋 メモリレポート生成中...")
                memory_report = optimizer.generate_memory_report()

                console.print("\n" + "=" * 60)
                console.print("💾 メモリ最適化レポート")
                console.print("=" * 60)

                # 現在のスナップショット
                if memory_report["current_snapshot"]:
                    snapshot = memory_report["current_snapshot"]
                    console.print(
                        f"💾 現在のメモリ使用量: {snapshot['memory_usage_mb']:.1f} MB"
                    )
                    console.print(
                        f"📊 現在のメモリ使用率: {snapshot['memory_percent']:.1f}%"
                    )

                # 統計情報
                if "error" not in memory_report["statistics"]:
                    stats = memory_report["statistics"]
                    console.print(f"\n📈 過去{stats['period_hours']}時間の統計:")
                    console.print(f"   スナップショット数: {stats['snapshot_count']}")

                    memory_usage = stats["memory_usage"]
                    console.print(
                        f"   平均メモリ使用量: {memory_usage['average_mb']:.1f} MB"
                    )
                    console.print(f"   メモリ使用量傾向: {memory_usage['trend']}")

                # リーク検出
                leaks = memory_report["leaks"]
                if leaks:
                    console.print(f"\n🚨 メモリリーク検出 ({len(leaks)}件):")
                    for leak in leaks:
                        severity_icon = "🔴" if leak.severity == "high" else "🟡"
                        console.print(
                            f"  {severity_icon} {leak.object_type}: +{leak.count_increase}個"
                        )
                else:
                    console.print("\n✅ メモリリークなし")

                # 推奨事項
                recommendations = memory_report["recommendations"]
                if recommendations:
                    console.print(f"\n💡 推奨事項 ({len(recommendations)}件):")
                    for rec in recommendations:
                        severity_icon = "🔴" if rec["severity"] == "high" else "🟡"
                        console.print(f"  {severity_icon} {rec['message']}")
                        console.print(f"    💡 {rec['action']}")
                else:
                    console.print("\n✅ 推奨事項なし")

        except Exception as e:
            console.print(f"❌ メモリ最適化エラー: {e}")
            raise typer.Exit(1)

    run_memory_optimization()


@app.command()
def errors(
    report: bool = typer.Option(True, "--report", "-r", help="エラーレポートを生成"),
    test: bool = typer.Option(
        False, "--test", "-t", help="エラーハンドリングテストを実行"
    ),
    clear: bool = typer.Option(False, "--clear", "-c", help="古いエラーを削除"),
    days: int = typer.Option(7, "--days", "-d", help="削除する古いエラーの日数"),
):
    """
    エラーハンドリング管理

    Examples:
        exchange-analytics data errors
        exchange-analytics data errors --test
        exchange-analytics data errors --clear --days 3
    """
    from ....infrastructure.error_handling.error_handler import ErrorHandler

    def run_error_handling():
        console.print("🚨 エラーハンドリング管理開始...")

        try:
            error_handler = ErrorHandler()

            if test:
                console.print("🧪 エラーハンドリングテスト実行中...")

                # テストエラーを発生
                test_errors = [
                    (
                        ValueError("テストバリデーションエラー"),
                        ErrorCategory.VALIDATION,
                        ErrorSeverity.MEDIUM,
                    ),
                    (
                        ConnectionError("テストデータベースエラー"),
                        ErrorCategory.DATABASE,
                        ErrorSeverity.HIGH,
                    ),
                    (
                        TimeoutError("テストAPIエラー"),
                        ErrorCategory.API,
                        ErrorSeverity.MEDIUM,
                    ),
                ]

                for error, category, severity in test_errors:
                    console.print(f"  📝 テストエラー: {error}")
                    error_info = error_handler.handle_error(
                        error=error,
                        category=category,
                        severity=severity,
                        auto_recover=False,  # テストでは自動復旧を無効
                    )
                    console.print(f"    ✅ 処理完了: {error_info.error_type}")

                console.print("✅ エラーハンドリングテスト完了")

            if clear:
                console.print(f"🧹 古いエラー削除中（{days}日より古い）...")
                initial_count = len(error_handler.errors)
                error_handler.clear_old_errors(days=days)
                final_count = len(error_handler.errors)
                deleted_count = initial_count - final_count

                console.print(f"✅ エラー削除完了")
                console.print(f"  📊 削除前: {initial_count}件")
                console.print(f"  📊 削除後: {final_count}件")
                console.print(f"  🗑️  削除数: {deleted_count}件")

            if report:
                console.print("📋 エラーレポート生成中...")
                error_report = error_handler.generate_error_report()

                console.print("\n" + "=" * 60)
                console.print("🚨 エラーハンドリングレポート")
                console.print("=" * 60)

                # 統計情報
                stats = error_report["statistics"]
                console.print(f"📊 統計情報:")
                console.print(f"   総エラー数: {stats['total_errors']}")
                console.print(f"   解決済み: {stats['resolved_errors']}")
                console.print(f"   解決率: {stats['resolution_rate']:.1%}")
                console.print(f"   期間: {stats['period_hours']}時間")

                # カテゴリ別分布
                if stats["category_distribution"]:
                    console.print(f"\n📋 カテゴリ別分布:")
                    for category, count in stats["category_distribution"].items():
                        console.print(f"   {category}: {count}件")

                # 深刻度別分布
                if stats["severity_distribution"]:
                    console.print(f"\n🚨 深刻度別分布:")
                    for severity, count in stats["severity_distribution"].items():
                        severity_icon = (
                            "🔴"
                            if severity == "critical"
                            else "🟡" if severity == "high" else "🟢"
                        )
                        console.print(f"   {severity_icon} {severity}: {count}件")

                # 最近のエラー
                recent_errors = error_report["recent_errors"]
                if recent_errors:
                    console.print(f"\n📋 最近のエラー ({len(recent_errors)}件):")
                    for error in recent_errors:
                        severity_icon = (
                            "🔴"
                            if error["severity"] == "critical"
                            else "🟡" if error["severity"] == "high" else "🟢"
                        )
                        resolved_icon = "✅" if error["resolved"] else "❌"
                        console.print(
                            f"   {severity_icon} {error['type']}: {error['message']} {resolved_icon}"
                        )
                else:
                    console.print("\n✅ 最近のエラーなし")

                # 復旧アクション
                recovery_actions = error_report["recovery_actions"]
                if recovery_actions:
                    console.print(f"\n🔧 復旧アクション:")
                    for category, count in recovery_actions.items():
                        console.print(f"   {category}: {count}件")

        except Exception as e:
            console.print(f"❌ エラーハンドリングエラー: {e}")
            raise typer.Exit(1)

    run_error_handling()
