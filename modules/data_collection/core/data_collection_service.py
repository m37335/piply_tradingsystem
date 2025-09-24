"""
データ収集サービス

データ収集の統合サービスを提供します。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time

from ..config.settings import DataCollectionSettings, TimeFrame, DataCollectionMode
from ..providers.yahoo_finance import YahooFinanceProvider
from ..core.intelligent_collector.intelligent_collector import IntelligentDataCollector
from ..core.database_saver.database_saver import DatabaseSaver
from ...data_persistence.core.database.connection_manager import DatabaseConnectionManager

logger = logging.getLogger(__name__)


class DataCollectionService:
    """データ収集サービス"""
    
    def __init__(self, settings: DataCollectionSettings):
        self.settings = settings
        self.provider = YahooFinanceProvider(settings.yahoo_finance)
        self.collector = IntelligentDataCollector(self.provider, settings.yahoo_finance)
        self.database_manager = DatabaseConnectionManager(
            connection_string=settings.database.connection_string,
            min_connections=settings.database.min_connections,
            max_connections=settings.database.max_connections
        )
        self.database_saver = DatabaseSaver(self.database_manager)
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """サービスを開始"""
        if self._running:
            logger.warning("Data collection service is already running")
            return
        
        try:
            # データベース接続を初期化
            await self.database_manager.initialize()
            
            # サービスを開始
            self._running = True
            
            if self.settings.collection.mode == DataCollectionMode.CONTINUOUS:
                # 継続的収集モード
                await self._start_continuous_collection()
            elif self.settings.collection.mode == DataCollectionMode.BACKFILL:
                # バックフィルモード
                await self._start_backfill_collection()
            elif self.settings.collection.mode == DataCollectionMode.MANUAL:
                # 手動モード（何もしない）
                logger.info("Manual mode - service started but no automatic collection")
            
            logger.info("Data collection service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start data collection service: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """サービスを停止"""
        if not self._running:
            return
        
        self._running = False
        
        # 実行中のタスクをキャンセル
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # タスクの完了を待機
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # データベース接続を閉じる
        await self.database_manager.close()
        
        logger.info("Data collection service stopped")
    
    async def _start_continuous_collection(self) -> None:
        """継続的収集を開始"""
        logger.info("Starting continuous data collection")
        
        # 各シンボルとタイムフレームの組み合わせでタスクを作成
        for symbol in self.settings.collection.symbols:
            for timeframe in self.settings.collection.timeframes:
                task = asyncio.create_task(
                    self._continuous_collection_worker(symbol, timeframe)
                )
                self._tasks.append(task)
        
        logger.info(f"Started {len(self._tasks)} continuous collection tasks")
    
    async def _start_backfill_collection(self) -> None:
        """バックフィル収集を開始"""
        logger.info("Starting backfill data collection")
        
        # 各シンボルとタイムフレームの組み合わせでバックフィルを実行
        for symbol in self.settings.collection.symbols:
            for timeframe in self.settings.collection.timeframes:
                try:
                    await self._backfill_symbol_timeframe(symbol, timeframe)
                except Exception as e:
                    logger.error(f"Backfill failed for {symbol} {timeframe.value}: {e}")
        
        logger.info("Backfill data collection completed")
    
    async def _continuous_collection_worker(self, symbol: str, timeframe: TimeFrame) -> None:
        """継続的収集ワーカー"""
        logger.info(f"Starting continuous collection for {symbol} {timeframe.value}")
        
        while self._running:
            try:
                # 最新データを収集
                await self._collect_latest_data(symbol, timeframe)
                
                # 次の収集まで待機
                await asyncio.sleep(self.settings.collection.collection_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info(f"Continuous collection cancelled for {symbol} {timeframe.value}")
                break
            except Exception as e:
                logger.error(f"Continuous collection error for {symbol} {timeframe.value}: {e}")
                # エラー時は少し長めに待機
                await asyncio.sleep(self.settings.collection.collection_interval_seconds * 2)
    
    async def _backfill_symbol_timeframe(self, symbol: str, timeframe: TimeFrame) -> None:
        """シンボルとタイムフレームのバックフィル"""
        logger.info(f"Starting backfill for {symbol} {timeframe.value}")
        
        try:
            # 既存データの最新日時を取得
            latest_timestamp = await self._get_latest_timestamp(symbol, timeframe)
            
            if latest_timestamp:
                start_date = latest_timestamp + timedelta(minutes=1)
                logger.info(f"Resuming backfill from {start_date} for {symbol} {timeframe.value}")
            else:
                # データがない場合は1年前から開始
                start_date = datetime.now() - timedelta(days=365)
                logger.info(f"Starting fresh backfill from {start_date} for {symbol} {timeframe.value}")
            
            # バックフィルを実行
            end_date = datetime.now()
            await self._collect_historical_data(symbol, timeframe, start_date, end_date)
            
        except Exception as e:
            logger.error(f"Backfill failed for {symbol} {timeframe.value}: {e}")
            raise
    
    async def _collect_latest_data(self, symbol: str, timeframe: TimeFrame) -> None:
        """最新データを収集"""
        try:
            # 最新の数分間のデータを収集
            end_date = datetime.now()
            start_date = end_date - timedelta(minutes=10)  # 最新10分間
            
            # データを収集
            price_data = await self.collector.collect_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if price_data:
                # データベースに保存
                save_result = await self.database_saver.save_price_data(price_data)
                logger.info(f"Collected {len(price_data)} records for {symbol} {timeframe.value}")
                
                # データ品質チェック
                if self.settings.enable_quality_checks:
                    await self._check_data_quality(symbol, timeframe, price_data)
            else:
                logger.warning(f"No new data collected for {symbol} {timeframe.value}")
                
        except Exception as e:
            logger.error(f"Failed to collect latest data for {symbol} {timeframe.value}: {e}")
            raise
    
    async def _collect_historical_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_date: datetime,
        end_date: datetime
    ) -> None:
        """履歴データを収集"""
        logger.info(f"Collecting historical data for {symbol} {timeframe.value} from {start_date} to {end_date}")
        
        current_start = start_date
        batch_size = timedelta(days=30)  # 30日ずつ処理
        
        while current_start < end_date and self._running:
            current_end = min(current_start + batch_size, end_date)
            
            try:
                # データを収集
                price_data = await self.collector.collect_data(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=current_start,
                    end_date=current_end
                )
                
                if price_data:
                    # データベースに保存
                    save_result = await self.database_saver.save_price_data(price_data)
                    logger.info(f"Saved {len(price_data)} records for {symbol} {timeframe.value} ({current_start} - {current_end})")
                    
                    # データ品質チェック
                    if self.settings.enable_quality_checks:
                        await self._check_data_quality(symbol, timeframe, price_data)
                
                # 次のバッチに進む
                current_start = current_end + timedelta(minutes=1)
                
                # レート制限のため少し待機
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Failed to collect historical data for {symbol} {timeframe.value} ({current_start} - {current_end}): {e}")
                # エラー時は次のバッチに進む
                current_start = current_end + timedelta(minutes=1)
                await asyncio.sleep(5.0)  # エラー時は長めに待機
    
    async def _get_latest_timestamp(self, symbol: str, timeframe: TimeFrame) -> Optional[datetime]:
        """最新のタイムスタンプを取得"""
        try:
            query = """
                SELECT MAX(timestamp) as latest_timestamp
                FROM price_data
                WHERE symbol = $1 AND timeframe = $2
            """
            
            result = await self.database_manager.execute_query(query, symbol, timeframe.value)
            
            if result and result[0]["latest_timestamp"]:
                return result[0]["latest_timestamp"]
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get latest timestamp for {symbol} {timeframe.value}: {e}")
            return None
    
    async def _check_data_quality(self, symbol: str, timeframe: TimeFrame, price_data: List[Dict[str, Any]]) -> None:
        """データ品質をチェック"""
        try:
            if not price_data:
                return
            
            # 基本的な品質チェック
            total_records = len(price_data)
            valid_records = 0
            missing_records = 0
            duplicate_records = 0
            
            seen_timestamps = set()
            
            for record in price_data:
                # 必須フィールドのチェック
                if all(record.get(field) is not None for field in ["open", "high", "low", "close", "volume"]):
                    valid_records += 1
                else:
                    missing_records += 1
                
                # 重複チェック
                timestamp = record.get("timestamp")
                if timestamp in seen_timestamps:
                    duplicate_records += 1
                else:
                    seen_timestamps.add(timestamp)
            
            # 品質スコアを計算
            quality_score = valid_records / total_records if total_records > 0 else 0.0
            
            # 品質が閾値以下の場合は警告
            if quality_score < self.settings.quality_threshold:
                logger.warning(
                    f"Data quality below threshold for {symbol} {timeframe.value}: "
                    f"score={quality_score:.2f}, valid={valid_records}/{total_records}, "
                    f"missing={missing_records}, duplicates={duplicate_records}"
                )
            else:
                logger.debug(
                    f"Data quality good for {symbol} {timeframe.value}: "
                    f"score={quality_score:.2f}, valid={valid_records}/{total_records}"
                )
                
        except Exception as e:
            logger.error(f"Failed to check data quality for {symbol} {timeframe.value}: {e}")
    
    async def collect_manual(self, symbol: str, timeframe: TimeFrame, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """手動データ収集"""
        try:
            logger.info(f"Manual collection for {symbol} {timeframe.value} from {start_date} to {end_date}")
            
            # データを収集
            price_data = await self.collector.collect_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if price_data:
                # データベースに保存
                save_result = await self.database_saver.save_price_data(price_data)
                
                return {
                    "success": True,
                    "records_collected": len(price_data),
                    "records_saved": save_result.records_saved,
                    "records_updated": save_result.records_updated,
                    "start_date": start_date,
                    "end_date": end_date
                }
            else:
                return {
                    "success": False,
                    "records_collected": 0,
                    "error": "No data collected"
                }
                
        except Exception as e:
            logger.error(f"Manual collection failed for {symbol} {timeframe.value}: {e}")
            return {
                "success": False,
                "records_collected": 0,
                "error": str(e)
            }
    
    async def get_collection_status(self) -> Dict[str, Any]:
        """収集状況を取得"""
        try:
            # データベースのヘルスチェック
            db_health = await self.database_manager.health_check()
            
            # 各シンボルの最新データ状況
            symbol_status = {}
            for symbol in self.settings.collection.symbols:
                symbol_status[symbol] = {}
                for timeframe in self.settings.collection.timeframes:
                    latest_timestamp = await self._get_latest_timestamp(symbol, timeframe)
                    symbol_status[symbol][timeframe.value] = {
                        "latest_timestamp": latest_timestamp.isoformat() if latest_timestamp else None,
                        "data_age_minutes": (
                            (datetime.now() - latest_timestamp).total_seconds() / 60
                            if latest_timestamp else None
                        )
                    }
            
            return {
                "service_running": self._running,
                "collection_mode": self.settings.collection.mode.value,
                "active_tasks": len([t for t in self._tasks if not t.done()]),
                "database_health": db_health,
                "symbol_status": symbol_status,
                "settings": self.settings.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection status: {e}")
            return {
                "service_running": self._running,
                "error": str(e)
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # データベースのヘルスチェック
            db_health = await self.database_manager.health_check()
            
            # プロバイダーのヘルスチェック
            provider_health = await self.provider.health_check()
            
            return {
                "status": "healthy" if db_health["status"] == "healthy" and provider_health else "unhealthy",
                "database": db_health,
                "provider": provider_health,
                "service_running": self._running,
                "active_tasks": len([t for t in self._tasks if not t.done()])
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
