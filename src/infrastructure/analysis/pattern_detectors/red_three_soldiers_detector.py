"""
赤三兵パターン検出器

パターン8: 赤三兵パターンを検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class RedThreeSoldiersDetector:
    """赤三兵パターン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_8()
        self.utils = PatternUtils()
        self.min_body_ratio = 0.3  # 実体比率の最小値（0.5から緩和）
        self.min_close_increase = 0.0005  # 終値上昇の最小値（0.001から緩和）

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        赤三兵パターンを検出

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
            confidence_score = self._calculate_pattern_strength(conditions_met)

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

        if price_data.empty or len(price_data) < 3:
            return False

        # 赤三兵パターンをチェック
        return self._detect_red_three_soldiers_pattern(price_data)

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        price_data = h4_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 3:
            return False

        # 赤三兵パターンをチェック
        return self._detect_red_three_soldiers_pattern(price_data)

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 3:
            return False

        # 赤三兵パターンをチェック
        return self._detect_red_three_soldiers_pattern(price_data)

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 3:
            return False

        # 赤三兵パターンをチェック
        return self._detect_red_three_soldiers_pattern(price_data)

    def _detect_red_three_soldiers_pattern(self, price_data: pd.DataFrame) -> bool:
        """
        赤三兵パターンを検出

        Args:
            price_data: 価格データ

        Returns:
            赤三兵パターンが検出された場合はTrue
        """
        if len(price_data) < 3:
            return False

        # 最新の3本のローソク足を取得
        candles = price_data.tail(3)

        # 3本連続陽線チェック
        if not self._check_three_consecutive_bullish_candles(candles):
            return False

        # 終値の高値更新チェック
        if not self._check_higher_closes(candles):
            return False

        # 実体サイズの一貫性チェック
        if not self._check_body_size_consistency(candles):
            return False

        return True

    def _check_three_consecutive_bullish_candles(self, candles: pd.DataFrame) -> bool:
        """
        3本連続陽線をチェック

        Args:
            candles: 3本のローソク足データ

        Returns:
            3本連続陽線の場合はTrue
        """
        for _, candle in candles.iterrows():
            if candle["Close"] <= candle["Open"]:
                return False
        return True

    def _check_higher_closes(self, candles: pd.DataFrame) -> bool:
        """
        終値の高値更新をチェック（緩和）

        Args:
            candles: 3本のローソク足データ

        Returns:
            終値が高値更新されている場合はTrue
        """
        closes = candles["Close"].values

        for i in range(1, len(closes)):
            # 終値上昇の条件を緩和（前日比0.05%以上または単純上昇）
            price_change = (closes[i] - closes[i - 1]) / closes[i - 1]
            if closes[i] <= closes[i - 1] and price_change < self.min_close_increase:
                return False

        return True

    def _check_body_size_consistency(self, candles: pd.DataFrame) -> bool:
        """
        実体サイズの一貫性をチェック

        Args:
            candles: 3本のローソク足データ

        Returns:
            実体サイズが一貫している場合はTrue
        """
        body_sizes = []

        for _, candle in candles.iterrows():
            body_size = abs(candle["Close"] - candle["Open"])
            total_range = candle["High"] - candle["Low"]

            if total_range == 0:
                return False

            body_ratio = body_size / total_range
            body_sizes.append(body_ratio)

            if body_ratio < self.min_body_ratio:
                return False

        # 実体サイズの一貫性をチェック（最大値と最小値の差が70%以内に緩和）
        if max(body_sizes) - min(body_sizes) > 0.7:
            return False

        return True

    def _calculate_pattern_strength(self, conditions_met: Dict[str, bool]) -> float:
        """
        パターン強度を計算

        Args:
            conditions_met: 各時間軸の条件達成状況

        Returns:
            信頼度スコア（0.0-1.0）
        """
        # 基本信頼度
        base_confidence = 0.80

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
