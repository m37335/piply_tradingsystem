#!/usr/bin/env python3
"""
TechnicalIndicatorCalculatorのデバッグスクリプト
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def debug_technical_calculator():
    """TechnicalIndicatorCalculatorのデバッグ"""
    
    print("🔍 TechnicalIndicatorCalculatorデバッグ開始")
    print("=" * 60)
    
    # データベース接続
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # 1d足のデータを取得
    print("\n📊 1d足のデータ取得:")
    print("-" * 40)
    
    query = """
    SELECT symbol, timeframe, timestamp, open, high, low, close, volume
    FROM price_data 
    WHERE symbol = 'USDJPY=X' AND timeframe = '1d'
    ORDER BY timestamp ASC
    LIMIT 10
    """
    
    result = await db_manager.execute_query(query)
    if result:
        df = pd.DataFrame(result, columns=['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        print(f"取得データ: {len(df)}件")
        print(f"期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")
        print(f"価格範囲: {df['close'].min():.5f} ～ {df['close'].max():.5f}")
        print(f"データサンプル:")
        print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].head())
    
    # 全1d足データを取得
    print("\n📊 全1d足データの取得:")
    print("-" * 40)
    
    query = """
    SELECT symbol, timeframe, timestamp, open, high, low, close, volume
    FROM price_data 
    WHERE symbol = 'USDJPY=X' AND timeframe = '1d'
    ORDER BY timestamp ASC
    """
    
    result = await db_manager.execute_query(query)
    if result:
        df_full = pd.DataFrame(result, columns=['symbol', 'timeframe', 'timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df_full['timestamp'] = pd.to_datetime(df_full['timestamp'])
        
        print(f"全データ: {len(df_full)}件")
        print(f"期間: {df_full['timestamp'].min()} ～ {df_full['timestamp'].max()}")
        
        # TechnicalIndicatorCalculatorで計算
        print("\n📊 TechnicalIndicatorCalculatorでの計算:")
        print("-" * 40)
        
        calculator = TechnicalIndicatorCalculator()
        
        # 1d足のみで計算
        indicators = calculator.calculate_all_indicators({'1d': df_full})
        
        if '1d' in indicators:
            df_with_indicators = indicators['1d']
            print(f"計算結果: {len(df_with_indicators)}行, {len(df_with_indicators.columns)}列")
            
            # 最新の指標値を確認
            latest_row = df_with_indicators.iloc[-1]
            print(f"\n最新の指標値:")
            
            important_indicators = ['EMA_200', 'EMA_55', 'EMA_21', 'MACD', 'MACD_Signal', 'RSI_14', 'ADX']
            
            for indicator in important_indicators:
                if indicator in df_with_indicators.columns:
                    value = latest_row[indicator]
                    if pd.notna(value):
                        print(f"  ✅ {indicator}: {value}")
                    else:
                        print(f"  ❌ {indicator}: NaN")
                else:
                    print(f"  ❌ {indicator}: 列が存在しません")
            
            # データの最初と最後を確認
            print(f"\nデータの最初の5行:")
            print(df_with_indicators[['timestamp', 'close', 'EMA_200', 'MACD', 'RSI_14']].head())
            
            print(f"\nデータの最後の5行:")
            print(df_with_indicators[['timestamp', 'close', 'EMA_200', 'MACD', 'RSI_14']].tail())
            
            # NaNの原因を調査
            print(f"\nNaNの原因調査:")
            print(f"  - EMA_200のNaN数: {df_with_indicators['EMA_200'].isna().sum()}")
            print(f"  - MACDのNaN数: {df_with_indicators['MACD'].isna().sum()}")
            print(f"  - RSI_14のNaN数: {df_with_indicators['RSI_14'].isna().sum()}")
            
            # 最初の非NaN値を確認
            for indicator in important_indicators:
                if indicator in df_with_indicators.columns:
                    first_valid = df_with_indicators[indicator].first_valid_index()
                    if first_valid is not None:
                        print(f"  - {indicator}の最初の有効値: 行{first_valid} = {df_with_indicators.loc[first_valid, indicator]}")
                    else:
                        print(f"  - {indicator}: 有効値なし")
    
    await db_manager.close()
    
    print("\n" + "=" * 60)
    print("🔍 TechnicalIndicatorCalculatorデバッグ完了")

if __name__ == "__main__":
    asyncio.run(debug_technical_calculator())
