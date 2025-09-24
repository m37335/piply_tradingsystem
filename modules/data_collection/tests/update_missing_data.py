#!/usr/bin/env python3
"""
欠けているデータの更新

データベースに欠けている最新データを取得して保存します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
from modules.data_collection.providers.base_provider import TimeFrame
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class MissingDataUpdater:
    """欠けているデータ更新クラス"""
    
    def __init__(self):
        self.provider = YahooFinanceProvider()
        self.db_config = DatabaseConfig()
        # 接続文字列を構築
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
    
    async def get_database_latest_timestamps(self):
        """データベースの最新タイムスタンプを取得"""
        logger.info("🔍 データベースの最新タイムスタンプを確認中...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT timeframe, MAX(timestamp) as latest_timestamp
                    FROM price_data 
                    WHERE symbol = 'USDJPY=X'
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query)
                latest_timestamps = {row['timeframe']: row['latest_timestamp'] for row in rows}
                
                logger.info("📊 データベースの最新タイムスタンプ:")
                for tf, ts in latest_timestamps.items():
                    logger.info(f"  {tf}: {ts}")
                
                return latest_timestamps
                
        except Exception as e:
            logger.error(f"データベース確認エラー: {e}")
            return {}
    
    async def fetch_missing_data(self, symbol="USDJPY=X"):
        """欠けているデータを取得"""
        logger.info(f"📊 {symbol} の欠けているデータを取得中...")
        
        # データベースの最新タイムスタンプを取得
        db_latest = await self.get_database_latest_timestamps()
        
        timeframes = [
            (TimeFrame.M5, "5分足"),
            (TimeFrame.M15, "15分足"),
            (TimeFrame.H1, "1時間足"),
            (TimeFrame.H4, "4時間足"),
            (TimeFrame.D1, "日足")
        ]
        
        results = {}
        
        for tf, tf_name in timeframes:
            logger.info(f"📈 {tf_name} 欠けているデータ取得中...")
            
            try:
                # データベースの最新タイムスタンプを取得
                db_latest_ts = db_latest.get(tf.value)
                if not db_latest_ts:
                    logger.warning(f"  ⚠️ {tf_name}: データベースにデータが見つかりません")
                    continue
                
                # データベースの最新時刻から現在時刻まで
                start_date = db_latest_ts + timedelta(minutes=1)  # 1分後から開始
                end_date = datetime.now()
                
                logger.info(f"  📅 取得期間: {start_date} ～ {end_date}")
                
                # データを取得
                result = await self.provider.get_historical_data(
                    symbol=symbol,
                    timeframe=tf,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if result.success and result.data:
                    logger.info(f"  ✅ {tf_name}: {len(result.data)}件の新しいデータを取得")
                    
                    # データベースに保存
                    saved_count = await self.save_to_database(
                        symbol=symbol,
                        timeframe=tf.value,
                        data=result.data
                    )
                    
                    results[tf.value] = {
                        "collected": len(result.data),
                        "saved": saved_count,
                        "success": True
                    }
                    
                    logger.info(f"  💾 {tf_name}: {saved_count}件保存完了")
                    
                else:
                    logger.info(f"  ℹ️ {tf_name}: 新しいデータはありません")
                    results[tf.value] = {
                        "collected": 0,
                        "saved": 0,
                        "success": True
                    }
                
                # レート制限対策
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"  ❌ {tf_name}: エラー - {e}")
                results[tf.value] = {
                    "collected": 0,
                    "saved": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def save_to_database(self, symbol: str, timeframe: str, data: list):
        """データベースに保存"""
        try:
            saved_count = 0
            
            async with self.connection_manager.get_connection() as conn:
                for record in data:
                    try:
                        # データベースに挿入
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
                        logger.warning(f"    レコード保存エラー: {e}")
                        continue
            
            return saved_count
            
        except Exception as e:
            logger.error(f"データベース保存エラー: {e}")
            return 0
    
    async def verify_updated_data(self):
        """更新されたデータの検証"""
        logger.info("🔍 更新されたデータの検証中...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # 各時間足の最新データを確認
                query = """
                    SELECT timeframe, COUNT(*) as count, 
                           MIN(timestamp) as earliest, 
                           MAX(timestamp) as latest
                    FROM price_data 
                    WHERE symbol = 'USDJPY=X'
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query)
                
                logger.info("📊 更新後のデータ統計:")
                for row in rows:
                    logger.info(f"  {row['timeframe']}: {row['count']}件")
                    logger.info(f"    期間: {row['earliest']} ～ {row['latest']}")
                
                return rows
                
        except Exception as e:
            logger.error(f"データ検証エラー: {e}")
            return []
    
    async def run_update(self):
        """データ更新実行"""
        logger.info("🚀 欠けているデータの更新開始")
        
        try:
            # 欠けているデータを取得・保存
            results = await self.fetch_missing_data()
            
            # 更新されたデータの検証
            updated_data = await self.verify_updated_data()
            
            # 結果サマリー
            logger.info("📊 更新結果サマリー:")
            logger.info("=" * 60)
            
            total_collected = 0
            total_saved = 0
            
            for tf, data in results.items():
                status = "✅ 成功" if data["success"] else "❌ 失敗"
                logger.info(f"  {tf}: {status}")
                logger.info(f"    取得: {data['collected']}件")
                logger.info(f"    保存: {data['saved']}件")
                
                if not data["success"] and "error" in data:
                    logger.info(f"    エラー: {data['error']}")
                
                total_collected += data["collected"]
                total_saved += data["saved"]
            
            logger.info(f"\n📈 合計:")
            logger.info(f"  取得: {total_collected}件")
            logger.info(f"  保存: {total_saved}件")
            
            if total_saved > 0:
                logger.info("🎉 データ更新完了！")
            else:
                logger.info("ℹ️ 新しいデータはありませんでした")
            
            return total_saved > 0
            
        except Exception as e:
            logger.error(f"❌ データ更新中にエラーが発生: {e}")
            return False
        finally:
            # 接続を閉じる
            await self.connection_manager.close()


async def main():
    """メイン関数"""
    updater = MissingDataUpdater()
    success = await updater.run_update()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
