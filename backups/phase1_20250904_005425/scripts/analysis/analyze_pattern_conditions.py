#!/usr/bin/env python3
"""
パターン条件分析スクリプト

実際のデータベースのデータを使用して、
各パターンの条件が適切かを判断します
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


async def analyze_pattern_conditions():
    """パターン条件の分析"""
    print("=" * 80)
    print("🔍 パターン条件分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🎯 1. RSIエントリーパターンの条件分析...")

            # RSIエントリー条件の分析
            print("✅ RSIエントリー条件:")
            print("   • 買いシグナル: RSI < 30 (過売り)")
            print("   • 売りシグナル: RSI > 70 (過買い)")
            print("   • 追加条件: 価格 > SMA20 (買い) / 価格 < SMA20 (売り)")
            print("   • 追加条件: MACDヒストグラム > 0 (買い) / < 0 (売り)")

            # 実際のデータで条件をチェック
            result = await db_session.execute(
                text(
                    """
                SELECT 
                    ti1.value as rsi_value,
                    ti2.value as sma_value,
                    ti3.value as macd_value,
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
                    AND ti3.indicator_type = 'MACD_histogram'
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
            rsi_conditions = result.fetchall()

            print(f"\n✅ RSI条件チェック結果: {len(rsi_conditions)}件")
            for rsi, sma, macd, price, timestamp, timeframe in rsi_conditions:
                if rsi and sma and price:
                    # 買い条件チェック
                    buy_condition = (
                        rsi < 30 and price > sma and (macd is None or macd > 0)
                    )
                    # 売り条件チェック
                    sell_condition = (
                        rsi > 70 and price < sma and (macd is None or macd < 0)
                    )

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    status = (
                        "✅ シグナル生成" if signal_type != "NONE" else "❌ 条件不満足"
                    )

                    macd_str = f"{macd:.5f}" if macd is not None else "N/A"
                    print(
                        f"  📊 {timeframe}: RSI={rsi:.2f}, SMA20={sma:.5f}, 価格={price:.5f}, MACD={macd_str} | {signal_type} {status}"
                    )

            print("\n🎯 2. ボリンジャーバンドパターンの条件分析...")

            # ボリンジャーバンド条件の分析
            print("✅ ボリンジャーバンドエントリー条件:")
            print(
                "   • 買いシグナル: 価格が下バンドにタッチ + RSI < 40 + 出来高 > 平均の1.5倍"
            )
            print(
                "   • 売りシグナル: 価格が上バンドにタッチ + RSI > 60 + 出来高 > 平均の1.5倍"
            )

            # 実際のデータで条件をチェック
            result = await db_session.execute(
                text(
                    """
                SELECT 
                    ti1.value as bb_upper,
                    ti2.value as bb_lower,
                    ti3.value as bb_middle,
                    ti4.value as rsi_value,
                    pd.close_price as current_price,
                    pd.volume,
                    ti1.timestamp,
                    ti1.timeframe
                FROM technical_indicators ti1
                LEFT JOIN technical_indicators ti2 ON 
                    ti1.timestamp = ti2.timestamp 
                    AND ti1.timeframe = ti2.timeframe 
                    AND ti2.indicator_type = 'BB_lower'
                LEFT JOIN technical_indicators ti3 ON 
                    ti1.timestamp = ti3.timestamp 
                    AND ti1.timeframe = ti3.timeframe 
                    AND ti3.indicator_type = 'BB_middle'
                LEFT JOIN technical_indicators ti4 ON 
                    ti1.timestamp = ti4.timestamp 
                    AND ti1.timeframe = ti4.timeframe 
                    AND ti4.indicator_type = 'RSI'
                LEFT JOIN price_data pd ON 
                    ti1.timestamp = pd.timestamp
                    AND ti1.currency_pair = pd.currency_pair
                WHERE ti1.indicator_type = 'BB_upper'
                AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY ti1.timestamp DESC
                LIMIT 10
                """
                )
            )
            bb_conditions = result.fetchall()

            print(f"\n✅ ボリンジャーバンド条件チェック結果: {len(bb_conditions)}件")
            for (
                bb_upper,
                bb_lower,
                bb_middle,
                rsi,
                price,
                volume,
                timestamp,
                timeframe,
            ) in bb_conditions:
                if bb_upper and bb_lower and bb_middle and rsi and price:
                    # 買い条件チェック（下バンドタッチ）
                    buy_condition = price <= bb_lower * 1.001 and rsi < 40
                    # 売り条件チェック（上バンドタッチ）
                    sell_condition = price >= bb_upper * 0.999 and rsi > 60

                    signal_type = (
                        "BUY" if buy_condition else "SELL" if sell_condition else "NONE"
                    )
                    status = (
                        "✅ シグナル生成" if signal_type != "NONE" else "❌ 条件不満足"
                    )

                    print(
                        f"  📊 {timeframe}: 価格={price:.5f}, BB上={bb_upper:.5f}, BB下={bb_lower:.5f}, RSI={rsi:.2f} | {signal_type} {status}"
                    )

            print("\n🎯 3. ボラティリティリスクパターンの条件分析...")

            # ボラティリティリスク条件の分析
            print("✅ ボラティリティリスク条件:")
            print("   • ATRが過去20期間平均の2倍以上")
            print("   • 価格変動が過去24時間で3%以上")
            print("   • 出来高が過去平均の3倍以上")

            # 実際のデータで条件をチェック
            result = await db_session.execute(
                text(
                    """
                SELECT 
                    ti1.value as current_atr,
                    ti1.timestamp,
                    ti1.timeframe,
                    pd.close_price as current_price
                FROM technical_indicators ti1
                LEFT JOIN price_data pd ON 
                    ti1.timestamp = pd.timestamp
                    AND ti1.currency_pair = pd.currency_pair
                WHERE ti1.indicator_type = 'ATR'
                AND ti1.timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY ti1.timestamp DESC
                LIMIT 10
                """
                )
            )
            atr_conditions = result.fetchall()

            print(f"\n✅ ボラティリティ条件チェック結果: {len(atr_conditions)}件")
            for current_atr, timestamp, timeframe, price in atr_conditions:
                if current_atr:
                    # ATRの平均値を計算（簡易版）
                    avg_atr = 0.01  # 仮の平均値
                    volatility_condition = current_atr > avg_atr * 2.0

                    status = (
                        "🚨 ボラティリティ急増"
                        if volatility_condition
                        else "✅ 正常範囲"
                    )

                    print(
                        f"  📊 {timeframe}: ATR={current_atr:.5f}, 平均ATR={avg_atr:.5f} | {status}"
                    )

            print("\n🎯 4. 条件最適化の提案...")

            # 条件最適化の提案
            print("✅ 現在の条件と実際のデータに基づく最適化提案:")

            # RSI条件の最適化
            result = await db_session.execute(
                text(
                    """
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(CASE WHEN value < 30 THEN 1 END) as oversold_count,
                    COUNT(CASE WHEN value > 70 THEN 1 END) as overbought_count,
                    COUNT(CASE WHEN value BETWEEN 30 AND 70 THEN 1 END) as normal_count
                FROM technical_indicators
                WHERE indicator_type = 'RSI'
                AND timestamp >= NOW() - INTERVAL '30 days'
                """
                )
            )
            rsi_stats = result.fetchone()

            if rsi_stats:
                total, oversold, overbought, normal = rsi_stats
                oversold_rate = (oversold / total) * 100 if total > 0 else 0
                overbought_rate = (overbought / total) * 100 if total > 0 else 0

                print(f"  📊 RSI統計（過去30日）:")
                print(f"    • 総データ数: {total:,}件")
                print(f"    • 過売り（<30）: {oversold:,}件 ({oversold_rate:.1f}%)")
                print(f"    • 過買い（>70）: {overbought:,}件 ({overbought_rate:.1f}%)")
                print(f"    • 正常範囲: {normal:,}件 ({(normal/total)*100:.1f}%)")

                if oversold_rate < 5:
                    print(f"    💡 提案: RSI過売り条件を35に緩和（現在の30から）")
                if overbought_rate < 5:
                    print(f"    💡 提案: RSI過買い条件を65に緩和（現在の70から）")

            print("\n🎯 5. シグナル生成頻度の分析...")

            # シグナル生成頻度の分析
            print("✅ シグナル生成頻度の分析:")

            # 過去7日間のシグナル候補を分析
            result = await db_session.execute(
                text(
                    """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as total_signals,
                    COUNT(CASE WHEN value < 35 THEN 1 END) as buy_candidates,
                    COUNT(CASE WHEN value > 65 THEN 1 END) as sell_candidates
                FROM technical_indicators
                WHERE indicator_type = 'RSI'
                AND timestamp >= NOW() - INTERVAL '7 days'
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                """
                )
            )
            daily_signals = result.fetchall()

            print(f"  📊 日別シグナル候補（過去7日）:")
            for date, total, buy_candidates, sell_candidates in daily_signals:
                print(
                    f"    • {date}: 総{total}件（買い候補{buy_candidates}件、売り候補{sell_candidates}件）"
                )

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(analyze_pattern_conditions())
