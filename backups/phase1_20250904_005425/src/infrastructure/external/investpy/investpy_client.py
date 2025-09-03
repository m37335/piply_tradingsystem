"""
investpyクライアント
investpyライブラリを使用した経済カレンダーデータ取得クライアント
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import investpy
import pandas as pd

from .investpy_error_handler import InvestpyErrorHandler
from .investpy_rate_limiter import InvestpyRateLimiter


class InvestpyClient:
    """investpyクライアント"""

    def __init__(
        self,
        error_handler: Optional[InvestpyErrorHandler] = None,
        rate_limiter: Optional[InvestpyRateLimiter] = None,
    ):
        self.error_handler = error_handler or InvestpyErrorHandler()
        self.rate_limiter = rate_limiter or InvestpyRateLimiter()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def get_economic_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        経済カレンダーデータを取得

        Args:
            from_date: 開始日（DD/MM/YYYY形式）
            to_date: 終了日（DD/MM/YYYY形式）
            countries: 国名リスト
            importances: 重要度リスト

        Returns:
            pd.DataFrame: 経済カレンダーデータ
        """
        try:
            # レート制限チェック
            await self.rate_limiter.wait_if_needed()

            # デフォルト値の設定
            if not from_date:
                from_date = datetime.now().strftime("%d/%m/%Y")
            if not to_date:
                to_date = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
            if not countries:
                countries = ["japan", "united states", "euro zone"]
            if not importances:
                importances = ["high", "medium"]

            self.logger.info(
                f"Fetching economic calendar from {from_date} to {to_date} "
                f"for countries: {countries}"
            )

            # investpyを使用してデータ取得
            df = investpy.economic_calendar(
                from_date=from_date,
                to_date=to_date,
                countries=countries,
                importances=importances,
            )

            self.logger.info(f"Successfully fetched {len(df)} economic events")

            # データの正規化
            df = self._normalize_dataframe(df)

            return df

        except Exception as e:
            self.logger.error(f"Error fetching economic calendar: {e}")
            self.error_handler.handle_error(e)
            raise

    async def get_today_events(
        self, countries: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        今日のイベントを取得

        Args:
            countries: 国名リスト

        Returns:
            pd.DataFrame: 今日の経済イベント
        """
        today = datetime.now().strftime("%d/%m/%Y")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
        return await self.get_economic_calendar(
            from_date=today, to_date=tomorrow, countries=countries
        )

    async def get_weekly_events(
        self, start_date: Optional[str] = None, countries: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        週間イベントを取得

        Args:
            start_date: 開始日（DD/MM/YYYY形式）
            countries: 国名リスト

        Returns:
            pd.DataFrame: 週間経済イベント
        """
        if not start_date:
            start_date = datetime.now().strftime("%d/%m/%Y")

        end_date = (
            datetime.strptime(start_date, "%d/%m/%Y") + timedelta(days=7)
        ).strftime("%d/%m/%Y")

        return await self.get_economic_calendar(
            from_date=start_date, to_date=end_date, countries=countries
        )

    async def get_available_countries(self) -> List[str]:
        """
        利用可能な国名リストを取得

        Returns:
            List[str]: 利用可能な国名リスト
        """
        try:
            await self.rate_limiter.wait_if_needed()

            countries = investpy.economic_calendar_countries()
            self.logger.info(f"Available countries: {countries}")

            return countries

        except Exception as e:
            self.logger.error(f"Error fetching available countries: {e}")
            self.error_handler.handle_error(e)
            raise

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        DataFrameの正規化

        Args:
            df: 正規化対象のDataFrame

        Returns:
            pd.DataFrame: 正規化されたDataFrame
        """
        if df.empty:
            return df

        # 列名の正規化
        column_mapping = {
            "Date": "Date",
            "Time": "Time",
            "Country": "Country",
            "Zone": "Zone",
            "Event": "Event",
            "Importance": "Importance",
            "Actual": "Actual",
            "Forecast": "Forecast",
            "Previous": "Previous",
            "Currency": "Currency",
            "Unit": "Unit",
        }

        # 存在する列のみマッピング
        existing_columns = {col: col for col in df.columns if col in column_mapping}
        df = df.rename(columns=existing_columns)

        # データ型の変換
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")

        if "Time" in df.columns:
            df["Time"] = pd.to_datetime(
                df["Time"], format="%H:%M", errors="coerce"
            ).dt.time

        # 重要度の正規化
        if "Importance" in df.columns:
            df["Importance"] = df["Importance"].str.lower()

        # 数値列の変換
        numeric_columns = ["Actual", "Forecast", "Previous"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        # 欠損値の処理
        df = df.fillna("")

        return df

    async def test_connection(self) -> bool:
        """
        接続テスト

        Returns:
            bool: 接続成功時True
        """
        try:
            await self.rate_limiter.wait_if_needed()

            # 簡単なデータ取得でテスト
            today = datetime.now().strftime("%d/%m/%Y")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
            investpy.economic_calendar(
                from_date=today,
                to_date=tomorrow,
                countries=["japan"],
                importances=["high"],
            )

            self.logger.info("Connection test successful")
            return True

        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            self.error_handler.handle_error(e)
            return False

    async def get_connection_stats(self) -> Dict[str, Any]:
        """
        接続統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            "client": "InvestpyClient",
            "rate_limiter_stats": self.rate_limiter.get_stats(),
            "error_handler_stats": self.error_handler.get_error_summary(),
            "last_connection_test": getattr(self, "_last_test_time", None),
            "total_requests": getattr(self, "_total_requests", 0),
            "successful_requests": getattr(self, "_successful_requests", 0),
        }

    def get_dataframe_info(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        DataFrameの情報を取得

        Args:
            df: 対象のDataFrame

        Returns:
            Dict[str, Any]: DataFrameの情報
        """
        if df.empty:
            return {
                "row_count": 0,
                "column_count": 0,
                "columns": [],
                "countries": [],
                "importances": [],
            }

        info = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "countries": (
                df["Country"].unique().tolist() if "Country" in df.columns else []
            ),
            "importances": (
                df["Importance"].unique().tolist() if "Importance" in df.columns else []
            ),
        }

        return info
