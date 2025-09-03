"""
継続処理監視サービス

責任:
- 継続処理パイプラインの監視
- パフォーマンス指標の収集
- エラー検出とアラート
- システム健全性の監視

特徴:
- リアルタイム監視
- 自動アラート機能
- パフォーマンス分析
- 障害検知
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContinuousProcessingMonitor:
    """
    継続処理監視サービス

    責任:
    - 継続処理パイプラインの監視
    - パフォーマンス指標の収集
    - エラー検出とアラート
    - システム健全性の監視
    """

    def __init__(self):
        self.metrics = {
            "processing_times": [],
            "error_counts": {},
            "success_rates": {},
            "data_volumes": [],
            "system_health": {},
            "alert_history": [],
        }

        # 監視設定
        self.alert_thresholds = {
            "max_processing_time": 300,  # 5分
            "min_success_rate": 0.8,  # 80%（初期化時に対応）
            "max_error_count": 5,  # 5回
            "max_consecutive_failures": 3,  # 3回
            "min_data_volume": 1,  # 1件（初期化時に対応）
        }

        # 統計情報
        self.stats = {
            "total_cycles": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "total_alerts": 0,
            "last_alert": None,
            "monitoring_start_time": datetime.now(),
        }

        # 監視状態
        self.is_monitoring = False
        self.monitoring_interval = 60  # 秒

    async def start_monitoring(self):
        """
        監視を開始
        """
        if self.is_monitoring:
            logger.warning("⚠️ 監視は既に実行中です")
            return

        try:
            logger.info("🔍 継続処理監視を開始します")
            self.is_monitoring = True
            self.stats["monitoring_start_time"] = datetime.now()

        except Exception as e:
            logger.error(f"❌ 監視開始エラー: {e}")
            self.is_monitoring = False
            raise

    async def stop_monitoring(self):
        """
        監視を停止
        """
        if not self.is_monitoring:
            logger.warning("⚠️ 監視は既に停止しています")
            return

        try:
            logger.info("🛑 継続処理監視を停止します")
            self.is_monitoring = False

        except Exception as e:
            logger.error(f"❌ 監視停止エラー: {e}")
            raise

    async def monitor_processing_cycle(self, cycle_data: Dict[str, Any]):
        """
        処理サイクルの監視

        Args:
            cycle_data: サイクル実行データ
        """
        try:
            if not self.is_monitoring:
                return

            self.stats["total_cycles"] += 1

            # 処理時間を記録
            processing_time = cycle_data.get("processing_time", 0)
            self.metrics["processing_times"].append(processing_time)

            # 処理時間の閾値チェック
            if processing_time > self.alert_thresholds["max_processing_time"]:
                await self.send_alert(
                    "PERFORMANCE", f"処理時間が閾値を超過: {processing_time:.2f}秒"
                )

            # 成功率を計算
            total_runs = cycle_data.get("total_runs", 0)
            successful_runs = cycle_data.get("successful_runs", 0)

            if total_runs > 0:
                success_rate = successful_runs / total_runs
                self.metrics["success_rates"]["overall"] = success_rate

                if success_rate < self.alert_thresholds["min_success_rate"]:
                    await self.send_alert(
                        "RELIABILITY", f"成功率が閾値を下回る: {success_rate:.2%}"
                    )

            # データ量を記録
            data_volume = cycle_data.get("data_volume", 0)
            self.metrics["data_volumes"].append(data_volume)

            if data_volume < self.alert_thresholds["min_data_volume"]:
                await self.send_alert(
                    "DATA_VOLUME", f"データ量が閾値を下回る: {data_volume}件"
                )

            # エラー情報を記録
            error_count = cycle_data.get("error_count", 0)
            if error_count > 0:
                self.metrics["error_counts"][datetime.now().isoformat()] = error_count

                if error_count > self.alert_thresholds["max_error_count"]:
                    await self.send_alert(
                        "ERROR_RATE", f"エラー数が閾値を超過: {error_count}回"
                    )

            # 成功サイクルとして記録
            if cycle_data.get("status") == "success":
                self.stats["successful_cycles"] += 1
            else:
                self.stats["failed_cycles"] += 1

        except Exception as e:
            logger.error(f"❌ 処理サイクル監視エラー: {e}")

    async def check_system_health(self) -> Dict[str, Any]:
        """
        システム健全性チェック

        Returns:
            Dict[str, Any]: 健全性情報
        """
        try:
            health_status = {
                "service": "ContinuousProcessingMonitor",
                "status": "healthy",
                "timestamp": datetime.now(),
                "is_monitoring": self.is_monitoring,
                "uptime": (
                    datetime.now() - self.stats["monitoring_start_time"]
                ).total_seconds(),
            }

            # 処理時間の分析
            if self.metrics["processing_times"]:
                avg_processing_time = sum(self.metrics["processing_times"]) / len(
                    self.metrics["processing_times"]
                )
                max_processing_time = max(self.metrics["processing_times"])
                health_status["processing_time"] = {
                    "average": avg_processing_time,
                    "max": max_processing_time,
                    "threshold": self.alert_thresholds["max_processing_time"],
                }

                if avg_processing_time > self.alert_thresholds["max_processing_time"]:
                    health_status["status"] = "degraded"
                    health_status["issues"] = ["処理時間が閾値を超過"]

            # 成功率の分析
            if "overall" in self.metrics["success_rates"]:
                success_rate = self.metrics["success_rates"]["overall"]
                health_status["success_rate"] = {
                    "current": success_rate,
                    "threshold": self.alert_thresholds["min_success_rate"],
                }

                if success_rate < self.alert_thresholds["min_success_rate"]:
                    health_status["status"] = "degraded"
                    if "issues" not in health_status:
                        health_status["issues"] = []
                    health_status["issues"].append("成功率が閾値を下回る")

            # エラー率の分析
            if self.metrics["error_counts"]:
                recent_errors = sum(
                    count
                    for timestamp, count in self.metrics["error_counts"].items()
                    if datetime.fromisoformat(timestamp)
                    > datetime.now() - timedelta(hours=1)
                )
                health_status["error_rate"] = {
                    "recent_errors": recent_errors,
                    "threshold": self.alert_thresholds["max_error_count"],
                }

                if recent_errors > self.alert_thresholds["max_error_count"]:
                    health_status["status"] = "degraded"
                    if "issues" not in health_status:
                        health_status["issues"] = []
                    health_status["issues"].append("エラー数が閾値を超過")

            # データ量の分析
            if self.metrics["data_volumes"]:
                recent_data_volume = sum(
                    volume for volume in self.metrics["data_volumes"][-10:]
                )
                health_status["data_volume"] = {
                    "recent_total": recent_data_volume,
                    "threshold": self.alert_thresholds["min_data_volume"],
                }

                if recent_data_volume < self.alert_thresholds["min_data_volume"]:
                    health_status["status"] = "degraded"
                    if "issues" not in health_status:
                        health_status["issues"] = []
                    health_status["issues"].append("データ量が閾値を下回る")

            # 統計情報
            health_status["stats"] = {
                "total_cycles": self.stats["total_cycles"],
                "successful_cycles": self.stats["successful_cycles"],
                "failed_cycles": self.stats["failed_cycles"],
                "total_alerts": self.stats["total_alerts"],
            }

            return health_status

        except Exception as e:
            logger.error(f"❌ システム健全性チェックエラー: {e}")
            return {
                "service": "ContinuousProcessingMonitor",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def send_alert(self, alert_type: str, message: str):
        """
        アラート送信

        Args:
            alert_type: アラートタイプ
            message: アラートメッセージ
        """
        try:
            alert_data = {
                "timestamp": datetime.now(),
                "type": alert_type,
                "message": message,
                "severity": self._get_alert_severity(alert_type),
            }

            # アラート履歴に追加
            self.metrics["alert_history"].append(alert_data)
            self.stats["total_alerts"] += 1
            self.stats["last_alert"] = datetime.now()

            # ログ出力
            logger.warning(f"🚨 アラート [{alert_type}]: {message}")

            # 実際のアラート送信（実装予定）
            # await self._send_notification(alert_data)

        except Exception as e:
            logger.error(f"❌ アラート送信エラー: {e}")

    def _get_alert_severity(self, alert_type: str) -> str:
        """
        アラートタイプに基づく重要度を取得

        Args:
            alert_type: アラートタイプ

        Returns:
            str: 重要度（critical, warning, info）
        """
        severity_map = {
            "PERFORMANCE": "warning",
            "RELIABILITY": "critical",
            "ERROR_RATE": "critical",
            "DATA_VOLUME": "warning",
            "SYSTEM_HEALTH": "critical",
        }
        return severity_map.get(alert_type, "info")

    async def get_monitoring_metrics(self) -> Dict[str, Any]:
        """
        監視指標を取得

        Returns:
            Dict[str, Any]: 監視指標
        """
        try:
            return {
                "metrics": self.metrics,
                "stats": self.stats,
                "thresholds": self.alert_thresholds,
                "is_monitoring": self.is_monitoring,
                "monitoring_interval": self.monitoring_interval,
            }

        except Exception as e:
            logger.error(f"❌ 監視指標取得エラー: {e}")
            return {}

    async def reset_metrics(self):
        """
        監視指標をリセット
        """
        try:
            self.metrics = {
                "processing_times": [],
                "error_counts": {},
                "success_rates": {},
                "data_volumes": {},
                "system_health": {},
                "alert_history": [],
            }

            self.stats = {
                "total_cycles": 0,
                "successful_cycles": 0,
                "failed_cycles": 0,
                "total_alerts": 0,
                "last_alert": None,
                "monitoring_start_time": datetime.now(),
            }

            logger.info("🔄 監視指標をリセットしました")

        except Exception as e:
            logger.error(f"❌ 監視指標リセットエラー: {e}")

    async def update_alert_thresholds(
        self,
        max_processing_time: Optional[int] = None,
        min_success_rate: Optional[float] = None,
        max_error_count: Optional[int] = None,
        max_consecutive_failures: Optional[int] = None,
        min_data_volume: Optional[int] = None,
    ):
        """
        アラート閾値を更新

        Args:
            max_processing_time: 最大処理時間（秒）
            min_success_rate: 最小成功率
            max_error_count: 最大エラー数
            max_consecutive_failures: 最大連続失敗回数
            min_data_volume: 最小データ量
        """
        try:
            if max_processing_time is not None:
                self.alert_thresholds["max_processing_time"] = max_processing_time
                logger.info(f"🔄 最大処理時間閾値を更新: {max_processing_time}秒")

            if min_success_rate is not None:
                self.alert_thresholds["min_success_rate"] = min_success_rate
                logger.info(f"🔄 最小成功率閾値を更新: {min_success_rate}")

            if max_error_count is not None:
                self.alert_thresholds["max_error_count"] = max_error_count
                logger.info(f"🔄 最大エラー数閾値を更新: {max_error_count}")

            if max_consecutive_failures is not None:
                self.alert_thresholds["max_consecutive_failures"] = (
                    max_consecutive_failures
                )
                logger.info(
                    f"🔄 最大連続失敗回数閾値を更新: {max_consecutive_failures}"
                )

            if min_data_volume is not None:
                self.alert_thresholds["min_data_volume"] = min_data_volume
                logger.info(f"🔄 最小データ量閾値を更新: {min_data_volume}")

        except Exception as e:
            logger.error(f"❌ アラート閾値更新エラー: {e}")

    async def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        アラート履歴を取得

        Args:
            hours: 取得する時間範囲（時間）

        Returns:
            List[Dict[str, Any]]: アラート履歴
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_alerts = [
                alert
                for alert in self.metrics["alert_history"]
                if alert["timestamp"] > cutoff_time
            ]
            return recent_alerts

        except Exception as e:
            logger.error(f"❌ アラート履歴取得エラー: {e}")
            return []

    async def analyze_performance_trends(self) -> Dict[str, Any]:
        """
        パフォーマンス傾向を分析

        Returns:
            Dict[str, Any]: パフォーマンス分析結果
        """
        try:
            if not self.metrics["processing_times"]:
                return {"message": "分析データが不足しています"}

            processing_times = self.metrics["processing_times"]
            recent_times = processing_times[-10:]  # 最新10件

            analysis = {
                "overall": {
                    "average": sum(processing_times) / len(processing_times),
                    "max": max(processing_times),
                    "min": min(processing_times),
                    "total_samples": len(processing_times),
                },
                "recent": {
                    "average": sum(recent_times) / len(recent_times),
                    "max": max(recent_times),
                    "min": min(recent_times),
                    "samples": len(recent_times),
                },
                "trend": "stable",
            }

            # 傾向分析
            if len(recent_times) >= 5:
                recent_avg = sum(recent_times) / len(recent_times)
                overall_avg = sum(processing_times) / len(processing_times)

                if recent_avg > overall_avg * 1.05:  # 5%以上の増加
                    analysis["trend"] = "degrading"
                elif recent_avg < overall_avg * 0.95:  # 5%以上の減少
                    analysis["trend"] = "improving"

            return analysis

        except Exception as e:
            logger.error(f"❌ パフォーマンス傾向分析エラー: {e}")
            return {"error": str(e)}
