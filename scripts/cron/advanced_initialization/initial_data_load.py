#!/usr/bin/env python3
"""
Initial Data Load Script
初回データ取得スクリプト - 履歴データを一括取得
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

sys.path.append("/app")

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.services.data_fetcher_service import DataFetcherService
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class InitialDataLoader:
    """初回データローダー"""

    def __init__(self):
        self.currency_pair = "USD/JPY"
        self.session = None
        self.yahoo_client = YahooFinanceClient()

    async def initialize(self):
        """初期化"""
        try:
            self.session = await get_async_session()
            logger.info("Initial data loader initialized")
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            raise

    async def load_historical_data(self, days: int = 7):
        """履歴データを読み込み"""
        try:
            logger.info(
                f"Loading {days} days of historical data for {self.currency_pair}"
            )

            # Yahoo Financeから履歴データ取得
            period = f"{days}d"
            df = await self.yahoo_client.get_historical_data(
                self.currency_pair, period, "5m"
            )

            if df is None or df.empty:
                logger.error("No historical data received")
                return 0

            logger.info(f"Retrieved {len(df)} records from Yahoo Finance")

            # データベースに保存
            saved_count = 0
            price_repo = PriceDataRepositoryImpl(self.session)

            for timestamp, row in df.iterrows():
                try:
                    # タイムスタンプの処理
                    if hasattr(timestamp, "to_pydatetime"):
                        dt = timestamp.to_pydatetime()
                    else:
                        dt = datetime.now()

                    # 価格データモデル作成
                    price_data = PriceDataModel(
                        currency_pair=self.currency_pair,
                        timestamp=dt,
                        open_price=float(row["Open"]),
                        high_price=float(row["High"]),
                        low_price=float(row["Low"]),
                        close_price=float(row["Close"]),
                        volume=int(row["Volume"]) if row["Volume"] > 0 else 1000000,
                        data_source="Yahoo Finance",
                    )

                    # 重複チェック
                    existing = await price_repo.find_by_timestamp(
                        dt, self.currency_pair
                    )
                    if existing:
                        continue

                    # 保存
                    await price_repo.save(price_data)
                    saved_count += 1

                    if saved_count % 100 == 0:
                        logger.info(f"Saved {saved_count} records...")

                except Exception as e:
                    logger.warning(f"Error saving record at {timestamp}: {e}")
                    continue

            logger.info(f"Successfully saved {saved_count} historical records")
            return saved_count

        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            return 0

    async def cleanup(self):
        """クリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン関数"""
    logger.info("Starting initial data load...")

    # 環境変数チェック
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///data/test_app.db"

    loader = InitialDataLoader()

    try:
        await loader.initialize()

        # 7日分の履歴データを読み込み
        saved_count = await loader.load_historical_data(days=7)

        if saved_count > 0:
            logger.info(
                f"Initial data load completed successfully: {saved_count} records"
            )
        else:
            logger.error("Initial data load failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Initial data load error: {e}")
        sys.exit(1)
    finally:
        await loader.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
