#!/usr/bin/env python3
"""
Wedge Pattern Detector (Pattern 14)
ウェッジパターン検出器

収束するトレンドラインで形成されるパターンを検出
"""

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.domain.entities.notification_pattern import (
    NotificationPattern,
    PatternPriority,
)
from src.utils.pattern_utils import PatternUtils

logger = logging.getLogger(__name__)


class WedgePatternDetector:
    """ウェッジパターン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_14()
        self.utils = PatternUtils()
        self.min_wedge_length = 10  # ウェッジの最小長さ
        self.max_wedge_length = 50  # ウェッジの最大長さ
        self.angle_tolerance = 15  # 角度の許容誤差（度）
        self.convergence_threshold = 0.8  # 収束判定閾値
        self.min_touch_points = 3  # 最小タッチポイント数

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """ウェッジパターン検出"""
        try:
            if price_data is None or len(price_data) < 30:
                return None

            # 上昇ウェッジ検出
            rising_wedge = self._detect_rising_wedge(price_data)
            if rising_wedge:
                return self._create_detection_result(
                    price_data, "rising_wedge", rising_wedge
                )

            # 下降ウェッジ検出
            falling_wedge = self._detect_falling_wedge(price_data)
            if falling_wedge:
                return self._create_detection_result(
                    price_data, "falling_wedge", falling_wedge
                )

            return None

        except Exception as e:
            logger.error(f"ウェッジパターン検出エラー: {e}")
            return None

    def _detect_rising_wedge(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """上昇ウェッジ検出"""
        try:
            # ウェッジライン識別
            wedge_lines = self._identify_wedge_lines(price_data, is_rising=True)
            if not wedge_lines:
                return None

            # 収束チェック
            if not self._check_convergence(wedge_lines):
                return None

            # ブレイクアウト検証
            breakout = self._validate_wedge_breakout(price_data, wedge_lines)
            if not breakout:
                return None

            return {
                "pattern_type": "rising_wedge",
                "wedge_lines": wedge_lines,
                "breakout": breakout,
                "direction": "SELL",
            }

        except Exception as e:
            logger.error(f"上昇ウェッジ検出エラー: {e}")
            return None

    def _detect_falling_wedge(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """下降ウェッジ検出"""
        try:
            # ウェッジライン識別
            wedge_lines = self._identify_wedge_lines(price_data, is_rising=False)
            if not wedge_lines:
                return None

            # 収束チェック
            if not self._check_convergence(wedge_lines):
                return None

            # ブレイクアウト検証
            breakout = self._validate_wedge_breakout(price_data, wedge_lines)
            if not breakout:
                return None

            return {
                "pattern_type": "falling_wedge",
                "wedge_lines": wedge_lines,
                "breakout": breakout,
                "direction": "BUY",
            }

        except Exception as e:
            logger.error(f"下降ウェッジ検出エラー: {e}")
            return None

    def _identify_wedge_lines(
        self, price_data: pd.DataFrame, is_rising: bool
    ) -> Optional[Dict[str, Any]]:
        """ウェッジライン識別"""
        try:
            # ピークとボトムを検出
            if is_rising:
                # 上昇ウェッジ: 上昇する高値と上昇する安値
                highs = self._find_peaks(price_data, "High")
                lows = self._find_peaks(price_data, "Low")
            else:
                # 下降ウェッジ: 下降する高値と下降する安値
                highs = self._find_peaks(price_data, "High")
                lows = self._find_peaks(price_data, "Low")

            if len(highs) < self.min_touch_points or len(lows) < self.min_touch_points:
                return None

            # トレンドラインを計算
            upper_line = self._calculate_trend_line(price_data, highs, "High")
            lower_line = self._calculate_trend_line(price_data, lows, "Low")

            if upper_line is None or lower_line is None:
                return None

            # ラインの角度を計算
            upper_angle = self._calculate_line_angle(upper_line)
            lower_angle = self._calculate_line_angle(lower_line)

            return {
                "upper_line": upper_line,
                "lower_line": lower_line,
                "upper_angle": upper_angle,
                "lower_angle": lower_angle,
                "highs": highs,
                "lows": lows,
            }

        except Exception as e:
            logger.error(f"ウェッジライン識別エラー: {e}")
            return None

    def _find_peaks(self, price_data: pd.DataFrame, column: str) -> List[int]:
        """ピーク/ボトム検出"""
        try:
            peaks = []
            for i in range(2, len(price_data) - 2):
                if column == "High":
                    # 高値のピーク検出
                    if (
                        price_data.iloc[i][column] > price_data.iloc[i - 1][column]
                        and price_data.iloc[i][column] > price_data.iloc[i - 2][column]
                        and price_data.iloc[i][column] > price_data.iloc[i + 1][column]
                        and price_data.iloc[i][column] > price_data.iloc[i + 2][column]
                    ):
                        peaks.append(i)
                else:
                    # 安値のボトム検出
                    if (
                        price_data.iloc[i][column] < price_data.iloc[i - 1][column]
                        and price_data.iloc[i][column] < price_data.iloc[i - 2][column]
                        and price_data.iloc[i][column] < price_data.iloc[i + 1][column]
                        and price_data.iloc[i][column] < price_data.iloc[i + 2][column]
                    ):
                        peaks.append(i)

            return peaks

        except Exception as e:
            logger.error(f"ピーク検出エラー: {e}")
            return []

    def _calculate_trend_line(
        self, price_data: pd.DataFrame, points: List[int], column: str
    ) -> Optional[Dict[str, float]]:
        """トレンドライン計算"""
        try:
            if len(points) < 2:
                return None

            # 線形回帰でトレンドラインを計算
            x = np.array(points)
            y = np.array([price_data.iloc[point][column] for point in points])

            if len(set(y)) < 2:
                return None

            # 線形回帰
            slope, intercept = np.polyfit(x, y, 1)

            return {"slope": slope, "intercept": intercept, "points": points}

        except Exception as e:
            logger.error(f"トレンドライン計算エラー: {e}")
            return None

    def _calculate_line_angle(self, line: Dict[str, float]) -> float:
        """ライン角度計算"""
        try:
            slope = line["slope"]
            angle = math.degrees(math.atan(slope))
            return angle

        except Exception as e:
            logger.error(f"角度計算エラー: {e}")
            return 0.0

    def _check_convergence(self, wedge_lines: Dict[str, Any]) -> bool:
        """収束チェック"""
        try:
            upper_angle = wedge_lines["upper_angle"]
            lower_angle = wedge_lines["lower_angle"]

            # 角度の差を計算
            angle_diff = abs(upper_angle - lower_angle)

            # 収束判定
            if angle_diff < self.angle_tolerance:
                return True

            # スロープの収束チェック
            upper_slope = wedge_lines["upper_line"]["slope"]
            lower_slope = wedge_lines["lower_line"]["slope"]

            # 上昇ウェッジの場合、上側のスロープが下側より緩い
            if upper_slope < lower_slope:
                slope_ratio = upper_slope / lower_slope if lower_slope != 0 else 0
                return slope_ratio > self.convergence_threshold

            return False

        except Exception as e:
            logger.error(f"収束チェックエラー: {e}")
            return False

    def _validate_wedge_breakout(
        self, price_data: pd.DataFrame, wedge_lines: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """ウェッジブレイクアウト検証"""
        try:
            upper_line = wedge_lines["upper_line"]
            lower_line = wedge_lines["lower_line"]

            # 最新の価格でブレイクアウトをチェック
            current_price = price_data.iloc[-1]["Close"]
            current_index = len(price_data) - 1

            # 上側ラインの価格を計算
            upper_price = upper_line["slope"] * current_index + upper_line["intercept"]
            # 下側ラインの価格を計算
            lower_price = lower_line["slope"] * current_index + lower_line["intercept"]

            # ブレイクアウト判定
            breakout_type = None
            breakout_strength = 0.0

            if current_price > upper_price:
                # 上側ブレイクアウト
                breakout_type = "upper"
                breakout_strength = (current_price - upper_price) / upper_price
            elif current_price < lower_price:
                # 下側ブレイクアウト
                breakout_type = "lower"
                breakout_strength = (lower_price - current_price) / lower_price

            if breakout_type and breakout_strength > 0.005:  # 0.5%以上のブレイクアウト
                return {
                    "type": breakout_type,
                    "strength": breakout_strength,
                    "upper_price": upper_price,
                    "lower_price": lower_price,
                    "current_price": current_price,
                }

            return None

        except Exception as e:
            logger.error(f"ブレイクアウト検証エラー: {e}")
            return None

    def _calculate_wedge_confidence(self, pattern_data: Dict) -> float:
        """ウェッジパターン信頼度計算"""
        try:
            base_confidence = 0.80

            # パターンタイプによる調整
            if pattern_data.get("pattern_type") == "rising_wedge":
                base_confidence += 0.05
            elif pattern_data.get("pattern_type") == "falling_wedge":
                base_confidence += 0.03

            # 収束度による調整
            wedge_lines = pattern_data.get("wedge_lines", {})
            if wedge_lines:
                upper_angle = wedge_lines.get("upper_angle", 0)
                lower_angle = wedge_lines.get("lower_angle", 0)
                angle_diff = abs(upper_angle - lower_angle)

                if angle_diff < 10:
                    base_confidence += 0.08
                elif angle_diff < 15:
                    base_confidence += 0.05
                elif angle_diff < 20:
                    base_confidence += 0.03

            # ブレイクアウト強度による調整
            breakout = pattern_data.get("breakout", {})
            if breakout:
                strength = breakout.get("strength", 0)
                if strength > 0.01:  # 1%以上
                    base_confidence += 0.05
                elif strength > 0.005:  # 0.5%以上
                    base_confidence += 0.03

            # タッチポイント数による調整
            highs = wedge_lines.get("highs", [])
            lows = wedge_lines.get("lows", [])
            touch_points = len(highs) + len(lows)

            if touch_points >= 8:
                base_confidence += 0.05
            elif touch_points >= 6:
                base_confidence += 0.03

            return min(base_confidence, 0.90)

        except Exception as e:
            logger.error(f"信頼度計算エラー: {e}")
            return 0.80

    def _create_detection_result(
        self, price_data: pd.DataFrame, pattern_type: str, pattern_data: Dict
    ) -> Dict[str, Any]:
        """検出結果作成"""
        try:
            current_price = price_data.iloc[-1]["Close"]
            confidence = self._calculate_wedge_confidence(pattern_data)

            # パターン名の決定
            if pattern_type == "rising_wedge":
                pattern_name = "上昇ウェッジ"
                strategy = "売りシグナル"
            else:
                pattern_name = "下降ウェッジ"
                strategy = "買いシグナル"

            result = {
                "pattern_number": 14,
                "pattern_name": f"ウェッジパターン検出 ({pattern_name})",
                "priority": PatternPriority.HIGH,
                "confidence_score": confidence,
                "detection_time": datetime.now().isoformat(),
                "notification_title": f"🔄 {pattern_name}パターン検出！",
                "notification_color": "0xFF8C00",
                "strategy": strategy,
                "entry_condition": "ブレイクアウト確認",
                "current_price": current_price,
                "pattern_type": pattern_type,
                "pattern_data": pattern_data,
                "direction": pattern_data.get("direction", "SELL" if pattern_type == "rising_wedge" else "BUY"),
                "description": f"収束するトレンドラインで形成される{pattern_name}パターン",
            }

            return result

        except Exception as e:
            logger.error(f"検出結果作成エラー: {e}")
            return None
