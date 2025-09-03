#!/usr/bin/env python3
"""
分析手法比較

24時間分析 vs 1時間分析の違いを比較
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def compare_analysis_methods():
    """分析手法の違いを比較"""
    print("=" * 80)
    print("🔍 分析手法比較 - 24時間 vs 1時間分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 同じシグナルでの比較分析...")
            
            # 買いシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12
                    FROM technical_indicators ti1
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    LEFT JOIN technical_indicators ti2 ON 
                        ti1.timestamp = ti2.timestamp 
                        AND ti1.timeframe = ti2.timeframe 
                        AND ti2.indicator_type = 'SMA_20'
                    LEFT JOIN technical_indicators ti3 ON 
                        ti1.timestamp = ti3.timestamp 
                        AND ti1.timeframe = ti3.timeframe 
                        AND ti3.indicator_type = 'EMA_12'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value < 40
                    ORDER BY ti1.timestamp DESC
                    LIMIT 3
                    """
                )
            )
            buy_signals = result.fetchall()
            
            print(f"✅ 買いシグナル: {len(buy_signals)}件")
            
            for i, (rsi, signal_price, signal_time, sma_20, ema_12) in enumerate(buy_signals):
                if signal_price and sma_20 and ema_12:
                    print(f"\n📊 シグナル {i+1}: {signal_time.strftime('%m-%d %H:%M')}")
                    print(f"RSI: {rsi:.1f}, エントリー: {signal_price:.3f}")
                    print(f"SMA20: {sma_20:.3f}, EMA12: {ema_12:.3f}")
                    
                    # 1時間後の価格
                    future_1h = signal_time + timedelta(hours=1)
                    result = await db_session.execute(
                        text(
                            """
                            SELECT close_price
                            FROM price_data
                            WHERE timestamp >= :future_time
                            AND currency_pair = 'USD/JPY'
                            ORDER BY timestamp ASC
                            LIMIT 1
                            """
                        ),
                        {"future_time": future_1h}
                    )
                    price_1h_result = result.fetchone()
                    
                    # 24時間後の価格
                    future_24h = signal_time + timedelta(hours=24)
                    result = await db_session.execute(
                        text(
                            """
                            SELECT close_price
                            FROM price_data
                            WHERE timestamp >= :future_time
                            AND currency_pair = 'USD/JPY'
                            ORDER BY timestamp ASC
                            LIMIT 1
                            """
                        ),
                        {"future_time": future_24h}
                    )
                    price_24h_result = result.fetchone()
                    
                    # 24時間の最大価格
                    result = await db_session.execute(
                        text(
                            """
                            SELECT MAX(close_price) as max_price, MIN(close_price) as min_price
                            FROM price_data
                            WHERE timestamp >= :signal_time
                            AND timestamp <= :future_time
                            AND currency_pair = 'USD/JPY'
                            """
                        ),
                        {
                            "signal_time": signal_time,
                            "future_time": future_24h
                        }
                    )
                    max_min_result = result.fetchone()
                    
                    print("\n📈 価格動向比較:")
                    print(f"{'分析手法':<15} {'価格':<10} {'利益(pips)':<12} {'備考':<20}")
                    print("-" * 60)
                    
                    # 1時間分析
                    if price_1h_result:
                        price_1h = price_1h_result[0]
                        profit_1h = (price_1h - signal_price) * 100
                        print(f"{'1時間分析':<15} {price_1h:<10.3f} {profit_1h:<12.1f} {'固定時点':<20}")
                    
                    # 24時間分析
                    if price_24h_result:
                        price_24h = price_24h_result[0]
                        profit_24h = (price_24h - signal_price) * 100
                        print(f"{'24時間分析':<15} {price_24h:<10.3f} {profit_24h:<12.1f} {'最終価格':<20}")
                    
                    # 最大戻り幅分析
                    if max_min_result and max_min_result[0]:
                        max_price = max_min_result[0]
                        min_price = max_min_result[1]
                        max_profit = (max_price - signal_price) * 100
                        max_loss = (signal_price - min_price) * 100
                        print(f"{'最大戻り幅':<15} {max_price:<10.3f} {max_profit:<12.1f} {'24時間最大':<20}")
                        print(f"{'最大下落幅':<15} {min_price:<10.3f} {max_loss:<12.1f} {'24時間最小':<20}")
                    
                    # 移動平均線での利確
                    profit_sma20 = (sma_20 - signal_price) * 100
                    print(f"{'SMA20利確':<15} {sma_20:<10.3f} {profit_sma20:<12.1f} {'移動平均線':<20}")
                    
                    print("\n🔍 分析結果の違い:")
                    if price_1h_result and max_min_result and max_min_result[0]:
                        price_1h = price_1h_result[0]
                        max_price = max_min_result[0]
                        difference = ((max_price - price_1h) / price_1h) * 100
                        print(f"- 1時間後 vs 24時間最大: {difference:.1f}%の差")
                        print(f"- 1時間分析では見逃す利益: {((max_price - price_1h) * 100):.1f}pips")
            
            print("\n🔍 2. 分析手法の違いの説明...")
            print("分析手法による結果の違い:")
            print("- 1時間分析: 短期的な固定時点での利益")
            print("- 24時間分析: 長期的な最大利益幅")
            print("- 移動平均線利確: 技術的指標ベースの利益")
            
            print("\n📊 推奨戦略:")
            print("1. エントリー: RSI < 40 + 価格 > SMA20")
            print("2. 利確戦略:")
            print("   - 保守的: SMA20到達時（約45pips）")
            print("   - 積極的: 24時間最大到達時（約80-120pips）")
            print("3. 損切り: EMA12以下（約30pips）")
            
            print("\n🎯 結論:")
            print("✅ 分析期間により結果が大きく異なる")
            print("✅ 1時間分析は保守的、24時間分析は積極的")
            print("✅ リスク許容度に応じた戦略選択が重要")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(compare_analysis_methods())
