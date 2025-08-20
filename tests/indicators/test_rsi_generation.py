#!/usr/bin/env python3
"""
RSI統合データ生成テスト
"""

import asyncio
import os
from src.infrastructure.database.services.continuous_processing_service import ContinuousProcessingService
from src.infrastructure.database.connection import get_async_session

async def test_rsi_generation():
    """RSI統合データ生成をテスト"""
    print("🚀 RSI統合データ生成テスト開始")
    
    # データベースURLを設定
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"
    
    try:
        # セッションを取得
        session = await get_async_session()
        print("✅ データベースセッション取得完了")
        
        # 継続処理サービスを初期化
        service = ContinuousProcessingService(session)
        print("✅ 継続処理サービス初期化完了")
        
        # 指標計算を実行
        result = await service.calculate_all_indicators_enhanced()
        print(f"📊 指標計算結果: {result}")
        
        # セッションを閉じる
        await session.close()
        print("✅ テスト完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rsi_generation())
