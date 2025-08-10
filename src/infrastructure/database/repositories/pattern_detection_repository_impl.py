"""
パターン検出リポジトリ実装

USD/JPY特化の5分おきデータ取得システム用のパターン検出リポジトリ実装
設計書参照: /app/note/database_implementation_design_2025.md
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)
from src.infrastructure.database.repositories.base_repository_impl import (
    BaseRepositoryImpl,
)
from src.infrastructure.database.repositories.pattern_detection_repository import (
    PatternDetectionRepository,
)

logger = logging.getLogger(__name__)


class PatternDetectionRepositoryImpl(BaseRepositoryImpl, PatternDetectionRepository):
    """
    パターン検出リポジトリ実装

    責任:
    - パターン検出結果の永続化
    - パターン検出結果の取得・検索
    - 通知状態管理
    - 信頼度別管理

    特徴:
    - USD/JPY特化設計
    - 6パターン対応
    - 通知重複防止
    - 信頼度管理
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def save(self, pattern: PatternDetectionModel) -> PatternDetectionModel:
        """
        パターン検出結果を保存

        Args:
            pattern: 保存するパターン検出結果

        Returns:
            PatternDetectionModel: 保存されたパターン検出結果
        """
        try:
            # バリデーション
            if not pattern.validate():
                raise ValueError("Invalid pattern detection")

            # 重複チェック
            existing = await self.find_by_timestamp_and_type(
                pattern.timestamp,
                pattern.pattern_type,
                pattern.currency_pair,
            )
            if existing:
                logger.warning(
                    f"Pattern detection already exists for {pattern.currency_pair} "
                    f"{pattern.pattern_type} at {pattern.timestamp}"
                )
                return existing

            # 保存
            saved_pattern = await super().save(pattern)
            logger.info(
                f"Saved pattern detection {saved_pattern.pattern_type} "
                f"for {saved_pattern.currency_pair} at {saved_pattern.timestamp}"
            )
            return saved_pattern

        except Exception as e:
            logger.error(f"Error saving pattern detection: {e}")
            raise

    async def save_batch(
        self, pattern_list: List[PatternDetectionModel]
    ) -> List[PatternDetectionModel]:
        """
        パターン検出結果をバッチ保存

        Args:
            pattern_list: 保存するパターン検出結果リスト

        Returns:
            List[PatternDetectionModel]: 保存されたパターン検出結果リスト
        """
        try:
            saved_patterns = []
            for pattern in pattern_list:
                if pattern.validate():
                    saved_pattern = await self.save(pattern)
                    saved_patterns.append(saved_pattern)
                else:
                    logger.warning(f"Invalid pattern detection skipped: {pattern}")

            logger.info(f"Saved {len(saved_patterns)} pattern detections")
            return saved_patterns

        except Exception as e:
            logger.error(f"Error saving pattern detections batch: {e}")
            raise

    async def find_by_id(self, id: int) -> Optional[PatternDetectionModel]:
        """
        IDでパターン検出結果を取得

        Args:
            id: パターン検出結果ID

        Returns:
            Optional[PatternDetectionModel]: パターン検出結果（存在しない場合はNone）
        """
        try:
            return await super().get_by_id(id)
        except Exception as e:
            logger.error(f"Error finding pattern detection by ID {id}: {e}")
            return None

    async def find_by_timestamp_and_type(
        self,
        timestamp: datetime,
        pattern_type: str,
        currency_pair: str = "USD/JPY",
    ) -> Optional[PatternDetectionModel]:
        """
        タイムスタンプ・パターンタイプでパターン検出結果を取得

        Args:
            timestamp: タイムスタンプ
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            Optional[PatternDetectionModel]: パターン検出結果（存在しない場合はNone）
        """
        try:
            query = select(PatternDetectionModel).where(
                and_(
                    PatternDetectionModel.timestamp == timestamp,
                    PatternDetectionModel.pattern_type == pattern_type,
                    PatternDetectionModel.currency_pair == currency_pair,
                )
            )
            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error finding pattern detection by timestamp and type: {e}")
            return None

    async def find_latest_by_type(
        self,
        pattern_type: str,
        currency_pair: str = "USD/JPY",
        limit: int = 1,
    ) -> List[PatternDetectionModel]:
        """
        パターンタイプで最新のパターン検出結果を取得

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数（デフォルト: 1）

        Returns:
            List[PatternDetectionModel]: 最新のパターン検出結果リスト
        """
        try:
            query = (
                select(PatternDetectionModel)
                .where(
                    and_(
                        PatternDetectionModel.pattern_type == pattern_type,
                        PatternDetectionModel.currency_pair == currency_pair,
                    )
                )
                .order_by(PatternDetectionModel.timestamp.desc())
                .limit(limit)
            )
            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding latest pattern detections by type: {e}")
            return []

    async def find_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        日付範囲でパターン検出結果を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        try:
            conditions = [
                PatternDetectionModel.timestamp >= start_date,
                PatternDetectionModel.timestamp <= end_date,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding pattern detections by date range: {e}")
            return []

    async def find_by_confidence_range(
        self,
        min_confidence: float,
        max_confidence: float,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        信頼度範囲でパターン検出結果を取得

        Args:
            min_confidence: 最小信頼度
            max_confidence: 最大信頼度
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        try:
            conditions = [
                PatternDetectionModel.confidence_score >= min_confidence,
                PatternDetectionModel.confidence_score <= max_confidence,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            if start_date:
                conditions.append(PatternDetectionModel.timestamp >= start_date)

            if end_date:
                conditions.append(PatternDetectionModel.timestamp <= end_date)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.confidence_score.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding pattern detections by confidence range: {e}")
            return []

    async def find_by_direction(
        self,
        direction: str,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        方向でパターン検出結果を取得

        Args:
            direction: 検出方向（BUY/SELL）
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        try:
            conditions = [
                PatternDetectionModel.direction == direction,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            if start_date:
                conditions.append(PatternDetectionModel.timestamp >= start_date)

            if end_date:
                conditions.append(PatternDetectionModel.timestamp <= end_date)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding pattern detections by direction: {e}")
            return []

    async def find_unnotified_patterns(
        self,
        currency_pair: str = "USD/JPY",
        pattern_type: Optional[str] = None,
        min_confidence: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        未通知のパターン検出結果を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            pattern_type: パターンタイプ（デフォルト: None）
            min_confidence: 最小信頼度（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 未通知のパターン検出結果リスト
        """
        try:
            conditions = [
                PatternDetectionModel.notification_sent.is_(False),
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            if min_confidence:
                conditions.append(
                    PatternDetectionModel.confidence_score >= min_confidence
                )

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding unnotified patterns: {e}")
            return []

    async def find_recent_notifications(
        self,
        hours: int = 1,
        currency_pair: str = "USD/JPY",
        pattern_type: Optional[str] = None,
    ) -> List[PatternDetectionModel]:
        """
        最近の通知済みパターンを取得（重複通知防止用）

        Args:
            hours: 時間範囲（デフォルト: 1）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            pattern_type: パターンタイプ（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 最近の通知済みパターンリスト
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)

            conditions = [
                PatternDetectionModel.notification_sent.is_(True),
                PatternDetectionModel.notification_sent_at >= cutoff_time,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.notification_sent_at.desc())
            )

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding recent notifications: {e}")
            return []

    async def count_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータ数を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: データ数
        """
        try:
            conditions = [
                PatternDetectionModel.timestamp >= start_date,
                PatternDetectionModel.timestamp <= end_date,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            query = select(func.count(PatternDetectionModel.id)).where(
                and_(*conditions)
            )
            result = await self.session.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Error counting pattern detections by date range: {e}")
            return 0

    async def get_pattern_statistics(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> dict:
        """
        パターン統計情報を取得

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            dict: 統計情報（パターン別件数、平均信頼度等）
        """
        try:
            conditions = [
                PatternDetectionModel.timestamp >= start_date,
                PatternDetectionModel.timestamp <= end_date,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            # 基本統計
            count_query = select(func.count(PatternDetectionModel.id)).where(
                and_(*conditions)
            )
            count_result = await self.session.execute(count_query)
            total_count = count_result.scalar()

            # 平均信頼度
            avg_confidence_query = select(
                func.avg(PatternDetectionModel.confidence_score)
            ).where(and_(*conditions))
            avg_result = await self.session.execute(avg_confidence_query)
            avg_confidence = avg_result.scalar()

            # パターン別統計
            pattern_stats_query = (
                select(
                    PatternDetectionModel.pattern_type,
                    func.count(PatternDetectionModel.id).label("count"),
                    func.avg(PatternDetectionModel.confidence_score).label(
                        "avg_confidence"
                    ),
                )
                .where(and_(*conditions))
                .group_by(PatternDetectionModel.pattern_type)
            )
            pattern_result = await self.session.execute(pattern_stats_query)
            pattern_stats = pattern_result.all()

            # 方向別統計
            direction_stats_query = (
                select(
                    PatternDetectionModel.direction,
                    func.count(PatternDetectionModel.id).label("count"),
                )
                .where(and_(*conditions))
                .group_by(PatternDetectionModel.direction)
            )
            direction_result = await self.session.execute(direction_stats_query)
            direction_stats = direction_result.all()

            return {
                "total_count": total_count,
                "avg_confidence": (float(avg_confidence) if avg_confidence else 0.0),
                "pattern_stats": [
                    {
                        "pattern_type": stat.pattern_type,
                        "count": stat.count,
                        "avg_confidence": (
                            float(stat.avg_confidence) if stat.avg_confidence else 0.0
                        ),
                    }
                    for stat in pattern_stats
                ],
                "direction_stats": [
                    {
                        "direction": stat.direction,
                        "count": stat.count,
                    }
                    for stat in direction_stats
                ],
            }

        except Exception as e:
            logger.error(f"Error getting pattern statistics: {e}")
            return {
                "total_count": 0,
                "avg_confidence": 0.0,
                "pattern_stats": [],
                "direction_stats": [],
            }

    async def delete_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        日付範囲のデータを削除

        Args:
            start_date: 開始日時
            end_date: 終了日時
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        try:
            conditions = [
                PatternDetectionModel.timestamp >= start_date,
                PatternDetectionModel.timestamp <= end_date,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            # 削除前に件数を取得
            count_query = select(func.count(PatternDetectionModel.id)).where(
                and_(*conditions)
            )
            count_result = await self.session.execute(count_query)
            delete_count = count_result.scalar()

            # 削除実行
            delete_query = delete(PatternDetectionModel).where(and_(*conditions))
            await self.session.execute(delete_query)

            logger.info(f"Deleted {delete_count} pattern detections")
            return delete_count

        except Exception as e:
            logger.error(f"Error deleting pattern detections by date range: {e}")
            return 0

    async def delete_old_data(
        self,
        days_to_keep: int = 365,
        pattern_type: Optional[str] = None,
        currency_pair: str = "USD/JPY",
    ) -> int:
        """
        古いデータを削除

        Args:
            days_to_keep: 保持する日数（デフォルト: 365）
            pattern_type: パターンタイプ（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            int: 削除されたデータ数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            conditions = [
                PatternDetectionModel.timestamp < cutoff_date,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if pattern_type:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            # 削除前に件数を取得
            count_query = select(func.count(PatternDetectionModel.id)).where(
                and_(*conditions)
            )
            count_result = await self.session.execute(count_query)
            delete_count = count_result.scalar()

            # 削除実行
            delete_query = delete(PatternDetectionModel).where(and_(*conditions))
            await self.session.execute(delete_query)

            logger.info(f"Deleted {delete_count} old pattern detections")
            return delete_count

        except Exception as e:
            logger.error(f"Error deleting old pattern detections: {e}")
            return 0

    async def exists_by_timestamp_and_type(
        self,
        timestamp: datetime,
        pattern_type: str,
        currency_pair: str = "USD/JPY",
    ) -> bool:
        """
        タイムスタンプ・パターンタイプのデータが存在するかチェック

        Args:
            timestamp: タイムスタンプ
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            bool: 存在する場合True
        """
        try:
            query = select(func.count(PatternDetectionModel.id)).where(
                and_(
                    PatternDetectionModel.timestamp == timestamp,
                    PatternDetectionModel.pattern_type == pattern_type,
                    PatternDetectionModel.currency_pair == currency_pair,
                )
            )
            result = await self.session.execute(query)
            return result.scalar() > 0

        except Exception as e:
            logger.error(f"Error checking pattern detection existence: {e}")
            return False

    async def get_pattern_types(self, currency_pair: str = "USD/JPY") -> List[str]:
        """
        パターンタイプ一覧を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）

        Returns:
            List[str]: パターンタイプ一覧
        """
        try:
            query = (
                select(PatternDetectionModel.pattern_type)
                .where(PatternDetectionModel.currency_pair == currency_pair)
                .distinct()
            )
            result = await self.session.execute(query)
            return [row.pattern_type for row in result.scalars()]

        except Exception as e:
            logger.error(f"Error getting pattern types: {e}")
            return []

    async def find_by_pattern_type(
        self,
        pattern_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        currency_pair: str = "USD/JPY",
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        パターンタイプでパターン検出結果を取得

        Args:
            pattern_type: パターンタイプ
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: パターン検出結果リスト
        """
        try:
            conditions = [
                PatternDetectionModel.pattern_type == pattern_type,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if start_date:
                conditions.append(PatternDetectionModel.timestamp >= start_date)

            if end_date:
                conditions.append(PatternDetectionModel.timestamp <= end_date)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.timestamp.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error finding pattern detections by pattern type: {e}")
            return []

    async def mark_notification_sent(
        self,
        pattern_id: int,
        message: Optional[str] = None,
    ) -> bool:
        """
        通知送信済みとしてマーク

        Args:
            pattern_id: パターン検出結果ID
            message: 通知メッセージ（デフォルト: None）

        Returns:
            bool: 更新成功の場合True
        """
        try:
            pattern = await self.find_by_id(pattern_id)
            if not pattern:
                logger.warning(f"Pattern detection not found: {pattern_id}")
                return False

            pattern.notification_sent = True
            pattern.notification_sent_at = datetime.now()
            if message:
                pattern.notification_message = message

            await self.session.commit()
            logger.info(f"Marked pattern detection {pattern_id} as notified")
            return True

        except Exception as e:
            logger.error(f"Error marking pattern detection as notified: {e}")
            return False

    async def get_high_confidence_patterns(
        self,
        min_confidence: float = 70.0,
        currency_pair: str = "USD/JPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> List[PatternDetectionModel]:
        """
        高信頼度パターンを取得

        Args:
            min_confidence: 最小信頼度（デフォルト: 70.0）
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）
            limit: 取得件数制限（デフォルト: None）

        Returns:
            List[PatternDetectionModel]: 高信頼度パターンリスト
        """
        try:
            conditions = [
                PatternDetectionModel.confidence_score >= min_confidence,
                PatternDetectionModel.currency_pair == currency_pair,
            ]

            if start_date:
                conditions.append(PatternDetectionModel.timestamp >= start_date)

            if end_date:
                conditions.append(PatternDetectionModel.timestamp <= end_date)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.confidence_score.desc())
            )

            if limit:
                query = query.limit(limit)

            result = await self.session.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Error getting high confidence patterns: {e}")
            return []

    async def find_latest(
        self,
        currency_pair: str = "USD/JPY",
        pattern_type: Optional[str] = None,
        limit: int = 10,
    ) -> List[PatternDetectionModel]:
        """
        最新のパターン検出結果を取得

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            pattern_type: パターンタイプ（デフォルト: None）
            limit: 取得件数制限（デフォルト: 10）

        Returns:
            List[PatternDetectionModel]: 最新のパターン検出結果リスト
        """
        try:
            conditions = [PatternDetectionModel.currency_pair == currency_pair]

            if pattern_type is not None:
                conditions.append(PatternDetectionModel.pattern_type == pattern_type)

            query = (
                select(PatternDetectionModel)
                .where(and_(*conditions))
                .order_by(PatternDetectionModel.timestamp.desc())
                .limit(limit)
            )

            result = await self.session.execute(query)
            patterns = result.scalars().all()

            logger.info(
                f"Found {len(patterns)} latest patterns for {currency_pair}"
                f"{f' type {pattern_type}' if pattern_type else ''}"
            )

            return list(patterns)

        except Exception as e:
            logger.error(f"Error finding latest patterns: {e}")
            return []

    async def find_recent_duplicate(
        self,
        currency_pair: str,
        pattern_type: str,
        timestamp: datetime,
        hours: int = 1,
    ) -> Optional[PatternDetectionModel]:
        """
        最近の重複パターンを検索

        Args:
            currency_pair: 通貨ペア
            pattern_type: パターンタイプ
            timestamp: タイムスタンプ
            hours: 検索時間範囲（時間）

        Returns:
            Optional[PatternDetectionModel]: 重複パターン（存在しない場合はNone）
        """
        try:
            start_time = timestamp - timedelta(hours=hours)
            end_time = timestamp + timedelta(hours=hours)

            query = select(PatternDetectionModel).where(
                and_(
                    PatternDetectionModel.currency_pair == currency_pair,
                    PatternDetectionModel.pattern_type == pattern_type,
                    PatternDetectionModel.timestamp >= start_time,
                    PatternDetectionModel.timestamp <= end_time,
                )
            )

            result = await self.session.execute(query)
            duplicate = result.scalar_one_or_none()

            if duplicate:
                logger.info(
                    f"Found duplicate pattern: {pattern_type} for {currency_pair}"
                    f" at {timestamp}"
                )

            return duplicate

        except Exception as e:
            logger.error(f"Error finding recent duplicate: {e}")
            return None
