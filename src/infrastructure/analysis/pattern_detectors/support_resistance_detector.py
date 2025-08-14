#!/usr/bin/env python3
"""
Support Resistance Detector (Pattern 15)
レジスタンス/サポートライン検出器

価格の重要な支え・抵抗レベルを検出するパターン
"""

import logging
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


class SupportResistanceDetector:
    """レジスタンス/サポートライン検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_15()
        self.utils = PatternUtils()
        self.min_touch_points = 1  # 最小タッチポイント数（2→1に緩和）
        self.line_tolerance = 0.1  # ラインの許容誤差（5%→10%にさらに緩和）
        self.breakout_threshold = 0.0001  # ブレイクアウト閾値（0.05%→0.01%に大幅緩和）
        self.confirmation_candles = 0  # 確認ローソク足数（1→0に緩和）

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """レジスタンス/サポートライン検出"""
        try:
            if price_data is None or len(price_data) < 30:
                return None

            # レンジ相場（行き来する現象）の検出を優先
            range_pattern = self._detect_range_pattern(price_data)
            if range_pattern:
                return self._create_detection_result(
                    price_data, "range_pattern", range_pattern
                )

            # レジスタンスライン検出
            resistance_line = self._detect_resistance_line(price_data)
            if resistance_line:
                return self._create_detection_result(
                    price_data, "resistance_line", resistance_line
                )

            # サポートライン検出
            support_line = self._detect_support_line(price_data)
            if support_line:
                return self._create_detection_result(
                    price_data, "support_line", support_line
                )

            return None

        except Exception as e:
            logger.error(f"レジスタンス/サポートライン検出エラー: {e}")
            return None

    def _detect_range_pattern(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """レンジ相場（行き来する現象）検出"""
        try:
            # レジスタンスラインとサポートラインの両方を検出（緩和された条件で）
            resistance_line = self._detect_resistance_line_for_range(price_data)
            support_line = self._detect_support_line_for_range(price_data)

            if not resistance_line or not support_line:
                return None

            # レンジの幅を計算
            resistance_price = resistance_line["line_data"]["intercept"]
            support_price = support_line["line_data"]["intercept"]
            range_width = abs(resistance_price - support_price) / support_price

            # レンジ幅が適切な範囲内かチェック（3%～25%に緩和）
            if range_width < 0.03 or range_width > 0.25:
                return None

            # 価格がレンジ内で行き来しているかをチェック
            price_oscillations = self._check_price_oscillations(
                price_data, resistance_price, support_price
            )

            if not price_oscillations:
                return None

            # レンジ相場の強度を計算
            range_strength = self._calculate_range_strength(
                price_data, resistance_line, support_line, price_oscillations
            )

            return {
                "pattern_type": "range_pattern",
                "resistance_line": resistance_line,
                "support_line": support_line,
                "range_width": range_width,
                "oscillations": price_oscillations,
                "strength": range_strength,
                "direction": "NEUTRAL",  # レンジ相場は中立
            }

        except Exception as e:
            logger.error(f"レンジ相場検出エラー: {e}")
            return None

    def _detect_resistance_line_for_range(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """レンジ相場用のレジスタンスライン検出（緩和版）"""
        try:
            # タッチポイント検出
            touch_points = self._find_touch_points(price_data, "resistance")
            if len(touch_points) < 1:  # 最小要件を1に緩和
                return None

            # ライン方程式計算
            line_data = self._calculate_line_equation(touch_points, price_data, "High")
            if line_data is None:
                return None

            # ライン強度検証（緩和）
            strength = self._validate_line_strength(touch_points, line_data)
            if strength < 0.005:  # 強度要件を0.5%に緩和
                return None

            # ブレイクアウト検出（緩和）
            breakout = self._detect_breakout_for_range(
                price_data, line_data, "resistance"
            )
            if not breakout:
                return None

            return {
                "line_type": "resistance",
                "touch_points": touch_points,
                "line_data": line_data,
                "strength": strength,
                "breakout": breakout,
                "direction": "SELL",
            }

        except Exception as e:
            logger.error(f"レンジ用レジスタンスライン検出エラー: {e}")
            return None

    def _detect_support_line_for_range(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """レンジ相場用のサポートライン検出（緩和版）"""
        try:
            # タッチポイント検出
            touch_points = self._find_touch_points(price_data, "support")
            if len(touch_points) < 1:  # 最小要件を1に緩和
                return None

            # ライン方程式計算
            line_data = self._calculate_line_equation(touch_points, price_data, "Low")
            if line_data is None:
                return None

            # ライン強度検証（緩和）
            strength = self._validate_line_strength(touch_points, line_data)
            if strength < 0.005:  # 強度要件を0.5%に緩和
                return None

            # ブレイクアウト検出（緩和）
            breakout = self._detect_breakout_for_range(price_data, line_data, "support")
            if not breakout:
                return None

            return {
                "line_type": "support",
                "touch_points": touch_points,
                "line_data": line_data,
                "strength": strength,
                "breakout": breakout,
                "direction": "BUY",
            }

        except Exception as e:
            logger.error(f"レンジ用サポートライン検出エラー: {e}")
            return None

    def _detect_breakout_for_range(
        self, price_data: pd.DataFrame, line_data: Dict, line_type: str
    ) -> Optional[Dict[str, Any]]:
        """レンジ相場用のブレイクアウト検出（緩和版）"""
        try:
            slope = line_data["slope"]
            intercept = line_data["intercept"]

            # 最新の価格でブレイクアウトをチェック
            current_index = len(price_data) - 1
            current_price = price_data.iloc[-1]["Close"]

            # ライン上の価格を計算
            line_price = slope * current_index + intercept

            # 価格がラインの10%以内にあれば有効（5%から緩和）
            if abs(current_price - line_price) / line_price < 0.10:
                return {
                    "type": "near_line",
                    "strength": abs(current_price - line_price) / line_price,
                    "line_price": line_price,
                    "current_price": current_price,
                    "confirmed": True,
                }

            return None

        except Exception as e:
            logger.error(f"レンジ用ブレイクアウト検出エラー: {e}")
            return None

    def _check_price_oscillations(
        self, price_data: pd.DataFrame, resistance_price: float, support_price: float
    ) -> Dict[str, Any]:
        """価格の行き来現象をチェック"""
        try:
            oscillations = {
                "resistance_touches": 0,
                "support_touches": 0,
                "crossings": 0,
                "is_valid": False,
            }

            # レンジの中心価格
            center_price = (resistance_price + support_price) / 2
            range_tolerance = (
                abs(resistance_price - support_price) * 0.1
            )  # 10%の許容範囲

            # 価格の行き来を分析
            for i in range(len(price_data)):
                high = price_data.iloc[i]["High"]
                low = price_data.iloc[i]["Low"]
                close = price_data.iloc[i]["Close"]

                # レジスタンスゾーンへのタッチ
                if high >= resistance_price - range_tolerance:
                    oscillations["resistance_touches"] += 1

                # サポートゾーンへのタッチ
                if low <= support_price + range_tolerance:
                    oscillations["support_touches"] += 1

                # 中心価格をまたぐ回数
                if i > 0:
                    prev_close = price_data.iloc[i - 1]["Close"]
                    if (prev_close < center_price and close > center_price) or (
                        prev_close > center_price and close < center_price
                    ):
                        oscillations["crossings"] += 1

            # 有効な行き来現象の条件
            min_touches = 3  # 最低3回のタッチ
            min_crossings = 2  # 最低2回の中心価格クロス

            if (
                oscillations["resistance_touches"] >= min_touches
                and oscillations["support_touches"] >= min_touches
                and oscillations["crossings"] >= min_crossings
            ):
                oscillations["is_valid"] = True

            return oscillations

        except Exception as e:
            logger.error(f"価格行き来チェックエラー: {e}")
            return {"is_valid": False}

    def _calculate_range_strength(
        self,
        price_data: pd.DataFrame,
        resistance_line: Dict,
        support_line: Dict,
        oscillations: Dict,
    ) -> float:
        """レンジ相場の強度計算"""
        try:
            # レジスタンスラインの強度
            resistance_strength = resistance_line.get("strength", 0.0)

            # サポートラインの強度
            support_strength = support_line.get("strength", 0.0)

            # 行き来の頻度
            total_touches = (
                oscillations["resistance_touches"] + oscillations["support_touches"]
            )
            oscillation_frequency = min(total_touches / 20.0, 1.0)  # 20回で最大1.0

            # クロス回数の正規化
            crossing_frequency = min(
                oscillations["crossings"] / 10.0, 1.0
            )  # 10回で最大1.0

            # 総合強度計算
            strength = (
                resistance_strength * 0.3
                + support_strength * 0.3
                + oscillation_frequency * 0.2
                + crossing_frequency * 0.2
            )

            return min(strength, 1.0)

        except Exception as e:
            logger.error(f"レンジ強度計算エラー: {e}")
            return 0.0

    def _detect_resistance_line(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """レジスタンスライン検出"""
        try:
            # タッチポイント検出
            touch_points = self._find_touch_points(price_data, "resistance")
            if len(touch_points) < self.min_touch_points:
                return None

            # ライン方程式計算
            line_data = self._calculate_line_equation(touch_points, price_data, "High")
            if line_data is None:
                return None

            # ライン強度検証
            strength = self._validate_line_strength(touch_points, line_data)
            if strength < 0.01:  # 強度が1%未満の場合は無効（5%→1%に大幅緩和）
                return None

            # ブレイクアウト検出
            breakout = self._detect_breakout(price_data, line_data, "resistance")
            if not breakout:
                return None

            return {
                "line_type": "resistance",
                "touch_points": touch_points,
                "line_data": line_data,
                "strength": strength,
                "breakout": breakout,
                "direction": "SELL",
            }

        except Exception as e:
            logger.error(f"レジスタンスライン検出エラー: {e}")
            return None

    def _detect_support_line(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """サポートライン検出"""
        try:
            # タッチポイント検出
            touch_points = self._find_touch_points(price_data, "support")
            if len(touch_points) < self.min_touch_points:
                return None

            # ライン方程式計算
            line_data = self._calculate_line_equation(touch_points, price_data, "Low")
            if line_data is None:
                return None

            # ライン強度検証
            strength = self._validate_line_strength(touch_points, line_data)
            if strength < 0.01:  # 強度が1%未満の場合は無効（5%→1%に大幅緩和）
                return None

            # ブレイクアウト検出
            breakout = self._detect_breakout(price_data, line_data, "support")
            if not breakout:
                return None

            return {
                "line_type": "support",
                "touch_points": touch_points,
                "line_data": line_data,
                "strength": strength,
                "breakout": breakout,
                "direction": "BUY",
            }

        except Exception as e:
            logger.error(f"サポートライン検出エラー: {e}")
            return None

    def _find_touch_points(self, price_data: pd.DataFrame, line_type: str) -> List[int]:
        """タッチポイント検出"""
        try:
            touch_points = []

            if line_type == "resistance":
                # レジスタンスライン: 高値の上位30%を検出（20%→30%に拡大）
                high_values = price_data["High"].values
                threshold = np.percentile(high_values, 70)  # 上位30%

                for i in range(len(price_data)):
                    if price_data.iloc[i]["High"] >= threshold:
                        touch_points.append(i)
            else:
                # サポートライン: 安値の下位30%を検出（20%→30%に拡大）
                low_values = price_data["Low"].values
                threshold = np.percentile(low_values, 30)  # 下位30%

                for i in range(len(price_data)):
                    if price_data.iloc[i]["Low"] <= threshold:
                        touch_points.append(i)

            return touch_points

        except Exception as e:
            logger.error(f"タッチポイント検出エラー: {e}")
            return []

    def _calculate_line_equation(
        self, touch_points: List[int], price_data: pd.DataFrame, column: str
    ) -> Optional[Dict[str, float]]:
        """ライン方程式計算"""
        try:
            if len(touch_points) < 2:
                return None

            # タッチポイントの価格を取得
            x = np.array(touch_points)
            y = np.array([price_data.iloc[point][column] for point in touch_points])

            if len(set(y)) < 2:
                return None

            # 線形回帰でライン方程式を計算
            slope, intercept = np.polyfit(x, y, 1)

            # 水平ラインの場合は傾きを0に近づける
            if abs(slope) < 0.001:
                slope = 0.0
                intercept = np.mean(y)

            return {
                "slope": slope,
                "intercept": intercept,
                "touch_points": touch_points,
                "prices": y.tolist(),
            }

        except Exception as e:
            logger.error(f"ライン方程式計算エラー: {e}")
            return None

    def _validate_line_strength(
        self, touch_points: List[int], line_data: Dict
    ) -> float:
        """ライン強度検証"""
        try:
            if len(touch_points) < 2:
                return 0.0

            # タッチポイント間の距離をチェック
            distances = []
            for i in range(len(touch_points) - 1):
                distance = touch_points[i + 1] - touch_points[i]
                distances.append(distance)

            # 距離の一貫性をチェック
            if len(distances) > 1:
                avg_distance = np.mean(distances)
                distance_variance = np.var(distances)
                distance_consistency = 1.0 / (1.0 + distance_variance / avg_distance)
            else:
                distance_consistency = 1.0

            # 価格の一貫性をチェック
            prices = line_data.get("prices", [])
            if len(prices) > 1:
                price_variance = np.var(prices)
                avg_price = np.mean(prices)
                price_consistency = 1.0 / (1.0 + price_variance / avg_price)
            else:
                price_consistency = 1.0

            # タッチポイント数のボーナス
            point_bonus = min(len(touch_points) / 5.0, 1.0)

            # 総合強度計算
            strength = (
                distance_consistency * 0.4 + price_consistency * 0.4 + point_bonus * 0.2
            )

            return min(strength, 1.0)

        except Exception as e:
            logger.error(f"ライン強度検証エラー: {e}")
            return 0.0

    def _detect_breakout(
        self, price_data: pd.DataFrame, line_data: Dict, line_type: str
    ) -> Optional[Dict[str, Any]]:
        """ブレイクアウト検出"""
        try:
            slope = line_data["slope"]
            intercept = line_data["intercept"]

            # 最新の価格でブレイクアウトをチェック
            current_index = len(price_data) - 1
            current_price = price_data.iloc[-1]["Close"]

            # ライン上の価格を計算
            line_price = slope * current_index + intercept

            breakout_type = None
            breakout_strength = 0.0

            if line_type == "resistance":
                # レジスタンスラインのブレイクアウト
                if current_price > line_price:
                    # 上向きブレイクアウト
                    breakout_type = "bullish"
                    breakout_strength = (current_price - line_price) / line_price
            else:
                # サポートラインのブレイクアウト
                if current_price < line_price:
                    # 下向きブレイクアウト
                    breakout_type = "bearish"
                    breakout_strength = (line_price - current_price) / line_price

            # ブレイクアウト強度が閾値を超える場合、または価格がラインに近い場合に有効
            if breakout_type and breakout_strength > self.breakout_threshold:
                # 確認ローソク足をチェック（0の場合はスキップ）
                if self.confirmation_candles == 0 or self._confirm_breakout(
                    price_data, line_data, line_type, breakout_type
                ):
                    return {
                        "type": breakout_type,
                        "strength": breakout_strength,
                        "line_price": line_price,
                        "current_price": current_price,
                        "confirmed": True,
                    }
            elif (
                abs(current_price - line_price) / line_price < 0.05
            ):  # 価格がラインの5%以内
                # 価格がラインに近い場合も検出
                return {
                    "type": "near_line",
                    "strength": abs(current_price - line_price) / line_price,
                    "line_price": line_price,
                    "current_price": current_price,
                    "confirmed": True,
                }

            return None

        except Exception as e:
            logger.error(f"ブレイクアウト検出エラー: {e}")
            return None

    def _confirm_breakout(
        self,
        price_data: pd.DataFrame,
        line_data: Dict,
        line_type: str,
        breakout_type: str,
    ) -> bool:
        """ブレイクアウト確認"""
        try:
            slope = line_data["slope"]
            intercept = line_data["intercept"]

            # 確認ローソク足をチェック
            for i in range(1, self.confirmation_candles + 1):
                if i >= len(price_data):
                    break

                index = len(price_data) - i
                price = price_data.iloc[index]["Close"]
                line_price = slope * index + intercept

                if line_type == "resistance":
                    if breakout_type == "bullish":
                        # 上向きブレイクアウトの確認
                        if price <= line_price:
                            return False
                else:
                    if breakout_type == "bearish":
                        # 下向きブレイクアウトの確認
                        if price >= line_price:
                            return False

            return True

        except Exception as e:
            logger.error(f"ブレイクアウト確認エラー: {e}")
            return False

    def _calculate_support_resistance_confidence(self, pattern_data: Dict) -> float:
        """レジスタンス/サポートライン信頼度計算"""
        try:
            base_confidence = 0.80

            # レンジ相場パターンの場合
            if pattern_data.get("pattern_type") == "range_pattern":
                # レンジ相場は信頼度が高い
                base_confidence = 0.85

                # レンジ強度による調整
                strength = pattern_data.get("strength", 0.0)
                if strength > 0.9:
                    base_confidence += 0.10
                elif strength > 0.8:
                    base_confidence += 0.07
                elif strength > 0.7:
                    base_confidence += 0.05

                # 行き来の頻度による調整
                oscillations = pattern_data.get("oscillations", {})
                total_touches = oscillations.get(
                    "resistance_touches", 0
                ) + oscillations.get("support_touches", 0)
                if total_touches >= 10:
                    base_confidence += 0.05
                elif total_touches >= 6:
                    base_confidence += 0.03

                # クロス回数による調整
                crossings = oscillations.get("crossings", 0)
                if crossings >= 5:
                    base_confidence += 0.05
                elif crossings >= 3:
                    base_confidence += 0.03

                return min(base_confidence, 0.95)

            # 通常のレジスタンス/サポートラインの場合
            # ラインタイプによる調整
            if pattern_data.get("line_type") == "resistance":
                base_confidence += 0.05
            elif pattern_data.get("line_type") == "support":
                base_confidence += 0.03

            # ライン強度による調整
            strength = pattern_data.get("strength", 0.0)
            if strength > 0.9:
                base_confidence += 0.08
            elif strength > 0.8:
                base_confidence += 0.05
            elif strength > 0.7:
                base_confidence += 0.03

            # タッチポイント数による調整
            touch_points = pattern_data.get("touch_points", [])
            if len(touch_points) >= 5:
                base_confidence += 0.05
            elif len(touch_points) >= 4:
                base_confidence += 0.03
            elif len(touch_points) >= 3:
                base_confidence += 0.02

            # ブレイクアウト強度による調整
            breakout = pattern_data.get("breakout", {})
            if breakout:
                strength = breakout.get("strength", 0)
                if strength > 0.02:  # 2%以上
                    base_confidence += 0.05
                elif strength > 0.01:  # 1%以上
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
            confidence = self._calculate_support_resistance_confidence(pattern_data)

            # パターン名と戦略の決定
            if pattern_type == "range_pattern":
                pattern_name = "レンジ相場"
                strategy = "レンジ内トレード"
                description = "価格が一定範囲内で行き来する現象を検出"
            elif pattern_type == "resistance_line":
                pattern_name = "レジスタンスライン"
                strategy = "売りシグナル"
                description = "価格の重要な抵抗レベルを検出"
            else:
                pattern_name = "サポートライン"
                strategy = "買いシグナル"
                description = "価格の重要な支えレベルを検出"

            result = {
                "pattern_number": 15,
                "pattern_name": f"レジスタンス/サポートライン検出 ({pattern_name})",
                "priority": PatternPriority.HIGH,
                "confidence_score": confidence,
                "detection_time": datetime.now().isoformat(),
                "notification_title": f"🔄 {pattern_name}検出！",
                "notification_color": "0x32CD32",
                "strategy": strategy,
                "entry_condition": (
                    "ブレイクアウト確認"
                    if pattern_type != "range_pattern"
                    else "レンジ内トレード"
                ),
                "current_price": current_price,
                "pattern_type": pattern_type,
                "pattern_data": pattern_data,
                "direction": pattern_data.get(
                    "direction",
                    (
                        "NEUTRAL"
                        if pattern_type == "range_pattern"
                        else ("SELL" if pattern_type == "resistance_line" else "BUY")
                    ),
                ),
                "description": description,
            }

            return result

        except Exception as e:
            logger.error(f"検出結果作成エラー: {e}")
            return None

        except Exception as e:
            logger.error(f"検出結果作成エラー: {e}")
            return None
