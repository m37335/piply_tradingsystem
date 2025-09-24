"""
日次評価・改善サイクルシステムのテスト

日次評価・改善サイクルシステムの動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone, timedelta

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.evaluation.daily_evaluator import (
    DailyEvaluator, PerformanceMetric, ImprovementCategory
)
from modules.llm_analysis.core.snapshot_manager import TradeSnapshot
from modules.llm_analysis.core.scenario_manager import ExitReason, TradeDirection


async def test_daily_performance_evaluation():
    """日次パフォーマンス評価のテスト"""
    print("🧪 日次パフォーマンス評価テスト")
    
    evaluator = DailyEvaluator()
    
    try:
        # ダミーのトレードスナップショットを作成
        trade_snapshots = []
        for i in range(5):
            trade_snapshot = TradeSnapshot(
                id=f"trade_snapshot_{i}",
                trade_id=f"trade_{i}",
                scenario_id=f"scenario_{i}",
                entry_snapshot_id=f"entry_snapshot_{i}",
                exit_snapshot_id=f"exit_snapshot_{i}",
                direction=TradeDirection.BUY,
                strategy=f"strategy_{i % 2}",  # 2つの戦略に分散
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
                adherence_score=85 + i * 3,  # 85, 88, 91, 94, 97点
                violation_tags=[f"violation_{i}"] if i % 2 == 0 else [],
                metadata={}
            )
            trade_snapshots.append(trade_snapshot)
        
        # 日次パフォーマンス評価
        daily_performance = await evaluator.evaluate_daily_performance(trade_snapshots)
        
        print(f"✅ 日次パフォーマンス評価完了:")
        print(f"   総トレード数: {daily_performance.total_trades}")
        print(f"   勝率: {daily_performance.win_rate:.1%}")
        print(f"   総利益: {daily_performance.total_profit_pips:.1f}ピップス")
        print(f"   プロフィットファクター: {daily_performance.profit_factor:.2f}")
        print(f"   最大ドローダウン: {daily_performance.max_drawdown:.1f}ピップス")
        print(f"   平均保有時間: {daily_performance.average_hold_time_minutes:.1f}分")
        print(f"   平均遵守スコア: {daily_performance.adherence_score_avg:.1f}点")
        print(f"   遵守スコア範囲: {daily_performance.adherence_score_min:.1f}-{daily_performance.adherence_score_max:.1f}点")
        
        # 戦略別パフォーマンス
        print(f"   戦略別パフォーマンス:")
        for strategy, performance in daily_performance.strategy_performance.items():
            print(f"     {strategy}: {performance['trades']}トレード, 勝率{performance['win_rate']:.1%}, 平均遵守スコア{performance.get('avg_adherence_score', 0):.1f}点")
        
        # 違反分析
        if daily_performance.violation_summary:
            print(f"   違反分析:")
            for violation, count in daily_performance.violation_summary.items():
                print(f"     {violation}: {count}件")
        
        # セッション分析
        print(f"   セッション分析:")
        for session, performance in daily_performance.session_performance.items():
            print(f"     {session}: {performance['trades']}トレード, 勝率{performance['win_rate']:.1%}")
        
        print("🎉 日次パフォーマンス評価テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()


async def test_improvement_suggestions():
    """改善提案生成のテスト"""
    print("\n🧪 改善提案生成テスト")
    
    evaluator = DailyEvaluator()
    
    try:
        # 低パフォーマンスのダミーデータを作成
        trade_snapshots = []
        for i in range(3):
            trade_snapshot = TradeSnapshot(
                id=f"trade_snapshot_{i}",
                trade_id=f"trade_{i}",
                scenario_id=f"scenario_{i}",
                entry_snapshot_id=f"entry_snapshot_{i}",
                exit_snapshot_id=f"exit_snapshot_{i}",
                direction=TradeDirection.BUY,
                strategy="low_performance_strategy",
                entry_price=147.123 + i * 0.001,
                exit_price=147.100 + i * 0.001,  # 負けトレード
                position_size=10000,
                stop_loss=146.800 + i * 0.001,
                take_profit_1=147.400 + i * 0.001,
                take_profit_2=147.600 + i * 0.001,
                take_profit_3=147.800 + i * 0.001,
                entry_time=datetime.now(timezone.utc) - timedelta(hours=i),
                exit_time=datetime.now(timezone.utc) - timedelta(hours=i-1),
                hold_time_minutes=300 + i * 60,  # 長い保有時間
                exit_reason=ExitReason.STOP_LOSS,
                profit_loss=-50 - i * 25,  # 負の利益
                profit_loss_pips=-5 - i * 2.5,
                adherence_score=60 + i * 5,  # 低い遵守スコア
                violation_tags=["risk_management", "timing", "hold_time"],
                metadata={}
            )
            trade_snapshots.append(trade_snapshot)
        
        # 日次パフォーマンス評価
        daily_performance = await evaluator.evaluate_daily_performance(trade_snapshots)
        
        # 改善提案の生成
        improvement_suggestions = await evaluator.generate_improvement_suggestions(
            daily_performance, []
        )
        
        print(f"✅ 改善提案生成完了: {len(improvement_suggestions)}件")
        
        for suggestion in improvement_suggestions:
            print(f"   📋 {suggestion.title}")
            print(f"      カテゴリ: {suggestion.category.value}")
            print(f"      説明: {suggestion.description}")
            print(f"      現在値: {suggestion.current_value}")
            print(f"      提案値: {suggestion.suggested_value}")
            print(f"      信頼度: {suggestion.confidence:.1%}")
            print(f"      期待効果: {suggestion.expected_impact}")
            print(f"      実装難易度: {suggestion.implementation_difficulty}")
            print()
        
        print("🎉 改善提案生成テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()


async def test_weekly_report():
    """週次レポート生成のテスト"""
    print("\n🧪 週次レポート生成テスト")
    
    evaluator = DailyEvaluator()
    
    try:
        # 週間のダミーデータを作成
        trade_snapshots = []
        for day in range(7):  # 7日間
            for i in range(2):  # 1日2トレード
                trade_snapshot = TradeSnapshot(
                    id=f"trade_snapshot_{day}_{i}",
                    trade_id=f"trade_{day}_{i}",
                    scenario_id=f"scenario_{day}_{i}",
                    entry_snapshot_id=f"entry_snapshot_{day}_{i}",
                    exit_snapshot_id=f"exit_snapshot_{day}_{i}",
                    direction=TradeDirection.BUY if i % 2 == 0 else TradeDirection.SELL,
                    strategy=f"strategy_{i % 2}",
                    entry_price=147.123 + day * 0.01 + i * 0.001,
                    exit_price=147.400 + day * 0.01 + i * 0.001,
                    position_size=10000,
                    stop_loss=146.800 + day * 0.01 + i * 0.001,
                    take_profit_1=147.400 + day * 0.01 + i * 0.001,
                    take_profit_2=147.600 + day * 0.01 + i * 0.001,
                    take_profit_3=147.800 + day * 0.01 + i * 0.001,
                    entry_time=datetime.now(timezone.utc) - timedelta(days=6-day, hours=i),
                    exit_time=datetime.now(timezone.utc) - timedelta(days=6-day, hours=i-1),
                    hold_time_minutes=60 + i * 30,
                    exit_reason=ExitReason.TP1_HIT if i % 2 == 0 else ExitReason.STOP_LOSS,
                    profit_loss=100 + day * 10 + i * 50,
                    profit_loss_pips=10 + day * 1 + i * 5,
                    adherence_score=80 + day * 2 + i * 3,
                    violation_tags=[f"violation_{i}"] if i % 3 == 0 else [],
                    metadata={}
                )
                trade_snapshots.append(trade_snapshot)
        
        # 週次レポートの生成
        weekly_report = await evaluator.generate_weekly_report(trade_snapshots)
        
        print(f"✅ 週次レポート生成完了:")
        print(f"   週間期間: {weekly_report.week_start.date()} - {weekly_report.week_end.date()}")
        print(f"   週間総トレード数: {weekly_report.total_trades}")
        print(f"   週間勝率: {weekly_report.overall_performance.win_rate:.1%}")
        print(f"   週間総利益: {weekly_report.overall_performance.total_profit_pips:.1f}ピップス")
        print(f"   週間平均遵守スコア: {weekly_report.overall_performance.adherence_score_avg:.1f}点")
        
        # 日別パフォーマンス
        print(f"   日別パフォーマンス:")
        for daily_perf in weekly_report.daily_performances:
            print(f"     {daily_perf.date.date()}: {daily_perf.total_trades}トレード, 勝率{daily_perf.win_rate:.1%}, 利益{daily_perf.total_profit_pips:.1f}ピップス")
        
        # 改善提案
        print(f"   改善提案: {len(weekly_report.improvement_suggestions)}件")
        for suggestion in weekly_report.improvement_suggestions[:3]:  # 最初の3件のみ表示
            print(f"     - {suggestion.title}")
        
        # ルールパフォーマンス分析
        if weekly_report.rule_performance_analysis.get("most_effective_strategy"):
            most_effective = weekly_report.rule_performance_analysis["most_effective_strategy"]
            print(f"   最も効果的な戦略: {most_effective['name']} (効果性: {most_effective['effectiveness']:.2f})")
        
        # リスク分析
        risk_analysis = weekly_report.risk_analysis
        print(f"   リスク分析:")
        print(f"     最大日次トレード数: {risk_analysis['max_daily_trades']}")
        print(f"     最大日次ドローダウン: {risk_analysis['max_daily_drawdown']:.1f}ピップス")
        print(f"     遵守スコア一貫性: {risk_analysis['adherence_consistency']:.1f}%")
        
        print("🎉 週次レポート生成テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()


async def test_empty_data_handling():
    """空データ処理のテスト"""
    print("\n🧪 空データ処理テスト")
    
    evaluator = DailyEvaluator()
    
    try:
        # 空のトレードリストでテスト
        empty_trade_snapshots = []
        
        # 日次パフォーマンス評価
        daily_performance = await evaluator.evaluate_daily_performance(empty_trade_snapshots)
        
        print(f"✅ 空データでの日次パフォーマンス評価:")
        print(f"   総トレード数: {daily_performance.total_trades}")
        print(f"   勝率: {daily_performance.win_rate:.1%}")
        print(f"   総利益: {daily_performance.total_profit_pips:.1f}ピップス")
        
        # 改善提案の生成
        improvement_suggestions = await evaluator.generate_improvement_suggestions(
            daily_performance, []
        )
        
        print(f"   改善提案数: {len(improvement_suggestions)}件")
        
        # 週次レポートの生成
        weekly_report = await evaluator.generate_weekly_report(empty_trade_snapshots)
        
        print(f"✅ 空データでの週次レポート:")
        print(f"   週間総トレード数: {weekly_report.total_trades}")
        print(f"   改善提案数: {len(weekly_report.improvement_suggestions)}件")
        
        print("🎉 空データ処理テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()


async def main():
    """メイン関数"""
    print("🚀 日次評価・改善サイクルシステムテスト開始")
    
    # 日次パフォーマンス評価テスト
    await test_daily_performance_evaluation()
    
    # 改善提案生成テスト
    await test_improvement_suggestions()
    
    # 週次レポート生成テスト
    await test_weekly_report()
    
    # 空データ処理テスト
    await test_empty_data_handling()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
