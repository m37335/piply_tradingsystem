"""
Notification History Repository Implementation
通知履歴リポジトリ実装

設計書参照:
- api_optimization_design_2025.md

NotificationHistoryRepositoryの具象実装
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.notification_history import NotificationHistory
from ....domain.repositories.notification_history_repository import (
    NotificationHistoryRepository,
)
from ....utils.logging_config import get_infrastructure_logger
from ..models.notification_history_model import NotificationHistoryModel
from .base_repository_impl import BaseRepositoryImpl

logger = get_infrastructure_logger()


class NotificationHistoryRepositoryImpl(
    BaseRepositoryImpl, NotificationHistoryRepository
):
    """
    通知履歴リポジトリ実装クラス

    責任:
    - 通知履歴の永続化操作
    - 重複通知の防止
    - DiscordメッセージIDの管理
    - 通知状態の追跡
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        super().__init__(session)
        self._session = session
        logger.debug("Initialized NotificationHistoryRepositoryImpl")

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
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await self._session.execute(
                select(NotificationHistoryModel)
                .where(
                    and_(
                        NotificationHistoryModel.pattern_type == pattern_type,
                        NotificationHistoryModel.currency_pair == currency_pair,
                        NotificationHistoryModel.sent_at >= cutoff_time,
                    )
                )
                .order_by(NotificationHistoryModel.sent_at.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} recent notifications for "
                f"{pattern_type}:{currency_pair}"
            )
            return entities

        except Exception as e:
            logger.error(
                f"Failed to find recent notifications for "
                f"{pattern_type}:{currency_pair}: {str(e)}"
            )
            raise

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
        try:
            result = await self._session.execute(
                select(NotificationHistoryModel).where(
                    NotificationHistoryModel.discord_message_id == message_id
                )
            )

            model = result.scalar_one_or_none()
            if model:
                entity = model.to_entity()
                logger.debug(f"Found notification by Discord message ID: {message_id}")
                return entity
            else:
                logger.debug(
                    f"Notification not found by Discord message ID: {message_id}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to find notification by Discord message ID "
                f"{message_id}: {str(e)}"
            )
            raise

    async def find_by_status(self, status: str) -> List[NotificationHistory]:
        """
        ステータスによる検索

        Args:
            status: 通知ステータス

        Returns:
            List[NotificationHistory]: 指定されたステータスの通知リスト
        """
        try:
            result = await self._session.execute(
                select(NotificationHistoryModel)
                .where(NotificationHistoryModel.status == status)
                .order_by(NotificationHistoryModel.sent_at.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} notifications with status: {status}")
            return entities

        except Exception as e:
            logger.error(f"Failed to find notifications by status {status}: {str(e)}")
            raise

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
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow(),
            }

            if discord_message_id:
                update_data["discord_message_id"] = discord_message_id

            result = await self._session.execute(
                update(NotificationHistoryModel)
                .where(NotificationHistoryModel.id == notification_id)
                .values(**update_data)
            )

            updated_count = result.rowcount
            await self._session.commit()

            if updated_count > 0:
                logger.debug(
                    f"Updated notification {notification_id} status to: {status}"
                )
                return True
            else:
                logger.debug(f"Notification {notification_id} not found for update")
                return False

        except Exception as e:
            logger.error(
                f"Failed to update notification {notification_id} status: {str(e)}"
            )
            await self._session.rollback()
            raise

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
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=time_window_minutes)

            result = await self._session.execute(
                select(func.count(NotificationHistoryModel.id)).where(
                    and_(
                        NotificationHistoryModel.pattern_type == pattern_type,
                        NotificationHistoryModel.currency_pair == currency_pair,
                        NotificationHistoryModel.sent_at >= cutoff_time,
                        NotificationHistoryModel.status == "sent",
                    )
                )
            )

            count = result.scalar()
            is_duplicate = count > 0

            logger.debug(
                f"Duplicate check for {pattern_type}:{currency_pair} "
                f"within {time_window_minutes} minutes: {is_duplicate}"
            )
            return is_duplicate

        except Exception as e:
            logger.error(
                f"Failed to check duplicate notification for "
                f"{pattern_type}:{currency_pair}: {str(e)}"
            )
            raise

    async def get_notification_statistics(self, hours: int = 24) -> dict:
        """
        通知統計を取得

        Args:
            hours: 何時間分の統計を取得するか

        Returns:
            dict: 通知統計情報
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # 総件数
            total_result = await self._session.execute(
                select(func.count(NotificationHistoryModel.id)).where(
                    NotificationHistoryModel.sent_at >= cutoff_time
                )
            )
            total_count = total_result.scalar()

            # ステータス別統計
            status_result = await self._session.execute(
                select(
                    NotificationHistoryModel.status,
                    func.count(NotificationHistoryModel.id),
                )
                .where(NotificationHistoryModel.sent_at >= cutoff_time)
                .group_by(NotificationHistoryModel.status)
            )
            status_stats = dict(status_result.all())

            # パターンタイプ別統計
            pattern_result = await self._session.execute(
                select(
                    NotificationHistoryModel.pattern_type,
                    func.count(NotificationHistoryModel.id),
                )
                .where(NotificationHistoryModel.sent_at >= cutoff_time)
                .group_by(NotificationHistoryModel.pattern_type)
            )
            pattern_stats = dict(pattern_result.all())

            statistics = {
                "total_notifications": total_count,
                "status_breakdown": status_stats,
                "pattern_breakdown": pattern_stats,
                "time_period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.debug(f"Notification statistics: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"Failed to get notification statistics: {str(e)}")
            raise

    async def get_statistics(self, hours: int = 24) -> dict:
        """
        通知統計を取得（エイリアスメソッド）

        Args:
            hours: 何時間分の統計を取得するか

        Returns:
            dict: 通知統計情報
        """
        return await self.get_notification_statistics(hours)

    async def cleanup_old_notifications(self, older_than_days: int = 30) -> int:
        """
        古い通知履歴を削除

        Args:
            older_than_days: 何日以上古いものを削除するか

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)

            result = await self._session.execute(
                delete(NotificationHistoryModel).where(
                    NotificationHistoryModel.sent_at < cutoff_time
                )
            )

            deleted_count = result.rowcount
            await self._session.commit()

            logger.info(
                f"Deleted {deleted_count} old notifications "
                f"(older than {older_than_days} days)"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {str(e)}")
            await self._session.rollback()
            raise

    async def find_failed_notifications(self) -> List[NotificationHistory]:
        """
        失敗した通知を検索

        Returns:
            List[NotificationHistory]: 失敗した通知のリスト
        """
        try:
            result = await self._session.execute(
                select(NotificationHistoryModel)
                .where(NotificationHistoryModel.status == "failed")
                .order_by(NotificationHistoryModel.sent_at.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} failed notifications")
            return entities

        except Exception as e:
            logger.error(f"Failed to find failed notifications: {str(e)}")
            raise

    async def retry_failed_notifications(self) -> int:
        """
        失敗した通知を再試行

        Returns:
            int: 再試行された件数
        """
        try:
            result = await self._session.execute(
                update(NotificationHistoryModel)
                .where(NotificationHistoryModel.status == "failed")
                .values(status="pending", updated_at=datetime.utcnow())
            )

            retry_count = result.rowcount
            await self._session.commit()

            logger.info(f"Retried {retry_count} failed notifications")
            return retry_count

        except Exception as e:
            logger.error(f"Failed to retry failed notifications: {str(e)}")
            await self._session.rollback()
            raise
