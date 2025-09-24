#!/usr/bin/env python3
"""
GATE 3の条件詳細が空になる問題をデバッグするスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import yaml
from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.data_persistence.core.database import DatabaseConnectionManager

async def debug_gate3_conditions():
    """GATE 3の条件評価をデバッグ"""
    
    print("🔍 GATE 3条件デバッグ開始")
    
    # データベース接続
    from modules.data_persistence.config.settings import DatabaseConfig
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
    LIMIT 250
    """
    
    result = await db_manager.execute_query(query)
    if not result:
        print("❌ 価格データが見つかりません")
        return
    
    # データをDataFrameに変換
    import pandas as pd
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
    
    # GATE 3パターン設定を読み込み
    print("\n📋 GATE 3パターン設定読み込み中...")
    with open('/app/modules/llm_analysis/config/gate3_patterns.yaml', 'r', encoding='utf-8') as f:
        gate3_config = yaml.safe_load(f)
    
    patterns = gate3_config['patterns']
    print(f"✅ {len(patterns)}個のパターンを読み込み")
    
    # 各パターンの条件をチェック
    for pattern_name, pattern_config in patterns.items():
        print(f"\n🔍 パターン: {pattern_name}")
        
        if 'pinbar_pattern' in pattern_config:
            print("  📊 pinbar_pattern の条件をチェック...")
            for variant_name, variant_config in pattern_config['pinbar_pattern'].items():
                print(f"    🔸 {variant_name}:")
                if 'conditions' in variant_config:
                    for condition in variant_config['conditions']:
                        indicator_name = condition.get('indicator')
                        print(f"      - 指標: {indicator_name}")
                        
                        # 指標が存在するかチェック
                        if indicator_name in all_indicators:
                            value = all_indicators[indicator_name]
                            print(f"        ✅ 存在: {value}")
                        else:
                            print(f"        ❌ 存在しない")
                            
                            # 類似の指標を探す
                            similar_indicators = [k for k in all_indicators.keys() if indicator_name.lower() in k.lower() or k.lower() in indicator_name.lower()]
                            if similar_indicators:
                                print(f"        💡 類似指標: {similar_indicators[:3]}")
        
        if 'engulfing_pattern' in pattern_config:
            print("  📊 engulfing_pattern の条件をチェック...")
            for variant_name, variant_config in pattern_config['engulfing_pattern'].items():
                print(f"    🔸 {variant_name}:")
                if 'conditions' in variant_config:
                    for condition in variant_config['conditions']:
                        indicator_name = condition.get('indicator')
                        print(f"      - 指標: {indicator_name}")
                        
                        # 指標が存在するかチェック
                        if indicator_name in all_indicators:
                            value = all_indicators[indicator_name]
                            print(f"        ✅ 存在: {value}")
                        else:
                            print(f"        ❌ 存在しない")
                            
                            # 類似の指標を探す
                            similar_indicators = [k for k in all_indicators.keys() if indicator_name.lower() in k.lower() or k.lower() in indicator_name.lower()]
                            if similar_indicators:
                                print(f"        💡 類似指標: {similar_indicators[:3]}")
        
        if 'uptrend_momentum' in pattern_config:
            print("  📊 uptrend_momentum の条件をチェック...")
            for variant_name, variant_config in pattern_config['uptrend_momentum'].items():
                print(f"    🔸 {variant_name}:")
                if 'conditions' in variant_config:
                    for condition in variant_config['conditions']:
                        indicator_name = condition.get('indicator')
                        print(f"      - 指標: {indicator_name}")
                        
                        # 指標が存在するかチェック
                        if indicator_name in all_indicators:
                            value = all_indicators[indicator_name]
                            print(f"        ✅ 存在: {value}")
                        else:
                            print(f"        ❌ 存在しない")
                            
                            # 類似の指標を探す
                            similar_indicators = [k for k in all_indicators.keys() if indicator_name.lower() in k.lower() or k.lower() in indicator_name.lower()]
                            if similar_indicators:
                                print(f"        💡 類似指標: {similar_indicators[:3]}")
    
    # 利用可能なローソク足関連指標を表示
    print(f"\n📋 利用可能なローソク足関連指標:")
    candle_indicators = [k for k in all_indicators.keys() if 'candle' in k.lower() or 'body' in k.lower() or 'shadow' in k.lower()]
    for indicator in candle_indicators:
        print(f"  - {indicator}: {all_indicators[indicator]}")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(debug_gate3_conditions())
