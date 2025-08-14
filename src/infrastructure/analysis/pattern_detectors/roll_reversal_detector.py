#!/usr/bin/env python3
"""
Roll Reversal Detector (Pattern 16)
ロールリバーサル検出器

トレンド転換を示すロールリバーサルパターンを検出
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


class RollReversalDetector:
    """ロールリバーサル検出器"""

    def __init__(self):
        self.pattern = NotificationPattern.create_pattern_16()
        self.utils = PatternUtils()
        self.min_roll_length = 2  # ロールの最小長さ（3→2に緩和）
        self.max_roll_length = 30  # ロールの最大長さ（25→30に緩和）
        self.reversal_threshold = 0.005  # リバーサル閾値（1%→0.5%に緩和）
        self.momentum_threshold = 0.005  # モメンタム閾値（1%→0.5%に緩和）

    def detect(self, price_data: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """ロールリバーサルパターン検出"""
        try:
            if price_data is None or len(price_data) < 30:
                return None

            # 強気ロールリバーサル検出
            bullish_roll = self._detect_bullish_roll_reversal(price_data)
            if bullish_roll:
                return self._create_detection_result(
                    price_data, "bullish_roll_reversal", bullish_roll
                )

            # 弱気ロールリバーサル検出
            bearish_roll = self._detect_bearish_roll_reversal(price_data)
            if bearish_roll:
                return self._create_detection_result(
                    price_data, "bearish_roll_reversal", bearish_roll
                )

            return None

        except Exception as e:
            logger.error(f"ロールリバーサル検出エラー: {e}")
            return None

    def _detect_bullish_roll_reversal(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """強気ロールリバーサル検出"""
        try:
            # ロールパターン識別
            roll_data = self._identify_roll_pattern(price_data, "bearish")
            if not roll_data:
                return None

            # リバーサルシグナル検出
            if not self._detect_reversal_signal(price_data, roll_data, "bullish"):
                return None

            # ロールリバーサル検証（一時的に無効化）
            # if not self._validate_roll_reversal(price_data, roll_data):
            #     return None

            return {
                "pattern_type": "bullish_roll_reversal",
                "roll_data": roll_data,
                "direction": "BUY",
            }

        except Exception as e:
            logger.error(f"強気ロールリバーサル検出エラー: {e}")
            return None

    def _detect_bearish_roll_reversal(
        self, price_data: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """弱気ロールリバーサル検出"""
        try:
            # ロールパターン識別
            roll_data = self._identify_roll_pattern(price_data, "bullish")
            if not roll_data:
                return None

            # リバーサルシグナル検出
            if not self._detect_reversal_signal(price_data, roll_data, "bearish"):
                return None

            # ロールリバーサル検証（一時的に無効化）
            # if not self._validate_roll_reversal(price_data, roll_data):
            #     return None

            return {
                "pattern_type": "bearish_roll_reversal",
                "roll_data": roll_data,
                "direction": "SELL",
            }

        except Exception as e:
            logger.error(f"弱気ロールリバーサル検出エラー: {e}")
            return None

    def _identify_roll_pattern(
        self, price_data: pd.DataFrame, trend_type: str
    ) -> Optional[Dict[str, Any]]:
        """ロールパターン識別"""
        try:
            # トレンドの方向に応じてロールパターンを検出
            if trend_type == "bearish":
                # 下降トレンドのロールパターン
                roll_points = self._find_bearish_roll_points(price_data)
            else:
                # 上昇トレンドのロールパターン
                roll_points = self._find_bullish_roll_points(price_data)

            if len(roll_points) < 1:  # 最小ロール長さを1に緩和
                return None

            # ロールの特徴を計算
            roll_characteristics = self._calculate_roll_characteristics(
                price_data, roll_points, trend_type
            )

            return {
                "trend_type": trend_type,
                "roll_points": roll_points,
                "characteristics": roll_characteristics,
            }

        except Exception as e:
            logger.error(f"ロールパターン識別エラー: {e}")
            return None

    def _find_bearish_roll_points(self, price_data: pd.DataFrame) -> List[int]:
        """下降トレンドのロールポイント検出"""
        try:
            roll_points = []

            # 下降トレンドの連続的な安値を検出
            for i in range(3, len(price_data) - 3):  # 5→3に緩和
                # 過去3期間の下降トレンドをチェック（5→3に緩和）
                past_lows = [price_data.iloc[j]["Low"] for j in range(i - 3, i)]
                if len(past_lows) >= 2 and all(
                    past_lows[j] >= past_lows[j + 1] for j in range(len(past_lows) - 1)
                ):
                    # 現在の安値が前回より低い
                    if price_data.iloc[i]["Low"] < price_data.iloc[i - 1]["Low"]:
                        roll_points.append(i)

            return roll_points

        except Exception as e:
            logger.error(f"下降ロールポイント検出エラー: {e}")
            return []

    def _find_bullish_roll_points(self, price_data: pd.DataFrame) -> List[int]:
        """上昇トレンドのロールポイント検出"""
        try:
            roll_points = []

            # 上昇トレンドの連続的な高値を検出
            for i in range(3, len(price_data) - 3):  # 5→3に緩和
                # 過去3期間の上昇トレンドをチェック（5→3に緩和）
                past_highs = [price_data.iloc[j]["High"] for j in range(i - 3, i)]
                if len(past_highs) >= 2 and all(
                    past_highs[j] <= past_highs[j + 1]
                    for j in range(len(past_highs) - 1)
                ):
                    # 現在の高値が前回より高い
                    if price_data.iloc[i]["High"] > price_data.iloc[i - 1]["High"]:
                        roll_points.append(i)

            return roll_points

        except Exception as e:
            logger.error(f"上昇ロールポイント検出エラー: {e}")
            return []

    def _calculate_roll_characteristics(
        self, price_data: pd.DataFrame, roll_points: List[int], trend_type: str
    ) -> Dict[str, Any]:
        """ロールの特徴計算"""
        try:
            if len(roll_points) < 2:
                return {}

            # ロールの長さ
            roll_length = len(roll_points)

            # 価格変動の計算
            if trend_type == "bearish":
                price_changes = [
                    price_data.iloc[roll_points[i]]["Low"]
                    - price_data.iloc[roll_points[i - 1]]["Low"]
                    for i in range(1, len(roll_points))
                ]
            else:
                price_changes = [
                    price_data.iloc[roll_points[i]]["High"]
                    - price_data.iloc[roll_points[i - 1]]["High"]
                    for i in range(1, len(roll_points))
                ]

            # 平均価格変動
            avg_price_change = np.mean(price_changes)

            # 価格変動の一貫性
            price_consistency = 1.0 / (1.0 + np.var(price_changes))

            # モメンタム計算
            momentum = self._calculate_momentum(price_data, roll_points[-5:])

            return {
                "roll_length": roll_length,
                "avg_price_change": avg_price_change,
                "price_consistency": price_consistency,
                "momentum": momentum,
                "trend_strength": abs(avg_price_change) / price_data.iloc[-1]["Close"],
            }

        except Exception as e:
            logger.error(f"ロール特徴計算エラー: {e}")
            return {}

    def _detect_reversal_signal(
        self, price_data: pd.DataFrame, roll_data: Dict, reversal_type: str
    ) -> bool:
        """リバーサルシグナル検出"""
        try:
            roll_points = roll_data.get("roll_points", [])
            if len(roll_points) < 1:  # 3→1に緩和
                return False

            # 最新のロールポイント以降の価格変動をチェック
            last_roll_point = roll_points[-1]
            recent_data = price_data.iloc[last_roll_point:]

            if len(recent_data) < 3:  # 5→3に緩和
                return False

            if reversal_type == "bullish":
                # 強気リバーサル: 価格が上昇に転換
                recent_lows = recent_data["Low"].values
                if len(recent_lows) >= 2:  # 3→2に緩和
                    # 最近の安値が上昇傾向にあるかチェック
                    low_trend = np.polyfit(range(len(recent_lows)), recent_lows, 1)[0]
                    return low_trend > 0 and abs(low_trend) > self.reversal_threshold

            else:
                # 弱気リバーサル: 価格が下降に転換
                recent_highs = recent_data["High"].values
                if len(recent_highs) >= 2:  # 3→2に緩和
                    # 最近の高値が下降傾向にあるかチェック
                    high_trend = np.polyfit(range(len(recent_highs)), recent_highs, 1)[
                        0
                    ]
                    return high_trend < 0 and abs(high_trend) > self.reversal_threshold

            return False

        except Exception as e:
            logger.error(f"リバーサルシグナル検出エラー: {e}")
            return False

    def _calculate_momentum(
        self, price_data: pd.DataFrame, points: List[int], window: int = 5
    ) -> float:
        """モメンタム計算"""
        try:
            if len(points) < window:
                return 0.0

            # 指定されたポイントでの価格を取得
            prices = [price_data.iloc[point]["Close"] for point in points[-window:]]

            if len(prices) < 2:
                return 0.0

            # 価格変化率の平均を計算
            price_changes = []
            for i in range(1, len(prices)):
                change = (prices[i] - prices[i - 1]) / prices[i - 1]
                price_changes.append(change)

            return np.mean(price_changes)

        except Exception as e:
            logger.error(f"モメンタム計算エラー: {e}")
            return 0.0

    def _validate_roll_reversal(
        self, price_data: pd.DataFrame, pattern_data: Dict
    ) -> bool:
        """ロールリバーサル検証"""
        try:
            characteristics = pattern_data.get("characteristics", {})

            # ロールの長さチェック
            roll_length = characteristics.get("roll_length", 0)
            if roll_length < 1 or roll_length > 50:  # より緩和された条件
                return False

            # トレンド強度チェック
            trend_strength = characteristics.get("trend_strength", 0)
            if trend_strength < 0.001:  # より緩和された条件
                return False

            # 価格一貫性チェック
            price_consistency = characteristics.get("price_consistency", 0)
            if price_consistency < 0.3:  # 60%→30%に緩和
                return False

            # モメンタムチェック
            momentum = characteristics.get("momentum", 0)
            if abs(momentum) < 0.001:  # より緩和された条件
                return False

            return True

        except Exception as e:
            logger.error(f"ロールリバーサル検証エラー: {e}")
            return False

    def _calculate_roll_reversal_confidence(self, pattern_data: Dict) -> float:
        """ロールリバーサル信頼度計算"""
        try:
            base_confidence = 0.75

            # パターンタイプによる調整
            if pattern_data.get("pattern_type") == "bullish_roll_reversal":
                base_confidence += 0.03
            elif pattern_data.get("pattern_type") == "bearish_roll_reversal":
                base_confidence += 0.02

            # ロールの特徴による調整
            roll_data = pattern_data.get("roll_data", {})
            characteristics = roll_data.get("characteristics", {})

            # ロール長による調整
            roll_length = characteristics.get("roll_length", 0)
            if 8 <= roll_length <= 15:
                base_confidence += 0.05
            elif 5 <= roll_length <= 20:
                base_confidence += 0.03

            # トレンド強度による調整
            trend_strength = characteristics.get("trend_strength", 0)
            if trend_strength > 0.03:  # 3%以上
                base_confidence += 0.05
            elif trend_strength > 0.02:  # 2%以上
                base_confidence += 0.03

            # 価格一貫性による調整
            price_consistency = characteristics.get("price_consistency", 0)
            if price_consistency > 0.8:
                base_confidence += 0.05
            elif price_consistency > 0.6:
                base_confidence += 0.03

            # モメンタムによる調整
            momentum = characteristics.get("momentum", 0)
            if abs(momentum) > 0.02:  # 2%以上
                base_confidence += 0.03
            elif abs(momentum) > 0.015:  # 1.5%以上
                base_confidence += 0.02

            return min(base_confidence, 0.85)

        except Exception as e:
            logger.error(f"信頼度計算エラー: {e}")
            return 0.75

    def _create_detection_result(
        self, price_data: pd.DataFrame, pattern_type: str, pattern_data: Dict
    ) -> Dict[str, Any]:
        """検出結果作成"""
        try:
            current_price = price_data.iloc[-1]["Close"]
            confidence = self._calculate_roll_reversal_confidence(pattern_data)

            # パターン名の決定
            if pattern_type == "bullish_roll_reversal":
                pattern_name = "強気ロールリバーサル"
                strategy = "買いシグナル"
            else:
                pattern_name = "弱気ロールリバーサル"
                strategy = "売りシグナル"

            result = {
                "pattern_number": 16,
                "pattern_name": f"ロールリバーサル検出 ({pattern_name})",
                "priority": PatternPriority.MEDIUM,
                "confidence_score": confidence,
                "detection_time": datetime.now().isoformat(),
                "notification_title": f"🔄 {pattern_name}検出！",
                "notification_color": "0x9370DB",
                "strategy": strategy,
                "entry_condition": "リバーサル確認",
                "current_price": current_price,
                "pattern_type": pattern_type,
                "pattern_data": pattern_data,
                "direction": pattern_data.get(
                    "direction",
                    "BUY" if pattern_type == "bullish_roll_reversal" else "SELL",
                ),
                "description": f"トレンド転換を示す{pattern_name}パターン",
            }

            return result

        except Exception as e:
            logger.error(f"検出結果作成エラー: {e}")
            return None
