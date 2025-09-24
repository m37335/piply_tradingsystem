#!/usr/bin/env python3
"""
全GATEとパターンの論理的整合性をチェックするスクリプト
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

async def check_logical_consistency():
    """全GATEとパターンの論理的整合性をチェック"""
    
    print("🔍 論理的整合性チェック開始")
    
    # データベース接続
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # 最新の価格データを取得
    print("📊 最新価格データ取得中...")
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
    
    # データをDataFrameに変換
    df = pd.DataFrame(result, columns=['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # 時間足別にデータを分離
    timeframes = ['1d', '4h', '1h', '5m']
    timeframe_data = {}
    
    for tf in timeframes:
        tf_data = df[df['timeframe'] == tf].copy()
        if len(tf_data) > 0:
            timeframe_data[tf] = tf_data
            print(f"✅ {tf}足: {len(tf_data)}件のデータ")
        else:
            print(f"❌ {tf}足: データなし")
    
    # テクニカル指標計算
    print("\n📊 テクニカル指標計算中...")
    calculator = TechnicalIndicatorCalculator()
    
    all_indicators = {}
    for tf, data in timeframe_data.items():
        print(f"⏰ {tf}足の指標計算中...")
        indicators = calculator.calculate_all_indicators({tf: data})
        all_indicators.update(indicators)
        print(f"✅ {tf}足: {len(indicators)}個の指標を計算")
    
    # テスト用のデータ（実際のデータを使用）
    test_data = {}
    for tf, data in timeframe_data.items():
        if tf in all_indicators:
            # DataFrameから最新の値を抽出
            latest_data = {}
            df_with_indicators = all_indicators[tf]
            
            # 基本価格データ
            latest_data['open'] = data['open'].iloc[-1]
            latest_data['high'] = data['high'].iloc[-1]
            latest_data['low'] = data['low'].iloc[-1]
            latest_data['close'] = data['close'].iloc[-1]
            latest_data['volume'] = data['volume'].iloc[-1]
            
            # テクニカル指標データ
            for col in df_with_indicators.columns:
                if col not in ['symbol', 'timeframe', 'timestamp']:
                    latest_data[col] = df_with_indicators[col].iloc[-1]
            
            test_data.update(latest_data)
    
    print(f"📊 テストデータ: {len(test_data)}個の指標")
    
    # GATE設定ファイルを読み込み
    print("\n📋 GATE設定ファイルの読み込み...")
    
    # GATE 1設定
    with open('/app/modules/llm_analysis/config/gate1_patterns.yaml', 'r', encoding='utf-8') as f:
        gate1_config = yaml.safe_load(f)
    
    # GATE 2設定
    with open('/app/modules/llm_analysis/config/gate2_patterns.yaml', 'r', encoding='utf-8') as f:
        gate2_config = yaml.safe_load(f)
    
    # GATE 3設定
    with open('/app/modules/llm_analysis/config/gate3_patterns.yaml', 'r', encoding='utf-8') as f:
        gate3_config = yaml.safe_load(f)
    
    print("✅ 全GATE設定ファイルを読み込み完了")
    
    # 論理的整合性チェック
    print("\n🔍 論理的整合性チェック開始...")
    
    # 1. GATE 1の論理的整合性
    print("\n📊 GATE 1: 環境認識ゲートの論理的整合性")
    gate1_patterns = gate1_config['patterns']
    
    for pattern_name, pattern_config in gate1_patterns.items():
        print(f"\n🔸 パターン: {pattern_name}")
        
        if 'variants' in pattern_config:
            for variant_name, variant_config in pattern_config['variants'].items():
                print(f"  📋 バリアント: {variant_name}")
                
                # 環境名の整合性チェック
                if 'environment' in variant_config:
                    env_name = variant_config['environment']
                    print(f"    - 環境名: {env_name}")
                    
                    # GATE 2の環境マッピングをチェック
                    if 'environment_mapping' in gate2_config.get('common_settings', {}):
                        env_mapping = gate2_config['common_settings']['environment_mapping']
                        if env_name in env_mapping:
                            print(f"    ✅ GATE 2で環境マッピング存在: {env_mapping[env_name]}")
                        else:
                            print(f"    ❌ GATE 2で環境マッピング不存在")
                
                # 条件の整合性チェック
                if 'conditions' in variant_config:
                    for condition in variant_config['conditions']:
                        indicator_name = condition.get('indicator')
                        if indicator_name and indicator_name not in test_data:
                            print(f"    ❌ 未定義指標: {indicator_name}")
                        else:
                            print(f"    ✅ 指標存在: {indicator_name}")
    
    # 2. GATE 2の論理的整合性
    print("\n📊 GATE 2: シナリオ選定ゲートの論理的整合性")
    gate2_patterns = gate2_config['patterns']
    
    for pattern_name, pattern_config in gate2_patterns.items():
        print(f"\n🔸 パターン: {pattern_name}")
        
        if 'variants' in pattern_config:
            for variant_name, variant_config in pattern_config['variants'].items():
                print(f"  📋 バリアント: {variant_name}")
                
                # 環境条件の整合性チェック
                if 'environment_conditions' in variant_config:
                    env_conditions = variant_config['environment_conditions']
                    print(f"    - 環境条件: {env_conditions}")
                    
                    # GATE 1の環境名と整合性チェック
                    for env_condition in env_conditions:
                        if env_condition not in [v.get('environment', '') for p in gate1_patterns.values() for v in p.get('variants', {}).values()]:
                            print(f"    ❌ GATE 1に存在しない環境: {env_condition}")
                        else:
                            print(f"    ✅ GATE 1に存在する環境: {env_condition}")
                
                # 条件の整合性チェック
                if 'conditions' in variant_config:
                    for condition in variant_config['conditions']:
                        indicator_name = condition.get('indicator')
                        if indicator_name and indicator_name not in test_data:
                            print(f"    ❌ 未定義指標: {indicator_name}")
                        else:
                            print(f"    ✅ 指標存在: {indicator_name}")
    
    # 3. GATE 3の論理的整合性
    print("\n📊 GATE 3: トリガーゲートの論理的整合性")
    gate3_patterns = gate3_config['patterns']
    
    for pattern_name, pattern_config in gate3_patterns.items():
        print(f"\n🔸 パターン: {pattern_name}")
        
        # 環境制限の整合性チェック
        if 'allowed_environments' in pattern_config:
            allowed_envs = pattern_config['allowed_environments']
            print(f"  - 許可環境: {allowed_envs}")
            
            # GATE 1の環境名と整合性チェック
            gate1_envs = []
            for pattern_name, pattern_config in gate1_patterns.items():
                # GATE 1の構造: patterns > pattern_name > variant_name > environment
                for key, value in pattern_config.items():
                    if isinstance(value, dict) and 'environment' in value:
                        gate1_envs.append(value['environment'])
                    elif key == 'environment':
                        gate1_envs.append(value)
            
            print(f"  - GATE 1の環境名: {gate1_envs}")
            
            for allowed_env in allowed_envs:
                if allowed_env not in gate1_envs:
                    print(f"    ❌ GATE 1に存在しない環境: {allowed_env}")
                else:
                    print(f"    ✅ GATE 1に存在する環境: {allowed_env}")
        
        # サブパターンの整合性チェック
        for sub_pattern_name, sub_pattern_config in pattern_config.items():
            if sub_pattern_name not in ['name', 'description', 'allowed_environments']:
                print(f"  📋 サブパターン: {sub_pattern_name}")
                
                if 'conditions' in sub_pattern_config:
                    for condition in sub_pattern_config['conditions']:
                        indicator_name = condition.get('indicator')
                        if indicator_name and indicator_name not in test_data:
                            print(f"    ❌ 未定義指標: {indicator_name}")
                        else:
                            print(f"    ✅ 指標存在: {indicator_name}")
    
    # 4. 実際の評価テスト
    print("\n🚪 実際の評価テスト...")
    engine = ThreeGateEngine()
    
    try:
        result = await engine.evaluate("USDJPY=X", test_data)
        if result:
            print(f"✅ 評価結果:")
            print(f"  - GATE 1: {'合格' if result.gate1_passed else '不合格'}")
            print(f"  - GATE 2: {'合格' if result.gate2_passed else '不合格'}")
            print(f"  - GATE 3: {'合格' if result.gate3_passed else '不合格'}")
            print(f"  - シグナル: {result.signal_type if result.signal_type else 'なし'}")
            
            # 各GATEの詳細情報
            if hasattr(result, 'gate1_result') and result.gate1_result:
                print(f"  - GATE 1環境: {result.gate1_result.pattern}")
            if hasattr(result, 'gate2_result') and result.gate2_result:
                print(f"  - GATE 2シナリオ: {result.gate2_result.pattern}")
            if hasattr(result, 'gate3_result') and result.gate3_result:
                print(f"  - GATE 3トリガー: {result.gate3_result.pattern}")
        else:
            print("❌ 評価結果がNoneです")
    except Exception as e:
        print(f"❌ 評価エラー: {e}")
        import traceback
        traceback.print_exc()
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_logical_consistency())
