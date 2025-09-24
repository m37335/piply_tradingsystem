#!/usr/bin/env python3
"""
JSTデータビューア

データベースのデータをJST時刻で表示します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
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


class JSTDataViewer:
    """JSTデータビューアクラス"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
    
    async def get_data_summary(self, symbol: str = "USDJPY=X"):
        """データサマリーをJSTで表示"""
        logger.info(f"📊 {symbol} のデータサマリー（JST表示）")
        
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
                
                rows = await conn.fetch(query, symbol)
                
                print("=" * 80)
                print(f"📈 {symbol} データサマリー（JST時刻）")
                print("=" * 80)
                
                for row in rows:
                    tf = row['timeframe']
                    count = row['count']
                    earliest_utc = row['earliest']
                    latest_utc = row['latest']
                    
                    # UTCをJSTに変換
                    earliest_jst = TimezoneUtils.format_jst(earliest_utc)
                    latest_jst = TimezoneUtils.format_jst(latest_utc)
                    
                    print(f"⏰ {tf:>4}足: {count:>6}件")
                    print(f"    期間: {earliest_jst} ～ {latest_jst}")
                    print()
                
                return rows
                
        except Exception as e:
            logger.error(f"データサマリー取得エラー: {e}")
            return []
    
    async def get_latest_data(self, symbol: str = "USDJPY=X", timeframe: str = "5m", limit: int = 10):
        """最新データをJSTで表示"""
        logger.info(f"📊 {symbol} {timeframe} の最新{limit}件（JST表示）")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT timestamp, open, close, high, low, volume
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = $2
                    ORDER BY timestamp DESC
                    LIMIT $3
                """
                
                rows = await conn.fetch(query, symbol, timeframe, limit)
                
                print("=" * 80)
                print(f"📈 {symbol} {timeframe} 最新{limit}件（JST時刻）")
                print("=" * 80)
                print(f"{'時刻(JST)':<20} {'始値':<10} {'終値':<10} {'高値':<10} {'安値':<10} {'出来高':<10}")
                print("-" * 80)
                
                for row in rows:
                    timestamp_utc = row['timestamp']
                    timestamp_jst = TimezoneUtils.format_jst(timestamp_utc)
                    
                    print(f"{timestamp_jst:<20} {row['open']:<10.3f} {row['close']:<10.3f} {row['high']:<10.3f} {row['low']:<10.3f} {row['volume']:<10}")
                
                return rows
                
        except Exception as e:
            logger.error(f"最新データ取得エラー: {e}")
            return []
    
    async def get_recent_data(self, symbol: str = "USDJPY=X", hours_back: int = 1):
        """過去数時間のデータをJSTで表示"""
        logger.info(f"📊 {symbol} の過去{hours_back}時間のデータ（JST表示）")
        
        try:
            # 現在時刻から指定時間前のUTC時刻を計算
            now_utc = TimezoneUtils.now_utc()
            start_utc = now_utc - timedelta(hours=hours_back)
            
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT timeframe, COUNT(*) as count,
                           MIN(timestamp) as earliest,
                           MAX(timestamp) as latest
                    FROM price_data 
                    WHERE symbol = $1 AND timestamp >= $2
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query, symbol, start_utc)
                
                print("=" * 80)
                print(f"📈 {symbol} 過去{hours_back}時間のデータ（JST時刻）")
                print("=" * 80)
                
                if not rows:
                    print("ℹ️ 指定期間のデータはありません")
                    return []
                
                for row in rows:
                    tf = row['timeframe']
                    count = row['count']
                    earliest_utc = row['earliest']
                    latest_utc = row['latest']
                    
                    # UTCをJSTに変換
                    earliest_jst = TimezoneUtils.format_jst(earliest_utc)
                    latest_jst = TimezoneUtils.format_jst(latest_utc)
                    
                    print(f"⏰ {tf:>4}足: {count:>4}件")
                    print(f"    期間: {earliest_jst} ～ {latest_jst}")
                    print()
                
                return rows
                
        except Exception as e:
            logger.error(f"過去データ取得エラー: {e}")
            return []
    
    async def get_current_status(self):
        """現在の状況をJSTで表示"""
        logger.info("📊 現在の状況（JST表示）")
        
        try:
            # タイムゾーン情報
            tz_info = TimezoneUtils.get_timezone_info()
            
            print("=" * 80)
            print("🌏 現在の状況（JST時刻）")
            print("=" * 80)
            print(f"現在時刻(JST): {TimezoneUtils.format_jst(tz_info['jst_now'])}")
            print(f"現在時刻(UTC): {TimezoneUtils.format_utc(tz_info['utc_now'])}")
            print(f"時差: {tz_info['timezone_difference']}")
            print()
            
            # データサマリー
            await self.get_data_summary()
            
            # 最新データ（5分足）
            await self.get_latest_data(timeframe="5m", limit=5)
            
        except Exception as e:
            logger.error(f"現在状況取得エラー: {e}")
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    viewer = JSTDataViewer()
    
    try:
        # 現在の状況を表示
        await viewer.get_current_status()
        
    finally:
        await viewer.close()


if __name__ == "__main__":
    asyncio.run(main())
