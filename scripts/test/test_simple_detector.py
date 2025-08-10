#!/usr/bin/env python3
"""
シンプルパターン検出器テストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.pattern_detection_service import (
    PatternDetectionService,
)
from src.utils.logging_config import get_infrastructure_logger
from simple_pattern_detector import SimplePatternDetector

logger = get_infrastructure_logger()


class SimpleDetectorTester:
    """
    シンプル検出器テストクラス
    """

    def __init__(self):
        self.session = None
        self.pattern_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up simple detector test...")
        logger.info("Setting up simple detector test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()
        
        # パターン検出サービスを初期化
        self.pattern_service = PatternDetectionService(self.session)

        print("Simple detector test setup completed")
        logger.info("Simple detector test setup completed")

    async def test_simple_detector(self):
        """
        シンプル検出器をテスト
        """
        print("Testing simple pattern detector...")
        logger.info("Testing simple pattern detector...")

        try:
            # データを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)
            
            price_data = await self.pattern_service._get_price_data(start_date, end_date)
            indicator_data = await self.pattern_service._get_indicator_data(start_date, end_date)
            
            print(f"Got price data: {len(price_data)} records")
            print(f"Got indicator data: {len(indicator_data)} timeframes")
            
            # 各タイムフレームのデータを表示
            for timeframe, data in indicator_data.items():
                print(f"Timeframe {timeframe}:")
                if "indicators" in data:
                    indicators = data["indicators"]
                    if "rsi" in indicators:
                        rsi_value = indicators["rsi"].get("current_value", "N/A")
                        print(f"  RSI: {rsi_value}")
                    if "macd" in indicators:
                        macd_value = indicators["macd"].get("macd", "N/A")
                        print(f"  MACD: {macd_value}")
            
            # シンプル検出器でテスト
            for pattern_number in range(1, 7):
                detector = SimplePatternDetector(pattern_number)
                result = detector.detect(indicator_data)
                
                if result:
                    print(f"Pattern {pattern_number} detected!")
                    print(f"  Name: {result['pattern_name']}")
                    print(f"  Confidence: {result['confidence']}")
                    print(f"  Direction: {result['technical_data']['direction']}")
                else:
                    print(f"Pattern {pattern_number}: No detection")

        except Exception as e:
            print(f"Simple detector test failed: {e}")
            logger.error(f"Simple detector test failed: {e}")
            import traceback
            traceback.print_exc()
            raise

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Simple detector test cleanup completed")
        logger.info("Simple detector test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting simple detector test...")
    logger.info("Starting simple detector test...")

    tester = SimpleDetectorTester()
    
    try:
        await tester.setup()
        await tester.test_simple_detector()
        print("Simple detector test completed successfully!")
        logger.info("Simple detector test completed successfully!")
        
    except Exception as e:
        print(f"Simple detector test failed: {e}")
        logger.error(f"Simple detector test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
