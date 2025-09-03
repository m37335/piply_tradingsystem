"""
AIレポートSQLリポジトリ
AIレポートデータのCRUD操作を担当
"""

import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, asc, desc, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.domain.entities.ai_report import AIReport, ReportType
from src.domain.repositories.ai_report_repository import AIReportRepository
from src.infrastructure.config.database import ConnectionManager
from src.infrastructure.database.models.ai_report import AIReportMapper, AIReportModel


class SQLAIReportRepository(AIReportRepository):
    """AIレポートSQLリポジトリ実装"""

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.mapper = AIReportMapper()
        self.logger = logging.getLogger(self.__class__.__name__)

    async def save(self, report: AIReport) -> AIReport:
        """
        AIレポートを保存

        Args:
            report: 保存するAIレポート

        Returns:
            AIReport: 保存されたAIレポート
        """
        try:
            with self.connection_manager.get_session() as session:
                if report.id is None:
                    # 新規作成
                    model = self.mapper.create_model_from_entity(report)
                    session.add(model)
                    session.flush()  # IDを取得するためにflush

                    # エンティティにIDを設定
                    report.id = model.id
                    self.logger.info(f"Created new AI report: {report.id}")
                else:
                    # 更新
                    model = (
                        session.query(AIReportModel)
                        .filter(AIReportModel.id == report.id)
                        .first()
                    )

                    if not model:
                        raise ValueError(f"AI report with ID {report.id} not found")

                    self.mapper.update_model_from_entity(model, report)
                    self.logger.info(f"Updated AI report: {report.id}")

                session.commit()
                return self.mapper.to_domain(model)

        except SQLAlchemyError as e:
            self.logger.error(f"Database error saving AI report: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error saving AI report: {e}")
            raise

    async def find_by_id(self, report_id: int) -> Optional[AIReport]:
        """
        IDでAIレポートを検索

        Args:
            report_id: レポートID

        Returns:
            Optional[AIReport]: 見つかったAIレポート
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(AIReportModel)
                    .filter(AIReportModel.id == report_id)
                    .first()
                )

                return self.mapper.to_domain(model) if model else None

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding AI report by ID: {e}")
            raise

    async def find_by_event_id(
        self, event_id: int, report_type: Optional[ReportType] = None
    ) -> List[AIReport]:
        """
        経済イベントIDでAIレポートを検索

        Args:
            event_id: 経済イベントID
            report_type: レポートタイプフィルター

        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(AIReportModel).filter(
                    AIReportModel.event_id == event_id
                )

                # レポートタイプフィルター
                if report_type:
                    query = query.filter(AIReportModel.report_type == report_type.value)

                # 生成日時の降順でソート
                query = query.order_by(desc(AIReportModel.generated_at))

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding AI reports by event ID: {e}")
            raise

    async def find_by_date_range(
        self,
        start_date: date,
        end_date: date,
        report_type: Optional[ReportType] = None,
        min_confidence: Optional[float] = None,
    ) -> List[AIReport]:
        """
        日付範囲でAIレポートを検索

        Args:
            start_date: 開始日
            end_date: 終了日
            report_type: レポートタイプフィルター
            min_confidence: 最小信頼度スコア

        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(AIReportModel).filter(
                    and_(
                        AIReportModel.generated_at >= start_date,
                        AIReportModel.generated_at <= end_date,
                    )
                )

                # レポートタイプフィルター
                if report_type:
                    query = query.filter(AIReportModel.report_type == report_type.value)

                # 信頼度フィルター
                if min_confidence is not None:
                    query = query.filter(
                        AIReportModel.confidence_score >= min_confidence
                    )

                # 生成日時の降順でソート
                query = query.order_by(desc(AIReportModel.generated_at))

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding AI reports by date range: {e}")
            raise

    async def find_recent_reports(
        self,
        limit: int = 50,
        report_type: Optional[ReportType] = None,
        min_confidence: Optional[float] = None,
    ) -> List[AIReport]:
        """
        最近のAIレポートを検索

        Args:
            limit: 取得件数上限
            report_type: レポートタイプフィルター
            min_confidence: 最小信頼度スコア

        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(AIReportModel)

                # レポートタイプフィルター
                if report_type:
                    query = query.filter(AIReportModel.report_type == report_type.value)

                # 信頼度フィルター
                if min_confidence is not None:
                    query = query.filter(
                        AIReportModel.confidence_score >= min_confidence
                    )

                # 生成日時の降順でソート
                query = query.order_by(desc(AIReportModel.generated_at))
                query = query.limit(limit)

                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding recent AI reports: {e}")
            raise

    async def find_high_confidence_reports(
        self, min_confidence: float = 0.7, limit: int = 50
    ) -> List[AIReport]:
        """
        高信頼度のAIレポートを検索

        Args:
            min_confidence: 最小信頼度スコア
            limit: 取得件数上限

        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        try:
            with self.connection_manager.get_session() as session:
                query = (
                    session.query(AIReportModel)
                    .filter(AIReportModel.confidence_score >= min_confidence)
                    .order_by(desc(AIReportModel.confidence_score))
                )

                query = query.limit(limit)
                models = query.all()
                return [self.mapper.to_domain(model) for model in models]

        except SQLAlchemyError as e:
            self.logger.error(f"Database error finding high confidence AI reports: {e}")
            raise

    async def delete(self, report_id: int) -> bool:
        """
        AIレポートを削除

        Args:
            report_id: 削除するレポートのID

        Returns:
            bool: 削除成功時True
        """
        try:
            with self.connection_manager.get_session() as session:
                model = (
                    session.query(AIReportModel)
                    .filter(AIReportModel.id == report_id)
                    .first()
                )

                if not model:
                    self.logger.warning(
                        f"AI report with ID {report_id} not found for deletion"
                    )
                    return False

                session.delete(model)
                session.commit()

                self.logger.info(f"Deleted AI report: {report_id}")
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting AI report: {e}")
            raise

    async def delete_by_event_id(self, event_id: int) -> int:
        """
        経済イベントIDに関連するAIレポートを全て削除

        Args:
            event_id: 経済イベントID

        Returns:
            int: 削除された件数
        """
        try:
            with self.connection_manager.get_session() as session:
                count = (
                    session.query(AIReportModel)
                    .filter(AIReportModel.event_id == event_id)
                    .count()
                )

                session.query(AIReportModel).filter(
                    AIReportModel.event_id == event_id
                ).delete()

                session.commit()

                self.logger.info(f"Deleted {count} AI reports for event {event_id}")
                return count

        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting AI reports by event ID: {e}")
            raise

    async def count_reports(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        report_type: Optional[ReportType] = None,
        min_confidence: Optional[float] = None,
    ) -> int:
        """
        条件に一致するAIレポートの件数を取得

        Args:
            start_date: 開始日
            end_date: 終了日
            report_type: レポートタイプフィルター
            min_confidence: 最小信頼度スコア

        Returns:
            int: レポート件数
        """
        try:
            with self.connection_manager.get_session() as session:
                query = session.query(AIReportModel)

                # 日付フィルター
                if start_date:
                    query = query.filter(AIReportModel.generated_at >= start_date)
                if end_date:
                    query = query.filter(AIReportModel.generated_at <= end_date)

                # レポートタイプフィルター
                if report_type:
                    query = query.filter(AIReportModel.report_type == report_type.value)

                # 信頼度フィルター
                if min_confidence is not None:
                    query = query.filter(
                        AIReportModel.confidence_score >= min_confidence
                    )

                return query.count()

        except SQLAlchemyError as e:
            self.logger.error(f"Database error counting AI reports: {e}")
            raise

    async def get_statistics(self) -> Dict[str, Any]:
        """
        AIレポートの統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            with self.connection_manager.get_session() as session:
                total_reports = session.query(AIReportModel).count()

                # レポートタイプ別の件数
                type_counts = {}
                for report_type in ReportType:
                    count = (
                        session.query(AIReportModel)
                        .filter(AIReportModel.report_type == report_type.value)
                        .count()
                    )
                    type_counts[report_type.value] = count

                # 平均信頼度スコア
                avg_confidence = (
                    session.query(AIReportModel.confidence_score)
                    .filter(AIReportModel.confidence_score.isnot(None))
                    .all()
                )

                avg_confidence_score = 0.0
                if avg_confidence:
                    scores = [float(score[0]) for score in avg_confidence]
                    avg_confidence_score = sum(scores) / len(scores)

                return {
                    "total_reports": total_reports,
                    "reports_by_type": type_counts,
                    "average_confidence_score": avg_confidence_score,
                }

        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting AI report statistics: {e}")
            raise
