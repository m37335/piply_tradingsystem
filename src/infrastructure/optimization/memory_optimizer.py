"""
メモリ使用量改善システム

責任:
- メモリリーク検出
- ガベージコレクション最適化
- メモリ使用量監視
- メモリ最適化提案
"""

import gc
import psutil
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


@dataclass
class MemorySnapshot:
    """メモリスナップショット"""
    timestamp: datetime
    memory_usage_mb: float
    memory_percent: float
    available_mb: float
    total_mb: float
    gc_stats: Dict[str, Any]
    object_counts: Dict[str, int]


@dataclass
class MemoryLeak:
    """メモリリーク情報"""
    object_type: str
    count_increase: int
    memory_increase_mb: float
    duration_minutes: int
    severity: str


class MemoryOptimizer:
    """メモリ最適化システム"""
    
    def __init__(self):
        self.snapshots: List[MemorySnapshot] = []
        self.max_snapshots = 100
        self.leak_threshold = 100  # 100個以上のオブジェクト増加でリークと判定
        self.memory_threshold_mb = 50  # 50MB以上の増加でリークと判定
        
    def take_memory_snapshot(self) -> MemorySnapshot:
        """メモリスナップショットを取得"""
        # システムメモリ情報
        memory = psutil.virtual_memory()
        
        # ガベージコレクション統計
        gc.collect()  # 強制GC実行
        gc_stats = {
            'collections': gc.get_stats(),
            'counts': gc.get_count(),
            'thresholds': gc.get_threshold()
        }
        
        # オブジェクト数カウント
        object_counts = self._count_objects()
        
        snapshot = MemorySnapshot(
            timestamp=datetime.now(),
            memory_usage_mb=memory.used / (1024 * 1024),
            memory_percent=memory.percent,
            available_mb=memory.available / (1024 * 1024),
            total_mb=memory.total / (1024 * 1024),
            gc_stats=gc_stats,
            object_counts=object_counts
        )
        
        self.snapshots.append(snapshot)
        
        # スナップショット数を制限
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
        
        return snapshot
    
    def _count_objects(self) -> Dict[str, int]:
        """オブジェクト数をカウント"""
        counts = {}
        
        # 主要なオブジェクトタイプをカウント
        object_types = [
            'dict', 'list', 'tuple', 'str', 'int', 'float',
            'function', 'class', 'module', 'frame', 'traceback'
        ]
        
        for obj_type in object_types:
            try:
                count = len([obj for obj in gc.get_objects() 
                           if type(obj).__name__ == obj_type])
                counts[obj_type] = count
            except Exception as e:
                logger.warning(f"オブジェクトカウントエラー ({obj_type}): {e}")
                counts[obj_type] = 0
        
        return counts
    
    def detect_memory_leaks(self, hours: int = 1) -> List[MemoryLeak]:
        """メモリリークを検出"""
        leaks = []
        
        if len(self.snapshots) < 2:
            return leaks
        
        # 指定時間内のスナップショットを取得
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [
            s for s in self.snapshots 
            if s.timestamp >= cutoff_time
        ]
        
        if len(recent_snapshots) < 2:
            return leaks
        
        # 最初と最後のスナップショットを比較
        first_snapshot = recent_snapshots[0]
        last_snapshot = recent_snapshots[-1]
        
        # メモリ使用量の変化
        memory_increase = last_snapshot.memory_usage_mb - first_snapshot.memory_usage_mb
        duration_minutes = (last_snapshot.timestamp - first_snapshot.timestamp).total_seconds() / 60
        
        # オブジェクト数の変化
        for obj_type in first_snapshot.object_counts:
            if obj_type in last_snapshot.object_counts:
                count_increase = (
                    last_snapshot.object_counts[obj_type] - 
                    first_snapshot.object_counts[obj_type]
                )
                
                # リーク判定
                if (count_increase > self.leak_threshold or 
                    memory_increase > self.memory_threshold_mb):
                    
                    severity = "high" if count_increase > 1000 else "medium"
                    
                    leaks.append(MemoryLeak(
                        object_type=obj_type,
                        count_increase=count_increase,
                        memory_increase_mb=memory_increase,
                        duration_minutes=duration_minutes,
                        severity=severity
                    ))
        
        return leaks
    
    def optimize_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量を最適化"""
        results = {
            "before_mb": 0,
            "after_mb": 0,
            "freed_mb": 0,
            "gc_runs": 0,
            "optimizations": []
        }
        
        # 最適化前のメモリ使用量
        before_snapshot = self.take_memory_snapshot()
        results["before_mb"] = before_snapshot.memory_usage_mb
        
        optimizations = []
        
        # 1. ガベージコレクション実行
        gc.collect()
        results["gc_runs"] += 1
        optimizations.append("ガベージコレクション実行")
        
        # 2. 弱参照のクリア
        try:
            import weakref
            weakref._remove_dead_weakrefs()
            optimizations.append("弱参照クリア")
        except Exception as e:
            logger.warning(f"弱参照クリアエラー: {e}")
        
        # 3. システムキャッシュのクリア
        try:
            import ctypes
            if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'kernel32'):
                ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
                optimizations.append("システムキャッシュクリア")
        except Exception as e:
            logger.warning(f"システムキャッシュクリアエラー: {e}")
        
        # 4. 再度ガベージコレクション実行
        gc.collect()
        results["gc_runs"] += 1
        optimizations.append("最終ガベージコレクション")
        
        # 最適化後のメモリ使用量
        after_snapshot = self.take_memory_snapshot()
        results["after_mb"] = after_snapshot.memory_usage_mb
        results["freed_mb"] = results["before_mb"] - results["after_mb"]
        results["optimizations"] = optimizations
        
        return results
    
    def get_memory_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """メモリ統計情報を取得"""
        if not self.snapshots:
            return {"error": "No snapshots available"}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_snapshots = [
            s for s in self.snapshots 
            if s.timestamp >= cutoff_time
        ]
        
        if not recent_snapshots:
            return {"error": "No recent snapshots"}
        
        # 基本統計
        memory_usage_values = [s.memory_usage_mb for s in recent_snapshots]
        memory_percent_values = [s.memory_percent for s in recent_snapshots]
        
        # オブジェクト統計
        object_stats = defaultdict(list)
        for snapshot in recent_snapshots:
            for obj_type, count in snapshot.object_counts.items():
                object_stats[obj_type].append(count)
        
        # 統計計算
        stats = {
            "period_hours": hours,
            "snapshot_count": len(recent_snapshots),
            "memory_usage": {
                "current_mb": memory_usage_values[-1],
                "average_mb": sum(memory_usage_values) / len(memory_usage_values),
                "min_mb": min(memory_usage_values),
                "max_mb": max(memory_usage_values),
                "trend": "increasing" if memory_usage_values[-1] > memory_usage_values[0] else "decreasing"
            },
            "memory_percent": {
                "current": memory_percent_values[-1],
                "average": sum(memory_percent_values) / len(memory_percent_values),
                "min": min(memory_percent_values),
                "max": max(memory_percent_values)
            },
            "object_counts": {}
        }
        
        # オブジェクト統計
        for obj_type, counts in object_stats.items():
            stats["object_counts"][obj_type] = {
                "current": counts[-1],
                "average": sum(counts) / len(counts),
                "min": min(counts),
                "max": max(counts),
                "trend": "increasing" if counts[-1] > counts[0] else "decreasing"
            }
        
        return stats
    
    def get_memory_recommendations(self) -> List[Dict[str, Any]]:
        """メモリ最適化推奨事項を取得"""
        recommendations = []
        
        if not self.snapshots:
            return recommendations
        
        current_snapshot = self.snapshots[-1]
        
        # メモリ使用率チェック
        if current_snapshot.memory_percent > 80:
            recommendations.append({
                "type": "high_memory_usage",
                "severity": "high",
                "message": f"メモリ使用率が高い: {current_snapshot.memory_percent:.1f}%",
                "action": "メモリ最適化を実行してください"
            })
        
        # オブジェクト数チェック
        for obj_type, count in current_snapshot.object_counts.items():
            if count > 10000:
                recommendations.append({
                    "type": "high_object_count",
                    "severity": "medium",
                    "message": f"{obj_type}オブジェクト数が多い: {count:,}個",
                    "action": f"{obj_type}オブジェクトの使用を最適化してください"
                })
        
        # ガベージコレクション統計チェック
        gc_stats = current_snapshot.gc_stats
        if 'counts' in gc_stats:
            gen0, gen1, gen2 = gc_stats['counts']
            if gen0 > 1000:
                recommendations.append({
                    "type": "frequent_gc",
                    "severity": "medium",
                    "message": f"ガベージコレクションが頻繁: gen0={gen0}",
                    "action": "オブジェクトの作成・破棄パターンを最適化してください"
                })
        
        return recommendations
    
    def monitor_memory_continuously(self, interval_seconds: int = 60, duration_minutes: int = 60):
        """メモリを継続監視"""
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        logger.info(f"メモリ継続監視開始: {interval_seconds}秒間隔, {duration_minutes}分間")
        
        while datetime.now() < end_time:
            try:
                snapshot = self.take_memory_snapshot()
                
                logger.info(
                    f"メモリ使用量: {snapshot.memory_usage_mb:.1f}MB "
                    f"({snapshot.memory_percent:.1f}%)"
                )
                
                # リーク検出
                leaks = self.detect_memory_leaks(hours=1)
                if leaks:
                    logger.warning(f"メモリリーク検出: {len(leaks)}件")
                    for leak in leaks:
                        logger.warning(
                            f"  {leak.object_type}: +{leak.count_increase}個 "
                            f"(+{leak.memory_increase_mb:.1f}MB)"
                        )
                
                time.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("メモリ監視を中断しました")
                break
            except Exception as e:
                logger.error(f"メモリ監視エラー: {e}")
                time.sleep(interval_seconds)
        
        logger.info("メモリ継続監視終了")
    
    def generate_memory_report(self) -> Dict[str, Any]:
        """メモリレポートを生成"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "current_snapshot": None,
            "statistics": self.get_memory_statistics(),
            "leaks": self.detect_memory_leaks(),
            "recommendations": self.get_memory_recommendations()
        }
        
        if self.snapshots:
            report["current_snapshot"] = {
                "memory_usage_mb": self.snapshots[-1].memory_usage_mb,
                "memory_percent": self.snapshots[-1].memory_percent,
                "object_counts": self.snapshots[-1].object_counts
            }
        
        return report
