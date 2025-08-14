"""
ブレイクアウト検出器

パターン4: ブレイクアウト狙いを検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class BreakoutDetector:
    """ブレイクアウト狙い検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_4()
        self.utils = PatternUtils()

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ブレイクアウト狙いを検出

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

        # RSI 45-75 のチェック（50-70から拡大）
        rsi_condition = False
        if "current_value" in rsi_data:
            rsi_value = rsi_data["current_value"]
            rsi_condition = 45 <= rsi_value <= 75

        # MACD 上昇トレンドのチェック（条件を改善）
        macd_condition = False
        if "macd" in macd_data and "signal" in macd_data:
            # MACDが上昇傾向にあるかチェック（3期間連続上昇）
            if len(macd_data["macd"]) >= 3:
                recent_macd = macd_data["macd"].iloc[-3:]
                macd_condition = (
                    recent_macd.iloc[-1] > recent_macd.iloc[-2] > recent_macd.iloc[-3]
                )

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
        bb_data = indicators.get("bollinger_bands", {})

        # ボリンジャーバンド +1.5σ 近接のチェック（+2σから緩和）
        bb_condition = False
        if bb_data and "upper" in bb_data:
            upper_band = bb_data["upper"].iloc[-1]
            # 価格が上限の5%以内にあるかチェック
            price_diff = abs(current_price - upper_band)
            bb_condition = price_diff <= upper_band * 0.05

        return bb_condition

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        indicators = h1_data.get("indicators", {})
        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        current_price = price_data["Close"].iloc[-1]
        bb_data = indicators.get("bollinger_bands", {})

        # ボリンジャーバンド +1.5σ 近接のチェック（+2σから緩和）
        bb_condition = False
        if bb_data and "upper" in bb_data:
            upper_band = bb_data["upper"].iloc[-1]
            # 価格が上限の5%以内にあるかチェック
            price_diff = abs(current_price - upper_band)
            bb_condition = price_diff <= upper_band * 0.05

        return bb_condition

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty:
            return False

        # 上昇モメンタムのチェック（条件を緩和）
        momentum_condition = False
        if len(price_data) >= 5:
            # 直近3期間で価格が上昇しているかチェック
            recent_prices = price_data["Close"].iloc[-3:]
            if len(recent_prices) >= 3:
                momentum_condition = (
                    recent_prices.iloc[-1] > recent_prices.iloc[-2] > recent_prices.iloc[-3]
                )

        return momentum_condition

    def detect_breakout_strength(
        self, multi_timeframe_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ブレイクアウトの強度を分析

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            ブレイクアウト強度分析結果
        """
        breakout_analysis = {}

        for timeframe, data in multi_timeframe_data.items():
            if not data or "indicators" not in data:
                continue

            price_data = data.get("price_data", pd.DataFrame())
            bb_data = data.get("indicators", {}).get("bollinger_bands", {})

            if price_data.empty or not bb_data:
                continue

            current_price = price_data["Close"].iloc[-1]
            upper_band = bb_data["upper"].iloc[-1]

            # ブレイクアウト強度を計算
            if current_price > upper_band:
                breakout_strength = (current_price - upper_band) / upper_band * 100
                breakout_analysis[timeframe] = {
                    "breakout_strength": breakout_strength,
                    "current_price": current_price,
                    "upper_band": upper_band,
                    "is_breakout": True,
                }
            else:
                breakout_analysis[timeframe] = {
                    "breakout_strength": 0.0,
                    "current_price": current_price,
                    "upper_band": upper_band,
                    "is_breakout": False,
                }

        return breakout_analysis

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
        }
