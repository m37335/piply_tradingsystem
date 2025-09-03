#!/usr/bin/env python3
"""
Chart Visualizer Module
1時間足特化のチャート描写システム

既存のデータ取得機能を活用して、移動平均線とフィボナッチレベルを表示
"""

import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import mplfinance as mpf
import numpy as np
import pandas as pd
import pytz
from rich.console import Console

# プロジェクトパスを追加
sys.path.append("/app")

from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class ChartVisualizer:
    """1時間足特化チャート描写クラス"""

    def __init__(self):
        self.console = Console()
        self.jst = pytz.timezone("Asia/Tokyo")

        # チャート保存ディレクトリ
        self.chart_dir = "/app/scripts/cron/integrated_ai_discord/charts"
        self.setup_chart_directory()

        # Discord最適化設定（横サイズを拡張してフィボナッチラベル用のスペースを確保）
        self.chart_size = (1400, 800)  # 横を1200→1400に拡張
        self.chart_dpi = 100

        # カラーパレット
        self.colors = {
            "background": "#2f3136",
            "text": "#ffffff",
            "grid": "#40444b",
            "candle_up": "#43b581",
            "candle_down": "#f04747",
            "ma_20": "#ffd93d",
            "ma_50": "#6c5ce7",
            "fibonacci": "#fd79a8",
            "rsi_overbought": "#ff7675",
            "rsi_oversold": "#74b9ff",
        }

        logger.info("Initialized Chart Visualizer")

    def setup_chart_directory(self):
        """チャート保存ディレクトリのセットアップ"""
        try:
            if not os.path.exists(self.chart_dir):
                os.makedirs(self.chart_dir)
                logger.info(f"Created chart directory: {self.chart_dir}")
        except Exception as e:
            logger.error(f"Failed to create chart directory: {str(e)}")

    def create_h1_chart(
        self,
        data: pd.DataFrame,
        currency_pair: str,
        indicators_data: Dict[str, Any],
        save_chart: bool = True,
    ) -> Optional[str]:
        """
        1時間足チャート作成

        Args:
            data: OHLCVデータ
            currency_pair: 通貨ペア
            indicators_data: テクニカル指標データ
            save_chart: チャート保存フラグ

        Returns:
            str: 保存されたファイルパス（Noneの場合は失敗）
        """
        return self._create_chart(
            data, currency_pair, indicators_data, "H1", save_chart
        )

    def create_h4_chart(
        self,
        data: pd.DataFrame,
        currency_pair: str,
        indicators_data: Dict[str, Any],
        save_chart: bool = True,
    ) -> Optional[str]:
        """
        4時間足チャート作成

        Args:
            data: OHLCVデータ
            currency_pair: 通貨ペア
            indicators_data: テクニカル指標データ
            save_chart: チャート保存フラグ

        Returns:
            str: 保存されたファイルパス（Noneの場合は失敗）
        """
        return self._create_chart(
            data, currency_pair, indicators_data, "H4", save_chart
        )

    def _create_chart(
        self,
        data: pd.DataFrame,
        currency_pair: str,
        indicators_data: Dict[str, Any],
        timeframe: str,
        save_chart: bool = True,
    ) -> Optional[str]:
        """
        チャート作成（共通処理）

        Args:
            data: OHLCVデータ
            currency_pair: 通貨ペア
            indicators_data: テクニカル指標データ
            timeframe: 時間軸（H1/H4）
            save_chart: チャート保存フラグ

        Returns:
            str: 保存されたファイルパス（Noneの場合は失敗）
        """
        try:
            self.console.print(f"📊 {currency_pair} {timeframe}チャート生成中...")

            # データ形式確認
            if data is None or data.empty:
                logger.error("No data provided for chart creation")
                return None

            # データ形式をmplfinance用に変換
            chart_data = self._prepare_data_for_chart(data, timeframe)

            # チャート作成
            fig, axes = self._create_chart_layout()

            # ローソク足プロット
            self._plot_candlesticks(axes[0], chart_data)

            # 移動平均線追加
            self._add_moving_averages(axes[0], chart_data, indicators_data)

            # フィボナッチレベル追加
            self._add_fibonacci_levels(axes[0], chart_data, indicators_data)

            # 現在価格表示
            self._add_current_price(axes[0], chart_data, indicators_data)

            # チャート装飾
            self._decorate_chart(fig, axes, currency_pair, timeframe)

            # チャート保存
            if save_chart:
                file_path = self._save_chart(fig, currency_pair, timeframe)
                plt.close(fig)
                return file_path
            else:
                plt.show()
                plt.close(fig)
                return None

        except Exception as e:
            logger.error(f"Chart creation error: {str(e)}")
            return None

    def _prepare_data_for_chart(
        self, data: pd.DataFrame, timeframe: str = "H1"
    ) -> pd.DataFrame:
        """チャート用データ準備"""
        try:
            # データ形式確認
            required_columns = ["Open", "High", "Low", "Close"]
            if not all(col in data.columns for col in required_columns):
                logger.error(f"Missing required columns: {required_columns}")
                logger.error(f"Available columns: {list(data.columns)}")
                return pd.DataFrame()

            # データのコピーを作成
            chart_data = data.copy()

            # デバッグ情報を追加
            logger.info(f"Original data index type: {type(chart_data.index)}")
            logger.info(f"Original data index sample: {chart_data.index[:5]}")
            logger.info(f"Original data columns: {list(chart_data.columns)}")

            # インデックスをdatetimeに設定
            if not isinstance(chart_data.index, pd.DatetimeIndex):
                # インデックスが既にdatetimeの場合
                if isinstance(chart_data.index, pd.DatetimeIndex):
                    pass
                # インデックスが文字列の場合、datetimeに変換
                elif isinstance(chart_data.index, pd.Index):
                    try:
                        chart_data.index = pd.to_datetime(chart_data.index)
                        logger.info(f"Successfully converted index to datetime")
                    except Exception as e:
                        logger.error(f"Failed to convert index to datetime: {str(e)}")
                        # 新しいインデックスを作成
                        chart_data.index = pd.date_range(
                            start=pd.Timestamp.now()
                            - pd.Timedelta(days=len(chart_data)),
                            periods=len(chart_data),
                            freq="H",
                        )
                        logger.info(f"Created new datetime index")
                else:
                    # 新しいインデックスを作成
                    chart_data.index = pd.date_range(
                        start=pd.Timestamp.now() - pd.Timedelta(days=len(chart_data)),
                        periods=len(chart_data),
                        freq="H",
                    )
                    logger.info(f"Created new datetime index")
            else:
                logger.info(f"Index is already DatetimeIndex")

            # 数値型に変換
            for col in required_columns:
                chart_data[col] = pd.to_numeric(chart_data[col], errors="coerce")

            # 欠損値除去
            chart_data = chart_data.dropna()

            # インデックスが正しく設定されているか確認
            if not isinstance(chart_data.index, pd.DatetimeIndex):
                logger.error("Index is still not DatetimeIndex after conversion")
                return pd.DataFrame()

            logger.info(
                f"Chart data prepared: {len(chart_data)} rows, index type: {type(chart_data.index)}"
            )
            return chart_data

        except Exception as e:
            logger.error(f"Data preparation error: {str(e)}")
            return pd.DataFrame()

    def _create_chart_layout(self) -> Tuple[plt.Figure, List[plt.Axes]]:
        """チャートレイアウト作成"""
        # ダークテーマ設定
        plt.style.use("dark_background")

        # フィギュアとサブプロット作成（RSIエリア削除）
        fig, ax = plt.subplots(
            1,
            1,
            figsize=(self.chart_size[0] / 100, self.chart_size[1] / 100),
            dpi=self.chart_dpi,
        )

        # 背景色設定
        fig.patch.set_facecolor(self.colors["background"])

        return fig, [ax]

    def _plot_candlesticks(self, ax: plt.Axes, data: pd.DataFrame):
        """ローソク足プロット（1週間表示）"""
        try:
            # データが空でないか確認
            if data.empty:
                logger.error("No data available for candlestick plotting")
                return

            # 1週間分のデータ範囲を計算（168時間 = 7日 × 24時間）
            display_hours = 168
            if len(data) > display_hours:
                # 最新の1週間分のみを使用
                display_data = data.tail(display_hours)
            else:
                display_data = data

            # シンプルなローソク足プロット
            for i in range(len(display_data)):
                open_price = display_data["Open"].iloc[i]
                high_price = display_data["High"].iloc[i]
                low_price = display_data["Low"].iloc[i]
                close_price = display_data["Close"].iloc[i]

                # ローソク足の色を決定（日本式：陽線：赤、陰線：緑）
                if close_price >= open_price:
                    color = self.colors["candle_down"]  # 陽線（赤）
                else:
                    color = self.colors["candle_up"]  # 陰線（緑）

                # ヒゲ（上下の線）
                ax.plot([i, i], [low_price, high_price], color=color, linewidth=1)

                # 実体（四角形）
                body_height = abs(close_price - open_price)
                if body_height > 0:
                    if close_price >= open_price:
                        # 陽線
                        ax.bar(
                            i, body_height, bottom=open_price, color=color, width=0.8
                        )
                    else:
                        # 陰線
                        ax.bar(
                            i, body_height, bottom=close_price, color=color, width=0.8
                        )
                else:
                    # 十字線
                    ax.plot(
                        [i - 0.4, i + 0.4],
                        [open_price, open_price],
                        color=color,
                        linewidth=1,
                    )

            # 軸の設定（時間軸に応じて右側マージンを動的に調整）
            # H1: 1週間分（168時間）→ マージン5、H4: 1ヶ月分（180時間）→ マージン10
            if len(data) > 0:
                # データの時間間隔を推定
                if len(data) > 1:
                    time_diff = data.index[1] - data.index[0]
                    if isinstance(time_diff, pd.Timedelta):
                        hours_diff = time_diff.total_seconds() / 3600
                        # 時間軸に応じて右マージンを調整
                        if hours_diff >= 3.5:  # H4以上
                            right_margin = 2  # H4用（4→2に削減）
                        else:  # H1以下
                            right_margin = 5  # H1用
                    else:
                        right_margin = 5  # デフォルト
                else:
                    right_margin = 5  # デフォルト
            else:
                right_margin = 5  # デフォルト

            ax.set_xlim(-1, len(display_data) + right_margin)

            # X軸のラベルを設定（1日ごとの日時表示）
            if len(display_data) > 0:
                # 1日ごとのラベルを表示
                daily_indices = []
                daily_labels = []
                current_date = None

                for i, timestamp in enumerate(display_data.index):
                    if isinstance(timestamp, pd.Timestamp):
                        date_str = timestamp.strftime("%m/%d")
                        if date_str != current_date:
                            daily_indices.append(i)
                            daily_labels.append(date_str)
                            current_date = date_str

                # 最初と最後のデータポイントも追加（重複しない場合）
                if len(display_data) > 0:
                    first_idx = 0
                    first_date = (
                        display_data.index[0].strftime("%m/%d")
                        if isinstance(display_data.index[0], pd.Timestamp)
                        else "0"
                    )
                    if first_idx not in daily_indices:
                        daily_indices.insert(0, first_idx)
                        daily_labels.insert(0, first_date)

                if len(display_data) > 1:
                    last_idx = len(display_data) - 1
                    last_date = (
                        display_data.index[-1].strftime("%m/%d")
                        if isinstance(display_data.index[-1], pd.Timestamp)
                        else str(last_idx)
                    )
                    if last_idx not in daily_indices:
                        daily_indices.append(last_idx)
                        daily_labels.append(last_date)

                ax.set_xticks(daily_indices)
                ax.set_xticklabels(daily_labels, rotation=45)
            ax.set_ylabel("Price", color=self.colors["text"])
            ax.set_xlabel("Time", color=self.colors["text"])

            # グリッドとテーマ
            ax.set_facecolor(self.colors["background"])
            ax.grid(True, color=self.colors["grid"], alpha=0.3)
            ax.tick_params(colors=self.colors["text"])

        except Exception as e:
            logger.error(f"Candlestick plotting error: {str(e)}")
            # フォールバック: シンプルな線グラフ
            try:
                ax.plot(
                    range(len(data)),
                    data["Close"],
                    color=self.colors["text"],
                    linewidth=1,
                )
                ax.set_facecolor(self.colors["background"])
                ax.grid(True, color=self.colors["grid"], alpha=0.3)
                ax.tick_params(colors=self.colors["text"])
                ax.set_ylabel("Price", color=self.colors["text"])
                ax.set_xlabel("Time", color=self.colors["text"])
            except Exception as fallback_error:
                logger.error(f"Fallback plotting also failed: {str(fallback_error)}")

    def _add_moving_averages(
        self, ax: plt.Axes, data: pd.DataFrame, indicators_data: Dict[str, Any]
    ):
        """移動平均線追加（複数EMA、曲線表示、時間軸に応じた表示期間）"""
        try:
            # 移動平均線の色設定
            ma_colors = {
                "EMA20": "#ffd93d",  # 黄色
                "EMA50": "#6c5ce7",  # 紫色
                "EMA200": "#e17055",  # オレンジ
            }

            # 時間軸に応じた表示期間を設定
            # H1: 1週間（168時間）、H4: 1ヶ月（180時間 = 30日 × 6時間/日）
            if len(data) > 0:
                # データの時間間隔を推定
                if len(data) > 1:
                    time_diff = data.index[1] - data.index[0]
                    if isinstance(time_diff, pd.Timedelta):
                        hours_diff = time_diff.total_seconds() / 3600
                        if hours_diff >= 3.5:  # H4以上
                            display_hours = 180  # 1ヶ月分
                        else:  # H1以下
                            display_hours = 168  # 1週間分
                    else:
                        display_hours = 168  # デフォルト
                else:
                    display_hours = 168  # デフォルト
            else:
                display_hours = 168  # デフォルト

            if len(data) > display_hours:
                # 最新の表示期間分のみを使用
                display_data = data.tail(display_hours)
                start_idx = len(data) - display_hours
            else:
                display_data = data
                start_idx = 0

            # 各移動平均線を計算して描画
            ma_periods = [20, 50, 200]
            ma_labels = ["EMA20", "EMA50", "EMA200"]

            for period, label in zip(ma_periods, ma_labels):
                logger.info(
                    f"EMA{period} calculation: data length={len(data)}, required={period}"
                )

                if len(data) >= period:
                    # 全データでEMA計算（精度向上のため）
                    ema_values = self._calculate_ema(data["Close"], period)

                    if ema_values is not None and len(ema_values) > 0:
                        logger.info(
                            f"EMA{period} calculated successfully: {len(ema_values)} values"
                        )

                        # 1週間分の表示範囲でEMAを描画
                        if len(ema_values) > display_hours:
                            # 最新の1週間分のみを表示
                            display_ema = ema_values[-display_hours:]
                            x_range = range(display_hours)
                        else:
                            # データが1週間未満の場合は全データを表示
                            display_ema = ema_values
                            x_range = range(len(display_ema))

                        # 曲線で移動平均線を描画
                        ax.plot(
                            x_range,
                            display_ema,
                            color=ma_colors[label],
                            linestyle="-",
                            linewidth=1.5,
                            alpha=0.8,
                            label=f"{label}: {display_ema[-1]:.4f}",
                        )
                    else:
                        logger.warning(
                            f"EMA{period} calculation failed or returned empty values"
                        )
                else:
                    logger.warning(
                        f"EMA{period} skipped: insufficient data ({len(data)} < {period})"
                    )

            # 凡例表示
            if len(ax.get_legend_handles_labels()[0]) > 0:
                ax.legend(loc="upper left", facecolor=self.colors["background"])

        except Exception as e:
            logger.error(f"Moving average plotting error: {str(e)}")

    def _calculate_ema(self, prices: pd.Series, period: int) -> Optional[np.ndarray]:
        """EMA計算"""
        try:
            if len(prices) < period:
                return None

            # TA-Libを使用してEMA計算
            import talib

            ema_values = talib.EMA(prices.values.astype(np.float64), timeperiod=period)

            # NaN値を除去
            valid_indices = ~np.isnan(ema_values)
            if np.any(valid_indices):
                return ema_values[valid_indices]
            else:
                return None

        except Exception as e:
            logger.error(f"EMA calculation error: {str(e)}")
            return None

    def _add_fibonacci_levels(
        self, ax: plt.Axes, data: pd.DataFrame, indicators_data: Dict[str, Any]
    ):
        """フィボナッチレベル追加"""
        try:
            # 時間軸に応じた表示期間を設定
            if len(data) > 0:
                # データの時間間隔を推定
                if len(data) > 1:
                    time_diff = data.index[1] - data.index[0]
                    if isinstance(time_diff, pd.Timedelta):
                        hours_diff = time_diff.total_seconds() / 3600
                        if hours_diff >= 3.5:  # H4以上
                            display_hours = 180  # 1ヶ月分
                        else:  # H1以下
                            display_hours = 168  # 1週間分
                    else:
                        display_hours = 168  # デフォルト
                else:
                    display_hours = 168  # デフォルト
            else:
                display_hours = 168  # デフォルト

            if len(data) > display_hours:
                # 最新の表示期間分のみを使用
                display_data = data.tail(display_hours)
            else:
                display_data = data

            # 時間軸に応じてフィボナッチデータを取得
            if len(data) > 0:
                # データの時間間隔を推定
                if len(data) > 1:
                    time_diff = data.index[1] - data.index[0]
                    if isinstance(time_diff, pd.Timedelta):
                        hours_diff = time_diff.total_seconds() / 3600
                        if hours_diff >= 3.5:  # H4以上
                            fib_data = indicators_data.get("H4_FIB", {})
                        else:  # H1以下
                            fib_data = indicators_data.get("H1_FIB", {})
                    else:
                        fib_data = indicators_data.get("H1_FIB", {})
                else:
                    fib_data = indicators_data.get("H1_FIB", {})
            else:
                fib_data = indicators_data.get("H1_FIB", {})

            if fib_data and "levels" in fib_data:
                levels = fib_data["levels"]

                for level_name, level_price in levels.items():
                    if isinstance(level_price, (int, float)) and not np.isnan(
                        level_price
                    ):
                        # フィボナッチレベル線を描画
                        ax.axhline(
                            y=level_price,
                            color=self.colors["fibonacci"],
                            linestyle="--",
                            linewidth=1,
                            alpha=0.7,
                            label=f"Fib {level_name}: {level_price:.4f}",
                        )

                        # レベルラベルを追加（右側に価格も表示）
                        # 100%と0%の場合は特別なラベルを使用
                        if level_name == "100%":
                            label_text = f" High ({level_price:.4f})"
                        elif level_name == "0%":
                            label_text = f" Low ({level_price:.4f})"
                        else:
                            label_text = f" {level_name} ({level_price:.4f})"

                        # 時間軸に応じてフィボナッチラベルの位置を調整
                        if len(data) > 0:
                            # データの時間間隔を推定
                            if len(data) > 1:
                                time_diff = data.index[1] - data.index[0]
                                if isinstance(time_diff, pd.Timedelta):
                                    hours_diff = time_diff.total_seconds() / 3600
                                    # 時間軸に応じてフィボナッチ位置を調整
                                    if hours_diff >= 3.5:  # H4以上
                                        label_x = (
                                            len(display_data) - 5
                                        )  # H4用（+1→-1に変更）
                                    else:  # H1以下
                                        label_x = (
                                            len(display_data) + 6
                                        )  # H1用（+6のまま）
                                else:
                                    label_x = len(display_data) + 2  # デフォルト
                            else:
                                label_x = len(display_data) + 2  # デフォルト
                        else:
                            label_x = len(display_data) + 2  # デフォルト

                        ax.text(
                            label_x,
                            level_price,
                            label_text,
                            color=self.colors["fibonacci"],
                            fontsize=8,
                            verticalalignment="center",
                            horizontalalignment="left",
                        )

        except Exception as e:
            logger.error(f"Fibonacci levels plotting error: {str(e)}")

    def _add_current_price(
        self, ax: plt.Axes, data: pd.DataFrame, indicators_data: Dict[str, Any]
    ):
        """現在価格表示"""
        try:
            if data.empty:
                return

            # 時間軸に応じた表示期間を設定
            if len(data) > 0:
                # データの時間間隔を推定
                if len(data) > 1:
                    time_diff = data.index[1] - data.index[0]
                    if isinstance(time_diff, pd.Timedelta):
                        hours_diff = time_diff.total_seconds() / 3600
                        if hours_diff >= 3.5:  # H4以上
                            display_hours = 180  # 1ヶ月分
                        else:  # H1以下
                            display_hours = 168  # 1週間分
                    else:
                        display_hours = 168  # デフォルト
                else:
                    display_hours = 168  # デフォルト
            else:
                display_hours = 168  # デフォルト

            if len(data) > display_hours:
                # 最新の表示期間分のみを使用
                display_data = data.tail(display_hours)
            else:
                display_data = data

            # 最新の終値を取得
            current_price = display_data["Close"].iloc[-1]

            # 現在価格をグラフエリアの中（右上）に表示
            ax.text(
                0.98,  # グラフエリアの中（右側）
                0.95,  # 上部
                f"Current: {current_price:.4f}",
                color=self.colors["text"],
                fontsize=10,
                fontweight="bold",
                verticalalignment="top",
                horizontalalignment="right",
                transform=ax.transAxes,  # グラフエリアの座標系を使用
                bbox=dict(
                    boxstyle="round,pad=0.3",
                    facecolor=self.colors["background"],
                    edgecolor=self.colors["text"],
                    alpha=0.8,
                ),
            )

        except Exception as e:
            logger.error(f"Current price display error: {str(e)}")

    def _add_rsi_subplot(
        self, ax: plt.Axes, data: pd.DataFrame, indicators_data: Dict[str, Any]
    ):
        """RSIサブプロット追加"""
        try:
            # H1のRSIデータを取得
            rsi_data = indicators_data.get("H1_RSI_SHORT", {})

            if rsi_data and "current_value" in rsi_data:
                rsi_value = rsi_data["current_value"]
                if rsi_value and not np.isnan(rsi_value):
                    # RSI値を表示
                    ax.text(
                        0.5,
                        0.5,
                        f"RSI: {rsi_value:.1f}",
                        transform=ax.transAxes,
                        ha="center",
                        va="center",
                        fontsize=12,
                        color=self.colors["text"],
                        bbox=dict(
                            boxstyle="round,pad=0.5",
                            facecolor=self.colors["background"],
                            edgecolor=self.colors["grid"],
                        ),
                    )

                    # RSI状態に応じて色を変更
                    if rsi_value > 70:
                        ax.set_facecolor(self.colors["rsi_overbought"])
                    elif rsi_value < 30:
                        ax.set_facecolor(self.colors["rsi_oversold"])
                    else:
                        ax.set_facecolor(self.colors["background"])

            ax.set_title("RSI", color=self.colors["text"], fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])

        except Exception as e:
            logger.error(f"RSI subplot error: {str(e)}")

    def _decorate_chart(
        self, fig: plt.Figure, axes: List[plt.Axes], currency_pair: str, timeframe: str
    ):
        """チャート装飾"""
        try:
            # タイトル設定
            current_time = datetime.now(self.jst).strftime("%Y-%m-%d %H:%M:%S JST")
            fig.suptitle(
                f"{currency_pair} - {timeframe} Chart ({current_time})",
                color=self.colors["text"],
                fontsize=14,
                fontweight="bold",
            )

            # レイアウト調整（グラフエリアの幅を制御しつつ右側マージンを確保）
            plt.tight_layout(pad=1.0, h_pad=0.5, w_pad=0.5)

            # 時間軸に応じてグラフエリアの幅を調整
            if timeframe == "H4":
                # H4: グラフエリア80%
                fig.subplots_adjust(left=0.08, right=0.88)
            else:
                # H1: 標準的なグラフエリア
                fig.subplots_adjust(left=0.08, right=0.85)

        except Exception as e:
            logger.error(f"Chart decoration error: {str(e)}")

    def _save_chart(self, fig: plt.Figure, currency_pair: str, timeframe: str) -> str:
        """チャート保存"""
        try:
            # 通貨ペア別ディレクトリ作成
            pair_dir = os.path.join(self.chart_dir, currency_pair.replace("/", ""))
            if not os.path.exists(pair_dir):
                os.makedirs(pair_dir)

            # ファイル名生成
            timestamp = datetime.now(self.jst).strftime("%Y%m%d_%H%M%S")
            filename = f"{currency_pair.replace('/', '')}_{timeframe}_{timestamp}.png"
            file_path = os.path.join(pair_dir, filename)

            # チャート保存（設定サイズで保存）
            fig.savefig(
                file_path,
                dpi=self.chart_dpi,
                facecolor=self.colors["background"],
                edgecolor="none",
            )

            self.console.print(f"✅ チャート保存完了: {file_path}")
            return file_path

        except Exception as e:
            logger.error(f"Chart save error: {str(e)}")
            return ""

    def cleanup_old_charts(self, currency_pair: str, days_to_keep: int = 7):
        """古いチャートファイルの削除"""
        try:
            pair_dir = os.path.join(self.chart_dir, currency_pair.replace("/", ""))
            if not os.path.exists(pair_dir):
                return

            cutoff_time = datetime.now(self.jst).timestamp() - (
                days_to_keep * 24 * 3600
            )

            for filename in os.listdir(pair_dir):
                file_path = os.path.join(pair_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        logger.info(f"Removed old chart: {file_path}")

        except Exception as e:
            logger.error(f"Chart cleanup error: {str(e)}")
