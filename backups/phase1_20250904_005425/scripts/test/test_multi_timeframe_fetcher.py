#!/usr/bin/env python3
"""
マルチタイムフレームデータ取得サービステストスクリプト
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
from src.infrastructure.database.services.multi_timeframe_data_fetcher_service import (
    MultiTimeframeDataFetcherService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class MultiTimeframeFetcherTester:
    """
    マルチタイムフレームデータ取得サービステストクラス
    """

    def __init__(self):
        self.session = None
        self.fetcher_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up multi-timeframe fetcher test...")
        logger.info("Setting up multi-timeframe fetcher test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # マルチタイムフレームデータ取得サービスを初期化
        self.fetcher_service = MultiTimeframeDataFetcherService(self.session)

        print("Multi-timeframe fetcher test setup completed")
        logger.info("Multi-timeframe fetcher test setup completed")

    async def test_connection(self):
        """
        接続テスト
        """
        print("Testing connection...")
        logger.info("Testing connection...")

        try:
            is_connected = await self.fetcher_service.test_connection()
            if is_connected:
                print("✅ Connection test passed")
                logger.info("Connection test passed")
            else:
                print("❌ Connection test failed")
                logger.error("Connection test failed")

            return is_connected

        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            logger.error(f"Connection test failed: {e}")
            return False

    async def test_single_timeframe_fetch(self):
        """
        単一時間軸のデータ取得テスト
        """
        print("Testing single timeframe fetch...")
        logger.info("Testing single timeframe fetch...")

        try:
            # 5分足データの取得テスト
            print("Testing 5m timeframe...")
            m5_data = await self.fetcher_service.fetch_timeframe_data("5m")
            if m5_data:
                print(f"✅ 5m data fetched: {m5_data.timestamp} - {m5_data.close_price}")
            else:
                print("❌ 5m data fetch failed")

            # 1時間足データの取得テスト
            print("Testing 1h timeframe...")
            h1_data = await self.fetcher_service.fetch_timeframe_data("1h")
            if h1_data:
                print(f"✅ 1h data fetched: {h1_data.timestamp} - {h1_data.close_price}")
            else:
                print("❌ 1h data fetch failed")

            # 4時間足データの取得テスト
            print("Testing 4h timeframe...")
            h4_data = await self.fetcher_service.fetch_timeframe_data("4h")
            if h4_data:
                print(f"✅ 4h data fetched: {h4_data.timestamp} - {h4_data.close_price}")
            else:
                print("❌ 4h data fetch failed")

            # 日足データの取得テスト
            print("Testing 1d timeframe...")
            d1_data = await self.fetcher_service.fetch_timeframe_data("1d")
            if d1_data:
                print(f"✅ 1d data fetched: {d1_data.timestamp} - {d1_data.close_price}")
            else:
                print("❌ 1d data fetch failed")

        except Exception as e:
            print(f"❌ Single timeframe fetch test failed: {e}")
            logger.error(f"Single timeframe fetch test failed: {e}")

    async def test_all_timeframes_fetch(self):
        """
        全時間軸のデータ取得テスト
        """
        print("Testing all timeframes fetch...")
        logger.info("Testing all timeframes fetch...")

        try:
            # 全時間軸のデータを取得
            results = await self.fetcher_service.fetch_all_timeframes()

            print(f"Fetched data for {len(results)} timeframes:")
            for timeframe, data in results.items():
                if data:
                    print(f"  ✅ {timeframe}: {data.timestamp} - {data.close_price}")
                else:
                    print(f"  ❌ {timeframe}: Failed to fetch")

        except Exception as e:
            print(f"❌ All timeframes fetch test failed: {e}")
            logger.error(f"All timeframes fetch test failed: {e}")

    async def test_historical_data_fetch(self):
        """
        履歴データ取得テスト
        """
        print("Testing historical data fetch...")
        logger.info("Testing historical data fetch...")

        try:
            from datetime import datetime, timedelta

            # 過去7日間のデータを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            # 各時間軸の履歴データを取得
            for timeframe in ["5m", "1h", "4h", "1d"]:
                print(f"Fetching {timeframe} historical data...")
                historical_data = (
                    await self.fetcher_service.fetch_historical_data_for_timeframe(
                        timeframe, start_date, end_date
                    )
                )

                if historical_data:
                    print(f"  ✅ {timeframe}: {len(historical_data)} records fetched")
                else:
                    print(f"  ❌ {timeframe}: No historical data fetched")

        except Exception as e:
            print(f"❌ Historical data fetch test failed: {e}")
            logger.error(f"Historical data fetch test failed: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Multi-timeframe fetcher test cleanup completed")
        logger.info("Multi-timeframe fetcher test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting multi-timeframe fetcher test...")
    logger.info("Starting multi-timeframe fetcher test...")

    tester = MultiTimeframeFetcherTester()

    try:
        await tester.setup()

        # 接続テスト
        if await tester.test_connection():
            # 単一時間軸テスト
            await tester.test_single_timeframe_fetch()

            # 全時間軸テスト
            await tester.test_all_timeframes_fetch()

            # 履歴データテスト
            await tester.test_historical_data_fetch()
        else:
            print("Skipping tests due to connection failure")

        print("Multi-timeframe fetcher test completed successfully!")
        logger.info("Multi-timeframe fetcher test completed successfully!")

    except Exception as e:
        print(f"Multi-timeframe fetcher test failed: {e}")
        logger.error(f"Multi-timeframe fetcher test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
