"""
テクニカル指標計算スケジューラー

USD/JPY特化のテクニカル指標自動計算スケジューラー
設計書参照: /app/note/database_implementation_design_2025.md
"""

import asyncio
import signal
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.technical_indicator_service import (
    TechnicalIndicatorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TechnicalIndicatorScheduler:
    """
    テクニカル指標計算スケジューラー

    責任:
    - テクニカル指標の自動計算
    - 複数タイムフレーム対応
    - 計算結果の保存
    - エラー処理

    特徴:
    - USD/JPY特化設計
    - 複数タイムフレーム対応
    - 包括的エラーハンドリング
    - 自動リトライ機能
    """

    def __init__(self):
        """
        初期化
        """
        self.running = False
        self.session: Optional[AsyncSession] = None
        self.indicator_service: Optional[TechnicalIndicatorService] = None

        # スケジューラー設定
        self.interval_minutes = 5
        self.max_retries = 3
        self.retry_delay = 30  # 秒

        # 対応タイムフレーム
        self.timeframes = ["5m", "1h", "4h", "1d"]

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "indicators_calculated": 0,
            "timeframes_processed": 0,
        }

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        logger.info("Initialized Technical Indicator Scheduler")

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
        スケジューラーを初期化
        """
        try:
            logger.info("Initializing Technical Indicator Scheduler...")

            # データベースセッション作成
            self.session = await get_async_session().__anext__()

            # サービス初期化
            self.indicator_service = TechnicalIndicatorService(self.session)

            logger.info("Technical Indicator Scheduler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Technical Indicator Scheduler: {e}")
            raise

    async def start(self):
        """
        スケジューラーを開始
        """
        try:
            logger.info("Starting Technical Indicator Scheduler...")

            # 初期化
            await self.initialize()

            self.running = True
            logger.info(
                f"Technical Indicator Scheduler started "
                f"(interval: {self.interval_minutes} minutes)"
            )

            # メインループ
            while self.running:
                try:
                    await self._run_single_execution()
                    await asyncio.sleep(self.interval_minutes * 60)

                except asyncio.CancelledError:
                    logger.info("Scheduler cancelled")
                    break
                except Exception as e:
                    await self._handle_execution_error(e)
                    await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"Failed to start Technical Indicator Scheduler: {e}")
            raise
        finally:
            await self.cleanup()

    async def _run_single_execution(self):
        """
        単一実行を実行
        """
        start_time = datetime.now()
        self.stats["total_runs"] += 1

        try:
            logger.info("Starting technical indicator calculation...")

            # 各タイムフレームで指標計算
            total_indicators = 0
            for timeframe in self.timeframes:
                indicators_count = await self._calculate_indicators_for_timeframe(
                    timeframe
                )
                total_indicators += indicators_count

            # 統計更新
            self.stats["successful_runs"] += 1
            self.stats["last_run"] = start_time
            self.stats["indicators_calculated"] += total_indicators
            self.stats["timeframes_processed"] += len(self.timeframes)

            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Technical indicator calculation completed successfully. "
                f"Timeframes: {len(self.timeframes)}, "
                f"Total indicators: {total_indicators}, "
                f"Execution time: {execution_time:.2f}s"
            )

        except Exception as e:
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)
            raise

    async def _calculate_indicators_for_timeframe(self, timeframe: str) -> int:
        """
        指定タイムフレームで指標を計算

        Args:
            timeframe: タイムフレーム

        Returns:
            int: 計算された指標数
        """
        try:
            logger.info(f"Calculating indicators for timeframe: {timeframe}")

            # 全指標を計算
            results = await self.indicator_service.calculate_all_indicators(
                timeframe=timeframe
            )

            # 計算された指標数をカウント
            total_indicators = sum(len(indicators) for indicators in results.values())

            logger.info(
                f"Calculated {total_indicators} indicators for {timeframe} timeframe"
            )

            return total_indicators

        except Exception as e:
            logger.error(f"Error calculating indicators for {timeframe}: {e}")
            raise

    async def _handle_execution_error(self, error: Exception):
        """
        実行エラーを処理

        Args:
            error: 発生したエラー
        """
        logger.error(f"Technical indicator calculation error: {error}")

        # リトライ回数チェック
        if self.stats["failed_runs"] >= self.max_retries:
            logger.error(
                f"Maximum retries ({self.max_retries}) exceeded. Stopping scheduler."
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
            self.indicator_service = TechnicalIndicatorService(self.session)

            logger.info("Successfully reconnected to database")

        except Exception as e:
            logger.error(f"Failed to reconnect to database: {e}")
            raise

    async def get_statistics(self) -> Dict:
        """
        統計情報を取得

        Returns:
            Dict: 統計情報
        """
        uptime = self._calculate_uptime()

        return {
            **self.stats,
            "uptime_seconds": uptime,
            "uptime_formatted": self._format_uptime(uptime),
            "success_rate": (
                (self.stats["successful_runs"] / self.stats["total_runs"] * 100)
                if self.stats["total_runs"] > 0
                else 0
            ),
            "timeframes": self.timeframes,
            "interval_minutes": self.interval_minutes,
        }

    def _calculate_uptime(self) -> int:
        """
        稼働時間を計算

        Returns:
            int: 稼働時間（秒）
        """
        if not self.stats["last_run"]:
            return 0

        return int((datetime.now() - self.stats["last_run"]).total_seconds())

    def _format_uptime(self, seconds: int) -> str:
        """
        稼働時間をフォーマット

        Args:
            seconds: 秒数

        Returns:
            str: フォーマットされた稼働時間
        """
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    async def stop(self):
        """
        スケジューラーを停止
        """
        logger.info("Stopping Technical Indicator Scheduler...")
        self.running = False

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Technical Indicator Scheduler cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def run_once(self):
        """
        一度だけ実行
        """
        try:
            await self.initialize()
            await self._run_single_execution()

        except Exception as e:
            logger.error(f"Error in single run: {e}")
            raise
        finally:
            await self.cleanup()


async def main():
    """
    メイン関数
    """
    scheduler = TechnicalIndicatorScheduler()

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())
