#!/usr/bin/env python3
"""
GATE通過テストスクリプト
各GATEが通過できるかどうかを詳細にテストする
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

class GatePassageTester:
    def __init__(self):
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.three_gate_engine = ThreeGateEngine()
    
    def create_test_data_for_gate1_pass(self, base_price: float = 150.0) -> dict:
        """GATE 1通過用のテストデータを作成"""
        # 1d足データ（250日分）
        dates_1d = pd.date_range(start='2024-01-01', periods=250, freq='D')
        
        # 下降トレンドのデータを生成（GATE 1のdowntrend_reversalパターン用）
        prices_1d = []
        for i in range(250):
            # 初期は上昇、後半で下降に転換
            if i < 200:
                price = base_price + (i * 0.1)  # 上昇
            else:
                price = base_price + (200 * 0.1) - ((i - 200) * 0.2)  # 下降転換
            prices_1d.append(price)
        
        # 1d足のOHLCデータ
        data_1d = []
        for i, (date, price) in enumerate(zip(dates_1d, prices_1d)):
            volatility = 0.5
            high = price + np.random.uniform(0, volatility)
            low = price - np.random.uniform(0, volatility)
            open_price = prices_1d[i-1] if i > 0 else price
            
            data_1d.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': price,
                'volume': np.random.uniform(1000, 5000)
            })
        
        df_1d = pd.DataFrame(data_1d)
        df_1d.set_index('timestamp', inplace=True)
        
        # 他の時間足も同様に生成（簡略化）
        data_by_timeframe = {
            '1d': df_1d,
            '4h': df_1d.copy(),  # 簡略化のため同じデータを使用
            '1h': df_1d.copy(),
            '5m': df_1d.copy()
        }
        
        # テクニカル指標を計算
        indicators = self.technical_calculator.calculate_all_indicators(data_by_timeframe)
        
        # テストデータを構築
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
        
        # 指標データを追加
        for timeframe, df_indicators in indicators.items():
            if not df_indicators.empty:
                latest_indicators = df_indicators.iloc[-1].to_dict()
                for key, value in latest_indicators.items():
                    test_data[f"{timeframe}_{key}"] = value
        
        return test_data
    
    async def test_gate1_passage(self):
        """GATE 1通過テスト"""
        print("🚪 GATE 1 通過テスト")
        print("=" * 50)
        
        # GATE 1通過用のデータを作成
        test_data = self.create_test_data_for_gate1_pass()
        
        print(f"📊 テストデータ準備完了: {len(test_data)}個のデータポイント")
        
        # 主要指標を確認
        key_indicators = ['1d_close', '1d_EMA_200', '1d_MACD']
        print(f"\n📋 主要指標:")
        for indicator in key_indicators:
            if indicator in test_data:
                print(f"   {indicator}: {test_data[indicator]:.6f}")
            else:
                print(f"   ❌ {indicator}: 見つかりません")
        
        # GATE 1のみをテスト
        print(f"\n🔍 GATE 1 個別テスト:")
        gate1_result = await self.three_gate_engine._evaluate_gate1("USDJPY=X", test_data)
        
        if gate1_result:
            print(f"   ✅ GATE 1 合格")
            print(f"   パターン: {gate1_result.pattern}")
            print(f"   信頼度: {gate1_result.confidence:.2f}")
            print(f"   合格条件: {gate1_result.passed_conditions}")
            print(f"   不合格条件: {gate1_result.failed_conditions}")
            return gate1_result
        else:
            print(f"   ❌ GATE 1 不合格")
            return None
    
    async def test_gate2_passage(self, gate1_result):
        """GATE 2通過テスト"""
        print(f"\n🚪 GATE 2 通過テスト")
        print("=" * 50)
        
        # GATE 1通過用のデータを作成
        test_data = self.create_test_data_for_gate1_pass()
        
        # GATE 2をテスト
        print(f"🔍 GATE 2 個別テスト:")
        gate2_result = await self.three_gate_engine._evaluate_gate2("USDJPY=X", test_data, gate1_result)
        
        print(f"   結果: {'✅ 合格' if gate2_result.valid else '❌ 不合格'}")
        print(f"   パターン: {gate2_result.pattern}")
        print(f"   信頼度: {gate2_result.confidence:.2f}")
        print(f"   合格条件: {gate2_result.passed_conditions}")
        print(f"   不合格条件: {gate2_result.failed_conditions}")
        
        # 詳細情報を表示
        if 'evaluated_scenarios' in gate2_result.additional_data:
            evaluated_scenarios = gate2_result.additional_data['evaluated_scenarios']
            print(f"\n📋 評価されたシナリオ詳細:")
            for i, scenario in enumerate(evaluated_scenarios, 1):
                status = "✅" if scenario['valid'] else "❌"
                print(f"   {i}. {status} {scenario['name']} (信頼度: {scenario['confidence']:.2f})")
                if 'condition_details' in scenario:
                    print(f"      条件詳細: {scenario['condition_details']}")
        
        return gate2_result
    
    async def test_gate3_passage(self, gate2_result):
        """GATE 3通過テスト"""
        print(f"\n🚪 GATE 3 通過テスト")
        print("=" * 50)
        
        # GATE 1通過用のデータを作成
        test_data = self.create_test_data_for_gate1_pass()
        
        # GATE 3をテスト
        print(f"🔍 GATE 3 個別テスト:")
        gate3_result = await self.three_gate_engine._evaluate_gate3("USDJPY=X", test_data, gate2_result)
        
        print(f"   結果: {'✅ 合格' if gate3_result.valid else '❌ 不合格'}")
        print(f"   パターン: {gate3_result.pattern}")
        print(f"   信頼度: {gate3_result.confidence:.2f}")
        print(f"   合格条件: {gate3_result.passed_conditions}")
        print(f"   不合格条件: {gate3_result.failed_conditions}")
        
        return gate3_result
    
    async def test_full_gate_passage(self):
        """全GATE通過テスト"""
        print("🚀 全GATE通過テスト開始")
        print("=" * 60)
        
        # GATE 1テスト
        gate1_result = await self.test_gate1_passage()
        if not gate1_result:
            print("❌ GATE 1で不合格のため、テスト終了")
            return
        
        # GATE 2テスト
        gate2_result = await self.test_gate2_passage(gate1_result)
        if not gate2_result.valid:
            print("❌ GATE 2で不合格のため、GATE 3テストをスキップ")
            return
        
        # GATE 3テスト
        gate3_result = await self.test_gate3_passage(gate2_result)
        
        # 最終結果
        print(f"\n🎯 最終結果:")
        print(f"   GATE 1: {'✅ 合格' if gate1_result else '❌ 不合格'}")
        print(f"   GATE 2: {'✅ 合格' if gate2_result.valid else '❌ 不合格'}")
        print(f"   GATE 3: {'✅ 合格' if gate3_result.valid else '❌ 不合格'}")
        
        if gate3_result.valid:
            print(f"   🎉 全GATE通過！シグナル生成可能")
        else:
            print(f"   ❌ 全GATE通過せず")

async def main():
    """メイン関数"""
    tester = GatePassageTester()
    
    try:
        await tester.test_full_gate_passage()
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
