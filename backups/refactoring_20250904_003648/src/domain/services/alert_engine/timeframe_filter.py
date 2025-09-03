"""
時間軸間フィルタリング器

プロトレーダー向け為替アラートシステム用の時間軸間フィルタリング器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime
from typing import Any, Dict, List

from src.infrastructure.database.models.entry_signal_model import EntrySignalModel


class TimeframeFilter:
    """
    時間軸間フィルタリング器

    責任:
    - 複数タイムフレーム間の一貫性チェック
    - 時間軸間の矛盾検出
    - フィルタリング結果の記録
    - フィルタリング効果の測定

    特徴:
    - 動的フィルタリング
    - 一貫性スコアリング
    - 効果測定
    - 結果記録
    """

    def __init__(self):
        """
        初期化
        """
        # フィルタリング設定
        self.consistency_threshold = 0.7  # 一貫性閾値
        self.timeframe_weights = {
            "M5": 0.25,
            "M15": 0.25,
            "H1": 0.25,
            "H4": 0.15,
            "D1": 0.10,
        }
        self.enable_filtering = True  # フィルタリング有効/無効

        # フィルタリング履歴
        self.filter_history = []

    def filter_signals_by_timeframe_consistency(
        self,
        signals: List[EntrySignalModel],
        timeframe_analyses: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        時間軸間一貫性に基づいてシグナルをフィルタリング

        Args:
            signals: エントリーシグナルリスト
            timeframe_analyses: タイムフレーム分析結果

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
            # 時間軸間一貫性チェック
            consistency_check = self._check_timeframe_consistency(
                signal, timeframe_analyses
            )

            if consistency_check["should_filter"]:
                filtered_count += 1
                filter_reasons.append(
                    {
                        "signal_id": signal.id if hasattr(signal, "id") else None,
                        "currency_pair": signal.currency_pair,
                        "reason": consistency_check["reason"],
                        "consistency_score": consistency_check["consistency_score"],
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

    def _check_timeframe_consistency(
        self,
        signal: EntrySignalModel,
        timeframe_analyses: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        時間軸間一貫性をチェック

        Args:
            signal: エントリーシグナル
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Dict[str, Any]: 一貫性チェック結果
        """
        signal_type = signal.signal_type
        should_filter = False
        reason = ""
        consistency_score = 0.0
        supporting_timeframes = 0
        total_timeframes = 0

        # 各タイムフレームの分析結果をチェック
        for timeframe, analysis in timeframe_analyses.items():
            if timeframe not in self.timeframe_weights:
                continue

            total_timeframes += 1
            trend = analysis.get("trend", {})
            momentum = analysis.get("momentum", {})

            # トレンド方向の一貫性チェック
            trend_direction = trend.get("direction", "unknown")
            momentum_direction = momentum.get("direction", "neutral")

            # シグナルタイプと一貫性をチェック
            if self._is_consistent_with_signal(
                signal_type, trend_direction, momentum_direction
            ):
                supporting_timeframes += 1
                consistency_score += self.timeframe_weights[timeframe]

        # 一貫性スコアを正規化
        if total_timeframes > 0:
            consistency_score = consistency_score / sum(
                self.timeframe_weights.get(tf, 0) for tf in timeframe_analyses.keys()
            )

        # フィルタリング判定
        if consistency_score < self.consistency_threshold:
            should_filter = True
            reason = f"時間軸間一貫性不足: {consistency_score:.2f} (閾値: {self.consistency_threshold})"

        return {
            "should_filter": should_filter,
            "reason": reason,
            "consistency_score": consistency_score,
            "supporting_timeframes": supporting_timeframes,
            "total_timeframes": total_timeframes,
        }

    def _is_consistent_with_signal(
        self, signal_type: str, trend_direction: str, momentum_direction: str
    ) -> bool:
        """
        シグナルと分析結果の一貫性をチェック

        Args:
            signal_type: シグナルタイプ
            trend_direction: トレンド方向
            momentum_direction: モメンタム方向

        Returns:
            bool: 一貫性があるかどうか
        """
        if signal_type == "BUY":
            # 買いシグナルの場合
            trend_consistent = trend_direction in ["uptrend", "sideways"]
            momentum_consistent = momentum_direction in ["bullish", "neutral"]
            return trend_consistent and momentum_consistent
        elif signal_type == "SELL":
            # 売りシグナルの場合
            trend_consistent = trend_direction in ["downtrend", "sideways"]
            momentum_consistent = momentum_direction in ["bearish", "neutral"]
            return trend_consistent and momentum_consistent
        else:
            return False

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
                "consistency_threshold": self.consistency_threshold,
                "timeframe_weights": self.timeframe_weights,
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
        from datetime import timedelta

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
        consistency_threshold: float = None,
        timeframe_weights: Dict[str, float] = None,
        enable_filtering: bool = None,
    ) -> None:
        """
        フィルタ設定を更新

        Args:
            consistency_threshold: 一貫性閾値
            timeframe_weights: タイムフレーム重み
            enable_filtering: フィルタリング有効/無効
        """
        if consistency_threshold is not None:
            self.consistency_threshold = max(0.0, min(1.0, consistency_threshold))

        if timeframe_weights is not None:
            # 重みの合計が1.0になるように正規化
            total_weight = sum(timeframe_weights.values())
            if total_weight > 0:
                self.timeframe_weights = {
                    tf: weight / total_weight
                    for tf, weight in timeframe_weights.items()
                }

        if enable_filtering is not None:
            self.enable_filtering = enable_filtering

    def get_filter_settings(self) -> Dict[str, Any]:
        """
        現在のフィルタ設定を取得

        Returns:
            Dict[str, Any]: フィルタ設定
        """
        return {
            "consistency_threshold": self.consistency_threshold,
            "timeframe_weights": self.timeframe_weights,
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
