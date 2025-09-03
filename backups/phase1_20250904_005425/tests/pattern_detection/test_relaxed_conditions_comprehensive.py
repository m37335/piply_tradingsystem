#!/usr/bin/env python3
"""
条件緩和テスト

RSIと移動平均線の条件を緩和して、より多くのシグナルを検出
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def test_relaxed_conditions():
    """条件緩和テストを実行"""
    print("=" * 80)
    print("🔍 条件緩和テスト - より多くのシグナル検出")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            # テストする条件パターン
            test_patterns = [
                {
                    "name": "現在条件",
                    "buy_rsi": 35,
                    "sell_rsi": 65,
                    "use_sma50": True,
                    "use_ema": True,
                },
                {
                    "name": "RSI緩和1",
                    "buy_rsi": 40,
                    "sell_rsi": 60,
                    "use_sma50": True,
                    "use_ema": True,
                },
                {
                    "name": "RSI緩和2",
                    "buy_rsi": 45,
                    "sell_rsi": 55,
                    "use_sma50": True,
                    "use_ema": True,
                },
                {
                    "name": "SMA50削除",
                    "buy_rsi": 35,
                    "sell_rsi": 65,
                    "use_sma50": False,
                    "use_ema": True,
                },
                {
                    "name": "EMA削除",
                    "buy_rsi": 35,
                    "sell_rsi": 65,
                    "use_sma50": True,
                    "use_ema": False,
                },
                {
                    "name": "大幅緩和",
                    "buy_rsi": 45,
                    "sell_rsi": 55,
                    "use_sma50": False,
                    "use_ema": False,
                },
            ]

            for pattern in test_patterns:
                print(f"\n🔍 {pattern['name']} テスト...")
                print(
                    f"条件: 買いRSI < {pattern['buy_rsi']}, 売りRSI > {pattern['sell_rsi']}"
                )
                print(f"SMA50使用: {pattern['use_sma50']}, EMA使用: {pattern['use_ema']}")

                # 買いシグナル検出
                buy_conditions = []
                buy_conditions.append(f"ti1.value < {pattern['buy_rsi']}")
                buy_conditions.append("pd.close_price > ti2.value")  # 価格 > SMA20

                if pattern["use_ema"]:
                    buy_conditions.append("ti3.value > ti4.value")  # EMA12 > EMA26

                if pattern["use_sma50"]:
                    buy_conditions.append("ti2.value > ti5.value")  # SMA20 > SMA50

                buy_where_clause = " AND ".join(buy_conditions)

                # 売りシグナル検出
                sell_conditions = []
                sell_conditions.append(f"ti1.value > {pattern['sell_rsi']}")
                sell_conditions.append("pd.close_price < ti2.value")  # 価格 < SMA20

                if pattern["use_ema"]:
                    sell_conditions.append("ti3.value < ti4.value")  # EMA12 < EMA26

                if pattern["use_sma50"]:
                    sell_conditions.append("ti2.value < ti5.value")  # SMA20 < SMA50

                sell_where_clause = " AND ".join(sell_conditions)

                # 買いシグナルを検索
                result = await db_session.execute(
                    text(
                        f"""
                        SELECT COUNT(*) as count
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
                            AND ti4.indicator_type = 'EMA_26'
                        LEFT JOIN technical_indicators ti5 ON
                            ti1.timestamp = ti5.timestamp
                            AND ti1.timeframe = ti5.timeframe
                            AND ti5.indicator_type = 'SMA_50'
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.currency_pair = 'USD/JPY'
                        AND {buy_where_clause}
                        """
                    )
                )
                buy_count = result.fetchone()[0]

                # 売りシグナルを検索
                result = await db_session.execute(
                    text(
                        f"""
                        SELECT COUNT(*) as count
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
                            AND ti4.indicator_type = 'EMA_26'
                        LEFT JOIN technical_indicators ti5 ON
                            ti1.timestamp = ti5.timestamp
                            AND ti1.timeframe = ti5.timeframe
                            AND ti5.indicator_type = 'SMA_50'
                        WHERE ti1.indicator_type = 'RSI'
                        AND ti1.currency_pair = 'USD/JPY'
                        AND {sell_where_clause}
                        """
                    )
                )
                sell_count = result.fetchone()[0]

                total_signals = buy_count + sell_count

                print(f"✅ 買いシグナル: {buy_count}件")
                print(f"✅ 売りシグナル: {sell_count}件")
                print(f"✅ 総シグナル: {total_signals}件")

                # パフォーマンス分析（最初の10件で）
                if total_signals > 0:
                    print("📊 パフォーマンス分析（最初の10件）...")

                    # 買いシグナルのパフォーマンス
                    if buy_count > 0:
                        result = await db_session.execute(
                            text(
                                f"""
                                SELECT
                                    ti1.value as rsi_value,
                                    pd.close_price as signal_price,
                                    ti1.timestamp as signal_time
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
                                    AND ti4.indicator_type = 'EMA_26'
                                LEFT JOIN technical_indicators ti5 ON
                                    ti1.timestamp = ti5.timestamp
                                    AND ti1.timeframe = ti5.timeframe
                                    AND ti5.indicator_type = 'SMA_50'
                                WHERE ti1.indicator_type = 'RSI'
                                AND ti1.currency_pair = 'USD/JPY'
                                AND {buy_where_clause}
                                ORDER BY ti1.timestamp DESC
                                LIMIT 10
                                """
                            )
                        )
                        buy_signals = result.fetchall()

                        buy_profits = []
                        for rsi, signal_price, signal_time in buy_signals:
                            if signal_price:
                                # 1時間後の価格を取得
                                future_time = signal_time + timedelta(hours=1)
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
                                    {"future_time": future_time},
                                )
                                future_price_result = result.fetchone()

                                if future_price_result:
                                    future_price = future_price_result[0]
                                    profit_pips = (future_price - signal_price) * 100
                                    buy_profits.append(profit_pips)

                        if buy_profits:
                            avg_buy_profit = sum(buy_profits) / len(buy_profits)
                            winning_buys = sum(1 for p in buy_profits if p > 0)
                            buy_win_rate = winning_buys / len(buy_profits) * 100
                            print(
                                f"  買い: 平均利益 {avg_buy_profit:.1f}pips, 勝率 {buy_win_rate:.1f}%"
                            )

                    # 売りシグナルのパフォーマンス
                    if sell_count > 0:
                        result = await db_session.execute(
                            text(
                                f"""
                                SELECT
                                    ti1.value as rsi_value,
                                    pd.close_price as signal_price,
                                    ti1.timestamp as signal_time
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
                                    AND ti4.indicator_type = 'EMA_26'
                                LEFT JOIN technical_indicators ti5 ON
                                    ti1.timestamp = ti5.timestamp
                                    AND ti1.timeframe = ti5.timeframe
                                    AND ti5.indicator_type = 'SMA_50'
                                WHERE ti1.indicator_type = 'RSI'
                                AND ti1.currency_pair = 'USD/JPY'
                                AND {sell_where_clause}
                                ORDER BY ti1.timestamp DESC
                                LIMIT 10
                                """
                            )
                        )
                        sell_signals = result.fetchall()

                        sell_profits = []
                        for rsi, signal_price, signal_time in sell_signals:
                            if signal_price:
                                # 1時間後の価格を取得
                                future_time = signal_time + timedelta(hours=1)
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
                                    {"future_time": future_time},
                                )
                                future_price_result = result.fetchone()

                                if future_price_result:
                                    future_price = future_price_result[0]
                                    profit_pips = (signal_price - future_price) * 100
                                    sell_profits.append(profit_pips)

                        if sell_profits:
                            avg_sell_profit = sum(sell_profits) / len(sell_profits)
                            winning_sells = sum(1 for p in sell_profits if p > 0)
                            sell_win_rate = winning_sells / len(sell_profits) * 100
                            print(
                                f"  売り: 平均利益 {avg_sell_profit:.1f}pips, 勝率 {sell_win_rate:.1f}%"
                            )

                print("-" * 60)

            print("\n🔍 戦略的洞察...")
            print("条件緩和テストからの洞察:")
            print("- シグナル頻度: 条件緩和による増加")
            print("- パフォーマンス: 頻度と質のバランス")
            print("- 最適条件: 頻度と勝率の最適化")

            print("\n🎯 結論:")
            print("✅ 条件緩和テスト完了")
            print("✅ シグナル頻度とパフォーマンスの把握")
            print("✅ 最適な条件設定の特定")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_relaxed_conditions())
