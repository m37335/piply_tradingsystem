"""
UnifiedTechnicalIndicatorService
UnifiedTechnicalCalculator のサービス層ラッパー

責任:
- UnifiedTechnicalCalculator の初期化と管理
- データベースセッションの管理
- エラーハンドリングとログ記録
- 既存システムとの互換性確保
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from scripts.cron.unified_technical_calculator import UnifiedTechnicalCalculator
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)

logger = logging.getLogger(__name__)


class UnifiedTechnicalIndicatorService:
    """
    UnifiedTechnicalCalculator のサービス層ラッパー
    """

    def __init__(self, session: AsyncSession, currency_pair: str = "USD/JPY"):
        self.session = session
        self.currency_pair = currency_pair
        self.calculator: Optional[UnifiedTechnicalCalculator] = None
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)

        # 初期化状態
        self.is_initialized = False
        self.initialization_error = None

    async def initialize(self) -> bool:
        """
        サービスを初期化

        Returns:
            bool: 初期化成功時True、失敗時False
        """
        try:
            logger.info("UnifiedTechnicalIndicatorService 初期化開始")

            # UnifiedTechnicalCalculator の初期化
            self.calculator = UnifiedTechnicalCalculator(self.currency_pair)
            await self.calculator.initialize()

            self.is_initialized = True
            logger.info("UnifiedTechnicalIndicatorService 初期化完了")
            return True

        except Exception as e:
            self.initialization_error = str(e)
            logger.error(f"UnifiedTechnicalIndicatorService 初期化エラー: {e}")
            return False

    async def calculate_and_save_all_indicators(self, timeframe: str) -> Dict[str, int]:
        """
        全テクニカル指標を計算して保存

        Args:
            timeframe: 時間足

        Returns:
            Dict[str, int]: 各指標の保存件数
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_timeframe_indicators(timeframe)

        except Exception as e:
            logger.error(f"calculate_and_save_all_indicators エラー: {e}")
            return {"error": str(e)}

    async def calculate_rsi(self, data, timeframe: str) -> Dict[str, Any]:
        """
        RSI計算（互換性メソッド）
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_rsi(data, timeframe)

        except Exception as e:
            logger.error(f"RSI計算エラー: {e}")
            return {"error": str(e)}

    async def calculate_macd(self, data, timeframe: str) -> Dict[str, Any]:
        """
        MACD計算（互換性メソッド）
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_macd(data, timeframe)

        except Exception as e:
            logger.error(f"MACD計算エラー: {e}")
            return {"error": str(e)}

    async def calculate_bollinger_bands(self, data, timeframe: str) -> Dict[str, Any]:
        """
        ボリンジャーバンド計算（互換性メソッド）
        """
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_bollinger_bands(data, timeframe)

        except Exception as e:
            logger.error(f"ボリンジャーバンド計算エラー: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict[str, Any]:
        """
        健全性チェック

        Returns:
            Dict[str, Any]: 健全性チェック結果
        """
        try:
            if not self.is_initialized:
                return {
                    "status": "uninitialized",
                    "error": "サービスが初期化されていません",
                    "timestamp": datetime.now()
                }

            # 基本的な健全性チェック
            health_status = {
                "status": "healthy",
                "timestamp": datetime.now(),
                "service_type": "UnifiedTechnicalIndicatorService",
                "currency_pair": self.currency_pair,
                "calculator_initialized": self.calculator is not None,
                "session_active": self.session is not None
            }

            # 計算機の健全性チェック
            if self.calculator:
                calculator_health = await self.calculator.health_check()
                health_status["calculator_health"] = calculator_health

            return health_status

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now()
            }

    async def cleanup(self):
        """
        リソースのクリーンアップ
        """
        try:
            if self.calculator:
                await self.calculator.cleanup()
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
