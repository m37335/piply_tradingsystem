#!/usr/bin/env python3
"""
複数移動平均条件テストスクリプト

SMA_20/EMA_12-26とSMA_50/EMA_50の両方を条件に組み込んでテスト
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


async def test_multiple_ma_conditions():
    """複数移動平均条件をテスト"""
    print("=" * 80)
    print("🔍 複数移動平均条件テスト - より強力なシグナル")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 複数移動平均条件の定義...")

            # テストする条件パターン
            conditions = [
                {
                    "name": "現在の条件",
                    "description": "SMA_20/EMA_12-26のみ",
                    "buy_condition": "RSI < 55 AND price > SMA_20 AND EMA_12 > EMA_26",
                    "sell_condition": "RSI > 45 AND price < SMA_20 AND EMA_12 < EMA_26",
                },
                {
                    "name": "長期MA追加",
                    "description": "SMA_20/EMA_12-26 + SMA_50/EMA_50確認",
                    "buy_condition": "RSI < 55 AND price > SMA_20 AND EMA_12 > EMA_26 AND price > SMA_50 AND EMA_26 > EMA_50",
                    "sell_condition": "RSI > 45 AND price < SMA_20 AND EMA_12 < EMA_26 AND price < SMA_50 AND EMA_26 < EMA_50",
                },
                {
                    "name": "短期上昇",
                    "description": "短期MA上昇 + 長期MA確認",
                    "buy_condition": "RSI < 55 AND price > SMA_20 AND EMA_12 > EMA_26 AND SMA_20 > SMA_50",
                    "sell_condition": "RSI > 45 AND price < SMA_20 AND EMA_12 < EMA_26 AND SMA_20 < SMA_50",
                },
                {
                    "name": "EMA上昇",
                    "description": "EMA上昇 + 長期MA確認",
                    "buy_condition": "RSI < 55 AND price > SMA_20 AND EMA_12 > EMA_26 AND EMA_12 > EMA_50",
                    "sell_condition": "RSI > 45 AND price < SMA_20 AND EMA_12 < EMA_26 AND EMA_12 < EMA_50",
                },
                {
                    "name": "強力な上昇",
                    "description": "全ての条件を満たす強力なシグナル",
                    "buy_condition": "RSI < 55 AND price > SMA_20 AND EMA_12 > EMA_26 AND price > SMA_50 AND EMA_26 > EMA_50 AND SMA_20 > SMA_50",
                    "sell_condition": "RSI > 45 AND price < SMA_20 AND EMA_12 < EMA_26 AND price < SMA_50 AND EMA_26 < EMA_50 AND SMA_20 < SMA_50",
                },
            ]

            print(f"✅ テストする条件: {len(conditions)}種類")

            all_results = []

            for condition in conditions:
                print(f"\n🔍 2. {condition['name']}のテスト...")
                print(f"   説明: {condition['description']}")

                # 買いシグナルのテスト
                buy_query = f"""
                SELECT
                    ti1.value as rsi_value,
                    ti2.value as sma_20,
                    ti3.value as ema_12,
                    ti4.value as ema_26,
                    ti5.value as sma_50,
                    ti6.value as ema_50,
                    ti7.value as atr_value,
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
                    AND ti6.indicator_type = 'EMA_50'
                LEFT JOIN technical_indicators ti7 ON
                    ti1.timestamp = ti7.timestamp
                    AND ti1.timeframe = ti7.timeframe
                    AND ti7.indicator_type = 'ATR'
                LEFT JOIN price_data pd ON
                    ti1.timestamp = pd.timestamp
                    AND ti1.currency_pair = pd.currency_pair
                WHERE ti1.indicator_type = 'RSI'
                AND ti1.value < 55
                AND pd.close_price > ti2.value
                AND ti3.value > ti4.value
                AND 0.01 <= ti7.value
                AND ti7.value <= 0.10
                """

                # 条件に応じてクエリを修正
                if "SMA_50" in condition["buy_condition"]:
                    buy_query += " AND pd.close_price > ti5.value"
                if "EMA_50" in condition["buy_condition"]:
                    buy_query += " AND ti4.value > ti6.value"
                if "SMA_20 > SMA_50" in condition["buy_condition"]:
                    buy_query += " AND ti2.value > ti5.value"
                if "EMA_12 > EMA_50" in condition["buy_condition"]:
                    buy_query += " AND ti3.value > ti6.value"

                buy_query += " ORDER BY ti1.timestamp DESC LIMIT 15"

                buy_result = await db_session.execute(text(buy_query))
                buy_signals = buy_result.fetchall()

                # 売りシグナルのテスト
                sell_query = f"""
                SELECT
                    ti1.value as rsi_value,
                    ti2.value as sma_20,
                    ti3.value as ema_12,
                    ti4.value as ema_26,
                    ti5.value as sma_50,
                    ti6.value as ema_50,
                    ti7.value as atr_value,
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
                    AND ti6.indicator_type = 'EMA_50'
                LEFT JOIN technical_indicators ti7 ON
                    ti1.timestamp = ti7.timestamp
                    AND ti1.timeframe = ti7.timeframe
                    AND ti7.indicator_type = 'ATR'
                LEFT JOIN price_data pd ON
                    ti1.timestamp = pd.timestamp
                    AND ti1.currency_pair = pd.currency_pair
                WHERE ti1.indicator_type = 'RSI'
                AND ti1.value > 45
                AND pd.close_price < ti2.value
                AND ti3.value < ti4.value
                AND 0.01 <= ti7.value
                AND ti7.value <= 0.10
                """

                # 条件に応じてクエリを修正
                if "SMA_50" in condition["sell_condition"]:
                    sell_query += " AND pd.close_price < ti5.value"
                if "EMA_50" in condition["sell_condition"]:
                    sell_query += " AND ti4.value < ti6.value"
                if "SMA_20 < SMA_50" in condition["sell_condition"]:
                    sell_query += " AND ti2.value < ti5.value"
                if "EMA_12 < EMA_50" in condition["sell_condition"]:
                    sell_query += " AND ti3.value < ti6.value"

                sell_query += " ORDER BY ti1.timestamp DESC LIMIT 15"

                sell_result = await db_session.execute(text(sell_query))
                sell_signals = sell_result.fetchall()

                print(f"   買いシグナル: {len(buy_signals)}件")
                print(f"   売りシグナル: {len(sell_signals)}件")

                # パフォーマンス分析
                buy_profits_1h = []
                buy_profits_4h = []
                buy_profits_1d = []
                sell_profits_1h = []
                sell_profits_4h = []
                sell_profits_1d = []

                # 買いシグナルの利益計算
                for (
                    rsi,
                    sma_20,
                    ema_12,
                    ema_26,
                    sma_50,
                    ema_50,
                    atr,
                    signal_price,
                    signal_time,
                    timeframe,
                ) in buy_signals:
                    if rsi and sma_20 and ema_12 and ema_26 and atr and signal_price:
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
                                {"future_time": future_time},
                            )
                            future_price_result = result.fetchone()

                            if future_price_result:
                                future_price = future_price_result[0]
                                profit_pips = (future_price - signal_price) * 100

                                if hours == 1:
                                    buy_profits_1h.append(profit_pips)
                                elif hours == 4:
                                    buy_profits_4h.append(profit_pips)
                                elif hours == 24:
                                    buy_profits_1d.append(profit_pips)

                # 売りシグナルの利益計算
                for (
                    rsi,
                    sma_20,
                    ema_12,
                    ema_26,
                    sma_50,
                    ema_50,
                    atr,
                    signal_price,
                    signal_time,
                    timeframe,
                ) in sell_signals:
                    if rsi and sma_20 and ema_12 and ema_26 and atr and signal_price:
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
                                {"future_time": future_time},
                            )
                            future_price_result = result.fetchone()

                            if future_price_result:
                                future_price = future_price_result[0]
                                profit_pips = (signal_price - future_price) * 100

                                if hours == 1:
                                    sell_profits_1h.append(profit_pips)
                                elif hours == 4:
                                    sell_profits_4h.append(profit_pips)
                                elif hours == 24:
                                    sell_profits_1d.append(profit_pips)

                # 統計計算
                result_data = {
                    "name": condition["name"],
                    "description": condition["description"],
                    "buy_count": len(buy_signals),
                    "sell_count": len(sell_signals),
                }

                # 買い統計
                if buy_profits_1h:
                    result_data["buy_avg_1h"] = sum(buy_profits_1h) / len(
                        buy_profits_1h
                    )
                    result_data["buy_win_rate_1h"] = (
                        len([p for p in buy_profits_1h if p > 0])
                        / len(buy_profits_1h)
                        * 100
                    )
                else:
                    result_data["buy_avg_1h"] = 0
                    result_data["buy_win_rate_1h"] = 0

                if buy_profits_4h:
                    result_data["buy_avg_4h"] = sum(buy_profits_4h) / len(
                        buy_profits_4h
                    )
                    result_data["buy_win_rate_4h"] = (
                        len([p for p in buy_profits_4h if p > 0])
                        / len(buy_profits_4h)
                        * 100
                    )
                else:
                    result_data["buy_avg_4h"] = 0
                    result_data["buy_win_rate_4h"] = 0

                if buy_profits_1d:
                    result_data["buy_avg_1d"] = sum(buy_profits_1d) / len(
                        buy_profits_1d
                    )
                    result_data["buy_win_rate_1d"] = (
                        len([p for p in buy_profits_1d if p > 0])
                        / len(buy_profits_1d)
                        * 100
                    )
                else:
                    result_data["buy_avg_1d"] = 0
                    result_data["buy_win_rate_1d"] = 0

                # 売り統計
                if sell_profits_1h:
                    result_data["sell_avg_1h"] = sum(sell_profits_1h) / len(
                        sell_profits_1h
                    )
                    result_data["sell_win_rate_1h"] = (
                        len([p for p in sell_profits_1h if p > 0])
                        / len(sell_profits_1h)
                        * 100
                    )
                else:
                    result_data["sell_avg_1h"] = 0
                    result_data["sell_win_rate_1h"] = 0

                if sell_profits_4h:
                    result_data["sell_avg_4h"] = sum(sell_profits_4h) / len(
                        sell_profits_4h
                    )
                    result_data["sell_win_rate_4h"] = (
                        len([p for p in sell_profits_4h if p > 0])
                        / len(sell_profits_4h)
                        * 100
                    )
                else:
                    result_data["sell_avg_4h"] = 0
                    result_data["sell_win_rate_4h"] = 0

                if sell_profits_1d:
                    result_data["sell_avg_1d"] = sum(sell_profits_1d) / len(
                        sell_profits_1d
                    )
                    result_data["sell_win_rate_1d"] = (
                        len([p for p in sell_profits_1d if p > 0])
                        / len(sell_profits_1d)
                        * 100
                    )
                else:
                    result_data["sell_avg_1d"] = 0
                    result_data["sell_win_rate_1d"] = 0

                all_results.append(result_data)

                print(
                    f"   買い - 1時間: {result_data['buy_avg_1h']:.2f}pips ({result_data['buy_win_rate_1h']:.1f}%)"
                )
                print(
                    f"   買い - 4時間: {result_data['buy_avg_4h']:.2f}pips ({result_data['buy_win_rate_4h']:.1f}%)"
                )
                print(
                    f"   買い - 1日: {result_data['buy_avg_1d']:.2f}pips ({result_data['buy_win_rate_1d']:.1f}%)"
                )
                print(
                    f"   売り - 1時間: {result_data['sell_avg_1h']:.2f}pips ({result_data['sell_win_rate_1h']:.1f}%)"
                )
                print(
                    f"   売り - 4時間: {result_data['sell_avg_4h']:.2f}pips ({result_data['sell_win_rate_4h']:.1f}%)"
                )
                print(
                    f"   売り - 1日: {result_data['sell_avg_1d']:.2f}pips ({result_data['sell_win_rate_1d']:.1f}%)"
                )

            # 結果の比較分析
            print("\n🔍 3. 条件別比較分析...")
            print("=" * 140)
            print(
                f"{'条件名':<15} {'買い数':<6} {'売り数':<6} {'買い1時間':<12} {'売り1時間':<12} {'買い4時間':<12} {'売り4時間':<12} {'買い1日':<12} {'売り1日':<12}"
            )
            print("=" * 140)

            for result in all_results:
                print(
                    f"{result['name']:<15} {result['buy_count']:<6} {result['sell_count']:<6} {result['buy_avg_1h']:<12.2f} {result['sell_avg_1h']:<12.2f} {result['buy_avg_4h']:<12.2f} {result['sell_avg_4h']:<12.2f} {result['buy_avg_1d']:<12.2f} {result['sell_avg_1d']:<12.2f}"
                )

            print("=" * 140)

            # 最適条件の特定
            print("\n🎯 最適条件の特定...")

            # 1時間後の最適条件
            best_1h = max(
                all_results, key=lambda x: (x["buy_avg_1h"] + x["sell_avg_1h"]) / 2
            )
            print(
                f"✅ 1時間後最適: {best_1h['name']} (買い{best_1h['buy_avg_1h']:.2f}, 売り{best_1h['sell_avg_1h']:.2f})"
            )

            # 4時間後の最適条件
            best_4h = max(
                all_results, key=lambda x: (x["buy_avg_4h"] + x["sell_avg_4h"]) / 2
            )
            print(
                f"✅ 4時間後最適: {best_4h['name']} (買い{best_4h['buy_avg_4h']:.2f}, 売り{best_4h['sell_avg_4h']:.2f})"
            )

            # 1日後の最適条件
            best_1d = max(
                all_results, key=lambda x: (x["buy_avg_1d"] + x["sell_avg_1d"]) / 2
            )
            print(
                f"✅ 1日後最適: {best_1d['name']} (買い{best_1d['buy_avg_1d']:.2f}, 売り{best_1d['sell_avg_1d']:.2f})"
            )

            # 総合最適条件
            best_overall = max(
                all_results,
                key=lambda x: (
                    x["buy_avg_1h"]
                    + x["sell_avg_1h"]
                    + x["buy_avg_4h"]
                    + x["sell_avg_4h"]
                    + x["buy_avg_1d"]
                    + x["sell_avg_1d"]
                )
                / 6,
            )
            print(f"✅ 総合最適: {best_overall['name']} (全時間軸平均)")

            print("\n💡 複数移動平均の洞察:")
            print("1. 短期+長期MA: より確実なトレンド確認")
            print("2. 条件の厳格化: シグナル数は減るが質は向上")
            print("3. 上昇/下降の確認: 複数期間での方向性確認")
            print("4. フィルタリング効果: ノイズの削減")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_multiple_ma_conditions())
