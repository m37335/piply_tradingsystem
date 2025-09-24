"""
継続パイプラインテスト

5分間隔での継続実行をテストし、起動状況を確認する
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# パスの設定
sys.path.append('/app')

from modules.llm_analysis.core.trading_pipeline import TradingPipeline


async def test_continuous_pipeline():
    """継続パイプラインテスト（5分間隔）"""
    print("🚀 継続パイプラインテスト開始")
    print("=" * 60)
    print("⏰ 5分間隔での分析サイクルを監視します")
    print("📊 各サイクルで以下を確認:")
    print("   - データ収集状況")
    print("   - テクニカル指標計算")
    print("   - ルール評価結果")
    print("   - シナリオ作成状況")
    print("   - Discord配信状況")
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
        print(f"📊 初期パイプライン状態: {status}")
        
        # 継続実行（10分間）
        print("⏰ 10分間の継続実行を開始...")
        print("   - 5分間隔で2回の分析サイクルを実行")
        print("   - 各サイクルで詳細ログを出力")
        
        # パイプライン実行タスク
        pipeline_task = asyncio.create_task(
            pipeline.start_pipeline('USDJPY=X')
        )
        
        # 監視タスク（30秒間隔で状態確認）
        async def monitor_pipeline():
            cycle_count = 0
            while True:
                await asyncio.sleep(30)  # 30秒間隔で監視
                cycle_count += 1
                
                status = pipeline.get_pipeline_status()
                current_time = datetime.now(timezone.utc)
                
                print(f"\n📊 監視レポート #{cycle_count} ({current_time.strftime('%H:%M:%S')} UTC)")
                print(f"   - パイプライン実行中: {status['is_running']}")
                print(f"   - アクティブシナリオ数: {status['active_scenarios']}")
                print(f"   - 最終分析時刻: {status['last_analysis_time']}")
                print(f"   - シナリオID: {status['scenario_ids']}")
                
                if status['last_analysis_time']:
                    last_analysis = datetime.fromisoformat(status['last_analysis_time'].replace('Z', '+00:00'))
                    time_diff = (current_time - last_analysis).total_seconds()
                    print(f"   - 前回分析からの経過時間: {time_diff:.0f}秒")
        
        # 監視タスク開始
        monitor_task = asyncio.create_task(monitor_pipeline())
        
        # 10分後に停止
        await asyncio.sleep(600)  # 10分間
        
        # タスク停止
        await pipeline.stop_pipeline()
        pipeline_task.cancel()
        monitor_task.cancel()
        
        try:
            await pipeline_task
        except asyncio.CancelledError:
            pass
        
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
        
        # 最終状態確認
        final_status = pipeline.get_pipeline_status()
        print("\n" + "=" * 60)
        print("📊 最終パイプライン状態:")
        print(f"   - 実行中: {final_status['is_running']}")
        print(f"   - アクティブシナリオ数: {final_status['active_scenarios']}")
        print(f"   - 最終分析時刻: {final_status['last_analysis_time']}")
        print(f"   - シナリオID: {final_status['scenario_ids']}")
        
        print("✅ 継続パイプラインテスト完了")
        
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


async def test_short_cycle():
    """短時間サイクルテスト（1分間隔で3回）"""
    print("🚀 短時間サイクルテスト開始")
    print("=" * 60)
    print("⏰ 1分間隔で3回の分析サイクルを実行")
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
        
        # 3回の分析サイクル実行
        for i in range(3):
            print(f"\n📊 分析サイクル #{i+1} 実行中...")
            start_time = datetime.now(timezone.utc)
            
            await pipeline._run_analysis_cycle('USDJPY=X')
            
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()
            
            status = pipeline.get_pipeline_status()
            print(f"✅ 分析サイクル #{i+1} 完了 ({duration:.1f}秒)")
            print(f"   - アクティブシナリオ数: {status['active_scenarios']}")
            print(f"   - 最終分析時刻: {status['last_analysis_time']}")
            
            if i < 2:  # 最後のサイクル以外は1分待機
                print("⏰ 1分間待機中...")
                await asyncio.sleep(60)
        
        print("\n✅ 短時間サイクルテスト完了")
        
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
    print("🎯 継続パイプラインテスト選択")
    print("1. 短時間サイクルテスト（1分間隔で3回）")
    print("2. 継続パイプラインテスト（10分間）")
    print("3. 終了")
    
    # 非対話的環境のため、短時間サイクルテストを実行
    print("非対話的環境のため、短時間サイクルテストを実行します...")
    await test_short_cycle()


if __name__ == "__main__":
    asyncio.run(main())
