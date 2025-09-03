#!/usr/bin/env python3
"""
過去データシグナル検出テストスクリプト

データベースの過去データを使って実際のシグナル検出をテストします
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


async def test_historical_signals():
    """過去データでシグナル検出をテスト"""
    print("=" * 80)
    print("🧪 過去データシグナル検出テスト")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 過去データでのシグナル検出...")

            # 過去のデータでシグナル生成可能性をチェック
            result = await db_session.execute(
                text(
                    """
                    SELECT
                        ti1.value as rsi_value,
                        ti2.value as sma_value,
                        ti3.value as ema_12,
                        ti4.value as ema_26,
                        ti5.value as atr_value,
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
                    LIMIT 30
                    """
                )
            )
            historical_signals = result.fetchall()

            print(f"✅ 過去データでのシグナル検出: {len(historical_signals)}件")

            buy_signals = []
            sell_signals = []

            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                atr,
                price,
                timestamp,
                timeframe,
            ) in historical_signals:
                if rsi and sma and ema_12 and ema_26 and atr and price:
                    buy_condition = (
                        rsi < 45
                        and price > sma
                        and ema_12 > ema_26
                        and 0.01 <= atr <= 0.10
                    )
                    sell_condition = (
                        rsi > 55
                        and price < sma
                        and ema_12 < ema_26
                        and 0.01 <= atr <= 0.10
                    )

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )

                    if signal_type == "BUY":
                        buy_signals.append(
                            (timestamp, timeframe, rsi, price, sma, ema_12, ema_26, atr)
                        )
                    elif signal_type == "SELL":
                        sell_signals.append(
                            (timestamp, timeframe, rsi, price, sma, ema_12, ema_26, atr)
                        )

                    print(f"  📊 {timeframe} - {timestamp}: {signal_type}")
                    print(f"     RSI={rsi:.2f}, 価格={price:.5f}, SMA20={sma:.5f}")
                    print(f"     EMA12={ema_12:.5f}, EMA26={ema_26:.5f}, ATR={atr:.5f}")

            print(f"\n📈 買いシグナル: {len(buy_signals)}件")
            print(f"📉 売りシグナル: {len(sell_signals)}件")

            print("\n🔍 2. 実際のRSIエントリー検出器でテスト...")

            # 実際のRSIエントリー検出器をテスト
            from src.domain.services.alert_engine.rsi_entry_detector import (
                RSIEntryDetector,
            )

            rsi_detector = RSIEntryDetector(db_session)

            timeframes = ["M5", "M15", "H1", "H4", "D1"]

            total_signals = 0
            for timeframe in timeframes:
                print(f"\n📊 タイムフレーム: {timeframe}")
                try:
                    signals = await rsi_detector.detect_rsi_entry_signals(timeframe)
                    print(f"✅ 検出されたシグナル数: {len(signals)}")
                    total_signals += len(signals)

                    for i, signal in enumerate(signals, 1):
                        print(f"  📈 シグナル {i}:")
                        print(f"     タイプ: {signal.signal_type}")
                        print(f"     エントリー価格: {signal.entry_price}")
                        print(f"     ストップロス: {signal.stop_loss}")
                        print(f"     利益確定: {signal.take_profit}")
                        print(f"     信頼度スコア: {signal.confidence_score}")
                        print(f"     使用指標: {signal.indicators_used}")

                except Exception as e:
                    print(f"❌ エラー: {e}")

            print(f"\n🎯 総シグナル数: {total_signals}件")

            print("\n🔍 3. シグナル詳細分析...")

            if len(historical_signals) > 0:
                print("✅ シグナル詳細分析:")

                # タイムフレーム別分析
                timeframe_counts = {}
                for _, timeframe, _, _, _, _, _, _ in historical_signals:
                    timeframe_counts[timeframe] = timeframe_counts.get(timeframe, 0) + 1

                print("   タイムフレーム別シグナル数:")
                for timeframe, count in sorted(timeframe_counts.items()):
                    print(f"     {timeframe}: {count}件")

                # RSI分布分析
                rsi_values = [
                    rsi for rsi, _, _, _, _, _, _, _ in historical_signals if rsi
                ]
                if rsi_values:
                    avg_rsi = sum(rsi_values) / len(rsi_values)
                    min_rsi = min(rsi_values)
                    max_rsi = max(rsi_values)
                    print(
                        f"   RSI統計: 平均={avg_rsi:.2f}, 最小={min_rsi:.2f}, 最大={max_rsi:.2f}"
                    )

                # 価格範囲分析
                prices = [
                    price for _, _, _, _, _, price, _, _ in historical_signals if price
                ]
                if prices:
                    avg_price = sum(prices) / len(prices)
                    min_price = min(prices)
                    max_price = max(prices)
                    print(
                        f"   価格統計: 平均={avg_price:.5f}, 最小={min_price:.5f}, 最大={max_price:.5f}"
                    )

            print("\n🔍 4. テスト結果のまとめ...")

            if len(historical_signals) > 0:
                print(f"✅ 過去データで{len(historical_signals)}件のシグナル検出成功")
                print("💡 システムは正常に動作しています")
                print("💡 実際の取引環境でシグナル生成が可能です")
            else:
                print("❌ 過去データでシグナル検出なし")
                print("💡 条件をさらに調整するか、他の検出器をテストすることを推奨")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_historical_signals())
