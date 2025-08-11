#!/usr/bin/env python3
"""
Test Data Amount Script
データ量確認スクリプト
"""

import asyncio
import sys

sys.path.append("/app")

from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient


async def test_data_amount():
    """データ量をテスト"""
    print("=== Yahoo Financeから取得可能なデータ量を確認 ===")
    
    client = YahooFinanceClient()
    
    # 7日分の5分足データを取得
    print("7日分の5分足データを取得中...")
    df = await client.get_historical_data('USD/JPY', '7d', '5m')
    
    if df is None or df.empty:
        print("❌ データが取得できませんでした")
        return
    
    print(f"✅ 取得データ: {len(df)}件")
    print(f"データ期間: {df.index[0]} から {df.index[-1]}")
    print("\n最初の5件:")
    print(df.head())
    print("\n最後の5件:")
    print(df.tail())
    
    # 1日分のデータ量も確認
    print("\n=== 1日分のデータ量も確認 ===")
    df_1d = await client.get_historical_data('USD/JPY', '1d', '5m')
    if df_1d is not None and not df_1d.empty:
        print(f"1日分の5分足データ: {len(df_1d)}件")


if __name__ == "__main__":
    asyncio.run(test_data_amount())
