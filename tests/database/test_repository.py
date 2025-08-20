#!/usr/bin/env python3
"""
Repository Test Script
リポジトリテストスクリプト
"""

import asyncio
import sys
from datetime import datetime

sys.path.append("/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)


async def test_repository():
    """リポジトリをテスト"""
    print("=== データベースリポジトリテスト ===")
    
    try:
        # セッション初期化
        session = await get_async_session()
        print("✅ データベースセッション接続完了")
        
        # リポジトリ初期化
        repo = PriceDataRepositoryImpl(session)
        print("✅ PriceDataRepositoryImpl初期化完了")
        
        # 期間設定
        start_date = datetime(2025, 8, 1, 8, 0, 0)
        end_date = datetime(2025, 8, 11, 12, 0, 0)
        
        print(f"📅 検索期間: {start_date} ～ {end_date}")
        
        # データ取得テスト
        print("\n🔍 データ取得テスト...")
        data = await repo.find_by_date_range(start_date, end_date, "USD/JPY", 1000)
        
        print(f"取得データ数: {len(data)}件")
        if data:
            print(f"最初のデータ: {data[0].timestamp} - {data[0].close_price}")
            print(f"最後のデータ: {data[-1].timestamp} - {data[-1].close_price}")
        
        # セッション終了
        await session.close()
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_repository())
