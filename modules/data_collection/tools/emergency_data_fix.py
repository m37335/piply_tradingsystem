#!/usr/bin/env python3
"""
緊急データ修復ツール

欠けているデータを即座に取得・保存します。
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
# from modules.data_persistence.core.database.data_saver import DataSaver
from modules.data_collection.utils.timezone_utils import TimezoneUtils

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EmergencyDataFixer:
    """緊急データ修復クラス"""
    
    def __init__(self):
        self.provider = YahooFinanceProvider()
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        # self.data_saver = DataSaver(self.connection_manager)
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
    
    async def fetch_and_save_missing_data(self, timeframe: TimeFrame):
        """欠けているデータを取得・保存"""
        logger.info(f"🔧 {timeframe.value} の欠けているデータを修復中...")
        
        # データベースの最新タイムスタンプ
        db_latest = await self.get_db_latest_timestamp(timeframe)
        if db_latest:
            db_latest_jst = TimezoneUtils.format_jst(db_latest)
            logger.info(f"  📊 DB最新: {db_latest_jst}")
        else:
            logger.warning(f"  📊 DB最新: データなし")
            db_latest = None
        
        # 現在時刻
        now_utc = datetime.now(timezone.utc)
        now_jst = TimezoneUtils.format_jst(now_utc)
        logger.info(f"  🕐 現在時刻: {now_jst}")
        
        # 取得開始時刻を決定
        if db_latest:
            start_date = db_latest + timedelta(minutes=1)  # 1分余裕を持たせる
        else:
            start_date = now_utc - timedelta(hours=3)  # 過去3時間分
        
        logger.info(f"  📅 取得期間: {TimezoneUtils.format_jst(start_date)} ～ {now_jst}")
        
        # APIからデータを取得
        try:
            result = await self.provider.get_historical_data(
                self.symbol, timeframe, start_date, now_utc
            )
            
            if result.success and result.data:
                logger.info(f"  📡 API取得成功: {len(result.data)}件")
                
                # データベースに直接保存
                saved_count = await self.save_price_data_direct(result.data, timeframe)
                logger.info(f"  💾 保存完了: {saved_count}件")
                
                # 保存後の最新タイムスタンプを確認
                new_db_latest = await self.get_db_latest_timestamp(timeframe)
                if new_db_latest:
                    new_db_latest_jst = TimezoneUtils.format_jst(new_db_latest)
                    logger.info(f"  ✅ 修復後DB最新: {new_db_latest_jst}")
                
                return {
                    "timeframe": timeframe.value,
                    "fetched": len(result.data),
                    "saved": saved_count,
                    "success": True
                }
            else:
                logger.error(f"  ❌ API取得失敗: {result.error_message}")
                return {
                    "timeframe": timeframe.value,
                    "fetched": 0,
                    "saved": 0,
                    "success": False,
                    "error": result.error_message
                }
                
        except Exception as e:
            logger.error(f"  ❌ 修復エラー: {e}")
            return {
                "timeframe": timeframe.value,
                "fetched": 0,
                "saved": 0,
                "success": False,
                "error": str(e)
            }
    
    async def run_emergency_fix(self):
        """緊急修復を実行"""
        logger.info("🚨 緊急データ修復開始")
        logger.info(f"🕐 現在時刻(JST): {TimezoneUtils.format_jst(TimezoneUtils.now_jst())}")
        logger.info("=" * 80)
        
        results = {}
        total_fetched = 0
        total_saved = 0
        success_count = 0
        
        for tf in self.timeframes:
            result = await self.fetch_and_save_missing_data(tf)
            results[tf.value] = result
            
            if result["success"]:
                success_count += 1
                total_fetched += result["fetched"]
                total_saved += result["saved"]
            
            logger.info("-" * 80)
        
        # サマリー表示
        logger.info("📊 緊急修復サマリー:")
        logger.info("=" * 80)
        
        for tf, result in results.items():
            if result["success"]:
                logger.info(f"✅ {tf}: {result['saved']}件保存成功")
            else:
                logger.info(f"❌ {tf}: 修復失敗 - {result.get('error', 'Unknown error')}")
        
        logger.info(f"\n📈 合計:")
        logger.info(f"  取得: {total_fetched}件")
        logger.info(f"  保存: {total_saved}件")
        logger.info(f"  成功率: {success_count}/{len(self.timeframes)}")
        
        if success_count == len(self.timeframes):
            logger.info("🎉 全時間足の修復が完了しました！")
        else:
            logger.error("⚠️ 一部の時間足で修復に失敗しました。")
        
        return results
    
    async def save_price_data_direct(self, data, timeframe: TimeFrame):
        """価格データを直接データベースに保存"""
        try:
            async with self.connection_manager.get_connection() as conn:
                saved_count = 0
                for record in data:
                    try:
                        query = """
                            INSERT INTO price_data (
                                symbol, timeframe, timestamp, open, close, high, low, volume, created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
                            )
                            ON CONFLICT (symbol, timeframe, timestamp) DO UPDATE SET
                                open = EXCLUDED.open,
                                close = EXCLUDED.close,
                                high = EXCLUDED.high,
                                low = EXCLUDED.low,
                                volume = EXCLUDED.volume,
                                updated_at = NOW()
                        """
                        
                        await conn.execute(
                            query,
                            self.symbol,
                            timeframe.value,
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
            logger.error(f"データ保存エラー: {e}")
            return 0
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    fixer = EmergencyDataFixer()
    
    try:
        await fixer.run_emergency_fix()
    finally:
        await fixer.close()


if __name__ == "__main__":
    asyncio.run(main())
