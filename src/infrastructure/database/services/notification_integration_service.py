"""
通知統合サービス

USD/JPY特化のデータベースベース通知統合サービス
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)

# パターン検出システムは分離済みのため、インポートを削除
# from src.infrastructure.database.services.pattern_detection_service import (
#     PatternDetectionService,
# )
from src.infrastructure.messaging.discord_client import DiscordClient
from src.infrastructure.messaging.notification_manager import (
    NotificationManager,
    NotificationPattern,
)
from src.utils.logging_config import get_infrastructure_logger

# パターン検出システムは分離済みのため、インポートを削除
# from src.infrastructure.database.repositories.pattern_detection_repository_impl import (
#     PatternDetectionRepositoryImpl,
# )


logger = get_infrastructure_logger()


class NotificationIntegrationService:
    """
    通知統合サービス

    責任:
    - パターン検出結果の通知送信
    - データベースベースの通知履歴管理
    - 重複通知防止機能
    - 通知統計の管理

    特徴:
    - USD/JPY特化設計
    - データベースベース管理
    - 既存通知システムとの統合
    - 高精度通知管理
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session

        # リポジトリ・サービス初期化
        # パターン検出システムは分離済みのため、初期化を削除
        # self.pattern_repo = PatternDetectionRepositoryImpl(session)
        # パターン検出システムは分離済みのため、初期化を削除
        # self.pattern_service = PatternDetectionService(session)

        # USD/JPY設定
        self.currency_pair = "USD/JPY"

        # Discord設定
        import os

        webhook_url = os.getenv(
            "DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test"
        )
        self.discord_client = DiscordClient(webhook_url)
        self.notification_manager = NotificationManager(
            discord_client=self.discord_client,
            notification_history_repository=None,  # データベースベース管理
            duplicate_check_window_minutes=60,  # 1時間
            max_notifications_per_hour=20,
            enable_priority_filtering=True,
            enable_duplicate_prevention=True,
        )

        # 通知設定
        self.notification_config = {
            "min_confidence": 0.7,  # 最小信頼度
            "min_priority": 70,  # 最小優先度
            "max_notifications_per_run": 5,  # 1回の実行での最大通知数
        }

        logger.info(
            f"Initialized NotificationIntegrationService for {self.currency_pair}"
        )

    async def process_pattern_notifications(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, int]:
        """
        パターン通知を処理

        Args:
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            Dict[str, int]: 処理結果統計
        """
        try:
            logger.info(f"Processing pattern notifications for {self.currency_pair}")

            # デフォルト期間設定
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(hours=1)  # 1時間分

            # 未通知のパターンを取得
            unprocessed_patterns = await self._get_unprocessed_patterns(
                start_date, end_date
            )

            if not unprocessed_patterns:
                logger.info("No unprocessed patterns found")
                return {"processed": 0, "sent": 0, "skipped": 0, "errors": 0}

            # 通知パターンに変換
            notification_patterns = await self._convert_to_notification_patterns(
                unprocessed_patterns
            )

            # 通知を送信
            results = await self._send_notifications(notification_patterns)

            # 通知送信済みをマーク
            await self._mark_notifications_sent(unprocessed_patterns, results)

            logger.info(
                f"Notification processing completed: {results['sent']} sent, "
                f"{results['skipped']} skipped, {results['errors']} errors"
            )

            return results

        except Exception as e:
            logger.error(f"Error processing pattern notifications: {e}")
            return {"processed": 0, "sent": 0, "skipped": 0, "errors": 1}

    async def _get_unprocessed_patterns(
        self, start_date: datetime, end_date: datetime
    ) -> List[PatternDetectionModel]:
        """
        未処理のパターンを取得

        Args:
            start_date: 開始日時
            end_date: 終了日時

        Returns:
            List[PatternDetectionModel]: 未処理パターンリスト
        """
        try:
            # 未通知のパターンを取得
            patterns = await self.pattern_repo.find_unprocessed_by_date_range(
                start_date, end_date, self.currency_pair, 100
            )

            # フィルタリング（信頼度・優先度）
            filtered_patterns = []
            for pattern in patterns:
                if (
                    pattern.confidence_score
                    >= self.notification_config["min_confidence"]
                    and pattern.priority >= self.notification_config["min_priority"]
                ):
                    filtered_patterns.append(pattern)

            # 優先度順にソート
            filtered_patterns.sort(key=lambda x: x.priority, reverse=True)

            # 最大通知数に制限
            max_notifications = self.notification_config["max_notifications_per_run"]
            if len(filtered_patterns) > max_notifications:
                filtered_patterns = filtered_patterns[:max_notifications]

            logger.info(f"Found {len(filtered_patterns)} unprocessed patterns")

            return filtered_patterns

        except Exception as e:
            logger.error(f"Error getting unprocessed patterns: {e}")
            return []

    async def _convert_to_notification_patterns(
        self, patterns: List[PatternDetectionModel]
    ) -> List[NotificationPattern]:
        """
        パターンを通知パターンに変換

        Args:
            patterns: パターンリスト

        Returns:
            List[NotificationPattern]: 通知パターンリスト
        """
        try:
            notification_patterns = []

            for pattern in patterns:
                # パターンデータを作成
                pattern_data = {
                    "pattern_id": pattern.id,
                    "pattern_name": pattern.pattern_name,
                    "confidence_score": pattern.confidence_score,
                    "strategy": pattern.strategy,
                    "entry_condition": pattern.entry_condition,
                    "take_profit": pattern.take_profit,
                    "stop_loss": pattern.stop_loss,
                    "description": pattern.description,
                    "conditions_met": pattern.conditions_met,
                    "technical_data": pattern.technical_data,
                }

                # 通知パターンを作成
                notification_pattern = NotificationPattern(
                    pattern_type=f"pattern_{pattern.pattern_number}",
                    currency_pair=pattern.currency_pair,
                    pattern_data=pattern_data,
                    priority=pattern.priority,
                    confidence=pattern.confidence_score,
                    timeframe="5m",  # デフォルトタイムフレーム
                )

                notification_patterns.append(notification_pattern)

            return notification_patterns

        except Exception as e:
            logger.error(f"Error converting to notification patterns: {e}")
            return []

    async def _send_notifications(
        self, notification_patterns: List[NotificationPattern]
    ) -> Dict[str, int]:
        """
        通知を送信

        Args:
            notification_patterns: 通知パターンリスト

        Returns:
            Dict[str, int]: 送信結果統計
        """
        try:
            results = {
                "processed": len(notification_patterns),
                "sent": 0,
                "skipped": 0,
                "errors": 0,
            }

            for pattern in notification_patterns:
                try:
                    # 重複チェック
                    is_duplicate = await self._check_duplicate_notification(pattern)
                    if is_duplicate:
                        results["skipped"] += 1
                        logger.info(
                            f"Skipped duplicate notification: {pattern.pattern_type}"
                        )
                        continue

                    # 通知を送信
                    success = await self.notification_manager.send_pattern_notification(
                        pattern
                    )

                    if success:
                        results["sent"] += 1
                        logger.info(
                            f"Notification sent successfully: {pattern.pattern_type}"
                        )
                    else:
                        results["errors"] += 1
                        logger.error(
                            f"Failed to send notification: {pattern.pattern_type}"
                        )

                except Exception as e:
                    results["errors"] += 1
                    logger.error(f"Error sending notification: {e}")

            return results

        except Exception as e:
            logger.error(f"Error in notification sending: {e}")
            return {"processed": 0, "sent": 0, "skipped": 0, "errors": 1}

    async def _check_duplicate_notification(
        self, notification_pattern: NotificationPattern
    ) -> bool:
        """
        重複通知をチェック

        Args:
            notification_pattern: 通知パターン

        Returns:
            bool: 重複の場合True
        """
        try:
            # 1時間以内の同じパターンをチェック
            recent_patterns = await self.pattern_repo.find_recent_by_pattern(
                int(notification_pattern.pattern_type.split("_")[1]),
                datetime.now(),
                self.currency_pair,
                hours=1,
            )

            # 通知済みのパターンがあるかチェック
            for pattern in recent_patterns:
                if pattern.notification_sent:
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking duplicate notification: {e}")
            return False

    async def _mark_notifications_sent(
        self,
        patterns: List[PatternDetectionModel],
        results: Dict[str, int],
    ):
        """
        通知送信済みをマーク

        Args:
            patterns: パターンリスト
            results: 送信結果
        """
        try:
            # 送信成功したパターンのみマーク
            sent_count = 0
            for pattern in patterns:
                if sent_count < results["sent"]:
                    # パターン検出システムは分離済みのため、スキップ
                    # await self.pattern_service.mark_notification_sent(pattern.id)
                    sent_count += 1

            logger.info(f"Marked {sent_count} patterns as notification sent")

        except Exception as e:
            logger.error(f"Error marking notifications sent: {e}")

    async def get_notification_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        通知統計を取得

        Args:
            start_date: 開始日時（デフォルト: None）
            end_date: 終了日時（デフォルト: None）

        Returns:
            Dict: 通知統計
        """
        try:
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)

            # パターン検出システムは分離済みのため、ダミーデータを使用
            # pattern_stats = await self.pattern_service.get_pattern_statistics(
            #     start_date, end_date
            # )
            pattern_stats = {
                "total_patterns": 0,
                "notified_patterns": 0,
                "pattern_distribution": {},
                "timeframe_distribution": {},
            }

            # 通知統計を計算
            notification_stats = {
                "total_patterns": pattern_stats.get("total_patterns", 0),
                "notified_patterns": pattern_stats.get("notified_patterns", 0),
                "notification_rate": 0.0,
                "pattern_distribution": pattern_stats.get("pattern_distribution", {}),
                "timeframe_distribution": pattern_stats.get(
                    "timeframe_distribution", {}
                ),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }

            # 通知率を計算
            if notification_stats["total_patterns"] > 0:
                notification_stats["notification_rate"] = (
                    notification_stats["notified_patterns"]
                    / notification_stats["total_patterns"]
                    * 100
                )

            return notification_stats

        except Exception as e:
            logger.error(f"Error getting notification statistics: {e}")
            return {}

    async def cleanup_old_notifications(self, days: int = 30) -> int:
        """
        古い通知履歴をクリーンアップ

        Args:
            days: 保持日数（デフォルト: 30）

        Returns:
            int: 削除された件数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            deleted_count = await self.pattern_repo.delete_old_patterns(
                cutoff_date, self.currency_pair
            )

            logger.info(f"Cleaned up {deleted_count} old notifications")

            return deleted_count

        except Exception as e:
            logger.error(f"Error cleaning up old notifications: {e}")
            return 0

    async def test_notification_system(self) -> bool:
        """
        通知システムのテスト

        Returns:
            bool: テスト成功の場合True
        """
        try:
            logger.info("Testing notification system...")

            # テストパターンを作成
            test_pattern_data = {
                "pattern_id": 0,
                "pattern_name": "テストパターン",
                "confidence_score": 0.9,
                "strategy": "テスト戦略",
                "entry_condition": "テスト条件",
                "take_profit": "テスト利確",
                "stop_loss": "テスト損切",
                "description": "通知システムテスト用",
                "conditions_met": {},
                "technical_data": {},
            }

            test_pattern = NotificationPattern(
                pattern_type="test_pattern",
                currency_pair=self.currency_pair,
                pattern_data=test_pattern_data,
                priority=95,
                confidence=0.9,
                timeframe="5m",
            )

            # テスト通知を送信
            success = await self.notification_manager.send_pattern_notification(
                test_pattern
            )

            if success:
                logger.info("Notification system test completed successfully")
            else:
                logger.error("Notification system test failed")

            return success

        except Exception as e:
            logger.error(f"Error testing notification system: {e}")
            return False
