"""
Data Show Commands
データ表示コマンド

責任:
- データベースの状態表示
- 価格データの表示
- テクニカル指標データの表示
"""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from sqlalchemy import Float, Integer, desc, func, select, text

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.utils.logging_config import get_presentation_logger

logger = get_presentation_logger()
console = Console()

show_app = typer.Typer(
    name="show",
    help="📊 データ表示コマンド",
    no_args_is_help=True,
)


@show_app.command()
def list(
    limit: int = typer.Option(30, "--limit", "-l", help="表示件数"),
    currency_pair: str = typer.Option("USD/JPY", "--pair", "-p", help="通貨ペア"),
    table: str = typer.Option("price_data", "--table", "-t", help="テーブル名"),
    timeframe: str = typer.Option(
        "5m", "--timeframe", "-tf", help="時間足 (5m, 1h, 4h, 1d)"
    ),
    source: str = typer.Option(
        "all", "--source", "-s", help="データソース (real, aggregated, ongoing, all)"
    ),
    indicator_type: Optional[str] = typer.Option(
        None, "--indicator-type", "-it", help="指標タイプ (RSI, MACD, SMA等)"
    ),
    period: Optional[float] = typer.Option(None, "--period", "-pr", help="指標期間"),
):
    """
    データベースのデータを表示

    Examples:
        exchange-analytics data show list
        exchange-analytics data show list --table price_data --limit 50
        exchange-analytics data show list --table technical_indicators --indicator-type RSI
    """
    console.print(f"📊 データ表示開始...")
    console.print(f"💱 通貨ペア: {currency_pair}")
    console.print(f"📋 テーブル: {table}")
    console.print(f"⏰ 時間足: {timeframe}")
    console.print(f"🔌 データソース: {source}")
    console.print(f"📈 表示件数: {limit}件")

    try:
        # 環境変数を設定
        import os
        os.environ["DATABASE_URL"] = (
            "postgresql+asyncpg://exchange_analytics_user:"
            "exchange_password@localhost:5432/exchange_analytics_production_db"
        )
        
        # 非同期データベース接続を使用
        async def fetch_data():
            session = await get_async_session()
            try:
                # データを取得
                if table == "price_data":
                    # 時間足とデータソースでフィルタリング
                    query = select(PriceDataModel).where(
                        PriceDataModel.currency_pair == currency_pair
                    )

                    # データソースフィルタリング
                    if source == "real":
                        query = query.where(
                            PriceDataModel.data_source.in_(["yahoo_finance", "5m Real"])
                        )
                    elif source == "aggregated":
                        query = query.where(
                            PriceDataModel.data_source.like("%Aggregated%")
                        ).where(~PriceDataModel.data_source.like("%Ongoing%"))
                    elif source == "ongoing":
                        query = query.where(
                            PriceDataModel.data_source.like("%Ongoing%")
                        )
                    # source == "all" の場合はフィルタリングなし

                    # 時間足フィルタリング（データソースから判定）
                    if timeframe == "5m":
                        query = query.where(
                            (PriceDataModel.data_source.like("%5m%"))
                            | (PriceDataModel.data_source.like("%M5%"))
                            | (PriceDataModel.data_source == "yahoo_finance")
                        )
                    elif timeframe == "1h":
                        query = query.where(
                            (PriceDataModel.data_source.like("%1h%"))
                            | (PriceDataModel.data_source.like("%H1%"))
                            | (PriceDataModel.data_source.like("%1時間足%"))
                            | (PriceDataModel.data_source == "yahoo_finance")
                        )
                    elif timeframe == "4h":
                        query = query.where(
                            (PriceDataModel.data_source.like("%4h%"))
                            | (PriceDataModel.data_source.like("%H4%"))
                            | (PriceDataModel.data_source.like("%4時間足%"))
                            | (PriceDataModel.data_source == "yahoo_finance")
                        )
                    elif timeframe == "1d":
                        query = query.where(
                            (PriceDataModel.data_source.like("%1d%"))
                            | (PriceDataModel.data_source.like("%D1%"))
                            | (PriceDataModel.data_source.like("%日足%"))
                            | (PriceDataModel.data_source == "yahoo_finance")
                        )

                    query = query.order_by(desc(PriceDataModel.timestamp)).limit(limit)

                    result = await session.execute(query)
                    return result.scalars().all()

                elif table == "technical_indicators":
                    # テクニカル指標の場合は時間足と指標タイプでフィルタリング
                    query = select(TechnicalIndicatorModel).where(
                        TechnicalIndicatorModel.currency_pair == currency_pair
                    )

                    # 時間足フィルタリング（CLIの時間足をDBの形式に変換）
                    timeframe_mapping = {"5m": "M5", "1h": "H1", "4h": "H4", "1d": "D1"}
                    db_timeframe = timeframe_mapping.get(timeframe, timeframe)
                    query = query.where(
                        TechnicalIndicatorModel.timeframe == db_timeframe
                    )

                    # 指標タイプフィルタリング
                    if indicator_type:
                        query = query.where(
                            TechnicalIndicatorModel.indicator_type
                            == indicator_type.upper()
                        )

                    # 期間フィルタリング
                    if period:
                        # RSIの場合はadditional_dataから期間を取得
                        if indicator_type and indicator_type.upper() == "RSI":
                            query = query.where(
                                func.jsonb_extract_path_text(
                                    TechnicalIndicatorModel.additional_data, "period"
                                ).cast(Float)
                                == float(period)
                            )
                        # 移動平均の場合はparametersから期間を取得
                        elif indicator_type and indicator_type.upper() in [
                            "SMA",
                            "EMA",
                        ]:
                            query = query.where(
                                func.jsonb_extract_path_text(
                                    TechnicalIndicatorModel.parameters, "period"
                                ).cast(Float)
                                == float(period)
                            )

                    query = query.order_by(
                        desc(TechnicalIndicatorModel.timestamp)
                    ).limit(limit)

                    result = await session.execute(query)
                    return result.scalars().all()

                else:
                    raise ValueError(f"サポートされていないテーブル: {table}")

            finally:
                await session.close()

        # 非同期実行
        console.print("🔄 データベースからデータを取得中...")
        data = asyncio.run(fetch_data())
        console.print(f"📊 取得したデータ件数: {len(data) if data else 0}")

        if not data:
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

        try:
            # データテーブルを作成
            console.print("📋 データテーブルを作成中...")
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

                for row in data:
                    # タイムスタンプを日本時間で表示
                    import pytz

                    jst = pytz.timezone("Asia/Tokyo")

                    # タイムスタンプが日本時間でない場合は変換
                    display_timestamp = row.timestamp
                    if display_timestamp.tzinfo != jst:
                        if display_timestamp.tzinfo is None:
                            display_timestamp = jst.localize(display_timestamp)
                        else:
                            display_timestamp = display_timestamp.astimezone(jst)

                    data_table.add_row(
                        display_timestamp.strftime("%Y-%m-%d\n%H:%M:%S+09:00"),
                        f"{row.open_price:.4f}",
                        f"{row.high_price:.4f}",
                        f"{row.low_price:.4f}",
                        f"{row.close_price:.4f}",
                        str(row.data_source),
                    )

            elif table == "technical_indicators":
                data_table.add_column("タイムスタンプ", style="cyan")
                data_table.add_column("指標タイプ", style="green")
                data_table.add_column("時間軸", style="blue")
                data_table.add_column("値", style="yellow")
                data_table.add_column("追加データ", style="magenta")

                for row in data:
                    # タイムスタンプを日本時間で表示
                    import pytz

                    jst = pytz.timezone("Asia/Tokyo")

                    # タイムスタンプが日本時間でない場合は変換
                    display_timestamp = row.timestamp
                    if display_timestamp.tzinfo != jst:
                        if display_timestamp.tzinfo is None:
                            display_timestamp = jst.localize(display_timestamp)
                        else:
                            display_timestamp = display_timestamp.astimezone(jst)

                    data_table.add_row(
                        display_timestamp.strftime("%Y-%m-%d\n%H:%M:%S+09:00"),
                        str(row.indicator_type),
                        str(row.timeframe),
                        f"{row.value:.4f}" if row.value else "N/A",
                        str(row.additional_data) if row.additional_data else "N/A",
                    )

            console.print(data_table)

        except Exception as e:
            console.print(f"❌ データ表示エラー: {e}")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"❌ データ取得エラー: {e}")
        raise typer.Exit(1)


