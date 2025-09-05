#!/usr/bin/env python3
"""
Support Resistance Detector V3 (Pattern 15) - 時間足別最適化版
角度付きサポート/レジスタンスライン検出器

数学的アプローチ: y = ax + b の1次関数として表現される重要な価格レベルを検出
時間足別最適化: 各時間足に最適化されたパラメータで検出
バッファ付き極値: 価格の極値をバッファ付きで検出
"""

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.signal import find_peaks

from src.domain.entities.notification_pattern import (
    NotificationPattern,
    PatternPriority,
)
from src.utils.pattern_utils import PatternUtils

logger = logging.getLogger(__name__)


class SupportResistanceDetectorV3:
    """角度付きサポート/レジスタンスライン検出器 V3（時間足別最適化版）"""

    def __init__(self, timeframe: str = "5m"):
        self.pattern = NotificationPattern.create_pattern_15()
        self.utils = PatternUtils()
        self.timeframe = timeframe

        # 時間足別パラメータ設定
        self._set_timeframe_parameters()

    def _set_timeframe_parameters(self):
        """時間足別パラメータ設定"""
        if self.timeframe == "5m":
            # 5分足: 短期的な価格レベル
            self.min_peaks = 2
            self.analysis_period = 60  # 5時間
            self.buffer_percentile = 20  # 上位/下位20%
            self.min_line_strength = 0.4
            self.max_angle = 45  # より急な角度も許容
            self.price_tolerance = 0.005  # 0.5%
            self.min_line_length = 5
        elif self.timeframe == "1h":
            # 1時間足: 中期的なトレンドライン
            self.min_peaks = 3
            self.analysis_period = 168  # 1週間
            self.buffer_percentile = 15  # 上位/下位15%
            self.min_line_strength = 0.6
            self.max_angle = 30
            self.price_tolerance = 0.003  # 0.3%
            self.min_line_length = 10
        elif self.timeframe == "1d":
            # 日足: 長期的な重要なレベル
            self.min_peaks = 4
            self.analysis_period = 60  # 2ヶ月
            self.buffer_percentile = 10  # 上位/下位10%
            self.min_line_strength = 0.8
            self.max_angle = 20
            self.price_tolerance = 0.002  # 0.2%
            self.min_line_length = 15
        else:
            # デフォルト（5分足相当）
            self.min_peaks = 2
            self.analysis_period = 60
            self.buffer_percentile = 20
            self.min_line_strength = 0.4
            self.max_angle = 45
            self.price_tolerance = 0.005
            self.min_line_length = 5

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """角度付きサポート/レジスタンスライン検出"""
        try:
            if price_data is None or len(price_data) < self.analysis_period:
                return None

            # 分析期間を制限
            analysis_data = price_data.tail(self.analysis_period).copy()
            analysis_data = analysis_data.reset_index(drop=True)

            # レジスタンスライン検出（高値の極大値ベース）
            resistance_line = self._detect_resistance_line_v3(analysis_data)
            if resistance_line:
                return self._create_detection_result(
                    analysis_data, "resistance_line", resistance_line
                )

            # サポートライン検出（安値の極小値ベース）
            support_line = self._detect_support_line_v3(analysis_data)
            if support_line:
                return self._create_detection_result(
                    analysis_data, "support_line", support_line
                )

            return None

        except Exception as e:
            logger.error(f"角度付きサポート/レジスタンスライン検出エラー: {e}")
            return None

    def _detect_resistance_line_v3(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """レジスタンスライン検出 V3（バッファ付き極値ベース）"""
        try:
            # バッファ付き極大値検出
            peaks = self._find_buffered_peaks(price_data["High"].values, "max")
            if len(peaks) < self.min_peaks:
                return None

            # 最適な1次関数を計算
            best_line = self._find_best_line_equation_v3(peaks, price_data, "High")
            if not best_line:
                return None

            # 角度チェック
            if abs(best_line["angle"]) > self.max_angle:
                return None

            # ライン強度を計算
            strength = self._calculate_line_strength_v3(
                peaks, best_line, price_data, "High"
            )
            if strength < self.min_line_strength:
                return None

            # 現在価格との関係を分析
            current_analysis = self._analyze_current_price_relation_v3(
                price_data, best_line, "resistance"
            )

            return {
                "line_type": "resistance",
                "peaks": peaks,
                "equation": best_line,
                "strength": strength,
                "current_analysis": current_analysis,
                "direction": "SELL",
                "timeframe": self.timeframe,
            }

        except Exception as e:
            logger.error(f"レジスタンスライン検出V3エラー: {e}")
            return None

    def _detect_support_line_v3(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """サポートライン検出 V3（バッファ付き極値ベース）"""
        try:
            # バッファ付き極小値検出
            troughs = self._find_buffered_peaks(price_data["Low"].values, "min")
            if len(troughs) < self.min_peaks:
                return None

            # 最適な1次関数を計算
            best_line = self._find_best_line_equation_v3(troughs, price_data, "Low")
            if not best_line:
                return None

            # 角度チェック
            if abs(best_line["angle"]) > self.max_angle:
                return None

            # ライン強度を計算
            strength = self._calculate_line_strength_v3(
                troughs, best_line, price_data, "Low"
            )
            if strength < self.min_line_strength:
                return None

            # 現在価格との関係を分析
            current_analysis = self._analyze_current_price_relation_v3(
                price_data, best_line, "support"
            )

            return {
                "line_type": "support",
                "troughs": troughs,
                "equation": best_line,
                "strength": strength,
                "current_analysis": current_analysis,
                "direction": "BUY",
                "timeframe": self.timeframe,
            }

        except Exception as e:
            logger.error(f"サポートライン検出V3エラー: {e}")
            return None

    def _find_buffered_peaks(self, prices: np.ndarray, peak_type: str) -> List[int]:
        """バッファ付き極値（ピーク/ボトム）を検出"""
        try:
            if peak_type == "max":
                # 上位N%の価格帯をバッファとして定義
                threshold = np.percentile(prices, 100 - self.buffer_percentile)
                peaks, _ = find_peaks(prices, height=threshold, distance=1)

                # もし極値が見つからない場合は、上位の価格ポイントを使用
                if len(peaks) == 0:
                    sorted_indices = np.argsort(prices)[::-1]
                    peaks = sorted_indices[: self.min_peaks]
            else:
                # 下位N%の価格帯をバッファとして定義
                threshold = np.percentile(prices, self.buffer_percentile)
                peaks, _ = find_peaks(-prices, height=-threshold, distance=1)

                # もし極値が見つからない場合は、下位の価格ポイントを使用
                if len(peaks) == 0:
                    sorted_indices = np.argsort(prices)
                    peaks = sorted_indices[: self.min_peaks]

            return peaks.tolist()

        except Exception as e:
            logger.error(f"バッファ付き極値検出エラー: {e}")
            return []

    def _find_best_line_equation_v3(
        self, peaks: List[int], price_data: pd.DataFrame, column: str
    ) -> Optional[Dict[str, float]]:
        """最適な1次関数（y = ax + b）を計算 V3"""
        try:
            if len(peaks) < 2:
                return None

            best_line = None
            best_score = 0

            # 全てのピークの組み合わせを試す
            for i in range(len(peaks)):
                for j in range(i + 1, len(peaks)):
                    # 2点間の1次関数を計算
                    x1, y1 = peaks[i], price_data.iloc[peaks[i]][column]
                    x2, y2 = peaks[j], price_data.iloc[peaks[j]][column]

                    # 傾きと切片を計算
                    if x2 - x1 == 0:  # 垂直線は除外
                        continue

                    a = (y2 - y1) / (x2 - x1)
                    b = y1 - a * x1

                    # この1次関数のスコアを計算
                    score = self._evaluate_line_equation_v3(
                        peaks, price_data, column, a, b
                    )

                    if score > best_score:
                        best_score = score
                        best_line = {
                            "slope": a,
                            "intercept": b,
                            "angle": math.degrees(math.atan(a)),
                            "score": score,
                        }

            return best_line if best_score > 0.5 else None

        except Exception as e:
            logger.error(f"最適1次関数計算V3エラー: {e}")
            return None

    def _evaluate_line_equation_v3(
        self,
        peaks: List[int],
        price_data: pd.DataFrame,
        column: str,
        a: float,
        b: float,
    ) -> float:
        """1次関数の評価スコアを計算 V3"""
        try:
            valid_points = 0
            total_error = 0

            for peak in peaks:
                x = peak
                actual_y = price_data.iloc[peak][column]
                predicted_y = a * x + b

                # 予測値と実際値の誤差
                error = abs(actual_y - predicted_y) / actual_y

                if error <= self.price_tolerance:
                    valid_points += 1

                total_error += error

            # スコア計算（有効ポイント率 + 誤差の逆数）
            valid_ratio = valid_points / len(peaks)
            avg_error = total_error / len(peaks)
            error_score = 1.0 / (1.0 + avg_error)

            return valid_ratio * 0.7 + error_score * 0.3

        except Exception as e:
            logger.error(f"1次関数評価V3エラー: {e}")
            return 0.0

    def _calculate_line_strength_v3(
        self, peaks: List[int], line_data: Dict, price_data: pd.DataFrame, column: str
    ) -> float:
        """ライン強度計算 V3"""
        try:
            a = line_data["slope"]
            b = line_data["intercept"]

            # 1. ピーク数の強度
            peak_strength = min(len(peaks) / 5.0, 1.0)

            # 2. 角度の強度（時間足別に調整）
            angle = abs(line_data["angle"])
            if angle < 5:  # ほぼ水平
                angle_strength = 1.0
            elif angle < 15:  # 緩やかな角度
                angle_strength = 0.9
            elif angle < 30:  # 中程度の角度
                angle_strength = 0.7
            elif angle < 45:  # 急な角度
                angle_strength = 0.5
            else:  # 非常に急な角度
                angle_strength = 0.3

            # 3. 価格の一貫性
            consistency = self._evaluate_line_equation_v3(
                peaks, price_data, column, a, b
            )

            # 4. 時間足別の重み付け
            if self.timeframe == "5m":
                weights = [0.3, 0.2, 0.5]  # ピーク数、角度、一貫性
            elif self.timeframe == "1h":
                weights = [0.25, 0.25, 0.5]  # バランス重視
            else:  # 1d
                weights = [0.2, 0.3, 0.5]  # 角度と一貫性重視

            # 総合強度
            strength = (
                peak_strength * weights[0]
                + angle_strength * weights[1]
                + consistency * weights[2]
            )
            return min(strength, 1.0)

        except Exception as e:
            logger.error(f"ライン強度計算V3エラー: {e}")
            return 0.0

    def _analyze_current_price_relation_v3(
        self, price_data: pd.DataFrame, line_data: Dict, line_type: str
    ) -> Dict[str, Any]:
        """現在価格とラインの関係を分析 V3"""
        try:
            current_price = price_data.iloc[-1]["Close"]
            current_index = len(price_data) - 1

            a = line_data["slope"]
            b = line_data["intercept"]
            line_price = a * current_index + b

            # 価格とラインの距離
            distance = abs(current_price - line_price) / line_price

            # 関係性の判定
            if line_type == "resistance":
                if current_price > line_price:
                    relation = "breakout"
                    strength = (current_price - line_price) / line_price
                elif distance <= self.price_tolerance:
                    relation = "touching"
                    strength = 1.0 - distance
                else:
                    relation = "below"
                    strength = 1.0 / (1.0 + distance)
            else:  # support
                if current_price < line_price:
                    relation = "breakdown"
                    strength = (line_price - current_price) / line_price
                elif distance <= self.price_tolerance:
                    relation = "touching"
                    strength = 1.0 - distance
                else:
                    relation = "above"
                    strength = 1.0 / (1.0 + distance)

            return {
                "relation": relation,
                "strength": strength,
                "distance": distance,
                "line_price": line_price,
                "current_price": current_price,
            }

        except Exception as e:
            logger.error(f"現在価格関係分析V3エラー: {e}")
            return {"relation": "unknown", "strength": 0.0}

    def _calculate_confidence_v3(self, pattern_data: Dict) -> float:
        """信頼度計算 V3"""
        try:
            base_confidence = 0.75

            # 時間足別の基本信頼度調整
            if self.timeframe == "5m":
                base_confidence = 0.70
            elif self.timeframe == "1h":
                base_confidence = 0.80
            elif self.timeframe == "1d":
                base_confidence = 0.85

            # ライン強度による調整
            strength = pattern_data.get("strength", 0.0)
            if strength > 0.9:
                base_confidence += 0.15
            elif strength > 0.8:
                base_confidence += 0.10
            elif strength > 0.7:
                base_confidence += 0.05

            # 角度による調整
            angle = abs(pattern_data.get("equation", {}).get("angle", 0))
            if angle < 5:  # 水平ラインは信頼度が高い
                base_confidence += 0.05
            elif angle < 15:  # 緩やかな角度
                base_confidence += 0.03

            # 現在価格との関係による調整
            current_analysis = pattern_data.get("current_analysis", {})
            relation = current_analysis.get("relation", "unknown")
            if relation == "touching":
                base_confidence += 0.05
            elif relation in ["breakout", "breakdown"]:
                base_confidence += 0.03

            return min(base_confidence, 0.95)

        except Exception as e:
            logger.error(f"信頼度計算V3エラー: {e}")
            return 0.75

    def _create_detection_result(
        self, price_data: pd.DataFrame, pattern_type: str, pattern_data: Dict
    ) -> Dict[str, Any]:
        """検出結果作成 V3"""
        try:
            current_price = price_data.iloc[-1]["Close"]
            confidence = self._calculate_confidence_v3(pattern_data)

            # パターン名と戦略の決定
            if pattern_type == "resistance_line":
                pattern_name = f"角度付きレジスタンスライン ({self.timeframe})"
                strategy = "売りシグナル"
                description = f"高値の極大値を結ぶ角度付きレジスタンスラインを検出 ({self.timeframe})"
            else:
                pattern_name = f"角度付きサポートライン ({self.timeframe})"
                strategy = "買いシグナル"
                description = f"安値の極小値を結ぶ角度付きサポートラインを検出 ({self.timeframe})"

            # 角度情報
            angle = pattern_data.get("equation", {}).get("angle", 0)
            angle_description = self._get_angle_description(angle)

            result = {
                "pattern_number": 15,
                "pattern_name": f"角度付きサポート/レジスタンスライン検出 ({pattern_name})",
                "priority": PatternPriority.HIGH,
                "confidence_score": confidence,
                "detection_time": datetime.now().isoformat(),
                "notification_title": f"📐 {pattern_name}検出！",
                "notification_color": "0x32CD32",
                "strategy": strategy,
                "entry_condition": f"角度: {angle_description} ({self.timeframe})",
                "current_price": current_price,
                "pattern_type": pattern_type,
                "pattern_data": pattern_data,
                "direction": pattern_data.get(
                    "direction", "SELL" if pattern_type == "resistance_line" else "BUY"
                ),
                "description": f"{description} - {angle_description}",
                "timeframe": self.timeframe,
            }

            return result

        except Exception as e:
            logger.error(f"検出結果作成V3エラー: {e}")
            return None

    def _get_angle_description(self, angle: float) -> str:
        """角度の説明を取得"""
        abs_angle = abs(angle)
        if abs_angle < 5:
            return "ほぼ水平"
        elif abs_angle < 15:
            return "緩やかな上昇" if angle > 0 else "緩やかな下降"
        elif abs_angle < 30:
            return "中程度の上昇" if angle > 0 else "中程度の下降"
        elif abs_angle < 45:
            return "急な上昇" if angle > 0 else "急な下降"
        else:
            return "非常に急な上昇" if angle > 0 else "非常に急な下降"
