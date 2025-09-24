"""
階層的LLM分析エンジンのテスト

言語化処理、日誌生成、改善提案の統合テストを行う。
"""

import asyncio
import sys
import os
from datetime import datetime, timezone, timedelta

# パスの追加
sys.path.append('/app')

from modules.llm_analysis.llm.llm_analyzer import LLMAnalyzer
from modules.llm_analysis.llm.language_processor import LanguageProcessor
from modules.llm_analysis.llm.journal_generator import JournalGenerator
from modules.llm_analysis.llm.improvement_advisor import ImprovementAdvisor


async def test_language_processor():
    """言語化処理システムのテスト"""
    print("\n🧪 言語化処理システムテスト")
    
    try:
        processor = LanguageProcessor()
        
        # テストデータ
        trade_snapshot = {
            'trade_id': 'test_001',
            'entry_price': 146.123,
            'direction': 'BUY',
            'rsi': 38.5,
            'macd': 0.0012,
            'ema_200': 145.800,
            'fibonacci_position': 'Fib_0.382',
            'session': 'Tokyo',
            'risk_percent': 0.8
        }
        
        performance_metrics = {
            'win_rate': 65.5,
            'total_profit': 1250.0,
            'max_drawdown': 0.03,
            'sharpe_ratio': 1.8,
            'adherence_score': 87.5,
            'total_trades': 12
        }
        
        market_conditions = {
            'current_price': 146.123,
            'trend_direction': 'BULLISH',
            'volatility': 'MEDIUM',
            'session': 'Tokyo'
        }
        
        technical_indicators = {
            'RSI_14': 38.5,
            'MACD': 0.0012,
            'MACD_Signal': 0.0008,
            'EMA_21': 146.100,
            'EMA_200': 145.800,
            'ATR_14': 0.45
        }
        
        rule_evaluation = {
            'rule_name': 'pullback_buy',
            'score': 0.75,
            'conditions_met': ['RSI_14 <= 40', 'price > EMA_200'],
            'conditions_failed': ['MACD > MACD_Signal']
        }
        
        # テスト実行
        print("📝 トレードスナップ言語化テスト...")
        trade_desc = processor.describe_trade_snapshot(trade_snapshot)
        print(f"✅ トレード説明: {trade_desc[:100]}...")
        
        print("📊 パフォーマンス言語化テスト...")
        perf_desc = processor.describe_performance(performance_metrics)
        print(f"✅ パフォーマンス説明: {perf_desc[:100]}...")
        
        print("🌍 市場状況言語化テスト...")
        market_desc = processor.describe_market_conditions(market_conditions)
        print(f"✅ 市場状況説明: {market_desc[:100]}...")
        
        print("📈 テクニカル指標言語化テスト...")
        tech_desc = processor.describe_technical_indicators(technical_indicators)
        print(f"✅ テクニカル説明: {tech_desc[:100]}...")
        
        print("🔍 ルール評価言語化テスト...")
        rule_desc = processor.describe_rule_evaluation(rule_evaluation)
        print(f"✅ ルール評価説明: {rule_desc[:100]}...")
        
        processor.close()
        print("✅ 言語化処理システムテスト完了")
        
    except Exception as e:
        print(f"❌ 言語化処理システムテストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_journal_generator():
    """日誌生成システムのテスト"""
    print("\n📝 日誌生成システムテスト")
    
    try:
        generator = JournalGenerator()
        
        # テストデータ
        trades = [
            {
                'trade_id': 'test_001',
                'direction': 'BUY',
                'entry_price': 146.123,
                'exit_price': 146.250,
                'profit': 127.0,
                'pips': 12.7,
                'hold_time_minutes': 105
            },
            {
                'trade_id': 'test_002',
                'direction': 'SELL',
                'entry_price': 146.200,
                'exit_price': 146.150,
                'profit': 50.0,
                'pips': 5.0,
                'hold_time_minutes': 45
            }
        ]
        
        rule_performance = {
            'pullback_buy': {
                'win_rate': 65.5,
                'total_trades': 8,
                'total_profit': 850.0,
                'avg_hold_time': 95
            },
            'breakout_buy': {
                'win_rate': 45.0,
                'total_trades': 4,
                'total_profit': -200.0,
                'avg_hold_time': 120
            }
        }
        
        weekly_data = {
            'start_date': datetime.now(timezone.utc) - timedelta(days=7),
            'end_date': datetime.now(timezone.utc),
            'total_trades': 12,
            'win_rate': 58.3,
            'total_profit': 650.0,
            'max_drawdown': 0.025,
            'adherence_score': 82.5
        }
        
        monthly_data = {
            'month': '2025年1月',
            'total_trades': 45,
            'win_rate': 62.2,
            'total_profit': 2850.0,
            'sharpe_ratio': 1.6,
            'max_drawdown': 0.045,
            'adherence_score': 85.0
        }
        
        # テスト実行
        print("📅 日次日誌生成テスト...")
        daily_journal = generator.generate_daily_journal(trades)
        print(f"✅ 日次日誌: {daily_journal[:150]}...")
        
        print("📊 ルールパフォーマンス日誌生成テスト...")
        rule_journal = generator.generate_rule_performance_journal(rule_performance)
        print(f"✅ ルール日誌: {rule_journal[:150]}...")
        
        print("📈 週次レポート生成テスト...")
        weekly_report = generator.generate_weekly_report(weekly_data)
        print(f"✅ 週次レポート: {weekly_report[:150]}...")
        
        print("📊 月次レポート生成テスト...")
        monthly_report = generator.generate_monthly_report(monthly_data)
        print(f"✅ 月次レポート: {monthly_report[:150]}...")
        
        generator.close()
        print("✅ 日誌生成システムテスト完了")
        
    except Exception as e:
        print(f"❌ 日誌生成システムテストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_improvement_advisor():
    """改善提案システムのテスト"""
    print("\n💡 改善提案システムテスト")
    
    try:
        advisor = ImprovementAdvisor()
        
        # テストデータ
        performance_data = {
            'rules': {
                'pullback_buy': {
                    'win_rate': 0.55,
                    'total_trades': 15,
                    'avg_profit': 25.0,
                    'false_positive_rate': 0.3
                },
                'breakout_buy': {
                    'win_rate': 0.45,
                    'total_trades': 8,
                    'avg_profit': -15.0,
                    'false_positive_rate': 0.4
                }
            },
            'overall_win_rate': 0.52,
            'max_drawdown': 0.06,
            'total_trades': 23
        }
        
        backtest_results = {
            'rsi_tests': {
                35: {'win_rate': 0.65, 'sharpe_ratio': 1.8, 'total_trades': 12},
                40: {'win_rate': 0.55, 'sharpe_ratio': 1.5, 'total_trades': 15},
                45: {'win_rate': 0.48, 'sharpe_ratio': 1.2, 'total_trades': 18}
            },
            'atr_tests': {
                1.2: {'win_rate': 0.58, 'avg_profit': 30.0, 'max_drawdown': 0.04, 'total_trades': 12},
                1.5: {'win_rate': 0.55, 'avg_profit': 25.0, 'max_drawdown': 0.05, 'total_trades': 15},
                1.8: {'win_rate': 0.52, 'avg_profit': 20.0, 'max_drawdown': 0.06, 'total_trades': 18}
            }
        }
        
        risk_metrics = {
            'max_drawdown': 0.08,
            'var_95': 0.06,
            'sharpe_ratio': 0.8,
            'max_consecutive_losses': 6,
            'avg_risk_per_trade': 0.025
        }
        
        timing_analysis = {
            'session_performance': {
                'Tokyo': {'win_rate': 0.65, 'total_trades': 8},
                'London': {'win_rate': 0.45, 'total_trades': 6},
                'NewYork': {'win_rate': 0.55, 'total_trades': 9}
            },
            'hour_performance': {
                '9': {'win_rate': 0.7, 'total_trades': 5},
                '14': {'win_rate': 0.3, 'total_trades': 4},
                '21': {'win_rate': 0.6, 'total_trades': 6}
            }
        }
        
        # テスト実行
        print("🔧 ルール改善提案生成テスト...")
        rule_suggestions = advisor.suggest_rule_improvements(performance_data)
        print(f"✅ ルール改善提案: {len(rule_suggestions)}件")
        for suggestion in rule_suggestions[:2]:
            print(f"  - {suggestion}")
        
        print("⚙️ パラメータ調整提案生成テスト...")
        param_suggestions = advisor.suggest_parameter_adjustments(backtest_results)
        print(f"✅ パラメータ調整提案: {len(param_suggestions)}件")
        for key, suggestion in param_suggestions.items():
            if key != 'error':
                print(f"  - {key}: {suggestion.get('reason', '')[:50]}...")
        
        print("🛡️ リスク管理改善提案生成テスト...")
        risk_suggestions = advisor.suggest_risk_management_improvements(risk_metrics)
        print(f"✅ リスク管理改善提案: {len(risk_suggestions)}件")
        for suggestion in risk_suggestions[:2]:
            print(f"  - {suggestion}")
        
        print("⏰ タイミング改善提案生成テスト...")
        timing_suggestions = advisor.suggest_timing_improvements(timing_analysis)
        print(f"✅ タイミング改善提案: {len(timing_suggestions)}件")
        for suggestion in timing_suggestions[:2]:
            print(f"  - {suggestion}")
        
        advisor.close()
        print("✅ 改善提案システムテスト完了")
        
    except Exception as e:
        print(f"❌ 改善提案システムテストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_llm_analyzer():
    """階層的LLM分析エンジンの統合テスト"""
    print("\n🚀 階層的LLM分析エンジン統合テスト")
    
    try:
        analyzer = LLMAnalyzer()
        
        # テストデータ
        trade_snapshot = {
            'trade_id': 'test_001',
            'entry_price': 146.123,
            'direction': 'BUY',
            'rsi': 38.5,
            'macd': 0.0012,
            'ema_200': 145.800,
            'fibonacci_position': 'Fib_0.382',
            'session': 'Tokyo',
            'risk_percent': 0.8,
            'technical_indicators': {
                'RSI_14': 38.5,
                'MACD': 0.0012,
                'EMA_21': 146.100,
                'EMA_200': 145.800,
                'ATR_14': 0.45
            }
        }
        
        daily_data = {
            'date': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'trades': [
                {
                    'trade_id': 'test_001',
                    'direction': 'BUY',
                    'entry_price': 146.123,
                    'exit_price': 146.250,
                    'profit': 127.0,
                    'pips': 12.7,
                    'hold_time_minutes': 105
                }
            ],
            'performance_metrics': {
                'win_rate': 65.5,
                'total_profit': 1250.0,
                'max_drawdown': 0.03,
                'sharpe_ratio': 1.8,
                'adherence_score': 87.5,
                'total_trades': 12
            },
            'market_conditions': {
                'current_price': 146.123,
                'trend_direction': 'BULLISH',
                'volatility': 'MEDIUM',
                'session': 'Tokyo'
            },
            'rule_performance': {
                'pullback_buy': {
                    'win_rate': 0.65,
                    'total_trades': 8,
                    'avg_profit': 25.0
                }
            }
        }
        
        rule_evaluation = {
            'rule_name': 'pullback_buy',
            'score': 0.75,
            'conditions_met': ['RSI_14 <= 40', 'price > EMA_200'],
            'conditions_failed': ['MACD > MACD_Signal']
        }
        
        # テスト実行
        print("🔍 トレードスナップ分析テスト...")
        snapshot_analysis = await analyzer.analyze_trade_snapshot(trade_snapshot)
        print(f"✅ スナップ分析完了: {snapshot_analysis.get('analysis_type', 'unknown')}")
        
        print("📊 日次分析生成テスト...")
        daily_analysis = await analyzer.generate_daily_analysis(daily_data)
        print(f"✅ 日次分析完了: {daily_analysis.get('analysis_type', 'unknown')}")
        
        print("🔍 ルール評価分析テスト...")
        rule_analysis = await analyzer.analyze_rule_evaluation(rule_evaluation)
        print(f"✅ ルール分析完了: {rule_analysis.get('analysis_type', 'unknown')}")
        
        print("📋 分析機能一覧取得テスト...")
        capabilities = analyzer.get_analysis_capabilities()
        print(f"✅ 分析機能: {len(capabilities['capabilities'])}個")
        
        await analyzer.close()
        print("✅ 階層的LLM分析エンジン統合テスト完了")
        
    except Exception as e:
        print(f"❌ 階層的LLM分析エンジン統合テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """メインテスト関数"""
    print("🚀 階層的LLM分析エンジンテスト開始")
    print("=" * 60)
    
    try:
        # 各コンポーネントのテスト
        await test_language_processor()
        await test_journal_generator()
        await test_improvement_advisor()
        await test_llm_analyzer()
        
        print("\n" + "=" * 60)
        print("🎉 全テスト完了!")
        
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
