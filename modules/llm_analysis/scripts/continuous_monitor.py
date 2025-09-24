#!/usr/bin/env python3
"""
継続的システム監視ツール

イベント駆動システムを継続的に監視し、リアルタイムで状況を表示します。
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ContinuousMonitor:
    """継続的監視クラス"""
    
    def __init__(self, interval_seconds: int = 30):
        self.interval_seconds = interval_seconds
        self.is_running = False
        
        # データベース接続
        self.db_config = DatabaseConfig()
        connection_string = f"postgresql://{self.db_config.username}:{self.db_config.password}@{self.db_config.host}:{self.db_config.port}/{self.db_config.database}"
        self.connection_manager = DatabaseConnectionManager(
            connection_string=connection_string,
            min_connections=self.db_config.min_connections,
            max_connections=self.db_config.max_connections
        )
        
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。監視を停止します...")
        asyncio.create_task(self.stop())
    
    async def initialize(self):
        """初期化"""
        await self.connection_manager.initialize()
        logger.info("✅ 継続的監視ツール初期化完了")
    
    async def start(self):
        """継続的監視を開始"""
        if self.is_running:
            logger.warning("⚠️ 監視は既に実行中です")
            return
        
        self.is_running = True
        logger.info(f"🔄 継続的監視開始 (間隔: {self.interval_seconds}秒)")
        
        try:
            while self.is_running:
                try:
                    # 画面をクリア
                    print("\033[2J\033[H", end="")
                    
                    # 現在時刻を表示（日本時間）
                    now_utc = datetime.now(timezone.utc)
                    now_jst = now_utc.astimezone(timezone(timedelta(hours=9)))
                    print(f"🕐 監視時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S JST')} ({now_utc.strftime('%H:%M:%S UTC')})")
                    print("="*80)
                    
                    # システム状況を取得・表示
                    await self._display_system_status()
                    
                    # 次の監視まで待機
                    await asyncio.sleep(self.interval_seconds)
                    
                except Exception as e:
                    logger.error(f"❌ 監視エラー: {e}")
                    await asyncio.sleep(5)  # エラー時は5秒待機
                    
        except asyncio.CancelledError:
            logger.info("🛑 継続的監視が停止されました")
        except Exception as e:
            logger.error(f"❌ 継続的監視エラー: {e}")
        finally:
            self.is_running = False
    
    async def stop(self):
        """監視を停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 継続的監視を停止中...")
        self.is_running = False
        
        try:
            await self.connection_manager.close()
            logger.info("✅ 継続的監視停止完了")
        except Exception as e:
            logger.error(f"❌ 監視停止エラー: {e}")
    
    async def _display_system_status(self):
        """システム状況を表示"""
        try:
            # データ収集状況
            data_status = await self._get_data_collection_status()
            print(f"📈 データ収集状況:")
            print(f"   総レコード数: {data_status.get('total_records', 0):,}件")
            
            for tf, info in data_status.get('timeframes', {}).items():
                latest = info['latest']
                if latest:
                    time_diff = datetime.now(timezone.utc) - latest
                    minutes_ago = int(time_diff.total_seconds() / 60)
                    latest_jst = latest.astimezone(timezone(timedelta(hours=9)))
                    status_icon = "🟢" if minutes_ago <= 10 else "🟡" if minutes_ago <= 30 else "🔴"
                    print(f"   {status_icon} {tf}: {info['count']:,}件 (最新: {latest_jst.strftime('%H:%M JST')} - {minutes_ago}分前)")
            
            # イベント処理状況（直近1時間）
            event_status = await self._get_event_status(hours=1)
            print(f"\n📢 イベント処理状況 (直近1時間):")
            summary = event_status.get('summary', {})
            print(f"   総イベント: {summary.get('total_events', 0)}件")
            print(f"   処理済み: {summary.get('processed_events', 0)}件")
            print(f"   待機中: {summary.get('pending_events', 0)}件")
            print(f"   エラー: {summary.get('error_events', 0)}件")
            
            # 最新のイベント
            recent_events = await self._get_recent_events(limit=5)
            if recent_events:
                print(f"\n🔄 最新のイベント:")
                for event in recent_events:
                    time_ago = self._get_time_ago(event['created_at'])
                    event_time_jst = event['created_at'].astimezone(timezone(timedelta(hours=9)))
                    status_icon = "✅" if event['processed'] else "⏳" if not event['error_message'] else "❌"
                    print(f"   {status_icon} {event['event_type']} - {event_time_jst.strftime('%H:%M JST')} ({event['symbol']})")
            
            # 分析結果（直近1時間）
            analysis_results = await self._get_analysis_results(hours=1)
            print(f"\n🔍 分析結果 (直近1時間):")
            analyses = analysis_results.get('analyses', [])
            print(f"   分析実行回数: {len(analyses)}回")
            
            if analyses:
                latest_analysis = analyses[0]
                analysis_time_jst = latest_analysis['timestamp'].astimezone(timezone(timedelta(hours=9)))
                print(f"   最新分析: {analysis_time_jst.strftime('%H:%M JST')}")
                print(f"   条件合致: {'✅' if latest_analysis['conditions_met'] else '❌'}")
                print(f"   シグナル数: {latest_analysis['signal_count']}個")
                print(f"   信頼度: {latest_analysis['confidence']:.1f}%")
            
            # シナリオ状況（直近1時間）
            scenario_status = await self._get_scenario_status(hours=1)
            scenarios = scenario_status.get('created_scenarios', [])
            print(f"\n🎯 シナリオ状況 (直近1時間):")
            print(f"   作成されたシナリオ: {len(scenarios)}個")
            
            if scenarios:
                latest_scenario = scenarios[0]
                scenario_time_jst = latest_scenario['timestamp'].astimezone(timezone(timedelta(hours=9)))
                print(f"   最新シナリオ: {latest_scenario['scenario_id']} - {latest_scenario['strategy']}")
                print(f"   方向: {latest_scenario['direction']}, ステータス: {latest_scenario['status']}")
                print(f"   作成時刻: {scenario_time_jst.strftime('%H:%M JST')}")
            
            # システムヘルス
            health = await self._get_system_health()
            print(f"\n💚 システムヘルス: {health['status']}")
            if health.get('message'):
                print(f"   {health['message']}")
            
            print("\n" + "="*80)
            print(f"⏰ 次回更新: {self.interval_seconds}秒後 (Ctrl+C で停止)")
            
        except Exception as e:
            print(f"❌ 状況表示エラー: {e}")
    
    async def _get_data_collection_status(self) -> dict:
        """データ収集状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
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
                    "total_records": 0
                }
                
                for row in rows:
                    status["timeframes"][row["timeframe"]] = {
                        "count": row["count"],
                        "earliest": row["earliest"],
                        "latest": row["latest"]
                    }
                    status["total_records"] += row["count"]
                
                return status
                
        except Exception as e:
            logger.error(f"❌ データ収集状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def _get_event_status(self, hours: int = 1) -> dict:
        """イベント処理状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = """
                    SELECT event_type, 
                           COUNT(*) as total_count,
                           COUNT(CASE WHEN processed = true THEN 1 END) as processed_count,
                           COUNT(CASE WHEN processed = false THEN 1 END) as pending_count,
                           COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_count
                    FROM events 
                    WHERE created_at >= $1
                    GROUP BY event_type
                    ORDER BY event_type
                """
                
                rows = await conn.fetch(query, since_time)
                
                status = {
                    "summary": {
                        "total_events": 0,
                        "processed_events": 0,
                        "pending_events": 0,
                        "error_events": 0
                    }
                }
                
                for row in rows:
                    status["summary"]["total_events"] += row["total_count"]
                    status["summary"]["processed_events"] += row["processed_count"]
                    status["summary"]["pending_events"] += row["pending_count"]
                    status["summary"]["error_events"] += row["error_count"]
                
                return status
                
        except Exception as e:
            logger.error(f"❌ イベント状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def _get_recent_events(self, limit: int = 5) -> list:
        """最新のイベントを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                query = """
                    SELECT event_type, symbol, processed, error_message, created_at
                    FROM events 
                    ORDER BY created_at DESC
                    LIMIT $1
                """
                
                rows = await conn.fetch(query, limit)
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"❌ 最新イベント取得エラー: {e}")
            return []
    
    async def _get_analysis_results(self, hours: int = 1) -> dict:
        """分析結果を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = """
                    SELECT event_data, created_at
                    FROM events 
                    WHERE event_type = 'technical_analysis_completed'
                    AND created_at >= $1
                    ORDER BY created_at DESC
                    LIMIT 5
                """
                
                rows = await conn.fetch(query, since_time)
                
                results = {
                    "analyses": []
                }
                
                for row in rows:
                    event_data = json.loads(row["event_data"])
                    results["analyses"].append({
                        "timestamp": row["created_at"],
                        "symbol": event_data.get("symbol", "Unknown"),
                        "conditions_met": event_data.get("conditions_met", False),
                        "signal_count": len(event_data.get("signals", [])),
                        "confidence": event_data.get("confidence", 0.0)
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"❌ 分析結果取得エラー: {e}")
            return {"error": str(e)}
    
    async def _get_scenario_status(self, hours: int = 1) -> dict:
        """シナリオ状況を取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                since_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = """
                    SELECT event_data, created_at
                    FROM events 
                    WHERE event_type = 'scenario_created'
                    AND created_at >= $1
                    ORDER BY created_at DESC
                    LIMIT 5
                """
                
                rows = await conn.fetch(query, since_time)
                
                scenarios = {
                    "created_scenarios": []
                }
                
                for row in rows:
                    event_data = json.loads(row["event_data"])
                    scenarios["created_scenarios"].append({
                        "timestamp": row["created_at"],
                        "scenario_id": event_data.get("scenario_id", "Unknown"),
                        "strategy": event_data.get("strategy", "Unknown"),
                        "direction": event_data.get("direction", "Unknown"),
                        "status": event_data.get("status", "Unknown")
                    })
                
                return scenarios
                
        except Exception as e:
            logger.error(f"❌ シナリオ状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def _get_system_health(self) -> dict:
        """システムヘルスチェック"""
        try:
            async with self.connection_manager.get_connection() as conn:
                await conn.fetchval("SELECT 1")
            
            data_status = await self._get_data_collection_status()
            latest_update = None
            
            for tf, info in data_status.get('timeframes', {}).items():
                if info['latest'] and (latest_update is None or info['latest'] > latest_update):
                    latest_update = info['latest']
            
            health = {
                "database_connection": "OK",
                "status": "HEALTHY"
            }
            
            if latest_update:
                time_diff = datetime.now(timezone.utc) - latest_update
                minutes_ago = int(time_diff.total_seconds() / 60)
                
                if minutes_ago > 15:
                    health["status"] = "WARNING"
                    health["message"] = f"データが{minutes_ago}分古いです"
                elif minutes_ago > 30:
                    health["status"] = "ERROR"
                    health["message"] = f"データが{minutes_ago}分古いです"
            
            return health
            
        except Exception as e:
            return {
                "database_connection": "ERROR",
                "status": "ERROR",
                "message": str(e)
            }
    
    def _get_time_ago(self, timestamp) -> str:
        """時間差を文字列で返す"""
        if not timestamp:
            return "不明"
        
        time_diff = datetime.now(timezone.utc) - timestamp
        minutes = int(time_diff.total_seconds() / 60)
        
        if minutes < 1:
            return "たった今"
        elif minutes < 60:
            return f"{minutes}分前"
        else:
            hours = int(minutes / 60)
            return f"{hours}時間前"


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="継続的システム監視ツール")
    parser.add_argument("--interval", type=int, default=30, help="監視間隔（秒）")
    
    args = parser.parse_args()
    
    monitor = ContinuousMonitor(interval_seconds=args.interval)
    
    try:
        await monitor.initialize()
        await monitor.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 キーボード割り込みを受信しました")
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")
    finally:
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
