"""
相関性ベースフィルタリング器

プロトレーダー向け為替アラートシステム用の相関性ベースフィルタリング器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.infrastructure.database.models.entry_signal_model import EntrySignalModel


class CorrelationFilter:
    """
    相関性ベースフィルタリング器

    責任:
    - 高相関時のシグナルフィルタリング
    - 相関性閾値の調整
    - フィルタリング結果の記録
    - フィルタリング効果の測定

    特徴:
    - 動的フィルタリング
    - 閾値調整機能
    - 効果測定
    - 結果記録
    """

    def __init__(self):
        """
        初期化
        """
        # フィルタリング設定
        self.correlation_threshold = 0.8  # 高相関閾値
        self.filter_strength = 0.7  # フィルタリング強度（0-1）
        self.enable_filtering = True  # フィルタリング有効/無効

        # フィルタリング履歴
        self.filter_history = []

    def filter_signals_by_correlation(
        self,
        signals: List[EntrySignalModel],
        correlation_matrix: Dict[str, Dict[str, float]],
        current_positions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        相関性に基づいてシグナルをフィルタリング

        Args:
            signals: エントリーシグナルリスト
            correlation_matrix: 相関性行列
            current_positions: 現在のポジションリスト

        Returns:
            Dict[str, Any]: フィルタリング結果
        """
        if not self.enable_filtering:
            return {
                "filtered_signals": signals,
                "filtered_count": 0,
                "total_count": len(signals),
                "filter_reasons": [],
                "filtering_applied": False,
            }

        filtered_signals = []
        filtered_count = 0
        filter_reasons = []

        for signal in signals:
            # 相関性チェック
            correlation_check = self._check_signal_correlation(
                signal, correlation_matrix, current_positions
            )

            if correlation_check["should_filter"]:
                filtered_count += 1
                filter_reasons.append(
                    {
                        "signal_id": signal.id if hasattr(signal, "id") else None,
                        "currency_pair": signal.currency_pair,
                        "reason": correlation_check["reason"],
                        "correlation_value": correlation_check["correlation_value"],
                        "timestamp": datetime.utcnow(),
                    }
                )
            else:
                filtered_signals.append(signal)

        # フィルタリング履歴を記録
        self._record_filtering_result(len(signals), filtered_count, filter_reasons)

        return {
            "filtered_signals": filtered_signals,
            "filtered_count": filtered_count,
            "total_count": len(signals),
            "filter_reasons": filter_reasons,
            "filtering_applied": True,
            "filter_ratio": filtered_count / len(signals) if signals else 0,
        }

    def _check_signal_correlation(
        self,
        signal: EntrySignalModel,
        correlation_matrix: Dict[str, Dict[str, float]],
        current_positions: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        シグナルの相関性をチェック

        Args:
            signal: エントリーシグナル
            correlation_matrix: 相関性行列
            current_positions: 現在のポジションリスト

        Returns:
            Dict[str, Any]: 相関性チェック結果
        """
        signal_pair = signal.currency_pair
        should_filter = False
        reason = ""
        max_correlation = 0.0

        # 現在のポジションとの相関性をチェック
        if current_positions:
            for position in current_positions:
                position_pair = position.get("currency_pair")

                if position_pair and position_pair != signal_pair:
                    # 相関性を取得
                    correlation = self._get_correlation_value(
                        signal_pair, position_pair, correlation_matrix
                    )

                    if abs(correlation) > abs(max_correlation):
                        max_correlation = correlation

                    # 高相関で同じ方向のポジションがある場合
                    if abs(
                        correlation
                    ) >= self.correlation_threshold and self._is_same_direction(
                        signal, position
                    ):

                        should_filter = True
                        reason = f"高相関ポジションとの重複: {position_pair} (相関: {correlation:.3f})"
                        break

        # 信頼度スコアを調整
        adjusted_confidence = self._adjust_confidence_by_correlation(
            signal.confidence_score, max_correlation
        )

        return {
            "should_filter": should_filter,
            "reason": reason,
            "correlation_value": max_correlation,
            "adjusted_confidence": adjusted_confidence,
        }

    def _get_correlation_value(
        self,
        pair1: str,
        pair2: str,
        correlation_matrix: Dict[str, Dict[str, float]],
    ) -> float:
        """
        相関値を取得

        Args:
            pair1: 通貨ペア1
            pair2: 通貨ペア2
            correlation_matrix: 相関性行列

        Returns:
            float: 相関値
        """
        try:
            # 相関性行列から値を取得
            if pair1 in correlation_matrix and pair2 in correlation_matrix[pair1]:
                return correlation_matrix[pair1][pair2]
            elif pair2 in correlation_matrix and pair1 in correlation_matrix[pair2]:
                return correlation_matrix[pair2][pair1]
            else:
                return 0.0
        except Exception as e:
            print(f"Error getting correlation value: {e}")
            return 0.0

    def _is_same_direction(
        self, signal: EntrySignalModel, position: Dict[str, Any]
    ) -> bool:
        """
        シグナルとポジションが同じ方向かチェック

        Args:
            signal: エントリーシグナル
            position: ポジション情報

        Returns:
            bool: 同じ方向かどうか
        """
        signal_type = signal.signal_type
        position_type = position.get("signal_type", "")

        return signal_type == position_type

    def _adjust_confidence_by_correlation(
        self, original_confidence: int, correlation_value: float
    ) -> int:
        """
        相関性に基づいて信頼度を調整

        Args:
            original_confidence: 元の信頼度
            correlation_value: 相関値

        Returns:
            int: 調整後の信頼度
        """
        # 高相関時は信頼度を下げる
        if abs(correlation_value) >= self.correlation_threshold:
            reduction = int(
                original_confidence * self.filter_strength * abs(correlation_value)
            )
            adjusted_confidence = max(0, original_confidence - reduction)
        else:
            adjusted_confidence = original_confidence

        return adjusted_confidence

    def _record_filtering_result(
        self,
        total_signals: int,
        filtered_count: int,
        filter_reasons: List[Dict[str, Any]],
    ) -> None:
        """
        フィルタリング結果を記録

        Args:
            total_signals: 総シグナル数
            filtered_count: フィルタリングされた数
            filter_reasons: フィルタリング理由
        """
        record = {
            "timestamp": datetime.utcnow(),
            "total_signals": total_signals,
            "filtered_count": filtered_count,
            "filter_ratio": filtered_count / total_signals if total_signals > 0 else 0,
            "filter_reasons": filter_reasons,
            "settings": {
                "correlation_threshold": self.correlation_threshold,
                "filter_strength": self.filter_strength,
                "enable_filtering": self.enable_filtering,
            },
        }

        self.filter_history.append(record)

        # 履歴を100件まで保持
        if len(self.filter_history) > 100:
            self.filter_history = self.filter_history[-100:]

    def get_filtering_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        フィルタリング統計を取得

        Args:
            days: 取得日数

        Returns:
            Dict[str, Any]: フィルタリング統計
        """
        if not self.filter_history:
            return {
                "total_records": 0,
                "avg_filter_ratio": 0.0,
                "total_signals_processed": 0,
                "total_signals_filtered": 0,
                "most_common_reason": "データなし",
            }

        # 指定日数以内のレコードを取得
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_records = [
            record
            for record in self.filter_history
            if record["timestamp"] >= cutoff_date
        ]

        if not recent_records:
            return {
                "total_records": 0,
                "avg_filter_ratio": 0.0,
                "total_signals_processed": 0,
                "total_signals_filtered": 0,
                "most_common_reason": "データなし",
            }

        # 統計を計算
        total_records = len(recent_records)
        avg_filter_ratio = (
            sum(record["filter_ratio"] for record in recent_records) / total_records
        )
        total_signals_processed = sum(
            record["total_signals"] for record in recent_records
        )
        total_signals_filtered = sum(
            record["filtered_count"] for record in recent_records
        )

        # 最も一般的なフィルタリング理由を取得
        all_reasons = []
        for record in recent_records:
            for reason in record["filter_reasons"]:
                all_reasons.append(reason.get("reason", "不明"))

        most_common_reason = "データなし"
        if all_reasons:
            from collections import Counter

            reason_counts = Counter(all_reasons)
            most_common_reason = reason_counts.most_common(1)[0][0]

        return {
            "total_records": total_records,
            "avg_filter_ratio": avg_filter_ratio,
            "total_signals_processed": total_signals_processed,
            "total_signals_filtered": total_signals_filtered,
            "most_common_reason": most_common_reason,
            "filtering_effectiveness": (
                total_signals_filtered / total_signals_processed
                if total_signals_processed > 0
                else 0
            ),
        }

    def update_filter_settings(
        self,
        correlation_threshold: float = None,
        filter_strength: float = None,
        enable_filtering: bool = None,
    ) -> None:
        """
        フィルタ設定を更新

        Args:
            correlation_threshold: 相関性閾値
            filter_strength: フィルタリング強度
            enable_filtering: フィルタリング有効/無効
        """
        if correlation_threshold is not None:
            self.correlation_threshold = max(0.0, min(1.0, correlation_threshold))

        if filter_strength is not None:
            self.filter_strength = max(0.0, min(1.0, filter_strength))

        if enable_filtering is not None:
            self.enable_filtering = enable_filtering

    def get_filter_settings(self) -> Dict[str, Any]:
        """
        現在のフィルタ設定を取得

        Returns:
            Dict[str, Any]: フィルタ設定
        """
        return {
            "correlation_threshold": self.correlation_threshold,
            "filter_strength": self.filter_strength,
            "enable_filtering": self.enable_filtering,
        }

    def clear_filter_history(self) -> None:
        """
        フィルタリング履歴をクリア
        """
        self.filter_history = []

    def export_filter_history(self) -> List[Dict[str, Any]]:
        """
        フィルタリング履歴をエクスポート

        Returns:
            List[Dict[str, Any]]: フィルタリング履歴
        """
        return self.filter_history.copy()

    def analyze_filter_performance(self) -> Dict[str, Any]:
        """
        フィルタリングパフォーマンスを分析

        Returns:
            Dict[str, Any]: パフォーマンス分析結果
        """
        if not self.filter_history:
            return {
                "performance_score": 0.0,
                "recommendations": ["フィルタリング履歴が不足しています"],
                "trend": "stable",
            }

        # 最近のフィルタリング比率の傾向を分析
        recent_ratios = [record["filter_ratio"] for record in self.filter_history[-10:]]

        if len(recent_ratios) < 2:
            trend = "stable"
        else:
            # 単純な傾向分析
            first_half = sum(recent_ratios[: len(recent_ratios) // 2]) / (
                len(recent_ratios) // 2
            )
            second_half = sum(recent_ratios[len(recent_ratios) // 2 :]) / (
                len(recent_ratios) // 2
            )

            if second_half > first_half * 1.1:
                trend = "increasing"
            elif second_half < first_half * 0.9:
                trend = "decreasing"
            else:
                trend = "stable"

        # パフォーマンススコアを計算
        avg_ratio = sum(recent_ratios) / len(recent_ratios)
        performance_score = min(1.0, avg_ratio * 2)  # 0.5の平均比率で1.0スコア

        # 推奨事項を生成
        recommendations = []
        if avg_ratio < 0.2:
            recommendations.append("フィルタリングが緩すぎる可能性があります")
        elif avg_ratio > 0.8:
            recommendations.append("フィルタリングが厳しすぎる可能性があります")

        if trend == "increasing":
            recommendations.append("フィルタリング比率が上昇傾向です")
        elif trend == "decreasing":
            recommendations.append("フィルタリング比率が下降傾向です")

        return {
            "performance_score": performance_score,
            "recommendations": recommendations,
            "trend": trend,
            "avg_filter_ratio": avg_ratio,
        }
