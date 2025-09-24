#!/usr/bin/env python3
"""
最新データ取得テスト

現在時刻までの最新データを取得してデータベースに保存します。
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


class LatestDataTester:
    """最新データ取得テストクラス"""
    
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
    
    async def get_latest_data(self, symbol="USDJPY=X"):
        """最新データを取得"""
        logger.info(f"📊 {symbol} の最新データを取得中...")
        
        timeframes = [
            (TimeFrame.M5, "5分足"),
            (TimeFrame.M15, "15分足"),
            (TimeFrame.H1, "1時間足"),
            (TimeFrame.H4, "4時間足"),
            (TimeFrame.D1, "日足")
        ]
        
        results = {}
        
        for tf, tf_name in timeframes:
            logger.info(f"📈 {tf_name} 最新データ取得中...")
            
            try:
                # 最新データを取得
                result = await self.provider.get_latest_data(symbol, tf)
                
                if result.success and result.data:
                    latest_record = result.data[-1]  # 最新のレコード
                    logger.info(f"  ✅ {tf_name}: {len(result.data)}件取得")
                    logger.info(f"     最新時刻: {latest_record.timestamp}")
                    logger.info(f"     最新価格: {latest_record.close}")
                    
                    results[tf.value] = {
                        "count": len(result.data),
                        "latest_timestamp": latest_record.timestamp,
                        "latest_price": latest_record.close,
                        "success": True
                    }
                else:
                    logger.error(f"  ❌ {tf_name}: 取得失敗 - {result.error_message if result else 'Unknown error'}")
                    results[tf.value] = {
                        "count": 0,
                        "success": False,
                        "error": result.error_message if result else "Unknown error"
                    }
                
                # レート制限対策
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ {tf_name}: エラー - {e}")
                results[tf.value] = {
                    "count": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def get_recent_data(self, symbol="USDJPY=X", hours_back=2):
        """過去数時間のデータを取得"""
        logger.info(f"📊 {symbol} の過去{hours_back}時間のデータを取得中...")
        
        timeframes = [
            (TimeFrame.M5, "5分足"),
            (TimeFrame.M15, "15分足"),
            (TimeFrame.H1, "1時間足")
        ]
        
        results = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        for tf, tf_name in timeframes:
            logger.info(f"📈 {tf_name} 過去{hours_back}時間データ取得中...")
            
            try:
                result = await self.provider.get_historical_data(
                    symbol=symbol,
                    timeframe=tf,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if result.success and result.data:
                    latest_record = result.data[-1]
                    earliest_record = result.data[0]
                    logger.info(f"  ✅ {tf_name}: {len(result.data)}件取得")
                    logger.info(f"     期間: {earliest_record.timestamp} ～ {latest_record.timestamp}")
                    logger.info(f"     最新価格: {latest_record.close}")
                    
                    results[tf.value] = {
                        "count": len(result.data),
                        "earliest": earliest_record.timestamp,
                        "latest": latest_record.timestamp,
                        "latest_price": latest_record.close,
                        "success": True
                    }
                else:
                    logger.error(f"  ❌ {tf_name}: 取得失敗 - {result.error_message if result else 'Unknown error'}")
                    results[tf.value] = {
                        "count": 0,
                        "success": False,
                        "error": result.error_message if result else "Unknown error"
                    }
                
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"  ❌ {tf_name}: エラー - {e}")
                results[tf.value] = {
                    "count": 0,
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    async def check_database_latest(self):
        """データベースの最新データを確認"""
        logger.info("🔍 データベースの最新データを確認中...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT timeframe, MAX(timestamp) as latest_timestamp, 
                           COUNT(*) as total_count
                    FROM price_data 
                    WHERE symbol = 'USDJPY=X'
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query)
                
                logger.info("📊 データベースの最新データ:")
                for row in rows:
                    logger.info(f"  {row['timeframe']}: {row['total_count']}件, 最新: {row['latest_timestamp']}")
                
                return rows
                
        except Exception as e:
            logger.error(f"データベース確認エラー: {e}")
            return []
    
    async def run_all_tests(self):
        """全テスト実行"""
        logger.info("🚀 最新データ取得テスト開始")
        
        try:
            # データベースの現在の最新データを確認
            db_latest = await self.check_database_latest()
            
            # 最新データを取得
            latest_results = await self.get_latest_data()
            
            # 過去2時間のデータを取得
            recent_results = await self.get_recent_data(hours_back=2)
            
            # 結果サマリー
            logger.info("📊 テスト結果サマリー:")
            logger.info("=" * 60)
            
            logger.info("🗄️ データベースの最新データ:")
            for row in db_latest:
                logger.info(f"  {row['timeframe']}: {row['latest_timestamp']}")
            
            logger.info("\n📡 Yahoo Finance API 最新データ:")
            for tf, data in latest_results.items():
                if data["success"]:
                    logger.info(f"  {tf}: {data['latest_timestamp']} (価格: {data['latest_price']})")
                else:
                    logger.info(f"  {tf}: 取得失敗 - {data.get('error', 'Unknown error')}")
            
            logger.info("\n⏰ 過去2時間のデータ:")
            for tf, data in recent_results.items():
                if data["success"]:
                    logger.info(f"  {tf}: {data['count']}件 ({data['earliest']} ～ {data['latest']})")
                else:
                    logger.info(f"  {tf}: 取得失敗 - {data.get('error', 'Unknown error')}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ テスト実行中にエラーが発生: {e}")
            return False
        finally:
            # 接続を閉じる
            await self.connection_manager.close()


async def main():
    """メイン関数"""
    tester = LatestDataTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
