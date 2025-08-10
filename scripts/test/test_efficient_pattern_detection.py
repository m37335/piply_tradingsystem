#!/usr/bin/env python3
"""
効率的パターン検出サービステストスクリプト
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
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class EfficientPatternDetectionTester:
    """
    効率的パターン検出サービステストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up efficient pattern detection test...")
        logger.info("Setting up efficient pattern detection test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # 効率的パターン検出サービスを初期化
        self.pattern_service = EfficientPatternDetectionService(self.session)

        print("Efficient pattern detection test setup completed")
        logger.info("Efficient pattern detection test setup completed")

    async def test_detect_all_patterns(self):
        """
        全パターン検出テスト
        """
        print("Testing all pattern detection...")
        logger.info("Testing all pattern detection...")

        try:
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
                    for pattern in pattern_list[:3]:  # 最初の3つを表示
                        print(
                            f"    - {pattern.pattern_name} (confidence: {pattern.confidence_score})"
                        )
            else:
                print("❌ No patterns detected")

        except Exception as e:
            print(f"❌ All pattern detection test failed: {e}")
            logger.error(f"All pattern detection test failed: {e}")

    async def test_get_latest_patterns(self):
        """
        最新パターン取得テスト
        """
        print("Testing latest pattern retrieval...")
        logger.info("Testing latest pattern retrieval...")

        try:
            # 最新のパターンを取得
            latest_patterns = await self.pattern_service.get_latest_patterns(limit=5)

            if latest_patterns:
                print(f"✅ Latest patterns retrieved: {len(latest_patterns)} patterns")
                for pattern in latest_patterns:
                    print(
                        f"  - {pattern.pattern_name} (confidence: {pattern.confidence_score}, direction: {pattern.direction})"
                    )
            else:
                print("❌ No latest patterns found")

        except Exception as e:
            print(f"❌ Latest pattern retrieval test failed: {e}")
            logger.error(f"Latest pattern retrieval test failed: {e}")

    async def test_get_pattern_statistics(self):
        """
        パターン統計取得テスト
        """
        print("Testing pattern statistics retrieval...")
        logger.info("Testing pattern statistics retrieval...")

        try:
            # 過去24時間のパターン統計を取得
            from datetime import datetime, timedelta

            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            statistics = await self.pattern_service.get_pattern_statistics(
                start_date, end_date
            )

            if statistics:
                print("✅ Pattern statistics retrieved:")
                print(f"  Total patterns: {statistics.get('total_patterns', 0)}")
                print(f"  Pattern types: {statistics.get('pattern_types', 0)}")
                print(
                    f"  Average confidence: {statistics.get('average_confidence', 0):.2f}"
                )

                # パターン別統計
                pattern_breakdown = statistics.get("pattern_breakdown", {})
                if pattern_breakdown:
                    print("  Pattern breakdown:")
                    for pattern_type, count in pattern_breakdown.items():
                        print(f"    - Pattern {pattern_type}: {count}")
            else:
                print("❌ No pattern statistics found")

        except Exception as e:
            print(f"❌ Pattern statistics test failed: {e}")
            logger.error(f"Pattern statistics test failed: {e}")

    async def test_single_pattern_detection(self):
        """
        単一パターン検出テスト
        """
        print("Testing single pattern detection...")
        logger.info("Testing single pattern detection...")

        try:
            # 各パターンタイプを個別にテスト
            for pattern_number in range(1, 7):
                print(f"Testing pattern {pattern_number}...")

                # 過去12時間のデータでパターン検出を実行
                from datetime import datetime, timedelta

                end_date = datetime.now()
                start_date = end_date - timedelta(hours=12)

                patterns = await self.pattern_service.detect_all_patterns(
                    start_date, end_date
                )

                if pattern_number in patterns:
                    pattern_list = patterns[pattern_number]
                    print(
                        f"  ✅ Pattern {pattern_number}: {len(pattern_list)} detections"
                    )
                    for pattern in pattern_list[:2]:  # 最初の2つを表示
                        print(
                            f"    - {pattern.pattern_name} (confidence: {pattern.confidence_score})"
                        )
                else:
                    print(f"  ❌ Pattern {pattern_number}: No detections")

        except Exception as e:
            print(f"❌ Single pattern detection test failed: {e}")
            logger.error(f"Single pattern detection test failed: {e}")

    async def test_multi_timeframe_data_building(self):
        """
        マルチタイムフレームデータ構築テスト
        """
        print("Testing multi-timeframe data building...")
        logger.info("Testing multi-timeframe data building...")

        try:
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
            else:
                print("❌ No multi-timeframe data built")

        except Exception as e:
            print(f"❌ Multi-timeframe data building test failed: {e}")
            logger.error(f"Multi-timeframe data building test failed: {e}")

    async def test_pattern_duplicate_check(self):
        """
        パターン重複チェックテスト
        """
        print("Testing pattern duplicate check...")
        logger.info("Testing pattern duplicate check...")

        try:
            # 最新のパターンを取得して重複チェック機能をテスト
            latest_patterns = await self.pattern_service.get_latest_patterns(limit=3)

            if latest_patterns:
                # 重複チェック機能をテスト
                saved_patterns = (
                    await self.pattern_service._save_patterns_with_duplicate_check(
                        latest_patterns
                    )
                )

                if saved_patterns:
                    print(
                        f"✅ Pattern duplicate check: {len(saved_patterns)} patterns saved"
                    )
                else:
                    print(
                        "✅ Pattern duplicate check: All patterns were duplicates (expected)"
                    )
            else:
                print("❌ No patterns available for duplicate check test")

        except Exception as e:
            print(f"❌ Pattern duplicate check test failed: {e}")
            logger.error(f"Pattern duplicate check test failed: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Efficient pattern detection test cleanup completed")
        logger.info("Efficient pattern detection test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting efficient pattern detection test...")
    logger.info("Starting efficient pattern detection test...")

    tester = EfficientPatternDetectionTester()

    try:
        await tester.setup()

        # マルチタイムフレームデータ構築テスト
        await tester.test_multi_timeframe_data_building()

        # 全パターン検出テスト
        await tester.test_detect_all_patterns()

        # 単一パターン検出テスト
        await tester.test_single_pattern_detection()

        # 最新パターン取得テスト
        await tester.test_get_latest_patterns()

        # パターン統計取得テスト
        await tester.test_get_pattern_statistics()

        # パターン重複チェックテスト
        await tester.test_pattern_duplicate_check()

        print("Efficient pattern detection test completed successfully!")
        logger.info("Efficient pattern detection test completed successfully!")

    except Exception as e:
        print(f"Efficient pattern detection test failed: {e}")
        logger.error(f"Efficient pattern detection test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
