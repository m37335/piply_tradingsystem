"""
API Call History Repository Implementation
API呼び出し履歴リポジトリ実装

設計書参照:
- api_optimization_design_2025.md

ApiCallHistoryRepositoryの具象実装
"""

from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.api_call_history import ApiCallHistory
from ....domain.repositories.api_call_history_repository import ApiCallHistoryRepository
from ....utils.logging_config import get_infrastructure_logger
from ..models.api_call_history_model import ApiCallHistoryModel
from .base_repository_impl import BaseRepositoryImpl

logger = get_infrastructure_logger()


class ApiCallHistoryRepositoryImpl(BaseRepositoryImpl, ApiCallHistoryRepository):
    """
    API呼び出し履歴リポジトリ実装クラス

    責任:
    - API呼び出し履歴の永続化操作
    - レート制限監視
    - パフォーマンス測定
    - エラー追跡
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        super().__init__(session)
        self._session = session
        logger.debug("Initialized ApiCallHistoryRepositoryImpl")

    async def find_recent_calls(
        self, api_name: str, minutes: int = 60
    ) -> List[ApiCallHistory]:
        """
        最近のAPI呼び出しを検索

        Args:
            api_name: API名
            minutes: 何分以内の呼び出しを検索するか

        Returns:
            List[ApiCallHistory]: 最近のAPI呼び出しのリスト
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

            result = await self._session.execute(
                select(ApiCallHistoryModel)
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                    )
                )
                .order_by(ApiCallHistoryModel.called_at.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} recent calls for {api_name}")
            return entities

        except Exception as e:
            logger.error(f"Failed to find recent calls for {api_name}: {str(e)}")
            raise

    async def get_call_statistics(
        self, api_name: str, hours: int = 24
    ) -> Dict[str, any]:
        """
        API呼び出し統計を取得

        Args:
            api_name: API名
            hours: 何時間分の統計を取得するか

        Returns:
            Dict[str, any]: API呼び出し統計情報
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # 総件数
            total_result = await self._session.execute(
                select(func.count(ApiCallHistoryModel.id)).where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                    )
                )
            )
            total_count = total_result.scalar()

            # 成功件数
            success_result = await self._session.execute(
                select(func.count(ApiCallHistoryModel.id)).where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.success.is_(True),
                    )
                )
            )
            success_count = success_result.scalar()

            # 失敗件数
            failed_count = total_count - success_count

            # 平均レスポンス時間
            avg_response_result = await self._session.execute(
                select(func.avg(ApiCallHistoryModel.response_time_ms)).where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.response_time_ms.isnot(None),
                    )
                )
            )
            avg_response_time = avg_response_result.scalar()

            # ステータスコード別統計
            status_result = await self._session.execute(
                select(
                    ApiCallHistoryModel.status_code,
                    func.count(ApiCallHistoryModel.id),
                )
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                    )
                )
                .group_by(ApiCallHistoryModel.status_code)
            )
            status_stats = dict(status_result.all())

            statistics = {
                "api_name": api_name,
                "total_count": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "success_rate": (
                    (success_count / total_count * 100) if total_count > 0 else 0
                ),
                "avg_response_time_ms": (
                    float(avg_response_time) if avg_response_time else None
                ),
                "status_code_statistics": status_stats,
                "time_period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.debug(f"API call statistics for {api_name}: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"Failed to get call statistics for {api_name}: {str(e)}")
            raise

    async def find_rate_limit_errors(
        self, api_name: str, hours: int = 24
    ) -> List[ApiCallHistory]:
        """
        レート制限エラーを検索

        Args:
            api_name: API名
            hours: 何時間分を検索するか

        Returns:
            List[ApiCallHistory]: レート制限エラーのリスト
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await self._session.execute(
                select(ApiCallHistoryModel)
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.status_code == 429,
                    )
                )
                .order_by(ApiCallHistoryModel.called_at.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} rate limit errors for {api_name}")
            return entities

        except Exception as e:
            logger.error(f"Failed to find rate limit errors for {api_name}: {str(e)}")
            raise

    async def find_slow_responses(
        self, api_name: str, threshold_ms: int = 5000, hours: int = 24
    ) -> List[ApiCallHistory]:
        """
        遅いレスポンスを検索

        Args:
            api_name: API名
            threshold_ms: 閾値（ミリ秒）
            hours: 何時間分を検索するか

        Returns:
            List[ApiCallHistory]: 遅いレスポンスのリスト
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await self._session.execute(
                select(ApiCallHistoryModel)
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.response_time_ms > threshold_ms,
                    )
                )
                .order_by(ApiCallHistoryModel.response_time_ms.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} slow responses for {api_name} "
                f"(threshold: {threshold_ms}ms)"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to find slow responses for {api_name}: {str(e)}")
            raise

    async def get_performance_summary(
        self, api_name: str, hours: int = 24
    ) -> Dict[str, any]:
        """
        パフォーマンスサマリーを取得

        Args:
            api_name: API名
            hours: 何時間分のサマリーを取得するか

        Returns:
            Dict[str, any]: パフォーマンスサマリー
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # レスポンス時間統計
            response_stats = await self._session.execute(
                select(
                    func.min(ApiCallHistoryModel.response_time_ms).label("min"),
                    func.max(ApiCallHistoryModel.response_time_ms).label("max"),
                    func.avg(ApiCallHistoryModel.response_time_ms).label("avg"),
                    func.percentile_cont(0.95)
                    .within_group(ApiCallHistoryModel.response_time_ms.desc())
                    .label("p95"),
                ).where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.response_time_ms.isnot(None),
                        ApiCallHistoryModel.success == True,
                    )
                )
            )
            response_data = response_stats.first()

            # パフォーマンスカテゴリ別統計
            performance_result = await self._session.execute(
                select(
                    func.case(
                        [
                            (ApiCallHistoryModel.response_time_ms < 1000, "fast"),
                            (ApiCallHistoryModel.response_time_ms < 5000, "normal"),
                        ],
                        else_="slow",
                    ).label("category"),
                    func.count(ApiCallHistoryModel.id),
                )
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.success == True,
                    )
                )
                .group_by("category")
            )
            performance_stats = dict(performance_result.all())

            summary = {
                "api_name": api_name,
                "response_time_stats": {
                    "min_ms": float(response_data.min) if response_data.min else None,
                    "max_ms": float(response_data.max) if response_data.max else None,
                    "avg_ms": float(response_data.avg) if response_data.avg else None,
                    "p95_ms": float(response_data.p95) if response_data.p95 else None,
                },
                "performance_categories": performance_stats,
                "time_period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.debug(f"Performance summary for {api_name}: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Failed to get performance summary for {api_name}: {str(e)}")
            raise

    async def cleanup_old_calls(self, older_than_days: int = 7) -> int:
        """
        古いAPI呼び出し履歴を削除

        Args:
            older_than_days: 何日以上古いものを削除するか

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)

            result = await self._session.execute(
                delete(ApiCallHistoryModel).where(
                    ApiCallHistoryModel.called_at < cutoff_time
                )
            )

            deleted_count = result.rowcount
            await self._session.commit()

            logger.info(
                f"Deleted {deleted_count} old API calls "
                f"(older than {older_than_days} days)"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old API calls: {str(e)}")
            await self._session.rollback()
            raise

    async def find_failed_calls(
        self, api_name: str, hours: int = 24
    ) -> List[ApiCallHistory]:
        """
        失敗したAPI呼び出しを検索

        Args:
            api_name: API名
            hours: 何時間分を検索するか

        Returns:
            List[ApiCallHistory]: 失敗したAPI呼び出しのリスト
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            result = await self._session.execute(
                select(ApiCallHistoryModel)
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.success == False,
                    )
                )
                .order_by(ApiCallHistoryModel.called_at.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} failed calls for {api_name}")
            return entities

        except Exception as e:
            logger.error(f"Failed to find failed calls for {api_name}: {str(e)}")
            raise

    async def get_error_summary(self, api_name: str, hours: int = 24) -> Dict[str, any]:
        """
        エラーサマリーを取得

        Args:
            api_name: API名
            hours: 何時間分のサマリーを取得するか

        Returns:
            Dict[str, any]: エラーサマリー
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            # エラータイプ別統計
            error_result = await self._session.execute(
                select(
                    ApiCallHistoryModel.status_code,
                    func.count(ApiCallHistoryModel.id),
                )
                .where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.success == False,
                    )
                )
                .group_by(ApiCallHistoryModel.status_code)
            )
            error_stats = dict(error_result.all())

            # レート制限エラー数
            rate_limit_result = await self._session.execute(
                select(func.count(ApiCallHistoryModel.id)).where(
                    and_(
                        ApiCallHistoryModel.api_name == api_name,
                        ApiCallHistoryModel.called_at >= cutoff_time,
                        ApiCallHistoryModel.status_code == 429,
                    )
                )
            )
            rate_limit_count = rate_limit_result.scalar()

            summary = {
                "api_name": api_name,
                "error_statistics": error_stats,
                "rate_limit_errors": rate_limit_count,
                "time_period_hours": hours,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.debug(f"Error summary for {api_name}: {summary}")
            return summary

        except Exception as e:
            logger.error(f"Failed to get error summary for {api_name}: {str(e)}")
            raise
