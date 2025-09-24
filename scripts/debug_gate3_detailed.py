#!/usr/bin/env python3
"""
GATE 3の条件評価の詳細デバッグスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def debug_gate3_detailed():
    """GATE 3の条件評価を詳細デバッグ"""
    
    print("🔍 GATE 3詳細デバッグ開始")
    
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
    
    # ThreeGateEngineでGATE 3をテスト
    print("\n🚪 GATE 3テスト開始...")
    engine = ThreeGateEngine()
    
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
    
    # GATE 3の条件を手動でテスト
    print("\n🔍 GATE 3条件の手動テスト...")
    
    # ローソク足分析指標をチェック
    candle_indicators = ['candle_body', 'candle_upper_shadow', 'candle_lower_shadow', 'candle_bullish', 'candle_bearish']
    for indicator in candle_indicators:
        if indicator in test_data:
            print(f"✅ {indicator}: {test_data[indicator]}")
        else:
            print(f"❌ {indicator}: 見つからない")
    
    # GATE 3の条件を直接テスト
    print("\n🔍 GATE 3条件の直接テスト...")
    
    # price_action_reversalパターンの条件をテスト
    print("📊 price_action_reversal パターンの条件テスト:")
    
    # uptrend_pinbar条件
    print("  🔸 uptrend_pinbar:")
    
    # long_lower_shadow条件
    candle_lower_shadow = test_data.get('candle_lower_shadow', None)
    candle_body = test_data.get('candle_body', None)
    if candle_lower_shadow is not None and candle_body is not None:
        long_lower_shadow = candle_lower_shadow > (candle_body * 2.0)
        print(f"    - long_lower_shadow: {candle_lower_shadow} > {candle_body * 2.0} = {long_lower_shadow}")
    else:
        print(f"    - long_lower_shadow: データ不足 (candle_lower_shadow={candle_lower_shadow}, candle_body={candle_body})")
    
    # small_upper_shadow条件
    candle_upper_shadow = test_data.get('candle_upper_shadow', None)
    if candle_upper_shadow is not None and candle_body is not None:
        small_upper_shadow = candle_upper_shadow < (candle_body * 0.5)
        print(f"    - small_upper_shadow: {candle_upper_shadow} < {candle_body * 0.5} = {small_upper_shadow}")
    else:
        print(f"    - small_upper_shadow: データ不足 (candle_upper_shadow={candle_upper_shadow}, candle_body={candle_body})")
    
    # near_support条件
    close = test_data.get('close', None)
    print(f"    - near_support: close={close} (scenario_supportは未定義)")
    
    # ThreeGateEngineで実際の評価をテスト
    print("\n🚪 ThreeGateEngineでの実際の評価テスト...")
    
    try:
        result = await engine.evaluate("USDJPY=X", test_data)
        print(f"✅ 評価結果: {result}")
        if result:
            print(f"  - GATE 1: {'合格' if result.gate1_passed else '不合格'}")
            print(f"  - GATE 2: {'合格' if result.gate2_passed else '不合格'}")
            print(f"  - GATE 3: {'合格' if result.gate3_passed else '不合格'}")
            print(f"  - シグナル: {result.signal_type if result.signal_type else 'なし'}")
    except Exception as e:
        print(f"❌ 評価エラー: {e}")
        import traceback
        traceback.print_exc()
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(debug_gate3_detailed())
