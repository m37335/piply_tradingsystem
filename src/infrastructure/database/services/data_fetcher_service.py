"""
データ取得サービス

USD/JPY特化の5分おきデータ取得システム用のデータ取得サービス
設計書参照: /app/note/database_implementation_design_2025.md
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


class DataFetcherService:
    """
    USD/JPY特化データ取得サービス

    責任:
    - USD/JPYの5分間隔データ取得
    - データの正規化と保存
    - エラーハンドリングとリトライ
    - 取得履歴の管理

    特徴:
    - USD/JPY特化設計
    - 5分間隔データ取得
    - 重複データ防止
    - 包括的エラーハンドリング
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session
        self.yahoo_client = YahooFinanceClient()

        # リポジトリ初期化
        self.price_repo = PriceDataRepositoryImpl(session)
        self.history_repo = DataFetchHistoryRepositoryImpl(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"
        self.symbol = "USDJPY=X"

        # 取得設定
        self.interval_minutes = 5
        self.max_retries = 3
        self.retry_delay = 2.0

        logger.info(f"Initialized DataFetcherService for {self.currency_pair}")

    async def fetch_current_price_data(self) -> Optional[PriceDataModel]:
        """
        現在の価格データを取得

        Returns:
            Optional[PriceDataModel]: 取得した価格データ（失敗時はNone）
        """
        start_time = datetime.now()

        try:
            logger.info(f"Fetching current price data for {self.currency_pair}")

            # Yahoo Financeからデータ取得
            ticker_data = await self.yahoo_client.get_current_rate(self.currency_pair)
            if not ticker_data:
                raise ValueError("Failed to fetch ticker data from Yahoo Finance")

            # データの正規化
            price_data = self._normalize_ticker_data(ticker_data)
            if not price_data:
                raise ValueError("Failed to normalize ticker data")

            # 重複チェック
            existing_data = await self.price_repo.find_by_timestamp(
                price_data.timestamp, self.currency_pair
            )
            if existing_data:
                logger.info(f"Price data already exists for {price_data.timestamp}")
                return existing_data

            # データベースに保存
            saved_data = await self.price_repo.save(price_data)

            # 取得履歴を記録
            await self._record_fetch_history("success", datetime.now() - start_time, 1)

            logger.info(
                f"Successfully fetched and saved price data: "
                f"Close={saved_data.close_price}, Volume={saved_data.volume}"
            )
            return saved_data

        except Exception as e:
            logger.error(f"Error fetching current price data: {e}")

            # エラー履歴を記録
            await self._record_fetch_history(
                "error", datetime.now() - start_time, 0, str(e)
            )
            return None

    async def fetch_historical_data(
        self, start_date: datetime, end_date: datetime, interval: str = "5m"
    ) -> List[PriceDataModel]:
        """
        履歴データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            interval: 間隔（デフォルト: 5m）

        Returns:
            List[PriceDataModel]: 取得した価格データリスト
        """
        start_time = datetime.now()

        try:
            logger.info(
                f"Fetching historical data for {self.currency_pair} "
                f"from {start_date} to {end_date}"
            )

            # Yahoo Financeから履歴データ取得
            df = await self.yahoo_client.get_historical_data(
                self.currency_pair,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
            )

            if df is None or df.empty:
                logger.warning("No historical data received from Yahoo Finance")
                return []

            # データの正規化
            price_data_list = []
            for _, row in df.iterrows():
                price_data = self._normalize_dataframe_row(row)
                if price_data:
                    price_data_list.append(price_data)

            if not price_data_list:
                logger.warning("No valid price data after normalization")
                return []

            # 重複チェックと保存
            saved_data_list = []
            for price_data in price_data_list:
                existing_data = await self.price_repo.find_by_timestamp(
                    price_data.timestamp, self.currency_pair
                )
                if not existing_data:
                    saved_data = await self.price_repo.save(price_data)
                    saved_data_list.append(saved_data)

            # 取得履歴を記録
            await self._record_fetch_history(
                "success", datetime.now() - start_time, len(saved_data_list)
            )

            logger.info(
                f"Successfully fetched and saved {len(saved_data_list)} "
                f"historical price data records"
            )
            return saved_data_list

        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")

            # エラー履歴を記録
            await self._record_fetch_history(
                "error", datetime.now() - start_time, 0, str(e)
            )
            return []

    async def fetch_missing_data(
        self, start_date: datetime, end_date: datetime, interval_minutes: int = 5
    ) -> List[PriceDataModel]:
        """
        不足データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            interval_minutes: 間隔（分）

        Returns:
            List[PriceDataModel]: 取得した価格データリスト
        """
        try:
            logger.info(
                f"Fetching missing data for {self.currency_pair} "
                f"from {start_date} to {end_date}"
            )

            # 不足データの時間を特定
            missing_times = await self.price_repo.find_missing_data(
                start_date, end_date, self.currency_pair, interval_minutes
            )

            if not missing_times:
                logger.info("No missing data found")
                return []

            logger.info(f"Found {len(missing_times)} missing data points")

            # 不足データを取得
            all_fetched_data = []
            for missing_time in missing_times:
                # 5分間隔でデータ取得
                fetch_start = missing_time - timedelta(minutes=2)
                fetch_end = missing_time + timedelta(minutes=2)

                fetched_data = await self.fetch_historical_data(
                    fetch_start, fetch_end, "5m"
                )
                all_fetched_data.extend(fetched_data)

            logger.info(
                f"Successfully fetched {len(all_fetched_data)} missing data records"
            )
            return all_fetched_data

        except Exception as e:
            logger.error(f"Error fetching missing data: {e}")
            return []

    async def get_latest_price_data(self, limit: int = 1) -> List[PriceDataModel]:
        """
        最新の価格データを取得

        Args:
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[PriceDataModel]: 最新の価格データリスト
        """
        try:
            return await self.price_repo.find_latest(self.currency_pair, limit)
        except Exception as e:
            logger.error(f"Error getting latest price data: {e}")
            return []

    async def get_price_data_by_range(
        self, start_date: datetime, end_date: datetime, limit: Optional[int] = None
    ) -> List[PriceDataModel]:
        """
        期間指定で価格データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        try:
            return await self.price_repo.find_by_date_range(
                start_date, end_date, self.currency_pair, limit
            )
        except Exception as e:
            logger.error(f"Error getting price data by range: {e}")
            return []

    async def get_fetch_statistics(
        self, start_date: datetime, end_date: datetime
    ) -> Dict:
        """
        取得統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            Dict: 統計情報
        """
        try:
            # 価格データ統計
            price_stats = await self.price_repo.get_price_statistics(
                start_date, end_date, self.currency_pair
            )

            # 取得履歴統計
            history_stats = await self.history_repo.get_fetch_statistics(
                start_date, end_date, self.currency_pair
            )

            return {
                "price_data": price_stats,
                "fetch_history": history_stats,
                "currency_pair": self.currency_pair,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }

        except Exception as e:
            logger.error(f"Error getting fetch statistics: {e}")
            return {}

    def _normalize_ticker_data(self, ticker_data: Dict) -> Optional[PriceDataModel]:
        """
        Yahoo Financeのティッカーデータを正規化

        Args:
            ticker_data: Yahoo Financeのティッカーデータ

        Returns:
            Optional[PriceDataModel]: 正規化された価格データ
        """
        try:
            # 実際のYahoo Financeクライアントのデータ形式に対応
            if "rate" in ticker_data:
                # カスタムYahoo Financeクライアントの形式
                close_price = ticker_data.get("rate", 0)
                high_price = ticker_data.get("day_high", close_price)
                low_price = ticker_data.get("day_low", close_price)
                open_price = ticker_data.get(
                    "previous_close", close_price
                )  # 前日終値をオープンとして使用
                volume = ticker_data.get("volume", 1000000)  # デフォルトボリューム

                # タイムスタンプの処理
                timestamp_str = ticker_data.get("timestamp", "")
                if timestamp_str:
                    try:
                        timestamp = datetime.strptime(
                            timestamp_str, "%Y-%m-%d %H:%M:%S JST"
                        )
                    except:
                        timestamp = datetime.now()
                else:
                    timestamp = datetime.now()
            else:
                # 標準的なYahoo Financeティッカーデータ形式
                regular_market_price = ticker_data.get("regularMarketPrice", 0)
                regular_market_high = ticker_data.get(
                    "regularMarketDayHigh", regular_market_price
                )
                regular_market_low = ticker_data.get(
                    "regularMarketDayLow", regular_market_price
                )
                regular_market_open = ticker_data.get(
                    "regularMarketOpen", regular_market_price
                )
                volume = ticker_data.get("volume", 0)
                timestamp = datetime.fromtimestamp(
                    ticker_data.get("regularMarketTime", datetime.now().timestamp())
                )

                close_price = regular_market_price
                high_price = regular_market_high
                low_price = regular_market_low
                open_price = regular_market_open

            # 価格データモデルの作成
            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
            )

            return price_data if price_data.validate() else None

        except Exception as e:
            logger.error(f"Error normalizing ticker data: {e}")
            return None

    def _normalize_dataframe_row(self, row: pd.Series) -> Optional[PriceDataModel]:
        """
        DataFrameの行を正規化

        Args:
            row: DataFrameの行

        Returns:
            Optional[PriceDataModel]: 正規化された価格データ
        """
        try:
            # インデックスをタイムスタンプとして使用
            timestamp = (
                row.name.to_pydatetime()
                if hasattr(row.name, "to_pydatetime")
                else datetime.now()
            )

            # 価格データの抽出
            open_price = row.get("Open", 0)
            high_price = row.get("High", 0)
            low_price = row.get("Low", 0)
            close_price = row.get("Close", 0)
            volume = row.get("Volume", 0)

            # 価格データモデルの作成
            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                open_price=open_price,
                high_price=high_price,
                low_price=low_price,
                close_price=close_price,
                volume=volume,
            )

            return price_data if price_data.validate() else None

        except Exception as e:
            logger.error(f"Error normalizing dataframe row: {e}")
            return None

    async def _record_fetch_history(
        self,
        status: str,
        response_time: timedelta,
        records_fetched: int,
        error_message: Optional[str] = None,
    ) -> Optional[DataFetchHistoryModel]:
        """
        取得履歴を記録

        Args:
            status: ステータス
            response_time: レスポンス時間
            records_fetched: 取得レコード数
            error_message: エラーメッセージ（デフォルト: None）

        Returns:
            Optional[DataFetchHistoryModel]: 記録された履歴
        """
        try:
            fetch_history = DataFetchHistoryModel(
                currency_pair=self.currency_pair,
                fetch_timestamp=datetime.now(),
                data_source="Yahoo Finance",
                fetch_type="price_data",
                success=status == "success",
                response_time_ms=int(response_time.total_seconds() * 1000),
                data_count=records_fetched,
                error_message=error_message,
            )

            return await self.history_repo.save(fetch_history)

        except Exception as e:
            logger.error(f"Error recording fetch history: {e}")
            return None

    async def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功の場合True
        """
        try:
            return await self.yahoo_client.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    async def cleanup_old_data(self, days_to_keep: int = 365) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）

        Returns:
            int: 削除されたデータ数
        """
        try:
            deleted_count = await self.price_repo.delete_old_data(
                days_to_keep, self.currency_pair
            )
            logger.info(f"Deleted {deleted_count} old price data records")
            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
