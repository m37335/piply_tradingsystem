"""
継続処理スケジューラー（シンプル版）

責任:
- 5分足データ取得の実行
- 継続処理パイプラインの統合管理
- シンプルなエラーハンドリング

特徴:
- シンプルな構造
- 必要最小限の機能
- メンテナンスしやすい設計
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.services.continuous_processing_service import (
    ContinuousProcessingService,
)
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService

logger = logging.getLogger(__name__)


class ContinuousProcessingScheduler:
    """
    継続処理スケジューラー（シンプル版）

    責任:
    - 5分足データ取得の実行
    - 継続処理パイプラインの統合管理
    - シンプルなエラーハンドリング
    """

    def __init__(self, session: AsyncSession):
        self.session = session

        # 依存サービス初期化（必要最小限）
        self.data_fetcher = DataFetcherService(session)
        self.continuous_service = ContinuousProcessingService(session)

    async def run_single_cycle(self):
        """
        単一サイクルの実行（UnifiedTechnicalCalculator統合版）
        """
        try:
            logger.info("🔄 継続処理サイクル開始（UnifiedTechnicalCalculator統合版）")

            # 直接DataFetcherServiceを呼び出し
            result = await self._direct_fetch_data()

            # UnifiedTechnicalCalculatorによる処理確認
            if result and result.get("price_data"):
                await self.continuous_service.process_5m_data(result["price_data"])

            logger.info("✅ 継続処理サイクル完了（UnifiedTechnicalCalculator統合版）")
            return result

        except Exception as e:
            logger.error(f"❌ 継続処理サイクルエラー: {e}")
            raise

    async def _direct_fetch_data(self) -> Dict[str, Any]:
        """
        直接DataFetcherService.fetch_real_5m_data()を呼び出し

        Returns:
            Dict[str, Any]: 処理結果
        """
        try:
            logger.info("🎯 直接DataFetcherService.fetch_real_5m_data()を呼び出し")

            # 直接DataFetcherServiceを呼び出し
            price_data = await self.data_fetcher.fetch_real_5m_data()

            if not price_data:
                raise Exception("DataFetcherService.fetch_real_5m_data()でデータ取得失敗")

            logger.info(
                f"✅ 直接データ取得完了: "
                f"O={price_data.open_price}, H={price_data.high_price}, "
                f"L={price_data.low_price}, C={price_data.close_price}"
            )

            result = {
                "status": "success",
                "method": "direct_fetch",
                "price_data": price_data,
                "message": "DataFetcherService.fetch_real_5m_data()で直接取得",
            }

            return result

        except Exception as e:
            logger.error(f"❌ 直接データ取得エラー: {e}")
            raise

    async def _fetch_and_process_data(self) -> Dict[str, Any]:
        """
        データ取得と処理を実行（シンプル版）

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
        5分足データを取得（シンプル版）

        Returns:
            Optional[PriceDataModel]: 取得された価格データ
        """
        try:
            # 実際の5分足データを取得
            price_data = await self.data_fetcher.fetch_real_5m_data()
            if not price_data:
                raise Exception("実際の5分足データ取得失敗")

            logger.info(f"📊 実際の5分足データ取得完了: {price_data.close_price}")
            return price_data

        except Exception as e:
            logger.error(f"❌ 実際の5分足データ取得エラー: {e}")
            return None

    async def health_check(self) -> Dict[str, Any]:
        """
        スケジューラー健全性チェック（シンプル版）

        Returns:
            Dict[str, Any]: 健全性情報
        """
        try:
            health_status = {
                "service": "ContinuousProcessingScheduler",
                "status": "healthy",
                "timestamp": datetime.now(),
                "message": "UnifiedTechnicalCalculator統合版スケジューラーは正常稼働中",
            }

            # 基本的な健全性チェック
            if not self.data_fetcher:
                health_status["status"] = "unhealthy"
                health_status["error"] = "DataFetcherService not initialized"

            if not self.continuous_service:
                health_status["status"] = "unhealthy"
                health_status["error"] = "ContinuousProcessingService not initialized"

            return health_status

        except Exception as e:
            return {
                "service": "ContinuousProcessingScheduler",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(),
            }
