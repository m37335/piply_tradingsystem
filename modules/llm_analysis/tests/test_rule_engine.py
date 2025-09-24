"""
ルールベース判定エンジンのテスト

ルールベース判定エンジンの動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.core.rule_engine import RuleBasedEngine, TradeDirection


async def test_rule_engine():
    """ルールベース判定エンジンのテスト"""
    print("🧪 ルールベース判定エンジンテスト開始")
    
    engine = RuleBasedEngine()
    
    try:
        # 1. トレンド方向分析でのエントリー条件評価
        print("\n📊 1. トレンド方向分析でのエントリー条件評価...")
        trend_signals = await engine.evaluate_entry_conditions(
            symbol='USDJPY=X',
            analysis_type='trend_direction'
        )
        
        print(f"✅ トレンド方向分析完了: {len(trend_signals)}個のシグナル")
        for signal in trend_signals:
            print(f"   戦略: {signal.strategy}")
            print(f"   方向: {signal.direction.value}")
            print(f"   信頼度: {signal.confidence:.2f}")
            print(f"   エントリー価格: {signal.entry_price:.5f}")
            print(f"   ストップロス: {signal.stop_loss:.5f}")
            print(f"   テイクプロフィット1: {signal.take_profit_1:.5f}")
            print(f"   リスクリワード比: {signal.risk_reward_ratio:.2f}")
            print(f"   最大保有時間: {signal.max_hold_time}分")
            
            print("   ルール結果:")
            for result in signal.rule_results:
                status = "✅" if result.passed else "❌"
                print(f"     {status} {result.message} (スコア: {result.score:.2f})")
            print()
        
        # 2. ゾーン決定分析でのエントリー条件評価
        print("\n📊 2. ゾーン決定分析でのエントリー条件評価...")
        zone_signals = await engine.evaluate_entry_conditions(
            symbol='USDJPY=X',
            analysis_type='zone_decision'
        )
        
        print(f"✅ ゾーン決定分析完了: {len(zone_signals)}個のシグナル")
        for signal in zone_signals:
            print(f"   戦略: {signal.strategy}")
            print(f"   方向: {signal.direction.value}")
            print(f"   信頼度: {signal.confidence:.2f}")
            print()
        
        # 3. 執行タイミング分析でのエントリー条件評価
        print("\n📊 3. 執行タイミング分析でのエントリー条件評価...")
        timing_signals = await engine.evaluate_entry_conditions(
            symbol='USDJPY=X',
            analysis_type='timing_execution'
        )
        
        print(f"✅ 執行タイミング分析完了: {len(timing_signals)}個のシグナル")
        for signal in timing_signals:
            print(f"   戦略: {signal.strategy}")
            print(f"   方向: {signal.direction.value}")
            print(f"   信頼度: {signal.confidence:.2f}")
            print()
        
        # 4. トレンド補強分析でのエントリー条件評価
        print("\n📊 4. トレンド補強分析でのエントリー条件評価...")
        reinforcement_signals = await engine.evaluate_entry_conditions(
            symbol='USDJPY=X',
            analysis_type='trend_reinforcement'
        )
        
        print(f"✅ トレンド補強分析完了: {len(reinforcement_signals)}個のシグナル")
        for signal in reinforcement_signals:
            print(f"   戦略: {signal.strategy}")
            print(f"   方向: {signal.direction.value}")
            print(f"   信頼度: {signal.confidence:.2f}")
            print()
        
        # 5. ルール設定の確認
        print("\n📊 5. ルール設定の確認...")
        print("✅ アクティブルール:")
        for rule in engine.rules_config['active_rules']:
            status = "🟢" if rule.get('enabled', False) else "🔴"
            print(f"   {status} {rule['name']}: {rule['description']}")
        
        print("\n✅ パラメータ設定:")
        for key, value in engine.rules_config['parameters'].items():
            print(f"   {key}: {value}")
        
        print("\n✅ リスク制約:")
        for key, value in engine.risk_constraints.items():
            print(f"   {key}: {value}")
        
        # 6. テクニカルサマリーの確認
        if trend_signals:
            print("\n📊 6. テクニカルサマリーの確認...")
            signal = trend_signals[0]
            print("✅ テクニカルサマリー:")
            for timeframe, summary in signal.technical_summary.items():
                print(f"   {timeframe}:")
                print(f"     価格: {summary.get('price', 'N/A')}")
                print(f"     RSI_14: {summary.get('rsi_14', 'N/A')}")
                print(f"     EMA_21: {summary.get('ema_21', 'N/A')}")
                print(f"     EMA_200: {summary.get('ema_200', 'N/A')}")
                print(f"     MACD: {summary.get('macd', 'N/A')}")
                print(f"     ATR_14: {summary.get('atr_14', 'N/A')}")
                print(f"     ボリューム比率: {summary.get('volume_ratio', 'N/A')}")
                
                fib_levels = summary.get('fibonacci_levels', {})
                if fib_levels:
                    print(f"     フィボナッチレベル: {len(fib_levels)}個")
                    for level, value in list(fib_levels.items())[:3]:  # 最初の3個のみ表示
                        print(f"       Fib_{level}: {value:.5f}")
                print()
        
        print("🎉 全てのテストが成功しました！")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


async def test_rule_conditions():
    """ルール条件の個別テスト"""
    print("\n🧪 ルール条件の個別テスト...")
    
    engine = RuleBasedEngine()
    
    try:
        # サンプルデータでの条件評価テスト
        sample_data = {
            'timeframes': {
                '1h': {
                    'data': {
                        'close': [147.123],
                        'RSI_14': [38.5],
                        'EMA_200': [146.800],
                        'MACD': [0.0012],
                        'MACD_Signal': [0.0008],
                        'ATR_14': [0.45],
                        'Volume_Ratio': [1.2],
                        'Fib_0.382': [146.950],
                        'Fib_0.618': [146.850]
                    }
                }
            }
        }
        
        # RSI条件のテスト
        print("📊 RSI条件テスト...")
        rsi_result = engine._evaluate_rsi_condition("RSI_14 <= 40", sample_data)
        print(f"   RSI_14 <= 40: {rsi_result.passed} (スコア: {rsi_result.score:.2f})")
        print(f"   メッセージ: {rsi_result.message}")
        
        # EMA条件のテスト
        print("\n📊 EMA条件テスト...")
        ema_result = engine._evaluate_ema_condition("price > EMA_200", sample_data)
        print(f"   price > EMA_200: {ema_result.passed} (スコア: {ema_result.score:.2f})")
        print(f"   メッセージ: {ema_result.message}")
        
        # MACD条件のテスト
        print("\n📊 MACD条件テスト...")
        macd_result = engine._evaluate_macd_condition("MACD > MACD_Signal", sample_data)
        print(f"   MACD > MACD_Signal: {macd_result.passed} (スコア: {macd_result.score:.2f})")
        print(f"   メッセージ: {macd_result.message}")
        
        # セッション条件のテスト
        print("\n📊 セッション条件テスト...")
        session_result = engine._evaluate_session_condition("active_session = Tokyo OR London")
        print(f"   active_session = Tokyo OR London: {session_result.passed} (スコア: {session_result.score:.2f})")
        print(f"   メッセージ: {session_result.message}")
        
        # リスク条件のテスト
        print("\n📊 リスク条件テスト...")
        risk_result = engine._evaluate_risk_condition("daily_trades < 5", sample_data)
        print(f"   daily_trades < 5: {risk_result.passed} (スコア: {risk_result.score:.2f})")
        print(f"   メッセージ: {risk_result.message}")
        
        print("\n✅ ルール条件の個別テスト完了")
        
    except Exception as e:
        print(f"❌ ルール条件テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


async def main():
    """メイン関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 ルールベース判定エンジンテスト開始")
    
    # 基本機能テスト
    await test_rule_engine()
    
    # ルール条件の個別テスト
    await test_rule_conditions()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
