"""
マルチタイムフレームデータ取得サービス

各時間軸（5分足、1時間足、4時間足、日足）に対応したデータ取得サービス
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.data_fetch_history_model import (
    DataFetchHistoryModel,
)
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.data_fetch_history_repository_impl import (
    DataFetchHistoryRepositoryImpl,
)
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class MultiTimeframeDataFetcherService:
    """
    マルチタイムフレームデータ取得サービス

    対応時間軸:
    - 5分足 (5m)
    - 1時間足 (1h)
    - 4時間足 (4h)
    - 日足 (1d)
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.yahoo_client = YahooFinanceClient()

        # リポジトリ初期化
        self.price_repo = PriceDataRepositoryImpl(session)
        self.history_repo = DataFetchHistoryRepositoryImpl(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"
        self.symbol = "USDJPY=X"

        # 時間軸設定
        self.timeframes = {
            "5m": {"interval": "5m", "minutes": 5, "description": "5分足"},
            "1h": {"interval": "1h", "minutes": 60, "description": "1時間足"},
            "4h": {"interval": "4h", "minutes": 240, "description": "4時間足"},
            "1d": {"interval": "1d", "minutes": 1440, "description": "日足"},
        }

        # 取得設定
        self.max_retries = 3
        self.retry_delay = 2.0

        logger.info(
            f"Initialized MultiTimeframeDataFetcherService for {self.currency_pair}"
        )

    async def fetch_all_timeframes(self) -> Dict[str, Optional[PriceDataModel]]:
        """
        全時間軸のデータを取得

        Returns:
            Dict[str, Optional[PriceDataModel]]: 各時間軸の最新データ
        """
        results = {}

        for timeframe, config in self.timeframes.items():
            try:
                logger.info(f"Fetching {config['description']} data...")
                data = await self.fetch_timeframe_data(timeframe)
                results[timeframe] = data

                if data:
                    logger.info(f"Successfully fetched {config['description']} data")
                else:
                    logger.warning(f"Failed to fetch {config['description']} data")

            except Exception as e:
                logger.error(f"Error fetching {config['description']} data: {e}")
                results[timeframe] = None

        return results

    async def fetch_timeframe_data(self, timeframe: str) -> Optional[PriceDataModel]:
        """
        特定時間軸のデータを取得

        Args:
            timeframe: 時間軸（5m, 1h, 4h, 1d）

        Returns:
            Optional[PriceDataModel]: 取得したデータ
        """
        if timeframe not in self.timeframes:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None

        config = self.timeframes[timeframe]
        start_time = datetime.now()

        try:
            logger.info(
                f"Fetching {config['description']} data for {self.currency_pair}"
            )

            # 最新データの取得
            if timeframe == "5m":
                # 5分足は現在価格を取得
                ticker_data = await self.yahoo_client.get_current_rate(
                    self.currency_pair
                )
                if not ticker_data:
                    raise ValueError("Failed to fetch current price data")

                price_data = self._normalize_ticker_data(ticker_data, timeframe)
            else:
                # その他の時間軸は履歴データを取得
                # Yahoo Financeクライアントは期間ベースで取得
                period_map = {
                    "1h": "7d",  # 1時間足は過去7日分
                    "4h": "30d",  # 4時間足は過去30日分
                    "1d": "1y",  # 日足は過去1年分
                }

                period = period_map.get(timeframe, "7d")
                historical_data = await self.yahoo_client.get_historical_data(
                    self.currency_pair, period=period, interval=config["interval"]
                )

                if historical_data is None or historical_data.empty:
                    raise ValueError(
                        f"Failed to fetch {config['description']} historical data"
                    )

                # 最新のデータを取得
                latest_row = historical_data.iloc[-1]
                price_data = self._normalize_dataframe_row(latest_row, timeframe)

            if not price_data:
                raise ValueError(f"Failed to normalize {config['description']} data")

            # 重複チェック
            existing_data = await self.price_repo.find_by_timestamp(
                price_data.timestamp, self.currency_pair
            )
            if existing_data:
                logger.info(
                    f"{config['description']} data already exists for {price_data.timestamp}"
                )
                return existing_data

            # データを保存
            saved_data = await self.price_repo.save(price_data)

            # 取得履歴を記録
            response_time = datetime.now() - start_time
            await self._record_fetch_history(
                "success", response_time, 1, timeframe=timeframe
            )

            logger.info(f"Successfully saved {config['description']} data")
            return saved_data

        except Exception as e:
            logger.error(f"Error fetching {config['description']} data: {e}")

            # エラー履歴を記録
            response_time = datetime.now() - start_time
            await self._record_fetch_history(
                "error", response_time, 0, str(e), timeframe=timeframe
            )

            return None

    async def fetch_historical_data_for_timeframe(
        self, timeframe: str, start_date: datetime, end_date: datetime
    ) -> List[PriceDataModel]:
        """
        特定時間軸の履歴データを取得

        Args:
            timeframe: 時間軸
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            List[PriceDataModel]: 取得したデータリスト
        """
        if timeframe not in self.timeframes:
            logger.error(f"Invalid timeframe: {timeframe}")
            return []

        config = self.timeframes[timeframe]

        try:
            logger.info(
                f"Fetching {config['description']} historical data from {start_date} to {end_date}"
            )

            # Yahoo Financeから履歴データを取得
            # 期間を計算（最大2年分）
            days_diff = (end_date - start_date).days
            if days_diff <= 30:
                period = "30d"
            elif days_diff <= 90:
                period = "90d"
            elif days_diff <= 180:
                period = "180d"
            else:
                period = "730d"  # 2年分

            historical_data = await self.yahoo_client.get_historical_data(
                self.currency_pair, period=period, interval=config["interval"]
            )

            if historical_data is None or historical_data.empty:
                logger.warning(f"No {config['description']} historical data found")
                return []

            # データを正規化して保存
            saved_data = []
            for _, row in historical_data.iterrows():
                price_data = self._normalize_dataframe_row(row, timeframe)
                if price_data:
                    # 重複チェック
                    existing_data = await self.price_repo.find_by_timestamp(
                        price_data.timestamp, self.currency_pair
                    )
                    if not existing_data:
                        saved_data.append(await self.price_repo.save(price_data))

            logger.info(
                f"Successfully saved {len(saved_data)} {config['description']} historical data points"
            )
            return saved_data

        except Exception as e:
            logger.error(f"Error fetching {config['description']} historical data: {e}")
            return []

    def _normalize_ticker_data(
        self, ticker_data: Dict, timeframe: str = "5m"
    ) -> Optional[PriceDataModel]:
        """
        ティッカーデータを正規化
        """
        try:
            # 現在時刻を取得（時間軸に合わせて調整）
            now = datetime.now()
            adjusted_timestamp = self._adjust_timestamp_for_timeframe(now, timeframe)

            return PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=adjusted_timestamp,
                open_price=ticker_data.get("previous_close", 0.0),  # 前日終値をオープン価格として使用
                high_price=ticker_data.get("day_high", 0.0),
                low_price=ticker_data.get("day_low", 0.0),
                close_price=ticker_data.get("rate", 0.0),  # 現在価格をクローズ価格として使用
                volume=1000000,  # デフォルトボリューム
                data_source="Yahoo Finance",
            )

        except Exception as e:
            logger.error(f"Error normalizing ticker data: {e}")
            return None

    def _normalize_dataframe_row(
        self, row: pd.Series, timeframe: str = "5m"
    ) -> Optional[PriceDataModel]:
        """
        DataFrame行を正規化
        """
        try:
            # タイムスタンプを時間軸に合わせて調整
            timestamp = pd.to_datetime(row.name)
            adjusted_timestamp = self._adjust_timestamp_for_timeframe(
                timestamp, timeframe
            )

            return PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=adjusted_timestamp,
                open_price=float(row.get("Open", 0.0)),
                high_price=float(row.get("High", 0.0)),
                low_price=float(row.get("Low", 0.0)),
                close_price=float(row.get("Close", 0.0)),
                volume=int(row.get("Volume", 0)),
                data_source="Yahoo Finance",
            )

        except Exception as e:
            logger.error(f"Error normalizing dataframe row: {e}")
            return None

    def _adjust_timestamp_for_timeframe(
        self, timestamp: datetime, timeframe: str
    ) -> datetime:
        """
        タイムスタンプを時間軸に合わせて調整
        """
        if timeframe == "5m":
            # 5分単位に調整
            minutes = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "1h":
            # 1時間単位に調整
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif timeframe == "4h":
            # 4時間単位に調整
            hour = (timestamp.hour // 4) * 4
            return timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)
        elif timeframe == "1d":
            # 日単位に調整
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp

    async def _record_fetch_history(
        self,
        status: str,
        response_time: timedelta,
        records_fetched: int,
        error_message: Optional[str] = None,
        timeframe: str = "5m",
    ) -> Optional[DataFetchHistoryModel]:
        """
        取得履歴を記録
        """
        try:
            history = DataFetchHistoryModel(
                currency_pair=self.currency_pair,
                fetch_timestamp=datetime.now(),
                data_source="Yahoo Finance",
                fetch_type=f"{self.timeframes[timeframe]['description']}",
                success=status == "success",
                response_time_ms=int(response_time.total_seconds() * 1000),
                http_status_code=200 if status == "success" else 500,
                data_count=records_fetched,
                cache_used=False,
            )

            return await self.history_repo.save(history)

        except Exception as e:
            logger.error(f"Error recording fetch history: {e}")
            return None

    async def get_latest_data_by_timeframe(
        self, timeframe: str, limit: int = 1
    ) -> List[PriceDataModel]:
        """
        特定時間軸の最新データを取得
        """
        if timeframe not in self.timeframes:
            logger.error(f"Invalid timeframe: {timeframe}")
            return []

        try:
            # 最新のデータを取得
            latest_data = await self.price_repo.find_latest_by_timeframe(
                self.currency_pair, timeframe, limit
            )
            return latest_data

        except Exception as e:
            logger.error(f"Error getting latest {timeframe} data: {e}")
            return []

    async def test_connection(self) -> bool:
        """
        接続テスト
        """
        try:
            # 5分足データで接続テスト
            test_data = await self.yahoo_client.get_current_rate(self.currency_pair)
            return test_data is not None
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
