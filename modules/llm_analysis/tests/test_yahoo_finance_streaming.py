"""
Yahoo Finance Stream Client 本格テスト

60秒間隔での価格更新をテストし、リアルタイムデータ取得の動作を確認する。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from typing import Any

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.providers.yahoo_finance_stream_client import YahooFinanceStreamClient, StreamType, PriceData


class StreamingTestLogger:
    """ストリーミングテスト用のロガー"""
    
    def __init__(self):
        self.price_updates = []
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
        
        print(f"📊 [{elapsed:6.1f}s] {price_data.instrument}: {price_data.mid_price:.5f} "
              f"(Bid: {price_data.bid:.5f}, Ask: {price_data.ask:.5f}, Spread: {price_data.spread:.5f})")
    
    def get_summary(self):
        """テスト結果のサマリー"""
        if not self.price_updates:
            return "❌ 価格更新が記録されませんでした"
        
        instruments = set(update['instrument'] for update in self.price_updates)
        total_updates = len(self.price_updates)
        duration = (datetime.now() - self.start_time).total_seconds()
        
        summary = f"""
📈 ストリーミングテスト結果:
  - テスト時間: {duration:.1f}秒
  - 総更新回数: {total_updates}回
  - 監視通貨ペア: {', '.join(instruments)}
  - 平均更新間隔: {duration/total_updates:.1f}秒/回
"""
        
        # 通貨ペア別の統計
        for instrument in instruments:
            instrument_updates = [u for u in self.price_updates if u['instrument'] == instrument]
            if instrument_updates:
                prices = [u['price'] for u in instrument_updates]
                min_price = min(prices)
                max_price = max(prices)
                price_range = max_price - min_price
                
                summary += f"  - {instrument}: {len(instrument_updates)}回更新, "
                summary += f"価格範囲: {min_price:.5f} - {max_price:.5f} (変動: {price_range:.5f})\n"
        
        return summary


async def test_short_streaming():
    """短時間ストリーミングテスト（5分間）"""
    print("🧪 Yahoo Finance Stream Client 短時間テスト（5分間）")
    
    logger = StreamingTestLogger()
    client = YahooFinanceStreamClient()
    
    try:
        # 初期化
        await client.initialize()
        print("✅ クライアント初期化完了")
        
        # コールバックの設定
        client.add_callback(StreamType.PRICING, logger.log_price_update)
        print("✅ コールバック設定完了")
        
        # 監視する通貨ペア
        instruments = ['USD_JPY']
        print(f"📊 監視開始: {', '.join(instruments)}")
        
        # ストリーミング開始（バックグラウンドで実行）
        streaming_task = asyncio.create_task(
            client.start_price_stream(instruments)
        )
        
        # 5分間待機
        print("⏰ 5分間のストリーミングテストを開始...")
        await asyncio.sleep(300)  # 5分 = 300秒
        
        # ストリーミング停止
        client.stop_stream()
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
        await client.close()


async def test_quick_streaming():
    """クイックストリーミングテスト（1分間）"""
    print("🧪 Yahoo Finance Stream Client クイックテスト（1分間）")
    
    logger = StreamingTestLogger()
    client = YahooFinanceStreamClient()
    
    try:
        # 初期化
        await client.initialize()
        print("✅ クライアント初期化完了")
        
        # コールバックの設定
        client.add_callback(StreamType.PRICING, logger.log_price_update)
        print("✅ コールバック設定完了")
        
        # 監視する通貨ペア
        instruments = ['USD_JPY']
        print(f"📊 監視開始: {', '.join(instruments)}")
        
        # ストリーミング開始（バックグラウンドで実行）
        streaming_task = asyncio.create_task(
            client.start_price_stream(instruments)
        )
        
        # 1分間待機
        print("⏰ 1分間のストリーミングテストを開始...")
        await asyncio.sleep(60)  # 1分 = 60秒
        
        # ストリーミング停止
        client.stop_stream()
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
        await client.close()


async def test_manual_price_updates():
    """手動価格更新テスト"""
    print("🧪 手動価格更新テスト")
    
    client = YahooFinanceStreamClient()
    
    try:
        # 初期化
        await client.initialize()
        print("✅ クライアント初期化完了")
        
        # 複数通貨ペアの現在価格を取得
        instruments = ['USD_JPY']
        
        print("📊 現在価格取得テスト:")
        for instrument in instruments:
            price_data = await client.get_current_price(instrument)
            if price_data:
                print(f"  {instrument}: {price_data.mid_price:.5f} "
                      f"(Bid: {price_data.bid:.5f}, Ask: {price_data.ask:.5f})")
            else:
                print(f"  {instrument}: ❌ 価格取得失敗")
        
        print("✅ 手動価格更新テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


async def main():
    """メイン関数"""
    print("🚀 Yahoo Finance Stream Client 本格テスト開始")
    print()
    
    # ログレベル設定
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 1. 手動価格更新テスト
        await test_manual_price_updates()
        print()
        
        # 2. クイックストリーミングテスト
        await test_quick_streaming()
        print()
        
        # 3. 短時間ストリーミングテスト（スキップ）
        print("ℹ️ 5分間のストリーミングテストはスキップします")
        
        print("\n🎉 全テスト完了!")
        
    except KeyboardInterrupt:
        print("\n🛑 テスト中断")
    except Exception as e:
        print(f"\n❌ メインテストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
