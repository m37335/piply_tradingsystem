"""
データクリーンアップサービス

USD/JPY特化のデータクリーンアップサービス
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime, timedelta
from typing import Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.repositories.data_fetch_history_repository_impl import (
    DataFetchHistoryRepositoryImpl,
)
from src.infrastructure.database.repositories.pattern_detection_repository_impl import (
    PatternDetectionRepositoryImpl,
)
from src.infrastructure.database.repositories.price_data_repository_impl import (
    PriceDataRepositoryImpl,
)
from src.infrastructure.database.repositories.technical_indicator_repository_impl import (
    TechnicalIndicatorRepositoryImpl,
)
from src.infrastructure.database.services.system_config_service import (
    SystemConfigService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DataCleanupService:
    """
    データクリーンアップサービス

    責任:
    - 古いデータの自動削除
    - 設定可能な保持期間
    - 削除履歴の記録
    - 削除統計の管理

    特徴:
    - USD/JPY特化設計
    - 設定可能な保持期間
    - 安全な削除処理
    - 詳細な統計管理
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session

        # リポジトリ初期化
        self.price_repo = PriceDataRepositoryImpl(session)
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)
        self.pattern_repo = PatternDetectionRepositoryImpl(session)
        self.fetch_history_repo = DataFetchHistoryRepositoryImpl(session)

        # 設定サービス
        self.config_service = SystemConfigService(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"

        # デフォルト保持期間
        self.default_retention_days = {
            "price_data": 90,
            "technical_indicators": 90,
            "pattern_detections": 30,
            "data_fetch_history": 7,
        }

        logger.info("Initialized DataCleanupService")

    async def cleanup_all_data(self, dry_run: bool = True) -> Dict[str, int]:
        """
        全データのクリーンアップを実行

        Args:
            dry_run: ドライラン実行フラグ（デフォルト: True）

        Returns:
            Dict[str, int]: 削除されたデータ数の辞書
        """
        try:
            logger.info(f"Starting data cleanup (dry_run: {dry_run})")

            # 保持期間を取得
            retention_days = await self._get_retention_days()

            results = {}

            # 1. 価格データのクリーンアップ
            logger.info("Cleaning up price data...")
            price_deleted = await self._cleanup_price_data(
                retention_days["price_data"], dry_run
            )
            results["price_data"] = price_deleted

            # 2. テクニカル指標のクリーンアップ
            logger.info("Cleaning up technical indicators...")
            indicator_deleted = await self._cleanup_technical_indicators(
                retention_days["technical_indicators"], dry_run
            )
            results["technical_indicators"] = indicator_deleted

            # 3. パターン検出結果のクリーンアップ
            logger.info("Cleaning up pattern detections...")
            pattern_deleted = await self._cleanup_pattern_detections(
                retention_days["pattern_detections"], dry_run
            )
            results["pattern_detections"] = pattern_deleted

            # 4. データ取得履歴のクリーンアップ
            logger.info("Cleaning up data fetch history...")
            history_deleted = await self._cleanup_data_fetch_history(
                retention_days["data_fetch_history"], dry_run
            )
            results["data_fetch_history"] = history_deleted

            total_deleted = sum(results.values())
            logger.info(
                f"Data cleanup completed: {total_deleted} total records "
                f"(dry_run: {dry_run})"
            )

            return results

        except Exception as e:
            logger.error(f"Error in data cleanup: {e}")
            raise

    async def _cleanup_price_data(self, retention_days: int, dry_run: bool) -> int:
        """
        価格データのクリーンアップ

        Args:
            retention_days: 保持期間（日）
            dry_run: ドライラン実行フラグ

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            if dry_run:
                # 削除対象件数をカウント
                count = await self.price_repo.count_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(
                    f"Would delete {count} price data records "
                    f"(older than {cutoff_date})"
                )
                return count
            else:
                # 実際に削除
                deleted_count = await self.price_repo.delete_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(f"Deleted {deleted_count} price data records")
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up price data: {e}")
            return 0

    async def _cleanup_technical_indicators(
        self, retention_days: int, dry_run: bool
    ) -> int:
        """
        テクニカル指標のクリーンアップ

        Args:
            retention_days: 保持期間（日）
            dry_run: ドライラン実行フラグ

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            if dry_run:
                # 削除対象件数をカウント
                count = await self.indicator_repo.count_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(
                    f"Would delete {count} technical indicator records "
                    f"(older than {cutoff_date})"
                )
                return count
            else:
                # 実際に削除
                deleted_count = await self.indicator_repo.delete_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(f"Deleted {deleted_count} technical indicator records")
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up technical indicators: {e}")
            return 0

    async def _cleanup_pattern_detections(
        self, retention_days: int, dry_run: bool
    ) -> int:
        """
        パターン検出結果のクリーンアップ

        Args:
            retention_days: 保持期間（日）
            dry_run: ドライラン実行フラグ

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            if dry_run:
                # 削除対象件数をカウント
                count = await self.pattern_repo.count_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(
                    f"Would delete {count} pattern detection records "
                    f"(older than {cutoff_date})"
                )
                return count
            else:
                # 実際に削除
                deleted_count = await self.pattern_repo.delete_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(f"Deleted {deleted_count} pattern detection records")
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up pattern detections: {e}")
            return 0

    async def _cleanup_data_fetch_history(
        self, retention_days: int, dry_run: bool
    ) -> int:
        """
        データ取得履歴のクリーンアップ

        Args:
            retention_days: 保持期間（日）
            dry_run: ドライラン実行フラグ

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=retention_days)

            if dry_run:
                # 削除対象件数をカウント
                count = await self.fetch_history_repo.count_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(
                    f"Would delete {count} data fetch history records "
                    f"(older than {cutoff_date})"
                )
                return count
            else:
                # 実際に削除
                deleted_count = await self.fetch_history_repo.delete_old_data(
                    cutoff_date, self.currency_pair
                )
                logger.info(f"Deleted {deleted_count} data fetch history records")
                return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up data fetch history: {e}")
            return 0

    async def _get_retention_days(self) -> Dict[str, int]:
        """
        保持期間を取得

        Returns:
            Dict[str, int]: 保持期間の辞書
        """
        try:
            # 設定から保持期間を取得
            retention_days = await self.config_service.get_config("data_retention_days")

            return {
                "price_data": retention_days,
                "technical_indicators": retention_days,
                "pattern_detections": retention_days // 3,  # パターンは短め
                "data_fetch_history": retention_days // 12,  # 履歴はさらに短め
            }

        except Exception as e:
            logger.warning(f"Error getting retention days, using defaults: {e}")
            return self.default_retention_days

    async def get_data_statistics(self) -> Dict[str, Dict]:
        """
        データ統計を取得

        Returns:
            Dict[str, Dict]: データ統計の辞書
        """
        try:
            logger.info("Getting data statistics...")

            stats = {}

            # 価格データ統計
            price_stats = await self._get_price_data_stats()
            stats["price_data"] = price_stats

            # テクニカル指標統計
            indicator_stats = await self._get_indicator_stats()
            stats["technical_indicators"] = indicator_stats

            # パターン検出統計
            pattern_stats = await self._get_pattern_stats()
            stats["pattern_detections"] = pattern_stats

            # データ取得履歴統計
            history_stats = await self._get_history_stats()
            stats["data_fetch_history"] = history_stats

            logger.info("Data statistics retrieved successfully")
            return stats

        except Exception as e:
            logger.error(f"Error getting data statistics: {e}")
            raise

    async def _get_price_data_stats(self) -> Dict:
        """
        価格データ統計を取得

        Returns:
            Dict: 価格データ統計
        """
        try:
            total_count = await self.price_repo.count_by_currency_pair(
                self.currency_pair
            )
            latest_record = await self.price_repo.find_latest_by_currency_pair(
                self.currency_pair
            )

            return {
                "total_records": total_count,
                "latest_timestamp": latest_record.timestamp if latest_record else None,
                "currency_pair": self.currency_pair,
            }

        except Exception as e:
            logger.error(f"Error getting price data stats: {e}")
            return {"total_records": 0, "latest_timestamp": None}

    async def _get_indicator_stats(self) -> Dict:
        """
        テクニカル指標統計を取得

        Returns:
            Dict: テクニカル指標統計
        """
        try:
            total_count = await self.indicator_repo.count_by_currency_pair(
                self.currency_pair
            )
            latest_record = await self.indicator_repo.find_latest_by_currency_pair(
                self.currency_pair
            )

            return {
                "total_records": total_count,
                "latest_timestamp": latest_record.timestamp if latest_record else None,
                "currency_pair": self.currency_pair,
            }

        except Exception as e:
            logger.error(f"Error getting indicator stats: {e}")
            return {"total_records": 0, "latest_timestamp": None}

    async def _get_pattern_stats(self) -> Dict:
        """
        パターン検出統計を取得

        Returns:
            Dict: パターン検出統計
        """
        try:
            total_count = await self.pattern_repo.count_by_currency_pair(
                self.currency_pair
            )
            latest_record = await self.pattern_repo.find_latest_by_currency_pair(
                self.currency_pair
            )

            return {
                "total_records": total_count,
                "latest_timestamp": latest_record.detection_time
                if latest_record
                else None,
                "currency_pair": self.currency_pair,
            }

        except Exception as e:
            logger.error(f"Error getting pattern stats: {e}")
            return {"total_records": 0, "latest_timestamp": None}

    async def _get_history_stats(self) -> Dict:
        """
        データ取得履歴統計を取得

        Returns:
            Dict: データ取得履歴統計
        """
        try:
            total_count = await self.fetch_history_repo.count_by_currency_pair(
                self.currency_pair
            )
            latest_record = await self.fetch_history_repo.find_latest_by_currency_pair(
                self.currency_pair
            )

            return {
                "total_records": total_count,
                "latest_timestamp": latest_record.fetch_time if latest_record else None,
                "currency_pair": self.currency_pair,
            }

        except Exception as e:
            logger.error(f"Error getting history stats: {e}")
            return {"total_records": 0, "latest_timestamp": None}

    async def estimate_cleanup_impact(self) -> Dict[str, Dict]:
        """
        クリーンアップの影響を推定

        Returns:
            Dict[str, Dict]: 影響推定結果
        """
        try:
            logger.info("Estimating cleanup impact...")

            retention_days = await self._get_retention_days()
            impact = {}

            for data_type, days in retention_days.items():
                cutoff_date = datetime.now() - timedelta(days=days)

                if data_type == "price_data":
                    count = await self.price_repo.count_old_data(
                        cutoff_date, self.currency_pair
                    )
                elif data_type == "technical_indicators":
                    count = await self.indicator_repo.count_old_data(
                        cutoff_date, self.currency_pair
                    )
                elif data_type == "pattern_detections":
                    count = await self.pattern_repo.count_old_data(
                        cutoff_date, self.currency_pair
                    )
                elif data_type == "data_fetch_history":
                    count = await self.fetch_history_repo.count_old_data(
                        cutoff_date, self.currency_pair
                    )
                else:
                    count = 0

                impact[data_type] = {
                    "records_to_delete": count,
                    "retention_days": days,
                    "cutoff_date": cutoff_date.isoformat(),
                }

            logger.info("Cleanup impact estimation completed")
            return impact

        except Exception as e:
            logger.error(f"Error estimating cleanup impact: {e}")
            raise
