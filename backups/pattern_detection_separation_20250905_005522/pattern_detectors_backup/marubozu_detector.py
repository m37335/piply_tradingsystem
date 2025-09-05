"""
引け坊主パターン検出器

パターン9: 引け坊主パターンを検出するクラス
"""

from typing import Any, Dict, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class MarubozuDetector:
    """引け坊主パターン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_9()
        self.utils = PatternUtils()
        self.max_wick_ratio = 0.2  # ヒゲ比率の最大値（0.1から緩和）
        self.min_body_ratio = 0.6  # 実体比率の最小値（0.8から緩和）

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        引け坊主パターンを検出

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
            confidence_score = self._calculate_marubozu_strength(conditions_met)

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

        if price_data.empty or len(price_data) < 1:
            return False

        # 引け坊主パターンをチェック
        return self._detect_marubozu_pattern(price_data)

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        price_data = h4_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 1:
            return False

        # 引け坊主パターンをチェック
        return self._detect_marubozu_pattern(price_data)

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        price_data = h1_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 1:
            return False

        # 引け坊主パターンをチェック
        return self._detect_marubozu_pattern(price_data)

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        price_data = m5_data.get("price_data", pd.DataFrame())

        if price_data.empty or len(price_data) < 1:
            return False

        # 引け坊主パターンをチェック
        return self._detect_marubozu_pattern(price_data)

    def _detect_marubozu_pattern(self, price_data: pd.DataFrame) -> bool:
        """
        引け坊主パターンを検出

        Args:
            price_data: 価格データ

        Returns:
            引け坊主パターンが検出された場合はTrue
        """
        if len(price_data) < 1:
            return False

        # 最新のローソク足を取得
        latest_candle = price_data.iloc[-1]

        # 大陽線引け坊主をチェック
        if self._detect_bullish_marubozu(latest_candle):
            return True

        # 大陰線引け坊主をチェック
        if self._detect_bearish_marubozu(latest_candle):
            return True

        return False

    def _detect_bullish_marubozu(self, candle: pd.Series) -> bool:
        """
        大陽線引け坊主を検出

        Args:
            candle: ローソク足データ

        Returns:
            大陽線引け坊主が検出された場合はTrue
        """
        # 陽線であることを確認
        if candle["Close"] <= candle["Open"]:
            return False

        # ヒゲの欠如をチェック
        if not self._check_wick_absence(candle):
            return False

        # 実体比率をチェック
        body_size = abs(candle["Close"] - candle["Open"])
        total_range = candle["High"] - candle["Low"]

        if total_range == 0:
            return False

        body_ratio = body_size / total_range
        if body_ratio < self.min_body_ratio:
            return False

        return True

    def _detect_bearish_marubozu(self, candle: pd.Series) -> bool:
        """
        大陰線引け坊主を検出

        Args:
            candle: ローソク足データ

        Returns:
            大陰線引け坊主が検出された場合はTrue
        """
        # 陰線であることを確認
        if candle["Close"] >= candle["Open"]:
            return False

        # ヒゲの欠如をチェック
        if not self._check_wick_absence(candle):
            return False

        # 実体比率をチェック
        body_size = abs(candle["Close"] - candle["Open"])
        total_range = candle["High"] - candle["Low"]

        if total_range == 0:
            return False

        body_ratio = body_size / total_range
        if body_ratio < self.min_body_ratio:
            return False

        return True

    def _check_wick_absence(self, candle: pd.Series) -> bool:
        """
        ヒゲの欠如をチェック

        Args:
            candle: ローソク足データ

        Returns:
            ヒゲが欠如している場合はTrue
        """
        open_price = candle["Open"]
        close_price = candle["Close"]
        high = candle["High"]
        low = candle["Low"]

        # 上ヒゲの計算
        upper_wick = high - max(open_price, close_price)

        # 下ヒゲの計算
        lower_wick = min(open_price, close_price) - low

        # 総範囲
        total_range = high - low

        if total_range == 0:
            return False

        # 上ヒゲと下ヒゲの比率をチェック
        upper_wick_ratio = upper_wick / total_range
        lower_wick_ratio = lower_wick / total_range

        # ヒゲの条件を緩和（両方のヒゲが最大比率以下、または片方のヒゲが非常に小さい）
        if (
            upper_wick_ratio <= self.max_wick_ratio
            and lower_wick_ratio <= self.max_wick_ratio
        ) or (
            # 片方のヒゲが非常に小さい場合（5%以下）
            (upper_wick_ratio <= 0.05 and lower_wick_ratio <= self.max_wick_ratio * 1.5)
            or (
                lower_wick_ratio <= 0.05
                and upper_wick_ratio <= self.max_wick_ratio * 1.5
            )
        ):
            return True

        return False

    def _calculate_marubozu_strength(self, conditions_met: Dict[str, bool]) -> float:
        """
        引け坊主強度を計算

        Args:
            conditions_met: 各時間軸の条件達成状況

        Returns:
            信頼度スコア（0.0-1.0）
        """
        # 基本信頼度
        base_confidence = 0.75

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
