#!/usr/bin/env python3
"""
USD/JPYデータ取得cronスクリプト

USD/JPY特化の5分おきデータ取得システム用のcronスクリプト
設計書参照: /app/note/database_implementation_design_2025.md

使用方法:
    python scripts/cron/usdjpy_data_cron.py

cron設定例:
    */5 * * * * cd /app && python scripts/cron/usdjpy_data_cron.py >> \
        /var/log/usdjpy_data.log 2>&1
"""

import asyncio
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.analysis.technical_indicators import (
        TechnicalIndicatorsAnalyzer,
    )
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.data_fetcher_service import (
        DataFetcherService,
    )
    from src.infrastructure.database.services.notification_integration_service import (
        NotificationIntegrationService,
    )
    from src.infrastructure.database.services.pattern_detection_service import (
        PatternDetectionService,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class USDJPYDataCron:
    """
    USD/JPYデータ取得cronスクリプト

    責任:
    - 5分間隔でのデータ取得・保存・分析
    - エラーハンドリング
    - ログ出力
    - 監視機能

    特徴:
    - USD/JPY特化設計
    - 5分間隔実行
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

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "start_time": datetime.now(),
        }

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        logger.info("Initialized USD/JPY Data Cron")

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
            logger.info("Initializing USD/JPY Data Cron...")

            # データベースセッション作成
            self.session = await get_async_session()

            # サービス初期化
            self.services = {
                "data_fetcher": DataFetcherService(self.session),
                "technical_analyzer": TechnicalIndicatorsAnalyzer(),
                "pattern_service": PatternDetectionService(self.session),
                "notification_service": NotificationIntegrationService(self.session),
            }

            logger.info("USD/JPY Data Cron initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize USD/JPY Data Cron: {e}")
            raise

    async def run_single_execution(self):
        """
        単一実行を実行
        """
        start_time = time.time()
        self.stats["total_runs"] += 1

        try:
            logger.info(
                f"Starting USD/JPY data processing run #{self.stats['total_runs']}"
            )

            # 1. データ取得
            logger.info("Step 1: Fetching current price data...")
            data_fetcher = self.services["data_fetcher"]
            price_data = await data_fetcher.fetch_current_price_data()

            if not price_data:
                raise Exception("No price data fetched")

            logger.info(f"Fetched price data: {price_data}")

            # 2. テクニカル指標計算（簡易版）
            logger.info("Step 2: Calculating technical indicators...")
            # 現在はデータベースに既に計算済みのテクニカル指標があるため、
            # パターン検出に必要な最小限の処理のみ実行
            logger.info("Technical indicators already calculated in database")

            # 3. パターン検出
            logger.info("Step 3: Detecting patterns...")
            pattern_service = self.services["pattern_service"]
            pattern_results = await pattern_service.detect_all_patterns()

            total_patterns = sum(len(patterns) for patterns in pattern_results.values())
            logger.info(f"Detected {total_patterns} patterns")

            # 4. 通知処理
            logger.info("Step 4: Processing notifications...")
            notification_service = self.services["notification_service"]

            # 最新のパターンを取得して通知
            latest_patterns = await pattern_service.get_latest_patterns(limit=5)
            if latest_patterns:
                notification_results = await notification_service.send_notifications(
                    latest_patterns
                )
                logger.info(f"Sent notifications for {len(latest_patterns)} patterns")
            else:
                logger.info("No patterns to notify")

            # 統計更新
            self.stats["successful_runs"] += 1
            self.stats["last_run"] = datetime.now()

            execution_time = time.time() - start_time
            logger.info(
                f"USD/JPY data processing completed successfully in {execution_time:.2f}s"
            )

        except Exception as e:
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)
            logger.error(f"Error in USD/JPY data processing: {e}")
            raise

    async def run_continuous(self):
        """
        継続実行モード
        """
        try:
            logger.info("Starting USD/JPY Data Cron in continuous mode...")

            # 初期化
            await self.initialize()

            self.running = True
            logger.info("USD/JPY Data Cron started successfully")

            # メインループ
            while self.running:
                try:
                    await self.run_single_execution()

                    # 5分間待機
                    await asyncio.sleep(300)  # 5分 = 300秒

                except asyncio.CancelledError:
                    logger.info("USD/JPY Data Cron cancelled")
                    break
                except Exception as e:
                    await self._handle_execution_error(e)
                    await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"Failed to start USD/JPY Data Cron: {e}")
            raise
        finally:
            await self.cleanup()

    async def _handle_execution_error(self, error: Exception):
        """
        実行エラーを処理

        Args:
            error: 発生したエラー
        """
        logger.error(f"USD/JPY Data Cron execution error: {error}")

        # リトライ回数チェック
        if self.stats["failed_runs"] >= self.max_retries:
            logger.error(
                f"Maximum retries ({self.max_retries}) exceeded. "
                "Stopping USD/JPY Data Cron."
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
                "data_fetcher": DataFetcherService(self.session),
                "technical_analyzer": TechnicalIndicatorsAnalyzer(),
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
            logger.info("USD/JPY Data Cron cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting USD/JPY Data Cron...")

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
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

    cron = USDJPYDataCron()

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
        logger.error(f"USD/JPY Data Cron failed: {e}")
        sys.exit(1)
    finally:
        await cron.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
