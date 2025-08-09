"""
Exchange Rate Repository Implementation
為替レートリポジトリ実装

設計書参照:
- インフラ・プラグイン設計_20250809.md

ExchangeRateRepositoryの具象実装
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.exchange_rate import ExchangeRateEntity
from ....domain.repositories.exchange_rate_repository import ExchangeRateRepository
from ....domain.value_objects.currency import CurrencyPair, Price
from ....utils.logging_config import get_infrastructure_logger
from ..models.exchange_rate_model import ExchangeRateModel
from .base_repository import BaseRepositoryImpl

logger = get_infrastructure_logger()


class ExchangeRateRepositoryImpl(
    BaseRepositoryImpl[ExchangeRateEntity], ExchangeRateRepository
):
    """
    為替レートリポジトリ実装クラス

    責任:
    - 為替レートデータの永続化操作
    - 複雑な検索条件の実装
    - パフォーマンス最適化
    - データ整合性の保証
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        super().__init__(session, ExchangeRateModel, ExchangeRateEntity)
        logger.debug("Initialized ExchangeRateRepositoryImpl")

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
        try:
            pair_str = str(currency_pair)

            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(ExchangeRateModel.currency_pair == pair_str)
                .order_by(ExchangeRateModel.timestamp.desc())
                .limit(limit)
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} rates for currency pair {pair_str}")
            return entities

        except Exception as e:
            logger.error(
                f"Failed to find rates by currency pair {currency_pair}: {str(e)}"
            )
            raise

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
        try:
            pair_str = str(currency_pair)

            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(ExchangeRateModel.currency_pair == pair_str)
                .order_by(ExchangeRateModel.timestamp.desc())
                .limit(1)
            )

            model = result.scalar_one_or_none()

            if model:
                entity = model.to_entity()
                logger.debug(f"Found latest rate for {pair_str}: {entity.rate}")
                return entity
            else:
                logger.debug(f"No latest rate found for {pair_str}")
                return None

        except Exception as e:
            logger.error(f"Failed to find latest rate for {currency_pair}: {str(e)}")
            raise

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
        try:
            pair_str = str(currency_pair)

            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(
                    and_(
                        ExchangeRateModel.currency_pair == pair_str,
                        ExchangeRateModel.timestamp >= start_time,
                        ExchangeRateModel.timestamp <= end_time,
                    )
                )
                .order_by(ExchangeRateModel.timestamp.asc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} rates for {pair_str} "
                f"between {start_time} and {end_time}"
            )
            return entities

        except Exception as e:
            logger.error(
                f"Failed to find rates by time range for {currency_pair}: {str(e)}"
            )
            raise

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
        try:
            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(ExchangeRateModel.source == source)
                .order_by(ExchangeRateModel.timestamp.desc())
                .limit(limit)
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(f"Found {len(entities)} rates from source {source}")
            return entities

        except Exception as e:
            logger.error(f"Failed to find rates by source {source}: {str(e)}")
            raise

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
        try:
            cutoff_time = datetime.utcnow().replace(microsecond=0)
            cutoff_time = cutoff_time.replace(
                minute=cutoff_time.minute - max_age_minutes
            )

            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(ExchangeRateModel.timestamp < cutoff_time)
                .order_by(ExchangeRateModel.timestamp.asc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} stale rates older than {max_age_minutes} minutes"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to find stale rates: {str(e)}")
            raise

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
        try:
            pair_str = str(currency_pair)

            result = await self._session.execute(
                select(
                    func.min(ExchangeRateModel.rate).label("min_rate"),
                    func.max(ExchangeRateModel.rate).label("max_rate"),
                    func.avg(ExchangeRateModel.rate).label("avg_rate"),
                    func.count(ExchangeRateModel.id).label("count"),
                    func.sum(ExchangeRateModel.volume).label("total_volume"),
                ).where(
                    and_(
                        ExchangeRateModel.currency_pair == pair_str,
                        ExchangeRateModel.timestamp >= start_time,
                        ExchangeRateModel.timestamp <= end_time,
                    )
                )
            )

            row = result.first()

            if row and row.count > 0:
                stats = {
                    "min": float(row.min_rate) if row.min_rate else 0.0,
                    "max": float(row.max_rate) if row.max_rate else 0.0,
                    "avg": float(row.avg_rate) if row.avg_rate else 0.0,
                    "count": int(row.count),
                    "total_volume": int(row.total_volume) if row.total_volume else 0,
                }

                logger.debug(f"Calculated statistics for {pair_str}: {stats}")
                return stats
            else:
                logger.debug(f"No data found for statistics calculation: {pair_str}")
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "count": 0,
                    "total_volume": 0,
                }

        except Exception as e:
            logger.error(f"Failed to get rate statistics for {currency_pair}: {str(e)}")
            raise

    async def delete_old_rates(self, before_date: datetime) -> int:
        """
        指定日時より古い為替レートデータを削除

        Args:
            before_date: この日時より古いデータを削除

        Returns:
            int: 削除されたレコード数
        """
        try:
            # まず削除対象のカウントを取得
            count_result = await self._session.execute(
                select(func.count(ExchangeRateModel.id)).where(
                    ExchangeRateModel.timestamp < before_date
                )
            )
            count = count_result.scalar() or 0

            # 削除実行
            if count > 0:
                result = await self._session.execute(
                    ExchangeRateModel.__table__.delete().where(
                        ExchangeRateModel.timestamp < before_date
                    )
                )

                logger.info(
                    f"Deleted {count} old exchange rate records before {before_date}"
                )
                return count
            else:
                logger.debug("No old exchange rate records to delete")
                return 0

        except Exception as e:
            logger.error(f"Failed to delete old rates: {str(e)}")
            raise

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
        try:
            if not rates:
                return []

            # エンティティをモデルに変換
            models = [ExchangeRateModel.from_entity(rate) for rate in rates]

            # 一括追加
            self._session.add_all(models)
            await self._session.flush()

            # モデルをエンティティに戻して返す
            result_entities = [model.to_entity() for model in models]

            logger.debug(f"Bulk saved {len(result_entities)} exchange rates")
            return result_entities

        except Exception as e:
            logger.error(f"Failed to bulk save {len(rates)} rates: {str(e)}")
            raise

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
        try:
            result_dict = {}
            pair_strings = [str(pair) for pair in currency_pairs]

            if not pair_strings:
                return result_dict

            # サブクエリで各通貨ペアの最新タイムスタンプを取得
            latest_subquery = (
                select(
                    ExchangeRateModel.currency_pair,
                    func.max(ExchangeRateModel.timestamp).label("latest_timestamp"),
                )
                .where(ExchangeRateModel.currency_pair.in_(pair_strings))
                .group_by(ExchangeRateModel.currency_pair)
                .subquery()
            )

            # 最新レートを取得
            result = await self._session.execute(
                select(ExchangeRateModel).join(
                    latest_subquery,
                    and_(
                        ExchangeRateModel.currency_pair
                        == latest_subquery.c.currency_pair,
                        ExchangeRateModel.timestamp
                        == latest_subquery.c.latest_timestamp,
                    ),
                )
            )

            models = result.scalars().all()

            for model in models:
                entity = model.to_entity()
                result_dict[model.currency_pair] = entity

            logger.debug(
                f"Found latest rates for {len(result_dict)}/{len(currency_pairs)} currency pairs"
            )
            return result_dict

        except Exception as e:
            logger.error(f"Failed to find latest rates for pairs: {str(e)}")
            raise

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
        try:
            pair_str = str(currency_pair)
            threshold_value = float(threshold.value)

            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(
                    and_(
                        ExchangeRateModel.currency_pair == pair_str,
                        ExchangeRateModel.rate >= threshold_value,
                        ExchangeRateModel.timestamp >= since,
                    )
                )
                .order_by(ExchangeRateModel.timestamp.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} rates above {threshold_value} "
                f"for {pair_str} since {since}"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to find rates above threshold: {str(e)}")
            raise

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
        try:
            pair_str = str(currency_pair)
            threshold_value = float(threshold.value)

            result = await self._session.execute(
                select(ExchangeRateModel)
                .where(
                    and_(
                        ExchangeRateModel.currency_pair == pair_str,
                        ExchangeRateModel.rate <= threshold_value,
                        ExchangeRateModel.timestamp >= since,
                    )
                )
                .order_by(ExchangeRateModel.timestamp.desc())
            )

            models = result.scalars().all()
            entities = [model.to_entity() for model in models]

            logger.debug(
                f"Found {len(entities)} rates below {threshold_value} "
                f"for {pair_str} since {since}"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to find rates below threshold: {str(e)}")
            raise
