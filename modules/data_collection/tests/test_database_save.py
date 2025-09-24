#!/usr/bin/env python3
"""
Yahoo Finance API データベース保存テスト

USD/JPYの各時間足データを最大取得件数でデータベースに保存します。
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
from modules.data_persistence.core.database.database_initializer import DatabaseInitializer
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DatabaseSaveTester:
    """データベース保存テストクラス"""
    
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
        self.db_initializer = DatabaseInitializer(self.connection_manager)
    
    async def initialize_database(self):
        """データベース初期化"""
        logger.info("🗄️ データベース初期化中...")
        try:
            await self.db_initializer.initialize_database("trading_system")
            logger.info("✅ データベース初期化完了")
            return True
        except Exception as e:
            logger.error(f"❌ データベース初期化失敗: {e}")
            return False
    
    async def test_database_connection(self):
        """データベース接続テスト"""
        logger.info("🔌 データベース接続テスト中...")
        try:
            health = await self.connection_manager.health_check()
            if health:
                logger.info("✅ データベース接続成功")
                return True
            else:
                logger.error("❌ データベース接続失敗")
                return False
        except Exception as e:
            logger.error(f"❌ データベース接続エラー: {e}")
            return False
    
    async def collect_and_save_data(self, symbol="USDJPY=X"):
        """データ収集と保存"""
        logger.info(f"📊 {symbol} データ収集と保存開始...")
        
        # 各時間足の設定
        collection_plans = [
            {
                "timeframe": TimeFrame.M5,
                "name": "5分足",
                "period": timedelta(days=30),  # 1ヶ月
                "expected_records": 5965
            },
            {
                "timeframe": TimeFrame.M15,
                "name": "15分足", 
                "period": timedelta(days=30),  # 1ヶ月
                "expected_records": 1990
            },
            {
                "timeframe": TimeFrame.H1,
                "name": "1時間足",
                "period": timedelta(days=365),  # 1年
                "expected_records": 6143
            },
            {
                "timeframe": TimeFrame.H4,
                "name": "4時間足",
                "period": timedelta(days=365),  # 1年
                "expected_records": 1561
            },
            {
                "timeframe": TimeFrame.D1,
                "name": "日足",
                "period": timedelta(days=1825),  # 5年
                "expected_records": 1300
            }
        ]
        
        results = {}
        
        for plan in collection_plans:
            tf = plan["timeframe"]
            tf_name = plan["name"]
            period = plan["period"]
            expected = plan["expected_records"]
            
            logger.info(f"📈 {tf_name} データ収集中...")
            
            try:
                # データ取得
                end_date = datetime.now()
                start_date = end_date - period
                
                result = await self.provider.get_historical_data(
                    symbol=symbol,
                    timeframe=tf,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if result.success and result.data:
                    record_count = len(result.data)
                    logger.info(f"  ✅ {tf_name}: {record_count}件取得 ({expected}件期待)")
                    
                    # データベース保存
                    saved_count = await self.save_to_database(
                        symbol=symbol,
                        timeframe=tf.value,
                        data=result.data
                    )
                    
                    results[tf.value] = {
                        "collected": record_count,
                        "saved": saved_count,
                        "expected": expected,
                        "success": True
                    }
                    
                    logger.info(f"  💾 {tf_name}: {saved_count}件保存完了")
                    
                else:
                    logger.error(f"  ❌ {tf_name}: データ取得失敗 - {result.error_message if result else 'Unknown error'}")
                    results[tf.value] = {
                        "collected": 0,
                        "saved": 0,
                        "expected": expected,
                        "success": False,
                        "error": result.error_message if result else "Unknown error"
                    }
                
                # レート制限対策
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"  ❌ {tf_name}: エラー - {e}")
                results[tf.value] = {
                    "collected": 0,
                    "saved": 0,
                    "expected": expected,
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
    
    async def verify_saved_data(self):
        """保存されたデータの検証"""
        logger.info("🔍 保存されたデータの検証中...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # 各時間足の保存件数を確認
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
                
                logger.info("📊 保存されたデータ統計:")
                for row in rows:
                    logger.info(f"  {row['timeframe']}: {row['count']}件")
                    logger.info(f"    期間: {row['earliest']} ～ {row['latest']}")
                
                return rows
                
        except Exception as e:
            logger.error(f"データ検証エラー: {e}")
            return []
    
    async def run_all_tests(self):
        """全テスト実行"""
        logger.info("🚀 Yahoo Finance API データベース保存テスト開始")
        
        try:
            # データベース初期化
            if not await self.initialize_database():
                return False
            
            # データベース接続テスト
            if not await self.test_database_connection():
                return False
            
            # データ収集と保存
            results = await self.collect_and_save_data()
            
            # 保存されたデータの検証
            saved_data = await self.verify_saved_data()
            
            # 結果サマリー
            logger.info("📊 テスト結果サマリー:")
            logger.info("=" * 60)
            
            total_collected = 0
            total_saved = 0
            total_expected = 0
            
            for tf, data in results.items():
                status = "✅ 成功" if data["success"] else "❌ 失敗"
                logger.info(f"  {tf}: {status}")
                logger.info(f"    取得: {data['collected']}件 / 期待: {data['expected']}件")
                logger.info(f"    保存: {data['saved']}件")
                
                if not data["success"] and "error" in data:
                    logger.info(f"    エラー: {data['error']}")
                
                total_collected += data["collected"]
                total_saved += data["saved"]
                total_expected += data["expected"]
            
            logger.info(f"\n📈 合計:")
            logger.info(f"  取得: {total_collected}件 / 期待: {total_expected}件")
            logger.info(f"  保存: {total_saved}件")
            logger.info(f"  成功率: {(total_saved/total_expected*100):.1f}%")
            
            return total_saved > 0
            
        except Exception as e:
            logger.error(f"❌ テスト実行中にエラーが発生: {e}")
            return False
        finally:
            # 接続を閉じる
            await self.connection_manager.close()


async def main():
    """メイン関数"""
    tester = DatabaseSaveTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
