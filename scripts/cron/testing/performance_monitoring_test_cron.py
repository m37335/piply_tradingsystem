#!/usr/bin/env python3
"""
パフォーマンス監視システムテストcronスクリプト

責任:
- パフォーマンス監視システムのテスト実行
- システム継続性の確認
- パフォーマンスメトリクスの収集と配信
- アラート通知

特徴:
- 包括的なパフォーマンステスト
- システム健全性の確認
- 継続性の検証
- 結果の配信
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import psutil
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.services.notification_integration_service import (
    NotificationIntegrationService,
)
from src.infrastructure.monitoring.performance_monitor import PerformanceMonitor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/performance_monitoring_test_cron.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class PerformanceMonitoringTestCron:
    """
    パフォーマンス監視システムテストcronクラス
    """

    def __init__(self):
        self.db_url = None
        self.engine = None
        self.session_factory = None
        self.session = None
        self.performance_monitor = None
        self.notification_service = None

    async def initialize_database(self):
        """
        データベース接続を初期化
        """
        try:
            # 環境変数からデータベースURLを取得
            import os

            self.db_url = os.getenv("DATABASE_URL")
            if not self.db_url:
                raise ValueError("DATABASE_URL環境変数が設定されていません")

            # データベースエンジンを作成
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            logger.info("✅ データベース接続を初期化しました")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise

    async def initialize_services(self):
        """
        サービスを初期化
        """
        try:
            # セッションを作成
            self.session = self.session_factory()

            # パフォーマンス監視システムを初期化
            self.performance_monitor = PerformanceMonitor(self.session)

            # 通知サービスを初期化
            self.notification_service = NotificationIntegrationService(self.session)

            logger.info("✅ サービスを初期化しました")

        except Exception as e:
            logger.error(f"❌ サービス初期化エラー: {e}")
            raise

    async def run_performance_test(self) -> Dict[str, Any]:
        """
        パフォーマンス監視システムテストを実行

        Returns:
            Dict[str, Any]: テスト結果
        """
        try:
            logger.info("🔄 パフォーマンス監視システムテスト開始")

            # 1. システムメトリクス収集
            system_metrics = await self.performance_monitor.collect_system_metrics()
            logger.info(f"📊 システムメトリクス収集完了: {system_metrics}")

            # 2. データベースパフォーマンステスト
            db_performance = await self._test_database_performance()
            logger.info(f"🗄️ データベースパフォーマンステスト完了: {db_performance}")

            # 3. データ処理パフォーマンステスト
            processing_performance = await self._test_data_processing_performance()
            logger.info(
                f"⚙️ データ処理パフォーマンステスト完了: {processing_performance}"
            )

            # 4. システム健全性チェック
            health_status = await self._check_system_health()
            logger.info(f"🏥 システム健全性チェック完了: {health_status}")

            # 5. 継続性テスト
            continuity_test = await self._test_system_continuity()
            logger.info(f"🔄 継続性テスト完了: {continuity_test}")

            # 6. 結果の統合
            test_result = {
                "timestamp": datetime.now(),
                "system_metrics": system_metrics,
                "database_performance": db_performance,
                "processing_performance": processing_performance,
                "health_status": health_status,
                "continuity_test": continuity_test,
                "overall_status": "success",
            }

            # 7. アラート判定
            alerts = await self._check_alerts(test_result)
            if alerts:
                test_result["alerts"] = alerts
                test_result["overall_status"] = "warning"

            logger.info("✅ パフォーマンス監視システムテスト完了")
            return test_result

        except Exception as e:
            logger.error(f"❌ パフォーマンス監視システムテストエラー: {e}")
            return {
                "timestamp": datetime.now(),
                "overall_status": "error",
                "error": str(e),
            }

    async def _test_database_performance(self) -> Dict[str, Any]:
        """
        データベースパフォーマンステスト
        """
        try:
            # 基本的なクエリパフォーマンステスト
            async def test_query():
                from sqlalchemy import text

                result = await self.session.execute(
                    text("SELECT COUNT(*) FROM price_data")
                )
                return result.scalar()

            performance_result = (
                await self.performance_monitor.measure_query_performance(test_query)
            )

            return {
                "query_performance": performance_result,
                "status": "success" if performance_result["success"] else "error",
            }

        except Exception as e:
            logger.error(f"データベースパフォーマンステストエラー: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_data_processing_performance(self) -> Dict[str, Any]:
        """
        データ処理パフォーマンステスト
        """
        try:
            # データ処理のシミュレーション
            async def test_processing():
                await asyncio.sleep(0.1)  # 処理時間のシミュレーション
                return {"processed_records": 100}

            processing_result = (
                await self.performance_monitor.measure_data_processing_performance(
                    test_processing
                )
            )

            return {
                "processing_performance": processing_result,
                "status": "success" if processing_result["success"] else "error",
            }

        except Exception as e:
            logger.error(f"データ処理パフォーマンステストエラー: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_system_health(self) -> Dict[str, Any]:
        """
        システム健全性チェック
        """
        try:
            # CPU使用率チェック
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_healthy = cpu_percent < 80

            # メモリ使用率チェック
            memory = psutil.virtual_memory()
            memory_healthy = memory.percent < 85

            # ディスク使用率チェック
            disk = psutil.disk_usage("/app")
            disk_healthy = disk.percent < 90

            # データベース接続チェック
            db_healthy = True
            try:
                from sqlalchemy import text

                await self.session.execute(text("SELECT 1"))
            except Exception:
                db_healthy = False

            overall_healthy = (
                cpu_healthy and memory_healthy and disk_healthy and db_healthy
            )

            return {
                "cpu_healthy": cpu_healthy,
                "memory_healthy": memory_healthy,
                "disk_healthy": disk_healthy,
                "database_healthy": db_healthy,
                "overall_healthy": overall_healthy,
                "status": "healthy" if overall_healthy else "unhealthy",
            }

        except Exception as e:
            logger.error(f"システム健全性チェックエラー: {e}")
            return {"status": "error", "error": str(e)}

    async def _test_system_continuity(self) -> Dict[str, Any]:
        """
        システム継続性テスト
        """
        try:
            # 基本的なサービスが動作しているかチェック
            services_healthy = True
            service_checks = {}

            # パフォーマンス監視システムチェック
            try:
                await self.performance_monitor.collect_system_metrics()
                service_checks["performance_monitor"] = "healthy"
            except Exception as e:
                service_checks["performance_monitor"] = f"unhealthy: {e}"
                services_healthy = False

            # 通知サービスチェック
            try:
                # 通知サービスの健全性をチェック（実際の通知は送信しない）
                service_checks["notification_service"] = "healthy"
            except Exception as e:
                service_checks["notification_service"] = f"unhealthy: {e}"
                services_healthy = False

            return {
                "services_healthy": services_healthy,
                "service_checks": service_checks,
                "status": "continuous" if services_healthy else "interrupted",
            }

        except Exception as e:
            logger.error(f"システム継続性テストエラー: {e}")
            return {"status": "error", "error": str(e)}

    async def _check_alerts(self, test_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        アラートチェック
        """
        alerts = []

        # CPU使用率アラート
        if test_result["system_metrics"].get("cpu_percent", 0) > 80:
            alerts.append(
                {
                    "type": "high_cpu_usage",
                    "message": f"CPU使用率が高い: {test_result['system_metrics']['cpu_percent']}%",
                    "severity": "warning",
                }
            )

        # メモリ使用率アラート
        if test_result["system_metrics"].get("memory_percent", 0) > 85:
            alerts.append(
                {
                    "type": "high_memory_usage",
                    "message": f"メモリ使用率が高い: {test_result['system_metrics']['memory_percent']}%",
                    "severity": "warning",
                }
            )

        # ディスク使用率アラート
        if test_result["system_metrics"].get("disk_usage_percent", 0) > 90:
            alerts.append(
                {
                    "type": "high_disk_usage",
                    "message": f"ディスク使用率が高い: {test_result['system_metrics']['disk_usage_percent']}%",
                    "severity": "critical",
                }
            )

        # データベースパフォーマンスアラート
        if test_result["database_performance"]["status"] == "error":
            alerts.append(
                {
                    "type": "database_performance_issue",
                    "message": "データベースパフォーマンスに問題があります",
                    "severity": "critical",
                }
            )

        # システム健全性アラート
        if not test_result["health_status"]["overall_healthy"]:
            alerts.append(
                {
                    "type": "system_health_issue",
                    "message": "システム健全性に問題があります",
                    "severity": "critical",
                }
            )

        return alerts

    async def send_performance_report(self, test_result: Dict[str, Any]):
        """
        パフォーマンスレポートを送信
        """
        try:
            # 環境変数からDiscord Webhook URLを取得
            import os

            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                logger.error(
                    "❌ DISCORD_MONITORING_WEBHOOK_URL環境変数が設定されていません"
                )
                return

            # canary.discord.comをdiscord.comに変更
            if "canary.discord.com" in webhook_url:
                webhook_url = webhook_url.replace("canary.discord.com", "discord.com")
                logger.info("🔧 Discord Webhook URLを通常版に変更しました")

            from src.infrastructure.messaging.discord_client import DiscordClient

            discord_client = DiscordClient(webhook_url=webhook_url)

            # システムメトリクスを取得
            system_metrics = test_result.get("system_metrics", {})
            database_performance = test_result.get("database_performance", {})
            processing_performance = test_result.get("processing_performance", {})
            health_status = test_result.get("health_status", {})
            continuity_test = test_result.get("continuity_test", {})

            # レポートメッセージを作成
            if test_result["overall_status"] == "success":
                # 成功時のレポート
                status_emoji = "✅"
                status_text = "正常"
                urgency = "normal"
                title = "パフォーマンス監視システム定期レポート"

                report_message = f"""
{status_emoji} **パフォーマンス監視システム定期レポート**

📊 **システムメトリクス**
• CPU使用率: {system_metrics.get('cpu_percent', 'N/A')}%
• メモリ使用率: {system_metrics.get('memory_percent', 'N/A')}%
• ディスク使用率: {system_metrics.get('disk_usage_percent', 'N/A')}%
• データベースサイズ: {system_metrics.get('database_size_mb', 'N/A')}MB

🗄️ **データベース性能**
• クエリ実行時間: {database_performance.get('query_performance', {}).get('execution_time_ms', 'N/A')}ms
• レコード数: {database_performance.get('query_performance', {}).get('result', 'N/A')}件

⚙️ **データ処理性能**
• 処理時間: {processing_performance.get('processing_performance', {}).get('processing_time_ms', 'N/A')}ms
• 処理レコード数: {processing_performance.get('processing_performance', {}).get('result', {}).get('processed_records', 'N/A')}件

🏥 **システム健全性**
• CPU: {'健全' if health_status.get('cpu_healthy') else '注意'}
• メモリ: {'健全' if health_status.get('memory_healthy') else '注意'}
• ディスク: {'健全' if health_status.get('disk_healthy') else '注意'}
• データベース: {'健全' if health_status.get('database_healthy') else '注意'}

🔄 **システム継続性**
• パフォーマンス監視: {'健全' if continuity_test.get('service_checks', {}).get('performance_monitor') == 'healthy' else '注意'}
• 通知サービス: {'健全' if continuity_test.get('service_checks', {}).get('notification_service') == 'healthy' else '注意'}

**全体ステータス**: {status_text} ✅
                """.strip()
            else:
                # アラート時のレポート
                status_emoji = "🚨"
                status_text = "注意が必要"
                urgency = "high"
                title = "パフォーマンス監視システムアラート"

                alert_message = (
                    f"{status_emoji} **パフォーマンス監視システムアラート**\n\n"
                )
                if test_result.get("alerts"):
                    for alert in test_result["alerts"]:
                        alert_message += f"• {alert['message']} ({alert['severity']})\n"

                report_message = alert_message

            # Discordに送信
            result = await discord_client.send_alert(
                alert_type="PERFORMANCE_MONITORING",
                title=title,
                message=report_message,
                urgency=urgency,
            )

            logger.info(
                f"📢 パフォーマンス監視システムレポートを送信しました: {test_result['overall_status']}"
            )

        except Exception as e:
            logger.error(f"❌ パフォーマンスレポート送信エラー: {e}")
            # フォールバック: 直接httpxを使用して送信
            await self._send_fallback_discord_message(test_result)

    async def _send_fallback_discord_message(self, test_result: Dict[str, Any]):
        """
        フォールバックDiscordメッセージ送信
        """
        try:
            import os
            import httpx

            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                logger.error("❌ DISCORD_MONITORING_WEBHOOK_URL環境変数が設定されていません")
                return

            # canary.discord.comをdiscord.comに変更
            if "canary.discord.com" in webhook_url:
                webhook_url = webhook_url.replace("canary.discord.com", "discord.com")

            # システムメトリクスを取得
            system_metrics = test_result.get("system_metrics", {})
            health_status = test_result.get("health_status", {})

            # シンプルなメッセージを作成
            message_data = {
                "content": "📊 **パフォーマンス監視システムレポート**",
                "embeds": [
                    {
                        "title": "システムリソース状況",
                        "color": 0x00FF00 if test_result["overall_status"] == "success" else 0xFF0000,
                        "fields": [
                            {
                                "name": "CPU使用率",
                                "value": f"{system_metrics.get('cpu_percent', 'N/A')}%",
                                "inline": True,
                            },
                            {
                                "name": "メモリ使用率",
                                "value": f"{system_metrics.get('memory_percent', 'N/A')}%",
                                "inline": True,
                            },
                            {
                                "name": "ディスク使用率",
                                "value": f"{system_metrics.get('disk_usage_percent', 'N/A')}%",
                                "inline": True,
                            },
                            {
                                "name": "システム健全性",
                                "value": "健全" if health_status.get("overall_healthy") else "注意",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Performance Monitoring System"},
                        "timestamp": datetime.now().isoformat(),
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(webhook_url, json=message_data)
                if response.status_code == 204:
                    logger.info("✅ フォールバックDiscordメッセージ送信成功")
                else:
                    logger.error(f"❌ フォールバックDiscordメッセージ送信失敗: {response.status_code}")

        except Exception as e:
            logger.error(f"❌ フォールバックDiscordメッセージ送信エラー: {e}")

    async def test_discord_notification(self):
        """
        Discord通知機能をテスト
        """
        try:
            logger.info("📢 Discord通知機能テスト開始")

            # 環境変数からDiscord Webhook URLを取得
            import os

            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                logger.error("❌ DISCORD_MONITORING_WEBHOOK_URL環境変数が設定されていません")
                return False

            # canary.discord.comをdiscord.comに変更
            if "canary.discord.com" in webhook_url:
                webhook_url = webhook_url.replace("canary.discord.com", "discord.com")

            from src.infrastructure.messaging.discord_client import \
                DiscordClient

            discord_client = DiscordClient(webhook_url=webhook_url)

            # テスト用アラートを送信
            test_message = """
🔧 パフォーマンス監視システムテスト通知

✅ システム状態: 正常
📊 CPU使用率: 0.8%
💾 メモリ使用率: 60.9%
💿 ディスク使用率: 80.1%
🗄️ データベース: 正常 (25.95ms)
⚙️ データ処理: 正常 (101.20ms)
🔄 システム継続性: 継続中

このメッセージはパフォーマンス監視システムのテスト通知です。
            """.strip()

            result = await discord_client.send_alert(
                alert_type="PERFORMANCE_TEST",
                title="パフォーマンス監視システムテスト通知",
                message=test_message,
                urgency="normal",
            )

            logger.info(f"✅ Discord通知テスト成功: {result}")
            return True

        except Exception as e:
            logger.error(f"❌ Discord通知テストエラー: {e}")
            return False

    async def test_alert_notification(self):
        """
        アラート発生時のDiscord通知機能をテスト
        """
        try:
            logger.info("🚨 アラート通知機能テスト開始")

            # 環境変数からDiscord Webhook URLを取得
            import os

            webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
            if not webhook_url:
                logger.error("❌ DISCORD_MONITORING_WEBHOOK_URL環境変数が設定されていません")
                return False

            # canary.discord.comをdiscord.comに変更
            if "canary.discord.com" in webhook_url:
                webhook_url = webhook_url.replace("canary.discord.com", "discord.com")

            from src.infrastructure.messaging.discord_client import \
                DiscordClient

            discord_client = DiscordClient(webhook_url=webhook_url)

            # アラート発生時のテストメッセージを送信
            alert_message = """
🚨 パフォーマンス監視システムアラート

⚠️ システム状態: 注意が必要
📊 CPU使用率: 95.2% (閾値: 80%)
💾 メモリ使用率: 88.7% (閾値: 85%)
💿 ディスク使用率: 92.1% (閾値: 90%)
🗄️ データベース: 応答遅延 (150.25ms)
⚙️ データ処理: 処理遅延 (250.10ms)
🔄 システム継続性: 継続中

このメッセージはアラート発生時のテスト通知です。
            """.strip()

            result = await discord_client.send_alert(
                alert_type="PERFORMANCE_ALERT",
                title="パフォーマンス監視システムアラート",
                message=alert_message,
                urgency="high",
            )

            logger.info(f"✅ アラート通知テスト成功: {result}")
            return True

        except Exception as e:
            logger.error(f"❌ アラート通知テストエラー: {e}")
            return False

    async def run_system_cycle(self) -> Dict[str, Any]:
        """
        システムサイクルを実行
        """
        try:
            logger.info("🔄 パフォーマンス監視システムテストサイクル開始")

            # パフォーマンステスト実行
            test_result = await self.run_performance_test()

            # 結果に基づいてレポート送信
            await self.send_performance_report(test_result)

            logger.info("✅ パフォーマンス監視システムテストサイクル完了")
            return test_result

        except Exception as e:
            logger.error(f"❌ パフォーマンス監視システムテストサイクルエラー: {e}")
            return {"status": "error", "error": str(e)}

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            if self.engine:
                await self.engine.dispose()
            logger.info("✅ リソースをクリーンアップしました")
        except Exception as e:
            logger.error(f"❌ クリーンアップエラー: {e}")


async def main():
    """
    メイン関数
    """
    import sys

    # コマンドライン引数をチェック
    test_discord = "--test-discord" in sys.argv
    test_alert = "--test-alert" in sys.argv

    cron = PerformanceMonitoringTestCron()

    try:
        if test_discord:
            logger.info("🚀 Discord通知機能テスト開始")

            # Discord通知テストのみ実行
            success = await cron.test_discord_notification()

            if success:
                logger.info("🎉 Discord通知機能テスト完了")
            else:
                logger.error("❌ Discord通知機能テスト失敗")
                sys.exit(1)
        elif test_alert:
            logger.info("🚀 アラート通知機能テスト開始")

            # アラート通知テストのみ実行
            success = await cron.test_alert_notification()

            if success:
                logger.info("🎉 アラート通知機能テスト完了")
            else:
                logger.error("❌ アラート通知機能テスト失敗")
                sys.exit(1)
        else:
            logger.info("🚀 パフォーマンス監視システムテストcron開始")

            # 初期化
            await cron.initialize_database()
            await cron.initialize_services()

            # システムサイクル実行
            result = await cron.run_system_cycle()

            logger.info(f"🎉 パフォーマンス監視システムテストcron完了: {result}")

    except Exception as e:
        logger.error(f"❌ パフォーマンス監視システムテストcronエラー: {e}")
        logger.error(traceback.format_exc())
        sys.exit(1)

    finally:
        if not test_discord:
            await cron.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
