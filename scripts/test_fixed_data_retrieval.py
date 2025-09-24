#!/usr/bin/env python3
"""
修正されたデータ取得方法をテストするスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.llm_analysis.services.three_gate_analysis_service import ThreeGateAnalysisService
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def test_fixed_data_retrieval():
    """修正されたデータ取得方法をテスト"""
    
    print("🔍 修正されたデータ取得方法のテスト開始")
    print("=" * 60)
    
    # データベース接続
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # ThreeGateEngineのインスタンス作成
    from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
    engine = ThreeGateEngine()
    
    # ThreeGateAnalysisServiceのインスタンス作成
    service = ThreeGateAnalysisService(engine, db_manager)
    
    # テクニカル指標の計算をテスト
    print("\n📊 テクニカル指標計算のテスト:")
    print("-" * 40)
    
    try:
        indicators = await service._calculate_technical_indicators("USDJPY=X")
        
        if indicators:
            print(f"✅ テクニカル指標計算成功: {len(indicators)}個の指標")
            
            # 重要な指標の値を確認
            important_indicators = [
                '1d_EMA_200', '1d_EMA_55', '1d_EMA_21',
                '1d_MACD', '1d_MACD_Signal', '1d_RSI_14', '1d_ADX',
                '4h_EMA_200', '4h_MACD', '4h_RSI_14',
                '1h_EMA_200', '1h_MACD', '1h_RSI_14',
                '5m_EMA_200', '5m_MACD', '5m_RSI_14'
            ]
            
            print(f"\n📊 重要な指標の値:")
            for indicator in important_indicators:
                if indicator in indicators:
                    value = indicators[indicator]
                    if pd.notna(value):
                        print(f"  ✅ {indicator}: {value}")
                    else:
                        print(f"  ❌ {indicator}: NaN")
                else:
                    print(f"  ❌ {indicator}: 存在しません")
            
            # 三層ゲート評価をテスト
            print(f"\n🚪 三層ゲート評価のテスト:")
            print("-" * 40)
            
            result = await service.engine.evaluate("USDJPY=X", indicators)
            
            if result:
                print(f"✅ 三層ゲート評価成功")
                print(f"  - GATE 1: {'合格' if result.gate1_passed else '不合格'}")
                print(f"  - GATE 2: {'合格' if result.gate2_passed else '不合格'}")
                print(f"  - GATE 3: {'合格' if result.gate3_passed else '不合格'}")
                print(f"  - シグナル: {result.signal_type if result.signal_type else 'なし'}")
                
                # 各GATEの詳細情報
                if hasattr(result, 'gate1_result') and result.gate1_result:
                    print(f"  - GATE 1環境: {result.gate1_result.pattern}")
                    print(f"  - GATE 1信頼度: {result.gate1_result.confidence}")
                
                if hasattr(result, 'gate2_result') and result.gate2_result:
                    print(f"  - GATE 2シナリオ: {result.gate2_result.pattern}")
                    print(f"  - GATE 2信頼度: {result.gate2_result.confidence}")
                
                if hasattr(result, 'gate3_result') and result.gate3_result:
                    print(f"  - GATE 3トリガー: {result.gate3_result.pattern}")
                    print(f"  - GATE 3信頼度: {result.gate3_result.confidence}")
            else:
                print(f"❌ 三層ゲート評価失敗")
        else:
            print(f"❌ テクニカル指標計算失敗")
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    await db_manager.close()
    
    print("\n" + "=" * 60)
    print("🔍 修正されたデータ取得方法のテスト完了")

if __name__ == "__main__":
    asyncio.run(test_fixed_data_retrieval())
