#!/usr/bin/env python3
"""
反転後の価格動向分析

RSIシグナル後の反転ポイントと、反転後の価格動向を詳細分析
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


async def analyze_price_movement_after_reversal():
    """反転後の価格動向を詳細分析"""
    print("=" * 80)
    print("🔍 反転後の価格動向分析 - 詳細価格レベル分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 買いシグナル（RSI < 40）後の詳細価格動向...")

            # 買いシグナルを取得
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
                    AND ti1.value < 40
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            buy_signals = result.fetchall()

            print(f"✅ 買いシグナル: {len(buy_signals)}件")

            if len(buy_signals) > 0:
                print("\n📊 買いシグナル後の詳細価格動向:")
                print("=" * 140)
                print(
                    f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'SMA50':<8} {'反転レベル':<12} {'最大戻り':<12} {'最終価格':<12} {'動向':<15}"
                )
                print("=" * 140)

                reversal_stats = {
                    "sma_20": {"count": 0, "max_return": [], "final_prices": []},
                    "ema_12": {"count": 0, "max_return": [], "final_prices": []},
                    "sma_50": {"count": 0, "max_return": [], "final_prices": []},
                }

                for (
                    rsi,
                    signal_price,
                    signal_time,
                    sma_20,
                    ema_12,
                    sma_50,
                ) in buy_signals:
                    if signal_price and sma_20 and ema_12 and sma_50:
                        # 24時間後の価格データを取得
                        future_time = signal_time + timedelta(hours=24)

                        result = await db_session.execute(
                            text(
                                """
                                SELECT close_price, timestamp
                                FROM price_data
                                WHERE timestamp >= :signal_time
                                AND timestamp <= :future_time
                                AND currency_pair = 'USD/JPY'
                                ORDER BY timestamp ASC
                                """
                            ),
                            {"signal_time": signal_time, "future_time": future_time},
                        )
                        price_data = result.fetchall()

                        if len(price_data) > 0:
                            # 反転ポイントと最大戻り幅を計算
                            reversal_level = "N/A"
                            max_return_pips = 0
                            final_price = price_data[-1][0]
                            price_movement = "N/A"

                            for price, timestamp in price_data:
                                # 反転ポイントの判定
                                if reversal_level == "N/A":
                                    if price >= sma_20:
                                        reversal_level = "SMA20"
                                        reversal_stats["sma_20"]["count"] += 1
                                    elif price >= ema_12:
                                        reversal_level = "EMA12"
                                        reversal_stats["ema_12"]["count"] += 1
                                    elif price >= sma_50:
                                        reversal_level = "SMA50"
                                        reversal_stats["sma_50"]["count"] += 1

                                # 最大戻り幅の計算
                                if reversal_level != "N/A":
                                    return_pips = (price - signal_price) * 100
                                    if return_pips > max_return_pips:
                                        max_return_pips = return_pips

                            # 最終的な価格動向の判定
                            if final_price > signal_price:
                                price_movement = "上昇継続"
                            elif final_price < signal_price:
                                price_movement = "下落継続"
                            else:
                                price_movement = "横ばい"

                            # 統計に追加
                            if reversal_level in reversal_stats:
                                reversal_stats[reversal_level.lower()][
                                    "max_return"
                                ].append(max_return_pips)
                                reversal_stats[reversal_level.lower()][
                                    "final_prices"
                                ].append(final_price)

                            # 結果を表示
                            time_str = signal_time.strftime("%m-%d %H:%M")
                            rsi_str = f"{rsi:.1f}"
                            price_str = f"{signal_price:.3f}"
                            sma_20_str = f"{sma_20:.3f}"
                            ema_12_str = f"{ema_12:.3f}"
                            sma_50_str = f"{sma_50:.3f}"
                            max_return_str = (
                                f"{max_return_pips:.1f}"
                                if max_return_pips > 0
                                else "N/A"
                            )
                            final_price_str = f"{final_price:.3f}"

                            print(
                                f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {sma_50_str:<8} {reversal_level:<12} {max_return_str:<12} {final_price_str:<12} {price_movement:<15}"
                            )

                print("=" * 140)

                # 統計分析
                print(f"\n📈 買いシグナル反転統計:")
                for level, stats in reversal_stats.items():
                    if stats["count"] > 0 and len(stats["max_return"]) > 0:
                        avg_max_return = sum(stats["max_return"]) / len(
                            stats["max_return"]
                        )
                        avg_final_price = sum(stats["final_prices"]) / len(
                            stats["final_prices"]
                        )
                        print(
                            f"- {level.upper()}: {stats['count']}件, 平均最大戻り: {avg_max_return:.1f}pips, 平均最終価格: {avg_final_price:.3f}"
                        )
                    elif stats["count"] > 0:
                        print(f"- {level.upper()}: {stats['count']}件, データ不足")

            print("\n🔍 2. 売りシグナル（RSI > 60）後の詳細価格動向...")

            # 売りシグナルを取得
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
                    AND ti1.value > 60
                    ORDER BY ti1.timestamp DESC
                    LIMIT 10
                    """
                )
            )
            sell_signals = result.fetchall()

            print(f"✅ 売りシグナル: {len(sell_signals)}件")

            if len(sell_signals) > 0:
                print("\n📊 売りシグナル後の詳細価格動向:")
                print("=" * 140)
                print(
                    f"{'時刻':<20} {'RSI':<6} {'価格':<8} {'SMA20':<8} {'EMA12':<8} {'SMA50':<8} {'戻りレベル':<12} {'最大戻り':<12} {'最終価格':<12} {'動向':<15}"
                )
                print("=" * 140)

                return_stats = {
                    "sma_20": {"count": 0, "max_return": [], "final_prices": []},
                    "ema_12": {"count": 0, "max_return": [], "final_prices": []},
                    "sma_50": {"count": 0, "max_return": [], "final_prices": []},
                }

                for (
                    rsi,
                    signal_price,
                    signal_time,
                    sma_20,
                    ema_12,
                    sma_50,
                ) in sell_signals:
                    if signal_price and sma_20 and ema_12 and sma_50:
                        # 24時間後の価格データを取得
                        future_time = signal_time + timedelta(hours=24)

                        result = await db_session.execute(
                            text(
                                """
                                SELECT close_price, timestamp
                                FROM price_data
                                WHERE timestamp >= :signal_time
                                AND timestamp <= :future_time
                                AND currency_pair = 'USD/JPY'
                                ORDER BY timestamp ASC
                                """
                            ),
                            {"signal_time": signal_time, "future_time": future_time},
                        )
                        price_data = result.fetchall()

                        if len(price_data) > 0:
                            # 戻りポイントと最大戻り幅を計算
                            return_level = "N/A"
                            max_return_pips = 0
                            final_price = price_data[-1][0]
                            price_movement = "N/A"

                            for price, timestamp in price_data:
                                # 戻りポイントの判定
                                if return_level == "N/A":
                                    if price <= sma_20:
                                        return_level = "SMA20"
                                        return_stats["sma_20"]["count"] += 1
                                    elif price <= ema_12:
                                        return_level = "EMA12"
                                        return_stats["ema_12"]["count"] += 1
                                    elif price <= sma_50:
                                        return_level = "SMA50"
                                        return_stats["sma_50"]["count"] += 1

                                # 最大戻り幅の計算
                                if return_level != "N/A":
                                    return_pips = (signal_price - price) * 100
                                    if return_pips > max_return_pips:
                                        max_return_pips = return_pips

                            # 最終的な価格動向の判定
                            if final_price < signal_price:
                                price_movement = "下落継続"
                            elif final_price > signal_price:
                                price_movement = "上昇継続"
                            else:
                                price_movement = "横ばい"

                            # 統計に追加
                            if return_level in return_stats:
                                return_stats[return_level.lower()]["max_return"].append(
                                    max_return_pips
                                )
                                return_stats[return_level.lower()][
                                    "final_prices"
                                ].append(final_price)

                            # 結果を表示
                            time_str = signal_time.strftime("%m-%d %H:%M")
                            rsi_str = f"{rsi:.1f}"
                            price_str = f"{signal_price:.3f}"
                            sma_20_str = f"{sma_20:.3f}"
                            ema_12_str = f"{ema_12:.3f}"
                            sma_50_str = f"{sma_50:.3f}"
                            max_return_str = (
                                f"{max_return_pips:.1f}"
                                if max_return_pips > 0
                                else "N/A"
                            )
                            final_price_str = f"{final_price:.3f}"

                            print(
                                f"{time_str:<20} {rsi_str:<6} {price_str:<8} {sma_20_str:<8} {ema_12_str:<8} {sma_50_str:<8} {return_level:<12} {max_return_str:<12} {final_price_str:<12} {price_movement:<15}"
                            )

                print("=" * 140)

                # 統計分析
                print(f"\n📈 売りシグナル戻り統計:")
                for level, stats in return_stats.items():
                    if stats["count"] > 0 and len(stats["max_return"]) > 0:
                        avg_max_return = sum(stats["max_return"]) / len(
                            stats["max_return"]
                        )
                        avg_final_price = sum(stats["final_prices"]) / len(
                            stats["final_prices"]
                        )
                        print(
                            f"- {level.upper()}: {stats['count']}件, 平均最大戻り: {avg_max_return:.1f}pips, 平均最終価格: {avg_final_price:.3f}"
                        )
                    elif stats["count"] > 0:
                        print(f"- {level.upper()}: {stats['count']}件, データ不足")

            print("\n🔍 3. 戦略的洞察...")
            print("反転後の価格動向分析からの洞察:")
            print("- 反転レベル: どの移動平均線で反転するか")
            print("- 最大戻り幅: 反転後の最大利益幅")
            print("- 最終動向: 24時間後の価格方向")
            print("- 再エントリー: 反転後の再エントリーポイント")

            print("\n🎯 結論:")
            print("✅ 反転後の価格動向分析完了")
            print("✅ 最大戻り幅と最終動向の把握")
            print("✅ より精密な利益確定戦略の構築")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_price_movement_after_reversal())
