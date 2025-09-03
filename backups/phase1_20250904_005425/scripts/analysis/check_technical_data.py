#!/usr/bin/env python3
"""
テクニカル指標データ詳細確認スクリプト

データベースに保存されているテクニカル指標データの詳細を確認し、
シグナル生成の条件を分析します
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


async def check_technical_data():
    """テクニカル指標データの詳細確認"""
    print("=" * 80)
    print("📊 テクニカル指標データ詳細確認")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🗃️ 1. データベース全体統計...")
            
            # 全体統計
            result = await db_session.execute(
                text("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT indicator_type) as indicator_types,
                    COUNT(DISTINCT timeframe) as timeframes,
                    MIN(timestamp) as earliest_data,
                    MAX(timestamp) as latest_data
                FROM technical_indicators
                """)
            )
            stats = result.fetchone()
            print(f"✅ 総レコード数: {stats[0]:,}")
            print(f"✅ 指標タイプ数: {stats[1]}")
            print(f"✅ タイムフレーム数: {stats[2]}")
            print(f"✅ データ期間: {stats[3]} ～ {stats[4]}")

            print("\n📈 2. 指標タイプ別データ数...")
            
            # 指標タイプ別統計
            result = await db_session.execute(
                text("""
                SELECT 
                    indicator_type,
                    COUNT(*) as count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM technical_indicators
                GROUP BY indicator_type
                ORDER BY count DESC
                """)
            )
            indicators = result.fetchall()
            
            for indicator_type, count, earliest, latest in indicators:
                print(f"  📊 {indicator_type}: {count:,}件 ({earliest} ～ {latest})")

            print("\n⏰ 3. タイムフレーム別データ数...")
            
            # タイムフレーム別統計
            result = await db_session.execute(
                text("""
                SELECT 
                    timeframe,
                    COUNT(*) as count
                FROM technical_indicators
                GROUP BY timeframe
                ORDER BY count DESC
                """)
            )
            timeframes = result.fetchall()
            
            for timeframe, count in timeframes:
                print(f"  ⏰ {timeframe}: {count:,}件")

            print("\n🔍 4. 最新データの詳細確認（過去24時間）...")
            
            # 最新データの詳細
            result = await db_session.execute(
                text("""
                SELECT 
                    indicator_type,
                    timeframe,
                    value,
                    timestamp
                FROM technical_indicators
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                ORDER BY timestamp DESC
                LIMIT 20
                """)
            )
            recent_data = result.fetchall()
            
            print(f"✅ 過去24時間のデータ: {len(recent_data)}件")
            for indicator_type, timeframe, value, timestamp in recent_data[:10]:
                print(f"  📊 {indicator_type} ({timeframe}): {value} at {timestamp}")

            print("\n🎯 5. RSIシグナル生成条件の分析...")
            
            # RSIの最新値を確認
            result = await db_session.execute(
                text("""
                SELECT 
                    value,
                    timestamp,
                    timeframe
                FROM technical_indicators
                WHERE indicator_type = 'RSI'
                AND timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC
                LIMIT 10
                """)
            )
            rsi_data = result.fetchall()
            
            print(f"✅ 過去1時間のRSIデータ: {len(rsi_data)}件")
            for value, timestamp, timeframe in rsi_data:
                status = "過売り" if value < 30 else "過買い" if value > 70 else "通常"
                print(f"  📊 RSI ({timeframe}): {value:.2f} - {status} at {timestamp}")

            print("\n📊 6. 移動平均線データの確認...")
            
            # SMAデータの確認
            result = await db_session.execute(
                text("""
                SELECT 
                    indicator_type,
                    value,
                    timestamp,
                    timeframe
                FROM technical_indicators
                WHERE indicator_type LIKE 'SMA%'
                AND timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY timestamp DESC
                LIMIT 10
                """)
            )
            sma_data = result.fetchall()
            
            print(f"✅ 過去1時間のSMAデータ: {len(sma_data)}件")
            for indicator_type, value, timestamp, timeframe in sma_data:
                print(f"  📊 {indicator_type} ({timeframe}): {value:.5f} at {timestamp}")

            print("\n🔍 7. シグナル生成条件の評価...")
            
            # シグナル生成に必要な条件をチェック
            print("✅ RSIエントリーシグナル生成条件:")
            print("   - RSI < 30 (過売り) または RSI > 70 (過買い)")
            print("   - 価格 > SMA20 (上昇トレンド) または 価格 < SMA20 (下降トレンド)")
            print("   - MACDヒストグラム > 0 (モメンタム上昇) または < 0 (モメンタム下降)")
            
            # 現在の条件をチェック
            result = await db_session.execute(
                text("""
                SELECT 
                    ti1.value as rsi_value,
                    ti2.value as sma_value,
                    ti3.value as macd_hist,
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
                WHERE ti1.indicator_type = 'RSI'
                AND ti1.timestamp >= NOW() - INTERVAL '1 hour'
                ORDER BY ti1.timestamp DESC
                LIMIT 5
                """)
            )
            signal_conditions = result.fetchall()
            
            print(f"✅ シグナル条件チェック: {len(signal_conditions)}件")
            for rsi, sma, macd_hist, timestamp, timeframe in signal_conditions:
                rsi_condition = "過売り" if rsi and rsi < 30 else "過買い" if rsi and rsi > 70 else "通常"
                print(f"  📊 {timeframe}: RSI={rsi:.2f}({rsi_condition}), SMA20={sma:.5f if sma else 'N/A'}, MACD={macd_hist:.5f if macd_hist else 'N/A'}")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_technical_data())
