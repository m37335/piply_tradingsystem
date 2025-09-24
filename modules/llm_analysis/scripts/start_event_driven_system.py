#!/usr/bin/env python3
"""
完全なイベント駆動システムの起動スクリプト

データ収集サービスと分析サービスを同時に起動します。
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_collection.daemon.data_collection_daemon import DataCollectionDaemon
from modules.llm_analysis.services.analysis_service import AnalysisService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EventDrivenSystem:
    """完全なイベント駆動システム"""
    
    def __init__(self, symbol: str = "USDJPY=X"):
        self.symbol = symbol
        self.data_collection_daemon = DataCollectionDaemon(symbol=symbol, interval_minutes=5)
        self.analysis_service = AnalysisService(symbol=symbol)
        self.is_running = False
        
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。システムを停止します...")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """システムを開始"""
        if self.is_running:
            logger.warning("⚠️ システムは既に実行中です")
            return
        
        self.is_running = True
        logger.info("🚀 完全なイベント駆動システムを開始します...")
        logger.info(f"📊 シンボル: {self.symbol}")
        
        try:
            # 分析サービスを初期化・開始
            logger.info("🔧 分析サービスを初期化中...")
            await self.analysis_service.initialize()
            analysis_task = asyncio.create_task(self.analysis_service.start())
            
            # データ収集デーモンを初期化・開始
            logger.info("🔧 データ収集デーモンを初期化中...")
            await self.data_collection_daemon.collector.initialize()
            await self.data_collection_daemon.technical_analysis_service.initialize()
            
            # データ収集デーモンを開始
            daemon_task = asyncio.create_task(self.data_collection_daemon.start())
            
            logger.info("✅ 完全なイベント駆動システムが開始されました")
            logger.info("📋 システム構成:")
            logger.info("  - データ収集デーモン: 5分間隔でデータ収集・イベント発行")
            logger.info("  - 分析サービス: イベント監視・テクニカル分析・シナリオ作成")
            logger.info("  - イベントテーブル: データベースでイベント管理")
            
            # 両方のタスクが完了するまで待機
            await asyncio.gather(daemon_task, analysis_task, return_exceptions=True)
            
        except Exception as e:
            logger.error(f"❌ システム開始エラー: {e}")
            await self.stop()
    
    async def stop(self):
        """システムを停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 完全なイベント駆動システムを停止中...")
        self.is_running = False
        
        try:
            # データ収集デーモンを停止
            await self.data_collection_daemon.stop()
            
            # 分析サービスを停止
            await self.analysis_service.stop()
            
            logger.info("✅ 完全なイベント駆動システムが停止されました")
            
        except Exception as e:
            logger.error(f"❌ システム停止エラー: {e}")
    
    async def get_status(self):
        """システムの状況を取得"""
        try:
            daemon_status = await self.data_collection_daemon.get_status()
            
            status = {
                "system_running": self.is_running,
                "symbol": self.symbol,
                "data_collection": daemon_status,
                "analysis_service": {
                    "running": self.analysis_service.is_running
                }
            }
            
            return status
            
        except Exception as e:
            logger.error(f"状況取得エラー: {e}")
            return {"error": str(e)}


async def main():
    """メイン関数"""
    # ログディレクトリを作成
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)
    
    # システムを作成・実行
    system = EventDrivenSystem(symbol="USDJPY=X")
    
    try:
        await system.start()
    except KeyboardInterrupt:
        logger.info("🛑 キーボード割り込みを受信しました")
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")
    finally:
        await system.stop()
        logger.info("🔒 システム終了")


if __name__ == "__main__":
    asyncio.run(main())
