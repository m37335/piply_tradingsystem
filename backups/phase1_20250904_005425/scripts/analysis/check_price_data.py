#!/usr/bin/env python3
"""
価格データ確認スクリプト

2025-08-13 09:55:00の時のprice_dataテーブルを確認します
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


async def check_price_data():
    """価格データの確認"""
    print("=" * 80)
    print("💰 価格データ確認")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. price_dataテーブルの構造確認...")
            
            # テーブル構造を確認
            result = await db_session.execute(
                text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'price_data'
                ORDER BY ordinal_position
                """)
            )
            columns = result.fetchall()
            
            print("✅ price_dataテーブルの構造:")
            for column_name, data_type, is_nullable in columns:
                nullable_str = "NULL" if is_nullable == "YES" else "NOT NULL"
                print(f"  📊 {column_name}: {data_type} ({nullable_str})")

            print("\n🔍 2. 2025-08-13 09:55:00の価格データ...")
            
            # 指定時刻の価格データを確認
            from datetime import datetime
            target_timestamp = datetime(2025, 8, 13, 9, 55, 0)
            
            result = await db_session.execute(
                text("""
                SELECT *
                FROM price_data
                WHERE timestamp = :timestamp
                ORDER BY currency_pair
                """),
                {"timestamp": target_timestamp}
            )
            price_data = result.fetchall()
            
            if price_data:
                print(f"✅ {target_timestamp}の価格データ: {len(price_data)}件")
                for row in price_data:
                    print(f"  📊 {row}")
            else:
                print(f"❌ {target_timestamp}の価格データが見つかりません")

            print("\n🔍 3. 近い時刻の価格データ...")
            
            # 近い時刻の価格データを確認
            result = await db_session.execute(
                text("""
                SELECT *
                FROM price_data
                WHERE timestamp >= :start_time
                AND timestamp <= :end_time
                ORDER BY timestamp DESC
                LIMIT 10
                """),
                {
                    "start_time": datetime(2025, 8, 13, 9, 50, 0),
                    "end_time": datetime(2025, 8, 13, 10, 0, 0)
                }
            )
            nearby_price_data = result.fetchall()
            
            print(f"✅ 近い時刻の価格データ: {len(nearby_price_data)}件")
            for row in nearby_price_data:
                print(f"  📊 {row}")

            print("\n🔍 4. price_dataテーブルの最新データ...")
            
            # 最新の価格データを確認
            result = await db_session.execute(
                text("""
                SELECT timestamp, currency_pair, open_price, high_price, low_price, close_price, volume
                FROM price_data
                ORDER BY timestamp DESC
                LIMIT 5
                """)
            )
            latest_price_data = result.fetchall()
            
            print(f"✅ 最新の価格データ: {len(latest_price_data)}件")
            for timestamp, currency_pair, open_price, high, low, close, volume in latest_price_data:
                print(f"  📊 {timestamp} | {currency_pair} | O:{open_price} H:{high} L:{low} C:{close} V:{volume}")

            print("\n🔍 5. price_dataテーブルの統計情報...")
            
            # テーブルの統計情報を確認
            result = await db_session.execute(
                text("""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT currency_pair) as currency_pairs,
                    COUNT(DISTINCT DATE(timestamp)) as trading_days,
                    MIN(timestamp) as earliest_data,
                    MAX(timestamp) as latest_data
                FROM price_data
                """)
            )
            stats = result.fetchone()
            
            print("✅ price_dataテーブルの統計:")
            print(f"  📊 総レコード数: {stats[0]:,}")
            print(f"  📊 通貨ペア数: {stats[1]}")
            print(f"  📊 取引日数: {stats[2]}")
            print(f"  📊 データ期間: {stats[3]} ～ {stats[4]}")

            print("\n🔍 6. 通貨ペア別のデータ数...")
            
            # 通貨ペア別のデータ数を確認
            result = await db_session.execute(
                text("""
                SELECT 
                    currency_pair,
                    COUNT(*) as count,
                    MIN(timestamp) as earliest,
                    MAX(timestamp) as latest
                FROM price_data
                GROUP BY currency_pair
                ORDER BY count DESC
                """)
            )
            currency_stats = result.fetchall()
            
            print("✅ 通貨ペア別データ数:")
            for currency_pair, count, earliest, latest in currency_stats:
                print(f"  📊 {currency_pair}: {count:,}件 ({earliest} ～ {latest})")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(check_price_data())
