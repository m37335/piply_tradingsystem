#!/usr/bin/env python3
"""
経済指標キャッシュクリアスクリプト
"""
import os
import sys
import asyncio

# プロジェクトのルートディレクトリをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.infrastructure.database.connection import get_async_session
from sqlalchemy import text

async def clear_economic_cache():
    """経済指標キャッシュをクリア"""
    session = await get_async_session()
    
    try:
        # 経済指標キャッシュを削除
        result = await session.execute(
            text("DELETE FROM analysis_cache WHERE analysis_type = 'economic_calendar'")
        )
        await session.commit()
        
        print(f"✅ 経済指標キャッシュクリア完了: {result.rowcount}件削除")
        
    except Exception as e:
        print(f"❌ キャッシュクリアエラー: {e}")
        await session.rollback()
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(clear_economic_cache())
