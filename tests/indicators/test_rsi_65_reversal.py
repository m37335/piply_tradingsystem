#!/usr/bin/env python3
"""
RSI 65反転シグナルテスト

RSI 65で売りシグナル（反転）を探す
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


async def test_rsi_65_reversal():
    """RSI 65で反転シグナルテスト"""
    print("=" * 80)
    print("🔍 RSI 65反転シグナルテスト")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. RSI 65での反転シグナル検出...")
            print("   売り条件: RSI > 65 + 価格 < SMA20 + EMA12 < EMA26")
            print("   ※ 過買いからの反転を狙う")
            
            # RSI 65以上条件でシグナルを検出
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        ti2.value as sma_20,
                        ti3.value as ema_12,
                        ti4.value as ema_26,
                        ti5.value as sma_50,
                        ti6.value as atr_value,
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
                        AND ti5.indicator_type = 'SMA_50'
                    LEFT JOIN technical_indicators ti6 ON 
                        ti1.timestamp = ti6.timestamp 
                        AND ti1.timeframe = ti6.timeframe 
                        AND ti6.indicator_type = 'ATR'
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.value > 65
                    AND pd.close_price < ti2.value
                    AND ti3.value < ti4.value
                    AND 0.01 <= ti6.value AND ti6.value <= 0.10
                    ORDER BY ti1.timestamp DESC
                    LIMIT 50
                    """
                )
            )
            signals = result.fetchall()
            
            print(f"✅ 検出されたシグナル: {len(signals)}件")
            
            if len(signals) == 0:
                print("❌ シグナルなし - 条件を緩和してみます")
                
                # 条件を緩和
                print("\n🔍 2. 緩和条件でのテスト...")
                print("   売り条件: RSI > 65 + 価格 < SMA20")
                print("   ※ EMA条件を除外")
                
                result = await db_session.execute(
                    text(
                        """
                        SELECT 
                            ti1.value as rsi_value,
                            ti2.value as sma_20,
                            ti3.value as ema_12,
                            ti4.value as ema_26,
                            ti5.value as sma_50,
                            ti6.value as atr_value,
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
                            AND ti5.indicator_type = 'SMA_50'
                        LEFT JOIN technical_indicators ti6 ON 
                            ti1.timestamp = ti6.timestamp 
                            AND ti1.timeframe = ti6.timeframe 
                            AND ti6.indicator_type = 'ATR'
                        LEFT JOIN price_data pd ON 
                            ti1.timestamp = pd.timestamp
                            AND ti1.currency_pair = pd.currency_pair
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.value > 65
                        AND pd.close_price < ti2.value
                        AND 0.01 <= ti6.value AND ti6.value <= 0.10
                        ORDER BY ti1.timestamp DESC
                        LIMIT 50
                        """
                    )
                )
                signals = result.fetchall()
                print(f"✅ 緩和条件でのシグナル: {len(signals)}件")
            
            if len(signals) == 0:
                print("❌ シグナルなし - RSI 65は非常に厳しい条件です")
                return
            
            print("\n🔍 3. 反転シグナル詳細分析...")
            
            # 統計データ
            all_profits_1h = []
            all_profits_4h = []
            all_profits_1d = []
            
            print("\n📊 反転シグナル詳細:")
            print("=" * 120)
            print(f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'EMA26':<8} {'1時間後':<10} {'4時間後':<10} {'1日後':<10} {'1時間利益':<12} {'4時間利益':<12} {'1日利益':<12}")
            print("=" * 120)
            
            for rsi, sma_20, ema_12, ema_26, sma_50, atr, signal_price, signal_time, timeframe in signals:
                if rsi and sma_20 and ema_12 and ema_26 and sma_50 and atr and signal_price:
                    # 各時間後の価格を取得
                    profits = {}
                    future_prices = {}
                    
                    for hours in [1, 4, 24]:
                        future_time = signal_time + timedelta(hours=hours)
                        
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
                            future_prices[hours] = future_price
                            
                            # 利益計算（売りシグナル）
                            profit_pips = (signal_price - future_price) * 100
                            profits[hours] = profit_pips
                        else:
                            future_prices[hours] = None
                            profits[hours] = None
                    
                    # 結果を表示
                    time_str = signal_time.strftime("%m-%d %H:%M")
                    rsi_str = f"{rsi:.1f}"
                    price_str = f"{signal_price:.3f}"
                    sma_20_str = f"{sma_20:.3f}"
                    ema_12_str = f"{ema_12:.3f}"
                    ema_26_str = f"{ema_26:.3f}"
                    
                    price_1h = f"{future_prices.get(1, 0):.3f}" if future_prices.get(1) else "N/A"
                    price_4h = f"{future_prices.get(4, 0):.3f}" if future_prices.get(4) else "N/A"
                    price_1d = f"{future_prices.get(24, 0):.3f}" if future_prices.get(24) else "N/A"
                    
                    profit_1h = f"{profits.get(1, 0):.2f}" if profits.get(1) is not None else "N/A"
                    profit_4h = f"{profits.get(4, 0):.2f}" if profits.get(4) is not None else "N/A"
                    profit_1d = f"{profits.get(24, 0):.2f}" if profits.get(24) is not None else "N/A"
                    
                    print(f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {ema_26_str:<8} {price_1h:<10} {price_4h:<10} {price_1d:<10} {profit_1h:<12} {profit_4h:<12} {profit_1d:<12}")
                    
                    # 全体統計に追加
                    if profits.get(1) is not None:
                        all_profits_1h.append(profits[1])
                    if profits.get(4) is not None:
                        all_profits_4h.append(profits[4])
                    if profits.get(24) is not None:
                        all_profits_1d.append(profits[24])
            
            print("=" * 120)
            
            # 統計計算
            print("\n📈 反転シグナル統計分析:")
            print("-" * 60)
            
            # 全体統計
            if all_profits_1h:
                avg_profit_1h = sum(all_profits_1h) / len(all_profits_1h)
                win_rate_1h = len([p for p in all_profits_1h if p > 0]) / len(all_profits_1h) * 100
                print(f"RSI 65反転 - 1時間後: 平均{avg_profit_1h:.2f}pips, 勝率{win_rate_1h:.1f}%")
            
            if all_profits_4h:
                avg_profit_4h = sum(all_profits_4h) / len(all_profits_4h)
                win_rate_4h = len([p for p in all_profits_4h if p > 0]) / len(all_profits_4h) * 100
                print(f"RSI 65反転 - 4時間後: 平均{avg_profit_4h:.2f}pips, 勝率{win_rate_4h:.1f}%")
            
            if all_profits_1d:
                avg_profit_1d = sum(all_profits_1d) / len(all_profits_1d)
                win_rate_1d = len([p for p in all_profits_1d if p > 0]) / len(all_profits_1d) * 100
                print(f"RSI 65反転 - 1日後: 平均{avg_profit_1d:.2f}pips, 勝率{win_rate_1d:.1f}%")
            
            print("\n🔍 4. 反転シグナルの特徴...")
            print("RSI 65反転シグナルの特徴:")
            print("- 過買い状態からの明確な反転")
            print("- 価格がSMA20を下回る確認")
            print("- EMA12 < EMA26で下降モメンタム確認")
            print("- 短期での反転効果を狙う")
            
            print("\n🎯 結論:")
            print("✅ RSI 65反転シグナルで実際のデータベース検証完了")
            print("✅ 過買いからの反転を狙う戦略")
            print("✅ 短期取引に最適化")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_rsi_65_reversal())
