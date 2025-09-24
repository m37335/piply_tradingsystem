#!/usr/bin/env python3
"""
統合パイプラインのシンプルテスト

データ収集とテクニカル分析の統合を一度だけテストします。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.data_collection.core.continuous_collector import ContinuousDataCollector
from modules.llm_analysis.core.technical_analysis_service import TechnicalAnalysisService

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_integrated_pipeline_simple():
    """統合パイプラインのシンプルテスト"""
    logger.info("🧪 統合パイプラインテスト開始（シンプル版）")
    logger.info("=" * 60)
    
    collector = None
    analysis_service = None
    
    try:
        # データ収集器を作成
        collector = ContinuousDataCollector(symbol="USDJPY=X")
        await collector.initialize()
        
        # テクニカル分析サービスを作成
        analysis_service = TechnicalAnalysisService()
        await analysis_service.initialize()
        
        # データ収集完了時のコールバックを設定
        collector.add_data_collection_callback(analysis_service.process_data_collection_event)
        
        logger.info("✅ 初期化完了")
        
        # 一度だけデータ収集を実行
        logger.info("🔄 データ収集実行...")
        results = await collector.collect_all_timeframes()
        
        total_saved = sum(results.values())
        logger.info(f"📊 データ収集結果: {total_saved}件の新しいデータ")
        
        if total_saved > 0:
            logger.info("✅ テクニカル分析が自動実行されました")
        else:
            logger.info("ℹ️ 新しいデータがないため、テクニカル分析はスキップされました")
        
        logger.info("✅ テスト完了")
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
    finally:
        if collector:
            await collector.close()
        if analysis_service:
            await analysis_service.close()
        logger.info("🔒 リソース解放完了")


async def main():
    """メイン関数"""
    try:
        await test_integrated_pipeline_simple()
    except KeyboardInterrupt:
        logger.info("🛑 テスト中断")
    except Exception as e:
        logger.error(f"❌ メインエラー: {e}")


if __name__ == "__main__":
    asyncio.run(main())
