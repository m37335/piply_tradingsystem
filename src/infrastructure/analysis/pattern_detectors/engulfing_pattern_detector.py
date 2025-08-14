"""
つつみ足パターン検出器

パターン7: つつみ足パターンを検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class EngulfingPatternDetector:
    """つつみ足パターン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_7()
        self.utils = PatternUtils()
        self.min_body_ratio = 0.4  # 実体比率の最小値（0.6から緩和）
        self.min_engulfing_ratio = 1.05  # 包み込み比率の最小値（1.1から緩和）

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        つつみ足パターンを検出

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
            confidence_score = self._calculate_engulfing_confidence(conditions_met)

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

        price_data = d1_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 2:
            return False

        # つつみ足パターンをチェック
        return self._detect_engulfing_pattern(price_data)

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        price_data = h4_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 2:
            return False

        # つつみ足パターンをチェック
        return self._detect_engulfing_pattern(price_data)

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 2:
            return False

        # つつみ足パターンをチェック
        return self._detect_engulfing_pattern(price_data)

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 2:
            return False

        # つつみ足パターンをチェック
        return self._detect_engulfing_pattern(price_data)

    def _detect_engulfing_pattern(self, price_data: pd.DataFrame) -> bool:
        """
        つつみ足パターンを検出

        Args:
            price_data: 価格データ

        Returns:
            つつみ足パターンが検出された場合はTrue
        """
        if len(price_data) < 2:
            return False

        # 最新の2本のローソク足を取得
        current_candle = price_data.iloc[-1]
        previous_candle = price_data.iloc[-2]

        # 陽のつつみ足をチェック
        if self._detect_bullish_engulfing(current_candle, previous_candle):
            return True

        # 陰のつつみ足をチェック
        if self._detect_bearish_engulfing(current_candle, previous_candle):
            return True

        return False

    def _detect_bullish_engulfing(
        self, current_candle: pd.Series, previous_candle: pd.Series
    ) -> bool:
        """
        陽のつつみ足を検出

        Args:
            current_candle: 現在のローソク足
            previous_candle: 前のローソク足

        Returns:
            陽のつつみ足が検出された場合はTrue
        """
        # 前の足が陰線で、現在の足が陽線であることを確認
        if (
            previous_candle["close"] < previous_candle["open"]
            and current_candle["close"] > current_candle["open"]
        ):
            # 現在の足の実体が前の足の実体を包み込んでいることを確認
            current_body_high = max(current_candle["open"], current_candle["close"])
            current_body_low = min(current_candle["open"], current_candle["close"])
            previous_body_high = max(previous_candle["open"], previous_candle["close"])
            previous_body_low = min(previous_candle["open"], previous_candle["close"])

            # 実体比率をチェック
            current_body_size = abs(current_candle["close"] - current_candle["open"])
            previous_body_size = abs(previous_candle["close"] - previous_candle["open"])

            current_body_ratio = current_body_size / (
                current_candle["high"] - current_candle["low"]
            )
            engulfing_ratio = current_body_size / previous_body_size

            # 包み込み条件をチェック（緩和）
            # 完全包み込みまたは部分的な包み込みを許容
            if (
                current_body_high >= previous_body_high
                and current_body_low <= previous_body_low
            ) or (
                # 部分的な包み込みも許容（実体の80%以上を包み込む）
                current_body_high >= previous_body_high * 0.95
                and current_body_low <= previous_body_low * 1.05
                and current_body_size >= previous_body_size * 0.8
            ):
                if (
                    current_body_ratio >= self.min_body_ratio
                    and engulfing_ratio >= self.min_engulfing_ratio
                ):
                    return True

        return False

    def _detect_bearish_engulfing(
        self, current_candle: pd.Series, previous_candle: pd.Series
    ) -> bool:
        """
        陰のつつみ足を検出

        Args:
            current_candle: 現在のローソク足
            previous_candle: 前のローソク足

        Returns:
            陰のつつみ足が検出された場合はTrue
        """
        # 前の足が陽線で、現在の足が陰線であることを確認
        if (
            previous_candle["close"] > previous_candle["open"]
            and current_candle["close"] < current_candle["open"]
        ):
            # 現在の足の実体が前の足の実体を包み込んでいることを確認
            current_body_high = max(current_candle["open"], current_candle["close"])
            current_body_low = min(current_candle["open"], current_candle["close"])
            previous_body_high = max(previous_candle["open"], previous_candle["close"])
            previous_body_low = min(previous_candle["open"], previous_candle["close"])

            # 実体比率をチェック
            current_body_size = abs(current_candle["close"] - current_candle["open"])
            previous_body_size = abs(previous_candle["close"] - previous_candle["open"])

            current_body_ratio = current_body_size / (
                current_candle["high"] - current_candle["low"]
            )
            engulfing_ratio = current_body_size / previous_body_size

            # 包み込み条件をチェック（緩和）
            # 完全包み込みまたは部分的な包み込みを許容
            if (
                current_body_high >= previous_body_high
                and current_body_low <= previous_body_low
            ) or (
                # 部分的な包み込みも許容（実体の80%以上を包み込む）
                current_body_high >= previous_body_high * 0.95
                and current_body_low <= previous_body_low * 1.05
                and current_body_size >= previous_body_size * 0.8
            ):
                if (
                    current_body_ratio >= self.min_body_ratio
                    and engulfing_ratio >= self.min_engulfing_ratio
                ):
                    return True

        return False

    def _calculate_engulfing_confidence(self, conditions_met: Dict[str, bool]) -> float:
        """
        つつみ足の信頼度を計算

        Args:
            conditions_met: 各時間軸の条件達成状況

        Returns:
            信頼度スコア（0.0-1.0）
        """
        # 基本信頼度
        base_confidence = 0.85

        # 時間軸の重み付け
        timeframe_weights = {"D1": 0.4, "H4": 0.3, "H1": 0.2, "M5": 0.1}

        # 条件達成度に基づいて信頼度を調整
        weighted_confidence = 0.0
        total_weight = 0.0

        for timeframe, met in conditions_met.items():
            weight = timeframe_weights.get(timeframe, 0.1)
            if met:
                weighted_confidence += base_confidence * weight
            total_weight += weight

        if total_weight > 0:
            final_confidence = weighted_confidence / total_weight
            return min(final_confidence, 1.0)

        return base_confidence

    def get_pattern_info(self) -> Dict[str, Any]:
        """パターン情報を取得"""
        return {
            "pattern_number": self.pattern.pattern_number,
            "name": self.pattern.name,
            "description": self.pattern.description,
            "priority": self.pattern.priority.value,
            "conditions": self.pattern.conditions,
            "notification_title": self.pattern.notification_title,
            "notification_color": self.pattern.notification_color,
        }
