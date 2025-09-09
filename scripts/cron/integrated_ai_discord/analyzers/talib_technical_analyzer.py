#!/usr/bin/env python3
"""
TA-Lib Technical Indicators Analyzer
TA-Libを使用したテクニカル指標分析システム（モジュール化版）

既存の設定をそのままに、TA-Libライブラリを使用して高精度計算を実現
"""

import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import pytz
import talib
from rich.console import Console

# プロジェクトパスを追加
sys.path.append("/app")

from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TALibTechnicalIndicatorsAnalyzer:
    """TA-Libを使用したテクニカル指標アナライザー（既存設定互換）"""

    def __init__(self):
        self.console = Console()
        self.jst = pytz.timezone("Asia/Tokyo")

        # 既存の設定値をそのまま使用（trade_chart_settings_2025.mdに基づく）
        # RSI設定（複数期間対応）
        self.rsi_period = 14  # デフォルト期間
        self.rsi_long = 70  # 長期RSI
        self.rsi_medium = 50  # 中期RSI
        self.rsi_short = 30  # 短期RSI
        self.rsi_levels = {"overbought": 70, "neutral": 50, "oversold": 30}

        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9

        self.bb_period = 20
        self.bb_std = 2

        # 移動平均線設定
        self.ma_short = 20  # 短期移動平均
        self.ma_medium = 50  # 中期移動平均
        self.ma_long = 200  # 長期移動平均

        logger.info("Initialized TALib Technical Indicators Analyzer")

    def calculate_rsi(
        self, data: pd.DataFrame, timeframe: str = "D1", period: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        RSI計算 (TA-Lib使用、複数期間対応)

        Args:
            data: OHLCV データ
            timeframe: 時間軸 (D1, H4, H1, M5)
            period: 指定期間（Noneの場合はデフォルト値を使用）

        Returns:
            Dict: RSI値と分析結果
        """
        try:
            # 期間の決定（既存設定をそのまま使用）
            if period is not None:
                rsi_period = period
            else:
                rsi_period = self.rsi_period

            # データ型の詳細ログ
            logger.info(f"TALib RSI calculation - Data type: {type(data)}")
            logger.info(
                f"TALib RSI calculation - Data shape: {getattr(data, 'shape', 'N/A')}"
            )
            logger.info(
                f"TALib RSI calculation - Data columns: {getattr(data, 'columns', 'N/A')}"
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

            if len(data) < rsi_period:
                logger.warning(
                    f"Insufficient data for RSI calculation: {len(data)} < {rsi_period}"
                )
                return {"error": "データ不足"}

            # Close列が存在するかチェック
            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            # TA-Libを使用してRSI計算
            close = data["Close"].values.astype(np.float64)
            rsi_values = talib.RSI(close, timeperiod=rsi_period)

            current_rsi = rsi_values[-1] if not np.isnan(rsi_values[-1]) else None
            previous_rsi = (
                rsi_values[-2]
                if len(rsi_values) > 1 and not np.isnan(rsi_values[-2])
                else None
            )

            # RSI状態判定（既存ロジックをそのまま使用）
            rsi_state = self._classify_rsi_state(current_rsi)

            # シグナル判定（既存ロジックをそのまま使用）
            signal = self._analyze_rsi_signal(current_rsi, previous_rsi, timeframe)

            # ダイバージェンス検出（簡易版）
            divergence = self._detect_rsi_divergence(data, rsi_values, periods=5)

            result = {
                "indicator": "RSI",
                "timeframe": timeframe,
                "period": rsi_period,
                "current_value": round(current_rsi, 2) if current_rsi else None,
                "previous_value": round(previous_rsi, 2) if previous_rsi else None,
                "state": rsi_state,
                "signal": signal,
                "divergence": divergence,
                "calculation_time": datetime.now(self.jst),
                "library": "TALib",  # 使用ライブラリを明記
            }

            logger.info(
                f"TALib RSI calculated for {timeframe}: {current_rsi:.2f} ({rsi_state})"
            )
            return result

        except Exception as e:
            logger.error(f"TALib RSI calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_macd(
        self, data: pd.DataFrame, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        MACD計算 (TA-Lib使用)

        Args:
            data: OHLCV データ
            timeframe: 時間軸

        Returns:
            Dict: MACD値と分析結果
        """
        try:
            if len(data) < 40:  # MACD計算に必要な最小データ数
                logger.warning(f"Insufficient data for MACD: {len(data)} < 40")
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            # TA-Libを使用してMACD計算
            close = data["Close"].values.astype(np.float64)
            macd_line, signal_line, histogram = talib.MACD(
                close,
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal,
            )

            current_macd = macd_line[-1] if not np.isnan(macd_line[-1]) else None
            current_signal = signal_line[-1] if not np.isnan(signal_line[-1]) else None
            current_histogram = histogram[-1] if not np.isnan(histogram[-1]) else None

            # MACD状態判定
            macd_state = self._classify_macd_state(
                current_macd, current_signal, current_histogram
            )

            # シグナル判定
            signal = self._analyze_macd_signal(
                macd_line, signal_line, histogram, timeframe
            )

            result = {
                "indicator": "MACD",
                "timeframe": timeframe,
                "macd_line": round(current_macd, 4) if current_macd else None,
                "signal_line": round(current_signal, 4) if current_signal else None,
                "histogram": round(current_histogram, 4) if current_histogram else None,
                "state": macd_state,
                "signal": signal,
                "calculation_time": datetime.now(self.jst),
                "library": "TALib",  # 使用ライブラリを明記
            }

            logger.info(
                f"TALib MACD calculated for {timeframe}: "
                f"MACD={current_macd:.4f}, Signal={current_signal:.4f}"
            )
            return result

        except Exception as e:
            logger.error(f"TALib MACD calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_bollinger_bands(
        self, data: pd.DataFrame, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        ボリンジャーバンド計算 (TA-Lib使用)

        Args:
            data: OHLCV データ
            timeframe: 時間軸

        Returns:
            Dict: ボリンジャーバンド値と分析結果
        """
        try:
            if len(data) < self.bb_period:
                logger.warning(
                    f"Insufficient data for Bollinger Bands: {len(data)} < {self.bb_period}"
                )
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            # TA-Libを使用してボリンジャーバンド計算
            close = data["Close"].values.astype(np.float64)
            upper_band, middle_band, lower_band = talib.BBANDS(
                close,
                timeperiod=self.bb_period,
                nbdevup=self.bb_std,
                nbdevdn=self.bb_std,
                matype=0,  # SMA
            )

            current_upper = upper_band[-1] if not np.isnan(upper_band[-1]) else None
            current_middle = middle_band[-1] if not np.isnan(middle_band[-1]) else None
            current_lower = lower_band[-1] if not np.isnan(lower_band[-1]) else None
            current_close = close[-1]

            # バンド位置判定
            band_position = self._classify_bb_position(
                current_close, current_upper, current_middle, current_lower
            )

            # バンド幅計算
            band_width = (
                (current_upper - current_lower) / current_middle * 100
                if current_upper and current_lower and current_middle
                else None
            )

            result = {
                "indicator": "Bollinger Bands",
                "timeframe": timeframe,
                "upper_band": round(current_upper, 4) if current_upper else None,
                "middle_band": round(current_middle, 4) if current_middle else None,
                "lower_band": round(current_lower, 4) if current_lower else None,
                "current_price": round(current_close, 4),
                "band_position": band_position,
                "band_width": round(band_width, 2) if band_width else None,
                "calculation_time": datetime.now(self.jst),
                "library": "TALib",  # 使用ライブラリを明記
            }

            logger.info(
                f"TALib Bollinger Bands calculated for {timeframe}: "
                f"Upper={current_upper:.4f}, Middle={current_middle:.4f}, "
                f"Lower={current_lower:.4f}"
            )
            return result

        except Exception as e:
            logger.error(f"TALib Bollinger Bands calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_moving_averages(
        self,
        data: pd.DataFrame,
        timeframe: str = "D1",
        ma_type: str = "SMA",
        period: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        移動平均線計算 (TA-Lib使用)

        Args:
            data: OHLCV データ
            timeframe: 時間軸
            ma_type: 移動平均タイプ ("SMA" or "EMA")
            period: 期間（Noneの場合はデフォルト値を使用）

        Returns:
            Dict: 移動平均値と分析結果
        """
        try:
            # 期間の決定
            if period is not None:
                ma_period = period
            else:
                # 時間軸に応じてデフォルト期間を設定
                if timeframe == "D1":
                    ma_period = self.ma_long  # 200
                elif timeframe == "H4":
                    ma_period = self.ma_medium  # 50
                else:
                    ma_period = self.ma_short  # 20

            if len(data) < ma_period:
                logger.warning(
                    f"Insufficient data for MA calculation: {len(data)} < {ma_period}"
                )
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found in data")
                return {"error": "Close列が見つかりません"}

            # TA-Libを使用して移動平均計算
            close = data["Close"].values.astype(np.float64)

            if ma_type.upper() == "SMA":
                ma_values = talib.SMA(close, timeperiod=ma_period)
            elif ma_type.upper() == "EMA":
                ma_values = talib.EMA(close, timeperiod=ma_period)
            else:
                logger.error(f"Unsupported MA type: {ma_type}")
                return {"error": f"サポートされていない移動平均タイプ: {ma_type}"}

            current_ma = ma_values[-1] if not np.isnan(ma_values[-1]) else None
            current_close = close[-1]

            # 移動平均位置判定
            ma_position = self._classify_ma_position(current_close, current_ma)

            # 移動平均の傾き計算
            ma_slope = self._calculate_ma_slope(ma_values, periods=5)

            result = {
                "indicator": f"{ma_type}",
                "timeframe": timeframe,
                "period": ma_period,
                "ma_type": ma_type,
                "current_ma": round(current_ma, 4) if current_ma else None,
                "current_price": round(current_close, 4),
                "position": ma_position,
                "slope": ma_slope,
                "calculation_time": datetime.now(self.jst),
                "library": "TALib",  # 使用ライブラリを明記
            }

            logger.info(
                f"TALib {ma_type} calculated for {timeframe}: "
                f"MA={current_ma:.4f}, Price={current_close:.4f}"
            )
            return result

        except Exception as e:
            logger.error(f"TALib MA calculation error: {str(e)}")
            return {"error": str(e)}

    # 既存のヘルパーメソッド（そのまま使用）
    def _classify_rsi_state(self, rsi_value: float) -> str:
        """RSI状態を分類"""
        if rsi_value is None:
            return "unknown"
        elif rsi_value >= self.rsi_levels["overbought"]:
            return "overbought"
        elif rsi_value <= self.rsi_levels["oversold"]:
            return "oversold"
        else:
            return "neutral"

    def _analyze_rsi_signal(
        self, current_rsi: float, previous_rsi: float, timeframe: str
    ) -> str:
        """RSIシグナル分析"""
        if current_rsi is None or previous_rsi is None:
            return "neutral"

        # RSIの傾きに基づくシグナル
        if current_rsi > previous_rsi:
            if current_rsi < 30:
                return "oversold_recovery"
            elif current_rsi > 70:
                return "overbought_continuation"
            else:
                return "bullish"
        elif current_rsi < previous_rsi:
            if current_rsi > 70:
                return "overbought_reversal"
            elif current_rsi < 30:
                return "oversold_continuation"
            else:
                return "bearish"
        else:
            return "neutral"

    def _detect_rsi_divergence(
        self, data: pd.DataFrame, rsi_values: np.ndarray, periods: int = 5
    ) -> Dict[str, Any]:
        """RSIダイバージェンス検出（簡易版）"""
        try:
            if len(data) < periods * 2 or len(rsi_values) < periods * 2:
                return {"detected": False, "type": "insufficient_data"}

            # 価格とRSIの最新期間の傾向を比較
            recent_prices = data["Close"].tail(periods).values
            recent_rsi = rsi_values[-periods:]

            price_trend = "up" if recent_prices[-1] > recent_prices[0] else "down"
            rsi_trend = "up" if recent_rsi[-1] > recent_rsi[0] else "down"

            if price_trend != rsi_trend:
                return {
                    "detected": True,
                    "type": "divergence",
                    "price_trend": price_trend,
                    "rsi_trend": rsi_trend,
                }
            else:
                return {"detected": False, "type": "no_divergence"}

        except Exception as e:
            logger.error(f"RSI divergence detection error: {str(e)}")
            return {"detected": False, "type": "error"}

    def _classify_macd_state(self, macd: float, signal: float, histogram: float) -> str:
        """MACD状態を分類"""
        if macd is None or signal is None:
            return "unknown"

        if macd > signal:
            if histogram > 0:
                return "bullish_strong"
            else:
                return "bullish_weak"
        else:
            if histogram < 0:
                return "bearish_strong"
            else:
                return "bearish_weak"

    def _analyze_macd_signal(
        self,
        macd_line: np.ndarray,
        signal_line: np.ndarray,
        histogram: np.ndarray,
        timeframe: str,
    ) -> str:
        """MACDシグナル分析"""
        if len(macd_line) < 2 or len(signal_line) < 2:
            return "neutral"

        # ゴールデンクロス/デッドクロス検出
        current_macd = macd_line[-1]
        current_signal = signal_line[-1]
        previous_macd = macd_line[-2]
        previous_signal = signal_line[-2]

        if current_macd > current_signal and previous_macd <= previous_signal:
            return "golden_cross"
        elif current_macd < current_signal and previous_macd >= previous_signal:
            return "dead_cross"
        elif current_macd > current_signal:
            return "bullish"
        else:
            return "bearish"

    def _classify_bb_position(
        self, price: float, upper: float, middle: float, lower: float
    ) -> str:
        """ボリンジャーバンド位置を分類"""
        if price is None or upper is None or middle is None or lower is None:
            return "unknown"

        if price > upper:
            return "above_upper"
        elif price < lower:
            return "below_lower"
        elif price > middle:
            return "upper_half"
        else:
            return "lower_half"

    def _classify_ma_position(self, price: float, ma: float) -> str:
        """移動平均位置を分類"""
        if price is None or ma is None:
            return "unknown"

        if price > ma:
            return "above_ma"
        else:
            return "below_ma"

    def _calculate_ma_slope(self, ma_values: np.ndarray, periods: int = 5) -> str:
        """移動平均の傾きを計算"""
        if len(ma_values) < periods:
            return "unknown"

        recent_ma = ma_values[-periods:]
        if recent_ma[-1] > recent_ma[0]:
            return "upward"
        elif recent_ma[-1] < recent_ma[0]:
            return "downward"
        else:
            return "flat"

    def calculate_atr(
        self, data: pd.DataFrame, timeframe: str = "D1", period: int = 14
    ) -> Dict[str, Any]:
        """
        ATR（Average True Range）計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            timeframe: 時間軸
            period: ATR期間

        Returns:
            Dict: ATR値と分析結果
        """
        try:
            if len(data) < period + 1:
                logger.warning(f"Insufficient data for ATR: {len(data)} < {period + 1}")
                return {"error": "データ不足"}

            if not all(col in data.columns for col in ["High", "Low", "Close"]):
                logger.error("High, Low, Close columns not found")
                return {"error": "High, Low, Close列が見つかりません"}

            high_prices = data["High"].values.astype(np.float64)
            low_prices = data["Low"].values.astype(np.float64)
            close_prices = data["Close"].values.astype(np.float64)

            # TA-LibでATR計算
            atr_values = talib.ATR(
                high_prices, low_prices, close_prices, timeperiod=period
            )

            # 最新値を取得
            current_atr = atr_values[-1] if not np.isnan(atr_values[-1]) else None
            previous_atr = (
                atr_values[-2]
                if len(atr_values) > 1 and not np.isnan(atr_values[-2])
                else None
            )

            if current_atr is None:
                return {"error": "ATR計算失敗"}

            # ATR状態の判定
            atr_state = self._analyze_atr_state(current_atr, previous_atr)

            result = {
                "current_value": round(current_atr, 4),
                "previous_value": round(previous_atr, 4) if previous_atr else None,
                "state": atr_state,
                "timeframe": timeframe,
                "period": period,
            }

            logger.info(f"ATR calculation successful: {current_atr:.4f}")
            return result

        except Exception as e:
            logger.error(f"ATR calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_adx(
        self, data: pd.DataFrame, timeframe: str = "D1", period: int = 14
    ) -> Dict[str, Any]:
        """
        ADX（Average Directional Index）計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            timeframe: 時間軸
            period: ADX期間

        Returns:
            Dict: ADX値と分析結果
        """
        try:
            if len(data) < period + 1:
                logger.warning(f"Insufficient data for ADX: {len(data)} < {period + 1}")
                return {"error": "データ不足"}

            if not all(col in data.columns for col in ["High", "Low", "Close"]):
                logger.error("High, Low, Close columns not found")
                return {"error": "High, Low, Close列が見つかりません"}

            high_prices = data["High"].values.astype(np.float64)
            low_prices = data["Low"].values.astype(np.float64)
            close_prices = data["Close"].values.astype(np.float64)

            # TA-LibでADX計算
            adx_values = talib.ADX(
                high_prices, low_prices, close_prices, timeperiod=period
            )

            # 最新値を取得
            current_adx = adx_values[-1] if not np.isnan(adx_values[-1]) else None
            previous_adx = (
                adx_values[-2]
                if len(adx_values) > 1 and not np.isnan(adx_values[-2])
                else None
            )

            if current_adx is None:
                return {"error": "ADX計算失敗"}

            # ADX状態の判定
            adx_state = self._analyze_adx_state(current_adx, previous_adx)

            result = {
                "current_value": round(current_adx, 1),
                "previous_value": round(previous_adx, 1) if previous_adx else None,
                "state": adx_state,
                "timeframe": timeframe,
                "period": period,
            }

            logger.info(f"ADX calculation successful: {current_adx:.1f}")
            return result

        except Exception as e:
            logger.error(f"ADX calculation error: {str(e)}")
            return {"error": str(e)}

    def _analyze_atr_state(
        self, current_atr: float, previous_atr: Optional[float]
    ) -> str:
        """ATR状態を分析"""
        if previous_atr is None:
            return "neutral"

        if current_atr > previous_atr * 1.1:
            return "expanding"
        elif current_atr < previous_atr * 0.9:
            return "contracting"
        else:
            return "stable"

    def _analyze_adx_state(
        self, current_adx: float, previous_adx: Optional[float]
    ) -> str:
        """ADX状態を分析"""
        if current_adx >= 25:
            return "strong_trend"
        elif current_adx >= 20:
            return "moderate_trend"
        else:
            return "weak_trend"