@show_app.command()
def status():
    """
    データベースの状態を表示

    Examples:
        exchange-analytics data show status
    """
    console.print("📊 データベース状態確認中...")

    try:
        # 環境変数を設定
        import os
        os.environ["DATABASE_URL"] = (
            "postgresql+asyncpg://exchange_analytics_user:"
            "exchange_password@localhost:5432/exchange_analytics_production_db"
        )
        
        # 非同期データベース接続を使用
        async def check_database_status():
            session = await get_async_session()
            try:
                # データベース情報を取得
                result = await session.execute(text("SELECT current_database()"))
                database_name = result.scalar()

                result = await session.execute(text("SELECT current_user"))
                current_user = result.scalar()

                result = await session.execute(text("SELECT version()"))
                version = result.scalar()

                # テーブル一覧を取得
                result = await session.execute(
                    text(
                        """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                    )
                )
                tables = [row[0] for row in result.fetchall()]
                table_count = len(tables)

                # 各テーブルのレコード数を取得
                total_records = 0
                table_records = {}

                for table in tables:
                    result = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table}")
                    )
                    count = result.scalar()
                    table_records[table] = count
                    total_records += count

                # データベースサイズを取得
                result = await session.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_database_size(current_database())) as size
                """
                    )
                )
                db_size = result.scalar()

                return {
                    "database_name": database_name,
                    "current_user": current_user,
                    "version": version,
                    "table_count": table_count,
                    "total_records": total_records,
                    "table_records": table_records,
                    "db_size": db_size,
                }

            finally:
                await session.close()

        # 非同期実行
        import asyncio

        db_status = asyncio.run(check_database_status())

        # 状態データを作成
        status_data = {
            "データベース": "PostgreSQL",
            "データベース名": db_status["database_name"],
            "ユーザー": db_status["current_user"],
            "バージョン": db_status["version"].split()[0],
            "データベースサイズ": db_status["db_size"],
            "テーブル数": str(db_status["table_count"]),
            "総レコード数": f"{db_status['total_records']:,}",
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
        if db_status["table_records"]:
            detail_table = Table(title="📋 テーブル詳細")
            detail_table.add_column("テーブル名", style="cyan")
            detail_table.add_column("レコード数", style="green")

            for table_name, count in db_status["table_records"].items():
                detail_table.add_row(table_name, f"{count:,}")

            console.print(detail_table)

        # サマリーパネル
        summary_panel = Panel(
            "✅ PostgreSQLデータベースは正常に動作しています",
            title="📋 サマリー",
            border_style="green",
        )

        console.print(summary_panel)

    except Exception as e:
        console.print(f"❌ 状態確認エラー: {e}")
        raise typer.Exit(1)
