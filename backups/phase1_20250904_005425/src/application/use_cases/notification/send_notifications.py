"""
通知送信ユースケース
Discord通知の送信を管理するメインユースケース
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.entities.notification_history import NotificationHistory
from src.domain.repositories.notification_history_repository import (
    NotificationHistoryRepository,
)
from src.domain.services.notification import NotificationService


@dataclass
class NotificationRequest:
    """通知リクエスト"""

    event: EconomicEvent
    notification_type: str
    message_content: str
    priority: str = "normal"
    retry_count: int = 0


class SendNotificationsUseCase:
    """通知送信ユースケース"""

    def __init__(
        self,
        notification_service: NotificationService,
        notification_history_repository: NotificationHistoryRepository,
    ):
        self.notification_service = notification_service
        self.notification_history_repository = notification_history_repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(
        self, notification_requests: List[NotificationRequest]
    ) -> Dict[str, Any]:
        """
        通知送信を実行

        Args:
            notification_requests: 通知リクエストのリスト

        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(
                f"Starting notification sending: {len(notification_requests)} requests"
            )

            results = {
                "total_requests": len(notification_requests),
                "successful": 0,
                "failed": 0,
                "skipped": 0,
                "details": [],
            }

            for request in notification_requests:
                # クールダウンチェック
                if await self._should_skip_notification(request):
                    results["skipped"] += 1
                    results["details"].append(
                        {
                            "event_id": request.event.event_id,
                            "status": "skipped",
                            "reason": "cooldown_period",
                        }
                    )
                    continue

                # 通知送信
                try:
                    success = await self._send_notification(request)

                    if success:
                        results["successful"] += 1
                        status = "success"
                    else:
                        results["failed"] += 1
                        status = "failed"

                    results["details"].append(
                        {
                            "event_id": request.event.event_id,
                            "status": status,
                            "notification_type": request.notification_type,
                        }
                    )

                except Exception as e:
                    self.logger.error(
                        f"Error sending notification for event {request.event.event_id}: {e}"
                    )
                    results["failed"] += 1
                    results["details"].append(
                        {
                            "event_id": request.event.event_id,
                            "status": "error",
                            "error": str(e),
                        }
                    )

            # 通知履歴の保存
            await self._save_notification_history(notification_requests, results)

            self.logger.info(
                f"Notification sending completed: "
                f"{results['successful']} successful, "
                f"{results['failed']} failed, "
                f"{results['skipped']} skipped"
            )

            return {
                "success": True,
                "results": results,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error in notification sending: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def _send_notification(self, request: NotificationRequest) -> bool:
        """個別通知の送信"""
        try:
            # 通知サービスの呼び出し
            success = await self.notification_service.send_notification(
                event=request.event,
                notification_type=request.notification_type,
                message_content=request.message_content,
                priority=request.priority,
            )

            return success

        except Exception as e:
            self.logger.error(f"Error in _send_notification: {e}")
            return False

    async def _should_skip_notification(self, request: NotificationRequest) -> bool:
        """通知をスキップすべきかチェック"""
        try:
            # 最近の通知履歴をチェック
            recent_notifications = (
                await self.notification_history_repository.find_recent_notifications(
                    pattern_type=request.notification_type,
                    currency_pair="USD/JPY",  # 固定値として設定
                    time_window_minutes=30,
                )
            )

            # 同じイベントの最近の通知があるかチェック
            for notification in recent_notifications:
                if (
                    notification.notification_data.get("event_id")
                    == request.event.event_id
                ):
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking notification history: {e}")
            return False

    async def _save_notification_history(
        self, requests: List[NotificationRequest], results: Dict[str, Any]
    ) -> None:
        """通知履歴の保存"""
        try:
            for request, result_detail in zip(requests, results["details"]):
                if result_detail["status"] == "success":
                    # 成功した通知のみ履歴に保存
                    notification_history = NotificationHistory(
                        pattern_type=request.notification_type,
                        currency_pair="USD/JPY",
                        notification_data={
                            "event_id": request.event.event_id,
                            "event_name": request.event.event_name,
                            "country": request.event.country,
                            "importance": request.event.importance.value,
                            "notification_type": request.notification_type,
                            "message_content": request.message_content,
                        },
                        sent_at=datetime.utcnow(),
                        status="sent",
                    )

                    await self.notification_history_repository.save(
                        notification_history
                    )

        except Exception as e:
            self.logger.error(f"Error saving notification history: {e}")

    async def send_bulk_notifications(
        self, events: List[EconomicEvent], notification_type: str, message_template: str
    ) -> Dict[str, Any]:
        """
        一括通知送信

        Args:
            events: 通知対象のイベントリスト
            notification_type: 通知タイプ
            message_template: メッセージテンプレート

        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            # 通知リクエストの作成
            requests = []
            for event in events:
                message_content = message_template.format(
                    country=event.country,
                    event_name=event.event_name,
                    date=event.date_utc.strftime("%Y-%m-%d"),
                    time=event.time_utc.strftime("%H:%M") if event.time_utc else "TBD",
                    importance=event.importance.value,
                )

                request = NotificationRequest(
                    event=event,
                    notification_type=notification_type,
                    message_content=message_content,
                )
                requests.append(request)

            # 通知送信の実行
            return await self.execute(requests)

        except Exception as e:
            self.logger.error(f"Error in bulk notification sending: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    async def get_notification_statistics(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """通知統計情報の取得"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()

            # 通知履歴から統計を取得
            notifications = (
                await self.notification_history_repository.find_by_date_range(
                    start_date=start_date.date(), end_date=end_date.date()
                )
            )

            stats = {
                "total_notifications": len(notifications),
                "successful_notifications": len(
                    [n for n in notifications if n.status == "sent"]
                ),
                "failed_notifications": len(
                    [n for n in notifications if n.status == "failed"]
                ),
                "notifications_by_type": {},
                "notifications_by_country": {},
            }

            # タイプ別統計
            for notification in notifications:
                notification_type = notification.pattern_type
                if notification_type not in stats["notifications_by_type"]:
                    stats["notifications_by_type"][notification_type] = 0
                stats["notifications_by_type"][notification_type] += 1

                # 国別統計
                country = notification.notification_data.get("country", "unknown")
                if country not in stats["notifications_by_country"]:
                    stats["notifications_by_country"][country] = 0
                stats["notifications_by_country"][country] += 1

            return {
                "success": True,
                "statistics": stats,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting notification statistics: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 通知サービスのヘルスチェック
            service_health = await self.notification_service.health_check()

            # リポジトリのヘルスチェック
            repository_health = (
                await self.notification_history_repository.health_check()
            )

            return service_health and repository_health

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
