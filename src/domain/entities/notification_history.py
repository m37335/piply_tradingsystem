"""
Notification History Domain Entity
通知履歴ドメインエンティティ

設計書参照:
- api_optimization_design_2025.md

通知履歴用ドメインエンティティ
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ...utils.logging_config import get_domain_logger
from .base import BaseEntity

logger = get_domain_logger()


class NotificationHistory(BaseEntity):
    """
    通知履歴エンティティ

    責任:
    - 通知履歴の管理
    - 重複通知の防止
    - DiscordメッセージIDの管理
    - 通知状態の追跡

    特徴:
    - 不変性: 一度作成された履歴は変更不可
    - 一意性: パターンタイプと通貨ペアの組み合わせ
    - 時系列: 送信時刻による時系列管理
    """

    def __init__(
        self,
        pattern_type: str,
        currency_pair: str,
        notification_data: Dict[str, Any],
        sent_at: datetime,
        status: str = "sent",
        discord_message_id: Optional[str] = None,
        id: Optional[int] = None,
        uuid: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: int = 1,
    ):
        """
        初期化

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            notification_data: 通知データ
            sent_at: 送信時刻
            status: 通知ステータス
            discord_message_id: DiscordメッセージID
            id: データベースID
            uuid: UUID
            created_at: 作成時刻
            updated_at: 更新時刻
            version: バージョン
        """
        super().__init__(
            id=id,
            uuid=uuid,
            created_at=created_at,
            updated_at=updated_at,
            version=version,
        )

        self.pattern_type = pattern_type
        self.currency_pair = currency_pair
        self.notification_data = notification_data
        self.sent_at = sent_at
        self.status = status
        self.discord_message_id = discord_message_id

        logger.debug(f"Created NotificationHistory entity: {self.pattern_type}")

    def is_recent_notification(self, time_window_minutes: int = 30) -> bool:
        """
        最近の通知かどうかを判定

        Args:
            time_window_minutes: 時間窓（分）

        Returns:
            bool: 最近の通知の場合True
        """
        time_diff = datetime.utcnow() - self.sent_at
        return time_diff.total_seconds() < (time_window_minutes * 60)

    def is_successful(self) -> bool:
        """
        成功した通知かどうかを判定

        Returns:
            bool: 成功した通知の場合True
        """
        return self.status == "sent"

    def is_failed(self) -> bool:
        """
        失敗した通知かどうかを判定

        Returns:
            bool: 失敗した通知の場合True
        """
        return self.status == "failed"

    def get_notification_summary(self) -> Dict[str, str]:
        """
        通知サマリーを取得

        Returns:
            Dict[str, str]: 通知サマリー
        """
        return {
            "pattern_type": self.pattern_type,
            "currency_pair": self.currency_pair,
            "sent_at": self.sent_at.isoformat(),
            "status": self.status,
            "discord_message_id": self.discord_message_id or "N/A",
            "is_recent": str(self.is_recent_notification()),
            "is_successful": str(self.is_successful()),
        }

    def get_unique_key(self) -> str:
        """
        一意キーを取得（重複チェック用）

        Returns:
            str: 一意キー
        """
        return f"{self.pattern_type}:{self.currency_pair}"

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換

        Returns:
            Dict[str, Any]: エンティティの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "pattern_type": self.pattern_type,
                "currency_pair": self.currency_pair,
                "notification_data": self.notification_data,
                "sent_at": self.sent_at.isoformat() if self.sent_at else None,
                "status": self.status,
                "discord_message_id": self.discord_message_id,
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationHistory":
        """
        辞書からエンティティを復元

        Args:
            data: エンティティデータの辞書

        Returns:
            NotificationHistory: 復元されたエンティティインスタンス
        """
        # 日時文字列をdatetimeオブジェクトに変換
        sent_at = None
        if data.get("sent_at"):
            sent_at = datetime.fromisoformat(data["sent_at"])

        return cls(
            id=data.get("id"),
            uuid=data.get("uuid"),
            pattern_type=data["pattern_type"],
            currency_pair=data["currency_pair"],
            notification_data=data["notification_data"],
            sent_at=sent_at,
            status=data.get("status", "sent"),
            discord_message_id=data.get("discord_message_id"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
            version=data.get("version", 1),
        )

    def __repr__(self) -> str:
        """
        文字列表現

        Returns:
            str: エンティティの文字列表現
        """
        return (
            f"NotificationHistory("
            f"id={self.id}, "
            f"pattern_type='{self.pattern_type}', "
            f"currency_pair='{self.currency_pair}', "
            f"sent_at='{self.sent_at}', "
            f"status='{self.status}'"
            f")"
        )
