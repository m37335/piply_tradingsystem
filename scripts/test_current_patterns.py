#!/usr/bin/env python3
"""
現在のデータを使用してGATEパターンをテストするスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.scripts.analysis_system_router import AnalysisSystemRouter

async def test_current_patterns():
    """現在のパターン設定をテスト"""
    print("🚀 現在のGATEパターン設定をテスト")
    print("=" * 50)
    
    # 分析システムルーターを初期化
    router = AnalysisSystemRouter("three_gate")
    await router.initialize()
    
    try:
        # 最新のイベントを手動で処理
        print("📊 最新のイベントを取得中...")
        
        # データベースから最新のイベントを取得
        query = """
        SELECT id, event_type, event_data, created_at, processed
        FROM events 
        WHERE event_type = 'data_collection_completed'
        ORDER BY created_at DESC 
        LIMIT 1
        """
        
        async with router.db_manager.get_connection() as conn:
            result = await conn.fetchrow(query)
        
        if result:
            print(f"📥 最新イベント: ID={result['id']}, 時刻={result['created_at']}")
            
            # イベントを手動で処理
            await router._process_three_gate_event(result['event_data'])
            
            print("✅ テスト完了")
        else:
            print("❌ 処理可能なイベントが見つかりません")
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await router.db_manager.close()

if __name__ == "__main__":
    asyncio.run(test_current_patterns())
