"""
データベース保存機能

収集したデータをデータベースに保存する機能を提供します。
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg

from ...providers.base_provider import PriceData
from .data_validator import DataValidator
from .quality_metrics import QualityMetrics

logger = logging.getLogger(__name__)


@dataclass
class SaveResult:
    """保存結果"""

    success: bool
    saved_count: int
    skipped_count: int
    error_message: Optional[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None


class DatabaseSaver:
    """データベース保存クラス"""

    def __init__(self, connection_string: str, batch_size: int = 1000):
        self.connection_string = connection_string
        self.batch_size = batch_size
        self.validator = DataValidator()
        self.quality_metrics = QualityMetrics()
        self._connection_pool: Optional[asyncpg.Pool] = None

    async def initialize(self) -> None:
        """初期化"""
        try:
            self._connection_pool = await asyncpg.create_pool(
                self.connection_string, min_size=5, max_size=20, command_timeout=60
            )
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    async def close(self) -> None:
        """接続を閉じる"""
        if self._connection_pool:
            await self._connection_pool.close()
            logger.info("Database connection pool closed")

    async def save_price_data(
        self, price_data: List[PriceData], upsert: bool = True
    ) -> SaveResult:
        """価格データを保存"""
        if not price_data:
            return SaveResult(success=True, saved_count=0, skipped_count=0)

        try:
            # データの妥当性チェック
            validated_data = self.validator.validate_price_data(price_data)

            if not validated_data:
                return SaveResult(
                    success=False,
                    saved_count=0,
                    skipped_count=len(price_data),
                    error_message="All data failed validation",
                )

            # バッチ処理で保存
            saved_count = 0
            skipped_count = len(price_data) - len(validated_data)

            for batch in self._create_batches(validated_data, self.batch_size):
                batch_saved = await self._save_batch(batch, upsert)
                saved_count += batch_saved

            # 品質メトリクスを計算
            quality_metrics = self.quality_metrics.calculate_metrics(validated_data)

            return SaveResult(
                success=True,
                saved_count=saved_count,
                skipped_count=skipped_count,
                quality_metrics=quality_metrics,
            )

        except Exception as e:
            logger.error(f"Error saving price data: {e}")
            return SaveResult(
                success=False,
                saved_count=0,
                skipped_count=len(price_data),
                error_message=str(e),
            )

    async def _save_batch(self, batch: List[PriceData], upsert: bool) -> int:
        """バッチを保存"""
        if not self._connection_pool:
            raise RuntimeError("Database connection pool not initialized")

        async with self._connection_pool.acquire() as conn:
            try:
                if upsert:
                    return await self._upsert_batch(conn, batch)
                else:
                    return await self._insert_batch(conn, batch)
            except Exception as e:
                logger.error(f"Error saving batch: {e}")
                raise

    async def _upsert_batch(
        self, conn: asyncpg.Connection, batch: List[PriceData]
    ) -> int:
        """バッチをUPSERT"""
        query = """
        INSERT INTO price_data (
            symbol, timeframe, timestamp, open, high, low, close, volume,
            source, quality_score, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        ON CONFLICT (symbol, timeframe, timestamp)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            source = EXCLUDED.source,
            quality_score = EXCLUDED.quality_score,
            updated_at = EXCLUDED.updated_at
        """

        now = datetime.now()
        values = []

        for data in batch:
            values.append(
                (
                    data.symbol,
                    data.timeframe.value,
                    data.timestamp,
                    data.open,
                    data.high,
                    data.low,
                    data.close,
                    data.volume,
                    data.source,
                    data.quality_score,
                    now,
                    now,
                )
            )

        result = await conn.executemany(query, values)
        return len(batch)

    async def _insert_batch(
        self, conn: asyncpg.Connection, batch: List[PriceData]
    ) -> int:
        """バッチをINSERT"""
        query = """
        INSERT INTO price_data (
            symbol, timeframe, timestamp, open, high, low, close, volume,
            source, quality_score, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        """

        now = datetime.now()
        values = []

        for data in batch:
            values.append(
                (
                    data.symbol,
                    data.timeframe.value,
                    data.timestamp,
                    data.open,
                    data.high,
                    data.low,
                    data.close,
                    data.volume,
                    data.source,
                    data.quality_score,
                    now,
                    now,
                )
            )

        result = await conn.executemany(query, values)
        return len(batch)

    def _create_batches(self, data: List[Any], batch_size: int) -> List[List[Any]]:
        """データをバッチに分割"""
        batches = []
        for i in range(0, len(data), batch_size):
            batches.append(data[i : i + batch_size])
        return batches

    async def log_collection_activity(
        self,
        symbol: str,
        timeframe: str,
        start_date: datetime,
        end_date: datetime,
        records_collected: int,
        success: bool,
        error_message: Optional[str] = None,
    ) -> None:
        """収集活動をログ"""
        if not self._connection_pool:
            return

        query = """
        INSERT INTO data_collection_log (
            symbol, timeframe, start_date, end_date, records_collected,
            success, error_message, created_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        """

        try:
            async with self._connection_pool.acquire() as conn:
                await conn.execute(
                    query,
                    symbol,
                    timeframe,
                    start_date,
                    end_date,
                    records_collected,
                    success,
                    error_message,
                    datetime.now(),
                )
        except Exception as e:
            logger.error(f"Error logging collection activity: {e}")

    async def update_quality_metrics(
        self, symbol: str, timeframe: str, metrics: Dict[str, Any]
    ) -> None:
        """品質メトリクスを更新"""
        if not self._connection_pool:
            return

        query = """
        INSERT INTO data_quality_metrics (
            symbol, timeframe, metrics, updated_at
        ) VALUES ($1, $2, $3, $4)
        ON CONFLICT (symbol, timeframe)
        DO UPDATE SET
            metrics = EXCLUDED.metrics,
            updated_at = EXCLUDED.updated_at
        """

        try:
            async with self._connection_pool.acquire() as conn:
                await conn.execute(query, symbol, timeframe, metrics, datetime.now())
        except Exception as e:
            logger.error(f"Error updating quality metrics: {e}")
