#!/usr/bin/env python3
"""
時間軸変換精度テストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.infrastructure.database.services.timeframe_converter import TimeframeConverter
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TimeframeAccuracyTester:
    """
    時間軸変換精度テストクラス
    """

    def __init__(self):
        self.session = None
        self.timeframe_converter = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up timeframe accuracy test...")
        logger.info("Setting up timeframe accuracy test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # リポジトリとコンバーターを初期化
        price_repo = PriceDataRepositoryImpl(self.session)
        indicator_repo = TechnicalIndicatorRepositoryImpl(self.session)
        self.timeframe_converter = TimeframeConverter(price_repo, indicator_repo)

        print("Timeframe accuracy test setup completed")
        logger.info("Timeframe accuracy test setup completed")

    async def test_timeframe_conversion(self):
        """
        時間軸変換の精度をテスト
        """
        print("Testing timeframe conversion accuracy...")
        logger.info("Testing timeframe conversion accuracy...")

        try:
            from datetime import datetime, timedelta

            # テスト期間（過去24時間）
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            # マルチタイムフレームデータを作成
            multi_timeframe_data = (
                await self.timeframe_converter.create_multi_timeframe_data(
                    start_date, end_date, "USD/JPY"
                )
            )

            print(f"Created {len(multi_timeframe_data)} timeframes")

            # 各時間軸のデータを分析
            for timeframe, data in multi_timeframe_data.items():
                print(f"\n=== {timeframe} Timeframe ===")

                price_data = data.get("price_data", {})
                indicators = data.get("indicators", {})

                if hasattr(price_data, "shape") and price_data.shape[0] > 0:
                    print(f"Price data points: {price_data.shape[0]}")
                    print(f"Latest close: {price_data['Close'].iloc[-1]:.5f}")
                    print(
                        f"Price range: {price_data['High'].max():.5f} - {price_data['Low'].min():.5f}"
                    )
                else:
                    print("No price data available")

                # 指標データを表示
                if indicators:
                    print("Indicators:")
                    for indicator_name, indicator_data in indicators.items():
                        print(f"  {indicator_name}: {indicator_data}")
                else:
                    print("No indicators available")

            return multi_timeframe_data

        except Exception as e:
            print(f"Timeframe conversion test failed: {e}")
            logger.error(f"Timeframe conversion test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    async def test_pattern_detection_with_converted_data(self):
        """
        変換されたデータでのパターン検出をテスト
        """
        print("Testing pattern detection with converted data...")
        logger.info("Testing pattern detection with converted data...")

        try:
            from datetime import datetime, timedelta

            from scripts.test.simple_pattern_detector import SimplePatternDetector

            # テスト期間
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            # マルチタイムフレームデータを作成
            multi_timeframe_data = (
                await self.timeframe_converter.create_multi_timeframe_data(
                    start_date, end_date, "USD/JPY"
                )
            )

            # 各パターン検出器でテスト
            for pattern_number in range(1, 7):
                detector = SimplePatternDetector(pattern_number)
                result = detector.detect(multi_timeframe_data)

                if result:
                    print(f"Pattern {pattern_number} detected:")
                    print(f"  Name: {result['pattern_name']}")
                    print(f"  Confidence: {result['confidence']:.2f}")
                    print(f"  Direction: {result['technical_data']['direction']}")
                else:
                    print(f"Pattern {pattern_number}: No detection")

        except Exception as e:
            print(f"Pattern detection test failed: {e}")
            logger.error(f"Pattern detection test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Timeframe accuracy test cleanup completed")
        logger.info("Timeframe accuracy test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting timeframe accuracy test...")
    logger.info("Starting timeframe accuracy test...")

    tester = TimeframeAccuracyTester()

    try:
        await tester.setup()

        # 時間軸変換テスト
        await tester.test_timeframe_conversion()

        # パターン検出テスト
        await tester.test_pattern_detection_with_converted_data()

        print("Timeframe accuracy test completed successfully!")
        logger.info("Timeframe accuracy test completed successfully!")

    except Exception as e:
        print(f"Timeframe accuracy test failed: {e}")
        logger.error(f"Timeframe accuracy test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
