#!/usr/bin/env python3
"""
テクニカル分析cronスクリプト

USD/JPY特化のテクニカル分析定期実行スクリプト
設計書参照: /app/note/database_implementation_design_2025.md

使用方法:
    python scripts/cron/technical_analysis_cron.py

cron設定例:
    */10 * * * * cd /app && python scripts/cron/technical_analysis_cron.py >> \
        /var/log/technical_analysis.log 2>&1
"""

import asyncio
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.notification_integration_service import (
        NotificationIntegrationService,
    )
    from src.infrastructure.database.services.pattern_detection_service import (
        PatternDetectionService,
    )
    from src.infrastructure.database.services.technical_indicator_service import (
        TechnicalIndicatorService,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class TechnicalAnalysisCron:
    """
    テクニカル分析cronスクリプト

    責任:
    - 指標計算の定期実行
    - パターン検出の定期実行
    - 通知送信の定期実行
    - 監視機能

    特徴:
    - USD/JPY特化設計
    - 10分間隔実行
    - 包括的エラーハンドリング
    - 自動リトライ機能
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
        self.interval_minutes = 10  # 10分間隔

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "start_time": datetime.now(),
            "indicators_calculated": 0,
            "patterns_detected": 0,
            "notifications_sent": 0,
        }

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        logger.info("Initialized Technical Analysis Cron")

    def _setup_signal_handlers(self):
        """
        シグナルハンドラーを設定
        """
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """
        シグナルハンドラー

        Args:
            signum: シグナル番号
            frame: フレーム
        """
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False

    async def initialize(self):
        """
        cronスクリプトを初期化
        """
        try:
            logger.info("Initializing Technical Analysis Cron...")

            # データベースセッション作成
            self.session = await get_async_session().__anext__()

            # サービス初期化
            self.services = {
                "indicator_service": TechnicalIndicatorService(self.session),
                "pattern_service": PatternDetectionService(self.session),
                "notification_service": NotificationIntegrationService(self.session),
            }

            logger.info("Technical Analysis Cron initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Technical Analysis Cron: {e}")
            raise

    async def run_single_execution(self):
        """
        単一実行を実行
        """
        start_time = time.time()
        self.stats["total_runs"] += 1

        try:
            logger.info(f"Starting technical analysis run #{self.stats['total_runs']}")

            # 1. テクニカル指標計算
            logger.info("Step 1: Calculating technical indicators...")
            indicator_service = self.services["indicator_service"]
            indicator_results = await indicator_service.calculate_all_indicators()

            total_indicators = sum(
                len(indicators) for indicators in indicator_results.values()
            )
            self.stats["indicators_calculated"] += total_indicators
            logger.info(f"Calculated {total_indicators} technical indicators")

            # 2. パターン検出
            logger.info("Step 2: Detecting patterns...")
            pattern_service = self.services["pattern_service"]
            pattern_results = await pattern_service.detect_all_patterns()

            total_patterns = sum(len(patterns) for patterns in pattern_results.values())
            self.stats["patterns_detected"] += total_patterns
            logger.info(f"Detected {total_patterns} patterns")

            # 3. 通知処理
            logger.info("Step 3: Processing notifications...")
            notification_service = self.services["notification_service"]
            notification_results = (
                await notification_service.process_pattern_notifications()
            )

            self.stats["notifications_sent"] += notification_results["sent"]
            logger.info(
                f"Notification results: {notification_results['sent']} sent, "
                f"{notification_results['skipped']} skipped, "
                f"{notification_results['errors']} errors"
            )

            # 統計更新
            self.stats["successful_runs"] += 1
            self.stats["last_run"] = datetime.now()

            execution_time = time.time() - start_time
            logger.info(
                f"Technical analysis completed successfully in {execution_time:.2f}s"
            )

        except Exception as e:
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)
            logger.error(f"Error in technical analysis: {e}")
            raise

    async def run_continuous(self):
        """
        継続実行モード
        """
        try:
            logger.info("Starting Technical Analysis Cron in continuous mode...")

            # 初期化
            await self.initialize()

            self.running = True
            logger.info(
                f"Technical Analysis Cron started successfully "
                f"(interval: {self.interval_minutes} minutes)"
            )

            # メインループ
            while self.running:
                try:
                    await self.run_single_execution()

                    # 指定間隔で待機
                    await asyncio.sleep(self.interval_minutes * 60)

                except asyncio.CancelledError:
                    logger.info("Technical Analysis Cron cancelled")
                    break
                except Exception as e:
                    await self._handle_execution_error(e)
                    await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"Failed to start Technical Analysis Cron: {e}")
            raise
        finally:
            await self.cleanup()

    async def _handle_execution_error(self, error: Exception):
        """
        実行エラーを処理

        Args:
            error: 発生したエラー
        """
        logger.error(f"Technical Analysis Cron execution error: {error}")

        # リトライ回数チェック
        if self.stats["failed_runs"] >= self.max_retries:
            logger.error(
                f"Maximum retries ({self.max_retries}) exceeded. "
                "Stopping Technical Analysis Cron."
            )
            self.running = False
            return

        # 再接続試行
        try:
            await self._reconnect()
        except Exception as reconnect_error:
            logger.error(f"Failed to reconnect: {reconnect_error}")

    async def _reconnect(self):
        """
        データベース再接続
        """
        try:
            logger.info("Attempting to reconnect to database...")

            # 既存セッションをクローズ
            if self.session:
                await self.session.close()

            # 新しいセッションを作成
            self.session = await get_async_session().__anext__()

            # サービスを再初期化
            self.services = {
                "indicator_service": TechnicalIndicatorService(self.session),
                "pattern_service": PatternDetectionService(self.session),
                "notification_service": NotificationIntegrationService(self.session),
            }

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
            "interval_minutes": self.interval_minutes,
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

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Technical Analysis Cron cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting Technical Analysis Cron...")

    # 環境変数チェック
    required_env_vars = [
        "DATABASE_URL",
        "DISCORD_WEBHOOK_URL",
    ]

    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)

    cron = TechnicalAnalysisCron()

    try:
        # コマンドライン引数チェック
        if len(sys.argv) > 1 and sys.argv[1] == "--once":
            # 単発実行モード
            await cron.initialize()
            await cron.run_single_execution()
        else:
            # 継続実行モード
            await cron.run_continuous()

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Technical Analysis Cron failed: {e}")
        sys.exit(1)
    finally:
        await cron.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
