"""
売買パイプラインのテスト

正しい設計に基づく売買パイプラインのテスト：
1. 5分間隔でデータ収集・テクニカル指標計算・ルール判定
2. 条件成立時のみStream APIでリアルタイム監視
3. エントリーポイント確認・Discord配信
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# パスの設定
sys.path.append('/app')

from modules.llm_analysis.core.trading_pipeline import TradingPipeline


async def test_trading_pipeline():
    """売買パイプラインのテスト"""
    print("🚀 売買パイプラインテスト開始")
    print("=" * 60)
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # パイプラインの初期化
    pipeline = TradingPipeline()
    
    try:
        # 初期化
        print("📋 パイプライン初期化中...")
        await pipeline.initialize()
        print("✅ パイプライン初期化完了")
        
        # 状態確認
        status = pipeline.get_pipeline_status()
        print(f"📊 パイプライン状態: {status}")
        
        # 短時間のテスト実行（2分間）
        print("⏰ 2分間のテスト実行を開始...")
        print("   - 5分間隔の分析サイクルを2回実行")
        print("   - 条件成立時はDiscord配信")
        print("   - Stream API監視も実行")
        
        # テスト実行
        test_task = asyncio.create_task(
            pipeline.start_pipeline('USDJPY=X')
        )
        
        # 2分後に停止
        await asyncio.sleep(120)  # 2分間
        
        # パイプライン停止
        await pipeline.stop_pipeline()
        test_task.cancel()
        
        try:
            await test_task
        except asyncio.CancelledError:
            pass
        
        # 最終状態確認
        final_status = pipeline.get_pipeline_status()
        print("=" * 60)
        print("📊 最終パイプライン状態:")
        print(f"   - 実行中: {final_status['is_running']}")
        print(f"   - アクティブシナリオ数: {final_status['active_scenarios']}")
        print(f"   - 最終分析時刻: {final_status['last_analysis_time']}")
        print(f"   - シナリオID: {final_status['scenario_ids']}")
        
        print("✅ 売買パイプラインテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        try:
            await pipeline._cleanup()
            print("🧹 リソースクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")


async def test_single_analysis_cycle():
    """単一分析サイクルのテスト"""
    print("🔍 単一分析サイクルテスト開始")
    print("=" * 60)
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # パイプラインの初期化
    pipeline = TradingPipeline()
    
    try:
        # 初期化
        print("📋 パイプライン初期化中...")
        await pipeline.initialize()
        print("✅ パイプライン初期化完了")
        
        # 単一分析サイクル実行
        print("📊 単一分析サイクル実行中...")
        await pipeline._run_analysis_cycle('USDJPY=X')
        
        # 状態確認
        status = pipeline.get_pipeline_status()
        print("=" * 60)
        print("📊 分析サイクル結果:")
        print(f"   - アクティブシナリオ数: {status['active_scenarios']}")
        print(f"   - 最終分析時刻: {status['last_analysis_time']}")
        print(f"   - シナリオID: {status['scenario_ids']}")
        
        print("✅ 単一分析サイクルテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        try:
            await pipeline._cleanup()
            print("🧹 リソースクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")


async def main():
    """メイン関数"""
    print("🎯 売買パイプラインテスト選択")
    print("1. 単一分析サイクルテスト（推奨）")
    print("2. 2分間フルテスト")
    print("3. 終了")
    
    # 非対話的環境のため、単一分析サイクルテストを実行
    print("非対話的環境のため、単一分析サイクルテストを実行します...")
    await test_single_analysis_cycle()


if __name__ == "__main__":
    asyncio.run(main())
