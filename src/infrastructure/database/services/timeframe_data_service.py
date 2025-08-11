"""
時間軸別データ保存・集計サービス

各時間軸のデータを適切に保存し、集計するシステム
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.services.multi_timeframe_data_fetcher_service import (
    MultiTimeframeDataFetcherService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class TimeframeDataService:
    """
    時間軸別データ保存・集計サービス

    責任:
    - 5分足データの基本保存
    - 日足データの個別取得・保存
    - H1, H4データの5分足からの集計・保存
    - マルチタイムフレームデータの提供

    特徴:
    - 効率的なデータ管理
    - 重複防止
    - 自動集計
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session
        self.price_repo = PriceDataRepositoryImpl(session)
        self.fetcher_service = MultiTimeframeDataFetcherService(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"

        # 時間軸設定
        self.timeframes = {
            "5m": {"description": "5分足", "minutes": 5},
            "1h": {"description": "1時間足", "minutes": 60},
            "4h": {"description": "4時間足", "minutes": 240},
            "1d": {"description": "日足", "minutes": 1440},
        }

        logger.info(f"Initialized TimeframeDataService for {self.currency_pair}")

    async def save_5m_data(self, price_data: PriceDataModel) -> PriceDataModel:
        """
        5分足データを保存

        Args:
            price_data: 保存する価格データ

        Returns:
            PriceDataModel: 保存された価格データ
        """
        try:
            logger.info(
                f"Saving 5m data: {price_data.timestamp} - {price_data.close_price}"
            )

            # 重複チェック
            existing = await self.price_repo.find_by_timestamp(
                price_data.timestamp, self.currency_pair
            )
            if existing:
                logger.info(f"5m data already exists for {price_data.timestamp}")
                return existing

            # 保存
            saved_data = await self.price_repo.save(price_data)
            logger.info(f"Successfully saved 5m data: {saved_data.timestamp}")

            return saved_data

        except Exception as e:
            logger.error(f"Error saving 5m data: {e}")
            raise

    async def save_d1_data(self, price_data: PriceDataModel) -> PriceDataModel:
        """
        日足データを保存

        Args:
            price_data: 保存する価格データ

        Returns:
            PriceDataModel: 保存された価格データ
        """
        try:
            logger.info(
                f"Saving D1 data: {price_data.timestamp} - {price_data.close_price}"
            )

            # 重複チェック
            existing = await self.price_repo.find_by_timestamp(
                price_data.timestamp, self.currency_pair
            )
            if existing:
                logger.info(f"D1 data already exists for {price_data.timestamp}")
                return existing

            # 保存
            saved_data = await self.price_repo.save(price_data)
            logger.info(f"Successfully saved D1 data: {saved_data.timestamp}")

            return saved_data

        except Exception as e:
            logger.error(f"Error saving D1 data: {e}")
            raise

    async def aggregate_and_save_h1_data(self) -> List[PriceDataModel]:
        """
        5分足から1時間足データを集計して保存

        Returns:
            List[PriceDataModel]: 保存された1時間足データリスト
        """
        try:
            logger.info("Aggregating and saving H1 data from 5m data...")

            # 過去24時間の5分足データを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=24)

            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date, end_date, self.currency_pair, "5m", 1000
            )

            if not m5_data:
                logger.warning("No 5m data available for H1 aggregation")
                return []

            # DataFrameに変換
            df = self._convert_to_dataframe(m5_data)
            if df.empty:
                logger.warning("Empty DataFrame for H1 aggregation")
                return []

            # 1時間足に集計
            h1_df = self._aggregate_timeframe(df, "1H")

            # データベースに保存
            saved_data = []
            for timestamp, row in h1_df.iterrows():
                price_data = PriceDataModel(
                    currency_pair=self.currency_pair,
                    timestamp=timestamp,
                    open_price=float(row["Open"]),
                    high_price=float(row["High"]),
                    low_price=float(row["Low"]),
                    close_price=float(row["Close"]),
                    volume=int(row["Volume"]),
                    data_source="Aggregated from 5m",
                )

                # 重複チェック
                existing = await self.price_repo.find_by_timestamp(
                    timestamp, self.currency_pair
                )
                if not existing:
                    saved_data.append(await self.price_repo.save(price_data))

            logger.info(f"Successfully saved {len(saved_data)} H1 data points")
            return saved_data

        except Exception as e:
            logger.error(f"Error aggregating and saving H1 data: {e}")
            return []

    async def aggregate_and_save_h4_data(self) -> List[PriceDataModel]:
        """
        5分足から4時間足データを集計して保存

        Returns:
            List[PriceDataModel]: 保存された4時間足データリスト
        """
        try:
            logger.info("Aggregating and saving H4 data from 5m data...")

            # 過去7日間の5分足データを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)

            m5_data = await self.price_repo.find_by_date_range_and_timeframe(
                start_date, end_date, self.currency_pair, "5m", 2000
            )

            if not m5_data:
                logger.warning("No 5m data available for H4 aggregation")
                return []

            # DataFrameに変換
            df = self._convert_to_dataframe(m5_data)
            if df.empty:
                logger.warning("Empty DataFrame for H4 aggregation")
                return []

            # 4時間足に集計
            h4_df = self._aggregate_timeframe(df, "4H")

            # データベースに保存
            saved_data = []
            for timestamp, row in h4_df.iterrows():
                price_data = PriceDataModel(
                    currency_pair=self.currency_pair,
                    timestamp=timestamp,
                    open_price=float(row["Open"]),
                    high_price=float(row["High"]),
                    low_price=float(row["Low"]),
                    close_price=float(row["Close"]),
                    volume=int(row["Volume"]),
                    data_source="Aggregated from 5m",
                )

                # 重複チェック
                existing = await self.price_repo.find_by_timestamp(
                    timestamp, self.currency_pair
                )
                if not existing:
                    saved_data.append(await self.price_repo.save(price_data))

            logger.info(f"Successfully saved {len(saved_data)} H4 data points")
            return saved_data

        except Exception as e:
            logger.error(f"Error aggregating and saving H4 data: {e}")
            return []

    async def get_multi_timeframe_data(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        マルチタイムフレームデータを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            Dict: マルチタイムフレームデータ辞書
        """
        try:
            logger.info(f"Getting multi-timeframe data from {start_date} to {end_date}")

            multi_timeframe_data = {}

            # 各時間軸のデータを取得
            for timeframe, config in self.timeframes.items():
                price_data = await self.price_repo.find_by_date_range_and_timeframe(
                    start_date, end_date, self.currency_pair, timeframe, 1000
                )

                if price_data:
                    df = self._convert_to_dataframe(price_data)
                    multi_timeframe_data[timeframe] = {
                        "price_data": df,
                        "description": config["description"],
                    }
                    logger.info(f"Retrieved {len(price_data)} {timeframe} data points")
                else:
                    multi_timeframe_data[timeframe] = {
                        "price_data": pd.DataFrame(),
                        "description": config["description"],
                    }
                    logger.warning(f"No {timeframe} data found")

            return multi_timeframe_data

        except Exception as e:
            logger.error(f"Error getting multi-timeframe data: {e}")
            return {}

    async def update_all_timeframes(self) -> Dict[str, int]:
        """
        全時間軸のデータを更新

        Returns:
            Dict[str, int]: 各時間軸の更新件数
        """
        try:
            logger.info("Updating all timeframes...")

            results = {}

            # 5分足データを取得・保存
            m5_data = await self.fetcher_service.fetch_timeframe_data("5m")
            if m5_data:
                await self.save_5m_data(m5_data)
                results["5m"] = 1
            else:
                results["5m"] = 0

            # 日足データを取得・保存
            d1_data = await self.fetcher_service.fetch_timeframe_data("1d")
            if d1_data:
                await self.save_d1_data(d1_data)
                results["1d"] = 1
            else:
                results["1d"] = 0

            # H1データを集計・保存
            h1_data = await self.aggregate_and_save_h1_data()
            results["1h"] = len(h1_data)

            # H4データを集計・保存
            h4_data = await self.aggregate_and_save_h4_data()
            results["4h"] = len(h4_data)

            logger.info(f"Updated all timeframes: {results}")
            return results

        except Exception as e:
            logger.error(f"Error updating all timeframes: {e}")
            return {}

    def _convert_to_dataframe(self, price_data: List[PriceDataModel]) -> pd.DataFrame:
        """
        価格データをDataFrameに変換
        """
        if not price_data:
            return pd.DataFrame()

        df_data = []
        for data in price_data:
            df_data.append(
                {
                    "timestamp": data.timestamp,
                    "Open": float(data.open_price) if data.open_price else 0.0,
                    "High": float(data.high_price) if data.high_price else 0.0,
                    "Low": float(data.low_price) if data.low_price else 0.0,
                    "Close": float(data.close_price) if data.close_price else 0.0,
                    "Volume": int(data.volume) if data.volume else 0,
                }
            )

        df = pd.DataFrame(df_data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)
        return df

    def _aggregate_timeframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        時間軸を集計
        """
        if df.empty:
            return df

        try:
            # OHLCV集計
            agg_df = (
                df.resample(timeframe)
                .agg(
                    {
                        "Open": "first",
                        "High": "max",
                        "Low": "min",
                        "Close": "last",
                        "Volume": "sum",
                    }
                )
                .dropna()
            )

            return agg_df

        except Exception as e:
            logger.error(f"Error aggregating timeframe {timeframe}: {e}")
            return pd.DataFrame()

    async def get_latest_data_by_timeframe(
        self, timeframe: str, limit: int = 1
    ) -> List[PriceDataModel]:
        """
        特定時間軸の最新データを取得
        """
        try:
            # より直接的なアプローチで最新データを取得
            if timeframe == "5m":
                # データベースの最新データ時刻を取得
                from sqlalchemy import text

                result = await self.session.execute(
                    text(
                        "SELECT MAX(timestamp) as latest_data FROM price_data WHERE currency_pair = :currency_pair"
                    ),
                    {"currency_pair": self.currency_pair},
                )
                latest_data_str = result.scalar()
                if latest_data_str:
                    latest_data = datetime.fromisoformat(
                        latest_data_str.replace("Z", "+00:00")
                    )
                    # より短い期間で最新データを取得（重複チェックを回避するため）
                    start_date = latest_data - timedelta(hours=24)  # 30日 → 24時間
                    end_date = latest_data
                else:
                    # フォールバック
                    start_date = datetime.now() - timedelta(days=30)
                    end_date = datetime.now()

                # 5分足の場合は直接取得
                price_data = await self.price_repo.find_by_date_range(
                    start_date,
                    end_date,
                    self.currency_pair,
                    limit,
                )

                # デバッグ用ログ
                if price_data:
                    logger.info(
                        f"Found {len(price_data)} price data records for {timeframe}"
                    )
                    logger.info(
                        f"Range: {price_data[0].timestamp} to {price_data[-1].timestamp}"
                    )

                return price_data
            else:
                # 他の時間軸の場合は従来の方法を使用
                return await self.price_repo.find_by_date_range_and_timeframe(
                    datetime.now() - timedelta(days=7),
                    datetime.now(),
                    self.currency_pair,
                    timeframe,
                    limit,
                )
        except Exception as e:
            logger.error(f"Error getting latest {timeframe} data: {e}")
            return []
