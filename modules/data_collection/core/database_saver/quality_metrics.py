"""
品質メトリクスシステム

データの品質を測定・追跡するシステムです。
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque


@dataclass
class QualityMetric:
    """品質メトリクス"""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class QualityThreshold:
    """品質閾値"""
    name: str
    warning_threshold: float
    critical_threshold: float
    description: str = ""


class QualityMetrics:
    """品質メトリクス管理システム"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history_size))
        self.thresholds: Dict[str, QualityThreshold] = {}
        self.alerts: List[Dict[str, Any]] = []
        self._init_default_thresholds()
    
    def _init_default_thresholds(self) -> None:
        """デフォルトの閾値を初期化"""
        # データ完全性の閾値
        self.add_threshold(
            "data_completeness",
            0.95,  # 95%以上
            0.90,  # 90%以上
            "データの完全性"
        )
        
        # データ精度の閾値
        self.add_threshold(
            "data_accuracy",
            0.98,  # 98%以上
            0.95,  # 95%以上
            "データの精度"
        )
        
        # データ一貫性の閾値
        self.add_threshold(
            "data_consistency",
            0.99,  # 99%以上
            0.95,  # 95%以上
            "データの一貫性"
        )
        
        # データ鮮度の閾値（秒）
        self.add_threshold(
            "data_freshness",
            300,   # 5分以内
            600,   # 10分以内
            "データの鮮度"
        )
        
        # エラー率の閾値
        self.add_threshold(
            "error_rate",
            0.01,  # 1%以下
            0.05,  # 5%以下
            "エラー率"
        )
    
    def add_threshold(
        self,
        name: str,
        warning_threshold: float,
        critical_threshold: float,
        description: str = ""
    ) -> None:
        """
        品質閾値を追加
        
        Args:
            name: メトリクス名
            warning_threshold: 警告閾値
            critical_threshold: クリティカル閾値
            description: 説明
        """
        threshold = QualityThreshold(
            name=name,
            warning_threshold=warning_threshold,
            critical_threshold=critical_threshold,
            description=description
        )
        self.thresholds[name] = threshold
    
    def record_metric(
        self,
        name: str,
        value: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        品質メトリクスを記録
        
        Args:
            name: メトリクス名
            value: 値
            metadata: メタデータ
        """
        metric = QualityMetric(
            name=name,
            value=value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.metrics_history[name].append(metric)
        
        # 閾値チェック
        self._check_thresholds(name, value)
    
    def _check_thresholds(self, name: str, value: float) -> None:
        """
        閾値をチェック
        
        Args:
            name: メトリクス名
            value: 値
        """
        if name not in self.thresholds:
            return
        
        threshold = self.thresholds[name]
        
        # 閾値の比較（値が小さいほど良い場合の調整）
        is_lower_better = name in ["error_rate", "data_freshness"]
        
        if is_lower_better:
            # 値が小さいほど良い場合
            if value > threshold.critical_threshold:
                self._create_alert(name, "critical", value, threshold.critical_threshold)
            elif value > threshold.warning_threshold:
                self._create_alert(name, "warning", value, threshold.warning_threshold)
        else:
            # 値が大きいほど良い場合
            if value < threshold.critical_threshold:
                self._create_alert(name, "critical", value, threshold.critical_threshold)
            elif value < threshold.warning_threshold:
                self._create_alert(name, "warning", value, threshold.warning_threshold)
    
    def _create_alert(
        self,
        metric_name: str,
        severity: str,
        value: float,
        threshold: float
    ) -> None:
        """
        アラートを作成
        
        Args:
            metric_name: メトリクス名
            severity: 深刻度
            value: 値
            threshold: 閾値
        """
        alert = {
            "metric_name": metric_name,
            "severity": severity,
            "value": value,
            "threshold": threshold,
            "timestamp": datetime.now(),
            "description": f"{metric_name} is {severity}: {value} (threshold: {threshold})"
        }
        
        self.alerts.append(alert)
    
    def get_metric_history(
        self,
        name: str,
        hours: int = 24
    ) -> List[QualityMetric]:
        """
        メトリクスの履歴を取得
        
        Args:
            name: メトリクス名
            hours: 取得する時間範囲（時間）
            
        Returns:
            メトリクスの履歴
        """
        if name not in self.metrics_history:
            return []
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            metric for metric in self.metrics_history[name]
            if metric.timestamp >= cutoff_time
        ]
    
    def get_latest_metric(self, name: str) -> Optional[QualityMetric]:
        """
        最新のメトリクスを取得
        
        Args:
            name: メトリクス名
            
        Returns:
            最新のメトリクス、またはNone
        """
        if name not in self.metrics_history or not self.metrics_history[name]:
            return None
        
        return self.metrics_history[name][-1]
    
    def get_metric_statistics(
        self,
        name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        メトリクスの統計情報を取得
        
        Args:
            name: メトリクス名
            hours: 統計を計算する時間範囲（時間）
            
        Returns:
            統計情報
        """
        history = self.get_metric_history(name, hours)
        
        if not history:
            return {
                "count": 0,
                "min": None,
                "max": None,
                "avg": None,
                "latest": None,
                "trend": None
            }
        
        values = [metric.value for metric in history]
        
        # トレンド計算（線形回帰の簡易版）
        trend = self._calculate_trend(values)
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": values[-1],
            "trend": trend
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """
        トレンドを計算
        
        Args:
            values: 値のリスト
            
        Returns:
            トレンド（"up", "down", "stable"）
        """
        if len(values) < 2:
            return "stable"
        
        # 最初の1/3と最後の1/3の平均を比較
        n = len(values)
        first_third = values[:n//3] if n >= 3 else values[:1]
        last_third = values[-n//3:] if n >= 3 else values[-1:]
        
        first_avg = sum(first_third) / len(first_third)
        last_avg = sum(last_third) / len(last_third)
        
        change_ratio = (last_avg - first_avg) / first_avg if first_avg != 0 else 0
        
        if change_ratio > 0.05:  # 5%以上の増加
            return "up"
        elif change_ratio < -0.05:  # 5%以上の減少
            return "down"
        else:
            return "stable"
    
    def get_quality_score(self, hours: int = 24) -> float:
        """
        総合品質スコアを取得
        
        Args:
            hours: 計算する時間範囲（時間）
            
        Returns:
            品質スコア（0.0 - 1.0）
        """
        if not self.metrics_history:
            return 1.0
        
        total_score = 0.0
        metric_count = 0
        
        for name in self.metrics_history:
            if name in self.thresholds:
                latest_metric = self.get_latest_metric(name)
                if latest_metric:
                    # 閾値に基づいてスコアを計算
                    threshold = self.thresholds[name]
                    is_lower_better = name in ["error_rate", "data_freshness"]
                    
                    if is_lower_better:
                        # 値が小さいほど良い場合
                        if latest_metric.value <= threshold.warning_threshold:
                            score = 1.0
                        elif latest_metric.value <= threshold.critical_threshold:
                            score = 0.5
                        else:
                            score = 0.0
                    else:
                        # 値が大きいほど良い場合
                        if latest_metric.value >= threshold.warning_threshold:
                            score = 1.0
                        elif latest_metric.value >= threshold.critical_threshold:
                            score = 0.5
                        else:
                            score = 0.0
                    
                    total_score += score
                    metric_count += 1
        
        return total_score / metric_count if metric_count > 0 else 1.0
    
    def get_alerts(
        self,
        severity: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        アラートを取得
        
        Args:
            severity: 深刻度でフィルタ（"warning", "critical"）
            hours: 取得する時間範囲（時間）
            
        Returns:
            アラートのリスト
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        filtered_alerts = [
            alert for alert in self.alerts
            if alert["timestamp"] >= cutoff_time
        ]
        
        if severity:
            filtered_alerts = [
                alert for alert in filtered_alerts
                if alert["severity"] == severity
            ]
        
        return filtered_alerts
    
    def clear_old_alerts(self, hours: int = 168) -> int:  # デフォルト7日
        """
        古いアラートをクリア
        
        Args:
            hours: 保持する時間範囲（時間）
            
        Returns:
            削除されたアラート数
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        old_count = len(self.alerts)
        self.alerts = [
            alert for alert in self.alerts
            if alert["timestamp"] >= cutoff_time
        ]
        
        return old_count - len(self.alerts)
    
    def get_quality_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        品質サマリーを取得
        
        Args:
            hours: サマリーを計算する時間範囲（時間）
            
        Returns:
            品質サマリー
        """
        quality_score = self.get_quality_score(hours)
        alerts = self.get_alerts(hours=hours)
        
        critical_alerts = [a for a in alerts if a["severity"] == "critical"]
        warning_alerts = [a for a in alerts if a["severity"] == "warning"]
        
        # メトリクス別の統計
        metric_stats = {}
        for name in self.metrics_history:
            if name in self.thresholds:
                stats = self.get_metric_statistics(name, hours)
                metric_stats[name] = stats
        
        return {
            "overall_quality_score": quality_score,
            "total_alerts": len(alerts),
            "critical_alerts": len(critical_alerts),
            "warning_alerts": len(warning_alerts),
            "metric_statistics": metric_stats,
            "thresholds": {
                name: {
                    "warning": threshold.warning_threshold,
                    "critical": threshold.critical_threshold,
                    "description": threshold.description
                }
                for name, threshold in self.thresholds.items()
            }
        }
    
    def export_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """
        メトリクスをエクスポート
        
        Args:
            hours: エクスポートする時間範囲（時間）
            
        Returns:
            エクスポートされたメトリクス
        """
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "time_range_hours": hours,
            "metrics": {},
            "alerts": self.get_alerts(hours=hours),
            "quality_summary": self.get_quality_summary(hours)
        }
        
        for name in self.metrics_history:
            history = self.get_metric_history(name, hours)
            export_data["metrics"][name] = [
                {
                    "value": metric.value,
                    "timestamp": metric.timestamp.isoformat(),
                    "metadata": metric.metadata
                }
                for metric in history
            ]
        
        return export_data
