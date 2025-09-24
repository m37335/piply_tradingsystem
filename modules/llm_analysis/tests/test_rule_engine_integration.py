"""
ルールエンジン統合テスト

Yahoo Finance Stream Clientとルールエンジンを統合して、
リアルタイム価格データに基づく売買判定をテストする。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Any, Dict

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.providers.yahoo_finance_stream_client import YahooFinanceStreamClient, StreamType, PriceData
from modules.llm_analysis.core.rule_engine import RuleBasedEngine, EntrySignal
from modules.llm_analysis.core.data_preparator import LLMDataPreparator


class RuleEngineIntegrationLogger:
    """ルールエンジン統合テスト用のロガー"""
    
    def __init__(self):
        self.price_updates = []
        self.rule_evaluations = []
        self.entry_signals = []
        self.start_time = datetime.now()
    
    def log_price_update(self, price_data: PriceData):
        """価格更新のログ"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()
        
        self.price_updates.append({
            'timestamp': timestamp,
            'elapsed_seconds': elapsed,
            'instrument': price_data.instrument,
            'price': price_data.mid_price,
            'bid': price_data.bid,
            'ask': price_data.ask,
            'spread': price_data.spread
        })
        
        print(f"📊 [{elapsed:6.1f}s] {price_data.instrument}: {price_data.mid_price:.5f}")
    
    def log_rule_evaluation(self, evaluation_result: Dict):
        """ルール評価のログ"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()
        
        self.rule_evaluations.append({
            'timestamp': timestamp,
            'elapsed_seconds': elapsed,
            'result': evaluation_result
        })
        
        print(f"🔍 [{elapsed:6.1f}s] ルール評価: {evaluation_result}")
    
    def log_entry_signal(self, signal: EntrySignal):
        """エントリーシグナルのログ"""
        timestamp = datetime.now()
        elapsed = (timestamp - self.start_time).total_seconds()
        
        self.entry_signals.append({
            'timestamp': timestamp,
            'elapsed_seconds': elapsed,
            'signal': signal
        })
        
        print(f"🚨 [{elapsed:6.1f}s] エントリーシグナル: {signal.direction} @ {signal.price:.5f}")
    
    def get_summary(self):
        """テスト結果のサマリー"""
        duration = (datetime.now() - self.start_time).total_seconds()
        
        summary = f"""
🔍 ルールエンジン統合テスト結果:
  - テスト時間: {duration:.1f}秒
  - 価格更新回数: {len(self.price_updates)}回
  - ルール評価回数: {len(self.rule_evaluations)}回
  - エントリーシグナル数: {len(self.entry_signals)}回
"""
        
        if self.entry_signals:
            summary += "\n📈 エントリーシグナル詳細:\n"
            for signal_data in self.entry_signals:
                signal = signal_data['signal']
                summary += f"  - {signal.direction} @ {signal.price:.5f} (確率: {signal.probability}%)\n"
        
        return summary


async def test_rule_engine_integration():
    """ルールエンジン統合テスト"""
    print("🧪 ルールエンジン統合テスト")
    
    logger = RuleEngineIntegrationLogger()
    stream_client = YahooFinanceStreamClient()
    rule_engine = RuleBasedEngine()
    data_preparator = LLMDataPreparator()
    
    try:
        # 初期化
        await stream_client.initialize()
        await data_preparator.initialize()
        print("✅ クライアント初期化完了")
        
        # 価格更新コールバック
        async def price_update_callback(price_data: PriceData):
            logger.log_price_update(price_data)
            
            try:
                # データ準備
                analysis_data = await data_preparator.prepare_analysis_data(
                    analysis_type='trend_direction',
                    symbol='USDJPY=X',
                    timeframes=['5m', '15m', '1h', '4h', '1d']
                )
                
                if analysis_data:
                    # ルール評価
                    entry_signals = await rule_engine.evaluate_entry_conditions('USDJPY=X', 'trend_direction')
                    logger.log_rule_evaluation(entry_signals)
                    
                    # エントリーシグナル処理
                    if entry_signals:
                        for signal in entry_signals:
                            logger.log_entry_signal(signal)
                
            except Exception as e:
                print(f"❌ ルール評価エラー: {e}")
        
        # コールバック設定
        stream_client.add_callback(StreamType.PRICING, price_update_callback)
        print("✅ コールバック設定完了")
        
        # ストリーミング開始
        instruments = ['USD_JPY']
        print(f"📊 監視開始: {', '.join(instruments)}")
        
        streaming_task = asyncio.create_task(
            stream_client.start_price_stream(instruments)
        )
        
        # 2分間テスト
        print("⏰ 2分間のルールエンジン統合テストを開始...")
        await asyncio.sleep(120)  # 2分 = 120秒
        
        # ストリーミング停止
        stream_client.stop_stream()
        streaming_task.cancel()
        
        # 結果表示
        print("\n" + "="*60)
        print(logger.get_summary())
        print("="*60)
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await stream_client.close()
        await data_preparator.close()


async def test_manual_rule_evaluation():
    """手動ルール評価テスト"""
    print("🧪 手動ルール評価テスト")
    
    rule_engine = RuleBasedEngine()
    data_preparator = LLMDataPreparator()
    
    try:
        # 初期化
        await data_preparator.initialize()
        print("✅ データ準備器初期化完了")
        
        # データ準備
        analysis_data = await data_preparator.prepare_analysis_data(
            analysis_type='trend_direction',
            symbol='USDJPY=X',
            timeframes=['5m', '15m', '1h', '4h', '1d']
        )
        
        if analysis_data:
            print("✅ 分析データ準備完了")
            
            # ルール評価
            entry_signals = await rule_engine.evaluate_entry_conditions('USDJPY=X', 'trend_direction')
            print(f"🔍 ルール評価結果: {len(entry_signals)}個のシグナル")
            
            # エントリーシグナル処理
            if entry_signals:
                for signal in entry_signals:
                    print(f"🚨 エントリーシグナル: {signal.direction} @ {signal.price:.5f} (確率: {signal.probability}%)")
            else:
                print("ℹ️ エントリー条件未成立")
        else:
            print("❌ 分析データ準備失敗")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await data_preparator.close()


async def main():
    """メイン関数"""
    print("🚀 ルールエンジン統合テスト開始")
    print()
    
    # ログレベル設定
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 1. 手動ルール評価テスト
        await test_manual_rule_evaluation()
        print()
        
        # 2. ルールエンジン統合テスト
        await test_rule_engine_integration()
        
        print("\n🎉 全テスト完了!")
        
    except KeyboardInterrupt:
        print("\n🛑 テスト中断")
    except Exception as e:
        print(f"\n❌ メインテストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
