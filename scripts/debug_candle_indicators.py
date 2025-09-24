#!/usr/bin/env python3
"""
ローソク足分析指標の計算をデバッグするスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def debug_candle_indicators():
    """ローソク足分析指標の計算をデバッグ"""
    
    print("🔍 ローソク足分析指標デバッグ開始")
    
    # データベース接続
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # 最新の価格データを取得（より多くのデータ）
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
            print(f"   最新: {tf_data['timestamp'].max()}")
            print(f"   最古: {tf_data['timestamp'].min()}")
        else:
            print(f"❌ {tf}足: データなし")
    
    # テクニカル指標計算
    print("\n📊 テクニカル指標計算中...")
    calculator = TechnicalIndicatorCalculator()
    
    all_indicators = {}
    for tf, data in timeframe_data.items():
        print(f"\n⏰ {tf}足の指標計算中...")
        print(f"   データ期間: {data['timestamp'].min()} ～ {data['timestamp'].max()}")
        print(f"   データ数: {len(data)}")
        
        # 個別にローソク足分析指標を計算
        print("   🔸 ローソク足分析指標を計算中...")
        candle_indicators = calculator._calculate_candle_analysis_indicators(data)
        
        # 計算されたローソク足指標を表示
        candle_cols = [col for col in candle_indicators.columns if 'candle' in col.lower() or 'body' in col.lower() or 'shadow' in col.lower()]
        print(f"   ✅ ローソク足指標: {len(candle_cols)}個")
        for col in candle_cols:
            latest_value = candle_indicators[col].iloc[-1] if not candle_indicators[col].isna().all() else "NaN"
            print(f"      - {col}: {latest_value}")
        
        # 全指標を計算
        indicators = calculator.calculate_all_indicators({tf: data})
        all_indicators.update(indicators)
        print(f"   ✅ 全指標: {len(indicators)}個")
    
    # 利用可能なローソク足関連指標を表示
    print(f"\n📋 利用可能なローソク足関連指標:")
    candle_indicators = [k for k in all_indicators.keys() if 'candle' in k.lower() or 'body' in k.lower() or 'shadow' in k.lower()]
    if candle_indicators:
        for indicator in candle_indicators:
            print(f"  - {indicator}: {all_indicators[indicator]}")
    else:
        print("  ❌ ローソク足関連指標が見つかりません")
    
    # 利用可能な全指標を表示（最初の20個）
    print(f"\n📋 利用可能な全指標（最初の20個）:")
    all_indicator_names = list(all_indicators.keys())
    for i, indicator in enumerate(all_indicator_names[:20]):
        print(f"  {i+1:2d}. {indicator}: {all_indicators[indicator]}")
    
    if len(all_indicator_names) > 20:
        print(f"  ... 他 {len(all_indicator_names) - 20}個の指標")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(debug_candle_indicators())
