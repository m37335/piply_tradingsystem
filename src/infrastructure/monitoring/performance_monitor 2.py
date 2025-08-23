import asyncio
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import psutil
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_usage_percent: float
    database_size_mb: float
    active_connections: int
    query_execution_time_ms: float
    data_processing_time_ms: float
    error_count: int
    success_count: int


class PerformanceMonitor:
    """パフォーマンス監視システム"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        self.start_time = datetime.now()

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """システムメトリクスを収集"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # メモリ使用量
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_mb = memory.used / (1024 * 1024)

            # ディスク使用量
            disk = psutil.disk_usage("/app")
            disk_usage_percent = disk.percent

            # データベースサイズ
            db_size_mb = await self._get_database_size()

            # アクティブ接続数
            active_connections = await self._get_active_connections()

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_mb": memory_mb,
                "disk_usage_percent": disk_usage_percent,
                "database_size_mb": db_size_mb,
                "active_connections": active_connections,
            }
        except Exception as e:
            logger.error(f"システムメトリクス収集エラー: {e}")
            return {}

    async def measure_query_performance(
        self, query_func, *args, **kwargs
    ) -> Dict[str, Any]:
        """クエリパフォーマンスを測定"""
        start_time = time.time()
        try:
            result = await query_func(*args, **kwargs)
            execution_time_ms = (time.time() - start_time) * 1000
            return {
                "success": True,
                "execution_time_ms": execution_time_ms,
                "result": result,
            }
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"クエリ実行エラー: {e}")
            return {
                "success": False,
                "execution_time_ms": execution_time_ms,
                "error": str(e),
            }

    async def measure_data_processing_performance(
        self, processing_func, *args, **kwargs
    ) -> Dict[str, Any]:
        """データ処理パフォーマンスを測定"""
        start_time = time.time()
        try:
            result = await processing_func(*args, **kwargs)
            processing_time_ms = (time.time() - start_time) * 1000
            return {
                "success": True,
                "processing_time_ms": processing_time_ms,
                "result": result,
            }
        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(f"データ処理エラー: {e}")
            return {
                "success": False,
                "processing_time_ms": processing_time_ms,
                "error": str(e),
            }

    async def _get_database_size(self) -> float:
        """データベースサイズを取得（MB）"""
        try:
            result = await self.session.execute(
                text(
                    """
                SELECT page_count * page_size as size_bytes
                FROM pragma_page_count(), pragma_page_size()
            """
                )
            )
            size_bytes = result.scalar()
            return size_bytes / (1024 * 1024) if size_bytes else 0
        except Exception as e:
            logger.error(f"データベースサイズ取得エラー: {e}")
            return 0

    async def _get_active_connections(self) -> int:
        """アクティブ接続数を取得"""
        try:
            result = await self.session.execute(
                text(
                    """
                SELECT COUNT(*) FROM pragma_database_list()
            """
                )
            )
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"アクティブ接続数取得エラー: {e}")
            return 0

    async def collect_comprehensive_metrics(self) -> PerformanceMetrics:
        """包括的なメトリクスを収集"""
        system_metrics = await self.collect_system_metrics()

        # サンプルクエリのパフォーマンス測定
        query_result = await self.measure_query_performance(self._sample_query)

        # サンプルデータ処理のパフォーマンス測定
        processing_result = await self.measure_data_processing_performance(
            self._sample_data_processing
        )

        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            cpu_percent=system_metrics.get("cpu_percent", 0),
            memory_percent=system_metrics.get("memory_percent", 0),
            memory_mb=system_metrics.get("memory_mb", 0),
            disk_usage_percent=system_metrics.get("disk_usage_percent", 0),
            database_size_mb=system_metrics.get("database_size_mb", 0),
            active_connections=system_metrics.get("active_connections", 0),
            query_execution_time_ms=query_result.get("execution_time_ms", 0),
            data_processing_time_ms=processing_result.get("processing_time_ms", 0),
            error_count=(
                0
                if query_result.get("success", False)
                and processing_result.get("success", False)
                else 1
            ),
            success_count=(
                1
                if query_result.get("success", False)
                and processing_result.get("success", False)
                else 0
            ),
        )

        self.metrics_history.append(metrics)

        # 履歴サイズを制限
        if len(self.metrics_history) > self.max_history_size:
            self.metrics_history = self.metrics_history[-self.max_history_size :]

        return metrics

    async def _sample_query(self) -> Dict[str, Any]:
        """サンプルクエリ（パフォーマンス測定用）"""
        result = await self.session.execute(
            text(
                """
            SELECT COUNT(*) as count, 
                   MAX(timestamp) as latest_timestamp
            FROM price_data 
            WHERE timestamp >= datetime('now', '-1 hour')
        """
            )
        )
        row = result.fetchone()
        return {
            "count": row[0] if row else 0,
            "latest_timestamp": row[1] if row else None,
        }

    async def _sample_data_processing(self) -> Dict[str, Any]:
        """サンプルデータ処理（パフォーマンス測定用）"""
        # 実際のデータ処理をシミュレート
        await asyncio.sleep(0.01)  # 10msの処理時間をシミュレート
        return {"processed": True}

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンスサマリーを取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        if not recent_metrics:
            return {"error": "No metrics available"}

        return {
            "period_hours": hours,
            "total_measurements": len(recent_metrics),
            "avg_cpu_percent": sum(m.cpu_percent for m in recent_metrics)
            / len(recent_metrics),
            "avg_memory_percent": sum(m.memory_percent for m in recent_metrics)
            / len(recent_metrics),
            "avg_query_time_ms": sum(m.query_execution_time_ms for m in recent_metrics)
            / len(recent_metrics),
            "avg_processing_time_ms": sum(
                m.data_processing_time_ms for m in recent_metrics
            )
            / len(recent_metrics),
            "total_errors": sum(m.error_count for m in recent_metrics),
            "total_successes": sum(m.success_count for m in recent_metrics),
            "uptime_hours": (datetime.now() - self.start_time).total_seconds() / 3600,
        }

    def get_alerts(self) -> List[Dict[str, Any]]:
        """アラートを生成"""
        alerts = []

        if not self.metrics_history:
            return alerts

        latest = self.metrics_history[-1]

        # CPU使用率アラート
        if latest.cpu_percent > 80:
            alerts.append(
                {
                    "type": "high_cpu",
                    "severity": "warning",
                    "message": f"CPU使用率が高い: {latest.cpu_percent:.1f}%",
                    "timestamp": latest.timestamp,
                }
            )

        # メモリ使用率アラート
        if latest.memory_percent > 85:
            alerts.append(
                {
                    "type": "high_memory",
                    "severity": "warning",
                    "message": f"メモリ使用率が高い: {latest.memory_percent:.1f}%",
                    "timestamp": latest.timestamp,
                }
            )

        # クエリ実行時間アラート
        if latest.query_execution_time_ms > 1000:
            alerts.append(
                {
                    "type": "slow_query",
                    "severity": "warning",
                    "message": f"クエリ実行時間が長い: {latest.query_execution_time_ms:.1f}ms",
                    "timestamp": latest.timestamp,
                }
            )

        # エラー率アラート
        total_operations = latest.error_count + latest.success_count
        if total_operations > 0 and latest.error_count / total_operations > 0.1:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "severity": "error",
                    "message": f"エラー率が高い: {latest.error_count}/{total_operations}",
                    "timestamp": latest.timestamp,
                }
            )

        return alerts
