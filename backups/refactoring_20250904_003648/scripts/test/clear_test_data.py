#!/usr/bin/env python3
"""
テストデータクリアスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TestDataCleaner:
    """
    テストデータクリーンアップクラス
    """

    def __init__(self):
        self.database_url = "sqlite+aiosqlite:///./test_app.db"

    async def clear_test_data(self):
        """
        テストデータをクリア
        """
        try:
            print("Clearing test data...")
            logger.info("Clearing test data...")

            # エンジンを作成
            engine = create_async_engine(
                self.database_url, echo=False, connect_args={"check_same_thread": False}
            )

            async with engine.begin() as conn:
                # パターン検出データを削除
                await conn.execute(
                    text("DELETE FROM pattern_detections WHERE id >= 3000")
                )
                print("Cleared pattern detections")

                # テクニカル指標データを削除
                await conn.execute(
                    text("DELETE FROM technical_indicators WHERE id >= 2000")
                )
                print("Cleared technical indicators")

                # 価格データを削除
                await conn.execute(text("DELETE FROM price_data WHERE id >= 1000"))
                print("Cleared price data")

            print("Test data cleared successfully!")
            logger.info("Test data cleared successfully!")

        except Exception as e:
            print(f"Test data clear failed: {e}")
            logger.error(f"Test data clear failed: {e}")
            raise


async def main():
    """
    メイン関数
    """
    print("Starting test data cleanup...")
    logger.info("Starting test data cleanup...")

    # 環境変数の設定
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

    cleaner = TestDataCleaner()

    try:
        await cleaner.clear_test_data()
        print("Test data cleanup completed successfully!")

    except Exception as e:
        print(f"Test data cleanup failed: {e}")
        logger.error(f"Test data cleanup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
