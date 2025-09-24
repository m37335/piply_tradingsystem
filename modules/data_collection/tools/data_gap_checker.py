#!/usr/bin/env python3
"""
データ欠損チェッカー

各時間足のデータ欠損を確認します。
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


class DataGapChecker:
    """データ欠損チェッカークラス"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        
        # 時間足の設定
        self.timeframe_configs = {
            "5m": {"interval_minutes": 5, "name": "5分足"},
            "15m": {"interval_minutes": 15, "name": "15分足"},
            "1h": {"interval_minutes": 60, "name": "1時間足"},
            "4h": {"interval_minutes": 240, "name": "4時間足"},
            "1d": {"interval_minutes": 1440, "name": "日足"}
        }
    
    async def check_timeframe_gaps(self, symbol: str = "USDJPY=X", timeframe: str = "5m"):
        """指定時間足の欠損をチェック"""
        config = self.timeframe_configs[timeframe]
        interval_minutes = config["interval_minutes"]
        name = config["name"]
        
        logger.info(f"🔍 {name} の欠損チェック中...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # データの範囲を取得
                range_query = """
                    SELECT MIN(timestamp) as start_time, MAX(timestamp) as end_time, COUNT(*) as total_count
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = $2
                """
                
                range_result = await conn.fetchrow(range_query, symbol, timeframe)
                
                if not range_result or not range_result['start_time']:
                    logger.warning(f"⚠️ {name}: データが見つかりません")
                    return {"gaps": [], "total_gaps": 0, "total_count": 0}
                
                start_time = range_result['start_time']
                end_time = range_result['end_time']
                total_count = range_result['total_count']
                
                # 期待されるデータ数を計算
                expected_count = int((end_time - start_time).total_seconds() / (interval_minutes * 60)) + 1
                
                logger.info(f"📊 {name} データ範囲:")
                logger.info(f"  開始: {TimezoneUtils.format_jst(start_time)}")
                logger.info(f"  終了: {TimezoneUtils.format_jst(end_time)}")
                logger.info(f"  実際の件数: {total_count}件")
                logger.info(f"  期待件数: {expected_count}件")
                
                # 欠損を検出
                gaps = await self._detect_gaps(conn, symbol, timeframe, start_time, end_time, interval_minutes)
                
                return {
                    "timeframe": timeframe,
                    "name": name,
                    "start_time": start_time,
                    "end_time": end_time,
                    "actual_count": total_count,
                    "expected_count": expected_count,
                    "gaps": gaps,
                    "total_gaps": len(gaps)
                }
                
        except Exception as e:
            logger.error(f"❌ {name} 欠損チェックエラー: {e}")
            return {"gaps": [], "total_gaps": 0, "error": str(e)}
    
    async def _detect_gaps(self, conn, symbol: str, timeframe: str, start_time: datetime, end_time: datetime, interval_minutes: int):
        """欠損を検出"""
        gaps = []
        
        # データを時系列で取得
        data_query = """
            SELECT timestamp
            FROM price_data 
            WHERE symbol = $1 AND timeframe = $2
            ORDER BY timestamp
        """
        
        rows = await conn.fetch(data_query, symbol, timeframe)
        timestamps = [row['timestamp'] for row in rows]
        
        if not timestamps:
            return gaps
        
        # 連続性をチェック
        current_time = start_time
        expected_interval = timedelta(minutes=interval_minutes)
        
        for i, timestamp in enumerate(timestamps):
            # 期待される時刻と実際の時刻を比較
            if current_time != timestamp:
                # 欠損を発見
                gap_start = current_time
                gap_end = timestamp - expected_interval
                
                if gap_start <= gap_end:
                    gap_duration = gap_end - gap_start + expected_interval
                    gap_count = int(gap_duration.total_seconds() / (interval_minutes * 60))
                    
                    gaps.append({
                        "start": gap_start,
                        "end": gap_end,
                        "duration_minutes": int(gap_duration.total_seconds() / 60),
                        "missing_count": gap_count
                    })
            
            current_time = timestamp + expected_interval
        
        return gaps
    
    async def check_all_timeframes(self, symbol: str = "USDJPY=X"):
        """全時間足の欠損をチェック"""
        logger.info(f"🔍 {symbol} の全時間足欠損チェック開始...")
        
        results = {}
        
        for timeframe in self.timeframe_configs.keys():
            result = await self.check_timeframe_gaps(symbol, timeframe)
            results[timeframe] = result
            
            # レート制限対策
            await asyncio.sleep(0.5)
        
        return results
    
    async def print_gap_report(self, symbol: str = "USDJPY=X"):
        """欠損レポートを出力"""
        results = await self.check_all_timeframes(symbol)
        
        print("=" * 100)
        print(f"📊 {symbol} データ欠損レポート（JST時刻）")
        print("=" * 100)
        
        total_gaps = 0
        
        for timeframe, result in results.items():
            if "error" in result:
                print(f"❌ {result['name']}: エラー - {result['error']}")
                continue
            
            name = result['name']
            actual_count = result['actual_count']
            expected_count = result['expected_count']
            gaps = result['gaps']
            gap_count = result['total_gaps']
            
            print(f"\n⏰ {name}")
            print(f"  データ期間: {TimezoneUtils.format_jst(result['start_time'])} ～ {TimezoneUtils.format_jst(result['end_time'])}")
            print(f"  実際の件数: {actual_count:,}件")
            print(f"  期待件数: {expected_count:,}件")
            print(f"  欠損数: {gap_count}箇所")
            
            if gap_count > 0:
                print(f"  📉 欠損詳細:")
                for i, gap in enumerate(gaps[:5]):  # 最大5件まで表示
                    start_jst = TimezoneUtils.format_jst(gap['start'])
                    end_jst = TimezoneUtils.format_jst(gap['end'])
                    print(f"    {i+1}. {start_jst} ～ {end_jst} ({gap['duration_minutes']}分, {gap['missing_count']}件欠損)")
                
                if gap_count > 5:
                    print(f"    ... 他{gap_count - 5}件の欠損")
            else:
                print(f"  ✅ 欠損なし")
            
            total_gaps += gap_count
        
        print(f"\n📈 総合結果:")
        print(f"  総欠損箇所数: {total_gaps}")
        
        if total_gaps == 0:
            print(f"  🎉 全時間足で欠損なし！")
        else:
            print(f"  ⚠️ {total_gaps}箇所の欠損が検出されました")
        
        return results
    
    async def check_recent_gaps(self, symbol: str = "USDJPY=X", hours_back: int = 24):
        """最近の欠損をチェック"""
        logger.info(f"🔍 {symbol} の過去{hours_back}時間の欠損チェック...")
        
        # 現在時刻から指定時間前のUTC時刻を計算
        now_utc = TimezoneUtils.now_utc()
        start_utc = now_utc - timedelta(hours=hours_back)
        
        print("=" * 100)
        print(f"📊 {symbol} 過去{hours_back}時間の欠損チェック（JST時刻）")
        print("=" * 100)
        
        for timeframe, config in self.timeframe_configs.items():
            name = config["name"]
            interval_minutes = config["interval_minutes"]
            
            try:
                async with self.connection_manager.get_connection() as conn:
                    # 指定期間のデータを取得
                    query = """
                        SELECT timestamp
                        FROM price_data 
                        WHERE symbol = $1 AND timeframe = $2 AND timestamp >= $3
                        ORDER BY timestamp
                    """
                    
                    rows = await conn.fetch(query, symbol, timeframe, start_utc)
                    timestamps = [row['timestamp'] for row in rows]
                    
                    if not timestamps:
                        print(f"⏰ {name}: データなし")
                        continue
                    
                    # 欠損を検出
                    gaps = []
                    expected_interval = timedelta(minutes=interval_minutes)
                    
                    for i in range(len(timestamps) - 1):
                        current = timestamps[i]
                        next_time = timestamps[i + 1]
                        expected_next = current + expected_interval
                        
                        if next_time > expected_next:
                            gap_duration = next_time - expected_next
                            gap_count = int(gap_duration.total_seconds() / (interval_minutes * 60))
                            
                            gaps.append({
                                "start": expected_next,
                                "end": next_time - expected_interval,
                                "duration_minutes": int(gap_duration.total_seconds() / 60),
                                "missing_count": gap_count
                            })
                    
                    print(f"\n⏰ {name}: {len(timestamps)}件")
                    if gaps:
                        print(f"  📉 欠損: {len(gaps)}箇所")
                        for gap in gaps[:3]:  # 最大3件まで表示
                            start_jst = TimezoneUtils.format_jst(gap['start'])
                            end_jst = TimezoneUtils.format_jst(gap['end'])
                            print(f"    {start_jst} ～ {end_jst} ({gap['missing_count']}件欠損)")
                    else:
                        print(f"  ✅ 欠損なし")
                    
            except Exception as e:
                logger.error(f"❌ {name} チェックエラー: {e}")
                print(f"❌ {name}: エラー - {e}")
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    checker = DataGapChecker()
    
    try:
        # 全時間足の欠損チェック
        await checker.print_gap_report()
        
        print("\n" + "=" * 100)
        
        # 過去24時間の欠損チェック
        await checker.check_recent_gaps(hours_back=24)
        
    finally:
        await checker.close()


if __name__ == "__main__":
    asyncio.run(main())
