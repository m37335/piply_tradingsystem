"""
USD/JPYデータ取得スケジューラー

USD/JPY特化の5分おきデータ取得システム用のスケジューラー
設計書参照: /app/note/database_implementation_design_2025.md
"""

import asyncio
import signal
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService
from src.infrastructure.database.services.technical_indicator_service import (
    TechnicalIndicatorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class USDJPYDataScheduler:
    """
    USD/JPYデータ取得スケジューラー

    責任:
    - 5分間隔でのデータ取得
    - テクニカル指標計算
    - エラーハンドリング
    - ログ出力

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
        self.session: Optional[AsyncSession] = None
        self.data_fetcher: Optional[DataFetcherService] = None
        self.indicator_service: Optional[TechnicalIndicatorService] = None

        # スケジューラー設定
        self.interval_minutes = 5
        self.max_retries = 3
        self.retry_delay = 30  # 秒

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
        }

        # シグナルハンドラー設定
        self._setup_signal_handlers()

        logger.info("Initialized USD/JPY Data Scheduler")

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
            logger.info("Initializing USD/JPY Data Scheduler...")

            # データベースセッション作成
            self.session = await get_async_session().__anext__()

            # サービス初期化
            self.data_fetcher = DataFetcherService(self.session)
            self.indicator_service = TechnicalIndicatorService(self.session)

            # 接続テスト
            connection_ok = await self.data_fetcher.test_connection()
            if not connection_ok:
                raise Exception("Failed to connect to Yahoo Finance API")

            logger.info("USD/JPY Data Scheduler initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}")
            raise

    async def start(self):
        """
        スケジューラーを開始
        """
        try:
            await self.initialize()

            self.running = True
            logger.info(
                f"Starting USD/JPY Data Scheduler (interval: {self.interval_minutes} minutes)"
            )

            # 初回実行
            await self._run_single_execution()

            # 定期実行ループ
            while self.running:
                try:
                    # 次の実行時刻まで待機
                    await asyncio.sleep(self.interval_minutes * 60)

                    if self.running:
                        await self._run_single_execution()

                except asyncio.CancelledError:
                    logger.info("Scheduler cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in scheduler loop: {e}")
                    await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"Fatal error in scheduler: {e}")
        finally:
            await self.cleanup()

    async def _run_single_execution(self):
        """
        単回実行
        """
        start_time = datetime.now()
        self.stats["total_runs"] += 1

        try:
            logger.info(f"Starting execution #{self.stats['total_runs']}")

            # 1. 現在の価格データを取得
            price_data = await self._fetch_current_price_data()
            if not price_data:
                raise Exception("Failed to fetch current price data")

            # 2. テクニカル指標を計算
            await self._calculate_technical_indicators()

            # 3. 統計情報を更新
            self.stats["successful_runs"] += 1
            self.stats["last_run"] = start_time
            self.stats["last_error"] = None

            execution_time = datetime.now() - start_time
            logger.info(
                f"Execution #{self.stats['total_runs']} completed successfully "
                f"in {execution_time.total_seconds():.2f} seconds"
            )

        except Exception as e:
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)

            execution_time = datetime.now() - start_time
            logger.error(
                f"Execution #{self.stats['total_runs']} failed "
                f"after {execution_time.total_seconds():.2f} seconds: {e}"
            )

            # リトライ処理
            await self._handle_execution_error(e)

    async def _fetch_current_price_data(self):
        """
        現在の価格データを取得

        Returns:
            Optional[PriceDataModel]: 取得した価格データ
        """
        try:
            logger.info("Fetching current price data...")

            for attempt in range(self.max_retries):
                try:
                    price_data = await self.data_fetcher.fetch_current_price_data()
                    if price_data:
                        logger.info(
                            f"Successfully fetched price data: "
                            f"Close={price_data.close_price}, "
                            f"Volume={price_data.volume}"
                        )
                        return price_data
                    else:
                        raise Exception("No price data returned")

                except Exception as e:
                    if attempt < self.max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1} failed, retrying in {self.retry_delay} seconds: {e}"
                        )
                        await asyncio.sleep(self.retry_delay)
                    else:
                        raise

            return None

        except Exception as e:
            logger.error(
                f"Failed to fetch current price data after {self.max_retries} attempts: {e}"
            )
            return None

    async def _calculate_technical_indicators(self):
        """
        テクニカル指標を計算

        Returns:
            Dict: 計算された指標の辞書
        """
        try:
            logger.info("Calculating technical indicators...")

            # 最新の価格データを取得
            latest_price_data = await self.data_fetcher.get_latest_price_data(limit=100)
            if not latest_price_data:
                logger.warning("No price data available for indicator calculation")
                return {}

            # 計算期間を設定
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)  # 1週間分

            # 全指標を計算
            indicators = await self.indicator_service.calculate_all_indicators(
                timeframe="5m",
                start_date=start_date,
                end_date=end_date,
            )

            total_indicators = sum(len(ind_list) for ind_list in indicators.values())
            logger.info(
                f"Successfully calculated {total_indicators} technical indicators"
            )

            return indicators

        except Exception as e:
            logger.error(f"Failed to calculate technical indicators: {e}")
            return {}

    async def _handle_execution_error(self, error: Exception):
        """
        実行エラーを処理

        Args:
            error: 発生したエラー
        """
        try:
            logger.warning(f"Handling execution error: {error}")

            # エラーに応じた処理
            if "connection" in str(error).lower():
                logger.info("Connection error detected, attempting to reconnect...")
                await self._reconnect()
            elif "rate limit" in str(error).lower():
                logger.info("Rate limit detected, waiting longer...")
                await asyncio.sleep(self.retry_delay * 2)
            else:
                logger.info("Unknown error, waiting before retry...")
                await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"Error in error handler: {e}")

    async def _reconnect(self):
        """
        再接続処理
        """
        try:
            logger.info("Attempting to reconnect...")

            # セッションを再作成
            if self.session:
                await self.session.close()

            self.session = await get_async_session().__anext__()

            # サービスを再初期化
            self.data_fetcher = DataFetcherService(self.session)
            self.indicator_service = TechnicalIndicatorService(self.session)

            # 接続テスト
            connection_ok = await self.data_fetcher.test_connection()
            if connection_ok:
                logger.info("Reconnection successful")
            else:
                raise Exception("Reconnection failed")

        except Exception as e:
            logger.error(f"Reconnection failed: {e}")

    async def get_statistics(self):
        """
        統計情報を取得

        Returns:
            Dict: 統計情報
        """
        return {
            **self.stats,
            "uptime": self._calculate_uptime(),
            "success_rate": (
                self.stats["successful_runs"] / self.stats["total_runs"] * 100
                if self.stats["total_runs"] > 0
                else 0
            ),
        }

    def _calculate_uptime(self):
        """
        稼働時間を計算

        Returns:
            str: 稼働時間の文字列
        """
        if not self.stats["last_run"]:
            return "0:00:00"

        uptime = datetime.now() - self.stats["last_run"]
        hours = int(uptime.total_seconds() // 3600)
        minutes = int((uptime.total_seconds() % 3600) // 60)
        seconds = int(uptime.total_seconds() % 60)

        return f"{hours}:{minutes:02d}:{seconds:02d}"

    async def stop(self):
        """
        スケジューラーを停止
        """
        logger.info("Stopping USD/JPY Data Scheduler...")
        self.running = False

    async def cleanup(self):
        """
        クリーンアップ処理
        """
        try:
            logger.info("Cleaning up scheduler resources...")

            if self.session:
                await self.session.close()

            logger.info("Scheduler cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def run_once(self):
        """
        1回だけ実行（テスト用）

        Returns:
            bool: 実行成功の場合True
        """
        try:
            await self.initialize()
            await self._run_single_execution()
            return True

        except Exception as e:
            logger.error(f"Single execution failed: {e}")
            return False
        finally:
            await self.cleanup()


async def main():
    """
    メイン関数
    """
    scheduler = USDJPYDataScheduler()

    try:
        await scheduler.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await scheduler.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
