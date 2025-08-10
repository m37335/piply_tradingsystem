#!/usr/bin/env python3
"""
パフォーマンス監視システム
"""

import asyncio
import time
import psutil
import gc
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, asdict

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.monitoring.log_manager import LogManager
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


@dataclass
class PerformanceMetrics:
    """パフォーマンスメトリクス"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_io: Dict[str, float]
    process_count: int
    thread_count: int
    gc_stats: Dict[str, Any]
    database_connections: int
    active_tasks: int
    response_times: Dict[str, float]
    error_rate: float
    throughput: Dict[str, int]


@dataclass
class PerformanceAlert:
    """パフォーマンスアラート"""
    alert_type: str
    severity: str
    message: str
    metrics: Dict[str, Any]
    timestamp: str
    threshold: float
    current_value: float


class PerformanceMonitor:
    """
    パフォーマンス監視システム
    """
    
    def __init__(self, config_manager: SystemConfigManager, log_manager: LogManager):
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.metrics_history: deque = deque(maxlen=1000)  # 最新1000件を保持
        self.alerts_history: List[PerformanceAlert] = []
        self.performance_thresholds = self._load_performance_thresholds()
        self.monitoring_active = False
        self.monitoring_task = None
        
        # パフォーマンス統計
        self.operation_times: Dict[str, List[float]] = defaultdict(list)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.throughput_counts: Dict[str, int] = defaultdict(int)
        
        # 監視間隔
        self.monitoring_interval = self.config_manager.get("performance.monitoring_interval", 60)
        self.alert_cooldown = self.config_manager.get("performance.alert_cooldown", 300)
        self.last_alert_time: Dict[str, float] = {}
    
    def _load_performance_thresholds(self) -> Dict[str, Dict[str, float]]:
        """パフォーマンス閾値を読み込み"""
        return {
            "cpu": {
                "warning": self.config_manager.get("performance.cpu_warning", 70.0),
                "critical": self.config_manager.get("performance.cpu_critical", 90.0)
            },
            "memory": {
                "warning": self.config_manager.get("performance.memory_warning", 80.0),
                "critical": self.config_manager.get("performance.memory_critical", 95.0)
            },
            "disk": {
                "warning": self.config_manager.get("performance.disk_warning", 85.0),
                "critical": self.config_manager.get("performance.disk_critical", 95.0)
            },
            "response_time": {
                "warning": self.config_manager.get("performance.response_time_warning", 5.0),
                "critical": self.config_manager.get("performance.response_time_critical", 10.0)
            },
            "error_rate": {
                "warning": self.config_manager.get("performance.error_rate_warning", 5.0),
                "critical": self.config_manager.get("performance.error_rate_critical", 10.0)
            }
        }
    
    async def start_monitoring(self):
        """パフォーマンス監視を開始"""
        if self.monitoring_active:
            logger.warning("パフォーマンス監視は既に開始されています")
            return
        
        self.monitoring_active = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("パフォーマンス監視を開始しました")
    
    async def stop_monitoring(self):
        """パフォーマンス監視を停止"""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("パフォーマンス監視を停止しました")
    
    async def _monitoring_loop(self):
        """監視ループ"""
        while self.monitoring_active:
            try:
                # パフォーマンスメトリクスを収集
                metrics = await self._collect_performance_metrics()
                self.metrics_history.append(metrics)
                
                # アラートをチェック
                await self._check_performance_alerts(metrics)
                
                # パフォーマンス統計を更新
                await self._update_performance_statistics(metrics)
                
                # 設定された間隔で待機
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"パフォーマンス監視中にエラーが発生: {e}")
                await asyncio.sleep(10)  # エラー時は10秒待機
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """パフォーマンスメトリクスを収集"""
        try:
            # システムメトリクス
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # ネットワークI/O
            network_io = psutil.net_io_counters()
            network_stats = {
                "bytes_sent": network_io.bytes_sent,
                "bytes_recv": network_io.bytes_recv,
                "packets_sent": network_io.packets_sent,
                "packets_recv": network_io.packets_recv
            }
            
            # プロセス情報
            process = psutil.Process()
            thread_count = process.num_threads()
            
            # ガベージコレクション統計
            gc_stats = {
                "collections": gc.get_stats(),
                "count": gc.get_count(),
                "objects": len(gc.get_objects())
            }
            
            # データベース接続数（推定）
            database_connections = await self._get_database_connection_count()
            
            # アクティブタスク数
            active_tasks = len([task for task in asyncio.all_tasks() if not task.done()])
            
            # レスポンスタイム統計
            response_times = self._calculate_average_response_times()
            
            # エラー率
            error_rate = self._calculate_error_rate()
            
            # スループット統計
            throughput = self._calculate_throughput()
            
            metrics = PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                network_io=network_stats,
                process_count=len(psutil.pids()),
                thread_count=thread_count,
                gc_stats=gc_stats,
                database_connections=database_connections,
                active_tasks=active_tasks,
                response_times=response_times,
                error_rate=error_rate,
                throughput=throughput
            )
            
            return metrics
            
        except Exception as e:
            logger.error(f"パフォーマンスメトリクス収集中にエラー: {e}")
            # エラー時はデフォルト値を返す
            return PerformanceMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                disk_usage_percent=0.0,
                network_io={},
                process_count=0,
                thread_count=0,
                gc_stats={},
                database_connections=0,
                active_tasks=0,
                response_times={},
                error_rate=0.0,
                throughput={}
            )
    
    async def _get_database_connection_count(self) -> int:
        """データベース接続数を取得"""
        try:
            # 実際の実装では、データベース接続プールから取得
            # 現在は推定値を使用
            return len([task for task in asyncio.all_tasks() 
                       if 'database' in str(task).lower()])
        except Exception:
            return 0
    
    def _calculate_average_response_times(self) -> Dict[str, float]:
        """平均レスポンスタイムを計算"""
        response_times = {}
        for operation, times in self.operation_times.items():
            if times:
                response_times[operation] = sum(times) / len(times)
        return response_times
    
    def _calculate_error_rate(self) -> float:
        """エラー率を計算"""
        total_errors = sum(self.error_counts.values())
        total_operations = sum(self.throughput_counts.values())
        
        if total_operations == 0:
            return 0.0
        
        return (total_errors / total_operations) * 100
    
    def _calculate_throughput(self) -> Dict[str, int]:
        """スループットを計算"""
        return dict(self.throughput_counts)
    
    async def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """パフォーマンスアラートをチェック"""
        current_time = time.time()
        
        # CPU使用率チェック
        await self._check_cpu_alert(metrics, current_time)
        
        # メモリ使用率チェック
        await self._check_memory_alert(metrics, current_time)
        
        # ディスク使用率チェック
        await self._check_disk_alert(metrics, current_time)
        
        # レスポンスタイムチェック
        await self._check_response_time_alert(metrics, current_time)
        
        # エラー率チェック
        await self._check_error_rate_alert(metrics, current_time)
    
    async def _check_cpu_alert(self, metrics: PerformanceMetrics, current_time: float):
        """CPU使用率アラートをチェック"""
        thresholds = self.performance_thresholds["cpu"]
        
        if metrics.cpu_percent >= thresholds["critical"]:
            await self._create_alert("CPU_CRITICAL", "CRITICAL", 
                                   f"CPU使用率が危険レベル: {metrics.cpu_percent:.1f}%",
                                   metrics, current_time, thresholds["critical"], 
                                   metrics.cpu_percent)
        elif metrics.cpu_percent >= thresholds["warning"]:
            await self._create_alert("CPU_WARNING", "WARNING", 
                                   f"CPU使用率が警告レベル: {metrics.cpu_percent:.1f}%",
                                   metrics, current_time, thresholds["warning"], 
                                   metrics.cpu_percent)
    
    async def _check_memory_alert(self, metrics: PerformanceMetrics, current_time: float):
        """メモリ使用率アラートをチェック"""
        thresholds = self.performance_thresholds["memory"]
        
        if metrics.memory_percent >= thresholds["critical"]:
            await self._create_alert("MEMORY_CRITICAL", "CRITICAL", 
                                   f"メモリ使用率が危険レベル: {metrics.memory_percent:.1f}%",
                                   metrics, current_time, thresholds["critical"], 
                                   metrics.memory_percent)
        elif metrics.memory_percent >= thresholds["warning"]:
            await self._create_alert("MEMORY_WARNING", "WARNING", 
                                   f"メモリ使用率が警告レベル: {metrics.memory_percent:.1f}%",
                                   metrics, current_time, thresholds["warning"], 
                                   metrics.memory_percent)
    
    async def _check_disk_alert(self, metrics: PerformanceMetrics, current_time: float):
        """ディスク使用率アラートをチェック"""
        thresholds = self.performance_thresholds["disk"]
        
        if metrics.disk_usage_percent >= thresholds["critical"]:
            await self._create_alert("DISK_CRITICAL", "CRITICAL", 
                                   f"ディスク使用率が危険レベル: {metrics.disk_usage_percent:.1f}%",
                                   metrics, current_time, thresholds["critical"], 
                                   metrics.disk_usage_percent)
        elif metrics.disk_usage_percent >= thresholds["warning"]:
            await self._create_alert("DISK_WARNING", "WARNING", 
                                   f"ディスク使用率が警告レベル: {metrics.disk_usage_percent:.1f}%",
                                   metrics, current_time, thresholds["warning"], 
                                   metrics.disk_usage_percent)
    
    async def _check_response_time_alert(self, metrics: PerformanceMetrics, current_time: float):
        """レスポンスタイムアラートをチェック"""
        thresholds = self.performance_thresholds["response_time"]
        
        for operation, response_time in metrics.response_times.items():
            if response_time >= thresholds["critical"]:
                await self._create_alert("RESPONSE_TIME_CRITICAL", "CRITICAL", 
                                       f"レスポンスタイムが危険レベル: {operation}={response_time:.2f}s",
                                       metrics, current_time, thresholds["critical"], 
                                       response_time)
            elif response_time >= thresholds["warning"]:
                await self._create_alert("RESPONSE_TIME_WARNING", "WARNING", 
                                       f"レスポンスタイムが警告レベル: {operation}={response_time:.2f}s",
                                       metrics, current_time, thresholds["warning"], 
                                       response_time)
    
    async def _check_error_rate_alert(self, metrics: PerformanceMetrics, current_time: float):
        """エラー率アラートをチェック"""
        thresholds = self.performance_thresholds["error_rate"]
        
        if metrics.error_rate >= thresholds["critical"]:
            await self._create_alert("ERROR_RATE_CRITICAL", "CRITICAL", 
                                   f"エラー率が危険レベル: {metrics.error_rate:.1f}%",
                                   metrics, current_time, thresholds["critical"], 
                                   metrics.error_rate)
        elif metrics.error_rate >= thresholds["warning"]:
            await self._create_alert("ERROR_RATE_WARNING", "WARNING", 
                                   f"エラー率が警告レベル: {metrics.error_rate:.1f}%",
                                   metrics, current_time, thresholds["warning"], 
                                   metrics.error_rate)
    
    async def _create_alert(self, alert_type: str, severity: str, message: str, 
                           metrics: PerformanceMetrics, current_time: float, 
                           threshold: float, current_value: float):
        """アラートを作成"""
        # クールダウン期間をチェック
        if alert_type in self.last_alert_time:
            if current_time - self.last_alert_time[alert_type] < self.alert_cooldown:
                return
        
        alert = PerformanceAlert(
            alert_type=alert_type,
            severity=severity,
            message=message,
            metrics=asdict(metrics),
            timestamp=datetime.now().isoformat(),
            threshold=threshold,
            current_value=current_value
        )
        
        self.alerts_history.append(alert)
        self.last_alert_time[alert_type] = current_time
        
        # ログに記録
        await self.log_manager.log_system_event(
            "PERFORMANCE_ALERT",
            message,
            level=severity,
            additional_data=asdict(alert)
        )
        
        # Discordに通知
        await self._send_performance_alert_to_discord(alert)
        
        logger.warning(f"パフォーマンスアラート: {message}")
    
    async def _send_performance_alert_to_discord(self, alert: PerformanceAlert):
        """パフォーマンスアラートをDiscordに送信"""
        try:
            webhook_url = self.config_manager.get("notifications.discord_monitoring.webhook_url")
            if not webhook_url:
                webhook_url = self.config_manager.get("notifications.discord.webhook_url")
            
            if webhook_url:
                async with DiscordWebhookSender(webhook_url) as sender:
                    color = 0xFF0000 if alert.severity == "CRITICAL" else 0xFFA500
                    
                    embed = {
                        "title": f"🚨 パフォーマンスアラート: {alert.alert_type}",
                        "description": alert.message,
                        "color": color,
                        "timestamp": alert.timestamp,
                        "fields": [
                            {
                                "name": "重要度",
                                "value": alert.severity,
                                "inline": True
                            },
                            {
                                "name": "閾値",
                                "value": f"{alert.threshold}",
                                "inline": True
                            },
                            {
                                "name": "現在値",
                                "value": f"{alert.current_value:.2f}",
                                "inline": True
                            },
                            {
                                "name": "システム状態",
                                "value": f"CPU: {alert.metrics.get('cpu_percent', 'N/A')}%\n"
                                        f"メモリ: {alert.metrics.get('memory_percent', 'N/A')}%\n"
                                        f"ディスク: {alert.metrics.get('disk_usage_percent', 'N/A')}%",
                                "inline": False
                            }
                        ]
                    }
                    
                    await sender.send_embed(embed)
                    logger.info(f"パフォーマンスアラートをDiscordに送信: {alert.alert_type}")
                    
        except Exception as e:
            logger.error(f"パフォーマンスアラートのDiscord送信に失敗: {e}")
    
    async def _update_performance_statistics(self, metrics: PerformanceMetrics):
        """パフォーマンス統計を更新"""
        # 統計データをクリア（古いデータを削除）
        if len(self.operation_times) > 100:
            for operation in list(self.operation_times.keys()):
                if len(self.operation_times[operation]) > 50:
                    self.operation_times[operation] = self.operation_times[operation][-50:]
    
    def record_operation_time(self, operation: str, duration: float):
        """操作時間を記録"""
        self.operation_times[operation].append(duration)
    
    def record_error(self, operation: str):
        """エラーを記録"""
        self.error_counts[operation] += 1
    
    def record_throughput(self, operation: str):
        """スループットを記録"""
        self.throughput_counts[operation] += 1
    
    async def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """パフォーマンスレポートを取得"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            recent_metrics = [
                metrics for metrics in self.metrics_history
                if datetime.fromisoformat(metrics.timestamp) > cutoff_time
            ]
            
            if not recent_metrics:
                return {"message": "データがありません"}
            
            # 統計を計算
            cpu_values = [m.cpu_percent for m in recent_metrics]
            memory_values = [m.memory_percent for m in recent_metrics]
            disk_values = [m.disk_usage_percent for m in recent_metrics]
            
            # アラート統計
            recent_alerts = [
                alert for alert in self.alerts_history
                if datetime.fromisoformat(alert.timestamp) > cutoff_time
            ]
            
            alert_counts = defaultdict(int)
            for alert in recent_alerts:
                alert_counts[alert.alert_type] += 1
            
            return {
                "period_hours": hours,
                "metrics_count": len(recent_metrics),
                "alerts_count": len(recent_alerts),
                "cpu": {
                    "average": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "average": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values)
                },
                "disk": {
                    "average": sum(disk_values) / len(disk_values),
                    "max": max(disk_values),
                    "min": min(disk_values)
                },
                "alerts": dict(alert_counts),
                "latest_metrics": asdict(recent_metrics[-1]) if recent_metrics else None
            }
            
        except Exception as e:
            logger.error(f"パフォーマンスレポート取得中にエラー: {e}")
            return {"error": str(e)}
    
    async def send_performance_report_to_discord(self, hours: int = 24):
        """パフォーマンスレポートをDiscordに送信"""
        try:
            report = await self.get_performance_report(hours)
            
            if "error" in report:
                logger.error(f"パフォーマンスレポート取得エラー: {report['error']}")
                return
            
            webhook_url = self.config_manager.get("notifications.discord_monitoring.webhook_url")
            if not webhook_url:
                webhook_url = self.config_manager.get("notifications.discord.webhook_url")
            
            if webhook_url:
                async with DiscordWebhookSender(webhook_url) as sender:
                    embed = {
                        "title": f"📊 パフォーマンスレポート ({hours}時間)",
                        "description": f"監視期間: {hours}時間\nメトリクス数: {report['metrics_count']}\nアラート数: {report['alerts_count']}",
                        "color": 0x00FF00,
                        "timestamp": datetime.now().isoformat(),
                        "fields": [
                            {
                                "name": "CPU使用率",
                                "value": f"平均: {report['cpu']['average']:.1f}%\n"
                                        f"最大: {report['cpu']['max']:.1f}%\n"
                                        f"最小: {report['cpu']['min']:.1f}%",
                                "inline": True
                            },
                            {
                                "name": "メモリ使用率",
                                "value": f"平均: {report['memory']['average']:.1f}%\n"
                                        f"最大: {report['memory']['max']:.1f}%\n"
                                        f"最小: {report['memory']['min']:.1f}%",
                                "inline": True
                            },
                            {
                                "name": "ディスク使用率",
                                "value": f"平均: {report['disk']['average']:.1f}%\n"
                                        f"最大: {report['disk']['max']:.1f}%\n"
                                        f"最小: {report['disk']['min']:.1f}%",
                                "inline": True
                            }
                        ]
                    }
                    
                    if report['alerts']:
                        alert_text = "\n".join([f"• {k}: {v}回" for k, v in report['alerts'].items()])
                        embed["fields"].append({
                            "name": "アラート統計",
                            "value": alert_text,
                            "inline": False
                        })
                    
                    await sender.send_embed(embed)
                    logger.info(f"パフォーマンスレポートをDiscordに送信 ({hours}時間)")
                    
        except Exception as e:
            logger.error(f"パフォーマンスレポートのDiscord送信に失敗: {e}")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """現在のメトリクスを取得"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def clear_history(self):
        """履歴をクリア"""
        self.metrics_history.clear()
        self.alerts_history.clear()
        self.last_alert_time.clear()
        logger.info("パフォーマンス履歴をクリアしました")
