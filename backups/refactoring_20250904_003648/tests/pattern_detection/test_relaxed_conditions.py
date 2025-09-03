#!/usr/bin/env python3
"""
条件緩和シグナル生成テストスクリプト

RSIの条件を緩和してシグナル生成をテストします
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


async def test_relaxed_conditions():
    """条件緩和テスト"""
    print("=" * 80)
    print("🧪 条件緩和シグナル生成テスト")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 現在の条件での分析...")

            # 現在の条件（RSI < 30 または RSI > 70）
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
                    AND (ti1.value < 30 OR ti1.value > 70)
                    AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            current_conditions = result.fetchall()

            print(f"✅ 現在の条件（RSI < 30 または RSI > 70）: {len(current_conditions)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in current_conditions:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 30 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 70 and price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    status = "✅ シグナル生成" if signal_type != "NONE" else "❌ 条件不満足"

                    print(f"  📊 {timeframe}: RSI={rsi:.2f} | {signal_type} {status}")

            print("\n🔍 2. 緩和条件での分析...")

            # 緩和条件（RSI < 35 または RSI > 65）
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
                    AND (ti1.value < 35 OR ti1.value > 65)
                    AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            relaxed_conditions = result.fetchall()

            print(f"✅ 緩和条件（RSI < 35 または RSI > 65）: {len(relaxed_conditions)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in relaxed_conditions:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 35 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 65 and price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    status = "✅ シグナル生成" if signal_type != "NONE" else "❌ 条件不満足"

                    ema_momentum = "上昇" if ema_12 > ema_26 else "下降"
                    print(
                        f"  📊 {timeframe}: RSI={rsi:.2f}, 価格={price:.5f}, SMA20={sma:.5f}"
                    )
                    print(
                        f"     EMA12={ema_12:.5f}, EMA26={ema_26:.5f} | EMA傾き: {ema_momentum}"
                    )
                    print(f"     {signal_type} {status}")

            print("\n🔍 3. さらに緩和した条件での分析...")

            # さらに緩和条件（RSI < 40 または RSI > 60）
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
                    AND (ti1.value < 40 OR ti1.value > 60)
                    AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            more_relaxed_conditions = result.fetchall()

            print(f"✅ さらに緩和条件（RSI < 40 または RSI > 60）: {len(more_relaxed_conditions)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in more_relaxed_conditions:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 40 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 60 and price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    status = "✅ シグナル生成" if signal_type != "NONE" else "❌ 条件不満足"

                    ema_momentum = "上昇" if ema_12 > ema_26 else "下降"
                    print(
                        f"  📊 {timeframe}: RSI={rsi:.2f}, 価格={price:.5f}, SMA20={sma:.5f}"
                    )
                    print(
                        f"     EMA12={ema_12:.5f}, EMA26={ema_26:.5f} | EMA傾き: {ema_momentum}"
                    )
                    print(f"     {signal_type} {status}")

            print("\n🎯 4. 推奨設定...")

            print("✅ 推奨設定:")
            print("   📊 現在の条件: RSI < 30 または RSI > 70（厳しすぎる）")
            print("   📊 推奨条件: RSI < 35 または RSI > 65（バランス良い）")
            print("   📊 緩和条件: RSI < 40 または RSI > 60（頻繁すぎる可能性）")

            print("\n💡 理由:")
            print("   📊 RSI=30-35: 過売り圏の前段階でエントリー")
            print("   📊 RSI=65-70: 過買い圏の前段階でエントリー")
            print("   📊 より早いエントリーでリスク管理を強化")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_relaxed_conditions())
