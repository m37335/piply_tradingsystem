"""
スナップ保存システムのテスト

スナップ保存システムの動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.snapshot_manager import SnapshotManager, SnapshotType
from modules.llm_analysis.core.scenario_manager import (
    ScenarioManager, ScenarioStatus, ExitReason, TradeDirection
)
from modules.llm_analysis.core.rule_engine import EntrySignal, RuleResult


async def test_snapshot_basic_functionality():
    """スナップ保存システムの基本機能テスト"""
    print("🧪 スナップ保存システム基本機能テスト")
    
    snapshot_manager = SnapshotManager()
    scenario_manager = ScenarioManager()
    
    try:
        # ダミーのエントリーシグナルとシナリオを作成
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
        
        # シナリオとトレードの作成
        scenario = await scenario_manager.create_scenario(dummy_signal)
        await scenario_manager.arm_scenario(scenario.id)
        await scenario_manager.trigger_scenario(scenario.id, 147.125)
        trade = await scenario_manager.enter_scenario(scenario.id, 147.125)
        
        if trade is not None:
            print(f"✅ シナリオ・トレード作成完了: {scenario.id}, {trade.id}")
            
            # エントリースナップの保存
            entry_snapshot_id = await snapshot_manager.save_entry_snapshot(scenario, trade)
            print(f"✅ エントリースナップ保存: {entry_snapshot_id}")
            
            # エグジットの実行
            await scenario_manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
            print("✅ エグジット実行完了")
            
            # エグジットスナップの保存
            exit_snapshot_id = await snapshot_manager.save_exit_snapshot(trade, ExitReason.TP1_HIT)
            print(f"✅ エグジットスナップ保存: {exit_snapshot_id}")
            
            # スナップショットの取得
            trade_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
        else:
            print("❌ トレードの作成に失敗しました")
            trade_snapshots = []
        print(f"✅ トレード別スナップショット: {len(trade_snapshots)}件")
        
        for snapshot in trade_snapshots:
            print(f"   {snapshot.snapshot_type.value}: {snapshot.id} @ {snapshot.timestamp}")
        
        # パフォーマンス分析の取得
        analysis = await snapshot_manager.get_performance_analysis()
        print(f"✅ パフォーマンス分析:")
        print(f"   総トレード数: {analysis['total_trades']}")
        print(f"   完了トレード数: {analysis['completed_trades']}")
        print(f"   勝率: {analysis['win_rate']:.1f}%")
        print(f"   総損益: {analysis['total_profit']:.5f}")
        print(f"   総損益（ピップス）: {analysis['total_profit_pips']:.1f}")
        
        # 戦略別分析
        if analysis['strategy_analysis']:
            for strategy, strategy_data in analysis['strategy_analysis'].items():
                print(f"   戦略 {strategy}: {strategy_data['trades']}トレード, 勝率{strategy_data['win_rate']:.1f}%")
        
        print("🎉 基本機能テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await snapshot_manager.close()
        await scenario_manager.close()


async def test_multiple_trades():
    """複数トレードのテスト"""
    print("\n🧪 複数トレードテスト")
    
    snapshot_manager = SnapshotManager()
    scenario_manager = ScenarioManager()
    
    try:
        # 複数のトレードを作成
        for i in range(3):
            dummy_signal = EntrySignal(
                direction=TradeDirection.BUY if i % 2 == 0 else TradeDirection.SELL,
                strategy=f"strategy_{i+1}",
                confidence=0.7 + i * 0.1,
                entry_price=147.123 + i * 0.001,
                stop_loss=146.800 + i * 0.001,
                take_profit_1=147.400 + i * 0.001,
                take_profit_2=147.600 + i * 0.001,
                take_profit_3=147.800 + i * 0.001,
                risk_reward_ratio=2.0 + i * 0.5,
                max_hold_time=240,
                rule_results=[],
                technical_summary={},
                created_at=datetime.now(timezone.utc)
            )
            
            # シナリオとトレードの作成
            scenario = await scenario_manager.create_scenario(dummy_signal)
            await scenario_manager.arm_scenario(scenario.id)
            await scenario_manager.trigger_scenario(scenario.id, 147.125 + i * 0.001)
            trade = await scenario_manager.enter_scenario(scenario.id, 147.125 + i * 0.001)
            
            if trade is not None:
                # エントリースナップの保存
                entry_snapshot_id = await snapshot_manager.save_entry_snapshot(scenario, trade)
                print(f"✅ トレード{i+1} エントリースナップ: {entry_snapshot_id}")
                
                # エグジットの実行（異なる結果）
                if i < 2:  # 勝ち
                    exit_price = 147.400 + i * 0.1
                    exit_reason = ExitReason.TP1_HIT
                else:  # 負け
                    exit_price = 146.800 - 0.1
                    exit_reason = ExitReason.STOP_LOSS
                
                await scenario_manager.exit_scenario(scenario.id, exit_price, exit_reason)
                
                # エグジットスナップの保存
                exit_snapshot_id = await snapshot_manager.save_exit_snapshot(trade, exit_reason)
            else:
                print(f"❌ トレード{i+1} の作成に失敗しました")
                continue
            print(f"✅ トレード{i+1} エグジットスナップ: {exit_snapshot_id}")
        
        # トレード履歴の取得
        trade_history = await snapshot_manager.get_trade_history()
        print(f"✅ トレード履歴: {len(trade_history)}件")
        
        # パフォーマンス分析
        analysis = await snapshot_manager.get_performance_analysis()
        print(f"✅ 複数トレード分析:")
        print(f"   総トレード数: {analysis['total_trades']}")
        print(f"   勝率: {analysis['win_rate']:.1f}%")
        print(f"   総損益: {analysis['total_profit']:.5f}")
        
        print("🎉 複数トレードテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await snapshot_manager.close()
        await scenario_manager.close()


async def main():
    """メイン関数"""
    print("🚀 スナップ保存システムテスト開始")
    
    # 基本機能テスト
    await test_snapshot_basic_functionality()
    
    # 複数トレードテスト
    await test_multiple_trades()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
