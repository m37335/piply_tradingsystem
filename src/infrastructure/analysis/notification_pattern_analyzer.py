"""
通知パターン分析エンジン

マルチタイムフレーム戦略に基づく通知パターンを分析するメインエンジン
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from ...domain.entities.notification_pattern import NotificationPattern
from ...domain.value_objects.pattern_priority import PatternPriority
from ...utils.pattern_utils import PatternUtils
from .pattern_detectors.breakout_detector import BreakoutDetector
from .pattern_detectors.composite_signal_detector import CompositeSignalDetector
from .pattern_detectors.divergence_detector import DivergenceDetector
from .pattern_detectors.engulfing_pattern_detector import EngulfingPatternDetector
from .pattern_detectors.marubozu_detector import MarubozuDetector
from .pattern_detectors.pullback_detector import PullbackDetector
from .pattern_detectors.red_three_soldiers_detector import RedThreeSoldiersDetector
from .pattern_detectors.rsi_battle_detector import RSIBattleDetector
from .pattern_detectors.trend_reversal_detector import TrendReversalDetector


class NotificationPatternAnalyzer:
    """通知パターン分析エンジン"""

    def __init__(self):
        self.utils = PatternUtils()
        self.detectors = {
            1: TrendReversalDetector(),
            2: PullbackDetector(),
            3: DivergenceDetector(),
            4: BreakoutDetector(),
            5: RSIBattleDetector(),
            6: CompositeSignalDetector(),
            7: EngulfingPatternDetector(),
            8: RedThreeSoldiersDetector(),
            9: MarubozuDetector(),
        }

        # パターン定義
        self.patterns = {
            1: NotificationPattern.create_pattern_1(),
            2: NotificationPattern.create_pattern_2(),
            3: NotificationPattern.create_pattern_3(),
            4: NotificationPattern.create_pattern_4(),
            5: NotificationPattern.create_pattern_5(),
            6: NotificationPattern.create_pattern_6(),
            7: NotificationPattern.create_pattern_7(),
            8: NotificationPattern.create_pattern_8(),
            9: NotificationPattern.create_pattern_9(),
        }

    def analyze_multi_timeframe_data(
        self, multi_timeframe_data: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> List[Dict[str, Any]]:
        """
        マルチタイムフレームデータを分析してパターンを検出

        Args:
            multi_timeframe_data: マルチタイムフレームデータ
            currency_pair: 通貨ペア

        Returns:
            検出されたパターンのリスト
        """
        detected_patterns = []

        # データの妥当性チェック
        if not self._validate_multi_timeframe_data(multi_timeframe_data):
            return detected_patterns

        # 各パターンを検出
        for pattern_number, detector in self.detectors.items():
            try:
                detection_result = detector.detect(multi_timeframe_data)
                if detection_result:
                    # 通貨ペア情報を追加
                    detection_result["currency_pair"] = currency_pair
                    detection_result["analyzed_at"] = datetime.now()

                    detected_patterns.append(detection_result)
            except Exception as e:
                # エラーログを記録（実際の実装ではloggingを使用）
                print(f"パターン{pattern_number}の検出でエラー: {e}")
                continue

        # 優先度順にソート
        detected_patterns.sort(
            key=lambda x: x.get("priority", PatternPriority.LOW).value, reverse=True
        )

        return detected_patterns

    def get_pattern_info(self, pattern_number: int) -> Optional[Dict[str, Any]]:
        """
        パターン情報を取得

        Args:
            pattern_number: パターン番号

        Returns:
            パターン情報の辞書
        """
        if pattern_number not in self.patterns:
            return None

        pattern = self.patterns[pattern_number]
        return pattern.to_dict()

    def get_all_patterns_info(self) -> List[Dict[str, Any]]:
        """
        全パターンの情報を取得

        Returns:
            全パターン情報のリスト
        """
        return [pattern.to_dict() for pattern in self.patterns.values()]

    def get_detector_status(self) -> Dict[str, Any]:
        """
        検出器のステータスを取得

        Returns:
            検出器ステータスの辞書
        """
        status = {
            "total_detectors": len(self.detectors),
            "active_detectors": [],
            "inactive_detectors": [],
        }

        for pattern_number, detector in self.detectors.items():
            detector_info = {
                "pattern_number": pattern_number,
                "pattern_name": detector.pattern.name,
                "priority": detector.pattern.priority.value,
            }
            status["active_detectors"].append(detector_info)

        return status

    def _validate_multi_timeframe_data(self, data: Dict[str, Any]) -> bool:
        """マルチタイムフレームデータの妥当性をチェック"""
        required_timeframes = ["D1", "H4", "H1", "M5"]

        # 必要な時間軸が存在するかチェック
        for timeframe in required_timeframes:
            if timeframe not in data:
                print(f"必要な時間軸 {timeframe} が見つかりません")
                return False

        # 各時間軸のデータ妥当性をチェック
        for timeframe, timeframe_data in data.items():
            if not self.utils.validate_timeframe_data(timeframe_data):
                print(f"時間軸 {timeframe} のデータが無効です")
                return False

        return True

    def calculate_overall_confidence(
        self, detected_patterns: List[Dict[str, Any]]
    ) -> float:
        """
        全体的な信頼度を計算

        Args:
            detected_patterns: 検出されたパターンのリスト

        Returns:
            全体的な信頼度スコア（0.0-1.0）
        """
        if not detected_patterns:
            return 0.0

        # 重み付き平均を計算（優先度の高いパターンほど重みが大きい）
        total_weight = 0
        weighted_sum = 0

        for pattern in detected_patterns:
            priority = pattern.get("priority", PatternPriority.LOW)
            confidence = pattern.get("confidence_score", 0.0)

            # 優先度を重みとして使用
            weight = priority.value / 100.0
            weighted_sum += confidence * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(weighted_sum / total_weight, 2)

    def get_analysis_summary(
        self, multi_timeframe_data: Dict[str, Any], currency_pair: str = "USD/JPY"
    ) -> Dict[str, Any]:
        """
        分析サマリーを取得

        Args:
            multi_timeframe_data: マルチタイムフレームデータ
            currency_pair: 通貨ペア

        Returns:
            分析サマリーの辞書
        """
        # パターン検出
        detected_patterns = self.analyze_multi_timeframe_data(
            multi_timeframe_data, currency_pair
        )

        # 全体的な信頼度を計算
        overall_confidence = self.calculate_overall_confidence(detected_patterns)

        # 現在価格を取得
        current_price = self._get_current_price(multi_timeframe_data)

        # サマリー作成
        summary = {
            "currency_pair": currency_pair,
            "current_price": current_price,
            "analyzed_at": datetime.now().isoformat(),
            "total_patterns_detected": len(detected_patterns),
            "overall_confidence": overall_confidence,
            "detected_patterns": detected_patterns,
            "detector_status": self.get_detector_status(),
        }

        return summary

    def _get_current_price(self, multi_timeframe_data: Dict[str, Any]) -> str:
        """現在価格を取得"""
        # M5の最新価格を優先
        if "M5" in multi_timeframe_data:
            m5_data = multi_timeframe_data["M5"]
            price_data = m5_data.get("price_data", pd.DataFrame())
            if not price_data.empty:
                return f"{price_data['Close'].iloc[-1]:.3f}"

        # フォールバック: H1の最新価格
        if "H1" in multi_timeframe_data:
            h1_data = multi_timeframe_data["H1"]
            price_data = h1_data.get("price_data", pd.DataFrame())
            if not price_data.empty:
                return f"{price_data['Close'].iloc[-1]:.3f}"

        return "N/A"
