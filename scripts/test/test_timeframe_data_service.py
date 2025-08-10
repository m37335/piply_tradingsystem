#!/usr/bin/env python3
"""
時間軸別データ保存サービステストスクリプト
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
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.services.timeframe_data_service import (
    TimeframeDataService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TimeframeDataServiceTester:
    """
    時間軸別データ保存サービステストクラス
    """

    def __init__(self):
        self.session = None
        self.timeframe_service = None

    async def setup(self):
        """
        テスト環境をセットアップ
        """
        print("Setting up timeframe data service test...")
        logger.info("Setting up timeframe data service test...")

        # 環境変数の設定
        if not os.getenv("DATABASE_URL"):
            os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

        # セッションを取得
        self.session = await get_async_session()

        # 時間軸別データ保存サービスを初期化
        self.timeframe_service = TimeframeDataService(self.session)

        print("Timeframe data service test setup completed")
        logger.info("Timeframe data service test setup completed")

    async def test_save_5m_data(self):
        """
        5分足データ保存テスト
        """
        print("Testing 5m data save...")
        logger.info("Testing 5m data save...")

        try:
            from datetime import datetime

            # テスト用の5分足データを作成
            test_data = PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=datetime.now(),
                open_price=147.50,
                high_price=147.60,
                low_price=147.40,
                close_price=147.55,
                volume=1000,
                data_source="Test",
            )

            # データを保存
            saved_data = await self.timeframe_service.save_5m_data(test_data)

            if saved_data:
                print(
                    f"✅ 5m data saved: {saved_data.timestamp} - {saved_data.close_price}"
                )
            else:
                print("❌ 5m data save failed")

        except Exception as e:
            print(f"❌ 5m data save test failed: {e}")
            logger.error(f"5m data save test failed: {e}")

    async def test_save_d1_data(self):
        """
        日足データ保存テスト
        """
        print("Testing D1 data save...")
        logger.info("Testing D1 data save...")

        try:
            from datetime import datetime

            # テスト用の日足データを作成
            test_data = PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=datetime.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
                open_price=147.00,
                high_price=148.00,
                low_price=146.50,
                close_price=147.55,
                volume=10000,
                data_source="Test",
            )

            # データを保存
            saved_data = await self.timeframe_service.save_d1_data(test_data)

            if saved_data:
                print(
                    f"✅ D1 data saved: {saved_data.timestamp} - {saved_data.close_price}"
                )
            else:
                print("❌ D1 data save failed")

        except Exception as e:
            print(f"❌ D1 data save test failed: {e}")
            logger.error(f"D1 data save test failed: {e}")

    async def test_aggregate_h1_data(self):
        """
        H1データ集計テスト
        """
        print("Testing H1 data aggregation...")
        logger.info("Testing H1 data aggregation...")

        try:
            # H1データを集計・保存
            h1_data = await self.timeframe_service.aggregate_and_save_h1_data()

            if h1_data:
                print(f"✅ H1 data aggregated: {len(h1_data)} records")
                for data in h1_data[:3]:  # 最初の3件を表示
                    print(f"  - {data.timestamp} - {data.close_price}")
            else:
                print("❌ H1 data aggregation failed or no data")

        except Exception as e:
            print(f"❌ H1 data aggregation test failed: {e}")
            logger.error(f"H1 data aggregation test failed: {e}")

    async def test_aggregate_h4_data(self):
        """
        H4データ集計テスト
        """
        print("Testing H4 data aggregation...")
        logger.info("Testing H4 data aggregation...")

        try:
            # H4データを集計・保存
            h4_data = await self.timeframe_service.aggregate_and_save_h4_data()

            if h4_data:
                print(f"✅ H4 data aggregated: {len(h4_data)} records")
                for data in h4_data[:3]:  # 最初の3件を表示
                    print(f"  - {data.timestamp} - {data.close_price}")
            else:
                print("❌ H4 data aggregation failed or no data")

        except Exception as e:
            print(f"❌ H4 data aggregation test failed: {e}")
            logger.error(f"H4 data aggregation test failed: {e}")

    async def test_get_multi_timeframe_data(self):
        """
        マルチタイムフレームデータ取得テスト
        """
        print("Testing multi-timeframe data retrieval...")
        logger.info("Testing multi-timeframe data retrieval...")

        try:
            from datetime import datetime, timedelta

            # 過去24時間のデータを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            multi_timeframe_data = (
                await self.timeframe_service.get_multi_timeframe_data(
                    start_date, end_date
                )
            )

            if multi_timeframe_data:
                print(
                    f"✅ Multi-timeframe data retrieved: {len(multi_timeframe_data)} timeframes"
                )
                for timeframe, data in multi_timeframe_data.items():
                    price_data = data["price_data"]
                    if not price_data.empty:
                        print(f"  {timeframe}: {len(price_data)} records")
                    else:
                        print(f"  {timeframe}: No data")
            else:
                print("❌ Multi-timeframe data retrieval failed")

        except Exception as e:
            print(f"❌ Multi-timeframe data retrieval test failed: {e}")
            logger.error(f"Multi-timeframe data retrieval test failed: {e}")

    async def test_update_all_timeframes(self):
        """
        全時間軸更新テスト
        """
        print("Testing update all timeframes...")
        logger.info("Testing update all timeframes...")

        try:
            # 全時間軸のデータを更新
            results = await self.timeframe_service.update_all_timeframes()

            if results:
                print("✅ All timeframes updated:")
                for timeframe, count in results.items():
                    print(f"  {timeframe}: {count} records")
            else:
                print("❌ Update all timeframes failed")

        except Exception as e:
            print(f"❌ Update all timeframes test failed: {e}")
            logger.error(f"Update all timeframes test failed: {e}")

    async def test_get_latest_data(self):
        """
        最新データ取得テスト
        """
        print("Testing latest data retrieval...")
        logger.info("Testing latest data retrieval...")

        try:
            # 各時間軸の最新データを取得
            for timeframe in ["5m", "1h", "4h", "1d"]:
                latest_data = await self.timeframe_service.get_latest_data_by_timeframe(
                    timeframe, limit=3
                )

                if latest_data:
                    print(f"✅ Latest {timeframe} data: {len(latest_data)} records")
                    for data in latest_data:
                        print(f"  - {data.timestamp} - {data.close_price}")
                else:
                    print(f"❌ No latest {timeframe} data found")

        except Exception as e:
            print(f"❌ Latest data retrieval test failed: {e}")
            logger.error(f"Latest data retrieval test failed: {e}")

    async def cleanup(self):
        """
        テスト環境をクリーンアップ
        """
        if self.session:
            await self.session.close()
        print("Timeframe data service test cleanup completed")
        logger.info("Timeframe data service test cleanup completed")


async def main():
    """
    メイン関数
    """
    print("Starting timeframe data service test...")
    logger.info("Starting timeframe data service test...")

    tester = TimeframeDataServiceTester()

    try:
        await tester.setup()

        # 5分足データ保存テスト
        await tester.test_save_5m_data()

        # 日足データ保存テスト
        await tester.test_save_d1_data()

        # H1データ集計テスト
        await tester.test_aggregate_h1_data()

        # H4データ集計テスト
        await tester.test_aggregate_h4_data()

        # マルチタイムフレームデータ取得テスト
        await tester.test_get_multi_timeframe_data()

        # 最新データ取得テスト
        await tester.test_get_latest_data()

        # 全時間軸更新テスト
        await tester.test_update_all_timeframes()

        print("Timeframe data service test completed successfully!")
        logger.info("Timeframe data service test completed successfully!")

    except Exception as e:
        print(f"Timeframe data service test failed: {e}")
        logger.error(f"Timeframe data service test failed: {e}")
        raise
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
