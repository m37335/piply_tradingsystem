#!/usr/bin/env python3
"""
システムヘルスモニター

データ収集システムの健康状態を監視します。
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.providers.yahoo_finance import YahooFinanceProvider
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_collection.utils.timezone_utils import TimezoneUtils

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemHealthMonitor:
    """システムヘルスモニタークラス"""
    
    def __init__(self):
        self.provider = YahooFinanceProvider()
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
    
    async def check_api_health(self):
        """APIの健康状態をチェック"""
        logger.info("🔍 Yahoo Finance API ヘルスチェック...")
        
        try:
            # ヘルスチェック
            health = await self.provider.health_check()
            
            # 最新データ取得テスト
            result = await self.provider.get_latest_data("USDJPY=X", "5m")
            
            if health and result.success:
                logger.info("✅ API正常動作")
                return True
            else:
                logger.error(f"❌ API異常: health={health}, result={result.error_message if result else 'None'}")
                return False
                
        except Exception as e:
            logger.error(f"❌ APIチェックエラー: {e}")
            return False
    
    async def check_database_health(self):
        """データベースの健康状態をチェック"""
        logger.info("🔍 データベースヘルスチェック...")
        
        try:
            health = await self.connection_manager.health_check()
            
            if health:
                logger.info("✅ データベース正常動作")
                return True
            else:
                logger.error("❌ データベース異常")
                return False
                
        except Exception as e:
            logger.error(f"❌ データベースチェックエラー: {e}")
            return False
    
    async def check_recent_data_freshness(self, hours_back: int = 2):
        """最近のデータの鮮度をチェック"""
        logger.info(f"🔍 過去{hours_back}時間のデータ鮮度チェック...")
        
        try:
            async with self.connection_manager.get_connection() as conn:
                # 最新データの時刻を取得
                query = """
                    SELECT timeframe, MAX(timestamp) as latest_timestamp
                    FROM price_data 
                    WHERE symbol = 'USDJPY=X'
                    GROUP BY timeframe
                    ORDER BY timeframe
                """
                
                rows = await conn.fetch(query)
                
                now_utc = TimezoneUtils.now_utc()
                freshness_issues = []
                
                for row in rows:
                    timeframe = row['timeframe']
                    latest = row['latest_timestamp']
                    age_minutes = int((now_utc - latest).total_seconds() / 60)
                    
                    # 時間足別の許容遅延時間
                    max_delay = {
                        "5m": 15,    # 5分足は15分以内
                        "15m": 30,   # 15分足は30分以内
                        "1h": 90,    # 1時間足は90分以内
                        "4h": 300,   # 4時間足は5時間以内
                        "1d": 1440   # 日足は24時間以内
                    }
                    
                    if age_minutes > max_delay.get(timeframe, 60):
                        freshness_issues.append({
                            "timeframe": timeframe,
                            "latest": latest,
                            "age_minutes": age_minutes,
                            "max_delay": max_delay.get(timeframe, 60)
                        })
                
                if freshness_issues:
                    logger.warning("⚠️ データ鮮度問題:")
                    for issue in freshness_issues:
                        latest_jst = TimezoneUtils.format_jst(issue['latest'])
                        logger.warning(f"  {issue['timeframe']}: {latest_jst} ({issue['age_minutes']}分前, 許容: {issue['max_delay']}分)")
                    return False
                else:
                    logger.info("✅ データ鮮度正常")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ データ鮮度チェックエラー: {e}")
            return False
    
    async def run_comprehensive_health_check(self):
        """包括的なヘルスチェックを実行"""
        logger.info("🚀 包括的ヘルスチェック開始...")
        
        results = {
            "timestamp": TimezoneUtils.now_jst(),
            "api_health": False,
            "database_health": False,
            "data_freshness": False,
            "overall_health": False
        }
        
        try:
            # 1. APIヘルスチェック
            results["api_health"] = await self.check_api_health()
            
            # 2. データベースヘルスチェック
            results["database_health"] = await self.check_database_health()
            
            # 3. データ鮮度チェック
            results["data_freshness"] = await self.check_recent_data_freshness()
            
            # 4. 総合判定
            results["overall_health"] = all([
                results["api_health"],
                results["database_health"],
                results["data_freshness"]
            ])
            
            # 結果表示
            print("=" * 80)
            print(f"📊 システムヘルスチェック結果（{TimezoneUtils.format_jst(results['timestamp'])}）")
            print("=" * 80)
            print(f"🌐 Yahoo Finance API: {'✅ 正常' if results['api_health'] else '❌ 異常'}")
            print(f"🗄️ データベース: {'✅ 正常' if results['database_health'] else '❌ 異常'}")
            print(f"📈 データ鮮度: {'✅ 正常' if results['data_freshness'] else '❌ 異常'}")
            print(f"🎯 総合判定: {'✅ 正常' if results['overall_health'] else '❌ 異常'}")
            
            if not results["overall_health"]:
                print("\n⚠️ システムに問題が検出されました。詳細な調査が必要です。")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ ヘルスチェックエラー: {e}")
            return results
        finally:
            await self.connection_manager.close()


async def main():
    """メイン関数"""
    monitor = SystemHealthMonitor()
    
    try:
        results = await monitor.run_comprehensive_health_check()
        
        # ヘルスチェック結果に基づく推奨アクション
        if not results["overall_health"]:
            print("\n🔧 推奨アクション:")
            
            if not results["api_health"]:
                print("  1. Yahoo Finance APIの接続を確認")
                print("  2. レート制限の状況を確認")
                print("  3. ネットワーク接続を確認")
            
            if not results["database_health"]:
                print("  1. PostgreSQLの接続を確認")
                print("  2. データベースのリソース使用量を確認")
                print("  3. 接続プールの状態を確認")
            
            if not results["data_freshness"]:
                print("  1. データ収集デーモンの状態を確認")
                print("  2. 最新のデータ収集ログを確認")
                print("  3. 手動でデータ収集を実行")
        
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
