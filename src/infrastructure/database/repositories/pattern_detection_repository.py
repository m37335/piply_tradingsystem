"""
パターン検出リポジトリインターフェース

USD/JPY特化の5分おきデータ取得システム用のパターン検出リポジトリ
設計書参照: /app/note/database_implementation_design_2025.md
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)


class PatternDetectionRepository(ABC):
    """
    パターン検出リポジトリインターフェース

    責任:
    - パターン検出結果の永続化
    - パターン検出結果の取得・検索
    - 通知状態管理
    - 信頼度別管理

    特徴:
    - USD/JPY特化設計
    - 6パターン対応
    - 通知重複防止
    - 信頼度管理
    """

    @abstractmethod
    async def save(self, pattern: PatternDetectionModel) -> PatternDetectionModel:
        """
        パターン検出結果を保存

        Args:
            pattern: 保存するパターン検出結果

        Returns:
            PatternDetectionModel: 保存されたパターン検出結果
        """
        pass

    @abstractmethod
    async def save_batch(
        self, pattern_list: List[PatternDetectionModel]
    ) -> List[PatternDetectionModel]:
        """
        パターン検出結果をバッチ保存

        Args:
            pattern_list: 保存するパターン検出結果リスト

        Returns:
            List[PatternDetectionModel]: 保存されたパターン検出結果リスト
        """
        pass

    @abstractmethod
    async def find_by_id(self, id: int) -> Optional[PatternDetectionModel]:
        """
        IDでパターン検出結果を取得

        Args:
            id: パターン検出結果ID

        Returns:
            Optional[PatternDetectionModel]: パターン検出結果（存在しない場合はNone）
        """
        pass

    @abstractmethod
    async def find_by_timestamp_and_type(
        self,
        timestamp: datetime,
        pattern_type: str,
        currency_pair: str = "USD/JPY",
    ) -> Optional[PatternDetectionModel]:
        """
        タイムスタンプ・パターンタイプでパターン検出結果を取得

        Args:
            timestamp: タイムスタンプ
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            Optional[PatternDetectionModel]: パターン検出結果（存在しない場合はNone）
        """
        pass

    @abstractmethod
    async def find_latest_by_type(
        self,
        pattern_type: str,
        currency_pair: str = "USD/JPY",
        limit: int = 1,
    ) -> List[PatternDetectionModel]:
        """
        パターンタイプで最新のパターン検出結果を取得

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[PatternDetectionModel]: 最新のパターン検出結果リスト
        """
        pass

    @abstractmethod
    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        日付範囲でパターン検出結果を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        pass

    @abstractmethod
    async def find_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        信頼度範囲でパターン検出結果を取得

        Args:
            min_confidence: 最小信頼度
            max_confidence: 最大信頼度
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        pass

    @abstractmethod
    async def find_by_direction(
        self,
        direction: str,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        方向でパターン検出結果を取得

        Args:
            direction: 検出方向（BUY/SELL）
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        pass

    @abstractmethod
    async def find_unnotified_patterns(
        self,
        currency_pair: str = "USD/JPY",
        pattern_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        未通知のパターン検出結果を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            pattern_type: パターンタイプ（デフォルト: None）
            min_confidence: 最小信頼度（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 未通知のパターン検出結果リスト
        """
        pass

    @abstractmethod
    async def find_recent_notifications(
        self,
        hours: int = 1,
        currency_pair: str = "USD/JPY",
        pattern_type: Optional[str] = None,
    ) -> List[PatternDetectionModel]:
        """
        最近の通知済みパターンを取得（重複通知防止用）

        Args:
            hours: 時間範囲（デフォルト: 1）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            pattern_type: パターンタイプ（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 最近の通知済みパターンリスト
        """
        pass

    @abstractmethod
    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータ数を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: データ数
        """
        pass

    @abstractmethod
    async def get_pattern_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> dict:
        """
        パターン統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            dict: 統計情報（パターン別件数、平均信頼度等）
        """
        pass

    @abstractmethod
    async def delete_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータを削除

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        pass

    @abstractmethod
    async def delete_old_data(
        self,
        days_to_keep: int = 365,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        pass

    @abstractmethod
    async def exists_by_timestamp_and_type(
        self,
        timestamp: datetime,
        pattern_type: str,
        currency_pair: str = "USD/JPY",
    ) -> bool:
        """
        タイムスタンプ・パターンタイプのデータが存在するかチェック

        Args:
            timestamp: タイムスタンプ
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            bool: 存在する場合True
        """
        pass

    @abstractmethod
    async def get_pattern_types(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        パターンタイプ一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: パターンタイプ一覧
        """
        pass

    @abstractmethod
    async def find_by_pattern_type(
        self,
        pattern_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        パターンタイプでパターン検出結果を取得

        Args:
            pattern_type: パターンタイプ
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        pass

    @abstractmethod
    async def mark_notification_sent(
        self,
        pattern_id: int,
        message: Optional[str] = None,
    ) -> bool:
        """
        通知送信済みとしてマーク

        Args:
            pattern_id: パターン検出結果ID
            message: 通知メッセージ（デフォルト: None）

        Returns:
            bool: 更新成功の場合True
        """
        pass

    @abstractmethod
    async def get_high_confidence_patterns(
        self,
        min_confidence: float = 70.0,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        高信頼度パターンを取得

        Args:
            min_confidence: 最小信頼度（デフォルト: 70.0）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 高信頼度パターンリスト
        """
        pass
