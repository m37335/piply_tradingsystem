#!/usr/bin/env python3
"""
GATE 2評価の詳細デバッグスクリプト
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

class Gate2Debugger:
    def __init__(self):
        self.technical_calculator = TechnicalIndicatorCalculator()
        self.three_gate_engine = ThreeGateEngine()
    
    def create_test_data(self, base_price: float = 150.0) -> dict:
        """テストデータを作成"""
        # 1d足データ（250日分）
        dates_1d = pd.date_range(start='2024-01-01', periods=250, freq='D')
        
        # 下降トレンドのデータを生成
        prices_1d = []
        for i in range(250):
            if i < 200:
                price = base_price + (i * 0.1)
            else:
                price = base_price + (200 * 0.1) - ((i - 200) * 0.2)
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
        
        # 他の時間足も同様に生成
        data_by_timeframe = {
            '1d': df_1d,
            '4h': df_1d.copy(),
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
    
    async def debug_gate2_evaluation(self):
        """GATE 2評価をデバッグ"""
        print("🔍 GATE 2 評価デバッグ")
        print("=" * 50)
        
        # テストデータを作成
        test_data = self.create_test_data()
        
        # GATE 1を実行
        gate1_result = await self.three_gate_engine._evaluate_gate1("USDJPY=X", test_data)
        print(f"GATE 1結果: {gate1_result.pattern if gate1_result else 'None'}")
        
        # GATE 2のパターン設定を確認
        patterns = self.three_gate_engine.pattern_loader.load_gate_patterns(2)
        print(f"\n📋 GATE 2パターン設定:")
        print(f"   パターン数: {len(patterns.get('patterns', {}))}")
        for pattern_name in patterns.get('patterns', {}).keys():
            print(f"   - {pattern_name}")
        
        # 環境マッピングを確認
        env_mapping = patterns.get('environment_mapping', {})
        print(f"\n🗺️ 環境マッピング:")
        for env, scenarios in env_mapping.items():
            print(f"   {env}: {scenarios}")
        
        # 有効なシナリオを確認
        if gate1_result:
            valid_scenarios = self.three_gate_engine._get_valid_scenarios_for_environment(
                gate1_result.pattern, patterns
            )
            print(f"\n✅ 有効なシナリオ ({gate1_result.pattern}):")
            for scenario in valid_scenarios:
                print(f"   - {scenario}")
        
        # first_pullbackの詳細を確認
        if 'first_pullback' in patterns.get('patterns', {}):
            first_pullback_config = patterns['patterns']['first_pullback']
            print(f"\n🔍 first_pullback設定:")
            print(f"   名前: {first_pullback_config.get('name', 'N/A')}")
            
            env_conditions = first_pullback_config.get('environment_conditions', {})
            print(f"   環境条件数: {len(env_conditions)}")
            
            for env, config in env_conditions.items():
                print(f"   環境 '{env}':")
                conditions = config.get('conditions', [])
                print(f"     条件数: {len(conditions)}")
                for i, condition in enumerate(conditions):
                    print(f"     {i+1}. {condition.get('name', 'N/A')}")
                    print(f"        指標: {condition.get('indicator', 'N/A')}")
                    print(f"        演算子: {condition.get('operator', 'N/A')}")
                    print(f"        参照: {condition.get('reference', 'N/A')}")
                    print(f"        時間足: {condition.get('timeframe', 'N/A')}")
                    print(f"        重み: {condition.get('weight', 'N/A')}")
        
        # 実際のGATE 2評価を実行
        print(f"\n🚪 GATE 2評価実行:")
        if gate1_result:
            gate2_result = await self.three_gate_engine._evaluate_gate2("USDJPY=X", test_data, gate1_result)
            print(f"   結果: {'✅ 合格' if gate2_result.valid else '❌ 不合格'}")
            print(f"   パターン: {gate2_result.pattern}")
            print(f"   信頼度: {gate2_result.confidence:.2f}")
            
            # 詳細情報を表示
            if 'evaluated_scenarios' in gate2_result.additional_data:
                evaluated_scenarios = gate2_result.additional_data['evaluated_scenarios']
                print(f"   評価されたシナリオ数: {len(evaluated_scenarios)}")
                for i, scenario in enumerate(evaluated_scenarios, 1):
                    print(f"   {i}. {scenario['name']} (有効: {scenario['valid']}, 信頼度: {scenario['confidence']:.2f})")
                    if 'condition_details' in scenario:
                        print(f"      条件詳細: {scenario['condition_details']}")

async def main():
    """メイン関数"""
    debugger = Gate2Debugger()
    
    try:
        await debugger.debug_gate2_evaluation()
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
