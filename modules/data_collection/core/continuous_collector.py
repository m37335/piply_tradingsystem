#!/usr/bin/env python3
"""
継続的データ収集システム

定期的にYahoo Finance APIからデータを取得してデータベースに保存します。
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Callable, Awaitable

from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
from modules.data_collection.providers.base_provider import TimeFrame
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

logger = logging.getLogger(__name__)


class ContinuousDataCollector:
    """継続的データ収集クラス"""
    
    def __init__(self, symbol: str = "USDJPY=X"):
        self.symbol = symbol
        self.provider = YahooFinanceProvider()
        
        # データベース接続設定
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        
        # 収集設定
        self.timeframes = [
            (TimeFrame.M5, "5分足", 5),      # 5分間隔
            (TimeFrame.M15, "15分足", 15),   # 15分間隔
            (TimeFrame.H1, "1時間足", 60),   # 1時間間隔
            (TimeFrame.H4, "4時間足", 240),  # 4時間間隔
            (TimeFrame.D1, "日足", 1440)     # 1日間隔
        ]
        
        self.is_running = False
        self.tasks: List[asyncio.Task] = []
        
        # コールバック関数
        self.data_collection_callbacks: List[Callable] = []
    
    async def initialize(self):
        """初期化"""
        logger.info("🚀 継続的データ収集システムを初期化中...")
        await self.connection_manager.initialize()
        logger.info("✅ 初期化完了")
    
    async def get_database_latest_timestamp(self, timeframe: str) -> Optional[datetime]:
        """データベースの最新タイムスタンプを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT MAX(timestamp) as latest_timestamp
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = $2
                """
                
                result = await conn.fetchval(query, self.symbol, timeframe)
                return result
                
        except Exception as e:
            logger.error(f"データベース最新タイムスタンプ取得エラー ({timeframe}): {e}")
            return None
    
    async def collect_missing_data(self, timeframe: TimeFrame, tf_name: str) -> int:
        """欠けているデータを収集"""
        try:
            # データベースの最新タイムスタンプを取得
            db_latest = await self.get_database_latest_timestamp(timeframe.value)
            
            if not db_latest:
                logger.warning(f"⚠️ {tf_name}: データベースにデータが見つかりません")
                return 0
            
            # データベースの最新時刻から現在時刻まで
            start_date = db_latest + timedelta(minutes=1)
            end_date = datetime.now(timezone.utc)
            
            # データを取得
            result = await self.provider.get_historical_data(
                symbol=self.symbol,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if result.success and result.data:
                # データベースに保存
                saved_count = await self.save_to_database(
                    symbol=self.symbol,
                    timeframe=timeframe.value,
                    data=result.data
                )
                
                if saved_count > 0:
                    logger.info(f"📈 {tf_name}: {saved_count}件の新しいデータを保存")
                
                return saved_count
            else:
                logger.debug(f"ℹ️ {tf_name}: 新しいデータはありません")
                return 0
                
        except Exception as e:
            logger.error(f"❌ {tf_name} データ収集エラー: {e}")
            return 0
    
    async def save_to_database(self, symbol: str, timeframe: str, data: list) -> int:
        """データベースに保存"""
        try:
            saved_count = 0
            
            async with self.connection_manager.get_connection() as conn:
                for record in data:
                    try:
                        insert_query = """
                            INSERT INTO price_data (
                                symbol, timeframe, timestamp, open, close, high, low, volume,
                                created_at, updated_at
                            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                            ON CONFLICT (symbol, timeframe, timestamp) 
                            DO UPDATE SET
                                open = EXCLUDED.open,
                                close = EXCLUDED.close,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                volume = EXCLUDED.volume,
                                updated_at = NOW()
                        """
                        
                        await conn.execute(
                            insert_query,
                            symbol,
                            timeframe,
                            record.timestamp,
                            record.open,
                            record.close,
                            record.high,
                            record.low,
                            record.volume
                        )
                        
                        saved_count += 1
                        
                    except Exception as e:
                        logger.warning(f"レコード保存エラー: {e}")
                        continue
            
            return saved_count
            
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
            return 0
    
    async def collect_all_timeframes(self) -> Dict[str, int]:
        """全時間足のデータを収集"""
        logger.info("📊 全時間足のデータ収集開始...")
        
        results = {}
        
        for timeframe, tf_name, interval_minutes in self.timeframes:
            try:
                saved_count = await self.collect_missing_data(timeframe, tf_name)
                results[timeframe.value] = saved_count
                
                # レート制限対策
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"❌ {tf_name} 収集エラー: {e}")
                results[timeframe.value] = 0
        
        total_saved = sum(results.values())
        logger.info(f"📈 データ収集完了: 合計{total_saved}件保存")
        
        # コールバックの実行
        if total_saved > 0:
            await self._trigger_data_collection_callbacks(results)
            # イベントの発行
            await self._publish_data_collection_event(results)
        
        return results
    
    def add_data_collection_callback(self, callback: Callable):
        """データ収集完了時のコールバックを追加"""
        self.data_collection_callbacks.append(callback)
        logger.info("✅ データ収集コールバックを追加しました")
    
    async def _trigger_data_collection_callbacks(self, results: Dict[str, int]):
        """データ収集完了コールバックを実行"""
        for callback in self.data_collection_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(results)
                else:
                    callback(results)
            except Exception as e:
                logger.error(f"❌ データ収集コールバックエラー: {e}")
    
    async def _publish_data_collection_event(self, results: Dict[str, int]):
        """データ収集完了イベントを発行"""
        try:
            # イベントデータの作成
            event_data = {
                "symbol": self.symbol,
                "timeframes": {},
                "total_new_records": sum(results.values()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # 各時間足の詳細情報を追加
            for timeframe, count in results.items():
                if count > 0:
                    event_data["timeframes"][timeframe] = {
                        "new_records": count,
                        "latest_timestamp": datetime.now(timezone.utc).isoformat()
                    }
            
            # イベントをデータベースに保存
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO events (event_type, symbol, event_data, created_at) 
                    VALUES ('data_collection_completed', $1, $2, NOW())
                """, self.symbol, json.dumps(event_data))
            
            logger.info(f"📢 データ収集完了イベントを発行: {self.symbol} - {sum(results.values())}件")
            
        except Exception as e:
            logger.error(f"❌ イベント発行エラー: {e}")
    
    async def run_continuous_collection(self, interval_minutes: int = 5):
        """継続的データ収集を実行"""
        logger.info(f"🔄 継続的データ収集開始 (間隔: {interval_minutes}分)")
        
        self.is_running = True
        
        try:
            while self.is_running:
                try:
                    # データ収集実行
                    results = await self.collect_all_timeframes()
                    
                    # 結果ログ
                    total_saved = sum(results.values())
                    if total_saved > 0:
                        logger.info(f"✅ データ収集完了: {total_saved}件保存")
                    else:
                        logger.debug("ℹ️ 新しいデータはありませんでした")
                    
                except Exception as e:
                    logger.error(f"❌ データ収集エラー: {e}")
                
                # 次の実行まで待機
                await asyncio.sleep(interval_minutes * 60)
                
        except asyncio.CancelledError:
            logger.info("🛑 継続的データ収集が停止されました")
        except Exception as e:
            logger.error(f"❌ 継続的データ収集エラー: {e}")
        finally:
            self.is_running = False
    
    async def start_background_collection(self, interval_minutes: int = 5):
        """バックグラウンドで継続的データ収集を開始"""
        if self.is_running:
            logger.warning("⚠️ 継続的データ収集は既に実行中です")
            return
        
        task = asyncio.create_task(
            self.run_continuous_collection(interval_minutes)
        )
        self.tasks.append(task)
        
        logger.info(f"🚀 バックグラウンドデータ収集開始 (間隔: {interval_minutes}分)")
        return task
    
    async def stop_collection(self):
        """データ収集を停止"""
        logger.info("🛑 データ収集を停止中...")
        
        self.is_running = False
        
        # 実行中のタスクをキャンセル
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # タスクの完了を待機
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        self.tasks.clear()
        logger.info("✅ データ収集停止完了")
    
    async def get_collection_status(self) -> Dict:
        """収集状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT timeframe, COUNT(*) as count, 
                           MIN(timestamp) as earliest, 
                           MAX(timestamp) as latest
                    FROM price_data 
                    WHERE symbol = $1
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query, self.symbol)
                
                status = {
                    "is_running": self.is_running,
                    "symbol": self.symbol,
                    "timeframes": {}
                }
                
                for row in rows:
                    status["timeframes"][row["timeframe"]] = {
                        "count": row["count"],
                        "earliest": row["earliest"],
                        "latest": row["latest"]
                    }
                
                return status
                
        except Exception as e:
            logger.error(f"収集状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """リソースを解放"""
        await self.stop_collection()
        await self.connection_manager.close()
        logger.info("🔒 リソース解放完了")


# 使用例
async def main():
    """メイン関数（テスト用）"""
    collector = ContinuousDataCollector()
    
    try:
        # 初期化
        await collector.initialize()
        
        # 一度だけデータ収集を実行
        results = await collector.collect_all_timeframes()
        
        # 状況確認
        status = await collector.get_collection_status()
        logger.info(f"📊 収集状況: {status}")
        
    finally:
        await collector.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    asyncio.run(main())
