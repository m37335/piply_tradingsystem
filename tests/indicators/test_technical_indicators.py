#!/usr/bin/env python3
"""
Technical Indicators Test Script
テクニカル指標計算テストスクリプト
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.append("/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.technical_indicator_service import (
    TechnicalIndicatorService,
)


async def test_technical_indicators():
    """テクニカル指標計算をテスト"""
    print("=== テクニカル指標計算テスト ===")

    try:
        # セッション初期化
        session = await get_async_session()
        print("✅ データベースセッション接続完了")

        # サービス初期化
        service = TechnicalIndicatorService(session)
        print("✅ TechnicalIndicatorService初期化完了")

        # 期間設定（実際のデータに合わせる）
        end_date = datetime(2025, 8, 11, 12, 0, 0)  # 2025-08-11 12:00:00
        start_date = datetime(2024, 3, 19, 9, 0, 0)  # 2024-03-19 09:00:00

        print(f"📅 計算期間: {start_date} ～ {end_date}")

        # RSI計算テスト
        print("\n📊 RSI計算テスト...")

        # データ取得テスト
        print("  🔍 価格データ取得テスト...")
        price_data = await service._get_price_data_for_calculation(
            start_date=start_date, end_date=end_date, min_periods=15
        )
        print(f"  取得データ数: {len(price_data)}件")
        if price_data:
            print(f"  最初のデータ: {price_data[0].timestamp} - {price_data[0].close_price}")
            print(
                f"  最後のデータ: {price_data[-1].timestamp} - {price_data[-1].close_price}"
            )

        rsi_results = await service.calculate_rsi(
            start_date=start_date, end_date=end_date
        )
        print(f"RSI結果: {len(rsi_results)}件")

        # RSI計算の詳細デバッグ
        if len(price_data) >= 15:  # RSI計算に必要な最小データ数
            print("  🔍 RSI計算詳細デバッグ...")
            rsi_values = service._calculate_rsi_values(price_data, 14)
            print(f"  RSI計算結果: {len(rsi_values)}件")
            if rsi_values:
                print(f"  最初のRSI: {rsi_values[0][1]:.2f}")
                print(f"  最後のRSI: {rsi_values[-1][1]:.2f}")
        else:
            print(f"  ⚠️ データ不足: {len(price_data)}件 < 15件")

        # MACD計算テスト
        print("\n📈 MACD計算テスト...")
        macd_results = await service.calculate_macd(
            start_date=start_date, end_date=end_date
        )
        print(f"MACD結果: {len(macd_results)}件")

        # ボリンジャーバンド計算テスト
        print("\n📊 ボリンジャーバンド計算テスト...")
        bb_results = await service.calculate_bollinger_bands(
            start_date=start_date, end_date=end_date
        )
        print(f"ボリンジャーバンド結果: {len(bb_results)}件")

        # 全指標計算テスト
        print("\n🔄 全指標計算テスト...")
        all_results = await service.calculate_all_indicators(
            start_date=start_date, end_date=end_date
        )
        total_indicators = sum(len(indicators) for indicators in all_results.values())
        print(f"全指標結果: {total_indicators}件")

        # セッション終了
        await session.close()
        print("\n✅ テスト完了")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_technical_indicators())
