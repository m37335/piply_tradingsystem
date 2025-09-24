#!/usr/bin/env python3
"""
GATE 3の条件詳細が空になる問題の詳細デバッグ
"""

import sys
import os
sys.path.append('/app')

import asyncio
import pandas as pd
from modules.llm_analysis.core.three_gate_engine import ThreeGateEngine
from modules.llm_analysis.services.three_gate_analysis_service import ThreeGateAnalysisService
from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database import DatabaseConnectionManager

async def debug_gate3_condition_details():
    """GATE 3の条件詳細が空になる問題の詳細デバッグ"""
    
    print("🔍 GATE 3条件詳細デバッグ開始")
    print("=" * 60)
    
    # データベース接続
    config = DatabaseConfig()
    db_manager = DatabaseConnectionManager(config.connection_string)
    await db_manager.initialize()
    
    # ThreeGateEngineのインスタンス作成
    engine = ThreeGateEngine()
    
    # ThreeGateAnalysisServiceのインスタンス作成
    service = ThreeGateAnalysisService(engine, db_manager)
    
    # テクニカル指標の計算
    print("\n📊 テクニカル指標計算:")
    print("-" * 40)
    
    indicators = await service._calculate_technical_indicators("USDJPY=X")
    
    if not indicators:
        print("❌ テクニカル指標計算失敗")
        return
    
    print(f"✅ テクニカル指標計算成功: {len(indicators)}個の指標")
    
    # GATE 3の設定を確認
    print("\n📋 GATE 3設定の確認:")
    print("-" * 40)
    
    import yaml
    with open('/app/modules/llm_analysis/config/gate3_patterns.yaml', 'r', encoding='utf-8') as f:
        gate3_config = yaml.safe_load(f)
    
    gate3_patterns = gate3_config['patterns']
    
    for pattern_name, pattern_config in gate3_patterns.items():
        print(f"\n🔸 パターン: {pattern_name}")
        
        if 'allowed_environments' in pattern_config:
            print(f"  - 許可環境: {pattern_config['allowed_environments']}")
        
        # サブパターンの詳細確認
        for sub_pattern_name, sub_pattern_config in pattern_config.items():
            if sub_pattern_name not in ['name', 'description', 'allowed_environments']:
                print(f"  - サブパターン: {sub_pattern_name}")
                if 'conditions' in sub_pattern_config:
                    print(f"    * 条件数: {len(sub_pattern_config['conditions'])}")
                    for condition in sub_pattern_config['conditions']:
                        indicator_name = condition.get('indicator')
                        operator = condition.get('operator')
                        reference = condition.get('reference', condition.get('value', 'N/A'))
                        
                        print(f"      - {condition.get('name', 'N/A')}: {indicator_name} {operator} {reference}")
                        
                        # 指標の存在確認
                        if indicator_name:
                            found = False
                            for key in indicators.keys():
                                if indicator_name in key:
                                    print(f"        ✅ 指標存在: {key} = {indicators[key]}")
                                    found = True
                                    break
                            if not found:
                                print(f"        ❌ 指標不存在: {indicator_name}")
    
    # GATE 3の手動評価テスト
    print("\n🚪 GATE 3手動評価テスト:")
    print("-" * 40)
    
    try:
        # GATE 1とGATE 2の結果を模擬
        gate1_environment = "trend_reversal_downtrend_reversal"
        
        # GATE 2の結果を模擬
        from modules.llm_analysis.core.three_gate_engine import GateResult
        from datetime import datetime, timezone
        gate2_result = GateResult(
            pattern="first_pullback_trend_reversal",
            valid=True,
            confidence=1.0,
            passed_conditions=["retest_ema", "momentum_alignment"],
            failed_conditions=[],
            additional_data={'gate1_environment': gate1_environment},
            timestamp=datetime.now(timezone.utc)
        )
        
        # GATE 3の評価を直接実行
        gate3_result = await engine._evaluate_gate3("USDJPY=X", indicators, gate2_result)
        
        if gate3_result:
            print(f"✅ GATE 3評価成功")
            print(f"  - パターン: {gate3_result.pattern}")
            print(f"  - 有効: {gate3_result.valid}")
            print(f"  - 信頼度: {gate3_result.confidence}")
            
            if hasattr(gate3_result, 'additional_data') and 'condition_details' in gate3_result.additional_data:
                condition_details = gate3_result.additional_data['condition_details']
                print(f"  - 条件詳細: {condition_details}")
                
                if condition_details:
                    print(f"    ✅ 条件詳細が存在します")
                else:
                    print(f"    ❌ 条件詳細が空です")
            else:
                print(f"  - 条件詳細: なし")
        else:
            print(f"❌ GATE 3評価失敗")
            
    except Exception as e:
        print(f"❌ GATE 3評価エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # 個別の条件評価テスト
    print("\n🔍 個別条件評価テスト:")
    print("-" * 40)
    
    # GATE 3の条件を個別にテスト
    for pattern_name, pattern_config in gate3_patterns.items():
        print(f"\n🔸 パターン: {pattern_name}")
        
        for sub_pattern_name, sub_pattern_config in pattern_config.items():
            if sub_pattern_name not in ['name', 'description', 'allowed_environments'] and 'conditions' in sub_pattern_config:
                print(f"  - サブパターン: {sub_pattern_name}")
                
                for condition in sub_pattern_config['conditions']:
                    condition_name = condition.get('name', 'N/A')
                    indicator_name = condition.get('indicator')
                    operator = condition.get('operator')
                    reference = condition.get('reference', condition.get('value', 'N/A'))
                    
                    print(f"    * 条件: {condition_name}")
                    print(f"      - 指標: {indicator_name}")
                    print(f"      - 演算子: {operator}")
                    print(f"      - 参照値: {reference}")
                    
                    # 指標値の取得
                    if indicator_name:
                        indicator_value = None
                        for key in indicators.keys():
                            if indicator_name in key:
                                indicator_value = indicators[key]
                                break
                        
                        if indicator_value is not None:
                            print(f"      - 指標値: {indicator_value}")
                            
                            # 条件評価のテスト
                            try:
                                from modules.llm_analysis.core.three_gate_engine import ConditionEvaluator
                                evaluator = ConditionEvaluator()
                                
                                # 条件評価の実行
                                score = await evaluator.evaluate_condition(indicators, condition)
                                print(f"      - 評価結果: スコア {score}")
                                
                            except Exception as e:
                                print(f"      - 評価エラー: {e}")
                        else:
                            print(f"      - 指標値: 取得失敗")
    
    await db_manager.close()
    
    print("\n" + "=" * 60)
    print("🔍 GATE 3条件詳細デバッグ完了")

if __name__ == "__main__":
    asyncio.run(debug_gate3_condition_details())
