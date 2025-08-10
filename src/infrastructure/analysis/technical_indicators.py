"""
Technical Indicators for Real Trading Analysis
実トレード用テクニカル指標分析システム

設計書参照:
- trade_chart_settings_2025.md

機能:
- RSI (期間14, レベル70/50/30)
- MACD (12,26,9)
- ボリンジャーバンド (20,2)
- マルチタイムフレーム分析
"""

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytz
import ta
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# プロジェクトパスを追加
sys.path.append("/app")

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TechnicalIndicatorsAnalyzer:
    """実トレード用テクニカル指標アナライザー"""

    def __init__(self):
        self.console = Console()
        self.jst = pytz.timezone("Asia/Tokyo")

        # 設定値（trade_chart_settings_2025.mdに基づく）
        self.rsi_period = 14
        self.rsi_levels = {"overbought": 70, "neutral": 50, "oversold": 30}

        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        self.bb_period = 20
        self.bb_std = 2

        logger.info("Initialized Technical Indicators Analyzer")

    def calculate_rsi(
        self, data: pd.DataFrame, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        RSI計算 (期間14, レベル70/50/30)

        Args:
            data: OHLCV データ
            timeframe: 時間軸 (D1, H4, H1, M5)

        Returns:
            Dict: RSI値と分析結果
        """
        try:
            # データ型の詳細ログ
            logger.info(f"RSI calculation - Data type: {type(data)}")
            logger.info(
                f"RSI calculation - Data shape: {getattr(data, 'shape', 'N/A')}"
            )
            logger.info(
                f"RSI calculation - Data columns: {getattr(data, 'columns', 'N/A')}"
            )

            # データがnumpy配列の場合はDataFrameに変換
            if isinstance(data, np.ndarray):
                logger.warning("Data is numpy array, converting to DataFrame")
                return {"error": "データ形式エラー: DataFrameが必要"}

            # データが辞書の場合はDataFrameに変換を試行
            if isinstance(data, dict):
                try:
                    data = pd.DataFrame(data)
                except Exception as e:
                    logger.error(f"Failed to convert dict to DataFrame: {str(e)}")
                    return {"error": "データ変換エラー"}

            if len(data) < self.rsi_period:
                logger.warning(
                    f"Insufficient data for RSI calculation: {len(data)} < {self.rsi_period}"
                )
                return {"error": "データ不足"}

            # Close列が存在するかチェック
            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            close = data["Close"]
            rsi = ta.momentum.RSIIndicator(close, window=self.rsi_period).rsi()

            current_rsi = rsi.iloc[-1] if not np.isnan(rsi.iloc[-1]) else None
            previous_rsi = (
                rsi.iloc[-2] if len(rsi) > 1 and not np.isnan(rsi.iloc[-2]) else None
            )

            # RSI状態判定
            rsi_state = self._classify_rsi_state(current_rsi)

            # シグナル判定
            signal = self._analyze_rsi_signal(current_rsi, previous_rsi, timeframe)

            # ダイバージェンス検出（簡易版）
            divergence = self._detect_rsi_divergence(data, rsi, periods=5)

            result = {
                "indicator": "RSI",
                "timeframe": timeframe,
                "period": self.rsi_period,
                "current_value": round(current_rsi, 2) if current_rsi else None,
                "previous_value": round(previous_rsi, 2) if previous_rsi else None,
                "state": rsi_state,
                "signal": signal,
                "divergence": divergence,
                "levels": self.rsi_levels,
                "timestamp": datetime.now(self.jst).isoformat(),
                "data_points": len(data),
            }

            logger.info(
                f"RSI calculated for {timeframe}: {current_rsi:.2f} ({rsi_state})"
            )
            return result

        except Exception as e:
            logger.error(f"RSI calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_macd(
        self, data: pd.DataFrame, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        MACD計算 (12,26,9)

        Args:
            data: OHLCV データ
            timeframe: 時間軸

        Returns:
            Dict: MACD値と分析結果
        """
        try:
            # データがnumpy配列の場合はDataFrameに変換
            if isinstance(data, np.ndarray):
                logger.warning("Data is numpy array, converting to DataFrame")
                return {"error": "データ形式エラー: DataFrameが必要"}

            # データが辞書の場合はDataFrameに変換を試行
            if isinstance(data, dict):
                try:
                    data = pd.DataFrame(data)
                except Exception as e:
                    logger.error(f"Failed to convert dict to DataFrame: {str(e)}")
                    return {"error": "データ変換エラー"}

            required_periods = max(self.macd_slow, self.macd_signal) + 10
            if len(data) < required_periods:
                logger.warning(
                    f"Insufficient data for MACD calculation: {len(data)} < {required_periods}"
                )
                return {"error": "データ不足"}

            # Close列が存在するかチェック
            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            close = data["Close"]
            macd_indicator = ta.trend.MACD(
                close,
                window_fast=self.macd_fast,
                window_slow=self.macd_slow,
                window_sign=self.macd_signal,
            )
            macd_line = macd_indicator.macd()
            signal_line = macd_indicator.macd_signal()
            histogram = macd_indicator.macd_diff()

            current_macd = (
                macd_line.iloc[-1] if not np.isnan(macd_line.iloc[-1]) else None
            )
            current_signal = (
                signal_line.iloc[-1] if not np.isnan(signal_line.iloc[-1]) else None
            )
            current_histogram = (
                histogram.iloc[-1] if not np.isnan(histogram.iloc[-1]) else None
            )

            previous_macd = (
                macd_line.iloc[-2]
                if len(macd_line) > 1 and not np.isnan(macd_line.iloc[-2])
                else None
            )
            previous_signal = (
                signal_line.iloc[-2]
                if len(signal_line) > 1 and not np.isnan(signal_line.iloc[-2])
                else None
            )

            # クロス判定
            cross_signal = self._analyze_macd_cross(
                current_macd, current_signal, previous_macd, previous_signal
            )

            # ゼロライン位置判定
            zero_line_position = (
                "above"
                if current_macd > 0
                else "below"
                if current_macd < 0
                else "neutral"
            )

            result = {
                "indicator": "MACD",
                "timeframe": timeframe,
                "parameters": f"{self.macd_fast},{self.macd_slow},{self.macd_signal}",
                "macd_line": round(current_macd, 6) if current_macd else None,
                "signal_line": round(current_signal, 6) if current_signal else None,
                "histogram": round(current_histogram, 6) if current_histogram else None,
                "cross_signal": cross_signal,
                "zero_line_position": zero_line_position,
                "timestamp": datetime.now(self.jst).isoformat(),
                "data_points": len(data),
            }

            logger.info(f"MACD calculated for {timeframe}: {cross_signal}")
            return result

        except Exception as e:
            logger.error(f"MACD calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_bollinger_bands(
        self, data: pd.DataFrame, timeframe: str = "H4"
    ) -> Dict[str, Any]:
        """
        ボリンジャーバンド計算 (期間20, 偏差2)

        Args:
            data: OHLCV データ
            timeframe: 時間軸

        Returns:
            Dict: ボリンジャーバンド値と分析結果
        """
        try:
            # データがnumpy配列の場合はDataFrameに変換
            if isinstance(data, np.ndarray):
                logger.warning("Data is numpy array, converting to DataFrame")
                return {"error": "データ形式エラー: DataFrameが必要"}

            # データが辞書の場合はDataFrameに変換を試行
            if isinstance(data, dict):
                try:
                    data = pd.DataFrame(data)
                except Exception as e:
                    logger.error(f"Failed to convert dict to DataFrame: {str(e)}")
                    return {"error": "データ変換エラー"}

            if len(data) < self.bb_period + 5:
                logger.warning(
                    f"Insufficient data for Bollinger Bands: {len(data)} < {self.bb_period + 5}"
                )
                return {"error": "データ不足"}

            # Close列が存在するかチェック
            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            close = data["Close"]
            bb_indicator = ta.volatility.BollingerBands(
                close,
                window=self.bb_period,
                window_dev=self.bb_std,
            )
            upper = bb_indicator.bollinger_hband()
            middle = bb_indicator.bollinger_mavg()
            lower = bb_indicator.bollinger_lband()

            current_close = close.iloc[-1]
            current_upper = upper.iloc[-1] if not np.isnan(upper.iloc[-1]) else None
            current_middle = middle.iloc[-1] if not np.isnan(middle.iloc[-1]) else None
            current_lower = lower.iloc[-1] if not np.isnan(lower.iloc[-1]) else None

            # バンド位置分析
            band_position = self._analyze_bb_position(
                current_close, current_upper, current_middle, current_lower
            )

            # バンドウォーク検出
            band_walk = self._detect_band_walk(close, upper, lower, periods=5)

            # バンド幅分析
            band_width = (
                ((current_upper - current_lower) / current_middle) * 100
                if current_middle
                else None
            )

            result = {
                "indicator": "Bollinger Bands",
                "timeframe": timeframe,
                "parameters": f"BB({self.bb_period},{self.bb_std})",
                "current_price": round(current_close, 4),
                "upper_band": round(current_upper, 4) if current_upper else None,
                "middle_band": round(current_middle, 4) if current_middle else None,
                "lower_band": round(current_lower, 4) if current_lower else None,
                "band_position": band_position,
                "band_walk": band_walk,
                "band_width_percent": round(band_width, 2) if band_width else None,
                "timestamp": datetime.now(self.jst).isoformat(),
                "data_points": len(data),
            }

            logger.info(f"Bollinger Bands calculated for {timeframe}: {band_position}")
            return result

        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {str(e)}")
            return {"error": str(e)}

    def multi_timeframe_analysis(
        self, data_dict: Dict[str, pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        マルチタイムフレーム分析

        Args:
            data_dict: {"D1": df, "H4": df, "H1": df, "M5": df}

        Returns:
            Dict: 総合分析結果
        """
        try:
            analysis_result = {
                "analysis_type": "Multi-Timeframe Technical Analysis",
                "timestamp": datetime.now(self.jst).isoformat(),
                "timeframes": {},
            }

            # D1: RSI + MACD (大局判断) - MACDに必要なデータが不足の場合は長期データを取得
            if "D1" in data_dict:
                d1_analysis = {}
                d1_rsi = self.calculate_rsi(data_dict["D1"], "D1")

                # MACD計算に必要なデータ量チェック
                required_periods = max(self.macd_slow, self.macd_signal) + 10
                if len(data_dict["D1"]) < required_periods:
                    logger.warning(
                        f"D1 MACD: データ不足 {len(data_dict['D1'])} < {required_periods}. 長期データ取得を推奨"
                    )
                    d1_macd = {
                        "indicator": "MACD",
                        "timeframe": "D1",
                        "error": f"データ不足 ({len(data_dict['D1'])}件 < {required_periods}件必要)",
                        "recommendation": "3ヶ月以上の履歴データで再分析してください",
                    }
                else:
                    d1_macd = self.calculate_macd(data_dict["D1"], "D1")

                d1_analysis["RSI"] = d1_rsi
                d1_analysis["MACD"] = d1_macd
                d1_analysis["purpose"] = "大局判断"
                analysis_result["timeframes"]["D1"] = d1_analysis

            # H4: RSI + ボリンジャーバンド (戦術)
            if "H4" in data_dict:
                h4_analysis = {}
                h4_rsi = self.calculate_rsi(data_dict["H4"], "H4")
                h4_bb = self.calculate_bollinger_bands(data_dict["H4"], "H4")
                h4_analysis["RSI"] = h4_rsi
                h4_analysis["BollingerBands"] = h4_bb
                h4_analysis["purpose"] = "戦術判断"
                analysis_result["timeframes"]["H4"] = h4_analysis

            # H1: RSI + ボリンジャーバンド (ゾーン)
            if "H1" in data_dict:
                h1_analysis = {}
                h1_rsi = self.calculate_rsi(data_dict["H1"], "H1")
                h1_bb = self.calculate_bollinger_bands(data_dict["H1"], "H1")
                h1_analysis["RSI"] = h1_rsi
                h1_analysis["BollingerBands"] = h1_bb
                h1_analysis["purpose"] = "ゾーン決定"
                analysis_result["timeframes"]["H1"] = h1_analysis

            # M5: RSI (タイミング)
            if "M5" in data_dict:
                m5_analysis = {}
                m5_rsi = self.calculate_rsi(data_dict["M5"], "M5")
                m5_analysis["RSI"] = m5_rsi
                m5_analysis["purpose"] = "タイミング"
                analysis_result["timeframes"]["M5"] = m5_analysis

            # 総合判断
            overall_signal = self._generate_overall_signal(analysis_result)
            analysis_result["overall_signal"] = overall_signal

            logger.info("Multi-timeframe analysis completed")
            return analysis_result

        except Exception as e:
            logger.error(f"Multi-timeframe analysis error: {str(e)}")
            return {"error": str(e)}

    def _classify_rsi_state(self, rsi_value: float) -> str:
        """RSI状態分類"""
        if rsi_value is None:
            return "unknown"
        elif rsi_value >= self.rsi_levels["overbought"]:
            return "overbought"
        elif rsi_value <= self.rsi_levels["oversold"]:
            return "oversold"
        else:
            return "neutral"

    def _analyze_rsi_signal(
        self, current: float, previous: float, timeframe: str
    ) -> str:
        """RSIシグナル分析"""
        if current is None or previous is None:
            return "no_signal"

        # レベルクロス判定
        if (
            previous < self.rsi_levels["oversold"]
            and current >= self.rsi_levels["oversold"]
        ):
            return "buy_signal"
        elif (
            previous > self.rsi_levels["overbought"]
            and current <= self.rsi_levels["overbought"]
        ):
            return "sell_signal"

        # M5での特別ルール
        if timeframe == "M5":
            if current >= self.rsi_levels["overbought"]:
                return "sell_timing"
            elif current <= self.rsi_levels["oversold"]:
                return "buy_timing"

        return "neutral"

    def _detect_rsi_divergence(
        self, data: pd.DataFrame, rsi: np.ndarray, periods: int = 5
    ) -> str:
        """RSIダイバージェンス検出（簡易版）"""
        try:
            # データ形式チェック
            if isinstance(data, np.ndarray):
                logger.warning("Data is numpy array in _detect_rsi_divergence")
                return "data_format_error"

            if not isinstance(data, pd.DataFrame):
                logger.warning("Data is not DataFrame in _detect_rsi_divergence")
                return "data_format_error"

            if len(data) < periods * 2:
                return "insufficient_data"

            # High列が存在するかチェック
            if "High" not in data.columns:
                logger.warning("High column not found in data for divergence detection")
                return "missing_high_column"

            recent_highs = data["High"].rolling(periods).max().iloc[-periods:]
            recent_rsi = rsi[-periods:]

            # 価格とRSIの方向性比較（簡易）
            price_trend = recent_highs.iloc[-1] - recent_highs.iloc[0]
            rsi_trend = recent_rsi.iloc[-1] - recent_rsi.iloc[0]

            if price_trend > 0 and rsi_trend < 0:
                return "bearish_divergence"
            elif price_trend < 0 and rsi_trend > 0:
                return "bullish_divergence"
            else:
                return "no_divergence"

        except Exception as e:
            logger.error(f"Error in _detect_rsi_divergence: {str(e)}")
            return "detection_error"

    def _analyze_macd_cross(
        self, macd: float, signal: float, prev_macd: float, prev_signal: float
    ) -> str:
        """MACDクロス分析"""
        if any(x is None for x in [macd, signal, prev_macd, prev_signal]):
            return "no_signal"

        # ゴールデンクロス
        if prev_macd <= prev_signal and macd > signal:
            return "golden_cross"
        # デッドクロス
        elif prev_macd >= prev_signal and macd < signal:
            return "dead_cross"
        else:
            return "no_cross"

    def _analyze_bb_position(
        self, price: float, upper: float, middle: float, lower: float
    ) -> str:
        """ボリンジャーバンド位置分析"""
        if any(x is None for x in [upper, middle, lower]):
            return "unknown"

        if price >= upper:
            return "above_upper_band"
        elif price <= lower:
            return "below_lower_band"
        elif price > middle:
            return "above_middle"
        else:
            return "below_middle"

    def _detect_band_walk(
        self, close: np.ndarray, upper: np.ndarray, lower: np.ndarray, periods: int = 5
    ) -> str:
        """バンドウォーク検出"""
        try:
            recent_close = close[-periods:]
            recent_upper = upper[-periods:]
            recent_lower = lower[-periods:]

            # 上バンドウォーク
            upper_touches = sum(recent_close >= recent_upper * 0.99)  # 99%以上
            if upper_touches >= periods * 0.6:  # 60%以上
                return "upper_band_walk"

            # 下バンドウォーク
            lower_touches = sum(recent_close <= recent_lower * 1.01)  # 101%以下
            if lower_touches >= periods * 0.6:
                return "lower_band_walk"

            return "no_band_walk"

        except Exception:
            return "detection_error"

    def _generate_overall_signal(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """総合シグナル生成"""
        signals = []

        # 各時間軸からシグナル抽出
        for tf, data in analysis.get("timeframes", {}).items():
            if "RSI" in data and "signal" in data["RSI"]:
                rsi_signal = data["RSI"]["signal"]
                if rsi_signal not in ["neutral", "no_signal"]:
                    signals.append(f"{tf}_RSI_{rsi_signal}")

            if "MACD" in data and "cross_signal" in data["MACD"]:
                macd_signal = data["MACD"]["cross_signal"]
                if macd_signal not in ["no_cross", "no_signal"]:
                    signals.append(f"{tf}_MACD_{macd_signal}")

        # 総合判断ロジック（簡易版）
        buy_signals = len([s for s in signals if "buy" in s or "golden" in s])
        sell_signals = len([s for s in signals if "sell" in s or "dead" in s])

        if buy_signals > sell_signals:
            overall = "bullish"
        elif sell_signals > buy_signals:
            overall = "bearish"
        else:
            overall = "neutral"

        return {
            "direction": overall,
            "signal_count": len(signals),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "confidence": min(abs(buy_signals - sell_signals) * 20, 100),
        }

    def display_analysis_table(
        self, analysis: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> None:
        """分析結果をテーブル表示"""
        self.console.print(f"\n📊 Technical Analysis Report - {currency_pair}")

        for timeframe, data in analysis.get("timeframes", {}).items():
            table = Table(title=f"⏰ {timeframe} - {data.get('purpose', '')}")
            table.add_column("指標", style="cyan")
            table.add_column("値", style="green")
            table.add_column("状態", style="yellow")
            table.add_column("シグナル", style="red")

            if "RSI" in data:
                rsi = data["RSI"]
                table.add_row(
                    "RSI(14)",
                    str(rsi.get("current_value", "N/A")),
                    rsi.get("state", "N/A"),
                    rsi.get("signal", "N/A"),
                )

            if "MACD" in data:
                macd = data["MACD"]
                table.add_row(
                    "MACD(12,26,9)",
                    f"{macd.get('macd_line', 'N/A')}",
                    macd.get("zero_line_position", "N/A"),
                    macd.get("cross_signal", "N/A"),
                )

            if "BollingerBands" in data:
                bb = data["BollingerBands"]
                table.add_row(
                    "BB(20,2)",
                    f"{bb.get('current_price', 'N/A')}",
                    bb.get("band_position", "N/A"),
                    bb.get("band_walk", "N/A"),
                )

            self.console.print(table)

        # 総合シグナル表示
        overall = analysis.get("overall_signal", {})
        if overall:
            signal_panel = Panel.fit(
                f"方向: {overall.get('direction', 'N/A')}\n"
                f"信頼度: {overall.get('confidence', 0)}%\n"
                f"シグナル数: {overall.get('signal_count', 0)}",
                title="🎯 総合判断",
            )
            self.console.print(signal_panel)
