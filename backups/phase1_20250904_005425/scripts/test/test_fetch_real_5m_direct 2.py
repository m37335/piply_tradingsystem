#!/usr/bin/env python3
"""
fetch_real_5m_dataメソッド直接テストスクリプト
"""

import asyncio
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, "/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


async def test_fetch_real_5m_direct():
    """fetch_real_5m_dataメソッドを直接テスト"""
    try:
        logger.info("=== fetch_real_5m_data直接テスト開始 ===")
        
        # SQLite環境を強制設定
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"
        
        session = await get_async_session()
        data_fetcher = DataFetcherService(session)
        
        logger.info("DataFetcherService初期化完了")
        
        # fetch_real_5m_dataを直接呼び出し
        logger.info("fetch_real_5m_data呼び出し中...")
        result = await data_fetcher.fetch_real_5m_data()
        
        if result:
            logger.info("✅ fetch_real_5m_data成功:")
            logger.info(f"  Open: {result.open_price}")
            logger.info(f"  High: {result.high_price}")
            logger.info(f"  Low: {result.low_price}")
            logger.info(f"  Close: {result.close_price}")
            logger.info(f"  Volume: {result.volume}")
            logger.info(f"  Timestamp: {result.timestamp}")
            logger.info(f"  Data Source: {result.data_source}")
        else:
            logger.warning("❌ fetch_real_5m_data失敗: Noneが返されました")
        
        await session.close()
        logger.info("=== fetch_real_5m_data直接テスト完了 ===")
        
    except Exception as e:
        logger.error(f"❌ fetch_real_5m_data直接テストエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_fetch_real_5m_direct())
