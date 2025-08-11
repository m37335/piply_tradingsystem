"""
継続処理スケジューラー

責任:
- 5分足データ取得の定期実行
- 継続処理パイプラインの統合管理
- エラー処理とリトライ機能
- システム監視とログ記録

特徴:
- 5分間隔での自動実行
- 包括的エラーハンドリング
- パフォーマンス監視
- 自動復旧機能
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.services.continuous_processing_service import (
    ContinuousProcessingService,
)
from src.infrastructure.database.services.system_initialization_manager import (
    SystemInitializationManager,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient

logger = logging.getLogger(__name__)


class ContinuousProcessingScheduler:
    """
    継続処理スケジューラー

    責任:
    - 5分足データ取得の定期実行
    - 継続処理パイプラインの統合管理
    - エラー処理とリトライ機能
    - システム監視とログ記録
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.running = False
        self.task = None

        # 依存サービス初期化
        self.initialization_manager = SystemInitializationManager(session)
        self.continuous_service = ContinuousProcessingService(session)
        self.yahoo_client = YahooFinanceClient()

        # スケジューラー設定
        self.interval_minutes = 5
        self.max_retries = 3
        self.retry_delay = 30  # 秒
        self.currency_pair = "USD/JPY"

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "processing_times": [],
            "start_time": None,
            "uptime": 0,
        }

        # エラー追跡
        self.error_history = []
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5

    async def start(self):
        """
        スケジューラーを開始
        """
        if self.running:
            logger.warning("⚠️ スケジューラーは既に実行中です")
            return

        try:
            logger.info("🚀 継続処理スケジューラーを開始します")
            self.running = True
            self.stats["start_time"] = datetime.now()

            # 初期化チェック
            await self._perform_initialization_check()

            # 定期実行タスクを開始
            self.task = asyncio.create_task(self._run_scheduler_loop())
            logger.info(
                f"✅ スケジューラーが開始されました（間隔: {self.interval_minutes}分）"
            )

        except Exception as e:
            logger.error(f"❌ スケジューラー開始エラー: {e}")
            self.running = False
            raise

    async def stop(self):
        """
        スケジューラーを停止
        """
        if not self.running:
            logger.warning("⚠️ スケジューラーは既に停止しています")
            return

        try:
            logger.info("🛑 継続処理スケジューラーを停止します")
            self.running = False

            if self.task:
                self.task.cancel()
                try:
                    await self.task
                except asyncio.CancelledError:
                    pass
                self.task = None

            # 稼働時間を更新
            if self.stats["start_time"]:
                self.stats["uptime"] = (
                    datetime.now() - self.stats["start_time"]
                ).total_seconds()

            logger.info("✅ スケジューラーが停止されました")

        except Exception as e:
            logger.error(f"❌ スケジューラー停止エラー: {e}")
            raise

    async def _run_scheduler_loop(self):
        """
        スケジューラーループ
        """
        while self.running:
            try:
                # 単一サイクルを実行
                await self.run_single_cycle()

                # 指定間隔で待機
                await asyncio.sleep(self.interval_minutes * 60)

            except asyncio.CancelledError:
                logger.info("🔄 スケジューラーループがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ スケジューラーループエラー: {e}")
                self.consecutive_failures += 1

                # 連続失敗回数が上限に達した場合
                if self.consecutive_failures >= self.max_consecutive_failures:
                    logger.error(
                        f"❌ 連続失敗回数が上限に達しました: {self.consecutive_failures}"
                    )
                    await self._handle_critical_failure()
                    break

                # エラー後に待機
                await asyncio.sleep(self.retry_delay)

    async def run_single_cycle(self):
        """
        単一サイクルの実行
        """
        start_time = datetime.now()
        self.stats["total_runs"] += 1

        try:
            logger.info(f"🔄 継続処理サイクル #{self.stats['total_runs']} 開始")

            # データ取得と処理を実行
            result = await self._fetch_and_process_data()

            # 統計情報を更新
            processing_time = (datetime.now() - start_time).total_seconds()
            self.stats["processing_times"].append(processing_time)
            self.stats["successful_runs"] += 1
            self.stats["last_run"] = datetime.now()
            self.consecutive_failures = 0  # 成功時にリセット

            logger.info(f"✅ 継続処理サイクル完了: {processing_time:.2f}秒")
            logger.info(f"結果: {result}")

        except Exception as e:
            self.stats["failed_runs"] += 1
            self.stats["last_error"] = str(e)
            self.consecutive_failures += 1

            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ 継続処理サイクルエラー: {e}")

            # エラー履歴に追加
            self.error_history.append(
                {
                    "timestamp": datetime.now(),
                    "error": str(e),
                    "cycle_number": self.stats["total_runs"],
                    "processing_time": processing_time,
                }
            )

            # エラーハンドリング
            await self._handle_error(e)

    async def _fetch_and_process_data(self) -> Dict[str, Any]:
        """
        データ取得と処理を実行

        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            # 1. 5分足データを取得
            price_data = await self._fetch_5m_data()
            if not price_data:
                raise Exception("5分足データ取得失敗")

            # 2. 継続処理を実行
            result = await self.continuous_service.process_5m_data(price_data)

            return result

        except Exception as e:
            logger.error(f"❌ データ取得・処理エラー: {e}")
            raise

    async def _fetch_5m_data(self) -> Optional[PriceDataModel]:
        """
        5分足データを取得

        Returns:
            Optional[PriceDataModel]: 取得された価格データ
        """
        try:
            # Yahoo Financeから現在のレートを取得
            current_rate = await self.yahoo_client.get_current_rate(self.currency_pair)
            if not current_rate:
                raise Exception("現在のレート取得失敗")

            # PriceDataModelを作成
            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=datetime.now(),
                open_price=float(current_rate.get("open", 0)),
                high_price=float(current_rate.get("high", 0)),
                low_price=float(current_rate.get("low", 0)),
                close_price=float(current_rate.get("close", 0)),
                volume=int(current_rate.get("volume", 1000000)),
                data_source="Yahoo Finance Continuous Processing",
            )

            logger.info(f"📊 5分足データ取得完了: {price_data.close_price}")
            return price_data

        except Exception as e:
            logger.error(f"❌ 5分足データ取得エラー: {e}")
            return None

    async def _perform_initialization_check(self):
        """
        初期化チェックを実行
        """
        try:
            logger.info("🔍 初期化状態をチェック中...")

            # システムサイクルを実行（初期化チェック + 継続処理）
            result = await self.initialization_manager.run_system_cycle()

            logger.info(f"✅ 初期化チェック完了: {result}")

        except Exception as e:
            logger.error(f"❌ 初期化チェックエラー: {e}")
            raise

    async def _handle_error(self, error: Exception):
        """
        エラーハンドリング

        Args:
            error: 発生したエラー
        """
        try:
            logger.warning(f"⚠️ エラーハンドリング開始: {error}")

            # エラー種別に応じた処理
            if "API" in str(error):
                logger.warning("API制限エラーを検出、待機時間を延長")
                await asyncio.sleep(self.retry_delay * 2)
            elif "Database" in str(error):
                logger.warning("データベースエラーを検出、リトライを実行")
                await asyncio.sleep(self.retry_delay)
            else:
                logger.warning("一般的なエラーを検出、標準待機時間でリトライ")
                await asyncio.sleep(self.retry_delay)

        except Exception as e:
            logger.error(f"❌ エラーハンドリング中にエラーが発生: {e}")

    async def _handle_critical_failure(self):
        """
        重大な障害の処理
        """
        try:
            logger.error("🚨 重大な障害を検出、スケジューラーを停止します")

            # アラート送信（実装予定）
            # await self._send_critical_alert()

            # スケジューラーを停止
            await self.stop()

        except Exception as e:
            logger.error(f"❌ 重大障害処理中にエラーが発生: {e}")

    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """
        スケジューラー統計を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        # 稼働時間を更新
        if self.stats["start_time"] and self.running:
            self.stats["uptime"] = (
                datetime.now() - self.stats["start_time"]
            ).total_seconds()

        return {
            **self.stats,
            "running": self.running,
            "success_rate": (
                self.stats["successful_runs"] / max(self.stats["total_runs"], 1) * 100
            ),
            "average_processing_time": (
                sum(self.stats["processing_times"])
                / max(len(self.stats["processing_times"]), 1)
            ),
            "consecutive_failures": self.consecutive_failures,
            "error_count": len(self.error_history),
            "interval_minutes": self.interval_minutes,
        }

    async def reset_stats(self):
        """
        統計情報をリセット
        """
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "processing_times": [],
            "start_time": datetime.now() if self.running else None,
            "uptime": 0,
        }
        self.error_history = []
        self.consecutive_failures = 0
        logger.info("🔄 スケジューラー統計をリセットしました")

    async def health_check(self) -> Dict[str, Any]:
        """
        スケジューラー健全性チェック

        Returns:
            Dict[str, Any]: 健全性情報
        """
        try:
            health_status = {
                "service": "ContinuousProcessingScheduler",
                "status": "healthy",
                "timestamp": datetime.now(),
                "running": self.running,
                "uptime": self.stats.get("uptime", 0),
                "consecutive_failures": self.consecutive_failures,
            }

            # 依存サービスの健全性チェック
            try:
                init_health = await self.initialization_manager.health_check()
                health_status["initialization_manager"] = init_health["status"]
            except Exception as e:
                health_status["initialization_manager"] = f"unhealthy: {e}"

            try:
                continuous_health = await self.continuous_service.health_check()
                health_status["continuous_service"] = continuous_health["status"]
            except Exception as e:
                health_status["continuous_service"] = f"unhealthy: {e}"

            # 全体の健全性判定
            if self.consecutive_failures >= self.max_consecutive_failures:
                health_status["status"] = "critical"
            elif self.consecutive_failures > 0:
                health_status["status"] = "degraded"
            elif not self.running:
                health_status["status"] = "stopped"

            return health_status

        except Exception as e:
            return {
                "service": "ContinuousProcessingScheduler",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(),
            }

    async def update_config(
        self,
        interval_minutes: Optional[int] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[int] = None,
    ):
        """
        設定を更新

        Args:
            interval_minutes: 実行間隔（分）
            max_retries: 最大リトライ回数
            retry_delay: リトライ待機時間（秒）
        """
        if interval_minutes is not None:
            self.interval_minutes = interval_minutes
            logger.info(f"🔄 実行間隔を更新: {interval_minutes}分")

        if max_retries is not None:
            self.max_retries = max_retries
            logger.info(f"🔄 最大リトライ回数を更新: {max_retries}")

        if retry_delay is not None:
            self.retry_delay = retry_delay
            logger.info(f"🔄 リトライ待機時間を更新: {retry_delay}秒")
