#!/usr/bin/env python3
"""
テクニカル指標計算のデバッグスクリプト
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator

def create_test_data(periods: int = 250) -> pd.DataFrame:
    """テスト用のデータを生成"""
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='D')
    
    # 簡単な上昇トレンドデータ
    base_price = 150.0
    prices = []
    for i in range(periods):
        price = base_price + (i * 0.1) + np.random.normal(0, 0.5)
        prices.append(price)
    
    data = []
    for i, (date, price) in enumerate(zip(dates, prices)):
        volatility = 0.5
        high = price + np.random.uniform(0, volatility)
        low = price - np.random.uniform(0, volatility)
        open_price = prices[i-1] if i > 0 else price
        
        data.append({
            'timestamp': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': price,
            'volume': np.random.uniform(1000, 5000)
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df

def test_technical_calculator():
    """テクニカル指標計算をテスト"""
    print("🔧 テクニカル指標計算デバッグテスト")
    print("=" * 50)
    
    # テストデータを生成
    df_1d = create_test_data(250)
    print(f"📊 1d足データ: {len(df_1d)}件")
    print(f"   価格範囲: {df_1d['close'].min():.2f} - {df_1d['close'].max():.2f}")
    
    # テクニカル指標計算器を初期化
    calculator = TechnicalIndicatorCalculator()
    
    try:
        # 1d足の指標を計算
        print("\n📈 1d足の指標計算開始...")
        result_1d = calculator._calculate_timeframe_indicators(df_1d, '1d')
        
        print(f"✅ 1d足指標計算完了: {len(result_1d.columns)}個の指標")
        
        # 主要指標を確認
        key_indicators = ['EMA_200', 'MACD', 'MACD_Signal', 'ADX']
        for indicator in key_indicators:
            if indicator in result_1d.columns:
                latest_value = result_1d[indicator].iloc[-1]
                print(f"   {indicator}: {latest_value:.6f}")
            else:
                print(f"   ❌ {indicator}: 見つかりません")
        
        # 全指標を計算
        print("\n📊 全時間足の指標計算開始...")
        all_indicators = calculator.calculate_all_indicators({'1d': df_1d})
        
        print(f"✅ 全指標計算完了: {len(all_indicators)}個の指標")
        
        # 指標名を表示
        print("\n📋 計算された指標:")
        for i, indicator_name in enumerate(sorted(all_indicators.keys())):
            if i < 20:  # 最初の20個のみ表示
                value = all_indicators[indicator_name]
                if isinstance(value, (int, float)):
                    print(f"   {indicator_name}: {value:.6f}")
                else:
                    print(f"   {indicator_name}: {type(value).__name__}")
            elif i == 20:
                print(f"   ... 他{len(all_indicators) - 20}個の指標")
                break
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_technical_calculator()
