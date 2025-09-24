#!/usr/bin/env python3
"""
日足データ修正ツール

間違って取得された日足データを修正します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_collection.utils.timezone_utils import TimezoneUtils

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DailyDataFixer:
    """日足データ修正クラス"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        self.symbol = "USDJPY=X"
    
    async def analyze_daily_data(self):
        """日足データの現状を分析"""
        logger.info("🔍 日足データの現状分析中...")
        
        async with self.connection_manager.get_connection() as conn:
            # 日足データの統計
            query = """
                SELECT 
                    MIN(timestamp) as min_time,
                    MAX(timestamp) as max_time,
                    COUNT(*) as count,
                    MIN(close) as min_price,
                    MAX(close) as max_price
                FROM price_data 
                WHERE symbol = $1 AND timeframe = $2
            """
            result = await conn.fetchrow(query, self.symbol, "1d")
            
            logger.info(f"📊 日足データ統計:")
            logger.info(f"  件数: {result['count']}件")
            logger.info(f"  期間: {result['min_time']} ～ {result['max_time']}")
            logger.info(f"  価格範囲: {result['min_price']} ～ {result['max_price']}")
            
            # 最新の10件を確認
            query2 = """
                SELECT timestamp, close, open, high, low, volume
                FROM price_data 
                WHERE symbol = $1 AND timeframe = $2
                ORDER BY timestamp DESC 
                LIMIT 10
            """
            results = await conn.fetch(query2, self.symbol, "1d")
            
            logger.info(f"📋 最新10件:")
            for i, row in enumerate(results):
                timestamp_jst = TimezoneUtils.format_jst(row['timestamp'])
                logger.info(f"  {i+1}. {timestamp_jst} - Close: {row['close']}")
            
            return result
    
    async def fix_daily_data(self):
        """日足データを修正"""
        logger.info("🔧 日足データの修正開始...")
        
        # 現在時刻
        now_utc = datetime.now(timezone.utc)
        now_jst = TimezoneUtils.format_jst(now_utc)
        logger.info(f"🕐 現在時刻: {now_jst}")
        
        # 正しい日足の期間を計算（過去1年分）
        start_date = now_utc - timedelta(days=365)
        start_date_jst = TimezoneUtils.format_jst(start_date)
        logger.info(f"📅 正しい期間: {start_date_jst} ～ {now_jst}")
        
        async with self.connection_manager.get_connection() as conn:
            # 間違ったデータを削除
            delete_query = """
                DELETE FROM price_data 
                WHERE symbol = $1 AND timeframe = $2
            """
            delete_result = await conn.execute(delete_query, self.symbol, "1d")
            logger.info(f"🗑️ 間違った日足データを削除: {delete_result}")
            
            # 正しい日足データを取得・保存
            from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
            from modules.data_collection.config.settings import TimeFrame
            
            provider = YahooFinanceProvider()
            result = await provider.get_historical_data(
                self.symbol, TimeFrame.D1, start_date, now_utc
            )
            
            if result.success and result.data:
                logger.info(f"📡 正しい日足データ取得成功: {len(result.data)}件")
                
                # データベースに保存
                saved_count = 0
                for record in result.data:
                    try:
                        insert_query = """
                            INSERT INTO price_data (
                                symbol, timeframe, timestamp, open, close, high, low, volume, created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
                            )
                        """
                        
                        await conn.execute(
                            insert_query,
                            self.symbol,
                            "1d",
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
                
                logger.info(f"💾 正しい日足データ保存完了: {saved_count}件")
                
                # 修正後の確認
                await self.analyze_daily_data()
                
                return saved_count
            else:
                logger.error(f"❌ 正しい日足データ取得失敗: {result.error_message}")
                return 0
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    fixer = DailyDataFixer()
    
    try:
        # 現状分析
        await fixer.analyze_daily_data()
        
        # 修正実行
        saved_count = await fixer.fix_daily_data()
        
        if saved_count > 0:
            logger.info("🎉 日足データの修正が完了しました！")
        else:
            logger.error("❌ 日足データの修正に失敗しました。")
            
    finally:
        await fixer.close()


if __name__ == "__main__":
    asyncio.run(main())
