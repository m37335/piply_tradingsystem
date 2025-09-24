"""
ルール設定のテスト

現在のルール設定を確認し、下降トレンド検知ルールが有効になっているかチェック
"""

import asyncio
import logging
import sys
import os

# パスの設定
sys.path.append('/app')

from modules.llm_analysis.core.rule_engine import RuleBasedEngine


async def test_rule_config():
    """ルール設定のテスト"""
    print("🔍 ルール設定テスト開始")
    print("=" * 60)
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # ルールエンジンの初期化
    engine = RuleBasedEngine()
    
    try:
        # 初期化
        print("📋 ルールエンジン初期化中...")
        await engine.initialize()
        print("✅ ルールエンジン初期化完了")
        
        # ルール設定の確認
        print("\n📊 アクティブルール設定:")
        print("-" * 40)
        
        for i, rule in enumerate(engine.rules_config['active_rules']):
            status = "✅ 有効" if rule.get('enabled', False) else "❌ 無効"
            print(f"{i+1}. {rule['name']}: {status}")
            print(f"   説明: {rule['description']}")
            print(f"   条件数: {len(rule['conditions'])}")
            print()
        
        # 有効なルールの確認
        enabled_rules = [rule for rule in engine.rules_config['active_rules'] if rule.get('enabled', False)]
        print(f"📈 有効なルール数: {len(enabled_rules)}")
        
        # 下降トレンド検知ルールの確認
        sell_rules = [rule for rule in enabled_rules if 'sell' in rule['name']]
        print(f"📉 下降トレンド検知ルール数: {len(sell_rules)}")
        
        for rule in sell_rules:
            print(f"   - {rule['name']}: {rule['description']}")
        
        # ルール評価のテスト
        print("\n🧪 ルール評価テスト...")
        signals = await engine.evaluate_entry_conditions('USDJPY=X', 'trend_direction')
        
        print(f"✅ ルール評価完了: {len(signals)}個のシグナル")
        
        for signal in signals:
            print(f"\n📊 シグナル: {signal.strategy}")
            print(f"   方向: {signal.direction.value}")
            print(f"   信頼度: {signal.confidence:.2f}")
            print(f"   エントリー価格: {signal.entry_price:.5f}")
            print(f"   ストップロス: {signal.stop_loss:.5f}")
            print(f"   テイクプロフィット: {signal.take_profit:.5f}")
        
        print("\n✅ ルール設定テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # クリーンアップ
        try:
            await engine.close()
            print("🧹 リソースクリーンアップ完了")
        except Exception as e:
            print(f"⚠️ クリーンアップエラー: {e}")


if __name__ == "__main__":
    asyncio.run(test_rule_config())
