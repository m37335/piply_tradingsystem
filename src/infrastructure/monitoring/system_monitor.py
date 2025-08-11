#!/usr/bin/env python3
"""
システム監視サービス

USD/JPY特化の5分おきデータ取得システムの監視機能
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from src.infrastructure.config.system_config_manager import SystemConfigManager
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class SystemMonitor:
    """
    システム監視クラス
    """

    def __init__(self, config_manager: SystemConfigManager):
        self.config_manager = config_manager
        self.monitoring_data = {}
        self.alert_history = []
        self.start_time = datetime.now()
        self.is_running = False

    async def start_monitoring(self):
        """
        監視を開始
        """
        logger.info("Starting system monitoring...")
        self.is_running = True

        try:
            while self.is_running:
                # システムメトリクスを収集
                await self._collect_system_metrics()

                # データベースヘルスチェック
                await self._check_database_health()

                # データ取得状況をチェック
                await self._check_data_fetch_status()

                # パフォーマンスをチェック
                await self._check_performance()

                # アラートを処理
                await self._process_alerts()

                # 監視間隔で待機
                interval = self.config_manager.get("system.health_check_interval", 300)
                await asyncio.sleep(interval)

        except Exception as e:
            logger.error(f"System monitoring error: {e}")
            await self._send_alert("SYSTEM_ERROR", f"監視システムエラー: {e}")

    async def stop_monitoring(self):
        """
        監視を停止
        """
        logger.info("Stopping system monitoring...")
        self.is_running = False

    async def _collect_system_metrics(self):
        """
        システムメトリクスを収集
        """
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # メモリ使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # ディスク使用率
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            # ネットワーク使用量
            network = psutil.net_io_counters()

            # プロセス情報
            process = psutil.Process()
            process_memory = process.memory_info().rss / 1024 / 1024  # MB

            self.monitoring_data = {
                "timestamp": datetime.now(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "process_memory_mb": process_memory,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            }

            logger.debug(
                f"System metrics collected: CPU={cpu_percent}%, Memory={memory_percent}%"
            )

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    async def _check_database_health(self):
        """
        データベースヘルスチェック
        """
        try:
            session = await get_async_session()

            # 接続テスト
            await session.execute("SELECT 1")

            # テーブル存在確認
            tables = ["price_data", "technical_indicators", "pattern_detections"]
            for table in tables:
                result = await session.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                logger.debug(f"Table {table}: {count} records")

            await session.close()

            self.monitoring_data["database_healthy"] = True
            logger.debug("Database health check passed")

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.monitoring_data["database_healthy"] = False
            await self._send_alert("DATABASE_ERROR", f"データベース接続エラー: {e}")

    async def _check_data_fetch_status(self):
        """
        データ取得状況をチェック
        """
        try:
            session = await get_async_session()

            # 最新のデータ取得時刻を確認
            result = await session.execute(
                "SELECT MAX(timestamp) FROM price_data WHERE timeframe = '5m'"
            )
            latest_fetch = result.scalar()

            if latest_fetch:
                time_diff = datetime.now() - latest_fetch
                minutes_since_last_fetch = time_diff.total_seconds() / 60

                self.monitoring_data[
                    "minutes_since_last_fetch"
                ] = minutes_since_last_fetch

                # 5分以上データが取得されていない場合はアラート
                if minutes_since_last_fetch > 10:
                    await self._send_alert(
                        "DATA_FETCH_WARNING",
                        f"データ取得が遅延しています: {minutes_since_last_fetch:.1f}分前",
                    )
                else:
                    logger.debug(
                        f"Data fetch status OK: {minutes_since_last_fetch:.1f} minutes ago"
                    )
            else:
                await self._send_alert("DATA_FETCH_ERROR", "データが取得されていません")

            await session.close()

        except Exception as e:
            logger.error(f"Data fetch status check failed: {e}")

    async def _check_performance(self):
        """
        パフォーマンスをチェック
        """
        try:
            # CPU使用率チェック
            cpu_threshold = self.config_manager.get("performance.max_cpu_usage", 80.0)
            if self.monitoring_data.get("cpu_percent", 0) > cpu_threshold:
                await self._send_alert(
                    "PERFORMANCE_WARNING",
                    f"CPU使用率が高いです: {self.monitoring_data['cpu_percent']}%",
                )

            # メモリ使用率チェック
            memory_threshold = self.config_manager.get(
                "performance.max_memory_usage", 2147483648
            )
            memory_usage = psutil.virtual_memory().used
            if memory_usage > memory_threshold:
                await self._send_alert(
                    "PERFORMANCE_WARNING",
                    f"メモリ使用量が高いです: {memory_usage / 1024 / 1024:.1f}MB",
                )

            # ディスク使用率チェック
            if self.monitoring_data.get("disk_percent", 0) > 90:
                await self._send_alert(
                    "PERFORMANCE_WARNING",
                    f"ディスク使用率が高いです: {self.monitoring_data['disk_percent']}%",
                )

        except Exception as e:
            logger.error(f"Performance check failed: {e}")

    async def _process_alerts(self):
        """
        アラートを処理
        """
        try:
            # アラート履歴をクリーンアップ（24時間以上古いものを削除）
            cutoff_time = datetime.now() - timedelta(hours=24)
            self.alert_history = [
                alert
                for alert in self.alert_history
                if alert["timestamp"] > cutoff_time
            ]

            # 重複アラートを防止（同じタイプのアラートは1時間以内に再送しない）
            recent_alerts = [
                alert
                for alert in self.alert_history
                if alert["timestamp"] > datetime.now() - timedelta(hours=1)
            ]

            # 新しいアラートのみを送信
            for alert in recent_alerts:
                if not any(
                    existing["type"] == alert["type"]
                    and existing["timestamp"] > datetime.now() - timedelta(hours=1)
                    for existing in self.alert_history
                ):
                    await self._send_discord_alert(alert["type"], alert["message"])

        except Exception as e:
            logger.error(f"Alert processing failed: {e}")

    async def _send_alert(self, alert_type: str, message: str):
        """
        アラートを送信
        """
        alert = {"type": alert_type, "message": message, "timestamp": datetime.now()}

        self.alert_history.append(alert)
        logger.warning(f"Alert: {alert_type} - {message}")

    async def _send_discord_alert(self, alert_type: str, message: str):
        """
        Discordにアラートを送信
        """
        try:
            # システム監視専用のWebhook URLを使用
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                # フォールバック: 通常のDiscord Webhook URLを使用
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )
                if not webhook_url:
                    logger.warning("Discord webhook URL not configured")
                    return

            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": f"🚨 システムアラート: {alert_type}",
                    "description": message,
                    "color": 0xFF0000,  # 赤色
                    "timestamp": datetime.now().isoformat(),
                    "fields": [
                        {
                            "name": "システム状態",
                            "value": f"CPU: {self.monitoring_data.get('cpu_percent', 'N/A')}%\n"
                            f"メモリ: {self.monitoring_data.get('memory_percent', 'N/A')}%\n"
                            f"ディスク: {self.monitoring_data.get('disk_percent', 'N/A')}%",
                            "inline": True,
                        }
                    ],
                }

                await sender.send_embed(embed)
                logger.info(f"Discord alert sent: {alert_type}")

        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")

    async def send_system_status_to_discord(self):
        """
        システム状態をDiscordに送信
        """
        try:
            # システム監視専用のWebhook URLを使用
            webhook_url = self.config_manager.get(
                "notifications.discord_monitoring.webhook_url"
            )
            if not webhook_url:
                # フォールバック: 通常のDiscord Webhook URLを使用
                webhook_url = self.config_manager.get(
                    "notifications.discord.webhook_url"
                )
                if not webhook_url:
                    logger.warning("Discord webhook URL not configured")
                    return

            # システム状態を取得
            status = self.get_system_status()
            health_report = await self.get_health_report()

            # ステータスに応じて色を設定
            color = (
                0x00FF00 if health_report["system_healthy"] else 0xFFA500
            )  # 緑またはオレンジ

            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "📊 システム監視レポート",
                    "description": "USD/JPY パターン検出システムの現在の状態",
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                    "fields": [
                        {
                            "name": "🖥️ システムメトリクス",
                            "value": f"CPU: {self.monitoring_data.get('cpu_percent', 'N/A')}%\n"
                            f"メモリ: {self.monitoring_data.get('memory_percent', 'N/A')}%\n"
                            f"ディスク: {self.monitoring_data.get('disk_percent', 'N/A')}%\n"
                            f"プロセスメモリ: {self.monitoring_data.get('process_memory_mb', 'N/A')}MB",
                            "inline": True,
                        },
                        {
                            "name": "⏱️ システム情報",
                            "value": f"稼働時間: {status['uptime_seconds']:.0f}秒\n"
                            f"監視状態: {'稼働中' if status['is_running'] else '停止中'}\n"
                            f"アラート数: {status['alert_count']}件\n"
                            f"最終チェック: {status['last_check'].strftime('%H:%M:%S')}",
                            "inline": True,
                        },
                        {
                            "name": "🔍 ヘルスチェック",
                            "value": f"システム状態: {'✅ 正常' if health_report['system_healthy'] else '❌ 異常'}\n"
                            f"問題数: {len(health_report['issues'])}件",
                            "inline": False,
                        },
                    ],
                }

                # 問題がある場合は詳細を追加
                if health_report["issues"]:
                    issues_text = "\n".join(
                        [f"• {issue}" for issue in health_report["issues"]]
                    )
                    embed["fields"].append(
                        {
                            "name": "⚠️ 検出された問題",
                            "value": issues_text,
                            "inline": False,
                        }
                    )

                await sender.send_embed(embed)
                logger.info("System status sent to Discord")

        except Exception as e:
            logger.error(f"Failed to send system status to Discord: {e}")

    async def send_performance_report_to_discord(self):
        """
        パフォーマンスレポートをDiscordに送信
        """
        try:
            webhook_url = self.config_manager.get("notifications.discord.webhook_url")
            if not webhook_url:
                logger.warning("Discord webhook URL not configured")
                return

            # パフォーマンスメトリクスを取得
            cpu_percent = self.monitoring_data.get("cpu_percent", 0)
            memory_percent = self.monitoring_data.get("memory_percent", 0)
            disk_percent = self.monitoring_data.get("disk_percent", 0)

            # パフォーマンスレベルを判定
            if cpu_percent > 80 or memory_percent > 80 or disk_percent > 90:
                color = 0xFF0000  # 赤色（危険）
                status = "⚠️ 注意が必要"
            elif cpu_percent > 60 or memory_percent > 60 or disk_percent > 70:
                color = 0xFFA500  # オレンジ（警告）
                status = "⚡ 監視が必要"
            else:
                color = 0x00FF00  # 緑色（正常）
                status = "✅ 正常"

            async with DiscordWebhookSender(webhook_url) as sender:
                embed = {
                    "title": "📈 パフォーマンスレポート",
                    "description": f"USD/JPY パターン検出システムのパフォーマンス状況\n{status}",
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                    "fields": [
                        {
                            "name": "🖥️ CPU使用率",
                            "value": f"{cpu_percent:.1f}%",
                            "inline": True,
                        },
                        {
                            "name": "💾 メモリ使用率",
                            "value": f"{memory_percent:.1f}%",
                            "inline": True,
                        },
                        {
                            "name": "💿 ディスク使用率",
                            "value": f"{disk_percent:.1f}%",
                            "inline": True,
                        },
                        {
                            "name": "🌐 ネットワーク使用量",
                            "value": f"送信: {self.monitoring_data.get('network_bytes_sent', 0) / 1024 / 1024:.1f}MB\n"
                            f"受信: {self.monitoring_data.get('network_bytes_recv', 0) / 1024 / 1024:.1f}MB",
                            "inline": True,
                        },
                    ],
                }

                await sender.send_embed(embed)
                logger.info("Performance report sent to Discord")

        except Exception as e:
            logger.error(f"Failed to send performance report to Discord: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """
        システム状態を取得
        """
        return {
            "is_running": self.is_running,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "monitoring_data": self.monitoring_data,
            "alert_count": len(self.alert_history),
            "last_check": datetime.now(),
        }

    async def get_health_report(self) -> Dict[str, Any]:
        """
        ヘルスレポートを生成
        """
        try:
            # システムメトリクス
            health_data = {
                "timestamp": datetime.now(),
                "system_healthy": True,
                "issues": [],
            }

            # CPU使用率チェック
            cpu_percent = self.monitoring_data.get("cpu_percent", 0)
            if cpu_percent > 80:
                health_data["system_healthy"] = False
                health_data["issues"].append(f"CPU使用率が高い: {cpu_percent}%")

            # メモリ使用率チェック
            memory_percent = self.monitoring_data.get("memory_percent", 0)
            if memory_percent > 80:
                health_data["system_healthy"] = False
                health_data["issues"].append(f"メモリ使用率が高い: {memory_percent}%")

            # データベースヘルスチェック
            if not self.monitoring_data.get("database_healthy", True):
                health_data["system_healthy"] = False
                health_data["issues"].append("データベース接続エラー")

            # データ取得状況チェック
            minutes_since_last_fetch = self.monitoring_data.get(
                "minutes_since_last_fetch", 0
            )
            if minutes_since_last_fetch > 10:
                health_data["system_healthy"] = False
                health_data["issues"].append(
                    f"データ取得が遅延: {minutes_since_last_fetch:.1f}分前"
                )

            return health_data

        except Exception as e:
            logger.error(f"Health report generation failed: {e}")
            return {
                "timestamp": datetime.now(),
                "system_healthy": False,
                "issues": [f"ヘルスレポート生成エラー: {e}"],
            }
