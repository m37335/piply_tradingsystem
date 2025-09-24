#!/usr/bin/env python3
"""
リアルタイムデータ収集監視ツール

データ収集の進捗をリアルタイムで監視します。
"""

import asyncio
import logging
import sys
import time
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


class RealtimeMonitor:
    """リアルタイム監視クラス"""
    
    def __init__(self):
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        
        self.previous_counts = {}
        self.previous_timestamps = {}
    
    async def get_current_status(self, symbol: str = "USDJPY=X"):
        """現在の状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT timeframe, COUNT(*) as count, MAX(timestamp) as latest_timestamp
                    FROM price_data 
                    WHERE symbol = $1
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query, symbol)
                
                status = {}
                for row in rows:
                    status[row['timeframe']] = {
                        "count": row['count'],
                        "latest": row['latest_timestamp']
                    }
                
                return status
                
        except Exception as e:
            logger.error(f"状況取得エラー: {e}")
            return {}
    
    async def display_status(self, status: dict, symbol: str = "USDJPY=X"):
        """状況を表示"""
        now_jst = TimezoneUtils.now_jst()
        
        # 画面をクリア
        print("\033[2J\033[H", end="")
        
        print("=" * 100)
        print(f"📊 {symbol} リアルタイムデータ収集監視")
        print(f"🕐 現在時刻(JST): {TimezoneUtils.format_jst(now_jst)}")
        print("=" * 100)
        
        timeframes = ["5m", "15m", "1h", "4h", "1d"]
        timeframe_names = {
            "5m": "5分足",
            "15m": "15分足", 
            "1h": "1時間足",
            "4h": "4時間足",
            "1d": "日足"
        }
        
        for tf in timeframes:
            if tf in status:
                data = status[tf]
                count = data["count"]
                latest = data["latest"]
                latest_jst = TimezoneUtils.format_jst(latest)
                
                # 前回との比較
                if tf in self.previous_counts:
                    prev_count = self.previous_counts[tf]
                    new_records = count - prev_count
                    if new_records > 0:
                        print(f"⏰ {timeframe_names[tf]:>6}: {count:>6}件 (+{new_records}) 📈")
                    else:
                        print(f"⏰ {timeframe_names[tf]:>6}: {count:>6}件 (変化なし)")
                else:
                    print(f"⏰ {timeframe_names[tf]:>6}: {count:>6}件")
                
                # 最新データの時刻
                age_minutes = int((now_jst - TimezoneUtils.utc_to_jst(latest)).total_seconds() / 60)
                if age_minutes <= 5:
                    print(f"     最新: {latest_jst} (🟢 {age_minutes}分前)")
                elif age_minutes <= 15:
                    print(f"     最新: {latest_jst} (🟡 {age_minutes}分前)")
                else:
                    print(f"     最新: {latest_jst} (🔴 {age_minutes}分前)")
                
                # 前回の値を保存
                self.previous_counts[tf] = count
                self.previous_timestamps[tf] = latest
            else:
                print(f"⏰ {timeframe_names[tf]:>6}: データなし")
        
        print("\n" + "=" * 100)
        print("📈 監視状況:")
        print("  🟢 最新 (5分以内)")
        print("  🟡 やや古い (6-15分)")
        print("  🔴 古い (16分以上)")
        print("\n💡 Ctrl+C で監視を停止")
        print("=" * 100)
    
    async def monitor_continuously(self, symbol: str = "USDJPY=X", interval_seconds: int = 30):
        """継続的に監視"""
        logger.info(f"🚀 リアルタイム監視開始 (間隔: {interval_seconds}秒)")
        
        try:
            while True:
                # 現在の状況を取得
                status = await self.get_current_status(symbol)
                
                # 状況を表示
                await self.display_status(status, symbol)
                
                # 指定秒数待機
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 監視を停止しました")
        except Exception as e:
            logger.error(f"❌ 監視エラー: {e}")
    
    async def monitor_with_alerts(self, symbol: str = "USDJPY=X", interval_seconds: int = 30):
        """アラート付き監視"""
        logger.info(f"🚀 アラート付きリアルタイム監視開始 (間隔: {interval_seconds}秒)")
        
        alert_thresholds = {
            "5m": 15,   # 5分足は15分以内
            "15m": 30,  # 15分足は30分以内
            "1h": 90,   # 1時間足は90分以内
            "4h": 300,  # 4時間足は5時間以内
            "1d": 1440  # 日足は24時間以内
        }
        
        try:
            while True:
                # 現在の状況を取得
                status = await self.get_current_status(symbol)
                
                # 状況を表示
                await self.display_status(status, symbol)
                
                # アラートチェック
                now_jst = TimezoneUtils.now_jst()
                alerts = []
                
                for tf, data in status.items():
                    if tf in alert_thresholds:
                        latest = data["latest"]
                        age_minutes = int((now_jst - TimezoneUtils.utc_to_jst(latest)).total_seconds() / 60)
                        threshold = alert_thresholds[tf]
                        
                        if age_minutes > threshold:
                            alerts.append(f"⚠️ {tf}: {age_minutes}分前 (閾値: {threshold}分)")
                
                if alerts:
                    print("\n🚨 アラート:")
                    for alert in alerts:
                        print(f"  {alert}")
                
                # 指定秒数待機
                await asyncio.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n\n🛑 監視を停止しました")
        except Exception as e:
            logger.error(f"❌ 監視エラー: {e}")
    
    async def quick_status_check(self, symbol: str = "USDJPY=X"):
        """クイック状況確認"""
        status = await self.get_current_status(symbol)
        await self.display_status(status, symbol)
        return status
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="リアルタイムデータ収集監視")
    parser.add_argument("--interval", type=int, default=30, help="監視間隔（秒）")
    parser.add_argument("--alerts", action="store_true", help="アラート機能を有効化")
    parser.add_argument("--quick", action="store_true", help="クイック確認のみ")
    
    args = parser.parse_args()
    
    monitor = RealtimeMonitor()
    
    try:
        if args.quick:
            # クイック確認
            await monitor.quick_status_check()
        elif args.alerts:
            # アラート付き監視
            await monitor.monitor_with_alerts(interval_seconds=args.interval)
        else:
            # 通常監視
            await monitor.monitor_continuously(interval_seconds=args.interval)
            
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
