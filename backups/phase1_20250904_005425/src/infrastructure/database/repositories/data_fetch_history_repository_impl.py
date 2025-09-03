"""
データ取得履歴リポジトリ実装

USD/JPY特化のデータ取得履歴リポジトリ実装
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.data_fetch_history_model import (
    DataFetchHistoryModel,
)
from src.infrastructure.database.repositories.base_repository_impl import (
    BaseRepositoryImpl,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DataFetchHistoryRepositoryImpl(BaseRepositoryImpl):
    """
    データ取得履歴リポジトリ実装

    責任:
    - データ取得履歴のCRUD操作
    - 取得統計の管理
    - エラー履歴の追跡
    - パフォーマンス監視

    特徴:
    - USD/JPY特化設計
    - 高精度な履歴管理
    - 統計機能
    - エラー追跡
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        super().__init__(session)

    async def save(self, fetch_history: DataFetchHistoryModel) -> DataFetchHistoryModel:
        """
        データ取得履歴を保存

        Args:
            fetch_history: 保存する履歴

        Returns:
            DataFetchHistoryModel: 保存された履歴
        """
        try:
            # バリデーション
            if not fetch_history.validate():
                raise ValueError("Invalid fetch history data")

            # 保存
            self.session.add(fetch_history)
            await self.session.commit()
            await self.session.refresh(fetch_history)
            logger.info(
                f"Saved fetch history for {fetch_history.currency_pair} "
                f"at {fetch_history.fetch_timestamp}"
            )
            return fetch_history

        except Exception as e:
            logger.error(f"Error saving fetch history: {e}")
            raise

    async def create_fetch_history(
        self,
        currency_pair: str = "USD/JPY",
        data_source: str = "Yahoo Finance",
        status: str = "success",
        response_time: Optional[float] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0,
        records_fetched: Optional[int] = None,
    ) -> DataFetchHistoryModel:
        """
        データ取得履歴を作成

        Args:
            currency_pair: 通貨ペア
            data_source: データソース
            status: 取得ステータス
            response_time: レスポンス時間
            error_message: エラーメッセージ
            retry_count: リトライ回数
            records_fetched: 取得レコード数

        Returns:
            DataFetchHistoryModel: 作成された履歴
        """
        history = DataFetchHistoryModel(
            currency_pair=currency_pair,
            data_source=data_source,
            status=status,
            response_time=response_time,
            error_message=error_message,
            retry_count=retry_count,
            records_fetched=records_fetched,
        )

        return await self.save(history)

    async def get_latest_fetch_history(
        self, currency_pair: str = "USD/JPY", limit: int = 10
    ) -> List[DataFetchHistoryModel]:
        """
        最新のデータ取得履歴を取得

        Args:
            currency_pair: 通貨ペア
            limit: 取得件数

        Returns:
            List[DataFetchHistoryModel]: 履歴リスト
        """
        query = (
            self.session.query(DataFetchHistoryModel)
            .filter(DataFetchHistoryModel.currency_pair == currency_pair)
            .order_by(desc(DataFetchHistoryModel.timestamp))
            .limit(limit)
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_fetch_history_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        currency_pair: str = "USD/JPY",
    ) -> List[DataFetchHistoryModel]:
        """
        日付範囲でデータ取得履歴を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            currency_pair: 通貨ペア

        Returns:
            List[DataFetchHistoryModel]: 履歴リスト
        """
        query = (
            self.session.query(DataFetchHistoryModel)
            .filter(
                and_(
                    DataFetchHistoryModel.currency_pair == currency_pair,
                    DataFetchHistoryModel.timestamp >= start_date,
                    DataFetchHistoryModel.timestamp <= end_date,
                )
            )
            .order_by(desc(DataFetchHistoryModel.timestamp))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_successful_fetches(
        self, currency_pair: str = "USD/JPY", hours: int = 24
    ) -> List[DataFetchHistoryModel]:
        """
        成功したデータ取得履歴を取得

        Args:
            currency_pair: 通貨ペア
            hours: 時間範囲

        Returns:
            List[DataFetchHistoryModel]: 成功履歴リスト
        """
        start_time = datetime.now() - timedelta(hours=hours)

        query = (
            self.session.query(DataFetchHistoryModel)
            .filter(
                and_(
                    DataFetchHistoryModel.currency_pair == currency_pair,
                    DataFetchHistoryModel.status == "success",
                    DataFetchHistoryModel.timestamp >= start_time,
                )
            )
            .order_by(desc(DataFetchHistoryModel.timestamp))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_failed_fetches(
        self, currency_pair: str = "USD/JPY", hours: int = 24
    ) -> List[DataFetchHistoryModel]:
        """
        失敗したデータ取得履歴を取得

        Args:
            currency_pair: 通貨ペア
            hours: 時間範囲

        Returns:
            List[DataFetchHistoryModel]: 失敗履歴リスト
        """
        start_time = datetime.now() - timedelta(hours=hours)

        query = (
            self.session.query(DataFetchHistoryModel)
            .filter(
                and_(
                    DataFetchHistoryModel.currency_pair == currency_pair,
                    DataFetchHistoryModel.status == "error",
                    DataFetchHistoryModel.timestamp >= start_time,
                )
            )
            .order_by(desc(DataFetchHistoryModel.timestamp))
        )

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_fetch_statistics(
        self, currency_pair: str = "USD/JPY", hours: int = 24
    ) -> dict:
        """
        データ取得統計を取得

        Args:
            currency_pair: 通貨ペア
            hours: 時間範囲

        Returns:
            dict: 統計情報
        """
        start_time = datetime.now() - timedelta(hours=hours)

        # 総取得回数
        total_query = self.session.query(func.count(DataFetchHistoryModel.id)).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.timestamp >= start_time,
            )
        )

        # 成功回数
        success_query = self.session.query(func.count(DataFetchHistoryModel.id)).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.status == "success",
                DataFetchHistoryModel.timestamp >= start_time,
            )
        )

        # 失敗回数
        error_query = self.session.query(func.count(DataFetchHistoryModel.id)).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.status == "error",
                DataFetchHistoryModel.timestamp >= start_time,
            )
        )

        # 平均レスポンス時間
        avg_response_time_query = self.session.query(
            func.avg(DataFetchHistoryModel.response_time)
        ).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.status == "success",
                DataFetchHistoryModel.response_time.isnot(None),
                DataFetchHistoryModel.timestamp >= start_time,
            )
        )

        # 総取得レコード数
        total_records_query = self.session.query(
            func.sum(DataFetchHistoryModel.records_fetched)
        ).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.status == "success",
                DataFetchHistoryModel.records_fetched.isnot(None),
                DataFetchHistoryModel.timestamp >= start_time,
            )
        )

        # クエリ実行
        total_result = await self.session.execute(total_query)
        success_result = await self.session.execute(success_query)
        error_result = await self.session.execute(error_query)
        avg_response_time_result = await self.session.execute(avg_response_time_query)
        total_records_result = await self.session.execute(total_records_query)

        # 結果取得
        total_fetches = total_result.scalar() or 0
        successful_fetches = success_result.scalar() or 0
        failed_fetches = error_result.scalar() or 0
        avg_response_time = avg_response_time_result.scalar() or 0.0
        total_records = total_records_result.scalar() or 0

        # 成功率計算
        success_rate = (
            (successful_fetches / total_fetches * 100) if total_fetches > 0 else 0
        )

        return {
            "total_fetches": total_fetches,
            "successful_fetches": successful_fetches,
            "failed_fetches": failed_fetches,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_response_time, 3),
            "total_records": total_records,
            "time_range_hours": hours,
        }

    async def get_error_summary(
        self, currency_pair: str = "USD/JPY", hours: int = 24
    ) -> List[dict]:
        """
        エラーサマリーを取得

        Args:
            currency_pair: 通貨ペア
            hours: 時間範囲

        Returns:
            List[dict]: エラーサマリー
        """
        start_time = datetime.now() - timedelta(hours=hours)

        # エラーメッセージ別の集計
        error_summary_query = (
            self.session.query(
                DataFetchHistoryModel.error_message,
                func.count(DataFetchHistoryModel.id).label("error_count"),
            )
            .filter(
                and_(
                    DataFetchHistoryModel.currency_pair == currency_pair,
                    DataFetchHistoryModel.status == "error",
                    DataFetchHistoryModel.timestamp >= start_time,
                )
            )
            .group_by(DataFetchHistoryModel.error_message)
            .order_by(desc("error_count"))
        )

        result = await self.session.execute(error_summary_query)
        return [
            {
                "error_message": row.error_message,
                "error_count": row.error_count,
            }
            for row in result
        ]

    async def cleanup_old_history(
        self, days: int = 30, currency_pair: str = "USD/JPY"
    ) -> int:
        """
        古い履歴を削除

        Args:
            days: 保持日数
            currency_pair: 通貨ペア

        Returns:
            int: 削除件数
        """
        cutoff_date = datetime.now() - timedelta(days=days)

        query = self.session.query(DataFetchHistoryModel).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.timestamp < cutoff_date,
            )
        )

        result = await self.session.execute(query)
        old_records = result.scalars().all()

        # 削除実行
        deleted_count = 0
        for record in old_records:
            await self.session.delete(record)
            deleted_count += 1

        await self.session.commit()
        return deleted_count

    async def get_performance_metrics(
        self, currency_pair: str = "USD/JPY", hours: int = 24
    ) -> dict:
        """
        パフォーマンスメトリクスを取得

        Args:
            currency_pair: 通貨ペア
            hours: 時間範囲

        Returns:
            dict: パフォーマンスメトリクス
        """
        start_time = datetime.now() - timedelta(hours=hours)

        # レスポンス時間の統計
        response_time_stats_query = self.session.query(
            func.min(DataFetchHistoryModel.response_time).label("min_response_time"),
            func.max(DataFetchHistoryModel.response_time).label("max_response_time"),
            func.avg(DataFetchHistoryModel.response_time).label("avg_response_time"),
            func.stddev(DataFetchHistoryModel.response_time).label("std_response_time"),
        ).filter(
            and_(
                DataFetchHistoryModel.currency_pair == currency_pair,
                DataFetchHistoryModel.status == "success",
                DataFetchHistoryModel.response_time.isnot(None),
                DataFetchHistoryModel.timestamp >= start_time,
            )
        )

        result = await self.session.execute(response_time_stats_query)
        row = result.first()

        if row:
            return {
                "min_response_time": round(row.min_response_time or 0, 3),
                "max_response_time": round(row.max_response_time or 0, 3),
                "avg_response_time": round(row.avg_response_time or 0, 3),
                "std_response_time": round(row.std_response_time or 0, 3),
                "time_range_hours": hours,
            }
        else:
            return {
                "min_response_time": 0,
                "max_response_time": 0,
                "avg_response_time": 0,
                "std_response_time": 0,
                "time_range_hours": hours,
            }
