#!/usr/bin/env python3
"""
単一シナリオの詳細テスト
"""

import asyncio
import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.core.technical_calculator import TechnicalIndicatorCalculator

class SingleScenarioTester:
    def __init__(self):
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.three_gate_engine = ThreeGateEngine()
    
    def generate_trending_bullish_data(self, base_price: float = 150.0, periods: int = 250) -> pd.DataFrame:
        """上昇トレンドのデータを生成"""
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='D')
        
        # 上昇トレンド + ノイズ
        trend = np.linspace(0, 0.005, periods)  # 0.5%上昇
        noise = np.random.normal(0, 0.0001, periods)  # 0.01%のノイズ
        price_changes = trend + noise
        
        prices = [base_price]
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(new_price)
        
        # OHLCデータを生成
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            volatility = 0.0005  # 0.05%のボラティリティ
            high = price * (1 + np.random.uniform(0, volatility))
            low = price * (1 - np.random.uniform(0, volatility))
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
    
    async def test_single_scenario(self):
        """単一シナリオを詳細テスト"""
        print("🎯 上昇トレンド相場の詳細テスト")
        print("=" * 50)
        
        # 複数時間足のデータを生成
        data_by_timeframe = {}
        
        # 1d足データ（250日分 - EMA_200計算に必要）
        df_1d = self.generate_trending_bullish_data(150.0, 250)
        data_by_timeframe['1d'] = df_1d
        
        # 4h足データ（250時間分）
        df_4h = self.generate_trending_bullish_data(150.0, 250)
        data_by_timeframe['4h'] = df_4h
        
        # 1h足データ（250時間分）
        df_1h = self.generate_trending_bullish_data(150.0, 250)
        data_by_timeframe['1h'] = df_1h
        
        # 5m足データ（250分）
        df_5m = self.generate_trending_bullish_data(150.0, 250)
        data_by_timeframe['5m'] = df_5m
        
        print(f"📊 生成データ:")
        for timeframe, df in data_by_timeframe.items():
            print(f"   {timeframe}: {len(df)}件, 価格範囲: {df['close'].min():.5f} - {df['close'].max():.5f}")
        
        # テクニカル指標を計算
        print(f"\n📈 テクニカル指標計算中...")
        indicators = self.technical_calculator.calculate_all_indicators(data_by_timeframe)
        
        # 最新のデータポイントでテスト
        test_data = {}
        for timeframe, df in data_by_timeframe.items():
            latest_data = df.iloc[-1]
            test_data.update({
                f'{timeframe}_close': latest_data['close'],
                f'{timeframe}_open': latest_data['open'],
                f'{timeframe}_high': latest_data['high'],
                f'{timeframe}_low': latest_data['low'],
                f'{timeframe}_volume': latest_data['volume'],
            })
        
        # 指標データを追加（正しい形式で）
        for timeframe, df_indicators in indicators.items():
            if not df_indicators.empty:
                # 最新の指標値を取得
                latest_indicators = df_indicators.iloc[-1].to_dict()
                # 時間足プレフィックスを追加
                for key, value in latest_indicators.items():
                    test_data[f"{timeframe}_{key}"] = value
        
        print(f"✅ テストデータ準備完了: {len(test_data)}個のデータポイント")
        
        # 主要指標を確認
        print(f"\n📋 主要指標の確認:")
        key_indicators = [
            '1d_EMA_200', '1d_MACD', '1d_ADX', '1d_close',
            '4h_EMA_200', '4h_MACD', '4h_ADX', '4h_close',
            '1h_EMA_200', '1h_MACD', '1h_ADX', '1h_close',
            '5m_EMA_200', '5m_MACD', '5m_ADX', '5m_close'
        ]
        
        for indicator in key_indicators:
            if indicator in test_data:
                print(f"   {indicator}: {test_data[indicator]:.6f}")
            else:
                print(f"   ❌ {indicator}: 見つかりません")
        
        # GATE評価を実行
        print(f"\n🚪 GATE評価実行中...")
        result = await self.three_gate_engine.evaluate("USDJPY=X", test_data)
        
        print(f"\n📈 GATE評価結果:")
        if result:
            print(f"   GATE 1: {'✅ 合格' if result.gate1_passed else '❌ 不合格'}")
            print(f"   GATE 2: {'✅ 合格' if result.gate2_passed else '❌ 不合格'}")
            print(f"   GATE 3: {'✅ 合格' if result.gate3_passed else '❌ 不合格'}")
            print(f"   シグナル: {result.signal_type if result.signal_type else 'なし'}")
            print(f"   信頼度: {result.confidence:.2f}")
            if result.entry_price:
                print(f"   エントリー: {result.entry_price:.5f}")
                print(f"   ストップロス: {result.stop_loss:.5f}")
        else:
            print("   ❌ 評価失敗")
        
        return result

async def main():
    """メイン関数"""
    tester = SingleScenarioTester()
    
    try:
        await tester.test_single_scenario()
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
