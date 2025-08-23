"""
通知ログSQLリポジトリ
通知ログデータのCRUD操作を担当
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities.notification_history import NotificationHistory
from src.infrastructure.config.database import ConnectionManager
from src.infrastructure.database.models.notification_log import (
    NotificationLogMapper,
    NotificationLogModel,
    NotificationStatus,
    NotificationType,
)


class SQLNotificationLogRepository:
    """通知ログSQLリポジトリ実装"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.mapper = NotificationLogMapper()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def save(self, log: NotificationHistory) -> NotificationHistory:
        """
        通知ログを保存

        Args:
            log: 保存する通知ログ

        Returns:
            NotificationLog: 保存された通知ログ
        """
        try:
            with self.connection_manager.get_session() as session:
                if log.id is None:
                    # 新規作成
                    model = self.mapper.create_model_from_domain(log)
                    session.add(model)
                    session.flush()  # IDを取得するためにflush

                    # ドメインオブジェクトにIDを設定
                    log.id = model.id
                    self.logger.info(f"Created new notification log: {log.id}")
                else:
                    # 更新
                    model = (
                        session.query(NotificationLogModel)
                        .filter(NotificationLogModel.id == log.id)
                        .first()
                    )

                    if not model:
                        raise ValueError(f"Notification log with ID {log.id} not found")

                    self.mapper.update_model_from_domain(model, log)
                    self.logger.info(f"Updated notification log: {log.id}")

                session.commit()
                return self.mapper.to_domain(model)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error saving notification log: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error saving notification log: {e}")
            raise

    async def find_by_id(self, log_id: int) -> Optional[NotificationHistory]:
        """
        IDで通知ログを検索

        Args:
            log_id: ログID

        Returns:
            Optional[NotificationLog]: 見つかった通知ログ
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(NotificationLogModel)
                    .filter(NotificationLogModel.id == log_id)
                    .first()
                )

                return self.mapper.to_domain(model) if model else None

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding notification log by ID: {e}")
            raise

    async def find_by_event_id(
        self, event_id: int, notification_type: Optional[NotificationType] = None
    ) -> List[NotificationHistory]:
        """
        経済イベントIDで通知ログを検索

        Args:
            event_id: 経済イベントID
            notification_type: 通知タイプフィルター

        Returns:
            List[NotificationLog]: 見つかった通知ログのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(NotificationLogModel).filter(
                    NotificationLogModel.event_id == event_id
                )

                # 通知タイプフィルター
                if notification_type:
                    query = query.filter(
                        NotificationLogModel.notification_type
                        == notification_type.value
                    )

                # 作成日時の降順でソート
                query = query.order_by(desc(NotificationLogModel.created_at))

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error finding notification logs by event ID: {e}"
            )
            raise

    async def find_by_status(
        self, status: NotificationStatus, limit: int = 100
    ) -> List[NotificationHistory]:
        """
        ステータスで通知ログを検索

        Args:
            status: 通知ステータス
            limit: 取得件数上限

        Returns:
            List[NotificationLog]: 見つかった通知ログのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = (
                    session.query(NotificationLogModel)
                    .filter(NotificationLogModel.status == status.value)
                    .order_by(desc(NotificationLogModel.created_at))
                )

                query = query.limit(limit)
                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error finding notification logs by status: {e}"
            )
            raise

    async def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        notification_type: Optional[NotificationType] = None,
        status: Optional[NotificationStatus] = None,
    ) -> List[NotificationHistory]:
        """
        日付範囲で通知ログを検索

        Args:
            start_date: 開始日
            end_date: 終了日
            notification_type: 通知タイプフィルター
            status: ステータスフィルター

        Returns:
            List[NotificationHistory]: 見つかった通知ログのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(NotificationLogModel).filter(
                    and_(
                        NotificationLogModel.created_at >= start_date,
                        NotificationLogModel.created_at <= end_date,
                    )
                )

                # 通知タイプフィルター
                if notification_type:
                    query = query.filter(
                        NotificationLogModel.notification_type
                        == notification_type.value
                    )

                # ステータスフィルター
                if status:
                    query = query.filter(NotificationLogModel.status == status.value)

                # 作成日時の降順でソート
                query = query.order_by(desc(NotificationLogModel.created_at))

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error finding notification logs by date range: {e}"
            )
            raise

    async def find_recent_logs(
        self,
        limit: int = 100,
        notification_type: Optional[NotificationType] = None,
        status: Optional[NotificationStatus] = None,
    ) -> List[NotificationHistory]:
        """
        最近の通知ログを検索

        Args:
            limit: 取得件数上限
            notification_type: 通知タイプフィルター
            status: ステータスフィルター

        Returns:
            List[NotificationHistory]: 見つかった通知ログのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(NotificationLogModel)

                # 通知タイプフィルター
                if notification_type:
                    query = query.filter(
                        NotificationLogModel.notification_type
                        == notification_type.value
                    )

                # ステータスフィルター
                if status:
                    query = query.filter(NotificationLogModel.status == status.value)

                # 作成日時の降順でソート
                query = query.order_by(desc(NotificationLogModel.created_at))
                query = query.limit(limit)

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding recent notification logs: {e}")
            raise

    async def find_failed_notifications(
        self, hours_back: int = 24, limit: int = 50
    ) -> List[NotificationHistory]:
        """
        失敗した通知ログを検索

        Args:
            hours_back: 何時間前からの失敗を検索するか
            limit: 取得件数上限

        Returns:
            List[NotificationHistory]: 見つかった失敗通知ログのリスト
        """
        try:
            from datetime import timedelta

            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)

            with self.connection_manager.get_session() as session:
                query = (
                    session.query(NotificationLogModel)
                    .filter(
                        and_(
                            NotificationLogModel.status
                            == NotificationStatus.FAILED.value,
                            NotificationLogModel.created_at >= cutoff_time,
                        )
                    )
                    .order_by(desc(NotificationLogModel.created_at))
                )

                query = query.limit(limit)
                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding failed notifications: {e}")
            raise

    async def delete(self, log_id: int) -> bool:
        """
        通知ログを削除

        Args:
            log_id: 削除するログのID

        Returns:
            bool: 削除成功時True
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(NotificationLogModel)
                    .filter(NotificationLogModel.id == log_id)
                    .first()
                )

                if not model:
                    self.logger.warning(
                        f"Notification log with ID {log_id} not found for deletion"
                    )
                    return False

                session.delete(model)
                session.commit()

                self.logger.info(f"Deleted notification log: {log_id}")
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting notification log: {e}")
            raise

    async def delete_old_logs(self, days_old: int = 30) -> int:
        """
        古い通知ログを削除

        Args:
            days_old: 何日前より古いログを削除するか

        Returns:
            int: 削除された件数
        """
        try:
            from datetime import timedelta

            cutoff_date = date.today() - timedelta(days=days_old)

            with self.connection_manager.get_session() as session:
                count = (
                    session.query(NotificationLogModel)
                    .filter(NotificationLogModel.created_at < cutoff_date)
                    .count()
                )

                session.query(NotificationLogModel).filter(
                    NotificationLogModel.created_at < cutoff_date
                ).delete()

                session.commit()

                self.logger.info(
                    f"Deleted {count} old notification logs (older than {days_old} days)"
                )
                return count

        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting old notification logs: {e}")
            raise

    async def count_logs(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        notification_type: Optional[NotificationType] = None,
        status: Optional[NotificationStatus] = None,
    ) -> int:
        """
        条件に一致する通知ログの件数を取得

        Args:
            start_date: 開始日
            end_date: 終了日
            notification_type: 通知タイプフィルター
            status: ステータスフィルター

        Returns:
            int: ログ件数
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(NotificationLogModel)

                # 日付フィルター
                if start_date:
                    query = query.filter(NotificationLogModel.created_at >= start_date)
                if end_date:
                    query = query.filter(NotificationLogModel.created_at <= end_date)

                # 通知タイプフィルター
                if notification_type:
                    query = query.filter(
                        NotificationLogModel.notification_type
                        == notification_type.value
                    )

                # ステータスフィルター
                if status:
                    query = query.filter(NotificationLogModel.status == status.value)

                return query.count()

        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting notification logs: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        通知ログの統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            with self.connection_manager.get_session() as session:
                total_logs = session.query(NotificationLogModel).count()

                # ステータス別の件数
                status_counts = {}
                for status in NotificationStatus:
                    count = (
                        session.query(NotificationLogModel)
                        .filter(NotificationLogModel.status == status.value)
                        .count()
                    )
                    status_counts[status.value] = count

                # 通知タイプ別の件数
                type_counts = {}
                for notification_type in NotificationType:
                    count = (
                        session.query(NotificationLogModel)
                        .filter(
                            NotificationLogModel.notification_type
                            == notification_type.value
                        )
                        .count()
                    )
                    type_counts[notification_type.value] = count

                # 成功率
                success_rate = 0.0
                if total_logs > 0:
                    success_count = status_counts.get(NotificationStatus.SENT.value, 0)
                    success_rate = success_count / total_logs

                return {
                    "total_logs": total_logs,
                    "logs_by_status": status_counts,
                    "logs_by_type": type_counts,
                    "success_rate": success_rate,
                }

        except SQLAlchemyError as e:
            self.logger.error(
                f"Database error getting notification log statistics: {e}"
            )
            raise
