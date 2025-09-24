#!/usr/bin/env python3
"""
データ収集デーモン

バックグラウンドで継続的にデータを収集するデーモンプロセスです。
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_collection.core.continuous_collector import ContinuousDataCollector
from modules.llm_analysis.core.technical_analysis_service import TechnicalAnalysisService

# ログ設定（JST時刻で出力）
import logging.handlers
from modules.data_collection.utils.timezone_utils import TimezoneUtils

class JSTFormatter(logging.Formatter):
    """JST時刻でログを出力するフォーマッター"""
    
    def formatTime(self, record, datefmt=None):
        # ログの時刻をJSTに変換
        utc_time = datetime.fromtimestamp(record.created, tz=timezone.utc)
        jst_time = TimezoneUtils.format_jst(utc_time, "%Y-%m-%d %H:%M:%S")
        return jst_time

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# コンソールハンドラー
console_handler = logging.StreamHandler()
console_handler.setFormatter(JSTFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# ファイルハンドラー
file_handler = logging.FileHandler("/app/logs/data_collection_daemon.log")
file_handler.setFormatter(JSTFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger = logging.getLogger(__name__)


class DataCollectionDaemon:
    """データ収集デーモンクラス"""
    
    def __init__(self, symbol: str = "USDJPY=X", interval_minutes: int = 5):
        self.symbol = symbol
        self.interval_minutes = interval_minutes
        self.collector = ContinuousDataCollector(symbol)
        self.technical_analysis_service = TechnicalAnalysisService()
        self.is_running = False
        self.collection_task = None
        
        # シグナルハンドラーを設定
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """シグナルハンドラー"""
        logger.info(f"🛑 シグナル {signum} を受信しました。デーモンを停止します...")
        asyncio.create_task(self.stop())
    
    async def _on_data_collection_complete(self, results: Dict[str, int]):
        """データ収集完了時のコールバック"""
        try:
            total_new_data = sum(results.values())
            logger.info(f"🔄 データ収集完了イベント: {total_new_data}件の新しいデータ")
            
            # 新しいデータがある場合のみテクニカル分析を実行
            if total_new_data > 0:
                await self.technical_analysis_service.process_data_collection_event(
                    symbol=self.symbol,
                    new_data_count=total_new_data
                )
            else:
                logger.debug("ℹ️ 新しいデータがないため、テクニカル分析をスキップします")
                
        except Exception as e:
            logger.error(f"❌ データ収集完了コールバックエラー: {e}")
    
    async def start(self):
        """デーモンを開始"""
        logger.info("🚀 データ収集デーモンを開始します...")
        logger.info(f"📊 シンボル: {self.symbol}")
        logger.info(f"⏰ 収集間隔: {self.interval_minutes}分")
        
        try:
            # 初期化
            await self.collector.initialize()
            await self.technical_analysis_service.initialize()
            
            # データ収集完了時のコールバックを設定
            self.collector.add_data_collection_callback(self._on_data_collection_complete)
            
            # バックグラウンドで継続的データ収集を開始
            self.collection_task = await self.collector.start_background_collection(
                self.interval_minutes
            )
            
            self.is_running = True
            logger.info("✅ データ収集デーモンが開始されました")
            
            # デーモンが停止されるまで待機
            await self.collection_task
            
        except Exception as e:
            logger.error(f"❌ デーモン開始エラー: {e}")
            await self.stop()
    
    async def stop(self):
        """デーモンを停止"""
        if not self.is_running:
            return
        
        logger.info("🛑 データ収集デーモンを停止中...")
        
        self.is_running = False
        
        try:
            # データ収集を停止
            await self.collector.stop_collection()
            
            # リソースを解放
            await self.collector.close()
            if hasattr(self.technical_analysis_service, 'close'):
                await self.technical_analysis_service.close()
            
            logger.info("✅ データ収集デーモンが停止されました")
            
        except Exception as e:
            logger.error(f"❌ デーモン停止エラー: {e}")
    
    async def get_status(self):
        """デーモンの状況を取得"""
        try:
            status = await self.collector.get_collection_status()
            status["daemon_running"] = self.is_running
            status["interval_minutes"] = self.interval_minutes
            return status
        except Exception as e:
            logger.error(f"状況取得エラー: {e}")
            return {"error": str(e)}
    
    async def run_forever(self):
        """デーモンを永続実行"""
        try:
            await self.start()
            
            # 定期的に状況をログ出力
            while self.is_running:
                await asyncio.sleep(300)  # 5分間隔
                
                try:
                    status = await self.get_status()
                    if "error" not in status:
                        logger.info(f"📊 デーモン状況: {status['symbol']} - 実行中: {status['daemon_running']}")
                        
                        # 各時間足の最新データをログ
                        if "timeframes" in status and isinstance(status["timeframes"], dict):
                            for tf, data in status["timeframes"].items():
                                logger.info(f"  {tf}: {data['count']}件, 最新: {data['latest']}")
                    
                except Exception as e:
                    logger.error(f"状況確認エラー: {e}")
            
        except KeyboardInterrupt:
            logger.info("🛑 キーボード割り込みを受信しました")
        except Exception as e:
            logger.error(f"❌ デーモン実行エラー: {e}")
        finally:
            await self.stop()


async def main():
    """メイン関数"""
    # ログディレクトリを作成
    log_dir = Path("/app/logs")
    log_dir.mkdir(exist_ok=True)
    
    # デーモンを作成・実行
    daemon = DataCollectionDaemon(
        symbol="USDJPY=X",
        interval_minutes=5  # 5分間隔でデータ収集
    )
    
    try:
        await daemon.run_forever()
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")
    finally:
        logger.info("🔒 デーモンプロセス終了")


if __name__ == "__main__":
    asyncio.run(main())
