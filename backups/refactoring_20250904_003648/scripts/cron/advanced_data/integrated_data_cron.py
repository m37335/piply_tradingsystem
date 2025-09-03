#!/usr/bin/env python3
"""
統合データcronスクリプト

USD/JPY特化の統合データ処理cronスクリプト
設計書参照: /app/note/basic_data_acquisition_system_improvement_design.md

責任:
- 統合データサービスの定期実行
- データ取得・計算・検出の統合管理
- エラーハンドリングとリトライ
- パフォーマンス監視

特徴:
- ワンストップデータ処理
- 統合エラーハンドリング
- パフォーマンス最適化
- データ品質保証
"""

import asyncio
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.integrated_data_service import (
        IntegratedDataService,
    )
    from src.infrastructure.database.services.notification_integration_service import (
        NotificationIntegrationService,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class IntegratedDataCron:
    """
    統合データcronスクリプト

    責任:
    - 統合データサービスの定期実行
    - エラーハンドリングとリトライ
    - パフォーマンス監視
    - 通知処理

    特徴:
    - 統合データ処理
    - 包括的エラーハンドリング
    - 自動リトライ機能
    - パフォーマンス監視
    """

    def __init__(self):
        """
        初期化
        """
        self.running = False
        self.session = None
        self.services = {}

        # 実行設定
        self.currency_pair = "USD/JPY"
        self.max_retries = 3
        self.retry_delay = 30  # 秒
        self.execution_interval = 300  # 5分間隔

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "start_time": datetime.now(),
            "total_execution_time": 0,
            "average_execution_time": 0,
        }

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        logger.info("Initialized Integrated Data Cron")

    def _setup_signal_handlers(self):
        """シグナルハンドラー設定"""
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def initialize(self):
        """初期化"""
        try:
            # データベース接続
            self.session = await get_async_session()

            # 統合データサービス初期化
            self.services["integrated_data"] = IntegratedDataService(self.session)

            # 通知サービス初期化
            self.services["notification"] = NotificationIntegrationService(self.session)

            logger.info("Integrated Data Cron initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Integrated Data Cron: {e}")
            raise

    async def run_single_execution(self):
        """
        単発実行
        """
        self.stats["total_runs"] += 1

        try:
            logger.info(
                f"Starting integrated data processing run #{self.stats['total_runs']}"
            )

            # 統合データサービスで完全なデータサイクルを実行
            integrated_service = self.services["integrated_data"]
            results = await integrated_service.run_complete_data_cycle()

            if results["overall_success"]:
                # 統計更新
                self.stats["successful_runs"] += 1
                self.stats["last_run"] = datetime.now()

                # 実行時間統計
                execution_time = results["execution_time"]
                self.stats["total_execution_time"] += execution_time
                self.stats["average_execution_time"] = (
                    self.stats["total_execution_time"] / self.stats["total_runs"]
                )

                logger.info(
                    f"Integrated data processing completed successfully in {execution_time:.2f}s"
                )
                logger.info(f"Data fetch: {results['data_fetch']['records']} records")
                logger.info(
                    f"Technical indicators: {results['technical_indicators']['indicators']} indicators"
                )
                logger.info(
                    f"Pattern detection: {results['pattern_detection']['patterns']} patterns"
                )

                # 通知処理（パターンが検出された場合）
                if results["pattern_detection"]["patterns"] > 0:
                    await self._process_notifications()

            else:
                self.stats["failed_runs"] += 1
                self.stats["last_error"] = "Integrated data cycle failed"
                logger.error("Integrated data processing failed")

        except Exception as e:
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)
            logger.error(f"Error in integrated data processing: {e}")
            raise

    async def _process_notifications(self):
        """通知処理"""
        try:
            logger.info("Processing notifications...")

            # 最新のパターンを取得して通知
            integrated_service = self.services["integrated_data"]
            pattern_service = integrated_service.pattern_service

            latest_patterns = await pattern_service.get_latest_patterns(limit=5)
            if latest_patterns:
                notification_service = self.services["notification"]
                await notification_service.send_notifications(latest_patterns)
                logger.info(f"Sent notifications for {len(latest_patterns)} patterns")
            else:
                logger.info("No patterns to notify")

        except Exception as e:
            logger.error(f"Error processing notifications: {e}")

    async def run_continuous(self):
        """
        継続実行モード
        """
        try:
            logger.info("Starting Integrated Data Cron in continuous mode...")

            # 初期化
            await self.initialize()

            self.running = True
            logger.info("Integrated Data Cron started successfully")

            # メインループ
            while self.running:
                try:
                    await self.run_single_execution()

                    # 実行間隔待機
                    await asyncio.sleep(self.execution_interval)

                except asyncio.CancelledError:
                    logger.info("Integrated Data Cron cancelled")
                    break
                except Exception as e:
                    await self._handle_execution_error(e)
                    await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"Failed to start Integrated Data Cron: {e}")
            raise
        finally:
            await self.cleanup()

    async def _handle_execution_error(self, error: Exception):
        """
        実行エラーを処理

        Args:
            error: 発生したエラー
        """
        logger.error(f"Integrated Data Cron execution error: {error}")

        # データベース接続の再試行
        if "database" in str(error).lower() or "connection" in str(error).lower():
            logger.info("Attempting to reconnect to database...")
            await self._reconnect_database()

    async def _reconnect_database(self):
        """データベース再接続"""
        try:
            if self.session:
                await self.session.close()

            self.session = await get_async_session()

            # サービスを再初期化
            self.services["integrated_data"] = IntegratedDataService(self.session)
            self.services["notification"] = NotificationIntegrationService(self.session)

            logger.info("Successfully reconnected to database")

        except Exception as e:
            logger.error(f"Failed to reconnect to database: {e}")
            raise

    async def get_statistics(self):
        """
        統計情報を取得

        Returns:
            dict: 統計情報
        """
        uptime = (datetime.now() - self.stats["start_time"]).total_seconds()

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "success_rate": (
                (self.stats["successful_runs"] / self.stats["total_runs"] * 100)
                if self.stats["total_runs"] > 0
                else 0
            ),
            "currency_pair": self.currency_pair,
            "execution_interval": self.execution_interval,
        }

    def _format_uptime(self, seconds: float) -> str:
        """
        稼働時間をフォーマット

        Args:
            seconds: 秒数

        Returns:
            str: フォーマットされた稼働時間
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    async def get_system_status(self):
        """
        システム状態を取得

        Returns:
            dict: システム状態
        """
        try:
            if "integrated_data" in self.services:
                return await self.services["integrated_data"].get_system_status()
            else:
                return {
                    "currency_pair": self.currency_pair,
                    "system_health": "initializing",
                    "last_update": datetime.now().isoformat(),
                }
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {
                "currency_pair": self.currency_pair,
                "system_health": "error",
                "error": str(e),
                "last_update": datetime.now().isoformat(),
            }

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Integrated Data Cron cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting Integrated Data Cron...")

    # 環境変数チェック
    required_env_vars = [
        "DISCORD_WEBHOOK_URL",
        "YAHOO_FINANCE_API_KEY",
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    # テスト用SQLiteデータベースを設定
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"

    cron = IntegratedDataCron()

    try:
        # コマンドライン引数チェック
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            # 単発実行モード
            await cron.initialize()
            await cron.run_single_execution()
        elif len(sys.argv) > 1 and sys.argv[1] == "--status":
            # 状態確認モード
            await cron.initialize()
            status = await cron.get_system_status()
            print(f"System Status: {status}")
        else:
            # 継続実行モード
            await cron.run_continuous()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Integrated Data Cron failed: {e}")
        sys.exit(1)
    finally:
        await cron.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
