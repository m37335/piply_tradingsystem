#!/usr/bin/env python3
"""
スタンドアロンデータ収集デーモン

データ収集のみに特化し、分析システムとは完全に分離されたデーモンです。
イベントはデータベースに発行し、分析システムが独立して監視します。
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_collection.core.continuous_collector import ContinuousDataCollector
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class StandaloneDataCollectionDaemon:
    """スタンドアロンデータ収集デーモン"""
    
    def __init__(self, symbol: str = "USDJPY=X", interval_minutes: int = 5):
        self.symbol = symbol
        self.interval_minutes = interval_minutes
        self.collector = ContinuousDataCollector(symbol)
        self.connection_manager = None
        self.is_running = False
        self.collection_task = None
        
        # シグナルハンドラーの設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。データ収集デーモンを停止します...")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """デーモンを開始"""
        logger.info("🚀 スタンドアロンデータ収集デーモンを開始します...")
        logger.info(f"📊 シンボル: {self.symbol}")
        logger.info(f"⏰ 収集間隔: {self.interval_minutes}分")
        
        try:
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=2,
                max_connections=5
            )
            await self.connection_manager.initialize()
            
            # データ収集器の初期化
            await self.collector.initialize()
            
            # データ収集完了時のコールバックを設定
            self.collector.add_data_collection_callback(self._on_data_collection_complete)
            
            # バックグラウンドで継続的データ収集を開始
            self.collection_task = await self.collector.start_background_collection(
                self.interval_minutes
            )
            
            self.is_running = True
            logger.info("✅ スタンドアロンデータ収集デーモンが開始されました")
            logger.info("📋 デーモン機能:")
            logger.info("  - データ収集: 5分間隔で継続実行")
            logger.info("  - イベント発行: データベースにイベントを発行")
            logger.info("  - 分析分離: 分析システムとは完全に独立")
            
            # タスクの完了を待機
            await self.collection_task
            
        except Exception as e:
            logger.error(f"❌ データ収集デーモン開始エラー: {e}")
            await self.stop()
            raise
    
    async def _on_data_collection_complete(self, results: Dict[str, int]):
        """データ収集完了時のコールバック"""
        try:
            total_new_data = sum(results.values())
            logger.info(f"🔄 データ収集完了: {total_new_data}件の新しいデータ")
            
            # イベントをデータベースに発行
            await self._publish_data_collection_event(results)
            
        except Exception as e:
            logger.error(f"❌ データ収集完了コールバックエラー: {e}")
    
    async def _publish_data_collection_event(self, results: Dict[str, int]):
        """データ収集完了イベントを発行"""
        try:
            import json
            
            # イベントデータの作成
            event_data = {
                "symbol": self.symbol,
                "timeframes": {},
                "total_new_records": sum(results.values()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "daemon_type": "standalone"
            }
            
            # 各時間足の詳細情報を追加
            for timeframe, count in results.items():
                if count > 0:
                    event_data["timeframes"][timeframe] = {
                        "new_records": count,
                        "latest_timestamp": datetime.now(timezone.utc).isoformat()
                    }
            
            # イベントをデータベースに保存
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO events (event_type, symbol, event_data, created_at) 
                    VALUES ('data_collection_completed', $1, $2, NOW())
                """, self.symbol, json.dumps(event_data))
            
            logger.info(f"📢 データ収集完了イベントを発行: {self.symbol} - {sum(results.values())}件")
            
        except Exception as e:
            logger.error(f"❌ イベント発行エラー: {e}")
    
    async def stop(self):
        """デーモンを停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 スタンドアロンデータ収集デーモンを停止中...")
        self.is_running = False
        
        try:
            # データ収集タスクを停止
            if self.collection_task:
                self.collection_task.cancel()
                try:
                    await self.collection_task
                except asyncio.CancelledError:
                    pass
            
            # データ収集器を閉じる
            await self.collector.close()
            
            # データベース接続を閉じる
            if self.connection_manager:
                await self.connection_manager.close()
            
            logger.info("✅ スタンドアロンデータ収集デーモンが停止されました")
            
        except Exception as e:
            logger.error(f"❌ データ収集デーモン停止エラー: {e}")
    
    async def get_status(self):
        """デーモンの状況を取得"""
        try:
            if not self.is_running:
                return {"status": "stopped"}
            
            # データ収集器の状況を取得
            collector_status = await self.collector.get_status()
            
            # 最新のイベント発行状況を確認
            latest_event = None
            if self.connection_manager:
                async with self.connection_manager.get_connection() as conn:
                    latest_event = await conn.fetchrow("""
                        SELECT created_at, event_data 
                        FROM events 
                        WHERE event_type = 'data_collection_completed' 
                        AND symbol = $1 
                        ORDER BY created_at DESC 
                        LIMIT 1
                    """, self.symbol)
            
            return {
                "status": "running",
                "symbol": self.symbol,
                "interval_minutes": self.interval_minutes,
                "collector_status": collector_status,
                "latest_event": {
                    "timestamp": latest_event["created_at"].isoformat() if latest_event else None,
                    "data": latest_event["event_data"] if latest_event else None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ ステータス取得エラー: {e}")
            return {"status": "error", "error": str(e)}


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='スタンドアロンデータ収集デーモン')
    parser.add_argument('--symbol', default='USDJPY=X', help='通貨ペアシンボル')
    parser.add_argument('--interval', type=int, default=5, help='収集間隔（分）')
    
    args = parser.parse_args()
    
    daemon = StandaloneDataCollectionDaemon(
        symbol=args.symbol,
        interval_minutes=args.interval
    )
    
    try:
        # デーモンの開始
        await daemon.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ デーモンエラー: {e}")
        sys.exit(1)
    finally:
        await daemon.stop()


if __name__ == "__main__":
    # デーモンの実行
    asyncio.run(main())
