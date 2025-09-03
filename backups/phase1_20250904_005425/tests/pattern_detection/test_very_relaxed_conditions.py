#!/usr/bin/env python3
"""
非常に緩和した条件テストスクリプト

条件を大幅に緩和してシグナル生成をテストします
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


async def test_very_relaxed_conditions():
    """非常に緩和した条件でテスト"""
    print("=" * 80)
    print("🧪 非常に緩和した条件テスト")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 非常に緩和した条件でのテスト...")

            # 条件を大幅に緩和
            print("✅ テスト条件:")
            print("   買い: RSI < 45 + 価格 > SMA20 + EMA12 > EMA26")
            print("   売り: RSI > 55 + 価格 < SMA20 + EMA12 < EMA26")

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
                    AND (
                        (ti1.value < 45 AND pd.close_price > ti2.value AND ti3.value > ti4.value) OR
                        (ti1.value > 55 AND pd.close_price < ti2.value AND ti3.value < ti4.value)
                    )
                    ORDER BY ti1.timestamp DESC
                    LIMIT 20
                    """
                )
            )
            relaxed_signals = result.fetchall()

            print(f"✅ 非常に緩和した条件でのシグナル: {len(relaxed_signals)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in relaxed_signals:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 45 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 55 and price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    print(
                        f"  📊 {timeframe} - {timestamp}: {signal_type} (RSI={rsi:.2f}, 価格={price:.5f})"
                    )

            print("\n🔍 2. RSIのみの条件テスト...")

            # RSIのみの条件でテスト
            print("✅ RSIのみの条件テスト:")
            print("   買い: RSI < 40（価格・EMA条件なし）")
            print("   売り: RSI > 60（価格・EMA条件なし）")

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
                    ORDER BY ti1.timestamp DESC
                    LIMIT 20
                    """
                )
            )
            rsi_only_signals = result.fetchall()

            print(f"✅ RSIのみの条件でのシグナル: {len(rsi_only_signals)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in rsi_only_signals:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 40
                    sell_condition = rsi > 60

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    print(
                        f"  📊 {timeframe} - {timestamp}: {signal_type} (RSI={rsi:.2f}, 価格={price:.5f})"
                    )

            print("\n🔍 3. 価格・EMA条件のみのテスト...")

            # 価格・EMA条件のみでテスト
            print("✅ 価格・EMA条件のみのテスト:")
            print("   買い: 価格 > SMA20 + EMA12 > EMA26（RSI条件なし）")
            print("   売り: 価格 < SMA20 + EMA12 < EMA26（RSI条件なし）")

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
                    AND (
                        (pd.close_price > ti2.value AND ti3.value > ti4.value) OR
                        (pd.close_price < ti2.value AND ti3.value < ti4.value)
                    )
                    ORDER BY ti1.timestamp DESC
                    LIMIT 20
                    """
                )
            )
            price_ema_signals = result.fetchall()

            print(f"✅ 価格・EMA条件のみでのシグナル: {len(price_ema_signals)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in price_ema_signals:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = price > sma and ema_12 > ema_26
                    sell_condition = price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    print(
                        f"  📊 {timeframe} - {timestamp}: {signal_type} (RSI={rsi:.2f}, 価格={price:.5f})"
                    )

            print("\n🎯 4. 推奨設定...")

            print("✅ 分析結果:")
            print(f"   非常に緩和した条件: {len(relaxed_signals)}件")
            print(f"   RSIのみの条件: {len(rsi_only_signals)}件")
            print(f"   価格・EMA条件のみ: {len(price_ema_signals)}件")

            if len(relaxed_signals) > 0:
                print("💡 推奨: 条件を大幅に緩和する（RSI < 45 / RSI > 55）")
            elif len(rsi_only_signals) > 0:
                print("💡 推奨: RSI条件のみを使用する")
            elif len(price_ema_signals) > 0:
                print("💡 推奨: 価格・EMA条件のみを使用する")
            else:
                print("💡 推奨: 他の検出器（ボリンジャーバンド）をテストする")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_very_relaxed_conditions())
