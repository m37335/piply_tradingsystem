#!/usr/bin/env python3
"""
Debug script for technical indicators calculation
"""

import asyncio
import os
import sys

sys.path.append("/app")

from scripts.cron.technical_indicators_calculator import TechnicalIndicatorsCalculator

async def debug_calculation():
    """デバッグ用の計算実行"""
    try:
        print("=== デバッグ開始 ===")
        
        # 環境変数設定
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"
        
        # 計算器初期化
        print("1. 計算器初期化中...")
        calculator = TechnicalIndicatorsCalculator()
        await calculator.initialize()
        print("✅ 初期化完了")
        
        # テクニカル指標計算
        print("2. テクニカル指標計算中...")
        result = await calculator.calculate_all_indicators()
        print(f"✅ 計算結果: {result}")
        
        # クリーンアップ
        await calculator.cleanup()
        print("✅ クリーンアップ完了")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_calculation())
