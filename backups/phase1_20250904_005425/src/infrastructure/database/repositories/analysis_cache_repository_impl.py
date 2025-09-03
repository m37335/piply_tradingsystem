"""
Analysis Cache Repository Implementation
分析キャッシュリポジトリ実装

設計書参照:
- api_optimization_design_2025.md

AnalysisCacheRepositoryの具象実装
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.analysis_cache import AnalysisCache
from ....domain.repositories.analysis_cache_repository import AnalysisCacheRepository
from ....utils.logging_config import get_infrastructure_logger
from ..models.analysis_cache_model import AnalysisCacheModel
from .base_repository_impl import BaseRepositoryImpl

logger = get_infrastructure_logger()


class AnalysisCacheRepositoryImpl(BaseRepositoryImpl, AnalysisCacheRepository):
    """
    分析キャッシュリポジトリ実装クラス

    責任:
    - 分析結果キャッシュの永続化操作
    - キャッシュキーによる高速検索
    - 有効期限管理
    - 期限切れデータの自動削除
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        super().__init__(session)
        self._session = session
        logger.debug("Initialized AnalysisCacheRepositoryImpl")

    async def find_by_cache_key(self, cache_key: str) -> Optional[AnalysisCache]:
        """
        キャッシュキーによる検索

        Args:
            cache_key: キャッシュキー

        Returns:
            Optional[AnalysisCache]: 見つかったキャッシュ、存在しない場合None
        """
        try:
            result = await self._session.execute(
                select(AnalysisCacheModel).where(
                    AnalysisCacheModel.cache_key == cache_key
                )
            )

            model = result.scalar_one_or_none()
            if model:
                entity = model.to_entity()
                logger.debug(f"Found cache by key: {cache_key}")
                return entity
            else:
                logger.debug(f"Cache not found by key: {cache_key}")
                return None

        except Exception as e:
            logger.error(f"Failed to find cache by key {cache_key}: {str(e)}")
            raise

    async def find_by_analysis_type(
        self, analysis_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> List[AnalysisCache]:
        """
        分析タイプと通貨ペアによる検索

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸（オプション）

        Returns:
            List[AnalysisCache]: 見つかったキャッシュのリスト
        """
        try:
            query = select(AnalysisCacheModel).where(
                and_(
                    AnalysisCacheModel.analysis_type == analysis_type,
                    AnalysisCacheModel.currency_pair == currency_pair,
                )
            )

            if timeframe:
                query = query.where(AnalysisCacheModel.timeframe == timeframe)

            result = await self._session.execute(query)
            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} caches for " f"{analysis_type}:{currency_pair}"
            )
            return entities

        except Exception as e:
            logger.error(
                f"Failed to find caches by type "
                f"{analysis_type}:{currency_pair}: {str(e)}"
            )
            raise

    async def find_valid_caches(
        self, analysis_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> List[AnalysisCache]:
        """
        有効なキャッシュを検索（期限切れでないもの）

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸（オプション）

        Returns:
            List[AnalysisCache]: 有効なキャッシュのリスト
        """
        try:
            query = select(AnalysisCacheModel).where(
                and_(
                    AnalysisCacheModel.analysis_type == analysis_type,
                    AnalysisCacheModel.currency_pair == currency_pair,
                    AnalysisCacheModel.expires_at > datetime.utcnow(),
                )
            )

            if timeframe:
                query = query.where(AnalysisCacheModel.timeframe == timeframe)

            result = await self._session.execute(query)
            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} valid caches for "
                f"{analysis_type}:{currency_pair}"
            )
            return entities

        except Exception as e:
            logger.error(
                f"Failed to find valid caches for "
                f"{analysis_type}:{currency_pair}: {str(e)}"
            )
            raise

    async def delete_expired(self) -> int:
        """
        期限切れのキャッシュを削除

        Returns:
            int: 削除された件数
        """
        try:
            result = await self._session.execute(
                delete(AnalysisCacheModel).where(
                    AnalysisCacheModel.expires_at <= datetime.utcnow()
                )
            )

            deleted_count = result.rowcount
            await self._session.commit()

            logger.info(f"Deleted {deleted_count} expired caches")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete expired caches: {str(e)}")
            await self._session.rollback()
            raise

    async def delete_by_cache_key(self, cache_key: str) -> bool:
        """
        キャッシュキーによる削除

        Args:
            cache_key: キャッシュキー

        Returns:
            bool: 削除成功の場合True
        """
        try:
            result = await self._session.execute(
                delete(AnalysisCacheModel).where(
                    AnalysisCacheModel.cache_key == cache_key
                )
            )

            deleted_count = result.rowcount
            await self._session.commit()

            if deleted_count > 0:
                logger.debug(f"Deleted cache by key: {cache_key}")
                return True
            else:
                logger.debug(f"Cache not found for deletion: {cache_key}")
                return False

        except Exception as e:
            logger.error(f"Failed to delete cache by key {cache_key}: {str(e)}")
            await self._session.rollback()
            raise

    async def delete_by_currency_pair(self, currency_pair: str) -> int:
        """
        通貨ペアによる削除

        Args:
            currency_pair: 通貨ペア

        Returns:
            int: 削除された件数
        """
        try:
            result = await self._session.execute(
                delete(AnalysisCacheModel).where(
                    AnalysisCacheModel.currency_pair == currency_pair
                )
            )

            deleted_count = result.rowcount
            await self._session.commit()

            logger.info(f"Deleted {deleted_count} caches for {currency_pair}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete caches for {currency_pair}: {str(e)}")
            await self._session.rollback()
            raise

    async def delete_by_analysis_type(
        self, analysis_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> int:
        """
        分析タイプと通貨ペアによる削除

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸（オプション）

        Returns:
            int: 削除された件数
        """
        try:
            query = delete(AnalysisCacheModel).where(
                and_(
                    AnalysisCacheModel.analysis_type == analysis_type,
                    AnalysisCacheModel.currency_pair == currency_pair,
                )
            )

            if timeframe:
                query = query.where(AnalysisCacheModel.timeframe == timeframe)

            result = await self._session.execute(query)
            deleted_count = result.rowcount
            await self._session.commit()

            logger.info(
                f"Deleted {deleted_count} caches for "
                f"{analysis_type}:{currency_pair}"
            )
            return deleted_count

        except Exception as e:
            logger.error(
                f"Failed to delete caches for "
                f"{analysis_type}:{currency_pair}: {str(e)}"
            )
            await self._session.rollback()
            raise

    async def get_cache_statistics(self) -> dict:
        """
        キャッシュ統計を取得

        Returns:
            dict: キャッシュ統計情報
        """
        try:
            # 総件数
            total_result = await self._session.execute(
                select(func.count(AnalysisCacheModel.id))
            )
            total_count = total_result.scalar()

            # 有効件数
            valid_result = await self._session.execute(
                select(func.count(AnalysisCacheModel.id)).where(
                    AnalysisCacheModel.expires_at > datetime.utcnow()
                )
            )
            valid_count = valid_result.scalar()

            # 期限切れ件数
            expired_count = total_count - valid_count

            # 分析タイプ別統計
            type_result = await self._session.execute(
                select(
                    AnalysisCacheModel.analysis_type, func.count(AnalysisCacheModel.id)
                ).group_by(AnalysisCacheModel.analysis_type)
            )
            type_stats = dict(type_result.all())

            statistics = {
                "total_count": total_count,
                "valid_count": valid_count,
                "expired_count": expired_count,
                "type_statistics": type_stats,
                "timestamp": datetime.utcnow().isoformat(),
            }

            logger.debug(f"Cache statistics: {statistics}")
            return statistics

        except Exception as e:
            logger.error(f"Failed to get cache statistics: {str(e)}")
            raise

    async def find_caches_expiring_soon(
        self, within_minutes: int = 30
    ) -> List[AnalysisCache]:
        """
        まもなく期限切れになるキャッシュを検索

        Args:
            within_minutes: 何分以内に期限切れになるか

        Returns:
            List[AnalysisCache]: まもなく期限切れになるキャッシュのリスト
        """
        try:
            expiry_threshold = datetime.utcnow() + timedelta(minutes=within_minutes)

            result = await self._session.execute(
                select(AnalysisCacheModel).where(
                    and_(
                        AnalysisCacheModel.expires_at <= expiry_threshold,
                        AnalysisCacheModel.expires_at > datetime.utcnow(),
                    )
                )
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} caches expiring within {within_minutes} minutes"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to find caches expiring soon: {str(e)}")
            raise

    async def cleanup_old_caches(self, older_than_hours: int = 24) -> int:
        """
        古いキャッシュを削除

        Args:
            older_than_hours: 何時間以上古いものを削除するか

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)

            result = await self._session.execute(
                delete(AnalysisCacheModel).where(
                    AnalysisCacheModel.created_at < cutoff_time
                )
            )

            deleted_count = result.rowcount
            await self._session.commit()

            logger.info(
                f"Deleted {deleted_count} old caches (older than {older_than_hours} hours)"
            )
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old caches: {str(e)}")
            await self._session.rollback()
            raise
