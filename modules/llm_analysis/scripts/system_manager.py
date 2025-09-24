#!/usr/bin/env python3
"""
システムマネージャー

データ収集デーモンと分析システムルーターを管理し、
ホットスワップ機能を提供します。
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_collection.daemon.standalone_data_collection_daemon import StandaloneDataCollectionDaemon
from modules.llm_analysis.scripts.analysis_system_router import AnalysisSystemRouter

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class SystemManager:
    """システムマネージャー"""
    
    def __init__(self, symbol: str = "USDJPY=X", analysis_mode: str = "three_gate"):
        """
        初期化
        
        Args:
            symbol: 通貨ペアシンボル
            analysis_mode: 分析モード ("legacy" または "three_gate")
        """
        self.symbol = symbol
        self.analysis_mode = analysis_mode
        
        # システムコンポーネント
        self.data_collection_daemon = None
        self.analysis_router = None
        
        # 管理状態
        self.is_running = False
        self.management_task = None
        
        # シグナルハンドラーの設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。システムマネージャーを停止します...")
        asyncio.create_task(self.stop())
    
    async def start(self):
        """システムを開始"""
        if self.is_running:
            logger.warning("⚠️ システムは既に実行中です")
            return
        
        try:
            logger.info("🚀 システムマネージャー開始")
            logger.info(f"📊 シンボル: {self.symbol}")
            logger.info(f"🔧 分析モード: {self.analysis_mode}")
            
            self.is_running = True
            
            # データ収集デーモンを開始
            await self._start_data_collection_daemon()
            
            # 分析システムルーターを開始
            await self._start_analysis_router()
            
            # 管理タスクを開始
            self.management_task = asyncio.create_task(self._management_loop())
            
            logger.info("✅ システムマネージャー開始完了")
            logger.info("📋 システム構成:")
            logger.info("  - データ収集デーモン: 独立稼働")
            logger.info(f"  - 分析システム: {self.analysis_mode} モード")
            logger.info("  - ホットスワップ: 対応済み")
            
            # 管理タスクの完了を待機
            await self.management_task
            
        except Exception as e:
            logger.error(f"❌ システム開始エラー: {e}")
            await self.stop()
            raise
    
    async def _start_data_collection_daemon(self):
        """データ収集デーモンを開始"""
        try:
            logger.info("🔧 データ収集デーモンを開始中...")
            
            self.data_collection_daemon = StandaloneDataCollectionDaemon(
                symbol=self.symbol,
                interval_minutes=5
            )
            
            # バックグラウンドでデーモンを開始
            asyncio.create_task(self.data_collection_daemon.start())
            
            # デーモンの起動を待機
            await asyncio.sleep(2)
            
            logger.info("✅ データ収集デーモン開始完了")
            
        except Exception as e:
            logger.error(f"❌ データ収集デーモン開始エラー: {e}")
            raise
    
    async def _start_analysis_router(self):
        """分析システムルーターを開始"""
        try:
            logger.info("🔧 分析システムルーターを開始中...")
            
            self.analysis_router = AnalysisSystemRouter(
                analysis_mode=self.analysis_mode
            )
            
            await self.analysis_router.initialize()
            
            # バックグラウンドでルーターを開始
            asyncio.create_task(self.analysis_router.start())
            
            # ルーターの起動を待機
            await asyncio.sleep(2)
            
            logger.info("✅ 分析システムルーター開始完了")
            
        except Exception as e:
            logger.error(f"❌ 分析システムルーター開始エラー: {e}")
            raise
    
    async def _management_loop(self):
        """管理ループ"""
        logger.info("🔄 システム管理ループ開始")
        
        while self.is_running:
            try:
                # システムの健全性をチェック
                await self._health_check()
                
                # 30秒間隔でチェック
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                logger.info("🔄 管理ループがキャンセルされました")
                break
            except Exception as e:
                logger.error(f"❌ 管理ループエラー: {e}")
                await asyncio.sleep(10)
    
    async def _health_check(self):
        """システムの健全性チェック"""
        try:
            # データ収集デーモンの健全性チェック
            if self.data_collection_daemon:
                daemon_status = await self.data_collection_daemon.get_status()
                if daemon_status.get("status") != "running":
                    logger.warning("⚠️ データ収集デーモンが停止しています")
            
            # 分析システムルーターの健全性チェック
            if self.analysis_router:
                router_status = await self.analysis_router.get_status()
                if not router_status.get("router_running", False):
                    logger.warning("⚠️ 分析システムルーターが停止しています")
            
        except Exception as e:
            logger.error(f"❌ 健全性チェックエラー: {e}")
    
    async def switch_analysis_mode(self, new_mode: str):
        """分析モードをホットスワップ"""
        try:
            if new_mode not in ["legacy", "three_gate"]:
                raise ValueError(f"無効な分析モード: {new_mode}")
            
            if new_mode == self.analysis_mode:
                logger.info(f"ℹ️ 分析モードは既に {new_mode} です")
                return
            
            logger.info(f"🔄 分析モードをホットスワップ中: {self.analysis_mode} → {new_mode}")
            
            # データ収集は継続（停止しない）
            # 分析システムルーターのモードのみ切り替え
            if self.analysis_router:
                await self.analysis_router.switch_analysis_mode(new_mode)
            
            self.analysis_mode = new_mode
            
            logger.info(f"✅ 分析モードホットスワップ完了: {new_mode}")
            logger.info("📊 データ収集は継続中です")
            
        except Exception as e:
            logger.error(f"❌ 分析モードホットスワップエラー: {e}")
            raise
    
    async def restart_analysis_system(self):
        """分析システムを再起動"""
        try:
            logger.info("🔄 分析システムを再起動中...")
            
            # 現在の分析システムルーターを停止
            if self.analysis_router:
                await self.analysis_router.stop()
                self.analysis_router = None
            
            # 新しい分析システムルーターを開始
            await self._start_analysis_router()
            
            logger.info("✅ 分析システム再起動完了")
            
        except Exception as e:
            logger.error(f"❌ 分析システム再起動エラー: {e}")
            raise
    
    async def get_system_status(self) -> Dict[str, Any]:
        """システム全体の状況を取得"""
        try:
            status = {
                "system_running": self.is_running,
                "symbol": self.symbol,
                "analysis_mode": self.analysis_mode,
                "components": {}
            }
            
            # データ収集デーモンの状況
            if self.data_collection_daemon:
                daemon_status = await self.data_collection_daemon.get_status()
                status["components"]["data_collection_daemon"] = daemon_status
            
            # 分析システムルーターの状況
            if self.analysis_router:
                router_status = await self.analysis_router.get_status()
                status["components"]["analysis_router"] = router_status
            
            return status
            
        except Exception as e:
            logger.error(f"❌ システム状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def stop(self):
        """システムを停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 システムマネージャー停止開始")
        self.is_running = False
        
        try:
            # 管理タスクを停止
            if self.management_task:
                self.management_task.cancel()
                try:
                    await self.management_task
                except asyncio.CancelledError:
                    pass
            
            # 分析システムルーターを停止
            if self.analysis_router:
                await self.analysis_router.stop()
            
            # データ収集デーモンを停止
            if self.data_collection_daemon:
                await self.data_collection_daemon.stop()
            
            logger.info("✅ システムマネージャー停止完了")
            
        except Exception as e:
            logger.error(f"❌ システム停止エラー: {e}")


async def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='システムマネージャー')
    parser.add_argument('--symbol', default='USDJPY=X', help='通貨ペアシンボル')
    parser.add_argument('--mode', choices=['legacy', 'three_gate'], 
                       default='three_gate', help='分析モード')
    
    args = parser.parse_args()
    
    manager = SystemManager(
        symbol=args.symbol,
        analysis_mode=args.mode
    )
    
    try:
        # システムの開始
        await manager.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 ユーザーによる中断")
    except Exception as e:
        logger.error(f"❌ システムエラー: {e}")
        sys.exit(1)
    finally:
        await manager.stop()


if __name__ == "__main__":
    # システムマネージャーの実行
    asyncio.run(main())
