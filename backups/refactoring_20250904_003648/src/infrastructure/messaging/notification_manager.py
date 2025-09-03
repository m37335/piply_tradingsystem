"""
Notification Manager System
通知管理システム

設計書参照:
- api_optimization_design_2025.md
- notification_implementation_plan_2025.yaml

通知管理システム（重複防止機能付き）
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ...domain.entities.notification_history import NotificationHistory
from ...domain.repositories.notification_history_repository import (
    NotificationHistoryRepository,
)
from ...utils.logging_config import get_infrastructure_logger
from .discord_client import DiscordClient

logger = get_infrastructure_logger()


class NotificationPattern:
    """
    通知パターン

    責任:
    - 通知パターンの定義
    - 優先度管理
    - パターン検証
    """

    def __init__(
        self,
        pattern_type: str,
        currency_pair: str,
        pattern_data: Dict[str, Any],
        priority: int = 50,
        confidence: float = 0.0,
        timeframe: Optional[str] = None,
    ):
        """
        初期化

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            pattern_data: パターンデータ
            priority: 優先度（0-100）
            confidence: 信頼度（0.0-1.0）
            timeframe: 時間軸
        """
        self.pattern_type = pattern_type
        self.currency_pair = currency_pair
        self.pattern_data = pattern_data
        self.priority = max(0, min(100, priority))  # 0-100に制限
        self.confidence = max(0.0, min(1.0, confidence))  # 0.0-1.0に制限
        self.timeframe = timeframe
        self.created_at = datetime.utcnow()

    def get_pattern_key(self) -> str:
        """
        パターンキーを取得

        Returns:
            str: パターンキー
        """
        return f"{self.pattern_type}_{self.currency_pair}_{self.timeframe}"

    def get_priority_score(self) -> float:
        """
        優先度スコアを取得

        Returns:
            float: 優先度スコア
        """
        # 優先度と信頼度を組み合わせたスコア
        return (self.priority * 0.7) + (self.confidence * 100 * 0.3)

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            Dict[str, Any]: 辞書形式のデータ
        """
        return {
            "pattern_type": self.pattern_type,
            "currency_pair": self.currency_pair,
            "pattern_data": self.pattern_data,
            "priority": self.priority,
            "confidence": self.confidence,
            "timeframe": self.timeframe,
            "created_at": self.created_at.isoformat(),
            "priority_score": self.get_priority_score(),
        }


