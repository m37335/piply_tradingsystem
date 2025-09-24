#!/usr/bin/env python3
"""
システム監視ツール

イベント駆動システムの状態を監視します。
- データ収集状況
- イベント処理状況
- 分析結果
- シナリオ作成状況
"""

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemMonitor:
    """システム監視クラス"""
    
    def __init__(self):
        # データベース接続
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
    
    async def initialize(self):
        """初期化"""
        await self.connection_manager.initialize()
        logger.info("✅ システム監視ツール初期化完了")
    
    async def get_data_collection_status(self) -> dict:
        """データ収集状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 最新のデータ収集状況
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
                
                status = {
                    "timeframes": {},
                    "total_records": 0,
                    "latest_update": None
                }
                
                for row in rows:
                    status["timeframes"][row["timeframe"]] = {
                        "count": row["count"],
                        "earliest": row["earliest"],
                        "latest": row["latest"]
                    }
                    status["total_records"] += row["count"]
                    
                    if status["latest_update"] is None or row["latest"] > status["latest_update"]:
                        status["latest_update"] = row["latest"]
                
                return status
                
        except Exception as e:
            logger.error(f"❌ データ収集状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def get_event_status(self, hours: int = 24) -> dict:
        """イベント処理状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 指定時間内のイベント状況
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = """
                    SELECT event_type, 
                           COUNT(*) as total_count,
                           COUNT(CASE WHEN processed = true THEN 1 END) as processed_count,
                           COUNT(CASE WHEN processed = false THEN 1 END) as pending_count,
                           COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count,
                           MAX(created_at) as latest_event
                    FROM events 
                    WHERE created_at >= $1
                    GROUP BY event_type
                    ORDER BY event_type
                """
                
                rows = await conn.fetch(query, since_time)
                
                status = {
                    "period_hours": hours,
                    "events": {},
                    "summary": {
                        "total_events": 0,
                        "processed_events": 0,
                        "pending_events": 0,
                        "error_events": 0
                    }
                }
                
                for row in rows:
                    event_type = row["event_type"]
                    status["events"][event_type] = {
                        "total": row["total_count"],
                        "processed": row["processed_count"],
                        "pending": row["pending_count"],
                        "errors": row["error_count"],
                        "latest": row["latest_event"]
                    }
                    
                    status["summary"]["total_events"] += row["total_count"]
                    status["summary"]["processed_events"] += row["processed_count"]
                    status["summary"]["pending_events"] += row["pending_count"]
                    status["summary"]["error_events"] += row["error_count"]
                
                return status
                
        except Exception as e:
            logger.error(f"❌ イベント状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def get_analysis_results(self, hours: int = 24) -> dict:
        """分析結果を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # 分析完了イベントの詳細
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = """
                    SELECT event_data, created_at
                    FROM events 
                    WHERE event_type = 'technical_analysis_completed'
                    AND created_at >= $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """
                
                rows = await conn.fetch(query, since_time)
                
                results = {
                    "period_hours": hours,
                    "analyses": []
                }
                
                for row in rows:
                    event_data = json.loads(row["event_data"])
                    results["analyses"].append({
                        "timestamp": row["created_at"],
                        "symbol": event_data.get("symbol", "Unknown"),
                        "conditions_met": event_data.get("conditions_met", False),
                        "signal_count": len(event_data.get("signals", [])),
                        "confidence": event_data.get("confidence", 0.0),
                        "technical_summary": event_data.get("technical_summary", "")
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"❌ 分析結果取得エラー: {e}")
            return {"error": str(e)}
    
    async def get_scenario_status(self, hours: int = 24) -> dict:
        """シナリオ状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                # シナリオ作成イベントの詳細
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = """
                    SELECT event_data, created_at
                    FROM events 
                    WHERE event_type = 'scenario_created'
                    AND created_at >= $1
                    ORDER BY created_at DESC
                    LIMIT 10
                """
                
                rows = await conn.fetch(query, since_time)
                
                scenarios = {
                    "period_hours": hours,
                    "created_scenarios": []
                }
                
                for row in rows:
                    event_data = json.loads(row["event_data"])
                    scenarios["created_scenarios"].append({
                        "timestamp": row["created_at"],
                        "scenario_id": event_data.get("scenario_id", "Unknown"),
                        "strategy": event_data.get("strategy", "Unknown"),
                        "direction": event_data.get("direction", "Unknown"),
                        "status": event_data.get("status", "Unknown"),
                        "expires_at": event_data.get("expires_at", "Unknown")
                    })
                
                return scenarios
                
        except Exception as e:
            logger.error(f"❌ シナリオ状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def get_system_health(self) -> dict:
        """システムヘルスチェック"""
        try:
            # データベース接続テスト
            async with self.connection_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            
            # 最新のデータ収集時間をチェック
            data_status = await self.get_data_collection_status()
            latest_update = data_status.get("latest_update")
            
            # 最新のイベント処理時間をチェック
            event_status = await self.get_event_status(hours=1)
            
            health = {
                "database_connection": "OK",
                "latest_data_update": latest_update,
                "data_freshness_minutes": None,
                "recent_events": event_status.get("summary", {}),
                "status": "HEALTHY"
            }
            
            if latest_update:
                time_diff = datetime.now(timezone.utc) - latest_update
                health["data_freshness_minutes"] = int(time_diff.total_seconds() / 60)
                
                # データが10分以上古い場合は警告
                if health["data_freshness_minutes"] > 10:
                    health["status"] = "WARNING"
                    health["message"] = f"データが{health['data_freshness_minutes']}分古いです"
            
            return health
            
        except Exception as e:
            logger.error(f"❌ ヘルスチェックエラー: {e}")
            return {
                "database_connection": "ERROR",
                "status": "ERROR",
                "message": str(e)
            }
    
    async def print_status_report(self):
        """ステータスレポートを表示"""
        print("\n" + "="*80)
        print("🔍 システム監視レポート")
        print("="*80)
        
        # ヘルスチェック
        health = await self.get_system_health()
        print(f"\n📊 システムヘルス: {health['status']}")
        if health.get('message'):
            print(f"   {health['message']}")
        print(f"   データベース接続: {health['database_connection']}")
        if health.get('data_freshness_minutes'):
            print(f"   データ鮮度: {health['data_freshness_minutes']}分前")
        
        # データ収集状況
        data_status = await self.get_data_collection_status()
        print(f"\n📈 データ収集状況:")
        print(f"   総レコード数: {data_status.get('total_records', 0):,}件")
        for tf, info in data_status.get('timeframes', {}).items():
            print(f"   {tf}: {info['count']:,}件 (最新: {info['latest']})")
        
        # イベント処理状況
        event_status = await self.get_event_status(hours=24)
        print(f"\n📢 イベント処理状況 (24時間):")
        summary = event_status.get('summary', {})
        print(f"   総イベント: {summary.get('total_events', 0)}件")
        print(f"   処理済み: {summary.get('processed_events', 0)}件")
        print(f"   待機中: {summary.get('pending_events', 0)}件")
        print(f"   エラー: {summary.get('error_events', 0)}件")
        
        for event_type, info in event_status.get('events', {}).items():
            print(f"   {event_type}: {info['total']}件 (処理済み: {info['processed']}, 待機: {info['pending']}, エラー: {info['errors']})")
        
        # 分析結果
        analysis_results = await self.get_analysis_results(hours=24)
        print(f"\n🔍 分析結果 (24時間):")
        analyses = analysis_results.get('analyses', [])
        print(f"   分析実行回数: {len(analyses)}回")
        
        if analyses:
            print("   最新の分析結果:")
            for i, analysis in enumerate(analyses[:3]):  # 最新3件
                print(f"     {i+1}. {analysis['timestamp']} - {analysis['symbol']}")
                print(f"        条件合致: {analysis['conditions_met']}, シグナル数: {analysis['signal_count']}, 信頼度: {analysis['confidence']:.1f}%")
        
        # シナリオ状況
        scenario_status = await self.get_scenario_status(hours=24)
        print(f"\n🎯 シナリオ状況 (24時間):")
        scenarios = scenario_status.get('created_scenarios', [])
        print(f"   作成されたシナリオ: {len(scenarios)}個")
        
        if scenarios:
            print("   最新のシナリオ:")
            for i, scenario in enumerate(scenarios[:3]):  # 最新3件
                print(f"     {i+1}. {scenario['scenario_id']} - {scenario['strategy']} ({scenario['direction']})")
                print(f"         ステータス: {scenario['status']}, 有効期限: {scenario['expires_at']}")
        
        print("\n" + "="*80)
    
    async def close(self):
        """リソースを解放"""
        await self.connection_manager.close()


async def main():
    """メイン関数"""
    monitor = SystemMonitor()
    
    try:
        await monitor.initialize()
        await monitor.print_status_report()
        
    except Exception as e:
        logger.error(f"❌ 監視エラー: {e}")
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
