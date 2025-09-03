"""
価格データリポジトリインターフェース

USD/JPY特化の5分おきデータ取得システム用の価格データリポジトリ
設計書参照: /app/note/database_implementation_design_2025.md
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.infrastructure.database.models.price_data_model import PriceDataModel


class PriceDataRepository(ABC):
    """
    価格データリポジトリインターフェース

    責任:
    - 価格データの永続化
    - 価格データの取得・検索
    - バッチ処理
    - データクリーンアップ

    特徴:
    - USD/JPY特化設計
    - 5分間隔データ対応
    - 高パフォーマンスクエリ
    - バッチ処理最適化
    """

    @abstractmethod
    async def save(self, price_data: PriceDataModel) -> PriceDataModel:
        """
        価格データを保存

        Args:
            price_data: 保存する価格データ

        Returns:
            PriceDataModel: 保存された価格データ
        """
        pass

    @abstractmethod
    async def save_batch(
        self, price_data_list: List[PriceDataModel]
    ) -> List[PriceDataModel]:
        """
        価格データをバッチ保存

        Args:
            price_data_list: 保存する価格データリスト

        Returns:
            List[PriceDataModel]: 保存された価格データリスト
        """
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[PriceDataModel]:
        """
        IDで価格データを取得

        Args:
            id: 価格データID

        Returns:
            Optional[PriceDataModel]: 価格データ（存在しない場合はNone）
        """
        pass

    @abstractmethod
    async def find_by_timestamp(
        self, timestamp: datetime, currency_pair: str = "USD/JPY"
    ) -> Optional[PriceDataModel]:
        """
        タイムスタンプで価格データを取得

        Args:
            timestamp: タイムスタンプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            Optional[PriceDataModel]: 価格データ（存在しない場合はNone）
        """
        pass

    @abstractmethod
    async def find_latest(
        self, currency_pair: str = "USD/JPY", limit: int = 1
    ) -> List[PriceDataModel]:
        """
        最新の価格データを取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[PriceDataModel]: 最新の価格データリスト
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        日付範囲で価格データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        pass

    @abstractmethod
    async def find_by_price_range(
        self,
        min_price: float,
        max_price: float,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        価格範囲で価格データを取得

        Args:
            min_price: 最小価格
            max_price: 最大価格
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        pass

    @abstractmethod
    async def find_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
        interval_minutes: int = 5,
    ) -> List[datetime]:
        """
        欠損データのタイムスタンプを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
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
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータ数を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: データ数
        """
        pass

    @abstractmethod
    async def get_price_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
    ) -> dict:
        """
        価格統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
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
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータを削除

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        pass

    @abstractmethod
    async def delete_old_data(
        self, days_to_keep: int = 365, currency_pair: str = "USD/JPY"
    ) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        pass

    @abstractmethod
    async def exists_by_timestamp(
        self, timestamp: datetime, currency_pair: str = "USD/JPY"
    ) -> bool:
        """
        タイムスタンプのデータが存在するかチェック

        Args:
            timestamp: タイムスタンプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            bool: 存在する場合True
        """
        pass

    @abstractmethod
    async def get_data_sources(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        データソース一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: データソース一覧
        """
        pass

    @abstractmethod
    async def find_by_data_source(
        self,
        data_source: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        データソースで価格データを取得

        Args:
            data_source: データソース
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        pass
