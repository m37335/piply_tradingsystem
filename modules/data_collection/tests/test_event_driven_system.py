#!/usr/bin/env python3
"""
イベント駆動システムのテスト

データ収集サービスと分析サービスの連携をテストします。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.data_collection.core.continuous_collector import ContinuousDataCollector
from modules.llm_analysis.services.analysis_service import AnalysisService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_event_driven_system():
    """イベント駆動システムのテスト"""
    logger.info("🧪 イベント駆動システムテスト開始")
    logger.info("=" * 60)
    
    collector = None
    analysis_service = None
    
    try:
        # データ収集器を作成
        collector = ContinuousDataCollector(symbol="USDJPY=X")
        await collector.initialize()
        
        # 分析サービスを作成
        analysis_service = AnalysisService(symbol="USDJPY=X")
        await analysis_service.initialize()
        
        logger.info("✅ 初期化完了")
        
        # 分析サービスをバックグラウンドで開始
        logger.info("🚀 分析サービス開始...")
        analysis_task = asyncio.create_task(analysis_service.start())
        
        # 少し待機してからデータ収集を実行
        await asyncio.sleep(2)
        
        # 一度だけデータ収集を実行（イベント発行）
        logger.info("🔄 データ収集実行（イベント発行）...")
        results = await collector.collect_all_timeframes()
        
        total_saved = sum(results.values())
        logger.info(f"📊 データ収集結果: {total_saved}件の新しいデータ")
        
        if total_saved > 0:
            logger.info("✅ イベントが発行され、分析サービスが処理中...")
            
            # 分析サービスの処理を待機
            await asyncio.sleep(10)
        else:
            logger.info("ℹ️ 新しいデータがないため、イベントは発行されませんでした")
        
        logger.info("✅ テスト完了")
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
    finally:
        if analysis_service:
            logger.info("🛑 分析サービス停止中...")
            await analysis_service.stop()
            analysis_task.cancel()
        
        if collector:
            await collector.close()
        
        logger.info("🔒 リソース解放完了")


async def main():
    """メイン関数"""
    try:
        await test_event_driven_system()
    except KeyboardInterrupt:
        logger.info("🛑 テスト中断")
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
