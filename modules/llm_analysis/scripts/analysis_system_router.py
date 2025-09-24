#!/usr/bin/env python3
"""
分析システムルーター

データ収集完了イベントを監視し、設定に基づいて適切な分析システムに
ルーティングします。既存システムと三層ゲートシステムを切り替え可能です。
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig
from modules.llm_analysis.services.analysis_service import AnalysisService
from modules.llm_analysis.services.three_gate_analysis_service import ThreeGateAnalysisService
from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/analysis_system_router.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class AnalysisSystemRouter:
    """分析システムルーター"""
    
    def __init__(self, analysis_mode: str = "three_gate"):
        """
        初期化
        
        Args:
            analysis_mode: 分析モード ("legacy" または "three_gate")
        """
        self.analysis_mode = analysis_mode
        self.connection_manager = None
        self.analysis_service = None
        self.three_gate_service = None
        self.is_running = False
        self.monitor_task = None
        
        # 統計情報
        self.stats = {
            'total_events_processed': 0,
            'legacy_events_processed': 0,
            'three_gate_events_processed': 0,
            'last_analysis_time': None,
            'last_switch_time': None
        }
        
        # シグナルハンドラーの設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。分析システムルーターを停止します...")
        asyncio.create_task(self.stop())
    
    async def initialize(self):
        """ルーターの初期化"""
        try:
            logger.info("🔧 分析システムルーター初期化開始")
            logger.info(f"📊 分析モード: {self.analysis_mode}")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=3,
                max_connections=10
            )
            await self.connection_manager.initialize()
            
            # 分析サービスの初期化
            if self.analysis_mode == "legacy":
                self.analysis_service = AnalysisService()
                await self.analysis_service.initialize()
                logger.info("✅ 既存分析サービスを初期化しました")
            elif self.analysis_mode == "three_gate":
                engine = ThreeGateEngine()
                self.three_gate_service = ThreeGateAnalysisService(
                    engine=engine,
                    connection_manager=self.connection_manager
                )
                await self.three_gate_service.initialize()
                logger.info("✅ 三層ゲート分析サービスを初期化しました")
            else:
                raise ValueError(f"無効な分析モード: {self.analysis_mode}")
            
            logger.info("✅ 分析システムルーター初期化完了")
            
        except Exception as e:
            logger.error(f"❌ ルーター初期化エラー: {e}")
            raise
    
    async def start(self):
        """ルーターの開始"""
        if self.is_running:
            logger.warning("⚠️ ルーターは既に実行中です")
            return
        
        try:
            logger.info("🚀 分析システムルーター開始")
            self.is_running = True
            
            # イベント監視タスクの開始
            self.monitor_task = asyncio.create_task(self._monitor_events())
            
            logger.info("✅ 分析システムルーター開始完了")
            logger.info("📋 ルーター機能:")
            logger.info(f"  - 分析モード: {self.analysis_mode}")
            logger.info("  - イベント監視: データ収集完了イベントを監視")
            logger.info("  - 自動ルーティング: 設定に基づいて分析システムに転送")
            
            # タスクの完了を待機
            await self.monitor_task
            
        except Exception as e:
            logger.error(f"❌ ルーター開始エラー: {e}")
            raise
        finally:
            await self.stop()
    
    async def _monitor_events(self):
        """イベント監視タスク"""
        logger.info("👁️ イベント監視開始")
        
        while self.is_running:
            try:
                # 未処理のイベントを取得
                unprocessed_events = await self._get_unprocessed_events()
                
                if unprocessed_events:
                    logger.info(f"📥 {len(unprocessed_events)}件の未処理イベントを発見")
                    
                    for event in unprocessed_events:
                        await self._process_event(event)
                
                # 5秒間隔で監視
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                logger.info("👁️ イベント監視タスクがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ イベント監視エラー: {e}")
                await asyncio.sleep(10)  # エラー時は10秒待機
    
    async def _get_unprocessed_events(self) -> List[Dict[str, Any]]:
        """未処理のイベントを取得"""
        try:
            async with self.connection_manager.get_connection() as conn:
                events = await conn.fetch("""
                    SELECT id, event_type, symbol, event_data, created_at
                    FROM events 
                    WHERE event_type = 'data_collection_completed' 
                    AND processed = FALSE
                    ORDER BY created_at ASC
                    LIMIT 10
                """)
                
                return [
                    {
                        'id': event['id'],
                        'event_type': event['event_type'],
                        'symbol': event['symbol'],
                        'event_data': event['event_data'],
                        'created_at': event['created_at']
                    }
                    for event in events
                ]
                
        except Exception as e:
            logger.error(f"❌ 未処理イベント取得エラー: {e}")
            return []
    
    async def _process_event(self, event: Dict[str, Any]):
        """イベントを処理"""
        try:
            logger.info(f"🔄 イベント処理開始: ID={event['id']}, シンボル={event['symbol']}")
            
            # 分析モードに基づいてイベントを処理
            if self.analysis_mode == "legacy":
                await self._process_legacy_event(event)
            elif self.analysis_mode == "three_gate":
                await self._process_three_gate_event(event)
            
            # イベントを処理済みとしてマーク
            await self._mark_event_processed(event['id'])
            
            # 統計を更新
            self.stats['total_events_processed'] += 1
            if self.analysis_mode == "legacy":
                self.stats['legacy_events_processed'] += 1
            else:
                self.stats['three_gate_events_processed'] += 1
            self.stats['last_analysis_time'] = datetime.now(timezone.utc)
            
            logger.info(f"✅ イベント処理完了: ID={event['id']}")
            logger.info("─" * 80)
            
        except Exception as e:
            logger.error(f"❌ イベント処理エラー: ID={event['id']}, エラー={e}")
    
    async def _process_legacy_event(self, event: Dict[str, Any]):
        """既存システムでイベントを処理"""
        try:
            if not self.analysis_service:
                raise RuntimeError("既存分析サービスが初期化されていません")
            
            # イベントデータをパース
            event_data = event['event_data']
            if isinstance(event_data, str):
                import json
                event_data = json.loads(event_data)
            
            # 既存分析サービスでイベントを処理
            await self.analysis_service.process_data_collection_event(
                symbol=event['symbol'],
                new_data_count=event_data.get('total_new_records', 0)
            )
            
        except Exception as e:
            logger.error(f"❌ 既存システムイベント処理エラー: {e}")
            raise
    
    async def _process_three_gate_event(self, event: Dict[str, Any]):
        """三層ゲートシステムでイベントを処理"""
        try:
            if not self.three_gate_service:
                raise RuntimeError("三層ゲート分析サービスが初期化されていません")
            
            # イベントデータをパース
            event_data = event['event_data']
            if isinstance(event_data, str):
                import json
                event_data = json.loads(event_data)
            
            # 三層ゲート分析サービスでイベントを処理
            await self.three_gate_service.process_data_collection_event(
                symbol=event['symbol'],
                new_data_count=event_data.get('total_new_records', 0)
            )
            
        except Exception as e:
            logger.error(f"❌ 三層ゲートシステムイベント処理エラー: {e}")
            raise
    
    async def _mark_event_processed(self, event_id: int):
        """イベントを処理済みとしてマーク"""
        try:
            async with self.connection_manager.get_connection() as conn:
                await conn.execute("""
                    UPDATE events 
                    SET processed = TRUE, processed_at = NOW() 
                    WHERE id = $1
                """, event_id)
                
        except Exception as e:
            logger.error(f"❌ イベントマークエラー: {e}")
    
    async def switch_analysis_mode(self, new_mode: str):
        """分析モードを切り替え"""
        try:
            if new_mode not in ["legacy", "three_gate"]:
                raise ValueError(f"無効な分析モード: {new_mode}")
            
            if new_mode == self.analysis_mode:
                logger.info(f"ℹ️ 分析モードは既に {new_mode} です")
                return
            
            logger.info(f"🔄 分析モードを切り替え中: {self.analysis_mode} → {new_mode}")
            
            # 現在の分析サービスを停止
            if self.analysis_mode == "legacy" and self.analysis_service:
                await self.analysis_service.stop()
                self.analysis_service = None
            elif self.analysis_mode == "three_gate" and self.three_gate_service:
                await self.three_gate_service.close()
                self.three_gate_service = None
            
            # 新しい分析モードを設定
            self.analysis_mode = new_mode
            
            # 新しい分析サービスを初期化
            if new_mode == "legacy":
                self.analysis_service = AnalysisService()
                await self.analysis_service.initialize()
            elif new_mode == "three_gate":
                engine = ThreeGateEngine()
                self.three_gate_service = ThreeGateAnalysisService(
                    engine=engine,
                    connection_manager=self.connection_manager
                )
                await self.three_gate_service.initialize()
            
            self.stats['last_switch_time'] = datetime.now(timezone.utc)
            logger.info(f"✅ 分析モード切り替え完了: {new_mode}")
            
        except Exception as e:
            logger.error(f"❌ 分析モード切り替えエラー: {e}")
            raise
    
    async def get_status(self) -> Dict[str, Any]:
        """ルーターの状況を取得"""
        try:
            return {
                "router_running": self.is_running,
                "analysis_mode": self.analysis_mode,
                "stats": self.stats.copy(),
                "services": {
                    "legacy_service": self.analysis_service is not None,
                    "three_gate_service": self.three_gate_service is not None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ ステータス取得エラー: {e}")
            return {"error": str(e)}
    
    async def stop(self):
        """ルーターの停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 分析システムルーター停止開始")
        self.is_running = False
        
        try:
            # 監視タスクを停止
            if self.monitor_task:
                self.monitor_task.cancel()
                try:
                    await self.monitor_task
                except asyncio.CancelledError:
                    pass
            
            # 分析サービスを停止
            if self.analysis_service:
                await self.analysis_service.stop()
            
            if self.three_gate_service:
                await self.three_gate_service.close()
            
            # データベース接続を閉じる
            if self.connection_manager:
                await self.connection_manager.close()
            
            logger.info("✅ 分析システムルーター停止完了")
            
        except Exception as e:
            logger.error(f"❌ ルーター停止エラー: {e}")


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='分析システムルーター')
    parser.add_argument('--mode', choices=['legacy', 'three_gate'], 
                       default='three_gate', help='分析モード')
    
    args = parser.parse_args()
    
    router = AnalysisSystemRouter(analysis_mode=args.mode)
    
    try:
        # ルーターの初期化と開始
        await router.initialize()
        await router.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ ルーターエラー: {e}")
        sys.exit(1)
    finally:
        await router.stop()


if __name__ == "__main__":
    # ルーターの実行
    asyncio.run(main())
