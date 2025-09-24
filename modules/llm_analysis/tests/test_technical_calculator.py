#!/usr/bin/env python3
"""
テクニカル指標計算器のテスト
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator


def create_sample_data(days: int = 30) -> pd.DataFrame:
    """サンプルデータの作成"""
    dates = pd.date_range(start=datetime.now() - timedelta(days=days), periods=days*24*12, freq='5min')
    
    # ランダムウォークで価格データを生成
    np.random.seed(42)
    base_price = 150.0
    returns = np.random.normal(0, 0.001, len(dates))
    prices = [base_price]
    
    for ret in returns[1:]:
        prices.append(prices[-1] * (1 + ret))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices,
        'high': [p * (1 + abs(np.random.normal(0, 0.002))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.002))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000, 10000, len(dates))
    })
    
    df.set_index('timestamp', inplace=True)
    return df


def test_technical_calculator():
    """テクニカル指標計算器のテスト"""
    print("🧪 テクニカル指標計算器のテスト開始")
    
    # ログレベルをINFOに設定（デバッグ情報を非表示）
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 計算器の初期化
    calculator = TechnicalIndicatorCalculator()
    
    # サンプルデータの作成
    print("📊 サンプルデータの作成...")
    sample_data = {
        '5m': create_sample_data(30),   # 1ヶ月分の5分足
        '15m': create_sample_data(30),  # 1ヶ月分の15分足
        '1h': create_sample_data(90),   # 3ヶ月分の1時間足
        '4h': create_sample_data(180),  # 6ヶ月分の4時間足
        '1d': create_sample_data(365),  # 1年分の日足
    }
    
    # 時間足別にリサンプリング
    for timeframe, df in sample_data.items():
        if timeframe == '5m':
            continue
        elif timeframe == '15m':
            sample_data[timeframe] = df.resample('15min').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '1h':
            sample_data[timeframe] = df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '4h':
            sample_data[timeframe] = df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
        elif timeframe == '1d':
            sample_data[timeframe] = df.resample('1D').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
    
    print(f"✅ サンプルデータ作成完了:")
    for tf, df in sample_data.items():
        print(f"  {tf}: {len(df)}件")
    
    # テクニカル指標の計算
    print("\n📈 テクニカル指標の計算...")
    try:
        result = calculator.calculate_all_indicators(sample_data)
        
        print("✅ テクニカル指標計算完了:")
        for timeframe, df in result.items():
            print(f"  {timeframe}: {len(df.columns)}個の指標")
            
            # 最新データの表示
            latest = df.iloc[-1]
            print(f"    最新価格: {latest['close']:.5f}")
            print(f"    トレンド: {latest.get('Trend_Direction', 'N/A')}")
            print(f"    モメンタム: {latest.get('Momentum_State', 'N/A')}")
            
            # 移動平均線の表示
            ema_columns = [col for col in df.columns if col.startswith('EMA_')]
            if ema_columns:
                print(f"    EMA: {len(ema_columns)}個")
                for ema_col in sorted(ema_columns):
                    ema_value = latest.get(ema_col, 0)
                    if ema_value != 0:
                        print(f"      {ema_col}: {ema_value:.5f}")
            
            # SMAの表示
            sma_columns = [col for col in df.columns if col.startswith('SMA_')]
            if sma_columns:
                print(f"    SMA: {len(sma_columns)}個")
                for sma_col in sorted(sma_columns):
                    sma_value = latest.get(sma_col, 0)
                    if sma_value != 0:
                        print(f"      {sma_col}: {sma_value:.5f}")
            
            # RSIの表示
            rsi_columns = [col for col in df.columns if col.startswith('RSI_')]
            if rsi_columns:
                print(f"    RSI: {len(rsi_columns)}個")
                for rsi_col in sorted(rsi_columns):
                    rsi_value = latest.get(rsi_col, 0)
                    if rsi_value != 0:
                        print(f"      {rsi_col}: {rsi_value:.2f}")
            
            # MACDの表示
            macd_columns = [col for col in df.columns if col.startswith('MACD')]
            if macd_columns:
                print(f"    MACD: {len(macd_columns)}個")
                for macd_col in sorted(macd_columns):
                    macd_value = latest.get(macd_col, 0)
                    if macd_value != 0:
                        print(f"      {macd_col}: {macd_value:.5f}")
            
            # ATRの表示
            atr_columns = [col for col in df.columns if col.startswith('ATR_')]
            if atr_columns:
                print(f"    ATR: {len(atr_columns)}個")
                for atr_col in sorted(atr_columns):
                    atr_value = latest.get(atr_col, 0)
                    if atr_value != 0:
                        print(f"      {atr_col}: {atr_value:.5f}")
            
            # Stochasticの表示
            stoch_columns = [col for col in df.columns if col.startswith('Stochastic_')]
            if stoch_columns:
                print(f"    Stochastic: {len(stoch_columns)}個")
                for stoch_col in sorted(stoch_columns):
                    stoch_value = latest.get(stoch_col, 0)
                    if stoch_value != 0:
                        print(f"      {stoch_col}: {stoch_value:.2f}")
            
            # Williams %Rの表示
            williams_value = latest.get('Williams_R', 0)
            if williams_value != 0:
                print(f"    Williams %R: {williams_value:.2f}")
            
            # Bollinger Bandsの表示
            bb_columns = [col for col in df.columns if col.startswith('BB_')]
            if bb_columns:
                print(f"    Bollinger Bands: {len(bb_columns)}個")
                for bb_col in sorted(bb_columns):
                    bb_value = latest.get(bb_col, 0)
                    if bb_value != 0:
                        print(f"      {bb_col}: {bb_value:.5f}")
            
            # ボリューム指標の表示
            volume_columns = [col for col in df.columns if col.startswith('Volume_')]
            if volume_columns:
                print(f"    Volume: {len(volume_columns)}個")
                for vol_col in sorted(volume_columns):
                    vol_value = latest.get(vol_col, 0)
                    if vol_value != 0:
                        try:
                            print(f"      {vol_col}: {float(vol_value):.0f}")
                        except (ValueError, TypeError):
                            print(f"      {vol_col}: {vol_value}")
            
            # フィボナッチ情報の表示
            fib_columns = [col for col in df.columns if col.startswith('Fib_')]
            if fib_columns:
                print(f"    フィボナッチ: {len(fib_columns)}個のレベル")
                fib_position = latest.get('Fibonacci_Position', 'N/A')
                print(f"    フィボナッチ位置: {fib_position}")
                
                # 主要フィボナッチレベルの表示
                for level in [0.236, 0.382, 0.5, 0.618, 0.786]:
                    fib_col = f'Fib_{level}'
                    if fib_col in df.columns:
                        fib_value = latest.get(fib_col, 0)
                        print(f"    Fib_{level}: {fib_value:.5f}")
            print()
        
        # 分析サマリーの取得
        print("📊 分析サマリー:")
        summary = calculator.get_analysis_summary(result)
        for timeframe, data in summary.items():
            print(f"  {timeframe}:")
            print(f"    トレンド: {data['trend_direction']}")
            print(f"    モメンタム: {data['momentum_state']}")
            print(f"    ボラティリティ: {data['volatility_state']}")
            print(f"    ボリューム: {data['volume_state']}")
            print()
        
        print("🎉 テスト完了: 全てのテクニカル指標が正常に計算されました！")
        return True
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_technical_calculator()
    if success:
        print("\n✅ 全てのテストが成功しました！")
    else:
        print("\n❌ テストが失敗しました。")
        sys.exit(1)
