"""
パターン分析用ユーティリティ

マルチタイムフレーム戦略に基づくパターン分析の共通機能
"""

from typing import Any, Dict

import pandas as pd


class PatternUtils:
    """パターン分析用ユーティリティクラス"""

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """RSIを計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, pd.Series]:
        """MACDを計算"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal).mean()
        histogram = macd_line - signal_line

        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series, period: int = 20, std_dev: int = 2
    ) -> Dict[str, pd.Series]:
        """ボリンジャーバンドを計算"""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)

        return {"upper": upper_band, "middle": sma, "lower": lower_band}

    @staticmethod
    def calculate_volatility(prices: pd.Series, period: int = 20) -> float:
        """価格変動性を計算"""
        if len(prices) < period:
            return 0.0

        recent_prices = prices[-period:]
        returns = recent_prices.pct_change().dropna()
        volatility = returns.std()

        return float(volatility)

    @staticmethod
    def check_rsi_condition(rsi_value: float, condition: str) -> bool:
        """RSI条件をチェック"""
        if ">" in condition:
            threshold = float(condition.split(">")[1].strip())
            return rsi_value > threshold
        elif "<" in condition:
            threshold = float(condition.split("<")[1].strip())
            return rsi_value < threshold
        elif "-" in condition and "RSI" in condition:
            # RSI 30-50 のような範囲条件
            parts = condition.replace("RSI", "").strip().split("-")
            if len(parts) == 2:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip())
                return min_val <= rsi_value <= max_val
        return False

    @staticmethod
    def check_macd_dead_cross(macd_data: Dict[str, pd.Series]) -> bool:
        """MACDデッドクロスをチェック"""
        if len(macd_data["macd"]) < 2 or len(macd_data["signal"]) < 2:
            return False

        # 前回のクロスオーバーをチェック
        prev_macd = macd_data["macd"].iloc[-2]
        prev_signal = macd_data["signal"].iloc[-2]
        curr_macd = macd_data["macd"].iloc[-1]
        curr_signal = macd_data["signal"].iloc[-1]

        # デッドクロス: MACDがシグナルを下向きにクロス
        return prev_macd > prev_signal and curr_macd < curr_signal

    @staticmethod
    def check_macd_golden_cross(macd_data: Dict[str, pd.Series]) -> bool:
        """MACDゴールデンクロスをチェック"""
        if len(macd_data["macd"]) < 2 or len(macd_data["signal"]) < 2:
            return False

        # 前回のクロスオーバーをチェック
        prev_macd = macd_data["macd"].iloc[-2]
        prev_signal = macd_data["signal"].iloc[-2]
        curr_macd = macd_data["macd"].iloc[-1]
        curr_signal = macd_data["signal"].iloc[-1]

        # ゴールデンクロス: MACDがシグナルを上向きにクロス
        return prev_macd < prev_signal and curr_macd > curr_signal

    @staticmethod
    def check_bollinger_touch(
        price: float, bb_data: Dict[str, pd.Series], band: str = "+2σ"
    ) -> bool:
        """ボリンジャーバンドタッチをチェック"""
        if band == "+2σ":
            upper_band = bb_data["upper"].iloc[-1]
            # 0.1%以内
            return abs(price - upper_band) / upper_band < 0.001
        elif band == "-2σ":
            lower_band = bb_data["lower"].iloc[-1]
            # 0.1%以内
            return abs(price - lower_band) / lower_band < 0.001
        elif band == "ミドル":
            middle_band = bb_data["middle"].iloc[-1]
            # 0.2%以内
            return abs(price - middle_band) / middle_band < 0.002
        return False

    @staticmethod
    def check_bollinger_breakout(
        price: float, bb_data: Dict[str, pd.Series], direction: str = "up"
    ) -> bool:
        """ボリンジャーバンド突破をチェック"""
        if direction == "up":
            upper_band = bb_data["upper"].iloc[-1]
            return price > upper_band
        elif direction == "down":
            lower_band = bb_data["lower"].iloc[-1]
            return price < lower_band
        return False

    @staticmethod
    def detect_divergence(
        price_data: pd.Series, rsi_data: pd.Series, lookback: int = 10
    ) -> Dict[str, bool]:
        """ダイバージェンスを検出"""
        if len(price_data) < lookback or len(rsi_data) < lookback:
            return {"bullish": False, "bearish": False}

        # 価格とRSIの高値・安値を取得
        price_highs = price_data.rolling(window=5, center=True).max()
        price_lows = price_data.rolling(window=5, center=True).min()
        rsi_highs = rsi_data.rolling(window=5, center=True).max()
        rsi_lows = rsi_data.rolling(window=5, center=True).min()

        # 最新の高値・安値
        current_price_high = price_highs.iloc[-1]
        current_price_low = price_lows.iloc[-1]
        current_rsi_high = rsi_highs.iloc[-1]
        current_rsi_low = rsi_lows.iloc[-1]

        # 過去の高値・安値
        past_price_high = price_highs.iloc[-lookback:-1].max()
        past_price_low = price_lows.iloc[-lookback:-1].min()
        past_rsi_high = rsi_highs.iloc[-lookback:-1].max()
        past_rsi_low = rsi_lows.iloc[-lookback:-1].min()

        # ベアリッシュダイバージェンス: 価格新高値、RSI前回高値未達
        bearish_divergence = (
            current_price_high > past_price_high and current_rsi_high < past_rsi_high
        )

        # ブルリッシュダイバージェンス: 価格新安値、RSI前回安値未達
        bullish_divergence = (
            current_price_low < past_price_low and current_rsi_low > past_rsi_low
        )

        return {"bullish": bullish_divergence, "bearish": bearish_divergence}

    @staticmethod
    def check_candle_pattern(prices: pd.Series, pattern: str) -> bool:
        """ローソク足パターンをチェック"""
        if len(prices) < 3:
            return False

        # ヒゲ形成のチェック（簡易版）
        if pattern == "ヒゲ形成":
            current_price = prices.iloc[-1]
            prev_price = prices.iloc[-2]
            # 上昇トレンド中の上ヒゲ
            return current_price < prev_price and current_price > prices.iloc[-3]

        return False

    @staticmethod
    def check_momentum(prices: pd.Series, period: int = 5) -> str:
        """モメンタムをチェック"""
        if len(prices) < period:
            return "neutral"

        recent_prices = prices.iloc[-period:]
        price_change = (
            recent_prices.iloc[-1] - recent_prices.iloc[0]
        ) / recent_prices.iloc[0]

        if price_change > 0.01:  # 1%以上の上昇
            return "strong_up"
        elif price_change > 0.005:  # 0.5%以上の上昇
            return "up"
        elif price_change < -0.01:  # 1%以上の下降
            return "strong_down"
        elif price_change < -0.005:  # 0.5%以上の下降
            return "down"
        else:
            return "neutral"

    @staticmethod
    def validate_timeframe_data(data: Dict[str, Any]) -> bool:
        """タイムフレームデータの妥当性をチェック"""
        required_keys = ["price_data", "indicators"]
        required_indicators = ["rsi", "macd", "bollinger_bands"]

        # 基本キーの存在チェック
        for key in required_keys:
            if key not in data:
                return False

        # 指標の存在チェック
        indicators = data.get("indicators", {})
        for indicator in required_indicators:
            if indicator not in indicators:
                return False

        # データの長さチェック
        price_data = data.get("price_data", pd.DataFrame())
        if len(price_data) < 20:  # 最低20データポイント必要
            return False

        return True

    @staticmethod
    def get_pattern_confidence_score(conditions_met: Dict[str, bool]) -> float:
        """パターンの信頼度スコアを計算"""
        total_conditions = len(conditions_met)
        met_conditions = sum(conditions_met.values())

        if total_conditions == 0:
            return 0.0

        # 基本スコア: 条件達成率
        base_score = met_conditions / total_conditions

        # 時間軸の重み付け（上位足ほど重要）
        timeframe_weights = {"D1": 0.4, "H4": 0.3, "H1": 0.2, "M5": 0.1}

        weighted_score = 0.0
        for timeframe, met in conditions_met.items():
            weight = timeframe_weights.get(timeframe, 0.1)
            weighted_score += (1.0 if met else 0.0) * weight

        # 最終スコア: 基本スコアと重み付きスコアの平均
        final_score = (base_score + weighted_score) / 2
        return round(final_score, 2)