class NotificationManager:
    """
    通知管理システム

    責任:
    - 重複防止機能
    - 通知履歴管理
    - パターン検出統合
    - 統計情報
    """

    def __init__(
        self,
        discord_client: DiscordClient,
        notification_history_repository: NotificationHistoryRepository,
        duplicate_check_window_minutes: int = 30,
        max_notifications_per_hour: int = 10,
        enable_priority_filtering: bool = True,
        enable_duplicate_prevention: bool = True,
    ):
        """
        初期化

        Args:
            discord_client: Discordクライアント
            notification_history_repository: 通知履歴リポジトリ
            duplicate_check_window_minutes: 重複チェックウィンドウ（分）
            max_notifications_per_hour: 1時間あたりの最大通知数
            enable_priority_filtering: 優先度フィルタリングを有効にするか
            enable_duplicate_prevention: 重複防止を有効にするか
        """
        self.discord_client = discord_client
        self.notification_history_repository = notification_history_repository
        self.duplicate_check_window_minutes = duplicate_check_window_minutes
        self.max_notifications_per_hour = max_notifications_per_hour
        self.enable_priority_filtering = enable_priority_filtering
        self.enable_duplicate_prevention = enable_duplicate_prevention

        # 統計情報
        self.total_notifications_sent = 0
        self.duplicate_notifications_blocked = 0
        self.low_priority_notifications_filtered = 0
        self.notification_errors = 0

        # メモリキャッシュ（重複チェック用）
        self._recent_notifications: Set[str] = set()
        self._notification_count_per_hour: Dict[str, int] = {}

        logger.info(
            f"NotificationManager initialized: "
            f"duplicate_window={duplicate_check_window_minutes}min, "
            f"max_per_hour={max_notifications_per_hour}, "
            f"priority_filtering={enable_priority_filtering}, "
            f"duplicate_prevention={enable_duplicate_prevention}"
        )

    def _generate_notification_key(
        self, pattern_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> str:
        """
        通知キーを生成

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸

        Returns:
            str: 通知キー
        """
        return f"{pattern_type}_{currency_pair}_{timeframe or 'default'}"

    def _is_duplicate_notification(
        self, pattern_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> bool:
        """
        重複通知かどうかを判定

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸

        Returns:
            bool: 重複通知の場合True
        """
        if not self.enable_duplicate_prevention:
            return False

        notification_key = self._generate_notification_key(
            pattern_type, currency_pair, timeframe
        )
        return notification_key in self._recent_notifications

    def _add_to_recent_notifications(
        self, pattern_type: str, currency_pair: str, timeframe: Optional[str] = None
    ) -> None:
        """
        最近の通知に追加

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸

        Returns:
            None
        """
        notification_key = self._generate_notification_key(
            pattern_type, currency_pair, timeframe
        )
        self._recent_notifications.add(notification_key)

        # 一定時間後に削除
        asyncio.create_task(self._remove_from_recent_notifications(notification_key))

    async def _remove_from_recent_notifications(self, notification_key: str) -> None:
        """
        最近の通知から削除

        Args:
            notification_key: 通知キー

        Returns:
            None
        """
        await asyncio.sleep(self.duplicate_check_window_minutes * 60)
        self._recent_notifications.discard(notification_key)

    def _is_hourly_limit_exceeded(self, currency_pair: str) -> bool:
        """
        時間制限を超過しているかどうかを判定

        Args:
            currency_pair: 通貨ペア

        Returns:
            bool: 制限超過の場合True
        """
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        hour_key = f"{currency_pair}_{current_hour.isoformat()}"

        count = self._notification_count_per_hour.get(hour_key, 0)
        return count >= self.max_notifications_per_hour

    def _increment_hourly_count(self, currency_pair: str) -> None:
        """
        時間別カウントを増加

        Args:
            currency_pair: 通貨ペア

        Returns:
            None
        """
        current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        hour_key = f"{currency_pair}_{current_hour.isoformat()}"

        self._notification_count_per_hour[hour_key] = (
            self._notification_count_per_hour.get(hour_key, 0) + 1
        )

        # 古いエントリを削除
        cutoff_time = current_hour - timedelta(hours=2)
        old_keys = [
            key
            for key in self._notification_count_per_hour.keys()
            if key.split("_", 1)[1] < cutoff_time.isoformat()
        ]
        for key in old_keys:
            del self._notification_count_per_hour[key]

    async def check_duplicate_notification(
        self,
        pattern_type: str,
        currency_pair: str,
        timeframe: Optional[str] = None,
        hours: int = 1,
    ) -> bool:
        """
        重複通知をチェック（データベース）

        Args:
            pattern_type: パターンタイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸
            hours: チェック時間（時間）

        Returns:
            bool: 重複がある場合True
        """
        try:
            recent_notifications = (
                await self.notification_history_repository.find_recent_by_pattern(
                    pattern_type, currency_pair, hours
                )
            )
            return len(recent_notifications) > 0

        except Exception as e:
            logger.error(f"Failed to check duplicate notification: {str(e)}")
            return False

    async def send_pattern_notification(
        self, notification_pattern: NotificationPattern
    ) -> bool:
        """
        パターン通知を送信

        Args:
            notification_pattern: 通知パターン

        Returns:
            bool: 送信成功の場合True
        """
        try:
            # 重複チェック
            if self._is_duplicate_notification(
                notification_pattern.pattern_type,
                notification_pattern.currency_pair,
                notification_pattern.timeframe,
            ):
                self.duplicate_notifications_blocked += 1
                logger.debug(
                    f"Duplicate notification blocked: "
                    f"{notification_pattern.get_pattern_key()}"
                )
                return False

            # 時間制限チェック
            if self._is_hourly_limit_exceeded(notification_pattern.currency_pair):
                logger.warning(
                    f"Hourly limit exceeded for {notification_pattern.currency_pair}"
                )
                return False

            # 優先度フィルタリング
            if (
                self.enable_priority_filtering
                and notification_pattern.get_priority_score() < 30
            ):
                self.low_priority_notifications_filtered += 1
                logger.debug(
                    f"Low priority notification filtered: "
                    f"{notification_pattern.get_pattern_key()}"
                )
                return False

            # Discord通知を送信
            notification_data = notification_pattern.to_dict()
            discord_message = await self._create_discord_message(notification_data)

            message_id = await self.discord_client.send_rich_embed(
                title=discord_message["title"],
                description=discord_message["description"],
                fields=discord_message.get("fields", []),
                color=discord_message.get("color", 0x00FF00),
            )

            if message_id:
                # 通知履歴を記録
                await self._log_notification(
                    notification_pattern, message_id, notification_data
                )

                # 統計情報を更新
                self.total_notifications_sent += 1
                self._increment_hourly_count(notification_pattern.currency_pair)
                self._add_to_recent_notifications(
                    notification_pattern.pattern_type,
                    notification_pattern.currency_pair,
                    notification_pattern.timeframe,
                )

                logger.info(
                    f"Notification sent successfully: "
                    f"{notification_pattern.get_pattern_key()}, "
                    f"message_id: {message_id}"
                )
                return True
            else:
                self.notification_errors += 1
                logger.error("Failed to send Discord notification")
                return False

        except Exception as e:
            self.notification_errors += 1
            logger.error(f"Failed to send pattern notification: {str(e)}")
            return False

    async def _create_discord_message(
        self, notification_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Discordメッセージを作成

        Args:
            notification_data: 通知データ

        Returns:
            Dict[str, Any]: Discordメッセージ
        """
        pattern_type = notification_data["pattern_type"]
        currency_pair = notification_data["currency_pair"]

        # パターンタイプに基づいてメッセージを作成
        if pattern_type == "trend_reversal":
            return {
                "title": "🔄 トレンド転換シグナル",
                "description": f"**{currency_pair}** で強力なトレンド転換が検出されました",
                "fields": [
                    {
                        "name": "📊 信頼度",
                        "value": f"{notification_data['confidence']:.1%}",
                        "inline": True,
                    },
                    {
                        "name": "🎯 優先度",
                        "value": f"{notification_data['priority']}/100",
                        "inline": True,
                    },
                ],
                "color": 0xFF0000,  # 赤色
            }
        elif pattern_type == "pullback":
            return {
                "title": "📈 押し目買いチャンス",
                "description": f"**{currency_pair}** で押し目買いの機会が到来",
                "fields": [
                    {
                        "name": "📊 信頼度",
                        "value": f"{notification_data['confidence']:.1%}",
                        "inline": True,
                    },
                    {
                        "name": "🎯 優先度",
                        "value": f"{notification_data['priority']}/100",
                        "inline": True,
                    },
                ],
                "color": 0x00FF00,  # 緑色
            }
        else:
            # デフォルトメッセージ
            return {
                "title": f"📢 {pattern_type.replace('_', ' ').title()}",
                "description": f"**{currency_pair}** で{pattern_type}パターンが検出されました",
                "fields": [
                    {
                        "name": "📊 信頼度",
                        "value": f"{notification_data['confidence']:.1%}",
                        "inline": True,
                    },
                    {
                        "name": "🎯 優先度",
                        "value": f"{notification_data['priority']}/100",
                        "inline": True,
                    },
                ],
                "color": 0xFFFF00,  # 黄色
            }

    async def _log_notification(
        self,
        notification_pattern: NotificationPattern,
        message_id: str,
        notification_data: Dict[str, Any],
    ) -> None:
        """
        通知履歴を記録

        Args:
            notification_pattern: 通知パターン
            message_id: DiscordメッセージID
            notification_data: 通知データ

        Returns:
            None
        """
        try:
            notification_history = NotificationHistory(
                pattern_type=notification_pattern.pattern_type,
                currency_pair=notification_pattern.currency_pair,
                notification_data=notification_data,
                sent_at=datetime.utcnow(),
                discord_message_id=message_id,
                status="sent",
            )

            await self.notification_history_repository.save(notification_history)

        except Exception as e:
            logger.error(f"Failed to log notification: {str(e)}")

    async def process_notification_patterns(
        self, patterns: List[NotificationPattern]
    ) -> Dict[str, int]:
        """
        通知パターンを一括処理

        Args:
            patterns: 通知パターンリスト

        Returns:
            Dict[str, int]: 処理結果統計
        """
        results = {
            "total_patterns": len(patterns),
            "sent": 0,
            "duplicate_blocked": 0,
            "low_priority_filtered": 0,
            "errors": 0,
        }

        # 優先度でソート
        sorted_patterns = sorted(
            patterns, key=lambda p: p.get_priority_score(), reverse=True
        )

        for pattern in sorted_patterns:
            try:
                success = await self.send_pattern_notification(pattern)
                if success:
                    results["sent"] += 1
                else:
                    # 重複または低優先度でブロックされた場合
                    if self._is_duplicate_notification(
                        pattern.pattern_type,
                        pattern.currency_pair,
                        pattern.timeframe,
                    ):
                        results["duplicate_blocked"] += 1
                    elif (
                        self.enable_priority_filtering
                        and pattern.get_priority_score() < 30
                    ):
                        results["low_priority_filtered"] += 1
                    else:
                        results["errors"] += 1

            except Exception as e:
                results["errors"] += 1
                logger.error(f"Failed to process pattern: {str(e)}")

        logger.info(f"Notification patterns processed: {results}")
        return results

    async def get_notification_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        通知統計を取得

        Args:
            hours: 統計期間（時間）

        Returns:
            Dict[str, Any]: 通知統計
        """
        try:
            # データベースから統計を取得
            db_stats = await self.notification_history_repository.get_statistics(hours)

            # メモリ統計と組み合わせ
            statistics = {
                "total_notifications_sent": self.total_notifications_sent,
                "duplicate_notifications_blocked": self.duplicate_notifications_blocked,
                "low_priority_notifications_filtered": self.low_priority_notifications_filtered,
                "notification_errors": self.notification_errors,
                "recent_notifications_cache_size": len(self._recent_notifications),
                "hourly_count_cache_size": len(self._notification_count_per_hour),
                "database_statistics": db_stats,
                "duplicate_check_window_minutes": self.duplicate_check_window_minutes,
                "max_notifications_per_hour": self.max_notifications_per_hour,
                "enable_priority_filtering": self.enable_priority_filtering,
                "enable_duplicate_prevention": self.enable_duplicate_prevention,
            }

            return statistics

        except Exception as e:
            logger.error(f"Failed to get notification statistics: {str(e)}")
            return {"error": str(e)}

    def reset_statistics(self) -> None:
        """
        統計情報をリセット

        Returns:
            None
        """
        self.total_notifications_sent = 0
        self.duplicate_notifications_blocked = 0
        self.low_priority_notifications_filtered = 0
        self.notification_errors = 0
        self._recent_notifications.clear()
        self._notification_count_per_hour.clear()
        logger.info("NotificationManager statistics reset")

    async def cleanup_old_notifications(self, days: int = 7) -> int:
        """
        古い通知履歴を削除

        Args:
            days: 削除する日数

        Returns:
            int: 削除された通知数
        """
        try:
            deleted_count = (
                await self.notification_history_repository.delete_old_notifications(
                    days
                )
            )
            logger.info(f"Cleaned up {deleted_count} old notifications")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old notifications: {str(e)}")
            return 0
