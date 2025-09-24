#!/usr/bin/env python3
"""
統合パイプラインのテスト

データ収集デーモンとテクニカル分析サービスの統合をテストします。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.data_collection.daemon.data_collection_daemon import DataCollectionDaemon

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_integrated_pipeline():
    """統合パイプラインのテスト"""
    logger.info("🧪 統合パイプラインテスト開始")
    logger.info("=" * 60)
    
    daemon = None
    
    try:
        # デーモンを作成
        daemon = DataCollectionDaemon(
            symbol="USDJPY=X",
            interval_minutes=5  # 本番と同じ5分間隔
        )
        
        logger.info("✅ デーモン作成完了")
        
        # デーモンを開始
        logger.info("🚀 デーモン開始...")
        daemon_task = asyncio.create_task(daemon.start())
        
        # 10分間実行（2回のデータ収集サイクルを確認）
        logger.info("⏰ 10分間実行中...")
        await asyncio.sleep(600)  # 10分
        
        logger.info("✅ テスト完了")
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
    finally:
        if daemon:
            logger.info("🛑 デーモン停止中...")
            await daemon.stop()
            logger.info("✅ デーモン停止完了")


async def main():
    """メイン関数"""
    try:
        await test_integrated_pipeline()
    except KeyboardInterrupt:
        logger.info("🛑 テスト中断")
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
