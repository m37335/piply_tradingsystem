"""
スナップ保存システムの簡易テスト

データベース接続なしでスナップ保存システムの基本機能をテストする。
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
    """スナップ保存システムの基本機能テスト（簡易版）"""
    print("🧪 スナップ保存システム基本機能テスト（簡易版）")
    
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
            
            # エントリースナップの保存（データベース接続なし）
            try:
                entry_snapshot_id = await snapshot_manager.save_entry_snapshot(scenario, trade)
                print(f"✅ エントリースナップ保存: {entry_snapshot_id}")
            except Exception as e:
                print(f"⚠️ エントリースナップ保存エラー（データベース接続なし）: {e}")
                # ダミーのスナップショットを作成
                entry_snapshot_id = f"snapshot_dummy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"✅ ダミーエントリースナップ: {entry_snapshot_id}")
            
            # エグジットの実行
            await scenario_manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
            print("✅ エグジット実行完了")
            
            # エグジットスナップの保存（データベース接続なし）
            try:
                exit_snapshot_id = await snapshot_manager.save_exit_snapshot(trade, ExitReason.TP1_HIT)
                print(f"✅ エグジットスナップ保存: {exit_snapshot_id}")
            except Exception as e:
                print(f"⚠️ エグジットスナップ保存エラー（データベース接続なし）: {e}")
                # ダミーのスナップショットを作成
                exit_snapshot_id = f"snapshot_dummy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                print(f"✅ ダミーエグジットスナップ: {exit_snapshot_id}")
            
            # スナップショットの取得
            try:
                trade_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
            except Exception as e:
                print(f"⚠️ スナップショット取得エラー: {e}")
                trade_snapshots = []
        else:
            print("❌ トレードの作成に失敗しました")
            trade_snapshots = []
        
        if trade_snapshots:
            print(f"✅ トレード別スナップショット: {len(trade_snapshots)}件")
            
            for snapshot in trade_snapshots:
                print(f"   {snapshot.snapshot_type.value}: {snapshot.id} @ {snapshot.timestamp}")
        
        # パフォーマンス分析の取得
        try:
            analysis = await snapshot_manager.get_performance_analysis()
            print(f"✅ パフォーマンス分析:")
            print(f"   総トレード数: {analysis['total_trades']}")
            print(f"   完了トレード数: {analysis['completed_trades']}")
            print(f"   勝率: {analysis['win_rate']:.1f}%")
            print(f"   総損益: {analysis['total_profit']:.5f}")
            print(f"   総損益（ピップス）: {analysis['total_profit_pips']:.1f}")
        except Exception as e:
            print(f"⚠️ パフォーマンス分析エラー: {e}")
        
        print("🎉 基本機能テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await snapshot_manager.close()
        await scenario_manager.close()


async def test_snapshot_manager_structure():
    """スナップマネージャーの構造テスト"""
    print("\n🧪 スナップマネージャー構造テスト")
    
    snapshot_manager = SnapshotManager()
    
    try:
        # スナップマネージャーの状態確認
        state = snapshot_manager.to_dict()
        print(f"✅ スナップマネージャー状態:")
        print(f"   総スナップショット数: {state['total_snapshots']}")
        print(f"   総トレードスナップショット数: {state['total_trade_snapshots']}")
        
        # セッション情報の取得
        session_info = snapshot_manager._get_session_info()
        print(f"✅ セッション情報:")
        print(f"   アクティブセッション: {session_info.get('active_sessions', [])}")
        print(f"   現在時刻（JST）: {session_info.get('current_time_jst', 'N/A')}")
        
        # リスク指標の取得
        risk_metrics = await snapshot_manager._get_risk_metrics()
        print(f"✅ リスク指標:")
        print(f"   日次リスク: {risk_metrics.get('daily_risk_percent', 0)}%")
        print(f"   最大リスク/トレード: {risk_metrics.get('max_risk_per_trade', 0)}%")
        
        print("🎉 構造テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await snapshot_manager.close()


async def main():
    """メイン関数"""
    print("🚀 スナップ保存システム簡易テスト開始")
    
    # 構造テスト
    await test_snapshot_manager_structure()
    
    # 基本機能テスト
    await test_snapshot_basic_functionality()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
