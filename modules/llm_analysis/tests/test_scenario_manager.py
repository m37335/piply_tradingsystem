"""
シナリオ管理システムのテスト

シナリオ管理システムの動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone, timedelta

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.scenario_manager import (
    ScenarioManager, ScenarioStatus, ExitReason, TradeDirection
)
from modules.llm_analysis.core.rule_engine import EntrySignal, RuleResult


async def test_scenario_lifecycle():
    """シナリオライフサイクルのテスト"""
    print("🧪 シナリオライフサイクルテスト開始")
    
    manager = ScenarioManager()
    
    try:
        # 1. ダミーエントリーシグナルの作成
        print("\n📊 1. ダミーエントリーシグナルの作成...")
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
        print("✅ ダミーエントリーシグナル作成完了")
        
        # 2. シナリオの作成
        print("\n📊 2. シナリオの作成...")
        scenario = await manager.create_scenario(dummy_signal, expires_hours=4)
        print(f"✅ シナリオ作成完了: {scenario.id}")
        print(f"   戦略: {scenario.strategy}")
        print(f"   方向: {scenario.direction.value}")
        print(f"   ステータス: {scenario.status.value}")
        print(f"   有効期限: {scenario.expires_at}")
        
        # 3. シナリオのアーム
        print("\n📊 3. シナリオのアーム...")
        success = await manager.arm_scenario(scenario.id)
        print(f"✅ シナリオアーム: {success}")
        
        # シナリオ状態の確認
        updated_scenario = await manager.get_scenario(scenario.id)
        if updated_scenario is not None:
            print(f"   ステータス: {updated_scenario.status.value}")
        
        # 4. シナリオのトリガー
        print("\n📊 4. シナリオのトリガー...")
        success = await manager.trigger_scenario(scenario.id, 147.125)
        print(f"✅ シナリオトリガー: {success}")
        
        # シナリオ状態の確認
        updated_scenario = await manager.get_scenario(scenario.id)
        if updated_scenario is not None:
            print(f"   ステータス: {updated_scenario.status.value}")
            print(f"   トリガー時刻: {updated_scenario.triggered_at}")
            print(f"   エントリー価格: {updated_scenario.entry_price}")
        
        # 5. シナリオのエントリー
        print("\n📊 5. シナリオのエントリー...")
        trade = await manager.enter_scenario(scenario.id, 147.125)
        print(f"✅ シナリオエントリー: {trade.id if trade else 'Failed'}")
        
        if trade:
            print(f"   トレードID: {trade.id}")
            print(f"   エントリー価格: {trade.entry_price}")
            print(f"   ストップロス: {trade.stop_loss}")
            print(f"   テイクプロフィット1: {trade.take_profit_1}")
        
        # シナリオ状態の確認
        updated_scenario = await manager.get_scenario(scenario.id)
        if updated_scenario is not None:
            print(f"   ステータス: {updated_scenario.status.value}")
            print(f"   エントリー時刻: {updated_scenario.entered_at}")
            if updated_scenario.trades is not None:
                print(f"   トレード数: {len(updated_scenario.trades)}")
        
        # 6. シナリオのエグジット（TP1達成）
        print("\n📊 6. シナリオのエグジット（TP1達成）...")
        success = await manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
        print(f"✅ シナリオエグジット: {success}")
        
        # シナリオ状態の確認
        updated_scenario = await manager.get_scenario(scenario.id)
        if updated_scenario is not None:
            print(f"   ステータス: {updated_scenario.status.value}")
            print(f"   エグジット時刻: {updated_scenario.exited_at}")
            print(f"   エグジット価格: {updated_scenario.exit_price}")
            if updated_scenario.exit_reason is not None:
                print(f"   エグジット理由: {updated_scenario.exit_reason.value}")
            if updated_scenario.profit_loss is not None:
                print(f"   損益: {updated_scenario.profit_loss:.5f}")
            if updated_scenario.profit_loss_pips is not None:
                print(f"   損益（ピップス）: {updated_scenario.profit_loss_pips:.1f}")
            if updated_scenario.hold_time_minutes is not None:
                print(f"   保有時間: {updated_scenario.hold_time_minutes}分")
        
        # トレード状態の確認
        if trade:
            updated_trade = await manager.get_trade(trade.id)
            if updated_trade is not None:
                if updated_trade.profit_loss is not None:
                    print(f"   トレード損益: {updated_trade.profit_loss:.5f}")
                if updated_trade.profit_loss_pips is not None:
                    print(f"   トレード損益（ピップス）: {updated_trade.profit_loss_pips:.1f}")
        
        print("\n🎉 シナリオライフサイクルテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_multiple_scenarios():
    """複数シナリオのテスト"""
    print("\n🧪 複数シナリオテスト開始")
    
    manager = ScenarioManager()
    
    try:
        # 複数のシナリオを作成
        scenarios = []
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
            
            scenario = await manager.create_scenario(dummy_signal)
            scenarios.append(scenario)
            print(f"✅ シナリオ{i+1}作成: {scenario.id}")
        
        # アクティブシナリオの取得
        print("\n📊 アクティブシナリオの取得...")
        active_scenarios = await manager.get_active_scenarios()
        print(f"✅ アクティブシナリオ数: {len(active_scenarios)}")
        
        for scenario in active_scenarios:
            print(f"   {scenario.id}: {scenario.strategy} ({scenario.status.value})")
        
        # 戦略別シナリオの取得
        print("\n📊 戦略別シナリオの取得...")
        strategy_scenarios = await manager.get_scenarios_by_strategy("strategy_1")
        print(f"✅ strategy_1のシナリオ数: {len(strategy_scenarios)}")
        
        # ステータス別シナリオの取得
        print("\n📊 ステータス別シナリオの取得...")
        planned_scenarios = await manager.get_scenarios_by_status(ScenarioStatus.PLANNED)
        print(f"✅ PLANNEDステータスのシナリオ数: {len(planned_scenarios)}")
        
        print("\n🎉 複数シナリオテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_performance_summary():
    """パフォーマンスサマリーのテスト"""
    print("\n🧪 パフォーマンスサマリーテスト開始")
    
    manager = ScenarioManager()
    
    try:
        # 複数の完了したシナリオを作成
        for i in range(5):
            dummy_signal = EntrySignal(
                direction=TradeDirection.BUY,
                strategy="test_strategy",
                confidence=0.8,
                entry_price=147.123,
                stop_loss=146.800,
                take_profit_1=147.400,
                take_profit_2=147.600,
                take_profit_3=147.800,
                risk_reward_ratio=2.5,
                max_hold_time=240,
                rule_results=[],
                technical_summary={},
                created_at=datetime.now(timezone.utc)
            )
            
            scenario = await manager.create_scenario(dummy_signal)
            
            # シナリオを完了まで進める
            await manager.arm_scenario(scenario.id)
            await manager.trigger_scenario(scenario.id, 147.125)
            trade = await manager.enter_scenario(scenario.id, 147.125)
            
            # 異なる結果でエグジット
            if i < 3:  # 勝ち
                exit_price = 147.400 + i * 0.1
                exit_reason = ExitReason.TP1_HIT
            else:  # 負け
                exit_price = 146.800 - (i - 3) * 0.1
                exit_reason = ExitReason.STOP_LOSS
            
            await manager.exit_scenario(scenario.id, exit_price, exit_reason)
            print(f"✅ シナリオ{i+1}完了: {exit_reason.value}")
        
        # パフォーマンスサマリーの取得
        print("\n📊 パフォーマンスサマリーの取得...")
        summary = await manager.get_performance_summary()
        
        print("✅ パフォーマンスサマリー:")
        print(f"   総トレード数: {summary['total_trades']}")
        print(f"   勝ちトレード: {summary['winning_trades']}")
        print(f"   負けトレード: {summary['losing_trades']}")
        print(f"   勝率: {summary['win_rate']:.1f}%")
        print(f"   総損益: {summary['total_profit']:.5f}")
        print(f"   総損益（ピップス）: {summary['total_profit_pips']:.1f}")
        if summary['average_profit'] is not None:
            print(f"   平均損益: {summary['average_profit']:.5f}")
        if summary['average_profit_pips'] is not None:
            print(f"   平均損益（ピップス）: {summary['average_profit_pips']:.1f}")
        print(f"   最大利益: {summary['max_profit']:.5f}")
        print(f"   最大損失: {summary['max_loss']:.5f}")
        print(f"   平均保有時間: {summary['average_hold_time']:.1f}分")
        
        # トレード履歴の取得
        print("\n📊 トレード履歴の取得...")
        trade_history = await manager.get_trade_history()
        print(f"✅ トレード履歴数: {len(trade_history)}")
        
        for trade in trade_history:
            exit_reason_str = trade.exit_reason.value if trade.exit_reason is not None else "Unknown"
            print(f"   {trade.id}: {trade.direction.value} @ {trade.entry_price} → {trade.exit_price} ({exit_reason_str})")
        
        print("\n🎉 パフォーマンスサマリーテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_scenario_cancellation():
    """シナリオキャンセルのテスト"""
    print("\n🧪 シナリオキャンセルテスト開始")
    
    manager = ScenarioManager()
    
    try:
        # シナリオの作成
        dummy_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="test_cancel",
            confidence=0.8,
            entry_price=147.123,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=2.5,
            max_hold_time=240,
            rule_results=[],
            technical_summary={},
            created_at=datetime.now(timezone.utc)
        )
        
        scenario = await manager.create_scenario(dummy_signal)
        print(f"✅ シナリオ作成: {scenario.id}")
        
        # アーム状態でキャンセル
        await manager.arm_scenario(scenario.id)
        success = await manager.cancel_scenario(scenario.id, "market_conditions_changed")
        print(f"✅ シナリオキャンセル: {success}")
        
        # シナリオ状態の確認
        updated_scenario = await manager.get_scenario(scenario.id)
        if updated_scenario is not None:
            print(f"   ステータス: {updated_scenario.status.value}")
            if updated_scenario.metadata is not None:
                print(f"   キャンセル理由: {updated_scenario.metadata.get('cancel_reason')}")
        
        print("\n🎉 シナリオキャンセルテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_expired_scenarios():
    """期限切れシナリオのテスト"""
    print("\n🧪 期限切れシナリオテスト開始")
    
    manager = ScenarioManager()
    
    try:
        # 短い有効期限でシナリオを作成
        dummy_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="test_expire",
            confidence=0.8,
            entry_price=147.123,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=2.5,
            max_hold_time=240,
            rule_results=[],
            technical_summary={},
            created_at=datetime.now(timezone.utc)
        )
        
        scenario = await manager.create_scenario(dummy_signal, expires_hours=0)  # 即座に期限切れ
        print(f"✅ シナリオ作成: {scenario.id}")
        
        # クリーンアップの実行
        expired_count = await manager.cleanup_expired_scenarios()
        print(f"✅ 期限切れシナリオクリーンアップ: {expired_count}件")
        
        # シナリオ状態の確認
        updated_scenario = await manager.get_scenario(scenario.id)
        if updated_scenario is not None:
            print(f"   ステータス: {updated_scenario.status.value}")
        
        # アクティブシナリオの確認
        active_scenarios = await manager.get_active_scenarios()
        print(f"   アクティブシナリオ数: {len(active_scenarios)}")
        
        print("\n🎉 期限切れシナリオテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 シナリオ管理システムテスト開始")
    
    # 基本機能テスト
    await test_scenario_lifecycle()
    
    # 複数シナリオテスト
    await test_multiple_scenarios()
    
    # パフォーマンスサマリーテスト
    await test_performance_summary()
    
    # シナリオキャンセルテスト
    await test_scenario_cancellation()
    
    # 期限切れシナリオテスト
    await test_expired_scenarios()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
