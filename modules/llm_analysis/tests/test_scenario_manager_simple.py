"""
シナリオ管理システムの簡易テスト

主要機能のみをテストする。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.scenario_manager import (
    ScenarioManager, ScenarioStatus, ExitReason, TradeDirection
)
from modules.llm_analysis.core.rule_engine import EntrySignal, RuleResult


async def test_basic_functionality():
    """基本機能のテスト"""
    print("🧪 シナリオ管理システム基本機能テスト")
    
    manager = ScenarioManager()
    
    try:
        # ダミーエントリーシグナルの作成
        dummy_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="pullback_buy",
            confidence=0.85,
            entry_price=147.123,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=2.5,
            max_hold_time=240,
            rule_results=[
                RuleResult("RSI_14 <= 40", True, 0.9, "RSI: 38.5 ≤ 40", {}),
                RuleResult("price > EMA_200", True, 0.8, "Price: 147.123 > EMA_200: 146.800", {})
            ],
            technical_summary={"1h": {"price": 147.123, "rsi_14": 38.5}},
            created_at=datetime.now(timezone.utc)
        )
        
        # シナリオの作成
        scenario = await manager.create_scenario(dummy_signal)
        print(f"✅ シナリオ作成: {scenario.id} ({scenario.strategy})")
        
        # シナリオのアーム
        success = await manager.arm_scenario(scenario.id)
        print(f"✅ シナリオアーム: {success}")
        
        # シナリオのトリガー
        success = await manager.trigger_scenario(scenario.id, 147.125)
        print(f"✅ シナリオトリガー: {success}")
        
        # シナリオのエントリー
        trade = await manager.enter_scenario(scenario.id, 147.125)
        print(f"✅ シナリオエントリー: {trade.id if trade else 'Failed'}")
        
        # シナリオのエグジット
        success = await manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
        print(f"✅ シナリオエグジット: {success}")
        
        # 最終状態の確認
        final_scenario = await manager.get_scenario(scenario.id)
        if final_scenario is not None:
            print(f"✅ 最終ステータス: {final_scenario.status.value}")
            if final_scenario.profit_loss is not None:
                print(f"   損益: {final_scenario.profit_loss:.5f}")
            if final_scenario.profit_loss_pips is not None:
                print(f"   損益（ピップス）: {final_scenario.profit_loss_pips:.1f}")
        
        # パフォーマンスサマリー
        summary = await manager.get_performance_summary()
        print(f"✅ パフォーマンス: {summary['total_trades']}トレード, 勝率{summary['win_rate']:.1f}%")
        
        print("🎉 基本機能テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """メイン関数"""
    print("🚀 シナリオ管理システム簡易テスト開始")
    await test_basic_functionality()
    print("🎉 テスト完了")


if __name__ == "__main__":
    asyncio.run(main())
