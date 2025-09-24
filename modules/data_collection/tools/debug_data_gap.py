#!/usr/bin/env python3
"""
データギャップデバッグツール

Yahoo Finance APIから直接データを取得して、データベースとの差分を確認します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
from modules.data_collection.config.settings import TimeFrame
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_collection.utils.timezone_utils import TimezoneUtils

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataGapDebugger:
    """データギャップデバッガー"""
    
    def __init__(self):
        self.provider = YahooFinanceProvider()
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        self.symbol = "USDJPY=X"
        self.timeframes = [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4, TimeFrame.D1]
    
    async def get_db_latest_timestamp(self, timeframe: TimeFrame):
        """データベースの最新タイムスタンプを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                query = "SELECT MAX(timestamp) FROM price_data WHERE symbol = $1 AND timeframe = $2"
                result = await conn.fetchval(query, self.symbol, timeframe.value)
                return result
        except Exception as e:
            logger.error(f"データベース取得エラー ({timeframe.value}): {e}")
            return None
    
    async def get_api_latest_data(self, timeframe: TimeFrame, hours_back: int = 2):
        """APIから最新データを取得"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(hours=hours_back)
            
            result = await self.provider.get_historical_data(
                self.symbol, timeframe, start_date, end_date
            )
            
            if result.success and result.data:
                return result.data
            else:
                logger.error(f"API取得失敗 ({timeframe.value}): {result.error_message}")
                return []
        except Exception as e:
            logger.error(f"API取得エラー ({timeframe.value}): {e}")
            return []
    
    async def analyze_gap(self, timeframe: TimeFrame):
        """データギャップを分析"""
        logger.info(f"🔍 {timeframe.value} のデータギャップ分析中...")
        
        # データベースの最新タイムスタンプ
        db_latest = await self.get_db_latest_timestamp(timeframe)
        if db_latest:
            db_latest_jst = TimezoneUtils.format_jst(db_latest)
            logger.info(f"  📊 DB最新: {db_latest_jst}")
        else:
            logger.warning(f"  📊 DB最新: データなし")
            db_latest = None
        
        # APIから最新データを取得
        api_data = await self.get_api_latest_data(timeframe, hours_back=3)
        if api_data:
            api_latest = api_data[-1].timestamp
            api_latest_jst = TimezoneUtils.format_jst(api_latest)
            logger.info(f"  📡 API最新: {api_latest_jst}")
            logger.info(f"  📈 API件数: {len(api_data)}件")
            
            # ギャップ分析
            if db_latest:
                gap_minutes = int((api_latest - db_latest).total_seconds() / 60)
                logger.info(f"  ⏰ ギャップ: {gap_minutes}分")
                
                # 欠けているデータを特定
                missing_data = []
                for record in api_data:
                    if record.timestamp > db_latest:
                        missing_data.append(record)
                
                logger.info(f"  🚨 欠けているデータ: {len(missing_data)}件")
                
                if missing_data:
                    logger.info(f"  📅 欠けている期間: {TimezoneUtils.format_jst(missing_data[0].timestamp)} ～ {TimezoneUtils.format_jst(missing_data[-1].timestamp)}")
                    
                    # 最新の数件を表示
                    logger.info("  📋 欠けている最新データ:")
                    for i, record in enumerate(missing_data[-3:]):
                        timestamp_jst = TimezoneUtils.format_jst(record.timestamp)
                        logger.info(f"    {i+1}. {timestamp_jst} - Close: {record.close}")
                
                return {
                    "timeframe": timeframe.value,
                    "db_latest": db_latest,
                    "api_latest": api_latest,
                    "gap_minutes": gap_minutes,
                    "missing_count": len(missing_data),
                    "missing_data": missing_data
                }
            else:
                logger.info(f"  🚨 データベースにデータがありません")
                return {
                    "timeframe": timeframe.value,
                    "db_latest": None,
                    "api_latest": api_latest,
                    "gap_minutes": None,
                    "missing_count": len(api_data),
                    "missing_data": api_data
                }
        else:
            logger.error(f"  ❌ APIからデータを取得できませんでした")
            return None
    
    async def run_analysis(self):
        """全時間足のギャップ分析を実行"""
        logger.info("🚀 データギャップ分析開始")
        logger.info(f"🕐 現在時刻(JST): {TimezoneUtils.format_jst(TimezoneUtils.now_jst())}")
        logger.info("=" * 80)
        
        results = {}
        for tf in self.timeframes:
            result = await self.analyze_gap(tf)
            if result:
                results[tf.value] = result
            logger.info("-" * 80)
        
        # サマリー表示
        logger.info("📊 ギャップ分析サマリー:")
        logger.info("=" * 80)
        
        total_missing = 0
        for tf, result in results.items():
            if result['gap_minutes'] is not None:
                logger.info(f"⏰ {tf}: {result['gap_minutes']}分のギャップ ({result['missing_count']}件欠けている)")
                total_missing += result['missing_count']
            else:
                logger.info(f"⏰ {tf}: データベースにデータなし ({result['missing_count']}件必要)")
                total_missing += result['missing_count']
        
        logger.info(f"🚨 合計欠けているデータ: {total_missing}件")
        
        if total_missing > 0:
            logger.info("\n💡 推奨アクション:")
            logger.info("  1. 欠けているデータを手動で取得・保存")
            logger.info("  2. デーモンの動作を確認")
            logger.info("  3. API制限やエラーの確認")
        
        return results
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    debugger = DataGapDebugger()
    
    try:
        await debugger.run_analysis()
    finally:
        await debugger.close()


if __name__ == "__main__":
    asyncio.run(main())
