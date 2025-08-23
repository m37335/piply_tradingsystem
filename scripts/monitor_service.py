#!/usr/bin/env python3
"""
サービス監視スクリプト
本番環境でのサービス監視とアラート機能
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ServiceMonitor:
    """サービス監視"""

    def __init__(self, config_file: str = "config/production_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.logs_dir = Path("data/logs")
        self.monitoring_log = self.logs_dir / "monitoring" / "service_monitor.log"

    def _load_config(self) -> Dict[str, Any]:
        """設定ファイルの読み込み"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config file: {e}")
            return {}

    async def monitor_services(self) -> Dict[str, Any]:
        """サービスの監視"""
        try:
            logger.info("Starting service monitoring")

            monitoring_results = {
                "timestamp": datetime.utcnow().isoformat(),
                "services": {},
                "overall_status": "healthy",
                "alerts": [],
            }

            # 各サービスの監視
            services = {
                "database": self._check_database_service(),
                "redis": self._check_redis_service(),
                "discord": self._check_discord_service(),
                "openai": self._check_openai_service(),
                "crontab": self._check_crontab_service(),
                "logs": self._check_log_health(),
                "disk_space": self._check_disk_space(),
                "memory_usage": self._check_memory_usage(),
            }

            # 結果の集約
            for service_name, result in services.items():
                monitoring_results["services"][service_name] = result

                if not result["healthy"]:
                    monitoring_results["overall_status"] = "unhealthy"
                    monitoring_results["alerts"].append(
                        {
                            "service": service_name,
                            "status": "unhealthy",
                            "message": result.get("message", "Service check failed"),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

            # 監視結果の保存
            await self._save_monitoring_results(monitoring_results)

            # アラートの送信
            if monitoring_results["alerts"]:
                await self._send_alerts(monitoring_results["alerts"])

            logger.info(
                f"Service monitoring completed. Status: {monitoring_results['overall_status']}"
            )
            return monitoring_results

        except Exception as e:
            logger.error(f"Error in service monitoring: {e}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "overall_status": "error",
            }

    def _check_database_service(self) -> Dict[str, Any]:
        """データベースサービスのチェック"""
        try:
            # データベース接続テスト
            result = subprocess.run(
                ["python", "-c", "import psycopg2; print('DB OK')"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return {"healthy": True, "status": "connected", "response_time": "fast"}
            else:
                return {
                    "healthy": False,
                    "status": "disconnected",
                    "message": "Database connection failed",
                }

        except subprocess.TimeoutExpired:
            return {
                "healthy": False,
                "status": "timeout",
                "message": "Database connection timeout",
            }
        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_redis_service(self) -> Dict[str, Any]:
        """Redisサービスのチェック"""
        try:
            # Redis接続テスト
            result = subprocess.run(
                ["python", "-c", "import redis; print('Redis OK')"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return {"healthy": True, "status": "connected", "response_time": "fast"}
            else:
                return {
                    "healthy": False,
                    "status": "disconnected",
                    "message": "Redis connection failed",
                }

        except subprocess.TimeoutExpired:
            return {
                "healthy": False,
                "status": "timeout",
                "message": "Redis connection timeout",
            }
        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_discord_service(self) -> Dict[str, Any]:
        """Discordサービスのチェック"""
        try:
            webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
            if not webhook_url:
                return {
                    "healthy": False,
                    "status": "not_configured",
                    "message": "Discord economic indicators webhook URL not configured",
                }

            # Webhook URLの形式チェック
            if webhook_url.startswith("https://discord.com/api/webhooks/"):
                return {
                    "healthy": True,
                    "status": "configured",
                    "webhook_configured": True,
                }
            else:
                return {
                    "healthy": False,
                    "status": "invalid_url",
                    "message": "Invalid Discord webhook URL format",
                }

        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_openai_service(self) -> Dict[str, Any]:
        """OpenAIサービスのチェック"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return {
                    "healthy": False,
                    "status": "not_configured",
                    "message": "OpenAI API key not configured",
                }

            # APIキーの形式チェック
            if len(api_key) > 20 and api_key.startswith("sk-"):
                return {
                    "healthy": True,
                    "status": "configured",
                    "api_key_configured": True,
                }
            else:
                return {
                    "healthy": False,
                    "status": "invalid_key",
                    "message": "Invalid OpenAI API key format",
                }

        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_crontab_service(self) -> Dict[str, Any]:
        """crontabサービスのチェック"""
        try:
            # crontabの存在確認
            result = subprocess.run(
                ["crontab", "-l"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                crontab_content = result.stdout

                # 重要なスケジュールの確認
                has_weekly = "weekly_schedule.cron" in crontab_content
                has_daily = "daily_schedule.cron" in crontab_content
                has_realtime = "realtime_schedule.cron" in crontab_content

                return {
                    "healthy": True,
                    "status": "active",
                    "schedules": {
                        "weekly": has_weekly,
                        "daily": has_daily,
                        "realtime": has_realtime,
                    },
                }
            else:
                return {
                    "healthy": False,
                    "status": "not_configured",
                    "message": "No crontab configured",
                }

        except subprocess.TimeoutExpired:
            return {
                "healthy": False,
                "status": "timeout",
                "message": "Crontab check timeout",
            }
        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_log_health(self) -> Dict[str, Any]:
        """ログの健全性チェック"""
        try:
            log_files = []
            error_count = 0

            # ログファイルの確認
            for log_file in self.logs_dir.rglob("*.log"):
                try:
                    # ファイルサイズの確認
                    file_size = log_file.stat().st_size

                    # 最近のエラーログの確認
                    if "error" in log_file.name.lower():
                        with open(log_file, "r", encoding="utf-8") as f:
                            recent_lines = f.readlines()[-100:]  # 最後の100行
                            error_count += len(
                                [line for line in recent_lines if "ERROR" in line]
                            )

                    log_files.append(
                        {
                            "file": str(log_file),
                            "size_mb": round(file_size / (1024 * 1024), 2),
                            "last_modified": datetime.fromtimestamp(
                                log_file.stat().st_mtime
                            ).isoformat(),
                        }
                    )

                except Exception as e:
                    logger.error(f"Error checking log file {log_file}: {e}")

            # ログの健全性判定
            is_healthy = error_count < 50  # エラー数が50未満なら健全

            return {
                "healthy": is_healthy,
                "status": "healthy" if is_healthy else "high_error_rate",
                "log_files_count": len(log_files),
                "recent_errors": error_count,
                "message": (
                    f"Found {error_count} recent errors"
                    if error_count > 0
                    else "No recent errors"
                ),
            }

        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_disk_space(self) -> Dict[str, Any]:
        """ディスク容量のチェック"""
        try:
            # ディスク使用量の確認
            result = subprocess.run(
                ["df", "-h", "/app"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        usage_percent = int(parts[4].rstrip("%"))

                        is_healthy = usage_percent < 90

                        return {
                            "healthy": is_healthy,
                            "status": "healthy" if is_healthy else "high_usage",
                            "usage_percent": usage_percent,
                            "message": f"Disk usage: {usage_percent}%",
                        }

            return {
                "healthy": False,
                "status": "unknown",
                "message": "Could not determine disk usage",
            }

        except subprocess.TimeoutExpired:
            return {
                "healthy": False,
                "status": "timeout",
                "message": "Disk space check timeout",
            }
        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    def _check_memory_usage(self) -> Dict[str, Any]:
        """メモリ使用量のチェック"""
        try:
            # メモリ使用量の確認
            result = subprocess.run(
                ["free", "-m"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 3:
                        total_mb = int(parts[1])
                        used_mb = int(parts[2])
                        usage_percent = round((used_mb / total_mb) * 100, 1)

                        is_healthy = usage_percent < 85

                        return {
                            "healthy": is_healthy,
                            "status": "healthy" if is_healthy else "high_usage",
                            "usage_percent": usage_percent,
                            "total_mb": total_mb,
                            "used_mb": used_mb,
                            "message": f"Memory usage: {usage_percent}%",
                        }

            return {
                "healthy": False,
                "status": "unknown",
                "message": "Could not determine memory usage",
            }

        except subprocess.TimeoutExpired:
            return {
                "healthy": False,
                "status": "timeout",
                "message": "Memory usage check timeout",
            }
        except Exception as e:
            return {"healthy": False, "status": "error", "message": str(e)}

    async def _save_monitoring_results(self, results: Dict[str, Any]) -> None:
        """監視結果の保存"""
        try:
            # 監視ログディレクトリの作成
            monitoring_dir = self.logs_dir / "monitoring"
            monitoring_dir.mkdir(parents=True, exist_ok=True)

            # 結果をJSONファイルに保存
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = monitoring_dir / f"monitoring_result_{timestamp}.json"

            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # 古い結果ファイルの削除（30日以上前）
            cutoff_date = datetime.now() - timedelta(days=30)
            for old_file in monitoring_dir.glob("monitoring_result_*.json"):
                if datetime.fromtimestamp(old_file.stat().st_mtime) < cutoff_date:
                    old_file.unlink()

        except Exception as e:
            logger.error(f"Error saving monitoring results: {e}")

    async def _send_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """アラートの送信"""
        try:
            # Discord Webhookへのアラート送信
            webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
            if webhook_url:
                await self._send_discord_alert(webhook_url, alerts)

            # ログファイルへのアラート記録
            await self._log_alerts(alerts)

        except Exception as e:
            logger.error(f"Error sending alerts: {e}")

    async def _send_discord_alert(
        self, webhook_url: str, alerts: List[Dict[str, Any]]
    ) -> None:
        """Discordアラートの送信"""
        try:
            import aiohttp

            # アラートメッセージの作成
            message = "🚨 **Service Monitoring Alert**\n\n"
            for alert in alerts:
                message += f"**{alert['service']}**: {alert['message']}\n"

            payload = {"content": message, "username": "Service Monitor"}

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 204:
                        logger.info("Discord alert sent successfully")
                    else:
                        logger.error(f"Failed to send Discord alert: {response.status}")

        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")

    async def _log_alerts(self, alerts: List[Dict[str, Any]]) -> None:
        """アラートのログ記録"""
        try:
            alert_log = self.logs_dir / "monitoring" / "alerts.log"

            with open(alert_log, "a", encoding="utf-8") as f:
                for alert in alerts:
                    f.write(
                        f"{alert['timestamp']} - {alert['service']} - {alert['message']}\n"
                    )

        except Exception as e:
            logger.error(f"Error logging alerts: {e}")

    async def run_continuous_monitoring(self, interval_seconds: int = 300) -> None:
        """継続的な監視の実行"""
        try:
            logger.info(
                f"Starting continuous monitoring (interval: {interval_seconds}s)"
            )

            while True:
                await self.monitor_services()
                await asyncio.sleep(interval_seconds)

        except KeyboardInterrupt:
            logger.info("Continuous monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in continuous monitoring: {e}")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Service monitoring")
    parser.add_argument(
        "--config",
        default="config/production_config.json",
        help="Production config file path",
    )
    parser.add_argument(
        "--continuous", action="store_true", help="Run continuous monitoring"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Monitoring interval in seconds (default: 300)",
    )

    args = parser.parse_args()

    monitor = ServiceMonitor(args.config)

    if args.continuous:
        # 継続的な監視
        asyncio.run(monitor.run_continuous_monitoring(args.interval))
    else:
        # 1回の監視
        result = asyncio.run(monitor.monitor_services())

        if result.get("overall_status") == "healthy":
            print("✅ Service monitoring completed - All services healthy")
        else:
            print("❌ Service monitoring completed - Issues detected")
            for alert in result.get("alerts", []):
                print(f"  {alert['service']}: {alert['message']}")


if __name__ == "__main__":
    main()
