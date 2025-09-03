#!/usr/bin/env python3
"""
現在の条件分析スクリプト

なぜシグナルが生成されないのかを詳しく分析します
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def analyze_current_conditions():
    """現在の条件を詳しく分析"""
    print("=" * 80)
    print("🔍 現在の条件詳細分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 最新データの詳細分析...")
            
            # 最新のデータを取得
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        ti2.value as sma_value,
                        ti3.value as ema_12,
                        ti4.value as ema_26,
                        pd.close_price as current_price,
                        ti1.timestamp,
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
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                    ORDER BY ti1.timestamp DESC
                    LIMIT 5
                    """
                )
            )
            latest_data = result.fetchall()
            
            print(f"✅ 最新データ: {len(latest_data)}件")
            for rsi, sma, ema_12, ema_26, price, timestamp, timeframe in latest_data:
                if rsi and sma and ema_12 and ema_26 and price:
                    print(f"\n📊 {timeframe} - {timestamp}")
                    print(f"   RSI: {rsi:.2f}")
                    print(f"   価格: {price:.5f}")
                    print(f"   SMA20: {sma:.5f}")
                    print(f"   EMA12: {ema_12:.5f}")
                    print(f"   EMA26: {ema_26:.5f}")
                    
                    # 条件チェック
                    print(f"\n   🔍 条件チェック:")
                    
                    # 買い条件
                    rsi_buy = rsi < 35
                    price_buy = price > sma
                    ema_buy = ema_12 > ema_26
                    
                    print(f"   買い条件:")
                    print(f"     RSI < 35: {rsi:.2f} < 35 = {rsi_buy}")
                    print(f"     価格 > SMA20: {price:.5f} > {sma:.5f} = {price_buy}")
                    print(f"     EMA12 > EMA26: {ema_12:.5f} > {ema_26:.5f} = {ema_buy}")
                    
                    buy_signal = rsi_buy and price_buy and ema_buy
                    print(f"     買いシグナル: {buy_signal}")
                    
                    # 売り条件
                    rsi_sell = rsi > 65
                    price_sell = price < sma
                    ema_sell = ema_12 < ema_26
                    
                    print(f"   売り条件:")
                    print(f"     RSI > 65: {rsi:.2f} > 65 = {rsi_sell}")
                    print(f"     価格 < SMA20: {price:.5f} < {sma:.5f} = {price_sell}")
                    print(f"     EMA12 < EMA26: {ema_12:.5f} < {ema_26:.5f} = {ema_sell}")
                    
                    sell_signal = rsi_sell and price_sell and ema_sell
                    print(f"     売りシグナル: {sell_signal}")

            print("\n🔍 2. 過去のシグナル生成可能性をチェック...")
            
            # 過去30日間でシグナルが生成される可能性があったデータをチェック
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        ti2.value as sma_value,
                        ti3.value as ema_12,
                        ti4.value as ema_26,
                        pd.close_price as current_price,
                        ti1.timestamp,
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
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.timestamp >= NOW() - INTERVAL '30 days'
                    AND (
                        (ti1.value < 35 AND pd.close_price > ti2.value AND ti3.value > ti4.value) OR
                        (ti1.value > 65 AND pd.close_price < ti2.value AND ti3.value < ti4.value)
                    )
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            potential_signals = result.fetchall()
            
            print(f"✅ 過去30日間でシグナル生成可能性: {len(potential_signals)}件")
            for rsi, sma, ema_12, ema_26, price, timestamp, timeframe in potential_signals:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 35 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 65 and price < sma and ema_12 < ema_26
                    
                    signal_type = "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    print(f"  📊 {timeframe} - {timestamp}: {signal_type} (RSI={rsi:.2f})")

            print("\n🔍 3. 条件をさらに緩和したテスト...")
            
            # 条件をさらに緩和してテスト
            print("✅ さらに緩和した条件テスト:")
            print("   買い: RSI < 40 + 価格 > SMA20 + EMA12 > EMA26")
            print("   売り: RSI > 60 + 価格 < SMA20 + EMA12 < EMA26")
            
            result = await db_session.execute(
                text(
                    """
                    SELECT 
                        ti1.value as rsi_value,
                        ti2.value as sma_value,
                        ti3.value as ema_12,
                        ti4.value as ema_26,
                        pd.close_price as current_price,
                        ti1.timestamp,
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
                    LEFT JOIN price_data pd ON 
                        ti1.timestamp = pd.timestamp
                        AND ti1.currency_pair = pd.currency_pair
                    WHERE ti1.indicator_type = 'RSI'
                    AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                    AND (
                        (ti1.value < 40 AND pd.close_price > ti2.value AND ti3.value > ti4.value) OR
                        (ti1.value > 60 AND pd.close_price < ti2.value AND ti3.value < ti4.value)
                    )
                    ORDER BY ti1.timestamp DESC
                    LIMIT 5
                    """
                )
            )
            more_relaxed_signals = result.fetchall()
            
            print(f"✅ さらに緩和した条件でのシグナル: {len(more_relaxed_signals)}件")
            for rsi, sma, ema_12, ema_26, price, timestamp, timeframe in more_relaxed_signals:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 40 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 60 and price < sma and ema_12 < ema_26
                    
                    signal_type = "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    print(f"  📊 {timeframe} - {timestamp}: {signal_type} (RSI={rsi:.2f})")

            print("\n🎯 4. 推奨アクション...")
            
            if len(potential_signals) == 0:
                print("❌ 過去30日間でシグナル生成可能性なし")
                print("💡 推奨アクション:")
                print("   1. 条件をさらに緩和する（RSI < 40 / RSI > 60）")
                print("   2. 他の検出器（ボリンジャーバンド）をテストする")
                print("   3. より長期間のデータでテストする")
            else:
                print(f"✅ 過去30日間で{len(potential_signals)}件のシグナル生成可能性あり")
                print("💡 システムは正常に動作しています")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_current_conditions())
