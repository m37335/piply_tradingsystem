"""
Notification History Repository Interface
通知履歴リポジトリインターフェース

設計書参照:
- api_optimization_design_2025.md

通知履歴のリポジトリインターフェース
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.notification_history import NotificationHistory


class NotificationHistoryRepository(ABC):
    """
    通知履歴リポジトリインターフェース

    責任:
    - 通知履歴の永続化
    - 重複通知の防止
    - DiscordメッセージIDの管理
    - 通知状態の追跡
    """

    @abstractmethod
    async def find_recent_by_pattern(
        self, pattern_type: str, currency_pair: str, hours: int = 1
    ) -> List[NotificationHistory]:
        """
        最近の通知をパターンタイプと通貨ペアで検索

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            hours: 何時間以内の通知を検索するか

        Returns:
            List[NotificationHistory]: 最近の通知のリスト
        """
        pass

    @abstractmethod
    async def find_by_discord_message_id(
        self, message_id: str
    ) -> Optional[NotificationHistory]:
        """
        DiscordメッセージIDによる検索

        Args:
            message_id: DiscordメッセージID

        Returns:
            Optional[NotificationHistory]: 見つかった通知、存在しない場合None
        """
        pass

    @abstractmethod
    async def find_by_status(self, status: str) -> List[NotificationHistory]:
        """
        ステータスによる検索

        Args:
            status: 通知ステータス

        Returns:
            List[NotificationHistory]: 指定されたステータスの通知リスト
        """
        pass

    @abstractmethod
    async def save(
        self, notification_history: NotificationHistory
    ) -> NotificationHistory:
        """
        通知履歴を保存

        Args:
            notification_history: 保存する通知履歴

        Returns:
            NotificationHistory: 保存された通知履歴
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        notification_id: int,
        status: str,
        discord_message_id: Optional[str] = None,
    ) -> bool:
        """
        通知ステータスを更新

        Args:
            notification_id: 通知ID
            status: 新しいステータス
            discord_message_id: DiscordメッセージID（オプション）

        Returns:
            bool: 更新成功の場合True
        """
        pass

    @abstractmethod
    async def check_duplicate_notification(
        self, pattern_type: str, currency_pair: str, time_window_minutes: int = 30
    ) -> bool:
        """
        重複通知をチェック

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            time_window_minutes: 時間窓（分）

        Returns:
            bool: 重複がある場合True
        """
        pass

    @abstractmethod
    async def get_notification_statistics(self, hours: int = 24) -> dict:
        """
        通知統計を取得

        Args:
            hours: 何時間分の統計を取得するか

        Returns:
            dict: 通知統計情報
        """
        pass

    @abstractmethod
    async def cleanup_old_notifications(self, older_than_days: int = 30) -> int:
        """
        古い通知履歴を削除

        Args:
            older_than_days: 何日以上古いものを削除するか

        Returns:
            int: 削除された件数
        """
        pass

    @abstractmethod
    async def find_failed_notifications(self) -> List[NotificationHistory]:
        """
        失敗した通知を検索

        Returns:
            List[NotificationHistory]: 失敗した通知のリスト
        """
        pass

    @abstractmethod
    async def retry_failed_notifications(self) -> int:
        """
        失敗した通知を再試行

        Returns:
            int: 再試行された件数
        """
        pass
