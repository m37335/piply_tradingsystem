#!/usr/bin/env python3
"""
詳細欠損分析ツール

平日の取引時間中の欠損を詳細に分析します。
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


class DetailedGapAnalyzer:
    """詳細欠損分析クラス"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
    
    async def analyze_trading_hours_gaps(self, symbol: str = "USDJPY=X", timeframe: str = "5m", days_back: int = 7):
        """取引時間中の欠損を分析"""
        logger.info(f"🔍 {symbol} {timeframe} の過去{days_back}日間の取引時間欠損分析...")
        
        # 過去N日間のデータを取得
        end_time = TimezoneUtils.now_utc()
        start_time = end_time - timedelta(days=days_back)
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # 取引時間中のデータを取得（平日 09:00-15:00 JST = 00:00-06:00 UTC）
                query = """
                    SELECT timestamp, open, close, high, low, volume
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = $2 
                    AND timestamp >= $3 AND timestamp <= $4
                    AND EXTRACT(HOUR FROM timestamp) BETWEEN 0 AND 6
                    AND EXTRACT(DOW FROM timestamp) BETWEEN 1 AND 5
                    ORDER BY timestamp
                """
                
                rows = await conn.fetch(query, symbol, timeframe, start_time, end_time)
                
                if not rows:
                    logger.warning(f"⚠️ {timeframe} 取引時間中のデータが見つかりません")
                    return []
                
                # 欠損を検出
                gaps = []
                interval_minutes = 5 if timeframe == "5m" else 15 if timeframe == "15m" else 60
                expected_interval = timedelta(minutes=interval_minutes)
                
                for i in range(len(rows) - 1):
                    current = rows[i]['timestamp']
                    next_time = rows[i + 1]['timestamp']
                    expected_next = current + expected_interval
                    
                    if next_time > expected_next:
                        gap_duration = next_time - expected_next
                        gap_count = int(gap_duration.total_seconds() / (interval_minutes * 60))
                        
                        # 取引時間内の欠損のみを記録
                        if gap_count > 0:
                            gaps.append({
                                "start": expected_next,
                                "end": next_time - expected_interval,
                                "duration_minutes": int(gap_duration.total_seconds() / 60),
                                "missing_count": gap_count,
                                "current_data": rows[i],
                                "next_data": rows[i + 1]
                            })
                
                return gaps
                
        except Exception as e:
            logger.error(f"❌ 取引時間欠損分析エラー: {e}")
            return []
    
    async def analyze_recent_gaps_detailed(self, symbol: str = "USDJPY=X", hours_back: int = 24):
        """最近の欠損を詳細分析"""
        logger.info(f"🔍 {symbol} の過去{hours_back}時間の詳細欠損分析...")
        
        end_time = TimezoneUtils.now_utc()
        start_time = end_time - timedelta(hours=hours_back)
        
        print("=" * 120)
        print(f"📊 {symbol} 過去{hours_back}時間の詳細欠損分析（JST時刻）")
        print("=" * 120)
        
        timeframes = ["5m", "15m", "1h"]
        
        for timeframe in timeframes:
            interval_minutes = 5 if timeframe == "5m" else 15 if timeframe == "15m" else 60
            name = f"{interval_minutes}分足" if timeframe != "1h" else "1時間足"
            
            try:
                async with self.connection_manager.get_connection() as conn:
                    # データを取得
                    query = """
                        SELECT timestamp, open, close, high, low, volume
                        FROM price_data 
                        WHERE symbol = $1 AND timeframe = $2 AND timestamp >= $3
                        ORDER BY timestamp
                    """
                    
                    rows = await conn.fetch(query, symbol, timeframe, start_time)
                    
                    if not rows:
                        print(f"⏰ {name}: データなし")
                        continue
                    
                    # 欠損を検出
                    gaps = []
                    expected_interval = timedelta(minutes=interval_minutes)
                    
                    for i in range(len(rows) - 1):
                        current = rows[i]['timestamp']
                        next_time = rows[i + 1]['timestamp']
                        expected_next = current + expected_interval
                        
                        if next_time > expected_next:
                            gap_duration = next_time - expected_next
                            gap_count = int(gap_duration.total_seconds() / (interval_minutes * 60))
                            
                            if gap_count > 0:
                                gaps.append({
                                    "start": expected_next,
                                    "end": next_time - expected_interval,
                                    "duration_minutes": int(gap_duration.total_seconds() / 60),
                                    "missing_count": gap_count,
                                    "before_price": rows[i]['close'],
                                    "after_price": rows[i + 1]['open']
                                })
                    
                    print(f"\n⏰ {name}: {len(rows)}件")
                    
                    if gaps:
                        print(f"  📉 欠損: {len(gaps)}箇所")
                        for j, gap in enumerate(gaps):
                            start_jst = TimezoneUtils.format_jst(gap['start'])
                            end_jst = TimezoneUtils.format_jst(gap['end'])
                            price_change = gap['after_price'] - gap['before_price']
                            
                            print(f"    {j+1}. {start_jst} ～ {end_jst}")
                            print(f"       欠損: {gap['missing_count']}件 ({gap['duration_minutes']}分)")
                            print(f"       価格変動: {gap['before_price']:.3f} → {gap['after_price']:.3f} ({price_change:+.3f})")
                    else:
                        print(f"  ✅ 欠損なし")
                    
            except Exception as e:
                logger.error(f"❌ {name} 分析エラー: {e}")
                print(f"❌ {name}: エラー - {e}")
    
    async def check_data_quality_issues(self, symbol: str = "USDJPY=X"):
        """データ品質問題をチェック"""
        logger.info(f"🔍 {symbol} のデータ品質チェック...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # 異常な価格データをチェック
                quality_query = """
                    SELECT timeframe, timestamp, open, close, high, low, volume
                    FROM price_data 
                    WHERE symbol = $1
                    AND (
                        high < low OR
                        open < 0 OR close < 0 OR high < 0 OR low < 0 OR
                        volume < 0 OR
                        ABS(close - open) > (high - low) * 1.1
                    )
                    ORDER BY timestamp DESC
                    LIMIT 20
                """
                
                quality_issues = await conn.fetch(quality_query, symbol)
                
                print("=" * 120)
                print(f"📊 {symbol} データ品質チェック")
                print("=" * 120)
                
                if quality_issues:
                    print(f"⚠️ {len(quality_issues)}件の品質問題を発見:")
                    for issue in quality_issues:
                        timestamp_jst = TimezoneUtils.format_jst(issue['timestamp'])
                        print(f"  {issue['timeframe']} {timestamp_jst}: O:{issue['open']} H:{issue['high']} L:{issue['low']} C:{issue['close']} V:{issue['volume']}")
                else:
                    print("✅ データ品質問題なし")
                
                return quality_issues
                
        except Exception as e:
            logger.error(f"❌ データ品質チェックエラー: {e}")
            return []
    
    async def analyze_collection_patterns(self, symbol: str = "USDJPY=X", hours_back: int = 48):
        """データ収集パターンを分析"""
        logger.info(f"🔍 {symbol} の過去{hours_back}時間の収集パターン分析...")
        
        end_time = TimezoneUtils.now_utc()
        start_time = end_time - timedelta(hours=hours_back)
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # 5分足の収集パターンを分析
                query = """
                    SELECT 
                        DATE_TRUNC('hour', timestamp) as hour,
                        COUNT(*) as count,
                        MIN(timestamp) as first_data,
                        MAX(timestamp) as last_data
                    FROM price_data 
                    WHERE symbol = $1 AND timeframe = '5m' AND timestamp >= $2
                    GROUP BY DATE_TRUNC('hour', timestamp)
                    ORDER BY hour
                """
                
                rows = await conn.fetch(query, symbol, start_time)
                
                print("=" * 120)
                print(f"📊 {symbol} データ収集パターン分析（過去{hours_back}時間）")
                print("=" * 120)
                
                expected_per_hour = 12  # 5分足は1時間に12件
                total_gaps = 0
                
                for row in rows:
                    hour_jst = TimezoneUtils.format_jst(row['hour'])
                    count = row['count']
                    first_jst = TimezoneUtils.format_jst(row['first_data'])
                    last_jst = TimezoneUtils.format_jst(row['last_data'])
                    
                    if count < expected_per_hour:
                        missing = expected_per_hour - count
                        total_gaps += missing
                        print(f"⚠️ {hour_jst}: {count}/12件 (欠損{missing}件)")
                    else:
                        print(f"✅ {hour_jst}: {count}/12件")
                
                print(f"\n📈 総合結果:")
                print(f"  分析期間: {TimezoneUtils.format_jst(start_time)} ～ {TimezoneUtils.format_jst(end_time)}")
                print(f"  総欠損件数: {total_gaps}件")
                print(f"  欠損率: {(total_gaps / (len(rows) * expected_per_hour) * 100):.1f}%")
                
                return rows
                
        except Exception as e:
            logger.error(f"❌ 収集パターン分析エラー: {e}")
            return []
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    analyzer = DetailedGapAnalyzer()
    
    try:
        # 1. 最近の欠損を詳細分析
        await analyzer.analyze_recent_gaps_detailed(hours_back=24)
        
        # 2. データ品質チェック
        await analyzer.check_data_quality_issues()
        
        # 3. 収集パターン分析
        await analyzer.analyze_collection_patterns(hours_back=48)
        
    finally:
        await analyzer.close()


if __name__ == "__main__":
    asyncio.run(main())
