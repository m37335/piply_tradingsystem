#!/usr/bin/env python3
"""
テストデータを使用したパターン検出テストスクリプト
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

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.efficient_pattern_detection_service import (
    EfficientPatternDetectionService,
)
from src.infrastructure.database.services.test_data_generator_service import (
    TestDataGeneratorService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PatternDetectionWithTestDataTester:
    """
    テストデータを使用したパターン検出テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_service = None
        self.test_data_generator = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up pattern detection with test data test...")
        logger.info("Setting up pattern detection with test data test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # 効率的パターン検出サービスを初期化
        self.pattern_service = EfficientPatternDetectionService(self.session)

        # テストデータ生成サービスを初期化
        self.test_data_generator = TestDataGeneratorService(self.session)

        print("Pattern detection with test data test setup completed")
        logger.info("Pattern detection with test data test setup completed")

    async def test_pattern_1_detection(self):
        """
        パターン1（トレンド転換）の検出テスト
        """
        print("Testing Pattern 1 (Trend Reversal) detection...")
        logger.info("Testing Pattern 1 (Trend Reversal) detection...")

        try:
            # パターン1用のテストデータを生成
            success = await self.test_data_generator.generate_pattern_1_test_data()
            if not success:
                print("❌ Failed to generate Pattern 1 test data")
                return

            print("✅ Pattern 1 test data generated successfully")

            # 過去24時間のデータでパターン検出を実行
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            patterns = await self.pattern_service.detect_all_patterns(
                start_date, end_date
            )

            if patterns and 1 in patterns:
                pattern_list = patterns[1]
                print(f"✅ Pattern 1 detected: {len(pattern_list)} patterns")
                for pattern in pattern_list:
                    print(
                        f"  - {pattern.pattern_name} (confidence: {pattern.confidence_score}, direction: {pattern.direction})"
                    )
            else:
                print("❌ Pattern 1 not detected")
                print(
                    f"Available patterns: {list(patterns.keys()) if patterns else 'None'}"
                )

        except Exception as e:
            print(f"❌ Pattern 1 detection test failed: {e}")
            logger.error(f"Pattern 1 detection test failed: {e}")

    async def test_pattern_2_detection(self):
        """
        パターン2（押し目・戻り売り）の検出テスト
        """
        print("Testing Pattern 2 (Pullback) detection...")
        logger.info("Testing Pattern 2 (Pullback) detection...")

        try:
            # パターン2用のテストデータを生成
            success = await self.test_data_generator.generate_pattern_2_test_data()
            if not success:
                print("❌ Failed to generate Pattern 2 test data")
                return

            print("✅ Pattern 2 test data generated successfully")

            # 過去24時間のデータでパターン検出を実行
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            patterns = await self.pattern_service.detect_all_patterns(
                start_date, end_date
            )

            if patterns and 2 in patterns:
                pattern_list = patterns[2]
                print(f"✅ Pattern 2 detected: {len(pattern_list)} patterns")
                for pattern in pattern_list:
                    print(
                        f"  - {pattern.pattern_name} (confidence: {pattern.confidence_score}, direction: {pattern.direction})"
                    )
            else:
                print("❌ Pattern 2 not detected")
                print(
                    f"Available patterns: {list(patterns.keys()) if patterns else 'None'}"
                )

        except Exception as e:
            print(f"❌ Pattern 2 detection test failed: {e}")
            logger.error(f"Pattern 2 detection test failed: {e}")

    async def test_all_patterns_detection(self):
        """
        全パターンの検出テスト
        """
        print("Testing all patterns detection with test data...")
        logger.info("Testing all patterns detection with test data...")

        try:
            # パターン1とパターン2のテストデータを生成
            success1 = await self.test_data_generator.generate_pattern_1_test_data()
            success2 = await self.test_data_generator.generate_pattern_2_test_data()

            if not success1 or not success2:
                print("❌ Failed to generate test data")
                return

            print("✅ Test data generated successfully")

            # 過去24時間のデータでパターン検出を実行
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            patterns = await self.pattern_service.detect_all_patterns(
                start_date, end_date
            )

            if patterns:
                print(f"✅ All patterns detected: {len(patterns)} pattern types")
                for pattern_type, pattern_list in patterns.items():
                    print(f"  Pattern {pattern_type}: {len(pattern_list)} detections")
                    for pattern in pattern_list[:2]:  # 最初の2つを表示
                        print(
                            f"    - {pattern.pattern_name} (confidence: {pattern.confidence_score}, direction: {pattern.direction})"
                        )
            else:
                print("❌ No patterns detected")

        except Exception as e:
            print(f"❌ All patterns detection test failed: {e}")
            logger.error(f"All patterns detection test failed: {e}")

    async def test_multi_timeframe_data_with_test_data(self):
        """
        テストデータを使用したマルチタイムフレームデータ構築テスト
        """
        print("Testing multi-timeframe data building with test data...")
        logger.info("Testing multi-timeframe data building with test data...")

        try:
            # テストデータを生成
            await self.test_data_generator.generate_pattern_1_test_data()

            # 過去6時間のデータでマルチタイムフレームデータを構築
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=6)

            multi_timeframe_data = (
                await self.pattern_service._build_efficient_multi_timeframe_data(
                    start_date, end_date
                )
            )

            if multi_timeframe_data:
                print(
                    f"✅ Multi-timeframe data built: {len(multi_timeframe_data)} timeframes"
                )
                for timeframe, data in multi_timeframe_data.items():
                    price_data = data.get("price_data", pd.DataFrame())
                    indicators = data.get("indicators", {})
                    print(
                        f"  {timeframe}: {len(price_data)} price records, {len(indicators)} indicators"
                    )

                    # 指標の詳細を表示
                    if indicators:
                        for indicator_type, indicator_data in indicators.items():
                            if indicator_type == "rsi":
                                print(
                                    f"    RSI: {indicator_data.iloc[-1] if hasattr(indicator_data, 'iloc') else indicator_data}"
                                )
                            elif indicator_type == "macd":
                                print(
                                    f"    MACD: {indicator_data['macd'].iloc[-1] if hasattr(indicator_data, 'iloc') else indicator_data}"
                                )
                            elif indicator_type == "bollinger_bands":
                                print(
                                    f"    BB: {indicator_data['middle'].iloc[-1] if hasattr(indicator_data, 'iloc') else indicator_data}"
                                )
            else:
                print("❌ No multi-timeframe data built")

        except Exception as e:
            print(f"❌ Multi-timeframe data building test failed: {e}")
            logger.error(f"Multi-timeframe data building test failed: {e}")

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
        print("Pattern detection with test data test cleanup completed")
        logger.info("Pattern detection with test data test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting pattern detection with test data test...")
    logger.info("Starting pattern detection with test data test...")

    tester = PatternDetectionWithTestDataTester()

    try:
        await tester.setup()

        # マルチタイムフレームデータ構築テスト（テストデータ使用）
        await tester.test_multi_timeframe_data_with_test_data()

        # パターン1検出テスト
        await tester.test_pattern_1_detection()

        # テストデータをクリーンアップ
        await tester.cleanup_test_data()

        # パターン2検出テスト
        await tester.test_pattern_2_detection()

        # テストデータをクリーンアップ
        await tester.cleanup_test_data()

        # 全パターン検出テスト
        await tester.test_all_patterns_detection()

        # 最終クリーンアップ
        await tester.cleanup_test_data()

        print("Pattern detection with test data test completed successfully!")
        logger.info("Pattern detection with test data test completed successfully!")

    except Exception as e:
        print(f"Pattern detection with test data test failed: {e}")
        logger.error(f"Pattern detection with test data test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
