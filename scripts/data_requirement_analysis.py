#!/usr/bin/env python3
"""
データ要件分析スクリプト
各GATEで必要な最小データ量を分析
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def analyze_data_requirements():
    """データ要件分析"""
    
    print("📊 データ要件分析開始")
    print("=" * 60)
    
    # データベース接続
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # 各時間足のデータ量を確認
    timeframes = ['1d', '4h', '1h', '5m']
    
    print("\n📊 各時間足のデータ量分析:")
    print("-" * 40)
    
    for tf in timeframes:
        query = f"""
        SELECT COUNT(*) as count, 
               MIN(timestamp) as earliest, 
               MAX(timestamp) as latest
        FROM price_data 
        WHERE symbol = 'USDJPY=X' AND timeframe = '{tf}'
        """
        
        result = await db_manager.execute_query(query)
        if result:
            count, earliest, latest = result[0]
            print(f"  {tf}足: {count}件")
            print(f"    - 期間: {earliest} ～ {latest}")
            
            # 必要な最小データ量をチェック
            required_periods = {
                '1d': 250,  # EMA_200 + バッファ
                '4h': 100,  # EMA_55 + バッファ
                '1h': 100,  # EMA_55 + バッファ
                '5m': 250   # EMA_200 + バッファ
            }
            
            if count < required_periods[tf]:
                print(f"    ❌ 不足: {required_periods[tf] - count}件")
            else:
                print(f"    ✅ 十分: {count - required_periods[tf]}件の余裕")
    
    # 各指標の計算に必要な最小データ量
    print("\n📊 指標計算に必要な最小データ量:")
    print("-" * 40)
    
    indicators_requirements = {
        'EMA_200': 200,
        'EMA_55': 55,
        'EMA_21': 21,
        'SMA_200': 200,
        'SMA_50': 50,
        'SMA_20': 20,
        'MACD': 26,  # 12 + 14
        'RSI_14': 14,
        'ADX': 14,
        'Stochastic': 14,
        'Bollinger_Bands': 20,
        'ATR_14': 14
    }
    
    for indicator, required in indicators_requirements.items():
        print(f"  {indicator}: {required}期間")
    
    # 現在のデータで計算可能な指標を確認
    print("\n📊 現在のデータで計算可能な指標:")
    print("-" * 40)
    
    for tf in timeframes:
        query = f"""
        SELECT COUNT(*) as count
        FROM price_data 
        WHERE symbol = 'USDJPY=X' AND timeframe = '{tf}'
        """
        
        result = await db_manager.execute_query(query)
        if result:
            count = result[0][0]
            print(f"\n  {tf}足 ({count}件):")
            
            for indicator, required in indicators_requirements.items():
                if count >= required:
                    print(f"    ✅ {indicator}")
                else:
                    print(f"    ❌ {indicator} (必要: {required}, 現在: {count})")
    
    # 推奨される最小データ量
    print("\n📊 推奨される最小データ量:")
    print("-" * 40)
    
    recommendations = {
        '1d': 300,  # 1年分 + バッファ
        '4h': 200,  # 約1ヶ月分 + バッファ
        '1h': 200,  # 約1週間分 + バッファ
        '5m': 300   # 約1日分 + バッファ
    }
    
    for tf, recommended in recommendations.items():
        query = f"""
        SELECT COUNT(*) as count
        FROM price_data 
        WHERE symbol = 'USDJPY=X' AND timeframe = '{tf}'
        """
        
        result = await db_manager.execute_query(query)
        if result:
            count = result[0][0]
            if count >= recommended:
                print(f"  {tf}足: ✅ {count}件 (推奨: {recommended}件)")
            else:
                print(f"  {tf}足: ❌ {count}件 (推奨: {recommended}件) - 不足: {recommended - count}件")
    
    await db_manager.close()
    
    print("\n" + "=" * 60)
    print("📊 データ要件分析完了")

if __name__ == "__main__":
    asyncio.run(analyze_data_requirements())
