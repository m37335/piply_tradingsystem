#!/usr/bin/env python3
"""
Support Resistance Detector V4 (Pattern 15) - TA-Lib座標系版
座標系ベースのサポート/レジスタンスライン検出器

数学的アプローチ: 
- X軸: 時間（インデックス）
- Y軸: 価格（始値・終値）
- 1次関数: y = ax + b
- 点: (x, y) = (時間, 価格) with バッファ
- ライン: レジスタンスライン（上昇/下降）、サポートライン（上昇/下降）
"""

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from src.domain.entities.notification_pattern import (
    NotificationPattern,
    PatternPriority,
)
from src.utils.pattern_utils import PatternUtils

logger = logging.getLogger(__name__)


class SupportResistanceDetectorV4:
    """座標系ベースのサポート/レジスタンスライン検出器 V4（TA-Lib版）"""

    def __init__(self, timeframe: str = "5m"):
        self.pattern = NotificationPattern.create_pattern_15()
        self.utils = PatternUtils()
        self.timeframe = timeframe

        # 座標系パラメータ
        self._set_coordinate_parameters()

        # 検出パラメータ
        self._set_detection_parameters()

    def _set_coordinate_parameters(self):
        """座標系パラメータ設定"""
        # 点のバッファ設定
        self.point_buffer_percentile = 5  # 各点の周辺バッファ（パーセンタイル）
        self.min_points_for_line = 3  # ライン形成に必要な最小点数

        # 時間軸設定
        self.min_line_length = 10  # 最小ライン長（データポイント数）
        self.max_line_length = 200  # 最大ライン長（データポイント数）

    def _set_detection_parameters(self):
        """検出パラメータ設定"""
        # ライン強度
        self.min_line_strength = 0.3  # 最小ライン強度
        self.min_r_squared = 0.6  # 最小決定係数

        # 角度制限
        self.max_angle = 45  # 最大角度（度）
        self.min_angle = 0.1  # 最小角度（度）

        # 価格許容誤差
        self.price_tolerance = 0.005  # 価格許容誤差（0.5%）

        # 検出感度
        self.detection_sensitivity = 0.7  # 検出感度（0-1）

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """座標系ベースのサポート/レジスタンスライン検出"""
        try:
            if price_data is None or len(price_data) < self.min_line_length:
                return None

            logger.info(f"座標系ベース検出開始: {len(price_data)}件のデータ")

            # 座標系データの準備
            coordinates = self._prepare_coordinates(price_data)

            # 複数ライン検出
            all_lines = self._detect_multiple_lines(coordinates, price_data)

            if not all_lines:
                return None

            # 最適なラインを選択
            best_line = self._select_best_line(all_lines, price_data)

            if not best_line:
                return None

            # 検出結果を作成
            return self._create_detection_result(price_data, best_line)

        except Exception as e:
            logger.error(f"座標系ベース検出エラー: {e}")
            return None

    def _prepare_coordinates(self, price_data: pd.DataFrame) -> Dict[str, np.ndarray]:
        """座標系データの準備"""
        try:
            # 時間軸（X軸）: インデックス
            x_coordinates = np.arange(len(price_data))

            # 価格軸（Y軸）: 始値と終値
            open_prices = price_data["Open"].values
            close_prices = price_data["Close"].values
            high_prices = price_data["High"].values
            low_prices = price_data["Low"].values

            # バッファ付き極値点の検出
            resistance_points = self._find_resistance_points(high_prices, x_coordinates)
            support_points = self._find_support_points(low_prices, x_coordinates)

            return {
                "x": x_coordinates,
                "open": open_prices,
                "close": close_prices,
                "high": high_prices,
                "low": low_prices,
                "resistance_points": resistance_points,
                "support_points": support_points,
            }

        except Exception as e:
            logger.error(f"座標系データ準備エラー: {e}")
            return {}

    def _find_resistance_points(
        self, high_prices: np.ndarray, x_coordinates: np.ndarray
    ) -> List[Tuple[int, float]]:
        """レジスタンス点の検出（TA-Lib使用）"""
        try:
            # TA-Libでピーク検出
            peaks, _ = talib.find_peaks(
                high_prices, height=np.percentile(high_prices, 80), distance=5
            )

            # バッファ付き点の作成
            resistance_points = []
            for peak_idx in peaks:
                price = high_prices[peak_idx]
                x = x_coordinates[peak_idx]

                # バッファ計算
                buffer_threshold = np.percentile(
                    high_prices, 100 - self.point_buffer_percentile
                )
                if price >= buffer_threshold:
                    resistance_points.append((x, price))

            logger.info(f"レジスタンス点検出: {len(resistance_points)}点")
            return resistance_points

        except Exception as e:
            logger.error(f"レジスタンス点検出エラー: {e}")
            return []

    def _find_support_points(
        self, low_prices: np.ndarray, x_coordinates: np.ndarray
    ) -> List[Tuple[int, float]]:
        """サポート点の検出（TA-Lib使用）"""
        try:
            # TA-Libでピーク検出（極小値）
            troughs, _ = talib.find_peaks(
                -low_prices, height=-np.percentile(low_prices, 20), distance=5
            )

            # バッファ付き点の作成
            support_points = []
            for trough_idx in troughs:
                price = low_prices[trough_idx]
                x = x_coordinates[trough_idx]

                # バッファ計算
                buffer_threshold = np.percentile(
                    low_prices, self.point_buffer_percentile
                )
                if price <= buffer_threshold:
                    support_points.append((x, price))

            logger.info(f"サポート点検出: {len(support_points)}点")
            return support_points

        except Exception as e:
            logger.error(f"サポート点検出エラー: {e}")
            return []

    def _detect_multiple_lines(
        self, coordinates: Dict, price_data: pd.DataFrame
    ) -> List[Dict]:
        """複数ライン検出"""
        try:
            all_lines = []

            # レジスタンスライン検出
            resistance_lines = self._detect_resistance_lines(coordinates, price_data)
            all_lines.extend(resistance_lines)

            # サポートライン検出
            support_lines = self._detect_support_lines(coordinates, price_data)
            all_lines.extend(support_lines)

            logger.info(f"複数ライン検出完了: {len(all_lines)}本のライン")
            return all_lines

        except Exception as e:
            logger.error(f"複数ライン検出エラー: {e}")
            return []

    def _detect_resistance_lines(
        self, coordinates: Dict, price_data: pd.DataFrame
    ) -> List[Dict]:
        """レジスタンスライン検出"""
        try:
            lines = []
            resistance_points = coordinates["resistance_points"]

            if len(resistance_points) < self.min_points_for_line:
                return lines

            # 複数の点の組み合わせでライン検出
            for i in range(len(resistance_points)):
                for j in range(i + 1, len(resistance_points)):
                    line = self._calculate_line_from_points(
                        resistance_points[i],
                        resistance_points[j],
                        "resistance",
                        coordinates,
                        price_data,
                    )
                    if line:
                        lines.append(line)

            return lines

        except Exception as e:
            logger.error(f"レジスタンスライン検出エラー: {e}")
            return []

    def _detect_support_lines(
        self, coordinates: Dict, price_data: pd.DataFrame
    ) -> List[Dict]:
        """サポートライン検出"""
        try:
            lines = []
            support_points = coordinates["support_points"]

            if len(support_points) < self.min_points_for_line:
                return lines

            # 複数の点の組み合わせでライン検出
            for i in range(len(support_points)):
                for j in range(i + 1, len(support_points)):
                    line = self._calculate_line_from_points(
                        support_points[i],
                        support_points[j],
                        "support",
                        coordinates,
                        price_data,
                    )
                    if line:
                        lines.append(line)

            return lines

        except Exception as e:
            logger.error(f"サポートライン検出エラー: {e}")
            return []

    def _calculate_line_from_points(
        self,
        point1: Tuple[int, float],
        point2: Tuple[int, float],
        line_type: str,
        coordinates: Dict,
        price_data: pd.DataFrame,
    ) -> Optional[Dict]:
        """2点からラインを計算"""
        try:
            x1, y1 = point1
            x2, y2 = point2

            # ライン長チェック
            line_length = abs(x2 - x1)
            if line_length < self.min_line_length or line_length > self.max_line_length:
                return None

            # 1次関数の計算: y = ax + b
            if x2 - x1 == 0:  # 垂直線は除外
                return None

            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1

            # 角度計算
            angle = math.degrees(math.atan(slope))

            # 角度制限チェック
            if abs(angle) > self.max_angle or abs(angle) < self.min_angle:
                return None

            # ライン強度計算
            strength = self._calculate_line_strength(
                slope, intercept, coordinates, line_type
            )
            if strength < self.min_line_strength:
                return None

            # 決定係数計算
            r_squared = self._calculate_r_squared(
                slope, intercept, coordinates, line_type
            )
            if r_squared < self.min_r_squared:
                return None

            # 現在価格との関係分析
            current_analysis = self._analyze_current_price_relation(
                price_data, slope, intercept, line_type
            )

            return {
                "line_type": line_type,
                "points": [point1, point2],
                "equation": {
                    "slope": slope,
                    "intercept": intercept,
                    "angle": angle,
                    "r_squared": r_squared,
                },
                "strength": strength,
                "current_analysis": current_analysis,
                "line_length": line_length,
                "direction": "UP" if slope > 0 else "DOWN",
            }

        except Exception as e:
            logger.error(f"ライン計算エラー: {e}")
            return None

    def _calculate_line_strength(
        self, slope: float, intercept: float, coordinates: Dict, line_type: str
    ) -> float:
        """ライン強度計算"""
        try:
            x_coords = coordinates["x"]
            prices = (
                coordinates["high"] if line_type == "resistance" else coordinates["low"]
            )

            # ライン上の価格を計算
            line_prices = slope * x_coords + intercept

            # 実際の価格との一致度を計算
            if line_type == "resistance":
                # レジスタンス: 実際の価格がライン以下である割合
                valid_points = np.sum(
                    prices <= line_prices * (1 + self.price_tolerance)
                )
            else:
                # サポート: 実際の価格がライン以上である割合
                valid_points = np.sum(
                    prices >= line_prices * (1 - self.price_tolerance)
                )

            strength = valid_points / len(prices)
            return strength

        except Exception as e:
            logger.error(f"ライン強度計算エラー: {e}")
            return 0.0

    def _calculate_r_squared(
        self, slope: float, intercept: float, coordinates: Dict, line_type: str
    ) -> float:
        """決定係数計算"""
        try:
            x_coords = coordinates["x"]
            prices = (
                coordinates["high"] if line_type == "resistance" else coordinates["low"]
            )

            # ライン上の価格を計算
            line_prices = slope * x_coords + intercept

            # 決定係数計算
            ss_res = np.sum((prices - line_prices) ** 2)
            ss_tot = np.sum((prices - np.mean(prices)) ** 2)

            if ss_tot == 0:
                return 0.0

            r_squared = 1 - (ss_res / ss_tot)
            return r_squared

        except Exception as e:
            logger.error(f"決定係数計算エラー: {e}")
            return 0.0

    def _analyze_current_price_relation(
        self, price_data: pd.DataFrame, slope: float, intercept: float, line_type: str
    ) -> Dict:
        """現在価格との関係分析"""
        try:
            current_price = price_data["Close"].iloc[-1]
            current_x = len(price_data) - 1

            # 現在のライン価格を計算
            line_price = slope * current_x + intercept

            # 価格関係を分析
            if line_type == "resistance":
                if current_price > line_price:
                    relation = "ABOVE_RESISTANCE"
                    breakout_strength = (current_price - line_price) / line_price
                else:
                    relation = "BELOW_RESISTANCE"
                    breakout_strength = 0.0
            else:  # support
                if current_price < line_price:
                    relation = "BELOW_SUPPORT"
                    breakout_strength = (line_price - current_price) / line_price
                else:
                    relation = "ABOVE_SUPPORT"
                    breakout_strength = 0.0

            return {
                "current_price": current_price,
                "line_price": line_price,
                "relation": relation,
                "breakout_strength": breakout_strength,
                "distance": abs(current_price - line_price) / line_price,
            }

        except Exception as e:
            logger.error(f"現在価格関係分析エラー: {e}")
            return {}

    def _select_best_line(
        self, lines: List[Dict], price_data: pd.DataFrame
    ) -> Optional[Dict]:
        """最適なラインを選択"""
        try:
            if not lines:
                return None

            # スコアリング
            scored_lines = []
            for line in lines:
                score = self._calculate_line_score(line, price_data)
                scored_lines.append((score, line))

            # スコアでソート
            scored_lines.sort(key=lambda x: x[0], reverse=True)

            # 最適なラインを選択
            best_score, best_line = scored_lines[0]

            logger.info(
                f"最適ライン選択: {best_line['line_type']}, スコア: {best_score:.3f}"
            )
            return best_line

        except Exception as e:
            logger.error(f"最適ライン選択エラー: {e}")
            return None

    def _calculate_line_score(self, line: Dict, price_data: pd.DataFrame) -> float:
        """ラインスコア計算"""
        try:
            # 基本スコア
            base_score = line["strength"] * line["equation"]["r_squared"]

            # 角度ボーナス（水平に近いほど高スコア）
            angle = abs(line["equation"]["angle"])
            angle_bonus = 1.0 - (angle / self.max_angle)

            # ライン長ボーナス
            line_length = line["line_length"]
            length_bonus = min(line_length / 50.0, 1.0)

            # 現在価格関係ボーナス
            current_analysis = line["current_analysis"]
            if current_analysis.get("relation") in [
                "BELOW_RESISTANCE",
                "ABOVE_SUPPORT",
            ]:
                relation_bonus = 1.0
            else:
                relation_bonus = 0.5

            # 総合スコア
            total_score = base_score * angle_bonus * length_bonus * relation_bonus
            return total_score

        except Exception as e:
            logger.error(f"ラインスコア計算エラー: {e}")
            return 0.0

    def _create_detection_result(
        self, price_data: pd.DataFrame, line: Dict
    ) -> Dict[str, Any]:
        """検出結果作成"""
        try:
            # 信頼度計算
            confidence = self._calculate_confidence(line)

            # 戦略決定
            strategy = self._determine_strategy(line)

            # 方向決定
            direction = line["direction"]

            return {
                "pattern_type": f"{line['line_type']}_line",
                "confidence_score": confidence,
                "direction": direction,
                "strategy": strategy,
                "pattern_data": {
                    "line_type": line["line_type"],
                    "points": line["points"],
                    "equation": line["equation"],
                    "strength": line["strength"],
                    "current_analysis": line["current_analysis"],
                    "line_length": line["line_length"],
                    "timeframe": self.timeframe,
                },
                "timestamp": datetime.now().isoformat(),
                "priority": PatternPriority.MEDIUM,
            }

        except Exception as e:
            logger.error(f"検出結果作成エラー: {e}")
            return {}

    def _calculate_confidence(self, line: Dict) -> float:
        """信頼度計算"""
        try:
            # 基本信頼度
            base_confidence = line["strength"] * line["equation"]["r_squared"]

            # 角度補正
            angle = abs(line["equation"]["angle"])
            angle_factor = 1.0 - (angle / 90.0) * 0.3  # 角度が大きいほど信頼度低下

            # ライン長補正
            line_length = line["line_length"]
            length_factor = min(line_length / 100.0, 1.0)

            # 総合信頼度
            confidence = base_confidence * angle_factor * length_factor
            return min(confidence, 1.0)

        except Exception as e:
            logger.error(f"信頼度計算エラー: {e}")
            return 0.0

    def _determine_strategy(self, line: Dict) -> str:
        """戦略決定"""
        try:
            line_type = line["line_type"]
            current_analysis = line["current_analysis"]
            relation = current_analysis.get("relation", "")

            if line_type == "resistance":
                if relation == "ABOVE_RESISTANCE":
                    return "SELL_BREAKOUT"
                else:
                    return "SELL_AT_RESISTANCE"
            else:  # support
                if relation == "BELOW_SUPPORT":
                    return "BUY_BREAKDOWN"
                else:
                    return "BUY_AT_SUPPORT"

        except Exception as e:
            logger.error(f"戦略決定エラー: {e}")
            return "HOLD"
