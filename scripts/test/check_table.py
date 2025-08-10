#!/usr/bin/env python3
"""
テーブル構造確認スクリプト
"""

import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


async def check_table_structure():
    """テーブル構造を確認"""
    database_url = "sqlite+aiosqlite:///./test_app.db"

    engine = create_async_engine(
        database_url, echo=False, connect_args={"check_same_thread": False}
    )

    async with engine.begin() as conn:
        # テーブル一覧を取得
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = result.fetchall()
        print("Tables:", [table[0] for table in tables])

        # price_dataテーブルの構造を確認
        result = await conn.execute(text("PRAGMA table_info(price_data)"))
        columns = result.fetchall()
        print("\nprice_data table structure:")
        for col in columns:
            print(
                f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}"
            )

        # pattern_detectionsテーブルの構造を確認
        result = await conn.execute(text("PRAGMA table_info(pattern_detections)"))
        columns = result.fetchall()
        print("\npattern_detections table structure:")
        for col in columns:
            print(
                f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}"
            )


if __name__ == "__main__":
    asyncio.run(check_table_structure())
