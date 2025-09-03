"""
Exchange Rate Repository Interface
為替レートリポジトリインターフェース

設計書参照:
- 詳細内部設計_20250809.md

為替レートエンティティに特化したリポジトリインターフェース
"""

from abc import abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..entities.exchange_rate import ExchangeRateEntity
from ..value_objects.currency import CurrencyPair, Price
from .base import BaseRepository


class ExchangeRateRepository(BaseRepository[ExchangeRateEntity]):
    """
    為替レートリポジトリインターフェース

    責任:
    - 為替レートデータの永続化
    - 通貨ペア・時系列による検索
    - レート履歴の管理
    """

    @abstractmethod
    async def find_by_currency_pair(
        self, currency_pair: CurrencyPair, limit: int = 100
    ) -> List[ExchangeRateEntity]:
        """
        通貨ペアによる為替レート検索

        Args:
            currency_pair: 検索する通貨ペア
            limit: 最大取得件数

        Returns:
            List[ExchangeRateEntity]: 通貨ペアの為替レートリスト（新しい順）
        """
        pass

    @abstractmethod
    async def find_latest_by_currency_pair(
        self, currency_pair: CurrencyPair
    ) -> Optional[ExchangeRateEntity]:
        """
        通貨ペアの最新為替レート取得

        Args:
            currency_pair: 検索する通貨ペア

        Returns:
            Optional[ExchangeRateEntity]: 最新の為替レート、存在しない場合None
        """
        pass

    @abstractmethod
    async def find_by_time_range(
        self, currency_pair: CurrencyPair, start_time: datetime, end_time: datetime
    ) -> List[ExchangeRateEntity]:
        """
        期間による為替レート検索

        Args:
            currency_pair: 検索する通貨ペア
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            List[ExchangeRateEntity]: 期間内の為替レートリスト
        """
        pass

    @abstractmethod
    async def find_by_source(
        self, source: str, limit: int = 100
    ) -> List[ExchangeRateEntity]:
        """
        データソースによる為替レート検索

        Args:
            source: データソース名
            limit: 最大取得件数

        Returns:
            List[ExchangeRateEntity]: 指定ソースの為替レートリスト
        """
        pass

    @abstractmethod
    async def find_stale_rates(
        self, max_age_minutes: int = 5
    ) -> List[ExchangeRateEntity]:
        """
        古い為替レートデータの検索

        Args:
            max_age_minutes: 古いと判定する時間（分）

        Returns:
            List[ExchangeRateEntity]: 古い為替レートのリスト
        """
        pass

    @abstractmethod
    async def get_rate_statistics(
        self, currency_pair: CurrencyPair, start_time: datetime, end_time: datetime
    ) -> Dict[str, float]:
        """
        期間の為替レート統計情報を取得

        Args:
            currency_pair: 統計を取得する通貨ペア
            start_time: 開始時刻
            end_time: 終了時刻

        Returns:
            Dict[str, float]: 統計情報（min, max, avg, count等）
        """
        pass

    @abstractmethod
    async def delete_old_rates(self, before_date: datetime) -> int:
        """
        指定日時より古い為替レートデータを削除

        Args:
            before_date: この日時より古いデータを削除

        Returns:
            int: 削除されたレコード数
        """
        pass

    @abstractmethod
    async def bulk_save(
        self, rates: List[ExchangeRateEntity]
    ) -> List[ExchangeRateEntity]:
        """
        為替レートの一括保存

        Args:
            rates: 保存する為替レートのリスト

        Returns:
            List[ExchangeRateEntity]: 保存された為替レートのリスト
        """
        pass

    @abstractmethod
    async def find_latest_rates_for_pairs(
        self, currency_pairs: List[CurrencyPair]
    ) -> Dict[str, ExchangeRateEntity]:
        """
        複数通貨ペアの最新レートを一括取得

        Args:
            currency_pairs: 取得したい通貨ペアのリスト

        Returns:
            Dict[str, ExchangeRateEntity]: 通貨ペア文字列をキーとした最新レートの辞書
        """
        pass

    @abstractmethod
    async def find_rates_above_threshold(
        self, currency_pair: CurrencyPair, threshold: Price, since: datetime
    ) -> List[ExchangeRateEntity]:
        """
        閾値を上回る為替レートを検索

        Args:
            currency_pair: 検索する通貨ペア
            threshold: 閾値価格
            since: この時刻以降のデータを検索

        Returns:
            List[ExchangeRateEntity]: 閾値を上回る為替レートのリスト
        """
        pass

    @abstractmethod
    async def find_rates_below_threshold(
        self, currency_pair: CurrencyPair, threshold: Price, since: datetime
    ) -> List[ExchangeRateEntity]:
        """
        閾値を下回る為替レートを検索

        Args:
            currency_pair: 検索する通貨ペア
            threshold: 閾値価格
            since: この時刻以降のデータを検索

        Returns:
            List[ExchangeRateEntity]: 閾値を下回る為替レートのリスト
        """
        pass
