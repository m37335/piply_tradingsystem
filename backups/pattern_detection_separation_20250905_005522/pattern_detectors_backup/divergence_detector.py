"""
ダイバージェンス検出器

パターン3: ダイバージェンス警戒を検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class DivergenceDetector:
    """ダイバージェンス警戒検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_3()
        self.utils = PatternUtils()

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        ダイバージェンス警戒を検出

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
                "strategy": self.pattern.strategy,
                "risk": self.pattern.risk,
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

        if price_data.empty or len(price_data) < 20:
            return False

        rsi_data = indicators.get("rsi", {})

        # 価格上昇トレンドのチェック（新高値から緩和）
        price_trend_condition = False
        if len(price_data) >= 10:
            recent_prices = price_data["Close"].iloc[-10:]  # 直近10期間
            # 価格が上昇傾向にあるかチェック（直近3期間で上昇）
            if len(recent_prices) >= 3:
                price_trend_condition = (
                    recent_prices.iloc[-1]
                    > recent_prices.iloc[-2]
                    > recent_prices.iloc[-3]
                )

        # RSI ダイバージェンスのチェック（前回高値未達から緩和）
        rsi_divergence_condition = False
        if "series" in rsi_data:
            rsi_series = rsi_data["series"]
            if len(rsi_series) >= 10:
                recent_rsi = rsi_series.iloc[-10:]  # 直近10期間
                current_rsi = recent_rsi.iloc[-1]

                # RSIが価格の上昇に追いついていないかチェック
                # 現在のRSIが過去5期間の平均を下回っている場合
                if len(recent_rsi) >= 5:
                    rsi_avg = recent_rsi.iloc[-5:].mean()
                    rsi_divergence_condition = current_rsi < rsi_avg

        return price_trend_condition and rsi_divergence_condition

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        indicators = h4_data.get("indicators", {})
        price_data = h4_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 10:
            return False

        rsi_data = indicators.get("rsi", {})

        # 価格上昇トレンドのチェック（3期間で上昇）
        price_trend_condition = False
        if len(price_data) >= 5:
            recent_prices = price_data["Close"].iloc[-5:]
            if len(recent_prices) >= 3:
                price_trend_condition = (
                    recent_prices.iloc[-1]
                    > recent_prices.iloc[-2]
                    > recent_prices.iloc[-3]
                )

        # RSI ダイバージェンスのチェック（3期間で下降）
        rsi_divergence_condition = False
        if "series" in rsi_data:
            rsi_series = rsi_data["series"]
            if len(rsi_series) >= 5:
                recent_rsi = rsi_series.iloc[-5:]
                if len(recent_rsi) >= 3:
                    rsi_divergence_condition = (
                        recent_rsi.iloc[-1] < recent_rsi.iloc[-2] < recent_rsi.iloc[-3]
                    )

        return price_trend_condition and rsi_divergence_condition

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        indicators = h1_data.get("indicators", {})
        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 10:
            return False

        rsi_data = indicators.get("rsi", {})

        # 価格上昇トレンドのチェック（3期間で上昇）
        price_trend_condition = False
        if len(price_data) >= 5:
            recent_prices = price_data["Close"].iloc[-5:]
            if len(recent_prices) >= 3:
                price_trend_condition = (
                    recent_prices.iloc[-1]
                    > recent_prices.iloc[-2]
                    > recent_prices.iloc[-3]
                )

        # RSI ダイバージェンスのチェック（3期間で下降）
        rsi_divergence_condition = False
        if "series" in rsi_data:
            rsi_series = rsi_data["series"]
            if len(rsi_series) >= 5:
                recent_rsi = rsi_series.iloc[-5:]
                if len(recent_rsi) >= 3:
                    rsi_divergence_condition = (
                        recent_rsi.iloc[-1] < recent_rsi.iloc[-2] < recent_rsi.iloc[-3]
                    )

        return price_trend_condition and rsi_divergence_condition

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        indicators = m5_data.get("indicators", {})
        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 10:
            return False

        rsi_data = indicators.get("rsi", {})

        # 価格上昇トレンドのチェック（3期間で上昇）
        price_trend_condition = False
        if len(price_data) >= 5:
            recent_prices = price_data["Close"].iloc[-5:]
            if len(recent_prices) >= 3:
                price_trend_condition = (
                    recent_prices.iloc[-1]
                    > recent_prices.iloc[-2]
                    > recent_prices.iloc[-3]
                )

        # RSI ダイバージェンスのチェック（3期間で下降）
        rsi_divergence_condition = False
        if "series" in rsi_data:
            rsi_series = rsi_data["series"]
            if len(rsi_series) >= 5:
                recent_rsi = rsi_series.iloc[-5:]
                if len(recent_rsi) >= 3:
                    rsi_divergence_condition = (
                        recent_rsi.iloc[-1] < recent_rsi.iloc[-2] < recent_rsi.iloc[-3]
                    )

        return price_trend_condition and rsi_divergence_condition

    def detect_divergence_pattern(
        self, multi_timeframe_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        詳細なダイバージェンスパターンを検出

        Args:
            multi_timeframe_data: マルチタイムフレームデータ

        Returns:
            ダイバージェンス検出結果
        """
        divergence_results = {}

        for timeframe, data in multi_timeframe_data.items():
            if not data or "indicators" not in data:
                continue

            price_data = data.get("price_data", pd.DataFrame())
            rsi_data = data.get("indicators", {}).get("rsi", {})

            if price_data.empty or "series" not in rsi_data:
                continue

            # ダイバージェンス検出
            divergence = self.utils.detect_divergence(
                price_data["Close"], rsi_data["series"], lookback=10
            )

            divergence_results[timeframe] = {
                "bullish_divergence": divergence["bullish"],
                "bearish_divergence": divergence["bearish"],
                "current_price": price_data["Close"].iloc[-1],
                "current_rsi": rsi_data["series"].iloc[-1],
            }

        return divergence_results

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
            "strategy": self.pattern.strategy,
            "risk": self.pattern.risk,
        }
