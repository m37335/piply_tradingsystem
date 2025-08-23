#!/usr/bin/env python3
"""
人工的なデータ（同じOHLC値）を削除するスクリプト
"""

import asyncio
import sys
from datetime import datetime, timedelta

# プロジェクトパス追加
sys.path.append("/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)


async def cleanup_artificial_data():
    """人工的なデータを削除"""
    print("🧹 人工的なデータの削除を開始します...")
    
    async with get_async_session() as session:
        repo = PriceDataRepositoryImpl(session)
        
        try:
            # 最新の1000件のデータを取得
            print("📊 データを取得中...")
            all_data = await repo.find_all("USD/JPY", limit=1000)
            
            if not all_data:
                print("❌ データが見つかりませんでした")
                return
            
            print(f"📈 取得したデータ数: {len(all_data)}件")
            
            # 人工的なデータを特定
            artificial_data = []
            for data in all_data:
                if (data.open_price == data.high_price == 
                    data.low_price == data.close_price):
                    artificial_data.append(data)
            
            print(f"⚠️  人工的なデータ数: {len(artificial_data)}件")
            
            if not artificial_data:
                print("✅ 人工的なデータは見つかりませんでした")
                return
            
            # 最新の10件の人工的データを表示
            print("\n🔍 最新の人工的データ（最大10件）:")
            print("=" * 80)
            for i, data in enumerate(artificial_data[:10]):
                print(f"{i+1}. {data.timestamp} - O={data.open_price}, H={data.high_price}, L={data.low_price}, C={data.close_price}")
            
            # 削除確認
            print(f"\n⚠️  {len(artificial_data)}件の人工的データを削除しますか？")
            print("この操作は取り消せません。")
            
            # 自動削除（本番環境用）
            print("🔄 自動削除を実行します...")
            
            deleted_count = 0
            for data in artificial_data:
                try:
                    await repo.delete(data.id)
                    deleted_count += 1
                    if deleted_count % 10 == 0:
                        print(f"✅ {deleted_count}件削除完了")
                except Exception as e:
                    print(f"❌ 削除エラー (ID: {data.id}): {e}")
            
            print(f"🎉 削除完了: {deleted_count}件")
            
            # 削除後のデータ確認
            remaining_data = await repo.find_all("USD/JPY", limit=10)
            print(f"\n📊 削除後の最新データ数: {len(remaining_data)}件")
            
            if remaining_data:
                print("\n📈 削除後の最新データ（最大5件）:")
                print("=" * 80)
                for i, data in enumerate(remaining_data[:5]):
                    print(f"{i+1}. {data.timestamp} - O={data.open_price}, H={data.high_price}, L={data.low_price}, C={data.close_price}")
            
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(cleanup_artificial_data())
