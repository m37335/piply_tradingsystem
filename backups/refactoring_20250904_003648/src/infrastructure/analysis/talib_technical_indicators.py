"""
TA-Lib Technical Indicators Calculator
TA-Libを使用したテクニカル指標計算システム

機能:
- RSI (期間14, レベル70/50/30)
- MACD (12,26,9)
- ボリンジャーバンド (20,2)
- 移動平均線 (SMA/EMA)
- ストキャスティクス
- ATR (Average True Range)
- マルチタイムフレーム分析
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import talib

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TALibTechnicalIndicators:
    """TA-Libを使用したテクニカル指標計算クラス"""

    def __init__(self):
        # デフォルトパラメータ設定
        self.default_params = {
            "RSI": {"period": 14},
            "MACD": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
            "BB": {"period": 20, "std_dev": 2},
            "SMA": {"period": 20},
            "EMA": {"period": 20},
            "STOCH": {"fastk_period": 14, "slowk_period": 3, "slowd_period": 3},
            "ATR": {"period": 14},
        }

        # 移動平均線の複数期間設定
        self.ma_periods = {
            "short": 20,
            "medium": 50,
            "long": 200,
        }

        logger.info("Initialized TALib Technical Indicators Calculator")

    def calculate_rsi(
        self, data: pd.DataFrame, period: int = 14, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        RSI計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            period: RSI期間
            timeframe: 時間軸

        Returns:
            Dict: RSI値と分析結果
        """
        try:
            if len(data) < period + 1:
                logger.warning(f"Insufficient data for RSI: {len(data)} < {period + 1}")
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found")
                return {"error": "Close列が見つかりません"}

            close_prices = data["Close"].values.astype(np.float64)
            rsi_values = talib.RSI(close_prices, timeperiod=period)

            # 最新のRSI値を取得
            current_rsi = rsi_values[-1] if not np.isnan(rsi_values[-1]) else None
            previous_rsi = (
                rsi_values[-2]
                if len(rsi_values) > 1 and not np.isnan(rsi_values[-2])
                else None
            )

            if current_rsi is None:
                return {"error": "RSI計算失敗"}

            # RSI状態の判定
            rsi_state = self._analyze_rsi_state(current_rsi)

            # RSIの傾き分析
            rsi_slope = self._analyze_rsi_slope(rsi_values, periods=5)

            result = {
                "current_value": round(current_rsi, 2),
                "previous_value": round(previous_rsi, 2) if previous_rsi else None,
                "state": rsi_state,
                "slope": rsi_slope,
                "period": period,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "rsi_series": rsi_values.tolist()[-20:],  # 最新20件
                    "overbought_level": 70,
                    "oversold_level": 30,
                    "neutral_level": 50,
                },
            }

            logger.info(
                f"RSI calculated for {timeframe}: {current_rsi:.2f} ({rsi_state})"
            )
            return result

        except Exception as e:
            logger.error(f"RSI calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_macd(
        self,
        data: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        timeframe: str = "D1",
    ) -> Dict[str, Any]:
        """
        MACD計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            fast_period: 短期EMA期間
            slow_period: 長期EMA期間
            signal_period: シグナル期間
            timeframe: 時間軸

        Returns:
            Dict: MACD値と分析結果
        """
        try:
            min_periods = max(slow_period, signal_period) + 10
            if len(data) < min_periods:
                logger.warning(
                    f"Insufficient data for MACD: {len(data)} < {min_periods}"
                )
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found")
                return {"error": "Close列が見つかりません"}

            close_prices = data["Close"].values.astype(np.float64)

            # TA-LibでMACD計算
            macd_line, signal_line, histogram = talib.MACD(
                close_prices,
                fastperiod=fast_period,
                slowperiod=slow_period,
                signalperiod=signal_period,
            )

            # 最新値を取得
            current_macd = macd_line[-1] if not np.isnan(macd_line[-1]) else None
            current_signal = signal_line[-1] if not np.isnan(signal_line[-1]) else None
            current_histogram = histogram[-1] if not np.isnan(histogram[-1]) else None

            if current_macd is None:
                return {"error": "MACD計算失敗"}

            # MACD状態の判定
            macd_state = self._analyze_macd_state(
                current_macd, current_signal, current_histogram
            )

            result = {
                "current_value": round(current_macd, 4),
                "signal_line": round(current_signal, 4) if current_signal else None,
                "histogram": round(current_histogram, 4) if current_histogram else None,
                "state": macd_state,
                "fast_period": fast_period,
                "slow_period": slow_period,
                "signal_period": signal_period,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "macd_series": macd_line.tolist()[-20:],
                    "signal_series": signal_line.tolist()[-20:],
                    "histogram_series": histogram.tolist()[-20:],
                },
            }

            logger.info(
                f"MACD calculated for {timeframe}: {current_macd:.4f} ({macd_state})"
            )
            return result

        except Exception as e:
            logger.error(f"MACD calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_bollinger_bands(
        self,
        data: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        timeframe: str = "H4",
    ) -> Dict[str, Any]:
        """
        ボリンジャーバンド計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            period: 移動平均期間
            std_dev: 標準偏差の倍数
            timeframe: 時間軸

        Returns:
            Dict: ボリンジャーバンド値と分析結果
        """
        try:
            if len(data) < period + 1:
                logger.warning(f"Insufficient data for BB: {len(data)} < {period + 1}")
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found")
                return {"error": "Close列が見つかりません"}

            close_prices = data["Close"].values.astype(np.float64)

            # TA-Libでボリンジャーバンド計算
            upper_band, middle_band, lower_band = talib.BBANDS(
                close_prices,
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev,
                matype=0,  # SMA
            )

            # 最新値を取得
            current_price = close_prices[-1]
            current_upper = upper_band[-1] if not np.isnan(upper_band[-1]) else None
            current_middle = middle_band[-1] if not np.isnan(middle_band[-1]) else None
            current_lower = lower_band[-1] if not np.isnan(lower_band[-1]) else None

            if current_middle is None:
                return {"error": "ボリンジャーバンド計算失敗"}

            # ボリンジャーバンド状態の判定
            bb_state = self._analyze_bollinger_bands_state(
                current_price, current_upper, current_middle, current_lower
            )

            result = {
                "current_value": round(current_middle, 4),
                "upper_band": round(current_upper, 4) if current_upper else None,
                "lower_band": round(current_lower, 4) if current_lower else None,
                "state": bb_state,
                "period": period,
                "std_dev": std_dev,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "upper_series": upper_band.tolist()[-20:],
                    "middle_series": middle_band.tolist()[-20:],
                    "lower_series": lower_band.tolist()[-20:],
                    "price_position": (
                        (current_price - current_lower)
                        / (current_upper - current_lower)
                        if current_upper and current_lower
                        else None
                    ),
                },
            }

            logger.info(
                f"Bollinger Bands calculated for {timeframe}: {current_middle:.4f} ({bb_state})"
            )
            return result

        except Exception as e:
            logger.error(f"Bollinger Bands calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_sma(
        self, data: pd.DataFrame, period: int = 20, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        単純移動平均（SMA）計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            period: 移動平均期間
            timeframe: 時間軸

        Returns:
            Dict: SMA値と分析結果
        """
        try:
            if len(data) < period:
                logger.warning(f"Insufficient data for SMA: {len(data)} < {period}")
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found")
                return {"error": "Close列が見つかりません"}

            close_prices = data["Close"].values.astype(np.float64)

            # TA-LibでSMA計算
            sma_values = talib.SMA(close_prices, timeperiod=period)

            # 最新値を取得
            current_sma = sma_values[-1] if not np.isnan(sma_values[-1]) else None
            previous_sma = (
                sma_values[-2]
                if len(sma_values) > 1 and not np.isnan(sma_values[-2])
                else None
            )
            current_price = close_prices[-1]

            if current_sma is None:
                return {"error": "SMA計算失敗"}

            # SMA状態の判定
            sma_state = self._analyze_ma_state(current_price, current_sma, previous_sma)

            result = {
                "current_value": round(current_sma, 4),
                "previous_value": round(previous_sma, 4) if previous_sma else None,
                "state": sma_state,
                "period": period,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "sma_series": sma_values.tolist()[-20:],
                    "price_vs_sma": current_price - current_sma,
                },
            }

            logger.info(
                f"SMA calculated for {timeframe}: {current_sma:.4f} ({sma_state})"
            )
            return result

        except Exception as e:
            logger.error(f"SMA calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_ema(
        self, data: pd.DataFrame, period: int = 20, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        指数移動平均（EMA）計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            period: 移動平均期間
            timeframe: 時間軸

        Returns:
            Dict: EMA値と分析結果
        """
        try:
            if len(data) < period:
                logger.warning(f"Insufficient data for EMA: {len(data)} < {period}")
                return {"error": "データ不足"}

            if "Close" not in data.columns:
                logger.error("Close column not found")
                return {"error": "Close列が見つかりません"}

            close_prices = data["Close"].values.astype(np.float64)

            # TA-LibでEMA計算
            ema_values = talib.EMA(close_prices, timeperiod=period)

            # 最新値を取得
            current_ema = ema_values[-1] if not np.isnan(ema_values[-1]) else None
            previous_ema = (
                ema_values[-2]
                if len(ema_values) > 1 and not np.isnan(ema_values[-2])
                else None
            )
            current_price = close_prices[-1]

            if current_ema is None:
                return {"error": "EMA計算失敗"}

            # EMA状態の判定
            ema_state = self._analyze_ma_state(current_price, current_ema, previous_ema)

            result = {
                "current_value": round(current_ema, 4),
                "previous_value": round(previous_ema, 4) if previous_ema else None,
                "state": ema_state,
                "period": period,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "ema_series": ema_values.tolist()[-20:],
                    "price_vs_ema": current_price - current_ema,
                },
            }

            logger.info(
                f"EMA calculated for {timeframe}: {current_ema:.4f} ({ema_state})"
            )
            return result

        except Exception as e:
            logger.error(f"EMA calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_stochastic(
        self,
        data: pd.DataFrame,
        fastk_period: int = 14,
        slowk_period: int = 3,
        slowd_period: int = 3,
        timeframe: str = "D1",
    ) -> Dict[str, Any]:
        """
        ストキャスティクス計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            fastk_period: %K期間
            slowk_period: %Kの平滑化期間
            slowd_period: %D期間
            timeframe: 時間軸

        Returns:
            Dict: ストキャスティクス値と分析結果
        """
        try:
            if len(data) < fastk_period + slowk_period + slowd_period:
                logger.warning(
                    f"Insufficient data for Stochastic: {len(data)} < {fastk_period + slowk_period + slowd_period}"
                )
                return {"error": "データ不足"}

            if not all(col in data.columns for col in ["High", "Low", "Close"]):
                logger.error("High, Low, Close columns not found")
                return {"error": "High, Low, Close列が見つかりません"}

            high_prices = data["High"].values.astype(np.float64)
            low_prices = data["Low"].values.astype(np.float64)
            close_prices = data["Close"].values.astype(np.float64)

            # TA-Libでストキャスティクス計算
            slowk, slowd = talib.STOCH(
                high_prices,
                low_prices,
                close_prices,
                fastk_period=fastk_period,
                slowk_period=slowk_period,
                slowk_matype=0,
                slowd_period=slowd_period,
                slowd_matype=0,
            )

            # 最新値を取得
            current_k = slowk[-1] if not np.isnan(slowk[-1]) else None
            current_d = slowd[-1] if not np.isnan(slowd[-1]) else None

            if current_k is None or current_d is None:
                return {"error": "ストキャスティクス計算失敗"}

            # ストキャスティクス状態の判定
            stoch_state = self._analyze_stochastic_state(current_k, current_d)

            result = {
                "current_value": round(current_k, 2),
                "k_value": round(current_k, 2),
                "d_value": round(current_d, 2),
                "state": stoch_state,
                "fastk_period": fastk_period,
                "slowk_period": slowk_period,
                "slowd_period": slowd_period,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "k_series": slowk.tolist()[-20:],
                    "d_series": slowd.tolist()[-20:],
                },
            }

            logger.info(
                f"Stochastic calculated for {timeframe}: K={current_k:.2f}, D={current_d:.2f} ({stoch_state})"
            )
            return result

        except Exception as e:
            logger.error(f"Stochastic calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_atr(
        self, data: pd.DataFrame, period: int = 14, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        ATR（Average True Range）計算（TA-Lib使用）

        Args:
            data: OHLCVデータ
            period: ATR期間
            timeframe: 時間軸

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
                "period": period,
                "timeframe": timeframe,
                "calculation_time": datetime.now(),
                "additional_data": {
                    "atr_series": atr_values.tolist()[-20:],
                },
            }

            logger.info(
                f"ATR calculated for {timeframe}: {current_atr:.4f} ({atr_state})"
            )
            return result

        except Exception as e:
            logger.error(f"ATR calculation error: {str(e)}")
            return {"error": str(e)}

    def calculate_all_indicators(
        self, data: pd.DataFrame, timeframe: str = "D1"
    ) -> Dict[str, Any]:
        """
        全テクニカル指標を計算

        Args:
            data: OHLCVデータ
            timeframe: 時間軸

        Returns:
            Dict: 全指標の計算結果
        """
        try:
            results = {}

            # RSI計算
            rsi_result = self.calculate_rsi(data, timeframe=timeframe)
            if "error" not in rsi_result:
                results["RSI"] = rsi_result

            # MACD計算（十分なデータがある場合）
            if len(data) >= 40:
                macd_result = self.calculate_macd(data, timeframe=timeframe)
                if "error" not in macd_result:
                    results["MACD"] = macd_result

            # ボリンジャーバンド計算
            bb_result = self.calculate_bollinger_bands(data, timeframe=timeframe)
            if "error" not in bb_result:
                results["BB"] = bb_result

            # 移動平均線計算
            sma_result = self.calculate_sma(data, timeframe=timeframe)
            if "error" not in sma_result:
                results["SMA"] = sma_result

            ema_result = self.calculate_ema(data, timeframe=timeframe)
            if "error" not in ema_result:
                results["EMA"] = ema_result

            # ストキャスティクス計算
            stoch_result = self.calculate_stochastic(data, timeframe=timeframe)
            if "error" not in stoch_result:
                results["STOCH"] = stoch_result

            # ATR計算
            atr_result = self.calculate_atr(data, timeframe=timeframe)
            if "error" not in atr_result:
                results["ATR"] = atr_result

            logger.info(
                f"All indicators calculated for {timeframe}: {len(results)} indicators"
            )
            return results

        except Exception as e:
            logger.error(f"All indicators calculation error: {str(e)}")
            return {"error": str(e)}

    # 分析ヘルパーメソッド
    def _analyze_rsi_state(self, rsi_value: float) -> str:
        """RSI状態を分析"""
        if rsi_value >= 70:
            return "overbought"
        elif rsi_value <= 30:
            return "oversold"
        else:
            return "neutral"

    def _analyze_rsi_slope(self, rsi_values: np.ndarray, periods: int = 5) -> str:
        """RSIの傾きを分析"""
        if len(rsi_values) < periods:
            return "unknown"

        recent_rsi = rsi_values[-periods:]
        if len(recent_rsi) < 2:
            return "unknown"

        slope = np.polyfit(range(len(recent_rsi)), recent_rsi, 1)[0]

        if slope > 0.5:
            return "rising"
        elif slope < -0.5:
            return "falling"
        else:
            return "flat"

    def _analyze_macd_state(self, macd: float, signal: float, histogram: float) -> str:
        """MACD状態を分析"""
        if macd > signal and histogram > 0:
            return "bullish"
        elif macd < signal and histogram < 0:
            return "bearish"
        elif macd > signal and histogram < 0:
            return "weakening_bullish"
        elif macd < signal and histogram > 0:
            return "weakening_bearish"
        else:
            return "neutral"

    def _analyze_bollinger_bands_state(
        self, price: float, upper: float, middle: float, lower: float
    ) -> str:
        """ボリンジャーバンド状態を分析"""
        if upper is None or middle is None or lower is None:
            return "unknown"

        if price >= upper:
            return "above_upper"
        elif price <= lower:
            return "below_lower"
        elif price > middle:
            return "above_middle"
        else:
            return "below_middle"

    def _analyze_ma_state(
        self, price: float, current_ma: float, previous_ma: float
    ) -> str:
        """移動平均線状態を分析"""
        if current_ma is None:
            return "unknown"

        if price > current_ma:
            if previous_ma and current_ma > previous_ma:
                return "bullish_rising"
            else:
                return "bullish"
        else:
            if previous_ma and current_ma < previous_ma:
                return "bearish_falling"
            else:
                return "bearish"

    def _analyze_stochastic_state(self, k_value: float, d_value: float) -> str:
        """ストキャスティクス状態を分析"""
        if k_value >= 80 and d_value >= 80:
            return "overbought"
        elif k_value <= 20 and d_value <= 20:
            return "oversold"
        elif k_value > d_value:
            return "bullish"
        else:
            return "bearish"

    def _analyze_atr_state(self, current_atr: float, previous_atr: float) -> str:
        """ATR状態を分析"""
        if previous_atr is None:
            return "unknown"

        if current_atr > previous_atr * 1.1:
            return "increasing"
        elif current_atr < previous_atr * 0.9:
            return "decreasing"
        else:
            return "stable"
