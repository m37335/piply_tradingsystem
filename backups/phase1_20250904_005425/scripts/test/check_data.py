#!/usr/bin/env python3
"""
データ確認スクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_data():
    """データを確認"""
    database_url = "sqlite+aiosqlite:///./test_app.db"

    engine = create_async_engine(
        database_url, echo=False, connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        # 各テーブルのレコード数を確認
        tables = [
            "price_data",
            "technical_indicators",
            "system_config",
            "data_fetch_history",
        ]

        for table in tables:
            result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"Table {table}: {count} records")

        # サンプルデータを表示
        print("\nSample price data:")
        result = await conn.execute(text("SELECT * FROM price_data LIMIT 3"))
        rows = result.fetchall()
        for row in rows:
            print(
                f"  ID: {row[0]}, Currency: {row[1]}, Timestamp: {row[2]}, Close: {row[6]}"
            )

        print("\nSample technical indicators:")
        result = await conn.execute(text("SELECT * FROM technical_indicators LIMIT 3"))
        rows = result.fetchall()
        for row in rows:
            print(f"  ID: {row[0]}, Type: {row[3]}, Value: {row[5]}")

        print("\nSample system configs:")
        result = await conn.execute(text("SELECT * FROM system_config LIMIT 3"))
        rows = result.fetchall()
        for row in rows:
            print(f"  ID: {row[0]}, Key: {row[1]}, Category: {row[2]}")

        print("\nPattern detections count:")
        result = await conn.execute(text("SELECT COUNT(*) FROM pattern_detections"))
        count = result.scalar()
        print(f"  Total pattern detections: {count}")

        print("\nSample pattern detections:")
        result = await conn.execute(text("SELECT * FROM pattern_detections LIMIT 3"))
        rows = result.fetchall()
        for row in rows:
            print(
                f"  ID: {row[0]}, Type: {row[3]}, Name: {row[4]}, Confidence: {row[5]}"
            )


if __name__ == "__main__":
    asyncio.run(check_data())
