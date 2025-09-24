"""
ルール遵守判定システムのテスト

ルール遵守判定システムの動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone, timedelta

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.adherence_evaluator import AdherenceEvaluator, ViolationType
from modules.llm_analysis.core.scenario_manager import (
    ScenarioManager, ScenarioStatus, ExitReason, TradeDirection
)
from modules.llm_analysis.core.rule_engine import EntrySignal, RuleResult
from modules.llm_analysis.core.snapshot_manager import SnapshotManager


async def test_adherence_basic_functionality():
    """ルール遵守判定システムの基本機能テスト"""
    print("🧪 ルール遵守判定システム基本機能テスト")
    
    evaluator = AdherenceEvaluator()
    scenario_manager = ScenarioManager()
    snapshot_manager = SnapshotManager()
    
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
            entry_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
            entry_snapshot = entry_snapshots[0] if entry_snapshots else None
            
            print(f"✅ エントリースナップ保存: {entry_snapshot_id}")
            
            # エグジットの実行
            await scenario_manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
            print("✅ エグジット実行完了")
            
            # エグジットスナップの保存
            exit_snapshot_id = await snapshot_manager.save_exit_snapshot(trade, ExitReason.TP1_HIT)
            exit_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
            exit_snapshot = exit_snapshots[-1] if len(exit_snapshots) > 1 else None
            
            print(f"✅ エグジットスナップ保存: {exit_snapshot_id}")
            
            # 遵守度評価
            if entry_snapshot:
                score = await evaluator.evaluate_trade_adherence(
                    trade, entry_snapshot, exit_snapshot, daily_trades=1, daily_risk_percent=0.5
                )
        else:
            print("❌ トレードの作成に失敗しました")
            return
        
        print(f"✅ 遵守度評価完了:")
        print(f"   総合スコア: {score.total_score}/100")
        print(f"   違反数: {score.violation_count}")
        print(f"   重大違反: {score.critical_violations}")
        print(f"   高違反: {score.high_violations}")
        print(f"   中違反: {score.medium_violations}")
        print(f"   低違反: {score.low_violations}")
        
        # カテゴリ別スコア
        print(f"   カテゴリ別スコア:")
        print(f"     リスク管理: {score.risk_management_score}/25")
        print(f"     タイミング: {score.timing_score}/20")
        print(f"     ポジションサイズ: {score.position_sizing_score}/15")
        print(f"     ルールロジック: {score.rule_logic_score}/20")
        print(f"     セッション: {score.session_score}/10")
        print(f"     相関: {score.correlation_score}/5")
        print(f"     保有時間: {score.hold_time_score}/5")
        
        # 違反詳細
        if score.violations:
            print(f"   違反詳細:")
            for violation in score.violations:
                print(f"     - {violation.violation_type.value}: {violation.description} ({violation.penalty_points}点減点)")
        else:
            print(f"   違反なし: 完璧なトレード！")
        
        print("🎉 基本機能テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()
        await scenario_manager.close()
        await snapshot_manager.close()


async def test_violation_scenarios():
    """違反シナリオのテスト"""
    print("\n🧪 違反シナリオテスト")
    
    evaluator = AdherenceEvaluator()
    scenario_manager = ScenarioManager()
    snapshot_manager = SnapshotManager()
    
    try:
        # リスク管理違反のシナリオ
        high_risk_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="high_risk_test",
            confidence=0.7,
            entry_price=147.123,
            stop_loss=145.000,  # 大きなストップロス（リスク違反）
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=0.5,  # 低いリスクリワード比（違反）
            max_hold_time=240,
            rule_results=[],
            technical_summary={},
            created_at=datetime.now(timezone.utc)
        )
        
        # シナリオとトレードの作成
        scenario = await scenario_manager.create_scenario(high_risk_signal)
        await scenario_manager.arm_scenario(scenario.id)
        await scenario_manager.trigger_scenario(scenario.id, 147.125)
        trade = await scenario_manager.enter_scenario(scenario.id, 147.125)
        
        if trade is not None:
            print(f"✅ 高リスクシナリオ・トレード作成完了: {scenario.id}, {trade.id}")
            
            # エントリースナップの保存
            entry_snapshot_id = await snapshot_manager.save_entry_snapshot(scenario, trade)
            entry_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
            entry_snapshot = entry_snapshots[0] if entry_snapshots else None
            
            # 遵守度評価（高リスクシナリオ）
            if entry_snapshot:
                score = await evaluator.evaluate_trade_adherence(
                    trade, entry_snapshot, None, daily_trades=1, daily_risk_percent=0.5
                )
                
                print(f"✅ 高リスクシナリオ評価完了:")
                print(f"   総合スコア: {score.total_score}/100")
                print(f"   違反数: {score.violation_count}")
        else:
            print("❌ 高リスクトレードの作成に失敗しました")
        
        print("🎉 違反シナリオテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()
        await scenario_manager.close()
        await snapshot_manager.close()


async def test_adherence_summary():
    """遵守度サマリーのテスト"""
    print("\n🧪 遵守度サマリーテスト")
    
    evaluator = AdherenceEvaluator()
    
    try:
        # ダミーのトレードスナップショットを作成
        from modules.llm_analysis.core.snapshot_manager import TradeSnapshot
        
        # 複数のトレードスナップショットを作成
        trade_snapshots = []
        for i in range(3):
            trade_snapshot = TradeSnapshot(
                id=f"trade_snapshot_{i}",
                trade_id=f"trade_{i}",
                scenario_id=f"scenario_{i}",
                entry_snapshot_id=f"entry_snapshot_{i}",
                exit_snapshot_id=f"exit_snapshot_{i}",
                direction=TradeDirection.BUY,
                strategy=f"strategy_{i}",
                entry_price=147.123 + i * 0.001,
                exit_price=147.400 + i * 0.001,
                position_size=10000,
                stop_loss=146.800 + i * 0.001,
                take_profit_1=147.400 + i * 0.001,
                take_profit_2=147.600 + i * 0.001,
                take_profit_3=147.800 + i * 0.001,
                entry_time=datetime.now(timezone.utc) - timedelta(hours=i),
                exit_time=datetime.now(timezone.utc) - timedelta(hours=i-1),
                hold_time_minutes=60 + i * 30,
                exit_reason=ExitReason.TP1_HIT,
                profit_loss=100 + i * 50,
                profit_loss_pips=10 + i * 5,
                adherence_score=85 + i * 5,  # 85, 90, 95点
                violation_tags=[f"violation_{i}"],
                metadata={}
            )
            trade_snapshots.append(trade_snapshot)
        
        # 遵守度サマリーの取得
        summary = await evaluator.get_adherence_summary(trade_snapshots, days=7)
        
        print(f"✅ 遵守度サマリー取得完了:")
        print(f"   総トレード数: {summary['total_trades']}")
        print(f"   スコア付きトレード数: {summary['trades_with_scores']}")
        
        if 'score_statistics' in summary:
            stats = summary['score_statistics']
            print(f"   平均スコア: {stats['average']:.1f}")
            print(f"   最小スコア: {stats['minimum']}")
            print(f"   最大スコア: {stats['maximum']}")
        
        if 'score_distribution' in summary:
            dist = summary['score_distribution']
            print(f"   スコア分布:")
            print(f"     優秀(90+): {dist['excellent']}")
            print(f"     良好(80-89): {dist['good']}")
            print(f"     普通(70-79): {dist['fair']}")
            print(f"     不良(<70): {dist['poor']}")
        
        if 'strategy_analysis' in summary:
            print(f"   戦略別分析:")
            for strategy, analysis in summary['strategy_analysis'].items():
                print(f"     {strategy}: {analysis['trades']}トレード, 平均{analysis['avg_score']:.1f}点")
        
        print("🎉 遵守度サマリーテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()


async def main():
    """メイン関数"""
    print("🚀 ルール遵守判定システムテスト開始")
    
    # 基本機能テスト
    await test_adherence_basic_functionality()
    
    # 違反シナリオテスト
    await test_violation_scenarios()
    
    # 遵守度サマリーテスト
    await test_adherence_summary()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
