#!/usr/bin/env python3
"""
パターン検出テストスクリプト
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
from src.infrastructure.database.services.pattern_detection_service import (
    PatternDetectionService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class PatternDetectionTester:
    """
    パターン検出テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up pattern detection test...")
        logger.info("Setting up pattern detection test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # パターン検出サービスを初期化
        self.pattern_service = PatternDetectionService(self.session)

        print("Pattern detection test setup completed")
        logger.info("Pattern detection test setup completed")

    async def test_pattern_detection(self):
        """
        パターン検出をテスト
        """
        print("Testing pattern detection...")
        logger.info("Testing pattern detection...")

        try:
            # パターン検出を実行
            patterns = await self.pattern_service.detect_all_patterns()

            print(f"Pattern detection completed. Found {len(patterns)} pattern types")
            logger.info(
                f"Pattern detection completed. Found {len(patterns)} pattern types"
            )

            for pattern_type, pattern_list in patterns.items():
                print(f"Pattern type {pattern_type}: {len(pattern_list)} patterns")
                logger.info(
                    f"Pattern type {pattern_type}: {len(pattern_list)} patterns"
                )

                # 各パターンの詳細を表示
                for pattern in pattern_list[:3]:  # 最初の3つだけ表示
                    print(f"  - Pattern: {pattern.pattern_name}")
                    print(f"    Confidence: {pattern.confidence_score}")
                    print(f"    Direction: {pattern.direction}")
                    print(f"    Detection time: {pattern.timestamp}")
                    logger.info(f"  - Pattern: {pattern.pattern_name}")
                    logger.info(f"    Confidence: {pattern.confidence_score}")
                    logger.info(f"    Direction: {pattern.direction}")
                    logger.info(f"    Detection time: {pattern.timestamp}")

            return patterns

        except Exception as e:
            print(f"Pattern detection test failed: {e}")
            logger.error(f"Pattern detection test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    async def test_specific_patterns(self):
        """
        特定のパターンをテスト
        """
        print("Testing specific patterns...")
        logger.info("Testing specific patterns...")

        try:
            # RSIオーバーブought/オーバーソールドパターンをテスト
            print("Testing RSI patterns...")
            logger.info("Testing RSI patterns...")

            # 最新のRSIデータを取得
            from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
                TechnicalIndicatorRepositoryImpl,
            )

            indicator_repo = TechnicalIndicatorRepositoryImpl(self.session)
            rsi_data = await indicator_repo.find_latest_by_type("RSI", "5m", limit=20)

            print(f"Found {len(rsi_data)} RSI data points")
            logger.info(f"Found {len(rsi_data)} RSI data points")

            # RSIの極値をチェック
            for data in rsi_data[:5]:  # 最初の5つをチェック
                print(f"RSI: {data.value} at {data.timestamp}")
                logger.info(f"RSI: {data.value} at {data.timestamp}")

                if data.value > 70:
                    print(f"  -> Overbought detected (RSI: {data.value})")
                    logger.info(f"  -> Overbought detected (RSI: {data.value})")
                elif data.value < 30:
                    print(f"  -> Oversold detected (RSI: {data.value})")
                    logger.info(f"  -> Oversold detected (RSI: {data.value})")

            # MACDトレンド転換パターンをテスト
            print("Testing MACD patterns...")
            logger.info("Testing MACD patterns...")

            macd_data = await indicator_repo.find_latest_by_type("MACD", "5m", limit=20)
            print(f"Found {len(macd_data)} MACD data points")
            logger.info(f"Found {len(macd_data)} MACD data points")

            # MACDの変化をチェック
            for i, data in enumerate(macd_data[:5]):
                print(f"MACD: {data.value} at {data.timestamp}")
                logger.info(f"MACD: {data.value} at {data.timestamp}")

                if i > 0:
                    prev_data = macd_data[i - 1]
                    change = data.value - prev_data.value
                    print(f"  -> Change: {change:+.6f}")
                    logger.info(f"  -> Change: {change:+.6f}")

        except Exception as e:
            print(f"Specific pattern test failed: {e}")
            logger.error(f"Specific pattern test failed: {e}")
            import traceback

            traceback.print_exc()
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Pattern detection test cleanup completed")
        logger.info("Pattern detection test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting pattern detection test...")
    logger.info("Starting pattern detection test...")

    tester = PatternDetectionTester()

    try:
        await tester.setup()

        # 基本的なパターン検出テスト
        await tester.test_pattern_detection()

        # 特定のパターンテスト
        await tester.test_specific_patterns()

        print("Pattern detection test completed successfully!")
        logger.info("Pattern detection test completed successfully!")

    except Exception as e:
        print(f"Pattern detection test failed: {e}")
        logger.error(f"Pattern detection test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
