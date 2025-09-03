"""
トリプルトップ/ボトムパターン検出器

パターン11: トリプルトップ/ボトムパターンを検出するクラス
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from ....domain.entities.notification_pattern import NotificationPattern
from ....utils.pattern_utils import PatternUtils


class TripleTopBottomDetector:
    """トリプルトップ/ボトムパターン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_11()
        self.utils = PatternUtils()
        self.min_peak_distance = 5  # ピーク間の最小距離
        self.peak_tolerance = 0.015  # ピークの許容誤差（1.5%）
        self.neckline_tolerance = 0.008  # ネックラインの許容誤差（0.8%）

    def detect(self, multi_timeframe_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        トリプルトップ/ボトムパターンを検出

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
            confidence_score = self._calculate_triple_pattern_confidence(conditions_met)

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
        if price_data.empty:
            return False

        # トリプルトップまたはトリプルボトムの検出
        return self._detect_triple_top(price_data) or self._detect_triple_bottom(
            price_data
        )

    def _check_h4_conditions(self, h4_data: Dict[str, Any]) -> bool:
        """H4時間軸の条件をチェック"""
        if not h4_data:
            return False

        price_data = h4_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # トリプルトップまたはトリプルボトムの検出
        return self._detect_triple_top(price_data) or self._detect_triple_bottom(
            price_data
        )

    def _check_h1_conditions(self, h1_data: Dict[str, Any]) -> bool:
        """H1時間軸の条件をチェック"""
        if not h1_data:
            return False

        price_data = h1_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # トリプルトップまたはトリプルボトムの検出
        return self._detect_triple_top(price_data) or self._detect_triple_bottom(
            price_data
        )

    def _check_m5_conditions(self, m5_data: Dict[str, Any]) -> bool:
        """M5時間軸の条件をチェック"""
        if not m5_data:
            return False

        price_data = m5_data.get("price_data", pd.DataFrame())
        if price_data.empty:
            return False

        # トリプルトップまたはトリプルボトムの検出
        return self._detect_triple_top(price_data) or self._detect_triple_bottom(
            price_data
        )

    def _detect_triple_top(self, price_data: pd.DataFrame) -> bool:
        """トリプルトップ検出"""
        if len(price_data) < 30:
            return False

        # 高値のピークを検出
        peaks = self._find_peaks(price_data, "High", window=3)

        if len(peaks) < 3:
            return False

        # 最新の3つのピークを取得
        recent_peaks = peaks[-3:]

        # ピーク間の距離をチェック
        for i in range(len(recent_peaks) - 1):
            if recent_peaks[i + 1] - recent_peaks[i] < self.min_peak_distance:
                return False

        # ピークの高さが類似しているかチェック
        peak_heights = [price_data.iloc[peak]["High"] for peak in recent_peaks]
        base_height = peak_heights[0]

        for height in peak_heights[1:]:
            if abs(height - base_height) / base_height > self.peak_tolerance:
                return False

        # ネックラインの検証
        return self._validate_triple_neckline(price_data, recent_peaks, "top")

    def _detect_triple_bottom(self, price_data: pd.DataFrame) -> bool:
        """トリプルボトム検出"""
        if len(price_data) < 30:
            return False

        # 安値のピークを検出
        peaks = self._find_peaks(price_data, "Low", window=3)

        if len(peaks) < 3:
            return False

        # 最新の3つのピークを取得
        recent_peaks = peaks[-3:]

        # ピーク間の距離をチェック
        for i in range(len(recent_peaks) - 1):
            if recent_peaks[i + 1] - recent_peaks[i] < self.min_peak_distance:
                return False

        # ピークの高さが類似しているかチェック
        peak_heights = [price_data.iloc[peak]["Low"] for peak in recent_peaks]
        base_height = peak_heights[0]

        for height in peak_heights[1:]:
            if abs(height - base_height) / base_height > self.peak_tolerance:
                return False

        # ネックラインの検証
        return self._validate_triple_neckline(price_data, recent_peaks, "bottom")

    def _find_peaks(
        self, price_data: pd.DataFrame, column: str, window: int = 3
    ) -> List[int]:
        """ピーク検出"""
        peaks = []

        for i in range(window, len(price_data) - window):
            if column == "High":
                # 高値のピーク
                current_value = price_data.iloc[i][column]
                is_peak = True
                for j in range(i - window, i + window + 1):
                    if j != i and price_data.iloc[j][column] >= current_value:
                        is_peak = False
                        break
                if is_peak:
                    peaks.append(i)
            else:
                # 安値のピーク
                current_value = price_data.iloc[i][column]
                is_peak = True
                for j in range(i - window, i + window + 1):
                    if j != i and price_data.iloc[j][column] <= current_value:
                        is_peak = False
                        break
                if is_peak:
                    peaks.append(i)

        return peaks

    def _validate_triple_neckline(
        self, price_data: pd.DataFrame, peaks: List[int], pattern_type: str
    ) -> bool:
        """トリプルパターンのネックライン検証"""
        if len(peaks) < 3:
            return False

        # ピーク間の谷/山を検出
        valley_points = []

        for i in range(len(peaks) - 1):
            start_idx = peaks[i]
            end_idx = peaks[i + 1]

            if pattern_type == "top":
                # トリプルトップの場合、谷を検出
                valley_idx = price_data.iloc[start_idx:end_idx]["Low"].idxmin()
                valley_points.append(price_data.iloc[valley_idx]["Low"])
            else:
                # トリプルボトムの場合、山を検出
                valley_idx = price_data.iloc[start_idx:end_idx]["High"].idxmax()
                valley_points.append(price_data.iloc[valley_idx]["High"])

        # ネックラインの一貫性をチェック
        if len(valley_points) < 2:
            return False

        # ネックラインの傾きをチェック
        if len(valley_points) >= 2:
            slope = (valley_points[-1] - valley_points[0]) / len(valley_points)
            if abs(slope) > self.neckline_tolerance * price_data.iloc[-1]["Close"]:
                return False

        return True

    def _calculate_triple_pattern_confidence(
        self, conditions_met: Dict[str, bool]
    ) -> float:
        """トリプルパターン信頼度計算"""
        base_confidence = 0.85  # 基本信頼度85%

        # 各時間軸の重み
        timeframe_weights = {"D1": 0.4, "H4": 0.3, "H1": 0.2, "M5": 0.1}

        # 条件を満たした時間軸の重み付き合計
        weighted_sum = sum(
            timeframe_weights[timeframe]
            for timeframe, met in conditions_met.items()
            if met
        )

        # 信頼度を計算
        confidence = base_confidence * weighted_sum

        # 信頼度を0.6-0.95の範囲に制限
        return max(0.6, min(0.95, confidence))
