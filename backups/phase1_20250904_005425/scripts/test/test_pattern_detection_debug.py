#!/usr/bin/env python3
"""
パターン検出のデバッグ用テストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

import pandas as pd

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.analysis.pattern_detectors.trend_reversal_detector import (
    TrendReversalDetector,
)
from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.efficient_pattern_detection_service import (
    EfficientPatternDetectionService,
)
from src.infrastructure.database.services.test_data_generator_service import (
    TestDataGeneratorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PatternDetectionDebugTester:
    """
    パターン検出のデバッグ用テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_service = None
        self.test_data_generator = None
        self.detector = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up pattern detection debug test...")
        logger.info("Setting up pattern detection debug test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # 効率的パターン検出サービスを初期化
        self.pattern_service = EfficientPatternDetectionService(self.session)

        # テストデータ生成サービスを初期化
        self.test_data_generator = TestDataGeneratorService(self.session)

        # トレンド転換検出器を初期化
        self.detector = TrendReversalDetector()

        print("Pattern detection debug test setup completed")
        logger.info("Pattern detection debug test setup completed")

    async def test_pattern_detector_conditions(self):
        """
        パターン検出器の条件を詳細にテスト
        """
        print("Testing pattern detector conditions in detail...")
        logger.info("Testing pattern detector conditions in detail...")

        try:
            # パターン1用のテストデータを生成
            success = await self.test_data_generator.generate_pattern_1_test_data()
            if not success:
                print("❌ Failed to generate test data")
                return

            print("✅ Test data generated successfully")

            # 過去24時間のデータでマルチタイムフレームデータを構築
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            multi_timeframe_data = (
                await self.pattern_service._build_efficient_multi_timeframe_data(
                    start_date, end_date
                )
            )

            if not multi_timeframe_data:
                print("❌ No multi-timeframe data built")
                return

            print(
                f"✅ Multi-timeframe data built: {len(multi_timeframe_data)} timeframes"
            )

            # 各時間軸の条件を詳細にチェック
            for timeframe in ["D1", "H4", "H1", "M5"]:
                if timeframe in multi_timeframe_data:
                    print(f"\n🔍 Checking {timeframe} conditions:")
                    await self._check_timeframe_conditions(
                        timeframe, multi_timeframe_data[timeframe]
                    )
                else:
                    print(f"❌ {timeframe} data not found")

            # パターン検出器で直接テスト
            print(f"\n🔍 Testing pattern detector directly:")
            result = self.detector.detect(multi_timeframe_data)

            if result:
                print(f"✅ Pattern detected: {result}")
            else:
                print("❌ No pattern detected by detector")

        except Exception as e:
            print(f"❌ Pattern detector conditions test failed: {e}")
            logger.error(f"Pattern detector conditions test failed: {e}")

    async def _check_timeframe_conditions(self, timeframe: str, data: dict):
        """
        特定の時間軸の条件を詳細にチェック
        """
        try:
            indicators = data.get("indicators", {})
            price_data = data.get("price_data", pd.DataFrame())

            print(f"  📊 {timeframe} Price data: {len(price_data)} records")
            if not price_data.empty:
                print(f"    Latest close price: {price_data['Close'].iloc[-1]}")

            # RSI条件チェック
            rsi_data = indicators.get("rsi", {})
            if "current_value" in rsi_data:
                rsi_value = rsi_data["current_value"]
                rsi_condition = rsi_value > 70
                print(
                    f"  📈 RSI: {rsi_value} (condition: > 70) -> {'✅' if rsi_condition else '❌'}"
                )
            else:
                print(f"  📈 RSI: No current_value found")

            # MACD条件チェック
            macd_data = indicators.get("macd", {})
            if "macd" in macd_data and "signal" in macd_data:
                macd_value = macd_data["macd"].iloc[-1]
                signal_value = macd_data["signal"].iloc[-1]
                macd_condition = macd_value < signal_value  # デッドクロス
                print(
                    f"  📊 MACD: {macd_value} vs Signal: {signal_value} (condition: MACD < Signal) -> {'✅' if macd_condition else '❌'}"
                )
            else:
                print(f"  📊 MACD: Insufficient data")

            # ボリンジャーバンド条件チェック
            bb_data = indicators.get("bollinger_bands", {})
            if bb_data and not price_data.empty:
                current_price = price_data["Close"].iloc[-1]
                upper_band = bb_data["upper"].iloc[-1]
                bb_condition = abs(current_price - upper_band) / upper_band < 0.001
                print(
                    f"  📊 BB Touch: Price {current_price} vs Upper {upper_band} (condition: within 0.1%) -> {'✅' if bb_condition else '❌'}"
                )

        except Exception as e:
            print(f"  ❌ Error checking {timeframe} conditions: {e}")

    async def cleanup_test_data(self):
        """
        テストデータをクリーンアップ
        """
        print("Cleaning up test data...")
        logger.info("Cleaning up test data...")

        try:
            success = await self.test_data_generator.cleanup_test_data()
            if success:
                print("✅ Test data cleanup completed")
            else:
                print("❌ Test data cleanup failed")
        except Exception as e:
            print(f"❌ Test data cleanup error: {e}")
            logger.error(f"Test data cleanup error: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Pattern detection debug test cleanup completed")
        logger.info("Pattern detection debug test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting pattern detection debug test...")
    logger.info("Starting pattern detection debug test...")

    tester = PatternDetectionDebugTester()

    try:
        await tester.setup()

        # パターン検出器の条件を詳細にテスト
        await tester.test_pattern_detector_conditions()

        # テストデータをクリーンアップ
        await tester.cleanup_test_data()

        print("Pattern detection debug test completed successfully!")
        logger.info("Pattern detection debug test completed successfully!")

    except Exception as e:
        print(f"Pattern detection debug test failed: {e}")
        logger.error(f"Pattern detection debug test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
