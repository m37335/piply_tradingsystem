"""
経済カレンダーSQLリポジトリ
経済イベントデータのCRUD操作を担当
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.repositories.economic_calendar_repository import (
    EconomicCalendarRepository,
)
from src.infrastructure.config.database import ConnectionManager
from src.infrastructure.database.models.economic_event import (
    EconomicEventMapper,
    EconomicEventModel,
)


class SQLEconomicCalendarRepository(EconomicCalendarRepository):
    """経済カレンダーSQLリポジトリ実装"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.mapper = EconomicEventMapper()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def save(self, event: EconomicEvent) -> EconomicEvent:
        """
        経済イベントを保存

        Args:
            event: 保存する経済イベント

        Returns:
            EconomicEvent: 保存された経済イベント
        """
        try:
            with self.connection_manager.get_session() as session:
                if event.id is None:
                    # 新規作成
                    model = self.mapper.create_model_from_entity(event)
                    session.add(model)
                    session.flush()  # IDを取得するためにflush

                    # エンティティにIDを設定
                    event.id = model.id
                    self.logger.info(f"Created new economic event: {event.event_id}")
                else:
                    # 更新
                    model = (
                        session.query(EconomicEventModel)
                        .filter(EconomicEventModel.id == event.id)
                        .first()
                    )

                    if not model:
                        raise ValueError(f"Economic event with ID {event.id} not found")

                    self.mapper.update_model_from_entity(model, event)
                    self.logger.info(f"Updated economic event: {event.event_id}")

                session.commit()
                return self.mapper.to_domain(model)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error saving economic event: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error saving economic event: {e}")
            raise

    async def find_by_id(self, event_id: int) -> Optional[EconomicEvent]:
        """
        IDで経済イベントを検索

        Args:
            event_id: イベントID

        Returns:
            Optional[EconomicEvent]: 見つかった経済イベント
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(EconomicEventModel)
                    .filter(EconomicEventModel.id == event_id)
                    .first()
                )

                return self.mapper.to_domain(model) if model else None

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding economic event by ID: {e}")
            raise

    async def find_by_event_id(self, event_id: str) -> Optional[EconomicEvent]:
        """
        イベントIDで経済イベントを検索

        Args:
            event_id: イベントの一意ID

        Returns:
            Optional[EconomicEvent]: 見つかった経済イベント
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(EconomicEventModel)
                    .filter(EconomicEventModel.event_id == event_id)
                    .first()
                )

                return self.mapper.to_domain(model) if model else None

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding economic event by event_id: {e}")
            raise

    async def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None,
    ) -> List[EconomicEvent]:
        """
        日付範囲で経済イベントを検索

        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国名フィルター
            importances: 重要度フィルター

        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(EconomicEventModel).filter(
                    and_(
                        EconomicEventModel.date_utc >= start_date,
                        EconomicEventModel.date_utc <= end_date,
                    )
                )

                # 国名フィルター
                if countries:
                    query = query.filter(EconomicEventModel.country.in_(countries))

                # 重要度フィルター
                if importances:
                    importance_values = [imp.value for imp in importances]
                    query = query.filter(
                        EconomicEventModel.importance.in_(importance_values)
                    )

                # 日付順でソート
                query = query.order_by(asc(EconomicEventModel.date_utc))

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding events by date range: {e}")
            raise

    async def find_recent_events(
        self,
        limit: int = 100,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None,
    ) -> List[EconomicEvent]:
        """
        最近の経済イベントを検索

        Args:
            limit: 取得件数上限
            countries: 国名フィルター
            importances: 重要度フィルター

        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(EconomicEventModel)

                # 国名フィルター
                if countries:
                    query = query.filter(EconomicEventModel.country.in_(countries))

                # 重要度フィルター
                if importances:
                    importance_values = [imp.value for imp in importances]
                    query = query.filter(
                        EconomicEventModel.importance.in_(importance_values)
                    )

                # 作成日時の降順でソート
                query = query.order_by(desc(EconomicEventModel.created_at))
                query = query.limit(limit)

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding recent events: {e}")
            raise

    async def find_upcoming_events(
        self,
        days_ahead: int = 7,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None,
    ) -> List[EconomicEvent]:
        """
        今後の経済イベントを検索

        Args:
            days_ahead: 何日先まで検索するか
            countries: 国名フィルター
            importances: 重要度フィルター

        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        try:
            from datetime import timedelta

            start_date = date.today()
            end_date = start_date + timedelta(days=days_ahead)

            return await self.find_by_date_range(
                start_date=start_date,
                end_date=end_date,
                countries=countries,
                importances=importances,
            )

        except Exception as e:
            self.logger.error(f"Error finding upcoming events: {e}")
            raise

    async def search_events(
        self, search_term: str, limit: int = 50
    ) -> List[EconomicEvent]:
        """
        イベント名で検索

        Args:
            search_term: 検索語
            limit: 取得件数上限

        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = (
                    session.query(EconomicEventModel)
                    .filter(EconomicEventModel.event_name.ilike(f"%{search_term}%"))
                    .order_by(desc(EconomicEventModel.date_utc))
                )

                query = query.limit(limit)
                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error searching events: {e}")
            raise

    async def delete(self, event_id: int) -> bool:
        """
        経済イベントを削除

        Args:
            event_id: 削除するイベントのID

        Returns:
            bool: 削除成功時True
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(EconomicEventModel)
                    .filter(EconomicEventModel.id == event_id)
                    .first()
                )

                if not model:
                    self.logger.warning(
                        f"Economic event with ID {event_id} not found for deletion"
                    )
                    return False

                session.delete(model)
                session.commit()

                self.logger.info(f"Deleted economic event: {model.event_id}")
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting economic event: {e}")
            raise

    async def bulk_save(self, events: List[EconomicEvent]) -> List[EconomicEvent]:
        """
        経済イベントの一括保存

        Args:
            events: 保存する経済イベントのリスト

        Returns:
            List[EconomicEvent]: 保存された経済イベントのリスト
        """
        try:
            saved_events = []

            with self.connection_manager.get_session() as session:
                for event in events:
                    if event.id is None:
                        # 新規作成
                        model = self.mapper.create_model_from_entity(event)
                        session.add(model)
                    else:
                        # 更新
                        model = (
                            session.query(EconomicEventModel)
                            .filter(EconomicEventModel.id == event.id)
                            .first()
                        )

                        if model:
                            self.mapper.update_model_from_entity(model, event)
                        else:
                            # IDが指定されているが存在しない場合は新規作成
                            model = self.mapper.create_model_from_entity(event)
                            session.add(model)

                session.flush()  # 全てのIDを取得

                # 新規作成されたイベントのIDを更新
                for i, event in enumerate(events):
                    if event.id is None:
                        event.id = (
                            session.query(EconomicEventModel)
                            .filter(EconomicEventModel.event_id == event.event_id)
                            .first()
                            .id
                        )

                    saved_events.append(event)

                session.commit()
                self.logger.info(f"Bulk saved {len(events)} economic events")

                return saved_events

        except SQLAlchemyError as e:
            self.logger.error(f"Database error in bulk save: {e}")
            raise

    async def count_events(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None,
    ) -> int:
        """
        条件に一致する経済イベントの件数を取得

        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国名フィルター
            importances: 重要度フィルター

        Returns:
            int: イベント件数
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(EconomicEventModel)

                # 日付フィルター
                if start_date:
                    query = query.filter(EconomicEventModel.date_utc >= start_date)
                if end_date:
                    query = query.filter(EconomicEventModel.date_utc <= end_date)

                # 国名フィルター
                if countries:
                    query = query.filter(EconomicEventModel.country.in_(countries))

                # 重要度フィルター
                if importances:
                    importance_values = [imp.value for imp in importances]
                    query = query.filter(
                        EconomicEventModel.importance.in_(importance_values)
                    )

                return query.count()

        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting events: {e}")
            raise
