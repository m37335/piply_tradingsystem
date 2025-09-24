"""
価格データリポジトリ

価格データのCRUD操作を提供します。
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from ..database.connection_manager import ConnectionManager
from ...models.price_data import PriceDataModel, TimeFrame

logger = logging.getLogger(__name__)


@dataclass
class PriceDataQuery:
    """価格データクエリ条件"""
    symbol: Optional[str] = None
    timeframe: Optional[TimeFrame] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    order_by: str = "timestamp DESC"


class PriceDataRepository:
    """価格データリポジトリ"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
    
    async def create(self, price_data: PriceDataModel) -> PriceDataModel:
        """価格データを作成"""
        query = """
        INSERT INTO price_data (
            symbol, timeframe, timestamp, open, high, low, close, volume,
            source, quality_score, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
        """
        
        result = await self.connection_manager.fetchrow(
            query,
            price_data.symbol,
            price_data.timeframe.value,
            price_data.timestamp,
            price_data.open,
            price_data.high,
            price_data.low,
            price_data.close,
            price_data.volume,
            price_data.source,
            price_data.quality_score,
            price_data.created_at,
            price_data.updated_at
        )
        
        price_data.id = result['id']
        return price_data
    
    async def create_many(self, price_data_list: List[PriceDataModel]) -> List[PriceDataModel]:
        """複数の価格データを作成"""
        if not price_data_list:
            return []
        
        query = """
        INSERT INTO price_data (
            symbol, timeframe, timestamp, open, high, low, close, volume,
            source, quality_score, created_at, updated_at
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
        RETURNING id
        """
        
        values = []
        for data in price_data_list:
            values.append((
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
                data.created_at,
                data.updated_at
            ))
        
        results = await self.connection_manager.fetch(query, *values[0])
        
        # 結果を元のオブジェクトに設定
        for i, result in enumerate(results):
            price_data_list[i].id = result['id']
        
        return price_data_list
    
    async def upsert(self, price_data: PriceDataModel) -> PriceDataModel:
        """価格データをUPSERT"""
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
        RETURNING id
        """
        
        result = await self.connection_manager.fetchrow(
            query,
            price_data.symbol,
            price_data.timeframe.value,
            price_data.timestamp,
            price_data.open,
            price_data.high,
            price_data.low,
            price_data.close,
            price_data.volume,
            price_data.source,
            price_data.quality_score,
            price_data.created_at,
            price_data.updated_at
        )
        
        price_data.id = result['id']
        return price_data
    
    async def upsert_many(self, price_data_list: List[PriceDataModel]) -> int:
        """複数の価格データをUPSERT"""
        if not price_data_list:
            return 0
        
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
        
        values = []
        for data in price_data_list:
            values.append((
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
                data.created_at,
                data.updated_at
            ))
        
        result = await self.connection_manager.executemany(query, values)
        return len(price_data_list)
    
    async def find_by_id(self, id: int) -> Optional[PriceDataModel]:
        """IDで価格データを取得"""
        query = """
        SELECT id, symbol, timeframe, timestamp, open, high, low, close, volume,
               source, quality_score, created_at, updated_at
        FROM price_data
        WHERE id = $1
        """
        
        result = await self.connection_manager.fetchrow(query, id)
        if not result:
            return None
        
        return self._row_to_model(result)
    
    async def find_by_query(self, query_params: PriceDataQuery) -> List[PriceDataModel]:
        """クエリ条件で価格データを取得"""
        where_conditions = []
        params = []
        param_count = 0
        
        if query_params.symbol:
            param_count += 1
            where_conditions.append(f"symbol = ${param_count}")
            params.append(query_params.symbol)
        
        if query_params.timeframe:
            param_count += 1
            where_conditions.append(f"timeframe = ${param_count}")
            params.append(query_params.timeframe.value)
        
        if query_params.start_date:
            param_count += 1
            where_conditions.append(f"timestamp >= ${param_count}")
            params.append(query_params.start_date)
        
        if query_params.end_date:
            param_count += 1
            where_conditions.append(f"timestamp <= ${param_count}")
            params.append(query_params.end_date)
        
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
        SELECT id, symbol, timeframe, timestamp, open, high, low, close, volume,
               source, quality_score, created_at, updated_at
        FROM price_data
        WHERE {where_clause}
        ORDER BY {query_params.order_by}
        """
        
        if query_params.limit:
            param_count += 1
            query += f" LIMIT ${param_count}"
            params.append(query_params.limit)
        
        if query_params.offset:
            param_count += 1
            query += f" OFFSET ${param_count}"
            params.append(query_params.offset)
        
        results = await self.connection_manager.fetch(query, *params)
        return [self._row_to_model(row) for row in results]
    
    async def get_latest_data(self, symbol: str, timeframe: TimeFrame) -> Optional[PriceDataModel]:
        """最新の価格データを取得"""
        query = """
        SELECT id, symbol, timeframe, timestamp, open, high, low, close, volume,
               source, quality_score, created_at, updated_at
        FROM price_data
        WHERE symbol = $1 AND timeframe = $2
        ORDER BY timestamp DESC
        LIMIT 1
        """
        
        result = await self.connection_manager.fetchrow(query, symbol, timeframe.value)
        if not result:
            return None
        
        return self._row_to_model(result)
    
    async def get_data_range(self, symbol: str, timeframe: TimeFrame) -> Dict[str, Optional[datetime]]:
        """データの範囲を取得"""
        query = """
        SELECT 
            MIN(timestamp) as earliest,
            MAX(timestamp) as latest,
            COUNT(*) as count
        FROM price_data
        WHERE symbol = $1 AND timeframe = $2
        """
        
        result = await self.connection_manager.fetchrow(query, symbol, timeframe.value)
        return {
            "earliest": result['earliest'],
            "latest": result['latest'],
            "count": result['count']
        }
    
    async def get_missing_data_gaps(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, datetime]]:
        """データの欠損期間を取得"""
        # 時間軸に応じて間隔を設定
        interval_map = {
            TimeFrame.M1: "1 minute",
            TimeFrame.M5: "5 minutes",
            TimeFrame.M15: "15 minutes",
            TimeFrame.M30: "30 minutes",
            TimeFrame.H1: "1 hour",
            TimeFrame.H4: "4 hours",
            TimeFrame.D1: "1 day"
        }
        
        interval = interval_map.get(timeframe, "1 minute")
        
        query = f"""
        WITH time_series AS (
            SELECT generate_series(
                $1::timestamp,
                $2::timestamp,
                INTERVAL '{interval}'
            ) AS expected_time
        ),
        existing_data AS (
            SELECT timestamp
            FROM price_data
            WHERE symbol = $3 AND timeframe = $4
        )
        SELECT 
            ts.expected_time as gap_start,
            LEAD(ts.expected_time) OVER (ORDER BY ts.expected_time) as gap_end
        FROM time_series ts
        LEFT JOIN existing_data ed ON ts.expected_time = ed.timestamp
        WHERE ed.timestamp IS NULL
        ORDER BY ts.expected_time
        """
        
        results = await self.connection_manager.fetch(query, start_date, end_date, symbol, timeframe.value)
        return [{"start": row['gap_start'], "end": row['gap_end']} for row in results if row['gap_end']]
    
    async def delete_old_data(self, cutoff_date: datetime) -> int:
        """古いデータを削除"""
        query = """
        DELETE FROM price_data
        WHERE timestamp < $1
        """
        
        result = await self.connection_manager.execute(query, cutoff_date)
        return int(result.split()[-1])  # "DELETE n" から n を抽出
    
    async def get_statistics(self, symbol: str, timeframe: TimeFrame) -> Dict[str, Any]:
        """統計情報を取得"""
        query = """
        SELECT 
            COUNT(*) as total_records,
            MIN(timestamp) as earliest_data,
            MAX(timestamp) as latest_data,
            AVG(quality_score) as avg_quality_score,
            MIN(quality_score) as min_quality_score,
            MAX(quality_score) as max_quality_score,
            COUNT(DISTINCT DATE(timestamp)) as days_with_data
        FROM price_data
        WHERE symbol = $1 AND timeframe = $2
        """
        
        result = await self.connection_manager.fetchrow(query, symbol, timeframe.value)
        return dict(result) if result else {}
    
    def _row_to_model(self, row) -> PriceDataModel:
        """データベース行をモデルに変換"""
        return PriceDataModel(
            id=row['id'],
            symbol=row['symbol'],
            timeframe=TimeFrame(row['timeframe']),
            timestamp=row['timestamp'],
            open=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            volume=int(row['volume']),
            source=row['source'],
            quality_score=float(row['quality_score']),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
