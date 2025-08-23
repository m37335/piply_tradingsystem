#!/usr/bin/env python3
"""
RSIのみ条件テスト

RSIのみの条件でテストし、全体件数とシグナル率を分析
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


async def test_rsi_only_analysis():
    """RSIのみの条件でテスト"""
    print("=" * 80)
    print("🔍 RSIのみ条件テスト - 全体件数とシグナル率分析")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 全体データ件数の確認...")

            # 全体のRSIデータ件数を取得
            result = await db_session.execute(
                text(
                    """
                    SELECT COUNT(*) as total_count
                    FROM technical_indicators
                    WHERE indicator_type = 'RSI'
                    AND currency_pair = 'USD/JPY'
                    """
                )
            )
            total_count = result.scalar()
            print(f"✅ 全体RSIデータ件数: {total_count:,}件")

            # 各RSIレベルの件数を確認
            print("\n🔍 2. 各RSIレベルの件数分析...")

            rsi_levels = [
                (30, "RSI < 30 (強い過売り)"),
                (35, "RSI < 35 (過売り)"),
                (40, "RSI < 40 (軽度過売り)"),
                (45, "RSI < 45 (中程度)"),
                (50, "RSI < 50 (中立)"),
                (55, "RSI > 55 (中程度)"),
                (60, "RSI > 60 (軽度過買い)"),
                (65, "RSI > 65 (過買い)"),
                (70, "RSI > 70 (強い過買い)"),
            ]

            print(f"{'条件':<25} {'件数':<10} {'割合':<10}")
            print("-" * 45)

            for rsi_level, description in rsi_levels:
                if rsi_level <= 50:
                    # 買い条件
                    result = await db_session.execute(
                        text(
                            """
                            SELECT COUNT(*) as count
                            FROM technical_indicators
                            WHERE indicator_type = 'RSI'
                            AND currency_pair = 'USD/JPY'
                            AND value < :rsi_level
                            """
                        ),
                        {"rsi_level": rsi_level},
                    )
                else:
                    # 売り条件
                    result = await db_session.execute(
                        text(
                            """
                            SELECT COUNT(*) as count
                            FROM technical_indicators
                            WHERE indicator_type = 'RSI'
                            AND currency_pair = 'USD/JPY'
                            AND value > :rsi_level
                            """
                        ),
                        {"rsi_level": rsi_level},
                    )

                count = result.scalar()
                percentage = (count / total_count) * 100 if total_count > 0 else 0
                print(f"{description:<25} {count:<10,} {percentage:<10.2f}%")

            print("\n🔍 3. RSIのみ条件でのシグナルテスト...")

            # RSIのみの条件でテスト
            test_conditions = [
                (30, "RSI < 30 (強い過売り)"),
                (35, "RSI < 35 (過売り)"),
                (40, "RSI < 40 (軽度過売り)"),
                (65, "RSI > 65 (過買い)"),
                (70, "RSI > 70 (強い過買い)"),
            ]

            print(
                f"\n{'条件':<25} {'シグナル数':<12} {'シグナル率':<12} {'1時間勝率':<12} {'1時間平均利益':<15}"
            )
            print("-" * 80)

            for rsi_level, description in test_conditions:
                # RSIのみの条件でシグナルを検出
                if rsi_level <= 50:
                    # 買い条件
                    result = await db_session.execute(
                        text(
                            """
                            SELECT
                                ti1.value as rsi_value,
                                pd.close_price as signal_price,
                                ti1.timestamp as signal_time
                            FROM technical_indicators ti1
                            LEFT JOIN price_data pd ON
                                ti1.timestamp = pd.timestamp
                                AND ti1.currency_pair = pd.currency_pair
                            WHERE ti1.indicator_type = 'RSI'
                            AND ti1.currency_pair = 'USD/JPY'
                            AND ti1.value < :rsi_level
                            ORDER BY ti1.timestamp DESC
                            LIMIT 20
                            """
                        ),
                        {"rsi_level": rsi_level},
                    )
                else:
                    # 売り条件
                    result = await db_session.execute(
                        text(
                            """
                            SELECT
                                ti1.value as rsi_value,
                                pd.close_price as signal_price,
                                ti1.timestamp as signal_time
                            FROM technical_indicators ti1
                            LEFT JOIN price_data pd ON
                                ti1.timestamp = pd.timestamp
                                AND ti1.currency_pair = pd.currency_pair
                            WHERE ti1.indicator_type = 'RSI'
                            AND ti1.currency_pair = 'USD/JPY'
                            AND ti1.value > :rsi_level
                            ORDER BY ti1.timestamp DESC
                            LIMIT 20
                            """
                        ),
                        {"rsi_level": rsi_level},
                    )

                signals = result.fetchall()
                signal_count = len(signals)

                if signal_count > 0:
                    # パフォーマンス分析
                    profits_1h = []

                    for rsi, signal_price, signal_time in signals:
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

                                # 利益計算
                                if rsi_level <= 50:  # 買いシグナル
                                    profit_pips = (future_price - signal_price) * 100
                                else:  # 売りシグナル
                                    profit_pips = (signal_price - future_price) * 100

                                profits_1h.append(profit_pips)

                    if profits_1h:
                        avg_profit = sum(profits_1h) / len(profits_1h)
                        win_rate = (
                            len([p for p in profits_1h if p > 0])
                            / len(profits_1h)
                            * 100
                        )
                        signal_rate = (
                            (signal_count / total_count) * 100 if total_count > 0 else 0
                        )

                        print(
                            f"{description:<25} {signal_count:<12} {signal_rate:<12.2f}% {win_rate:<12.1f}% {avg_profit:<15.2f}pips"
                        )
                    else:
                        signal_rate = (
                            (signal_count / total_count) * 100 if total_count > 0 else 0
                        )
                        print(
                            f"{description:<25} {signal_count:<12} {signal_rate:<12.2f}% {'N/A':<12} {'N/A':<15}"
                        )
                else:
                    print(
                        f"{description:<25} {signal_count:<12} {'0.00':<12}% {'N/A':<12} {'N/A':<15}"
                    )

            print("\n🔍 4. 推奨条件の分析...")
            print("RSIのみ条件での推奨:")
            print("- シグナル率: 適度な頻度（1-5%）が理想的")
            print("- 勝率: 60%以上が望ましい")
            print("- 平均利益: プラスが望ましい")
            print("- 実用性: 月に数回程度のシグナル")

            print("\n🎯 結論:")
            print("✅ RSIのみ条件で全体件数とシグナル率を分析完了")
            print("✅ 各RSIレベルの出現頻度を確認")
            print("✅ 実用的な条件設定の指針を提供")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_rsi_only_analysis())
