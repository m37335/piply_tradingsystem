"""
テクニカル指標リポジトリ実装

USD/JPY特化の5分おきデータ取得システム用のテクニカル指標リポジトリ実装
設計書参照: /app/note/database_implementation_design_2025.md
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.repositories.base_repository_impl import (
    BaseRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository import (
    TechnicalIndicatorRepository,
)

logger = logging.getLogger(__name__)


class TechnicalIndicatorRepositoryImpl(
    BaseRepositoryImpl, TechnicalIndicatorRepository
):
    """
    テクニカル指標リポジトリ実装

    責任:
    - テクニカル指標の永続化
    - テクニカル指標の取得・検索
    - 複数タイムフレーム対応
    - 指標計算結果の管理

    特徴:
    - USD/JPY特化設計
    - 複数タイムフレーム対応
    - 高パフォーマンスクエリ
    - 指標別管理
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def save(self, indicator: TechnicalIndicatorModel) -> TechnicalIndicatorModel:
        """
        テクニカル指標を保存

        Args:
            indicator: 保存するテクニカル指標

        Returns:
            TechnicalIndicatorModel: 保存されたテクニカル指標
        """
        try:
            # バリデーション（一時的に無効化）
            # if not indicator.validate():
            #     raise ValueError("Invalid technical indicator")

            # 重複チェック
            existing = await self.find_by_timestamp_and_type(
                indicator.timestamp,
                indicator.indicator_type,
                indicator.timeframe,
                indicator.currency_pair,
            )
            if existing:
                logger.warning(
                    f"Technical indicator already exists for {indicator.currency_pair} "
                    f"{indicator.indicator_type} {indicator.timeframe} "
                    f"at {indicator.timestamp}"
                )
                return existing

            # 保存
            saved_indicator = await super().save(indicator)
            logger.info(
                f"Saved technical indicator {saved_indicator.indicator_type} "
                f"for {saved_indicator.currency_pair} at {saved_indicator.timestamp}"
            )
            return saved_indicator

        except Exception as e:
            logger.error(f"Error saving technical indicator: {e}")
            raise

    async def save_batch(
        self, indicator_list: List[TechnicalIndicatorModel]
    ) -> List[TechnicalIndicatorModel]:
        """
        テクニカル指標をバッチ保存

        Args:
            indicator_list: 保存するテクニカル指標リスト

        Returns:
            List[TechnicalIndicatorModel]: 保存されたテクニカル指標リスト
        """
        try:
            # バリデーション（一時的に無効化）
            valid_indicators = indicator_list
            # for indicator in indicator_list:
            #     if indicator.validate():
            #         valid_indicators.append(indicator)
            #     else:
            #         logger.warning(f"Invalid technical indicator: {indicator}")

            if not valid_indicators:
                logger.warning("No valid technical indicators to save")
                return []

            # 重複チェック
            unique_keys = [
                (ind.timestamp, ind.indicator_type, ind.timeframe, ind.currency_pair)
                for ind in valid_indicators
            ]
            existing_query = select(TechnicalIndicatorModel).where(
                and_(
                    TechnicalIndicatorModel.timestamp.in_(
                        [uk[0] for uk in unique_keys]
                    ),
                    TechnicalIndicatorModel.indicator_type.in_(
                        [uk[1] for uk in unique_keys]
                    ),
                    TechnicalIndicatorModel.timeframe.in_(
                        [uk[2] for uk in unique_keys]
                    ),
                    TechnicalIndicatorModel.currency_pair.in_(
                        [uk[3] for uk in unique_keys]
                    ),
                )
            )
            existing_result = await self.session.execute(existing_query)
            existing_data = existing_result.scalars().all()
            existing_keys = {
                (ed.timestamp, ed.indicator_type, ed.timeframe, ed.currency_pair)
                for ed in existing_data
            }

            # 重複しないデータのみ保存
            new_indicators = [
                ind
                for ind in valid_indicators
                if (ind.timestamp, ind.indicator_type, ind.timeframe, ind.currency_pair)
                not in existing_keys
            ]

            if not new_indicators:
                logger.info("All technical indicators already exist")
                return existing_data

            # バッチ保存
            saved_indicators = await super().save_batch(new_indicators)
            logger.info(f"Saved {len(saved_indicators)} new technical indicators")
            return saved_indicators

        except Exception as e:
            logger.error(f"Error saving technical indicator batch: {e}")
            raise

    async def find_by_timestamp_and_type(
        self,
        timestamp: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
    ) -> Optional[TechnicalIndicatorModel]:
        """
        タイムスタンプ・指標タイプ・タイムフレームでテクニカル指標を取得

        Args:
            timestamp: タイムスタンプ
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            Optional[TechnicalIndicatorModel]: テクニカル指標（存在しない場合はNone）
        """
        try:
            query = select(TechnicalIndicatorModel).where(
                and_(
                    TechnicalIndicatorModel.timestamp == timestamp,
                    TechnicalIndicatorModel.indicator_type == indicator_type,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.currency_pair == currency_pair,
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"Error finding technical indicator by timestamp and type: {e}"
            )
            raise

    async def find_latest_by_type(
        self,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
        limit: int = 1,
    ) -> List[TechnicalIndicatorModel]:
        """
        指標タイプ・タイムフレームで最新のテクニカル指標を取得

        Args:
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[TechnicalIndicatorModel]: 最新のテクニカル指標リスト
        """
        try:
            query = (
                select(TechnicalIndicatorModel)
                .where(
                    and_(
                        TechnicalIndicatorModel.indicator_type == indicator_type,
                        TechnicalIndicatorModel.timeframe == timeframe,
                        TechnicalIndicatorModel.currency_pair == currency_pair,
                    )
                )
                .order_by(TechnicalIndicatorModel.timestamp.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding latest technical indicators by type: {e}")
            raise

    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        日付範囲でテクニカル指標を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        try:
            conditions = [
                TechnicalIndicatorModel.currency_pair == currency_pair,
                TechnicalIndicatorModel.timestamp >= start_date,
                TechnicalIndicatorModel.timestamp <= end_date,
            ]

            if indicator_type:
                conditions.append(
                    TechnicalIndicatorModel.indicator_type == indicator_type
                )
            if timeframe:
                conditions.append(TechnicalIndicatorModel.timeframe == timeframe)

            query = (
                select(TechnicalIndicatorModel)
                .where(and_(*conditions))
                .order_by(TechnicalIndicatorModel.timestamp.asc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding technical indicators by date range: {e}")
            raise

    async def find_by_value_range(
        self,
        min_value: float,
        max_value: float,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        値範囲でテクニカル指標を取得

        Args:
            min_value: 最小値
            max_value: 最大値
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        try:
            conditions = [
                TechnicalIndicatorModel.currency_pair == currency_pair,
                TechnicalIndicatorModel.indicator_type == indicator_type,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.value >= min_value,
                TechnicalIndicatorModel.value <= max_value,
            ]

            if start_date:
                conditions.append(TechnicalIndicatorModel.timestamp >= start_date)
            if end_date:
                conditions.append(TechnicalIndicatorModel.timestamp <= end_date)

            query = (
                select(TechnicalIndicatorModel)
                .where(and_(*conditions))
                .order_by(TechnicalIndicatorModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding technical indicators by value range: {e}")
            raise

    async def find_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
        interval_minutes: int = 5,
    ) -> List[datetime]:
        """
        欠損データのタイムスタンプを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            interval_minutes: 間隔（分）（デフォルト: 5）

        Returns:
            List[datetime]: 欠損データのタイムスタンプリスト
        """
        try:
            # 期待されるタイムスタンプを生成
            expected_timestamps = []
            current = start_date
            while current <= end_date:
                expected_timestamps.append(current)
                current += timedelta(minutes=interval_minutes)

            # 実際のデータを取得
            existing_data = await self.find_by_date_range(
                start_date, end_date, indicator_type, timeframe, currency_pair
            )
            existing_timestamps = {ind.timestamp for ind in existing_data}

            # 欠損データを特定
            missing_timestamps = [
                ts for ts in expected_timestamps if ts not in existing_timestamps
            ]

            logger.info(
                f"Found {len(missing_timestamps)} missing timestamps "
                f"for {indicator_type} {timeframe} "
                f"out of {len(expected_timestamps)} expected"
            )
            return missing_timestamps

        except Exception as e:
            logger.error(f"Error finding missing technical indicator data: {e}")
            raise

    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータ数を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: データ数
        """
        try:
            # 文字列型のタイムスタンプに対応するため、文字列比較を使用
            start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
            end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")

            conditions = [
                TechnicalIndicatorModel.currency_pair == currency_pair,
                TechnicalIndicatorModel.timestamp >= start_date_str,
                TechnicalIndicatorModel.timestamp <= end_date_str,
            ]

            if indicator_type:
                conditions.append(
                    TechnicalIndicatorModel.indicator_type == indicator_type
                )
            if timeframe:
                conditions.append(TechnicalIndicatorModel.timeframe == timeframe)

            query = select(func.count(TechnicalIndicatorModel.id)).where(
                and_(*conditions)
            )
            result = await self.session.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Error counting technical indicators by date range: {e}")
            raise

    async def get_indicator_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
    ) -> dict:
        """
        指標統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            dict: 統計情報（最小値、最大値、平均値等）
        """
        try:
            query = select(
                func.min(TechnicalIndicatorModel.value).label("min_value"),
                func.max(TechnicalIndicatorModel.value).label("max_value"),
                func.avg(TechnicalIndicatorModel.value).label("avg_value"),
                func.count(TechnicalIndicatorModel.id).label("count"),
            ).where(
                and_(
                    TechnicalIndicatorModel.currency_pair == currency_pair,
                    TechnicalIndicatorModel.indicator_type == indicator_type,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.timestamp >= start_date,
                    TechnicalIndicatorModel.timestamp <= end_date,
                )
            )

            result = await self.session.execute(query)
            row = result.fetchone()

            return {
                "min_value": float(row.min_value) if row.min_value else None,
                "max_value": float(row.max_value) if row.max_value else None,
                "avg_value": float(row.avg_value) if row.avg_value else None,
                "count": row.count,
                "indicator_type": indicator_type,
                "timeframe": timeframe,
                "currency_pair": currency_pair,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting technical indicator statistics: {e}")
            raise

    async def delete_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータを削除

        Args:
            start_date: 開始日時
            end_date: 終了日時
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        try:
            # 削除前に件数を取得
            count = await self.count_by_date_range(
                start_date, end_date, indicator_type, timeframe, currency_pair
            )

            # 削除実行
            conditions = [
                TechnicalIndicatorModel.currency_pair == currency_pair,
                TechnicalIndicatorModel.timestamp >= start_date,
                TechnicalIndicatorModel.timestamp <= end_date,
            ]

            if indicator_type:
                conditions.append(
                    TechnicalIndicatorModel.indicator_type == indicator_type
                )
            if timeframe:
                conditions.append(TechnicalIndicatorModel.timeframe == timeframe)

            query = (
                select(TechnicalIndicatorModel)
                .where(and_(*conditions))
                .execution_options(synchronize_session=False)
            )

            result = await self.session.execute(query)
            records_to_delete = result.scalars().all()

            for record in records_to_delete:
                await self.session.delete(record)

            await self.session.commit()

            logger.info(
                f"Deleted {count} technical indicator records for {currency_pair} "
                f"from {start_date} to {end_date}"
            )
            return count

        except Exception as e:
            logger.error(f"Error deleting technical indicators by date range: {e}")
            await self.session.rollback()
            raise

    async def delete_old_data(
        self,
        days_to_keep: int = 365,
        indicator_type: Optional[str] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）
            indicator_type: 指標タイプ（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            return await self.delete_by_date_range(
                datetime.min, cutoff_date, indicator_type, timeframe, currency_pair
            )

        except Exception as e:
            logger.error(f"Error deleting old technical indicator data: {e}")
            raise

    async def exists_by_timestamp_and_type(
        self,
        timestamp: datetime,
        indicator_type: str,
        timeframe: str,
        currency_pair: str = "USD/JPY",
    ) -> bool:
        """
        タイムスタンプ・指標タイプ・タイムフレームのデータが存在するかチェック

        Args:
            timestamp: タイムスタンプ
            indicator_type: 指標タイプ
            timeframe: タイムフレーム
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            bool: 存在する場合True
        """
        try:
            query = select(func.count(TechnicalIndicatorModel.id)).where(
                and_(
                    TechnicalIndicatorModel.timestamp == timestamp,
                    TechnicalIndicatorModel.indicator_type == indicator_type,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.currency_pair == currency_pair,
                )
            )
            result = await self.session.execute(query)
            return result.scalar() > 0

        except Exception as e:
            logger.error(f"Error checking existence by timestamp and type: {e}")
            raise

    async def get_indicator_types(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        指標タイプ一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: 指標タイプ一覧
        """
        try:
            query = (
                select(TechnicalIndicatorModel.indicator_type)
                .where(TechnicalIndicatorModel.currency_pair == currency_pair)
                .distinct()
            )
            result = await self.session.execute(query)
            return [row[0] for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Error getting indicator types: {e}")
            raise

    async def get_timeframes(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        タイムフレーム一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: タイムフレーム一覧
        """
        try:
            query = (
                select(TechnicalIndicatorModel.timeframe)
                .where(TechnicalIndicatorModel.currency_pair == currency_pair)
                .distinct()
            )
            result = await self.session.execute(query)
            return [row[0] for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Error getting timeframes: {e}")
            raise

    async def find_by_indicator_type(
        self,
        indicator_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        指標タイプでテクニカル指標を取得

        Args:
            indicator_type: 指標タイプ
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            timeframe: タイムフレーム（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        try:
            conditions = [
                TechnicalIndicatorModel.currency_pair == currency_pair,
                TechnicalIndicatorModel.indicator_type == indicator_type,
            ]

            if start_date:
                conditions.append(TechnicalIndicatorModel.timestamp >= start_date)
            if end_date:
                conditions.append(TechnicalIndicatorModel.timestamp <= end_date)
            if timeframe:
                conditions.append(TechnicalIndicatorModel.timeframe == timeframe)

            query = (
                select(TechnicalIndicatorModel)
                .where(and_(*conditions))
                .order_by(TechnicalIndicatorModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding technical indicators by indicator type: {e}")
            raise

    async def find_by_timeframe(
        self,
        timeframe: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        indicator_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[TechnicalIndicatorModel]:
        """
        タイムフレームでテクニカル指標を取得

        Args:
            timeframe: タイムフレーム
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            indicator_type: 指標タイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[TechnicalIndicatorModel]: テクニカル指標リスト
        """
        try:
            conditions = [
                TechnicalIndicatorModel.currency_pair == currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
            ]

            if start_date:
                conditions.append(TechnicalIndicatorModel.timestamp >= start_date)
            if end_date:
                conditions.append(TechnicalIndicatorModel.timestamp <= end_date)
            if indicator_type:
                conditions.append(
                    TechnicalIndicatorModel.indicator_type == indicator_type
                )

            query = (
                select(TechnicalIndicatorModel)
                .where(and_(*conditions))
                .order_by(TechnicalIndicatorModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding technical indicators by timeframe: {e}")
            raise
