"""
押し目買い検出器

パターン2: 押し目買いチャンスを検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class PullbackDetector:
    """押し目買いチャンス検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_2()
        self.utils = PatternUtils()

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        押し目買いチャンスを検出

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
        """D1時間軸の条件をチェック"""
        if not d1_data:
            return False

        indicators = d1_data.get("indicators", {})
        price_data = d1_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        rsi_data = indicators.get("rsi", {})
        macd_data = indicators.get("macd", {})

        # RSI 30-50 のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 30 <= rsi_value <= 50

        # MACD 上昇継続のチェック
        macd_condition = False
        if "macd" in macd_data and "signal" in macd_data:
            # MACDがシグナルを上回っているかチェック
            current_macd = macd_data["macd"].iloc[-1]
            current_signal = macd_data["signal"].iloc[-1]
            macd_condition = current_macd > current_signal

        return rsi_condition and macd_condition

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        indicators = h4_data.get("indicators", {})
        price_data = h4_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        current_price = price_data["Close"].iloc[-1]
        rsi_data = indicators.get("rsi", {})
        bb_data = indicators.get("bollinger_bands", {})

        # RSI 30-40 のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 30 <= rsi_value <= 40

        # ボリンジャーバンド -2σ タッチのチェック
        bb_condition = False
        if bb_data:
            bb_condition = self.utils.check_bollinger_touch(
                current_price, bb_data, "-2σ"
            )

        return rsi_condition and bb_condition

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        indicators = h1_data.get("indicators", {})
        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        current_price = price_data["Close"].iloc[-1]
        rsi_data = indicators.get("rsi", {})
        bb_data = indicators.get("bollinger_bands", {})

        # RSI 30-35 のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 30 <= rsi_value <= 35

        # ボリンジャーバンド -2σ タッチのチェック
        bb_condition = False
        if bb_data:
            bb_condition = self.utils.check_bollinger_touch(
                current_price, bb_data, "-2σ"
            )

        return rsi_condition and bb_condition

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        indicators = m5_data.get("indicators", {})
        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        rsi_data = indicators.get("rsi", {})

        # RSI 30以下 のチェック
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = rsi_value <= 30

        # 反発サインのチェック（価格が上昇に転じているか）
        bounce_condition = False
        if len(price_data) >= 3:
            recent_prices = price_data["Close"].iloc[-3:]
            # 直近3期間で価格が上昇傾向にあるかチェック
            bounce_condition = (
                recent_prices.iloc[-1] > recent_prices.iloc[-2]
                and recent_prices.iloc[-2] > recent_prices.iloc[-3]
            )

        return rsi_condition and bounce_condition

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
