#!/usr/bin/env python3
"""
三層ゲートシステムの基幹部分を徹底的にチェックするスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import yaml
import pandas as pd
from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def comprehensive_system_check():
    """基幹システムの徹底チェック"""
    
    print("🔍 基幹システム徹底チェック開始")
    print("=" * 60)
    
    # 1. 設定ファイルの整合性チェック
    print("\n📋 1. 設定ファイルの整合性チェック")
    print("-" * 40)
    
    # GATE 1設定
    with open('/app/modules/llm_analysis/config/gate1_patterns.yaml', 'r', encoding='utf-8') as f:
        gate1_config = yaml.safe_load(f)
    
    # GATE 2設定
    with open('/app/modules/llm_analysis/config/gate2_patterns.yaml', 'r', encoding='utf-8') as f:
        gate2_config = yaml.safe_load(f)
    
    # GATE 3設定
    with open('/app/modules/llm_analysis/config/gate3_patterns.yaml', 'r', encoding='utf-8') as f:
        gate3_config = yaml.safe_load(f)
    
    print("✅ 全設定ファイル読み込み完了")
    
    # GATE 1の詳細チェック
    print("\n🔸 GATE 1 詳細チェック:")
    gate1_patterns = gate1_config['patterns']
    for pattern_name, pattern_config in gate1_patterns.items():
        print(f"  📊 パターン: {pattern_name}")
        for key, value in pattern_config.items():
            if isinstance(value, dict) and 'environment' in value:
                print(f"    - 環境: {value['environment']}")
                if 'conditions' in value:
                    print(f"    - 条件数: {len(value['conditions'])}")
                    for condition in value['conditions']:
                        print(f"      * {condition.get('name', 'N/A')}: {condition.get('indicator', 'N/A')} {condition.get('operator', 'N/A')} {condition.get('reference', condition.get('value', 'N/A'))}")
            elif key == 'environment':
                print(f"    - 環境: {value}")
                if 'conditions' in pattern_config:
                    print(f"    - 条件数: {len(pattern_config['conditions'])}")
    
    # GATE 2の詳細チェック
    print("\n🔸 GATE 2 詳細チェック:")
    gate2_patterns = gate2_config['patterns']
    for pattern_name, pattern_config in gate2_patterns.items():
        print(f"  📊 パターン: {pattern_name}")
        if 'variants' in pattern_config:
            for variant_name, variant_config in pattern_config['variants'].items():
                print(f"    - バリアント: {variant_name}")
                if 'environment_conditions' in variant_config:
                    print(f"      * 環境条件: {variant_config['environment_conditions']}")
                if 'conditions' in variant_config:
                    print(f"      * 条件数: {len(variant_config['conditions'])}")
                    for condition in variant_config['conditions']:
                        print(f"        - {condition.get('name', 'N/A')}: {condition.get('indicator', 'N/A')} {condition.get('operator', 'N/A')} {condition.get('reference', condition.get('value', 'N/A'))}")
    
    # GATE 3の詳細チェック
    print("\n🔸 GATE 3 詳細チェック:")
    gate3_patterns = gate3_config['patterns']
    for pattern_name, pattern_config in gate3_patterns.items():
        print(f"  📊 パターン: {pattern_name}")
        if 'allowed_environments' in pattern_config:
            print(f"    - 許可環境: {pattern_config['allowed_environments']}")
        
        # サブパターンの詳細チェック
        for sub_pattern_name, sub_pattern_config in pattern_config.items():
            if sub_pattern_name not in ['name', 'description', 'allowed_environments']:
                print(f"    - サブパターン: {sub_pattern_name}")
                if 'conditions' in sub_pattern_config:
                    print(f"      * 条件数: {len(sub_pattern_config['conditions'])}")
                    for condition in sub_pattern_config['conditions']:
                        print(f"        - {condition.get('name', 'N/A')}: {condition.get('indicator', 'N/A')} {condition.get('operator', 'N/A')} {condition.get('reference', condition.get('value', 'N/A'))}")
    
    # 2. データベース接続とデータ取得
    print("\n📊 2. データベース接続とデータ取得")
    print("-" * 40)
    
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # 最新の価格データを取得
    query = """
    SELECT symbol, timeframe, timestamp, open, high, low, close, volume
    FROM price_data 
    WHERE symbol = 'USDJPY=X' 
    ORDER BY timestamp DESC 
    LIMIT 1000
    """
    
    result = await db_manager.execute_query(query)
    if not result:
        print("❌ 価格データが見つかりません")
        return
    
    df = pd.DataFrame(result, columns=['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    print(f"✅ 価格データ取得: {len(df)}件")
    
    # 時間足別データ確認
    timeframes = ['1d', '4h', '1h', '5m']
    timeframe_data = {}
    for tf in timeframes:
        tf_data = df[df['timeframe'] == tf].copy()
        timeframe_data[tf] = tf_data
        print(f"  - {tf}足: {len(tf_data)}件")
    
    # 3. テクニカル指標計算の詳細チェック
    print("\n📊 3. テクニカル指標計算の詳細チェック")
    print("-" * 40)
    
    calculator = TechnicalIndicatorCalculator()
    all_indicators = {}
    
    for tf, data in timeframe_data.items():
        if len(data) > 0:
            print(f"\n⏰ {tf}足の指標計算:")
            indicators = calculator.calculate_all_indicators({tf: data})
            all_indicators.update(indicators)
            
            # 指標の詳細確認
            if tf in indicators:
                df_with_indicators = indicators[tf]
                print(f"  - 計算された指標数: {len(df_with_indicators.columns)}")
                print(f"  - データ行数: {len(df_with_indicators)}")
                
                # 最新の指標値を確認
                latest_row = df_with_indicators.iloc[-1]
                print(f"  - 最新データの指標値:")
                for col in df_with_indicators.columns:
                    if col not in ['symbol', 'timeframe', 'timestamp']:
                        value = latest_row[col]
                        if pd.notna(value):
                            print(f"    * {col}: {value}")
                        else:
                            print(f"    * {col}: NaN")
    
    # 4. テストデータの構築
    print("\n📊 4. テストデータの構築")
    print("-" * 40)
    
    test_data = {}
    for tf, data in timeframe_data.items():
        if tf in all_indicators and len(data) > 0:
            df_with_indicators = all_indicators[tf]
            latest_row = df_with_indicators.iloc[-1]
            
            # 基本価格データ
            test_data[f'{tf}_open'] = data['open'].iloc[-1]
            test_data[f'{tf}_high'] = data['high'].iloc[-1]
            test_data[f'{tf}_low'] = data['low'].iloc[-1]
            test_data[f'{tf}_close'] = data['close'].iloc[-1]
            test_data[f'{tf}_volume'] = data['volume'].iloc[-1]
            
            # テクニカル指標データ
            for col in df_with_indicators.columns:
                if col not in ['symbol', 'timeframe', 'timestamp']:
                    value = latest_row[col]
                    if pd.notna(value):
                        test_data[f'{tf}_{col}'] = value
    
    print(f"✅ テストデータ構築完了: {len(test_data)}個の指標")
    
    # 5. ThreeGateEngineの詳細テスト
    print("\n🚪 5. ThreeGateEngineの詳細テスト")
    print("-" * 40)
    
    engine = ThreeGateEngine()
    
    try:
        print("🔍 評価開始...")
        result = await engine.evaluate("USDJPY=X", test_data)
        
        if result:
            print("✅ 評価結果取得成功")
            print(f"  - GATE 1: {'合格' if result.gate1_passed else '不合格'}")
            print(f"  - GATE 2: {'合格' if result.gate2_passed else '不合格'}")
            print(f"  - GATE 3: {'合格' if result.gate3_passed else '不合格'}")
            print(f"  - シグナル: {result.signal_type if result.signal_type else 'なし'}")
            
            # 各GATEの詳細情報
            if hasattr(result, 'gate1_result') and result.gate1_result:
                print(f"  - GATE 1環境: {result.gate1_result.pattern}")
                print(f"  - GATE 1信頼度: {result.gate1_result.confidence}")
                if hasattr(result.gate1_result, 'additional_data') and 'condition_details' in result.gate1_result.additional_data:
                    print(f"  - GATE 1条件詳細: {result.gate1_result.additional_data['condition_details']}")
            
            if hasattr(result, 'gate2_result') and result.gate2_result:
                print(f"  - GATE 2シナリオ: {result.gate2_result.pattern}")
                print(f"  - GATE 2信頼度: {result.gate2_result.confidence}")
                if hasattr(result.gate2_result, 'additional_data') and 'condition_details' in result.gate2_result.additional_data:
                    print(f"  - GATE 2条件詳細: {result.gate2_result.additional_data['condition_details']}")
            
            if hasattr(result, 'gate3_result') and result.gate3_result:
                print(f"  - GATE 3トリガー: {result.gate3_result.pattern}")
                print(f"  - GATE 3信頼度: {result.gate3_result.confidence}")
                if hasattr(result.gate3_result, 'additional_data') and 'condition_details' in result.gate3_result.additional_data:
                    print(f"  - GATE 3条件詳細: {result.gate3_result.additional_data['condition_details']}")
                else:
                    print("  - GATE 3条件詳細: なし（問題！）")
        else:
            print("❌ 評価結果がNoneです")
            
    except Exception as e:
        print(f"❌ 評価エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 重要な指標の存在確認
    print("\n📊 6. 重要な指標の存在確認")
    print("-" * 40)
    
    important_indicators = [
        'EMA_200', 'EMA_21', 'MACD', 'MACD_Signal', 'RSI_14', 'ADX',
        'Stochastic_K', 'candle_body', 'candle_upper_shadow', 'candle_lower_shadow',
        'bollinger_width', 'BB_Upper', 'BB_Lower', 'BB_Middle'
    ]
    
    for indicator in important_indicators:
        found = False
        for key in test_data.keys():
            if indicator in key:
                print(f"✅ {indicator}: {test_data[key]}")
                found = True
                break
        if not found:
            print(f"❌ {indicator}: 見つかりません")
    
    await db_manager.close()
    
    print("\n" + "=" * 60)
    print("🔍 基幹システム徹底チェック完了")

if __name__ == "__main__":
    asyncio.run(comprehensive_system_check())
