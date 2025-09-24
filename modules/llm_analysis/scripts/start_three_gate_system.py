#!/usr/bin/env python3
"""
三層ゲート式フィルタリングシステム起動スクリプト

既存のイベント駆動システムと並行して動作する
新しい三層ゲート式フィルタリングシステムを起動します。
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.services.three_gate_analysis_service import ThreeGateAnalysisService
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/app/logs/three_gate_system.log')
    ]
)

logger = logging.getLogger(__name__)


class ThreeGateSystem:
    """三層ゲート式フィルタリングシステム"""
    
    def __init__(self):
        self.engine = ThreeGateEngine()
        self.analysis_service = None
        self.connection_manager = None
        self.is_running = False
        self.tasks = []
        
    async def initialize(self):
        """システムの初期化"""
        try:
            logger.info("🚀 三層ゲート式フィルタリングシステム初期化開始")
            
            # データベース接続の初期化
            db_config = DatabaseConfig()
            self.connection_manager = DatabaseConnectionManager(
                connection_string=db_config.connection_string,
                min_connections=db_config.min_connections,
                max_connections=db_config.max_connections
            )
            await self.connection_manager.initialize()
            
            # 分析サービスの初期化
            self.analysis_service = ThreeGateAnalysisService(
                engine=self.engine,
                connection_manager=self.connection_manager
            )
            await self.analysis_service.initialize()
            
            logger.info("✅ 三層ゲート式フィルタリングシステム初期化完了")
            
        except Exception as e:
            logger.error(f"❌ システム初期化エラー: {e}")
            raise
    
    async def start(self):
        """システムの開始"""
        if self.is_running:
            logger.warning("⚠️ システムは既に実行中です")
            return
        
        try:
            logger.info("🎯 三層ゲート式フィルタリングシステム開始")
            self.is_running = True
            
            # イベント監視タスクの開始
            event_task = asyncio.create_task(self._monitor_events())
            self.tasks.append(event_task)
            
            # ヘルスチェックタスクの開始
            health_task = asyncio.create_task(self._health_check())
            self.tasks.append(health_task)
            
            # 統計レポートタスクの開始
            stats_task = asyncio.create_task(self._statistics_report())
            self.tasks.append(stats_task)
            
            logger.info("✅ 三層ゲート式フィルタリングシステム開始完了")
            
            # タスクの完了を待機
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ システム実行エラー: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """システムの停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 三層ゲート式フィルタリングシステム停止開始")
        self.is_running = False
        
        # タスクのキャンセル
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # タスクの完了を待機
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # サービスの停止
        if self.analysis_service:
            await self.analysis_service.close()
        
        # データベース接続の閉じる
        if self.connection_manager:
            await self.connection_manager.close()
        
        logger.info("✅ 三層ゲート式フィルタリングシステム停止完了")
    
    async def _monitor_events(self):
        """イベント監視タスク"""
        logger.info("👁️ イベント監視開始")
        
        while self.is_running:
            try:
                # データ収集完了イベントを監視
                await self.analysis_service.process_events()
                
                # 5秒間隔で監視
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                logger.info("👁️ イベント監視タスクがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ イベント監視エラー: {e}")
                await asyncio.sleep(10)  # エラー時は10秒待機
    
    async def _health_check(self):
        """ヘルスチェックタスク"""
        logger.info("💓 ヘルスチェック開始")
        
        while self.is_running:
            try:
                # データベース接続のヘルスチェック
                if self.connection_manager:
                    health = await self.connection_manager.health_check()
                    if not health.get('healthy', False):
                        logger.warning("⚠️ データベース接続に問題があります")
                
                # 分析サービスのヘルスチェック
                if self.analysis_service:
                    service_health = await self.analysis_service.health_check()
                    if not service_health.get('healthy', False):
                        logger.warning("⚠️ 分析サービスに問題があります")
                
                # 30秒間隔でヘルスチェック
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("💓 ヘルスチェックタスクがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ ヘルスチェックエラー: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機
    
    async def _statistics_report(self):
        """統計レポートタスク"""
        logger.info("📊 統計レポート開始")
        
        while self.is_running:
            try:
                # 1時間間隔で統計レポート
                await asyncio.sleep(3600)
                
                if self.analysis_service:
                    stats = await self.analysis_service.get_statistics()
                    logger.info(f"📊 統計レポート: {stats}")
                
            except asyncio.CancelledError:
                logger.info("📊 統計レポートタスクがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ 統計レポートエラー: {e}")
                await asyncio.sleep(3600)  # エラー時も1時間待機
    
    def get_status(self) -> dict:
        """システムの状態を取得"""
        return {
            'running': self.is_running,
            'tasks_count': len(self.tasks),
            'active_tasks': [task.get_name() for task in self.tasks if not task.done()],
            'timestamp': datetime.now(timezone.utc).isoformat()
        }


# シグナルハンドラー
def signal_handler(signum, frame):
    """シグナルハンドラー"""
    logger.info(f"🛑 シグナル {signum} を受信しました。システムを停止します...")
    if 'system' in globals():
        asyncio.create_task(system.stop())


async def main():
    """メイン関数"""
    global system
    
    # シグナルハンドラーの設定
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    system = ThreeGateSystem()
    
    try:
        # システムの初期化と開始
        await system.initialize()
        await system.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ システムエラー: {e}")
        sys.exit(1)
    finally:
        await system.stop()


if __name__ == "__main__":
    # ログディレクトリの作成
    Path("/app/logs").mkdir(exist_ok=True)
    
    # システムの実行
    asyncio.run(main())
