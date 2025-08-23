"""
Technical Visualizer
テクニカル指標可視化システム

責任:
- 時間足ごとのテクニカル指標統合表示
- 指標組み合わせ分析
- 視認性向上機能（カラーコーディング、グラフィカル表示）
- 統計サマリー提供

設計書参照:
- CLIデータベース初期化システム実装仕様書_2025.md
"""

import argparse
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)

console = Console()


class TechnicalVisualizer:
    """
    テクニカル指標可視化クラス
    
    時間足ごとにテクニカル指標を組み合わせて視認性の高い出力を提供
    """

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair: str = currency_pair
        self.session: Optional[AsyncSession] = None

        # 指標設定
        self.indicators_config = {
            "RSI": {"overbought": 70, "oversold": 30, "neutral": 50},
            "MACD": {"bullish": 0, "bearish": 0},
            "BB": {"upper": 0.8, "lower": 0.2},
            "STOCH": {"overbought": 80, "oversold": 20},
        }

        # カラー設定
        self.colors = {
            "bullish": "green",
            "bearish": "red",
            "neutral": "yellow",
            "overbought": "red",
            "oversold": "green",
            "normal": "white",
        }

    async def visualize_timeframe(
        self, timeframe: str, days: int, detailed: bool, indicators: List[str]
    ) -> None:
        """
        特定時間足のテクニカル指標を可視化

        Args:
            timeframe: 時間足
            days: 表示期間
            detailed: 詳細表示
            indicators: 表示する指標
        """
        try:
            # データ取得
            data = await self._get_technical_data(timeframe, days, indicators)
            
            if data.empty:
                console.print(f"⚠️ {timeframe}のテクニカル指標データがありません")
                return

            # ヘッダー表示
            self._display_header(timeframe, days, len(data))

            # データ表示
            if detailed:
                self._display_detailed_data(data, indicators)
            else:
                self._display_summary_data(data, indicators)

            # 統計サマリー表示
            self._display_statistics(data, indicators)

        except Exception as e:
            console.print(f"❌ {timeframe}可視化エラー: {e}")

    async def _get_technical_data(
        self, timeframe: str, days: int, indicators: List[str]
    ) -> pd.DataFrame:
        """
        テクニカル指標データを取得

        Args:
            timeframe: 時間足
            days: 表示期間
            indicators: 表示する指標

        Returns:
            pd.DataFrame: テクニカル指標データ
        """
        try:
            # 期間設定
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # データベースからテクニカル指標データを取得
            query = (
                select(TechnicalIndicatorModel)
                .where(
                    TechnicalIndicatorModel.currency_pair == self.currency_pair,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.timestamp >= start_date,
                    TechnicalIndicatorModel.timestamp <= end_date
                )
                .order_by(TechnicalIndicatorModel.timestamp.desc())
            )

            result = await self.session.execute(query)
            indicator_data = result.scalars().all()

            if not indicator_data:
                return pd.DataFrame()

            # DataFrameに変換
            data = []
            for item in indicator_data:
                # 指標タイプのフィルタリング
                if indicators != ["all"] and item.indicator_type not in [ind.upper() for ind in indicators]:
                    continue
                
                data.append({
                    "timestamp": item.timestamp,
                    "indicator_type": item.indicator_type,
                    "value": float(item.value),
                    "parameters": item.parameters,
                })

            df = pd.DataFrame(data)
            
            if df.empty:
                return df

            # ピボットテーブルで時間足別に整理
            pivot_df = df.pivot_table(
                index="timestamp",
                columns="indicator_type",
                values="value",
                aggfunc="first"
            ).reset_index()

            return pivot_df

        except Exception as e:
            console.print(f"❌ データ取得エラー: {e}")
            return pd.DataFrame()

    def _display_header(self, timeframe: str, days: int, data_count: int) -> None:
        """
        ヘッダーを表示

        Args:
            timeframe: 時間足
            days: 表示期間
            data_count: データ件数
        """
        title = f"📊 USD/JPY - {timeframe}時間足 テクニカル指標分析"
        subtitle = f"期間: {days}日 | データ件数: {data_count}件 | 生成時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        panel = Panel(
            subtitle,
            title=title,
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)

    def _display_summary_data(self, data: pd.DataFrame, indicators: List[str]) -> None:
        """
        サマリーデータを表示

        Args:
            data: テクニカル指標データ
            indicators: 表示する指標
        """
        console.print("\n📈 最新テクニカル指標サマリー")
        console.print("=" * 80)

        # 最新データを取得
        latest_data = data.head(10)

        # テーブル作成
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("タイムスタンプ", style="cyan", width=20)
        
        # 指標カラムを追加
        for indicator in indicators:
            if indicator == "all":
                for col in data.columns:
                    if col != "timestamp":
                        table.add_column(col, style="white", width=12)
                break
            else:
                indicator_upper = indicator.upper()
                if indicator_upper in data.columns:
                    table.add_column(indicator_upper, style="white", width=12)

        # データ行を追加
        for _, row in latest_data.iterrows():
            timestamp = row["timestamp"].strftime("%m-%d %H:%M")
            table_row = [timestamp]
            
            for col in data.columns:
                if col != "timestamp":
                    value = row[col]
                    if pd.isna(value):
                        table_row.append("-")
                    else:
                        # カラーコーディング
                        color = self._get_value_color(col, value)
                        table_row.append(f"[{color}]{value:.2f}[/{color}]")
            
            table.add_row(*table_row)

        console.print(table)

    def _display_detailed_data(self, data: pd.DataFrame, indicators: List[str]) -> None:
        """
        詳細データを表示

        Args:
            data: テクニカル指標データ
            indicators: 表示する指標
        """
        console.print("\n📊 詳細テクニカル指標データ")
        console.print("=" * 80)

        # 全データを表示（最大50件）
        display_data = data.head(50)

        # テーブル作成
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("タイムスタンプ", style="cyan", width=20)
        
        # 指標カラムを追加
        for indicator in indicators:
            if indicator == "all":
                for col in data.columns:
                    if col != "timestamp":
                        table.add_column(col, style="white", width=12)
                break
            else:
                indicator_upper = indicator.upper()
                if indicator_upper in data.columns:
                    table.add_column(indicator_upper, style="white", width=12)

        # データ行を追加
        for _, row in display_data.iterrows():
            timestamp = row["timestamp"].strftime("%m-%d %H:%M")
            table_row = [timestamp]
            
            for col in data.columns:
                if col != "timestamp":
                    value = row[col]
                    if pd.isna(value):
                        table_row.append("-")
                    else:
                        # カラーコーディング
                        color = self._get_value_color(col, value)
                        table_row.append(f"[{color}]{value:.2f}[/{color}]")
            
            table.add_row(*table_row)

        console.print(table)

    def _display_statistics(self, data: pd.DataFrame, indicators: List[str]) -> None:
        """
        統計サマリーを表示

        Args:
            data: テクニカル指標データ
            indicators: 表示する指標
        """
        console.print("\n📋 統計サマリー")
        console.print("=" * 50)

        # 統計テーブル作成
        stats_table = Table(show_header=True, header_style="bold green")
        stats_table.add_column("指標", style="cyan", width=10)
        stats_table.add_column("平均値", style="white", width=12)
        stats_table.add_column("最小値", style="white", width=12)
        stats_table.add_column("最大値", style="white", width=12)
        stats_table.add_column("トレンド", style="white", width=15)

        # 各指標の統計を計算
        for indicator in indicators:
            if indicator == "all":
                for col in data.columns:
                    if col != "timestamp":
                        self._add_statistics_row(stats_table, col, data[col])
                break
            else:
                indicator_upper = indicator.upper()
                if indicator_upper in data.columns:
                    self._add_statistics_row(stats_table, indicator_upper, data[indicator_upper])

        console.print(stats_table)

        # シグナル分析
        self._display_signal_analysis(data, indicators)

    def _add_statistics_row(self, table: Table, indicator: str, series: pd.Series) -> None:
        """
        統計行をテーブルに追加

        Args:
            table: テーブル
            indicator: 指標名
            series: データ系列
        """
        if series.empty or series.isna().all():
            return

        # 統計計算
        mean_val = series.mean()
        min_val = series.min()
        max_val = series.max()
        
        # トレンド判定
        trend = self._calculate_trend(series)
        trend_color = "green" if trend == "上昇" else "red" if trend == "下降" else "yellow"
        
        table.add_row(
            indicator,
            f"{mean_val:.2f}",
            f"{min_val:.2f}",
            f"{max_val:.2f}",
            f"[{trend_color}]{trend}[/{trend_color}]"
        )

    def _calculate_trend(self, series: pd.Series) -> str:
        """
        トレンドを計算

        Args:
            series: データ系列

        Returns:
            str: トレンド（上昇/下降/横ばい）
        """
        if len(series) < 2:
            return "横ばい"
        
        # 最新5点の平均と最初5点の平均を比較
        recent_avg = series.head(5).mean()
        initial_avg = series.tail(5).mean()
        
        diff = recent_avg - initial_avg
        if abs(diff) < 0.01:  # 閾値
            return "横ばい"
        elif diff > 0:
            return "上昇"
        else:
            return "下降"

    def _get_value_color(self, indicator: str, value: float) -> str:
        """
        値に応じたカラーを取得

        Args:
            indicator: 指標名
            value: 値

        Returns:
            str: カラー名
        """
        if indicator == "RSI":
            if value >= 70:
                return self.colors["overbought"]
            elif value <= 30:
                return self.colors["oversold"]
            else:
                return self.colors["normal"]
        
        elif indicator == "STOCH":
            if value >= 80:
                return self.colors["overbought"]
            elif value <= 20:
                return self.colors["oversold"]
            else:
                return self.colors["normal"]
        
        elif indicator == "MACD":
            if value > 0:
                return self.colors["bullish"]
            else:
                return self.colors["bearish"]
        
        else:
            return self.colors["normal"]

    def _display_signal_analysis(self, data: pd.DataFrame, indicators: List[str]) -> None:
        """
        シグナル分析を表示

        Args:
            data: テクニカル指標データ
            indicators: 表示する指標
        """
        console.print("\n🎯 シグナル分析")
        console.print("=" * 30)

        signals = []
        
        # 最新データでシグナル分析
        if not data.empty:
            latest = data.iloc[0]
            
            for indicator in indicators:
                if indicator == "all":
                    for col in data.columns:
                        if col != "timestamp":
                            signal = self._analyze_signal(col, latest[col])
                            if signal:
                                signals.append(signal)
                    break
                else:
                    indicator_upper = indicator.upper()
                    if indicator_upper in data.columns:
                        signal = self._analyze_signal(indicator_upper, latest[indicator_upper])
                        if signal:
                            signals.append(signal)

        if signals:
            for signal in signals:
                console.print(f"  {signal}")
        else:
            console.print("  📊 特筆すべきシグナルなし")

    def _analyze_signal(self, indicator: str, value: float) -> Optional[str]:
        """
        シグナルを分析

        Args:
            indicator: 指標名
            value: 値

        Returns:
            Optional[str]: シグナルメッセージ
        """
        if pd.isna(value):
            return None

        if indicator == "RSI":
            if value >= 70:
                return f"🔴 RSI過買い: {value:.2f} (売りシグナル)"
            elif value <= 30:
                return f"🟢 RSI過売り: {value:.2f} (買いシグナル)"
        
        elif indicator == "STOCH":
            if value >= 80:
                return f"🔴 ストキャスティクス過買い: {value:.2f} (売りシグナル)"
            elif value <= 20:
                return f"🟢 ストキャスティクス過売り: {value:.2f} (買いシグナル)"
        
        elif indicator == "MACD":
            if value > 0:
                return f"🟢 MACD陽性: {value:.2f} (買いシグナル)"
            else:
                return f"🔴 MACD陰性: {value:.2f} (売りシグナル)"

        return None

    async def initialize(self) -> bool:
        """
        初期化処理

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            # セッションの初期化
            self.session = await get_async_session()
            return True

        except Exception as e:
            console.print(f"❌ 初期化エラー: {e}")
            return False

    async def cleanup(self) -> None:
        """
        リソースのクリーンアップ
        """
        if self.session:
            await self.session.close()


async def main():
    """
    メイン実行関数
    """
    parser = argparse.ArgumentParser(description="テクニカル指標可視化システム")
    parser.add_argument("--timeframe", default="M5", help="時間足 (M5, H1, H4, D1)")
    parser.add_argument("--days", type=int, default=7, help="表示期間（日数）")
    parser.add_argument("--detailed", action="store_true", help="詳細表示")
    parser.add_argument("--indicators", default="all", help="表示する指標 (all, rsi, macd, bb, ma, stoch, atr)")

    args = parser.parse_args()

    # 指標リストの処理
    if args.indicators == "all":
        indicators = ["all"]
    else:
        indicators = [ind.strip() for ind in args.indicators.split(",")]

    visualizer = TechnicalVisualizer()
    
    try:
        # 初期化
        if not await visualizer.initialize():
            console.print("❌ 初期化に失敗しました")
            return 1

        # 可視化実行
        await visualizer.visualize_timeframe(
            args.timeframe, args.days, args.detailed, indicators
        )

    except Exception as e:
        console.print(f"❌ 予期しないエラー: {e}")
        return 1
    finally:
        await visualizer.cleanup()

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
