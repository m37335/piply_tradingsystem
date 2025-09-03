#!/usr/bin/env python3
"""
シグナル性能検証スクリプト

シグナル発生後の価格動向を検証して、実際のパフォーマンスを分析します
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


async def verify_signal_performance():
    """シグナル性能を検証"""
    print("=" * 80)
    print("📊 シグナル性能検証")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. シグナル発生後の価格動向を検証...")
            
            # シグナル発生データを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        ti2.value as sma_value,
                        ti3.value as ema_12,
                        ti4.value as ema_26,
                        ti5.value as atr_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti1.timeframe
                    FROM technical_indicators ti1
                    LEFT JOIN technical_indicators ti2 ON 
                        ti1.timestamp = ti2.timestamp 
                        AND ti1.timeframe = ti2.timeframe 
                        AND ti2.indicator_type = 'SMA_20'
                    LEFT JOIN technical_indicators ti3 ON 
                        ti1.timestamp = ti3.timestamp 
                        AND ti1.timeframe = ti3.timeframe 
                        AND ti3.indicator_type = 'EMA_12'
                    LEFT JOIN technical_indicators ti4 ON 
                        ti1.timestamp = ti4.timestamp 
                        AND ti1.timeframe = ti4.timeframe 
                        AND ti4.indicator_type = 'EMA_26'
                    LEFT JOIN technical_indicators ti5 ON 
                        ti1.timestamp = ti5.timestamp 
                        AND ti1.timeframe = ti5.timeframe 
                        AND ti5.indicator_type = 'ATR'
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    WHERE ti1.indicator_type = 'RSI'
                    AND (
                        (ti1.value < 45 AND pd.close_price > ti2.value AND ti3.value > ti4.value AND 0.01 <= ti5.value AND ti5.value <= 0.10) OR
                        (ti1.value > 55 AND pd.close_price < ti2.value AND ti3.value < ti4.value AND 0.01 <= ti5.value AND ti5.value <= 0.10)
                    )
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            signals = result.fetchall()
            
            print(f"✅ 検証対象シグナル: {len(signals)}件")
            
            total_profit = 0
            winning_signals = 0
            losing_signals = 0
            
            for i, (rsi, sma, ema_12, ema_26, atr, signal_price, signal_time, timeframe) in enumerate(signals, 1):
                if rsi and sma and ema_12 and ema_26 and atr and signal_price:
                    print(f"\n📊 シグナル {i}: {timeframe} - {signal_time}")
                    
                    # シグナルタイプを判定
                    buy_condition = rsi < 45 and signal_price > sma and ema_12 > ema_26 and 0.01 <= atr <= 0.10
                    sell_condition = rsi > 55 and signal_price < sma and ema_12 < ema_26 and 0.01 <= atr <= 0.10
                    
                    signal_type = "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    
                    print(f"   シグナルタイプ: {signal_type}")
                    print(f"   エントリー価格: {signal_price:.5f}")
                    print(f"   RSI: {rsi:.2f}, ATR: {atr:.5f}")
                    
                    # シグナル発生後の価格動向を取得
                    # 1時間後、4時間後、1日後の価格を取得
                    time_periods = [
                        (1, "1時間後"),
                        (4, "4時間後"), 
                        (24, "1日後")
                    ]
                    
                    signal_profit = 0
                    best_profit = 0
                    worst_profit = 0
                    
                    for hours, period_name in time_periods:
                        future_time = signal_time + timedelta(hours=hours)
                        
                        # 未来の価格を取得
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
                            {"future_time": future_time}
                        )
                        future_price_result = result.fetchone()
                        
                        if future_price_result:
                            future_price = future_price_result[0]
                            
                            # 利益計算
                            if signal_type == "BUY":
                                profit_pips = (future_price - signal_price) * 100
                            else:  # SELL
                                profit_pips = (signal_price - future_price) * 100
                            
                            profit_percent = (profit_pips / signal_price) * 100
                            
                            print(f"   {period_name}: {future_price:.5f} (利益: {profit_pips:.2f} pips, {profit_percent:.3f}%)")
                            
                            # 最良・最悪の利益を記録
                            if profit_pips > best_profit:
                                best_profit = profit_pips
                            if profit_pips < worst_profit:
                                worst_profit = profit_pips
                            
                            # 1時間後の利益をメインの結果として使用
                            if hours == 1:
                                signal_profit = profit_pips
                        else:
                            print(f"   {period_name}: データなし")
                    
                    # 結果を集計
                    total_profit += signal_profit
                    if signal_profit > 0:
                        winning_signals += 1
                    else:
                        losing_signals += 1
                    
                    print(f"   最良利益: {best_profit:.2f} pips")
                    print(f"   最悪損失: {worst_profit:.2f} pips")
                    print(f"   1時間後利益: {signal_profit:.2f} pips")

            print("\n🔍 2. パフォーマンス統計...")
            
            if len(signals) > 0:
                avg_profit = total_profit / len(signals)
                win_rate = (winning_signals / len(signals)) * 100
                
                print(f"✅ パフォーマンス統計:")
                print(f"   総シグナル数: {len(signals)}件")
                print(f"   勝率: {win_rate:.1f}% ({winning_signals}勝/{len(signals)}件)")
                print(f"   平均利益: {avg_profit:.2f} pips")
                print(f"   総利益: {total_profit:.2f} pips")
                
                if avg_profit > 0:
                    print("   🟢 プラス収益の戦略")
                else:
                    print("   🔴 マイナス収益の戦略")
                
                print(f"\n💡 分析結果:")
                if win_rate > 60:
                    print("   ✅ 高い勝率を示しています")
                elif win_rate > 50:
                    print("   ⚠️ 勝率は平均的です")
                else:
                    print("   ❌ 勝率が低いです")
                
                if avg_profit > 5:
                    print("   ✅ 高い平均利益を示しています")
                elif avg_profit > 0:
                    print("   ⚠️ 平均利益はプラスですが低めです")
                else:
                    print("   ❌ 平均利益がマイナスです")

            print("\n🔍 3. 推奨改善案...")
            
            if len(signals) > 0:
                print("✅ 推奨改善案:")
                if win_rate < 50:
                    print("   📊 条件をより厳しくする（RSI閾値を調整）")
                if avg_profit < 0:
                    print("   📊 ストップロス・利益確定の調整")
                print("   📊 より長期間のデータでの検証")
                print("   📊 他のタイムフレームでの検証")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(verify_signal_performance())
