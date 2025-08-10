"""
テクニカル指標リポジトリインターフェース

USD/JPY特化の5分おきデータ取得システム用のテクニカル指標リポジトリ
設計書参照: /app/note/database_implementation_design_2025.md
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)


class TechnicalIndicatorRepository(ABC):
    """
    テクニカル指標リポジトリインターフェース

    責任:
    - テクニカル指標の永続化
    - テクニカル指標の取得・検索
    - 複数タイムフレーム対応
    - 指標計算結果の管理

    特徴:
    - USD/JPY特化設計
    - 複数タイムフレーム対応
    - 高パフォーマンスクエリ
    - 指標別管理
    """

    @abstractmethod
    async def save(self, indicator: TechnicalIndicatorModel) -> TechnicalIndicatorModel:
        """
        テクニカル指標を保存

        Args:
            indicator: 保存するテクニカル指標

        Returns:
            TechnicalIndicatorModel: 保存されたテクニカル指標
        """
        pass

    @abstractmethod
    async def save_batch(
        self, indicator_list: List[TechnicalIndicatorModel]
    ) -> List[TechnicalIndicatorModel]:
        """
        テクニカル指標をバッチ保存

        Args:
            indicator_list: 保存するテクニカル指標リスト

        Returns:
            List[TechnicalIndicatorModel]: 保存されたテクニカル指標リスト
        """
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[TechnicalIndicatorModel]:
        """
        IDでテクニカル指標を取得

        Args:
            id: テクニカル指標ID

        Returns:
            Optional[TechnicalIndicatorModel]: テクニカル指標（存在しない場合はNone）
        """
        pass

    @abstractmethod
    async def find_by_timestamp_and_type(
        self,
        timestamp: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
    ) -> Optional[TechnicalIndicatorModel]:
        """
        タイムスタンプ・指標タイプ・タイムフレームでテクニカル指標を取得

        Args:
            timestamp: タイムスタンプ
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            Optional[TechnicalIndicatorModel]: テクニカル指標（存在しない場合はNone）
        """
        pass

    @abstractmethod
    async def find_latest_by_type(
        self,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
        limit: int = 1,
    ) -> List[TechnicalIndicatorModel]:
        """
        指標タイプ・タイムフレームで最新のテクニカル指標を取得

        Args:
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[TechnicalIndicatorModel]: 最新のテクニカル指標リスト
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        日付範囲でテクニカル指標を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        pass

    @abstractmethod
    async def find_by_value_range(
        self,
        min_value: float,
        max_value: float,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        値範囲でテクニカル指標を取得

        Args:
            min_value: 最小値
            max_value: 最大値
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        pass

    @abstractmethod
    async def find_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
        interval_minutes: int = 5,
    ) -> List[datetime]:
        """
        欠損データのタイムスタンプを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            interval_minutes: 間隔（分）（デフォルト: 5）

        Returns:
            List[datetime]: 欠損データのタイムスタンプリスト
        """
        pass

    @abstractmethod
    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータ数を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: データ数
        """
        pass

    @abstractmethod
    async def get_indicator_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
    ) -> dict:
        """
        指標統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            dict: 統計情報（最小値、最大値、平均値等）
        """
        pass

    @abstractmethod
    async def delete_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータを削除

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        pass

    @abstractmethod
    async def delete_old_data(
        self,
        days_to_keep: int = 365,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        pass

    @abstractmethod
    async def exists_by_timestamp_and_type(
        self,
        timestamp: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
    ) -> bool:
        """
        タイムスタンプ・指標タイプ・タイムフレームのデータが存在するかチェック

        Args:
            timestamp: タイムスタンプ
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            bool: 存在する場合True
        """
        pass

    @abstractmethod
    async def get_indicator_types(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        指標タイプ一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: 指標タイプ一覧
        """
        pass

    @abstractmethod
    async def get_timeframes(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        タイムフレーム一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: タイムフレーム一覧
        """
        pass

    @abstractmethod
    async def find_by_indicator_type(
        self,
        indicator_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        指標タイプでテクニカル指標を取得

        Args:
            indicator_type: 指標タイプ
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        pass

    @abstractmethod
    async def find_by_timeframe(
        self,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        indicator_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        タイムフレームでテクニカル指標を取得

        Args:
            timeframe: タイムフレーム
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            indicator_type: 指標タイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        pass
