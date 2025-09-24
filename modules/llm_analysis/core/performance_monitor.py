#!/usr/bin/env python3
"""
パフォーマンス監視モジュール

三層ゲート式フィルタリングシステムのパフォーマンスを監視し、
最適化のための指標を提供します。
"""

import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """パフォーマンス指標"""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceStats:
    """パフォーマンス統計"""
    metric_name: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    p99_value: float
    last_value: float
    last_updated: datetime


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self, max_history: int = 1000):
        """
        初期化
        
        Args:
            max_history: 保持する履歴の最大数
        """
        self.max_history = max_history
        self.metrics_history: Dict[str, deque] = {}
        self.stats_cache: Dict[str, PerformanceStats] = {}
        self.logger = logging.getLogger(__name__)
        
        # 監視対象のメトリクス
        self.monitored_metrics = {
            'gate1_evaluation_time': 'GATE 1評価時間',
            'gate2_evaluation_time': 'GATE 2評価時間', 
            'gate3_evaluation_time': 'GATE 3評価時間',
            'total_evaluation_time': '総評価時間',
            'pattern_loading_time': 'パターン読み込み時間',
            'technical_calculation_time': 'テクニカル計算時間',
            'database_query_time': 'データベースクエリ時間',
            'signal_generation_time': 'シグナル生成時間'
        }
    
    def record_metric(self, name: str, value: float, metadata: Dict[str, Any] = None):
        """
        メトリクスを記録
        
        Args:
            name: メトリクス名
            value: 値
            metadata: 追加メタデータ
        """
        if metadata is None:
            metadata = {}
        
        metric = PerformanceMetric(
            name=name,
            value=value,
            timestamp=datetime.now(timezone.utc),
            metadata=metadata
        )
        
        # 履歴に追加
        if name not in self.metrics_history:
            self.metrics_history[name] = deque(maxlen=self.max_history)
        
        self.metrics_history[name].append(metric)
        
        # 統計キャッシュを無効化
        if name in self.stats_cache:
            del self.stats_cache[name]
        
        self.logger.debug(f"メトリクス記録: {name} = {value:.4f}s")
    
    def get_stats(self, metric_name: str) -> Optional[PerformanceStats]:
        """
        指定されたメトリクスの統計を取得
        
        Args:
            metric_name: メトリクス名
            
        Returns:
            パフォーマンス統計、またはNone
        """
        if metric_name not in self.metrics_history:
            return None
        
        # キャッシュから取得
        if metric_name in self.stats_cache:
            return self.stats_cache[metric_name]
        
        # 統計を計算
        metrics = list(self.metrics_history[metric_name])
        if not metrics:
            return None
        
        values = [m.value for m in metrics]
        
        stats = PerformanceStats(
            metric_name=metric_name,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            median_value=statistics.median(values),
            p95_value=self._percentile(values, 95),
            p99_value=self._percentile(values, 99),
            last_value=values[-1],
            last_updated=metrics[-1].timestamp
        )
        
        # キャッシュに保存
        self.stats_cache[metric_name] = stats
        
        return stats
    
    def get_all_stats(self) -> Dict[str, PerformanceStats]:
        """
        すべてのメトリクスの統計を取得
        
        Returns:
            メトリクス名をキーとした統計の辞書
        """
        all_stats = {}
        for metric_name in self.metrics_history.keys():
            stats = self.get_stats(metric_name)
            if stats:
                all_stats[metric_name] = stats
        
        return all_stats
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        パフォーマンスサマリーを取得
        
        Returns:
            パフォーマンスサマリー
        """
        summary = {
            'total_metrics': len(self.metrics_history),
            'monitored_metrics': list(self.monitored_metrics.keys()),
            'stats': {},
            'recommendations': []
        }
        
        # 各メトリクスの統計を取得
        for metric_name in self.monitored_metrics.keys():
            stats = self.get_stats(metric_name)
            if stats:
                summary['stats'][metric_name] = {
                    'display_name': self.monitored_metrics[metric_name],
                    'count': stats.count,
                    'avg': stats.avg_value,
                    'p95': stats.p95_value,
                    'last': stats.last_value
                }
        
        # 推奨事項を生成
        summary['recommendations'] = self._generate_recommendations(summary['stats'])
        
        return summary
    
    def _percentile(self, values: List[float], percentile: int) -> float:
        """
        パーセンタイル値を計算
        
        Args:
            values: 値のリスト
            percentile: パーセンタイル（0-100）
            
        Returns:
            パーセンタイル値
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int((percentile / 100) * (len(sorted_values) - 1))
        return sorted_values[index]
    
    def _generate_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """
        パフォーマンス改善の推奨事項を生成
        
        Args:
            stats: 統計データ
            
        Returns:
            推奨事項のリスト
        """
        recommendations = []
        
        # GATE評価時間のチェック
        for gate in ['gate1', 'gate2', 'gate3']:
            metric_name = f'{gate}_evaluation_time'
            if metric_name in stats:
                avg_time = stats[metric_name]['avg']
                if avg_time > 1.0:  # 1秒以上
                    recommendations.append(
                        f"{stats[metric_name]['display_name']}が{avg_time:.2f}秒と長いです。"
                        "パターン条件の最適化を検討してください。"
                    )
        
        # 総評価時間のチェック
        if 'total_evaluation_time' in stats:
            total_time = stats['total_evaluation_time']['avg']
            if total_time > 5.0:  # 5秒以上
                recommendations.append(
                    f"総評価時間が{total_time:.2f}秒と長いです。"
                    "並列処理の導入を検討してください。"
                )
        
        # データベースクエリ時間のチェック
        if 'database_query_time' in stats:
            db_time = stats['database_query_time']['avg']
            if db_time > 0.5:  # 0.5秒以上
                recommendations.append(
                    f"データベースクエリ時間が{db_time:.2f}秒と長いです。"
                    "インデックスの最適化やクエリの見直しを検討してください。"
                )
        
        # パターン読み込み時間のチェック
        if 'pattern_loading_time' in stats:
            load_time = stats['pattern_loading_time']['avg']
            if load_time > 0.1:  # 0.1秒以上
                recommendations.append(
                    f"パターン読み込み時間が{load_time:.2f}秒と長いです。"
                    "キャッシュの最適化を検討してください。"
                )
        
        return recommendations
    
    def clear_history(self, metric_name: str = None):
        """
        履歴をクリア
        
        Args:
            metric_name: 特定のメトリクス名（Noneの場合はすべて）
        """
        if metric_name:
            if metric_name in self.metrics_history:
                self.metrics_history[metric_name].clear()
                if metric_name in self.stats_cache:
                    del self.stats_cache[metric_name]
                self.logger.info(f"メトリクス履歴をクリアしました: {metric_name}")
        else:
            self.metrics_history.clear()
            self.stats_cache.clear()
            self.logger.info("すべてのメトリクス履歴をクリアしました")
    
    def export_stats(self) -> Dict[str, Any]:
        """
        統計データをエクスポート
        
        Returns:
            エクスポート用の統計データ
        """
        export_data = {
            'export_timestamp': datetime.now(timezone.utc).isoformat(),
            'summary': self.get_performance_summary(),
            'detailed_stats': {}
        }
        
        # 詳細統計を追加
        for metric_name, stats in self.get_all_stats().items():
            export_data['detailed_stats'][metric_name] = {
                'count': stats.count,
                'min': stats.min_value,
                'max': stats.max_value,
                'avg': stats.avg_value,
                'median': stats.median_value,
                'p95': stats.p95_value,
                'p99': stats.p99_value,
                'last': stats.last_value,
                'last_updated': stats.last_updated.isoformat()
            }
        
        return export_data


# グローバルインスタンス
performance_monitor = PerformanceMonitor()


def measure_time(metric_name: str, metadata: Dict[str, Any] = None):
    """
    実行時間を測定するデコレータ
    
    Args:
        metric_name: メトリクス名
        metadata: 追加メタデータ
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                performance_monitor.record_metric(metric_name, execution_time, metadata)
        
        return wrapper
    return decorator


def measure_async_time(metric_name: str, metadata: Dict[str, Any] = None):
    """
    非同期関数の実行時間を測定するデコレータ
    
    Args:
        metric_name: メトリクス名
        metadata: 追加メタデータ
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                execution_time = end_time - start_time
                performance_monitor.record_metric(metric_name, execution_time, metadata)
        
        return wrapper
    return decorator
