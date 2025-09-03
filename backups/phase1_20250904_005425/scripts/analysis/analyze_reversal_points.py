#!/usr/bin/env python3
"""
反転ポイント分析

RSIシグナル後の反転ポイントと戻り幅を分析
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


async def analyze_reversal_points():
    """反転ポイントと戻り幅を分析"""
    print("=" * 80)
    print("🔍 反転ポイント分析 - RSIシグナル後の移動平均線分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. RSI < 35 買いシグナル後の反転ポイント分析...")
            
            # RSI < 35のシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12,
                        ti4.value as sma_50
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
                    LEFT JOIN technical_indicators ti4 ON 
                        ti1.timestamp = ti4.timestamp 
                        AND ti1.timeframe = ti4.timeframe 
                        AND ti4.indicator_type = 'SMA_50'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value < 35
                    ORDER BY ti1.timestamp DESC
                    LIMIT 20
                    """
                )
            )
            buy_signals = result.fetchall()
            
            print(f"✅ 買いシグナル: {len(buy_signals)}件")
            
            if len(buy_signals) > 0:
                print("\n📊 買いシグナル後の反転ポイント分析:")
                print("=" * 120)
                print(f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'SMA50':<8} {'1時間後':<10} {'4時間後':<10} {'1日後':<10} {'反転レベル':<12} {'戻り幅':<12}")
                print("=" * 120)
                
                sma_20_reversals = 0
                ema_12_reversals = 0
                sma_50_reversals = 0
                total_analyzed = 0
                
                for rsi, signal_price, signal_time, sma_20, ema_12, sma_50 in buy_signals:
                    if signal_price and sma_20 and ema_12 and sma_50:
                        # 各時間後の価格を取得
                        future_prices = {}
                        reversal_level = "N/A"
                        return_pips = 0
                        
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
                                
                                # 反転ポイントの判定
                                if reversal_level == "N/A":
                                    if future_price >= sma_20:
                                        reversal_level = "SMA20"
                                        return_pips = (future_price - signal_price) * 100
                                        sma_20_reversals += 1
                                    elif future_price >= ema_12:
                                        reversal_level = "EMA12"
                                        return_pips = (future_price - signal_price) * 100
                                        ema_12_reversals += 1
                                    elif future_price >= sma_50:
                                        reversal_level = "SMA50"
                                        return_pips = (future_price - signal_price) * 100
                                        sma_50_reversals += 1
                            else:
                                future_prices[hours] = None
                        
                        # 結果を表示
                        time_str = signal_time.strftime("%m-%d %H:%M")
                        rsi_str = f"{rsi:.1f}"
                        price_str = f"{signal_price:.3f}"
                        sma_20_str = f"{sma_20:.3f}"
                        ema_12_str = f"{ema_12:.3f}"
                        sma_50_str = f"{sma_50:.3f}"
                        
                        price_1h = f"{future_prices.get(1, 0):.3f}" if future_prices.get(1) else "N/A"
                        price_4h = f"{future_prices.get(4, 0):.3f}" if future_prices.get(4) else "N/A"
                        price_1d = f"{future_prices.get(24, 0):.3f}" if future_prices.get(24) else "N/A"
                        
                        return_pips_str = f"{return_pips:.1f}" if return_pips > 0 else "N/A"
                        
                        print(f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {sma_50_str:<8} {price_1h:<10} {price_4h:<10} {price_1d:<10} {reversal_level:<12} {return_pips_str:<12}")
                        
                        total_analyzed += 1
                
                print("=" * 120)
                
                # 統計分析
                print(f"\n📈 買いシグナル反転統計:")
                print(f"- 総分析件数: {total_analyzed}件")
                print(f"- SMA20反転: {sma_20_reversals}件 ({sma_20_reversals/total_analyzed*100:.1f}%)")
                print(f"- EMA12反転: {ema_12_reversals}件 ({ema_12_reversals/total_analyzed*100:.1f}%)")
                print(f"- SMA50反転: {sma_50_reversals}件 ({sma_50_reversals/total_analyzed*100:.1f}%)")
            
            print("\n🔍 2. RSI > 65 売りシグナル後の戻り幅分析...")
            
            # RSI > 65のシグナルを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        pd.close_price as signal_price,
                        ti1.timestamp as signal_time,
                        ti2.value as sma_20,
                        ti3.value as ema_12,
                        ti4.value as sma_50
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
                    LEFT JOIN technical_indicators ti4 ON 
                        ti1.timestamp = ti4.timestamp 
                        AND ti1.timeframe = ti4.timeframe 
                        AND ti4.indicator_type = 'SMA_50'
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.currency_pair = 'USD/JPY'
                    AND ti1.value > 65
                    ORDER BY ti1.timestamp DESC
                    LIMIT 20
                    """
                )
            )
            sell_signals = result.fetchall()
            
            print(f"✅ 売りシグナル: {len(sell_signals)}件")
            
            if len(sell_signals) > 0:
                print("\n📊 売りシグナル後の戻り幅分析:")
                print("=" * 120)
                print(f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'SMA50':<8} {'1時間後':<10} {'4時間後':<10} {'1日後':<10} {'戻りレベル':<12} {'戻り幅':<12}")
                print("=" * 120)
                
                sma_20_returns = 0
                ema_12_returns = 0
                sma_50_returns = 0
                total_analyzed = 0
                
                for rsi, signal_price, signal_time, sma_20, ema_12, sma_50 in sell_signals:
                    if signal_price and sma_20 and ema_12 and sma_50:
                        # 各時間後の価格を取得
                        future_prices = {}
                        return_level = "N/A"
                        return_pips = 0
                        
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
                                
                                # 戻り幅の判定
                                if return_level == "N/A":
                                    if future_price <= sma_20:
                                        return_level = "SMA20"
                                        return_pips = (signal_price - future_price) * 100
                                        sma_20_returns += 1
                                    elif future_price <= ema_12:
                                        return_level = "EMA12"
                                        return_pips = (signal_price - future_price) * 100
                                        ema_12_returns += 1
                                    elif future_price <= sma_50:
                                        return_level = "SMA50"
                                        return_pips = (signal_price - future_price) * 100
                                        sma_50_returns += 1
                            else:
                                future_prices[hours] = None
                        
                        # 結果を表示
                        time_str = signal_time.strftime("%m-%d %H:%M")
                        rsi_str = f"{rsi:.1f}"
                        price_str = f"{signal_price:.3f}"
                        sma_20_str = f"{sma_20:.3f}"
                        ema_12_str = f"{ema_12:.3f}"
                        sma_50_str = f"{sma_50:.3f}"
                        
                        price_1h = f"{future_prices.get(1, 0):.3f}" if future_prices.get(1) else "N/A"
                        price_4h = f"{future_prices.get(4, 0):.3f}" if future_prices.get(4) else "N/A"
                        price_1d = f"{future_prices.get(24, 0):.3f}" if future_prices.get(24) else "N/A"
                        
                        return_pips_str = f"{return_pips:.1f}" if return_pips > 0 else "N/A"
                        
                        print(f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {sma_50_str:<8} {price_1h:<10} {price_4h:<10} {price_1d:<10} {return_level:<12} {return_pips_str:<12}")
                        
                        total_analyzed += 1
                
                print("=" * 120)
                
                # 統計分析
                print(f"\n📈 売りシグナル戻り幅統計:")
                print(f"- 総分析件数: {total_analyzed}件")
                print(f"- SMA20戻り: {sma_20_returns}件 ({sma_20_returns/total_analyzed*100:.1f}%)")
                print(f"- EMA12戻り: {ema_12_returns}件 ({ema_12_returns/total_analyzed*100:.1f}%)")
                print(f"- SMA50戻り: {sma_50_returns}件 ({sma_50_returns/total_analyzed*100:.1f}%)")
            
            print("\n🔍 3. 戦略的洞察...")
            print("反転ポイント分析からの洞察:")
            print("- 買いシグナル: どの移動平均線で反転するか")
            print("- 売りシグナル: どの移動平均線まで戻るか")
            print("- 利益確定: 反転ポイントでの決済")
            print("- リスク管理: 移動平均線でのストップロス")
            
            print("\n🎯 結論:")
            print("✅ 反転ポイントと戻り幅の分析完了")
            print("✅ 移動平均線を条件ではなく分析ツールとして活用")
            print("✅ より実用的なエントリー・決済戦略の構築")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_reversal_points())
