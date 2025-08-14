"""
価格データリポジトリ実装

USD/JPY特化の5分おきデータ取得システム用の価格データリポジトリ実装
設計書参照: /app/note/database_implementation_design_2025.md
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.base_repository_impl import (
    BaseRepositoryImpl,
)
from src.infrastructure.database.repositories.price_data_repository import (
    PriceDataRepository,
)

logger = logging.getLogger(__name__)


class PriceDataRepositoryImpl(BaseRepositoryImpl, PriceDataRepository):
    """
    価格データリポジトリ実装

    責任:
    - 価格データの永続化
    - 価格データの取得・検索
    - バッチ処理
    - データクリーンアップ

    特徴:
    - USD/JPY特化設計
    - 5分間隔データ対応
    - 高パフォーマンスクエリ
    - バッチ処理最適化
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def save(self, price_data: PriceDataModel) -> PriceDataModel:
        """
        価格データを保存

        Args:
            price_data: 保存する価格データ

        Returns:
            PriceDataModel: 保存された価格データ
        """
        try:
            # バリデーション
            if not price_data.validate():
                raise ValueError("Invalid price data")

            # 重複チェック（タイムスタンプ、通貨ペア、データソースで判定）
            existing = await self.find_by_timestamp_and_source(
                price_data.timestamp, price_data.currency_pair, price_data.data_source
            )
            if existing:
                # 重複の場合は静かに既存データを返す
                # WARNINGログは出さない
                return existing

            # 保存
            self.session.add(price_data)
            await self.session.commit()
            await self.session.refresh(price_data)
            logger.info(
                f"Saved price data for {price_data.currency_pair} "
                f"at {price_data.timestamp}"
            )
            return price_data

        except Exception as e:
            # エラーメッセージを簡潔に表示
            error_msg = str(e)
            if "Background on this error" in error_msg:
                # SQLAlchemyの詳細エラー情報を除去
                error_msg = error_msg.split("(Background on this error")[0].strip()
            logger.error(f"Error saving price data: {error_msg}")
            raise

    async def delete(self, id: int) -> bool:
        """
        価格データを削除

        Args:
            id: 削除する価格データのID

        Returns:
            bool: 削除成功フラグ
        """
        try:
            # データを取得
            query = select(PriceDataModel).where(PriceDataModel.id == id)
            result = await self.session.execute(query)
            price_data = result.scalar_one_or_none()

            if not price_data:
                logger.warning(f"Price data with id {id} not found")
                return False

            # 削除
            await self.session.delete(price_data)
            await self.session.commit()
            logger.info(f"Deleted price data with id {id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting price data: {e}")
            raise

    async def save_batch(
        self, price_data_list: List[PriceDataModel]
    ) -> List[PriceDataModel]:
        """
        価格データをバッチ保存

        Args:
            price_data_list: 保存する価格データリスト

        Returns:
            List[PriceDataModel]: 保存された価格データリスト
        """
        try:
            # バリデーション
            valid_data = []
            for price_data in price_data_list:
                if price_data.validate():
                    valid_data.append(price_data)
                else:
                    logger.warning(f"Invalid price data: {price_data}")

            if not valid_data:
                logger.warning("No valid price data to save")
                return []

            # 重複チェック
            timestamps = [(pd.timestamp, pd.currency_pair) for pd in valid_data]
            existing_query = select(PriceDataModel).where(
                and_(
                    PriceDataModel.timestamp.in_([ts[0] for ts in timestamps]),
                    PriceDataModel.currency_pair.in_([ts[1] for ts in timestamps]),
                )
            )
            existing_result = await self.session.execute(existing_query)
            existing_data = existing_result.scalars().all()
            existing_timestamps = {
                (ed.timestamp, ed.currency_pair) for ed in existing_data
            }

            # 重複しないデータのみ保存
            new_data = [
                pd
                for pd in valid_data
                if (pd.timestamp, pd.currency_pair) not in existing_timestamps
            ]

            if not new_data:
                logger.info("All price data already exists")
                return existing_data

            # バッチ保存
            saved_data = await super().save_batch(new_data)
            logger.info(f"Saved {len(saved_data)} new price data records")
            return saved_data

        except Exception as e:
            logger.error(f"Error saving price data batch: {e}")
            raise

    async def find_by_timestamp(
        self, timestamp: datetime, currency_pair: str = "USD/JPY"
    ) -> Optional[PriceDataModel]:
        """
        タイムスタンプで価格データを取得

        Args:
            timestamp: タイムスタンプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            Optional[PriceDataModel]: 価格データ（存在しない場合はNone）
        """
        try:
            query = select(PriceDataModel).where(
                and_(
                    PriceDataModel.timestamp == timestamp,
                    PriceDataModel.currency_pair == currency_pair,
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error finding price data by timestamp: {e}")
            raise

    async def find_by_timestamp_and_source(
        self, timestamp: datetime, currency_pair: str, data_source: str
    ) -> Optional[PriceDataModel]:
        """
        タイムスタンプとデータソースで価格データを取得

        Args:
            timestamp: タイムスタンプ
            currency_pair: 通貨ペア
            data_source: データソース

        Returns:
            Optional[PriceDataModel]: 価格データ（存在しない場合はNone）
        """
        try:
            query = select(PriceDataModel).where(
                and_(
                    PriceDataModel.timestamp == timestamp,
                    PriceDataModel.currency_pair == currency_pair,
                    PriceDataModel.data_source == data_source,
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error finding price data by timestamp and source: {e}")
            raise

    async def find_latest(
        self, currency_pair: str = "USD/JPY", limit: int = 1
    ) -> List[PriceDataModel]:
        """
        最新の価格データを取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[PriceDataModel]: 最新の価格データリスト
        """
        try:
            query = (
                select(PriceDataModel)
                .where(PriceDataModel.currency_pair == currency_pair)
                .order_by(PriceDataModel.timestamp.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding latest price data: {e}")
            raise

    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        日付範囲で価格データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        try:
            # デバッグ用ログ
            logger.info(
                f"Finding price data: {start_date} to {end_date} for {currency_pair}"
            )

            query = (
                select(PriceDataModel)
                .where(
                    and_(
                        PriceDataModel.currency_pair == currency_pair,
                        PriceDataModel.timestamp >= start_date,
                        PriceDataModel.timestamp <= end_date,
                    )
                )
                .order_by(PriceDataModel.timestamp.asc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            price_data_list = result.scalars().all()

            # デバッグ用ログ
            logger.info(f"Found {len(price_data_list)} price data records")
            if price_data_list:
                logger.info(
                    f"Range: {price_data_list[0].timestamp} to {price_data_list[-1].timestamp}"
                )

            return list(price_data_list)

        except Exception as e:
            logger.error(f"Error finding price data by date range: {e}")
            raise

    async def find_by_price_range(
        self,
        min_price: float,
        max_price: float,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        価格範囲で価格データを取得

        Args:
            min_price: 最小価格
            max_price: 最大価格
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        try:
            conditions = [
                PriceDataModel.currency_pair == currency_pair,
                PriceDataModel.close_price >= min_price,
                PriceDataModel.close_price <= max_price,
            ]

            if start_date:
                conditions.append(PriceDataModel.timestamp >= start_date)
            if end_date:
                conditions.append(PriceDataModel.timestamp <= end_date)

            query = (
                select(PriceDataModel)
                .where(and_(*conditions))
                .order_by(PriceDataModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding price data by price range: {e}")
            raise

    async def find_missing_data(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
        interval_minutes: int = 5,
    ) -> List[datetime]:
        """
        欠損データのタイムスタンプを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
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
                start_date, end_date, currency_pair
            )
            existing_timestamps = {pd.timestamp for pd in existing_data}

            # 欠損データを特定
            missing_timestamps = [
                ts for ts in expected_timestamps if ts not in existing_timestamps
            ]

            logger.info(
                f"Found {len(missing_timestamps)} missing timestamps "
                f"out of {len(expected_timestamps)} expected"
            )
            return missing_timestamps

        except Exception as e:
            logger.error(f"Error finding missing data: {e}")
            raise

    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータ数を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: データ数
        """
        try:
            query = select(func.count(PriceDataModel.id)).where(
                and_(
                    PriceDataModel.currency_pair == currency_pair,
                    PriceDataModel.timestamp >= start_date,
                    PriceDataModel.timestamp <= end_date,
                )
            )
            result = await self.session.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Error counting price data by date range: {e}")
            raise

    async def get_price_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
    ) -> dict:
        """
        価格統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            dict: 統計情報（最小値、最大値、平均値等）
        """
        try:
            query = select(
                func.min(PriceDataModel.close_price).label("min_price"),
                func.max(PriceDataModel.close_price).label("max_price"),
                func.avg(PriceDataModel.close_price).label("avg_price"),
                func.count(PriceDataModel.id).label("count"),
            ).where(
                and_(
                    PriceDataModel.currency_pair == currency_pair,
                    PriceDataModel.timestamp >= start_date,
                    PriceDataModel.timestamp <= end_date,
                )
            )

            result = await self.session.execute(query)
            row = result.fetchone()

            return {
                "min_price": float(row.min_price) if row.min_price else None,
                "max_price": float(row.max_price) if row.max_price else None,
                "avg_price": float(row.avg_price) if row.avg_price else None,
                "count": row.count,
                "currency_pair": currency_pair,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting price statistics: {e}")
            raise

    async def delete_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータを削除

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        try:
            # 削除前に件数を取得
            count = await self.count_by_date_range(start_date, end_date, currency_pair)

            # 削除実行
            query = (
                select(PriceDataModel)
                .where(
                    and_(
                        PriceDataModel.currency_pair == currency_pair,
                        PriceDataModel.timestamp >= start_date,
                        PriceDataModel.timestamp <= end_date,
                    )
                )
                .execution_options(synchronize_session=False)
            )

            result = await self.session.execute(query)
            records_to_delete = result.scalars().all()

            for record in records_to_delete:
                await self.session.delete(record)

            await self.session.commit()

            logger.info(
                f"Deleted {count} price data records for {currency_pair} "
                f"from {start_date} to {end_date}"
            )
            return count

        except Exception as e:
            logger.error(f"Error deleting price data by date range: {e}")
            await self.session.rollback()
            raise

    async def delete_old_data(
        self, days_to_keep: int = 365, currency_pair: str = "USD/JPY"
    ) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            return await self.delete_by_date_range(
                datetime.min, cutoff_date, currency_pair
            )

        except Exception as e:
            logger.error(f"Error deleting old data: {e}")
            raise

    async def exists_by_timestamp(
        self, timestamp: datetime, currency_pair: str = "USD/JPY"
    ) -> bool:
        """
        タイムスタンプのデータが存在するかチェック

        Args:
            timestamp: タイムスタンプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            bool: 存在する場合True
        """
        try:
            query = select(func.count(PriceDataModel.id)).where(
                and_(
                    PriceDataModel.timestamp == timestamp,
                    PriceDataModel.currency_pair == currency_pair,
                )
            )
            result = await self.session.execute(query)
            return result.scalar() > 0

        except Exception as e:
            logger.error(f"Error checking existence by timestamp: {e}")
            raise

    async def get_data_sources(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        データソース一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: データソース一覧
        """
        try:
            query = (
                select(PriceDataModel.data_source)
                .where(PriceDataModel.currency_pair == currency_pair)
                .distinct()
            )
            result = await self.session.execute(query)
            return [row[0] for row in result.fetchall()]

        except Exception as e:
            logger.error(f"Error getting data sources: {e}")
            raise

    async def find_by_data_source(
        self,
        data_source: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        データソースで価格データを取得

        Args:
            data_source: データソース
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        try:
            conditions = [
                PriceDataModel.currency_pair == currency_pair,
                PriceDataModel.data_source == data_source,
            ]

            if start_date:
                conditions.append(PriceDataModel.timestamp >= start_date)
            if end_date:
                conditions.append(PriceDataModel.timestamp <= end_date)

            query = (
                select(PriceDataModel)
                .where(and_(*conditions))
                .order_by(PriceDataModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding price data by data source: {e}")
            raise

    async def delete_by_data_source(
        self, data_source: str, currency_pair: str = "USD/JPY"
    ) -> int:
        """
        データソース別に価格データを削除

        Args:
            data_source: データソース名
            currency_pair: 通貨ペア

        Returns:
            int: 削除されたレコード数
        """
        try:
            from sqlalchemy import delete

            delete_query = delete(PriceDataModel).where(
                and_(
                    PriceDataModel.data_source == data_source,
                    PriceDataModel.currency_pair == currency_pair,
                )
            )

            result = await self.session.execute(delete_query)
            await self.session.commit()

            deleted_count = result.rowcount
            logger.info(f"Deleted {deleted_count} price data records for {data_source}")
            return deleted_count

        except Exception as e:
            logger.error(f"Error deleting price data by data source: {e}")
            await self.session.rollback()
            raise

    async def find_by_date_range_and_timeframe(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
        timeframe: str = "5m",
        limit: Optional[int] = None,
    ) -> List[PriceDataModel]:
        """
        時間軸別に価格データを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア
            timeframe: 時間軸（5m, 1h, 4h, 1d）
            limit: 取得件数制限

        Returns:
            List[PriceDataModel]: 価格データリスト
        """
        try:
            # 時間軸に応じてタイムスタンプを調整
            adjusted_start = self._adjust_timestamp_for_timeframe(start_date, timeframe)
            adjusted_end = self._adjust_timestamp_for_timeframe(end_date, timeframe)

            query = (
                select(PriceDataModel)
                .where(
                    and_(
                        PriceDataModel.currency_pair == currency_pair,
                        PriceDataModel.timestamp >= adjusted_start,
                        PriceDataModel.timestamp <= adjusted_end,
                    )
                )
                .order_by(PriceDataModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            price_data_list = result.scalars().all()

            logger.info(
                f"Found {len(price_data_list)} price data records for {currency_pair} "
                f"timeframe {timeframe} from {adjusted_start} to {adjusted_end}"
            )

            return list(price_data_list)

        except Exception as e:
            logger.error(f"Error finding price data by date range and timeframe: {e}")
            return []

    def _adjust_timestamp_for_timeframe(
        self, timestamp: datetime, timeframe: str
    ) -> datetime:
        """
        タイムスタンプを時間軸に合わせて調整
        """
        if timeframe == "5m":
            # 5分単位に調整
            minutes = (timestamp.minute // 5) * 5
            return timestamp.replace(minute=minutes, second=0, microsecond=0)
        elif timeframe == "1h":
            # 1時間単位に調整
            return timestamp.replace(minute=0, second=0, microsecond=0)
        elif timeframe == "4h":
            # 4時間単位に調整
            hour = (timestamp.hour // 4) * 4
            return timestamp.replace(hour=hour, minute=0, second=0, microsecond=0)
        elif timeframe == "1d":
            # 日単位に調整
            return timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            return timestamp
