"""
複合シグナル検出器

パターン6: 複合シグナル強化を検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class CompositeSignalDetector:
    """複合シグナル強化検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_6()
        self.utils = PatternUtils()

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        複合シグナル強化を検出

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            検出結果の辞書、検出されない場合はNone
        """
        # データの妥当性チェック
        if not self._validate_data(multi_timeframe_data):
            return None

        # 各時間軸の条件をチェック
        conditions_met = {}

        # D1条件チェック
        d1_conditions = self._check_d1_conditions(multi_timeframe_data.get("D1", {}))
        conditions_met["D1"] = d1_conditions

        # H4条件チェック
        h4_conditions = self._check_h4_conditions(multi_timeframe_data.get("H4", {}))
        conditions_met["H4"] = h4_conditions

        # H1条件チェック
        h1_conditions = self._check_h1_conditions(multi_timeframe_data.get("H1", {}))
        conditions_met["H1"] = h1_conditions

        # M5条件チェック
        m5_conditions = self._check_m5_conditions(multi_timeframe_data.get("M5", {}))
        conditions_met["M5"] = m5_conditions

        # 全条件が満たされているかチェック
        all_conditions_met = all(conditions_met.values())

        if all_conditions_met:
            # 信頼度スコアを計算
            confidence_score = self.utils.get_pattern_confidence_score(conditions_met)

            # 検出結果を返す
            return {
                "pattern_number": self.pattern.pattern_number,
                "pattern_name": self.pattern.name,
                "priority": self.pattern.priority,
                "conditions_met": conditions_met,
                "confidence_score": confidence_score,
                "notification_title": self.pattern.notification_title,
                "notification_color": self.pattern.notification_color,
                "take_profit": self.pattern.take_profit,
                "stop_loss": self.pattern.stop_loss,
                "confidence": self.pattern.confidence,
                "detected_at": pd.Timestamp.now(),
                "timeframe_data": multi_timeframe_data,
            }

        return None

    def _validate_data(self, data: Dict[str, Any]) -> bool:
        """データの妥当性をチェック"""
        required_timeframes = ["D1", "H4", "H1", "M5"]

        for timeframe in required_timeframes:
            if timeframe not in data:
                return False

            if not self.utils.validate_timeframe_data(data[timeframe]):
                return False

        return True

    def _check_d1_conditions(self, d1_data: Dict[str, Any]) -> bool:
        """D1時間軸の条件をチェック（RSI + MACD + 価格 3つ一致）"""
        if not d1_data:
            return False

        indicators = d1_data.get("indicators", {})
        price_data = d1_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        rsi_data = indicators.get("rsi", {})
        macd_data = indicators.get("macd", {})

        # RSI条件のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            # RSIが適切な範囲にあるかチェック
            rsi_condition = 30 <= rsi_value <= 70

        # MACD条件のチェック
        macd_condition = False
        if "macd" in macd_data and "signal" in macd_data:
            current_macd = macd_data["macd"].iloc[-1]
            current_signal = macd_data["signal"].iloc[-1]
            # MACDがシグナルを上回っているかチェック
            macd_condition = current_macd > current_signal

        # 価格条件のチェック
        price_condition = False
        if len(price_data) >= 5:
            recent_prices = price_data["Close"].iloc[-5:]
            # 価格が上昇傾向にあるかチェック
            price_condition = recent_prices.iloc[-1] > recent_prices.iloc[-2]

        # 3つすべての条件が一致しているかチェック
        return rsi_condition and macd_condition and price_condition

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック（RSI + ボリンジャーバンド 2つ一致）"""
        if not h4_data:
            return False

        indicators = h4_data.get("indicators", {})
        price_data = h4_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        current_price = price_data["Close"].iloc[-1]
        rsi_data = indicators.get("rsi", {})
        bb_data = indicators.get("bollinger_bands", {})

        # RSI条件のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 30 <= rsi_value <= 70

        # ボリンジャーバンド条件のチェック
        bb_condition = False
        if bb_data:
            # 価格がボリンジャーバンドの適切な位置にあるかチェック
            upper_band = bb_data["upper"].iloc[-1]
            lower_band = bb_data["lower"].iloc[-1]
            bb_condition = lower_band <= current_price <= upper_band

        # 2つすべての条件が一致しているかチェック
        return rsi_condition and bb_condition

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック（RSI + ボリンジャーバンド 2つ一致）"""
        if not h1_data:
            return False

        indicators = h1_data.get("indicators", {})
        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        current_price = price_data["Close"].iloc[-1]
        rsi_data = indicators.get("rsi", {})
        bb_data = indicators.get("bollinger_bands", {})

        # RSI条件のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 30 <= rsi_value <= 70

        # ボリンジャーバンド条件のチェック
        bb_condition = False
        if bb_data:
            # 価格がボリンジャーバンドの適切な位置にあるかチェック
            upper_band = bb_data["upper"].iloc[-1]
            lower_band = bb_data["lower"].iloc[-1]
            bb_condition = lower_band <= current_price <= upper_band

        # 2つすべての条件が一致しているかチェック
        return rsi_condition and bb_condition

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック（RSI + 価格形状 2つ一致）"""
        if not m5_data:
            return False

        indicators = m5_data.get("indicators", {})
        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        rsi_data = indicators.get("rsi", {})

        # RSI条件のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 30 <= rsi_value <= 70

        # 価格形状条件のチェック
        price_shape_condition = False
        if len(price_data) >= 5:
            recent_prices = price_data["Close"].iloc[-5:]
            # 価格が安定した形状を保っているかチェック
            price_volatility = recent_prices.std() / recent_prices.mean()
            price_shape_condition = price_volatility < 0.02  # 2%以下の変動率

        # 2つすべての条件が一致しているかチェック
        return rsi_condition and price_shape_condition

    def calculate_composite_score(
        self, multi_timeframe_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        複合シグナルスコアを計算

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            複合シグナルスコア分析結果
        """
        composite_analysis = {}

        for timeframe, data in multi_timeframe_data.items():
            if not data or "indicators" not in data:
                continue

            price_data = data.get("price_data", pd.DataFrame())
            indicators = data.get("indicators", {})

            if price_data.empty:
                continue

            # 各指標のスコアを計算
            scores = {}

            # RSIスコア
            if "rsi" in indicators and "current_value" in indicators["rsi"]:
                rsi_value = indicators["rsi"]["current_value"]
                if 30 <= rsi_value <= 70:
                    scores["rsi"] = 1.0
                else:
                    scores["rsi"] = 0.0

            # MACDスコア
            if "macd" in indicators:
                macd_data = indicators["macd"]
                if "macd" in macd_data and "signal" in macd_data:
                    current_macd = macd_data["macd"].iloc[-1]
                    current_signal = macd_data["signal"].iloc[-1]
                    if current_macd > current_signal:
                        scores["macd"] = 1.0
                    else:
                        scores["macd"] = 0.0

            # ボリンジャーバンドスコア
            if "bollinger_bands" in indicators:
                bb_data = indicators["bollinger_bands"]
                current_price = price_data["Close"].iloc[-1]
                upper_band = bb_data["upper"].iloc[-1]
                lower_band = bb_data["lower"].iloc[-1]
                if lower_band <= current_price <= upper_band:
                    scores["bollinger_bands"] = 1.0
                else:
                    scores["bollinger_bands"] = 0.0

            # 価格形状スコア
            if len(price_data) >= 5:
                recent_prices = price_data["Close"].iloc[-5:]
                price_volatility = recent_prices.std() / recent_prices.mean()
                if price_volatility < 0.02:
                    scores["price_shape"] = 1.0
                else:
                    scores["price_shape"] = 0.0

            # 総合スコアを計算
            if scores:
                composite_score = sum(scores.values()) / len(scores)
                composite_analysis[timeframe] = {
                    "individual_scores": scores,
                    "composite_score": composite_score,
                    "current_price": price_data["Close"].iloc[-1],
                }

        return composite_analysis

    def get_pattern_info(self) -> Dict[str, Any]:
        """パターン情報を取得"""
        return {
            "pattern_number": self.pattern.pattern_number,
            "name": self.pattern.name,
            "description": self.pattern.description,
            "priority": self.pattern.priority,
            "conditions": self.pattern.conditions,
            "notification_title": self.pattern.notification_title,
            "notification_color": self.pattern.notification_color,
            "take_profit": self.pattern.take_profit,
            "stop_loss": self.pattern.stop_loss,
            "confidence": self.pattern.confidence,
        }
