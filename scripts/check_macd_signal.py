#!/usr/bin/env python3
"""
MACD_Signalの値を確認するスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def check_macd_signal():
    """MACD_Signalの値を確認"""
    
    print("🔍 MACD_Signal値確認開始")
    
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
    
    # MACD_Signalの値を確認
    print("\n🔍 MACD_Signal値の確認:")
    
    for tf in timeframes:
        if tf in all_indicators:
            df_with_indicators = all_indicators[tf]
            
            # MACD関連指標を確認
            macd_cols = [col for col in df_with_indicators.columns if 'MACD' in col]
            print(f"\n📊 {tf}足のMACD関連指標:")
            for col in macd_cols:
                latest_value = df_with_indicators[col].iloc[-1]
                print(f"  - {col}: {latest_value}")
            
            # MACDとMACD_Signalの比較
            if 'MACD' in df_with_indicators.columns and 'MACD_Signal' in df_with_indicators.columns:
                macd = df_with_indicators['MACD'].iloc[-1]
                macd_signal = df_with_indicators['MACD_Signal'].iloc[-1]
                print(f"  - MACD vs MACD_Signal: {macd} vs {macd_signal}")
                print(f"  - MACD > MACD_Signal: {macd > macd_signal}")
                print(f"  - MACD < MACD_Signal: {macd < macd_signal}")
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(check_macd_signal())
