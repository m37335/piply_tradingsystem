"""
データ準備器のテスト

データベース連携型データ準備器の動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta, timezone

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.data_preparator import LLMDataPreparator


async def test_data_preparator():
    """データ準備器のテスト"""
    print("🧪 データ準備器テスト開始")
    
    preparator = LLMDataPreparator()
    
    try:
        # 1. トレンド方向分析用データの準備
        print("\n📊 1. トレンド方向分析用データ準備テスト...")
        trend_data = await preparator.prepare_analysis_data("trend_direction")
        
        print(f"✅ トレンド方向データ準備完了:")
        print(f"   シンボル: {trend_data['symbol']}")
        print(f"   利用可能時間足: {trend_data['metadata']['timeframes_available']}")
        print(f"   データ品質: {trend_data['metadata']['data_quality']:.2f}")
        
        for timeframe, tf_data in trend_data['timeframes'].items():
            print(f"   {timeframe}: {tf_data['count']}件, 品質: {tf_data['quality_score']:.2f}")
            if tf_data['latest']:
                print(f"     最新: {tf_data['latest']}")
        
        # 2. ゾーン決定分析用データの準備
        print("\n📊 2. ゾーン決定分析用データ準備テスト...")
        zone_data = await preparator.prepare_analysis_data("zone_decision")
        
        print(f"✅ ゾーン決定データ準備完了:")
        print(f"   利用可能時間足: {zone_data['metadata']['timeframes_available']}")
        print(f"   データ品質: {zone_data['metadata']['data_quality']:.2f}")
        
        # 3. 執行タイミング分析用データの準備
        print("\n📊 3. 執行タイミング分析用データ準備テスト...")
        timing_data = await preparator.prepare_analysis_data("timing_execution")
        
        print(f"✅ 執行タイミングデータ準備完了:")
        print(f"   利用可能時間足: {timing_data['metadata']['timeframes_available']}")
        print(f"   データ品質: {timing_data['metadata']['data_quality']:.2f}")
        
        # 4. トレンド補強分析用データの準備
        print("\n📊 4. トレンド補強分析用データ準備テスト...")
        reinforcement_data = await preparator.prepare_analysis_data("trend_reinforcement")
        
        print(f"✅ トレンド補強データ準備完了:")
        print(f"   利用可能時間足: {reinforcement_data['metadata']['timeframes_available']}")
        print(f"   データ品質: {reinforcement_data['metadata']['data_quality']:.2f}")
        
        # 5. 最新データサマリーの取得
        print("\n📊 5. 最新データサマリーテスト...")
        summary = await preparator.get_latest_data_summary()
        
        print("✅ 最新データサマリー:")
        for timeframe, data in summary.items():
            if data:
                print(f"   {timeframe}: {data['latest_price']:.5f} @ {data['latest_timestamp']}")
                print(f"      ボリューム: {data['latest_volume']:,}, 品質: {data['quality_score']:.2f}")
            else:
                print(f"   {timeframe}: データなし")
        
        # 6. カスタム時間足でのテスト
        print("\n📊 6. カスタム時間足テスト...")
        custom_data = await preparator.prepare_analysis_data(
            "trend_direction", 
            timeframes=["1h", "4h"]
        )
        
        print(f"✅ カスタム時間足データ準備完了:")
        print(f"   指定時間足: {custom_data['metadata']['timeframes_available']}")
        
        print("\n🎉 全てのテストが成功しました！")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await preparator.close()


async def test_data_quality():
    """データ品質チェックのテスト"""
    print("\n🧪 データ品質チェックテスト...")
    
    preparator = LLMDataPreparator()
    
    try:
        # サンプルデータでの品質チェック
        import pandas as pd
        import numpy as np
        
        # 正常なデータ
        good_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [101.0, 102.0, 103.0],
            'low': [99.0, 100.0, 101.0],
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })
        
        quality_score = preparator._check_data_quality(good_data, "1h")
        print(f"✅ 正常データの品質スコア: {quality_score:.2f}")
        
        # 異常なデータ（高値 < 安値）
        bad_data = pd.DataFrame({
            'open': [100.0, 101.0, 102.0],
            'high': [99.0, 100.0, 101.0],  # 高値が安値より低い
            'low': [101.0, 102.0, 103.0],  # 安値が高値より高い
            'close': [100.5, 101.5, 102.5],
            'volume': [1000, 1100, 1200]
        })
        
        quality_score = preparator._check_data_quality(bad_data, "1h")
        print(f"✅ 異常データの品質スコア: {quality_score:.2f}")
        
        # 空データ
        empty_data = pd.DataFrame()
        quality_score = preparator._check_data_quality(empty_data, "1h")
        print(f"✅ 空データの品質スコア: {quality_score:.2f}")
        
    except Exception as e:
        print(f"❌ データ品質テストエラー: {e}")
    finally:
        await preparator.close()


async def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 データ準備器テスト開始")
    
    # 基本機能テスト
    await test_data_preparator()
    
    # データ品質テスト
    await test_data_quality()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
