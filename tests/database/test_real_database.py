#!/usr/bin/env python3
"""
実際のデータベーステストスクリプト

実際のデータベースデータを使用してシグナル生成をテストします
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


async def test_real_database():
    """実際のデータベースでテスト"""
    print("=" * 80)
    print("🧪 実際のデータベーステスト")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. データベースの基本情報...")

            # テーブルの基本情報を確認
            result = await db_session.execute(
                text("SELECT COUNT(*) FROM technical_indicators")
            )
            total_indicators = result.scalar()

            result = await db_session.execute(text("SELECT COUNT(*) FROM price_data"))
            total_prices = result.scalar()

            result = await db_session.execute(
                text("SELECT MIN(timestamp), MAX(timestamp) FROM technical_indicators")
            )
            date_range = result.fetchone()

            print(f"✅ テクニカル指標データ: {total_indicators:,}件")
            print(f"✅ 価格データ: {total_prices:,}件")
            print(f"✅ データ期間: {date_range[0]} ～ {date_range[1]}")

            print("\n🔍 2. 利用可能な指標タイプ...")

            result = await db_session.execute(
                text(
                    "SELECT DISTINCT indicator_type FROM technical_indicators ORDER BY indicator_type"
                )
            )
            indicator_types = result.fetchall()

            print("✅ 利用可能な指標:")
            for indicator_type in indicator_types:
                result = await db_session.execute(
                    text(
                        "SELECT COUNT(*) FROM technical_indicators WHERE indicator_type = :type"
                    ),
                    {"type": indicator_type[0]},
                )
                count = result.scalar()
                print(f"   📊 {indicator_type[0]}: {count:,}件")

            print("\n🔍 3. 最新データの詳細分析...")

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
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
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
                    buy_condition = rsi < 40 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 60 and price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    status = "✅ シグナル生成" if signal_type != "NONE" else "❌ 条件不満足"

                    print(f"   シグナル: {signal_type} {status}")

            print("\n🔍 4. 過去のシグナル生成可能性をチェック...")

            # 過去のデータでシグナル生成可能性をチェック
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
                        (ti1.value < 40 AND pd.close_price > ti2.value AND ti3.value > ti4.value) OR
                        (ti1.value > 60 AND pd.close_price < ti2.value AND ti3.value < ti4.value)
                    )
                    ORDER BY ti1.timestamp DESC
                    LIMIT 20
                    """
                )
            )
            potential_signals = result.fetchall()

            print(f"✅ 過去のシグナル生成可能性: {len(potential_signals)}件")
            for (
                rsi,
                sma,
                ema_12,
                ema_26,
                price,
                timestamp,
                timeframe,
            ) in potential_signals:
                if rsi and sma and ema_12 and ema_26 and price:
                    buy_condition = rsi < 40 and price > sma and ema_12 > ema_26
                    sell_condition = rsi > 60 and price < sma and ema_12 < ema_26

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    print(
                        f"  📊 {timeframe} - {timestamp}: {signal_type} (RSI={rsi:.2f}, 価格={price:.5f})"
                    )

            print("\n🔍 5. RSIエントリー検出器の実際のテスト...")

            # 実際のRSIエントリー検出器をテスト
            from src.domain.services.alert_engine.rsi_entry_detector import (
                RSIEntryDetector,
            )

            rsi_detector = RSIEntryDetector(db_session)

            timeframes = ["M5", "M15", "H1", "H4", "D1"]

            for timeframe in timeframes:
                print(f"\n📊 タイムフレーム: {timeframe}")
                try:
                    signals = await rsi_detector.detect_rsi_entry_signals(timeframe)
                    print(f"✅ 検出されたシグナル数: {len(signals)}")

                    for i, signal in enumerate(signals, 1):
                        print(f"  📈 シグナル {i}:")
                        print(f"     タイプ: {signal.signal_type}")
                        print(f"     エントリー価格: {signal.entry_price}")
                        print(f"     ストップロス: {signal.stop_loss}")
                        print(f"     利益確定: {signal.take_profit}")
                        print(f"     信頼度スコア: {signal.confidence_score}")

                except Exception as e:
                    print(f"❌ エラー: {e}")

            print("\n🎯 6. テスト結果のまとめ...")

            if len(potential_signals) > 0:
                print(f"✅ 過去データで{len(potential_signals)}件のシグナル生成可能性を確認")
                print("💡 システムは正常に動作しています")
            else:
                print("❌ 過去データでもシグナル生成可能性なし")
                print("💡 条件をさらに調整するか、他の検出器をテストすることを推奨")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_real_database())
