"""
イベント通知ユースケース
経済イベントの通知を管理するユースケース
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.domain.services.notification import NotificationService
from src.domain.repositories.notification_history_repository import NotificationHistoryRepository
from src.domain.entities.economic_event import EconomicEvent, Importance
from .send_notifications import SendNotificationsUseCase, NotificationRequest


class SendEventNotificationsUseCase:
    """イベント通知ユースケース"""
    
    def __init__(
        self,
        notification_service: NotificationService,
        notification_history_repository: NotificationHistoryRepository
    ):
        self.notification_service = notification_service
        self.notification_history_repository = notification_history_repository
        self.send_notifications_uc = SendNotificationsUseCase(
            notification_service=notification_service,
            notification_history_repository=notification_history_repository
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def send_new_event_notifications(
        self,
        events: List[EconomicEvent],
        importance_filter: Optional[List[Importance]] = None
    ) -> Dict[str, Any]:
        """
        新規イベント通知を送信
        
        Args:
            events: 通知対象のイベントリスト
            importance_filter: 重要度フィルタ
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(f"Sending new event notifications: {len(events)} events")
            
            # 重要度フィルタリング
            if importance_filter:
                events = [e for e in events if e.importance in importance_filter]
            
            # 高重要度イベントのみ通知
            high_importance_events = [e for e in events if e.is_high_importance]
            
            if not high_importance_events:
                return {
                    "success": True,
                    "message": "No high importance events to notify",
                    "events_processed": 0
                }
            
            # 通知リクエストの作成
            requests = []
            for event in high_importance_events:
                message_content = self._create_new_event_message(event)
                
                request = NotificationRequest(
                    event=event,
                    notification_type="new_event",
                    message_content=message_content,
                    priority="high" if event.is_high_importance else "normal"
                )
                requests.append(request)
            
            # 通知送信
            return await self.send_notifications_uc.execute(requests)
            
        except Exception as e:
            self.logger.error(f"Error sending new event notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_forecast_change_notifications(
        self,
        old_events: List[EconomicEvent],
        new_events: List[EconomicEvent],
        change_threshold: float = 0.1
    ) -> Dict[str, Any]:
        """
        予測値変更通知を送信
        
        Args:
            old_events: 変更前のイベントリスト
            new_events: 変更後のイベントリスト
            change_threshold: 変更閾値
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(f"Sending forecast change notifications: {len(new_events)} events")
            
            # 変更検出
            changed_events = []
            for old_event, new_event in zip(old_events, new_events):
                if self._has_significant_forecast_change(old_event, new_event, change_threshold):
                    changed_events.append((old_event, new_event))
            
            if not changed_events:
                return {
                    "success": True,
                    "message": "No significant forecast changes detected",
                    "events_processed": 0
                }
            
            # 通知リクエストの作成
            requests = []
            for old_event, new_event in changed_events:
                message_content = self._create_forecast_change_message(old_event, new_event)
                
                request = NotificationRequest(
                    event=new_event,
                    notification_type="forecast_change",
                    message_content=message_content,
                    priority="medium"
                )
                requests.append(request)
            
            # 通知送信
            return await self.send_notifications_uc.execute(requests)
            
        except Exception as e:
            self.logger.error(f"Error sending forecast change notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_actual_announcement_notifications(
        self,
        events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """
        実際値発表通知を送信
        
        Args:
            events: 実際値が発表されたイベントリスト
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(f"Sending actual announcement notifications: {len(events)} events")
            
            # 実際値があるイベントのみ
            events_with_actual = [e for e in events if e.has_actual_value]
            
            if not events_with_actual:
                return {
                    "success": True,
                    "message": "No events with actual values",
                    "events_processed": 0
                }
            
            # 通知リクエストの作成
            requests = []
            for event in events_with_actual:
                message_content = self._create_actual_announcement_message(event)
                
                request = NotificationRequest(
                    event=event,
                    notification_type="actual_announcement",
                    message_content=message_content,
                    priority="high" if event.is_high_importance else "normal"
                )
                requests.append(request)
            
            # 通知送信
            return await self.send_notifications_uc.execute(requests)
            
        except Exception as e:
            self.logger.error(f"Error sending actual announcement notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _create_new_event_message(self, event: EconomicEvent) -> str:
        """新規イベントメッセージの作成"""
        importance_emoji = "🚨" if event.is_high_importance else "📊"
        time_str = event.time_utc.strftime("%H:%M") if event.time_utc else "TBD"
        
        return (
            f"{importance_emoji} **新規経済指標**\n"
            f"**国**: {event.country}\n"
            f"**指標**: {event.event_name}\n"
            f"**日時**: {event.date_utc.strftime('%Y-%m-%d')} {time_str}\n"
            f"**重要度**: {event.importance.value.upper()}"
        )
    
    def _create_forecast_change_message(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent
    ) -> str:
        """予測値変更メッセージの作成"""
        old_forecast = old_event.forecast_value or 0
        new_forecast = new_event.forecast_value or 0
        change_percent = ((new_forecast - old_forecast) / old_forecast * 100) if old_forecast != 0 else 0
        
        change_emoji = "📈" if change_percent > 0 else "📉"
        
        return (
            f"📊 **予測値変更**\n"
            f"**国**: {new_event.country}\n"
            f"**指標**: {new_event.event_name}\n"
            f"**変更**: {old_forecast} → {new_forecast} {change_emoji}\n"
            f"**変化率**: {change_percent:.2f}%"
        )
    
    def _create_actual_announcement_message(self, event: EconomicEvent) -> str:
        """実際値発表メッセージの作成"""
        actual = event.actual_value
        forecast = event.forecast_value
        previous = event.previous_value
        
        # サプライズ計算
        surprise_percent = 0
        if forecast and actual:
            surprise_percent = ((actual - forecast) / forecast * 100) if forecast != 0 else 0
        
        surprise_emoji = "🎯" if abs(surprise_percent) < 5 else "⚠️"
        
        message = (
            f"📈 **実際値発表**\n"
            f"**国**: {event.country}\n"
            f"**指標**: {event.event_name}\n"
            f"**実際値**: {actual}\n"
        )
        
        if forecast:
            message += f"**予測値**: {forecast}\n"
        
        if previous:
            message += f"**前回値**: {previous}\n"
        
        if forecast and actual:
            message += f"**サプライズ**: {surprise_percent:.2f}% {surprise_emoji}"
        
        return message
    
    def _has_significant_forecast_change(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent,
        threshold: float
    ) -> bool:
        """重要な予測値変更があるかチェック"""
        if not (old_event.has_forecast_value and new_event.has_forecast_value):
            return False
        
        old_forecast = old_event.forecast_value
        new_forecast = new_event.forecast_value
        
        if old_forecast == 0:
            return False
        
        change_percent = abs((new_forecast - old_forecast) / old_forecast)
        return change_percent >= threshold
    
    async def get_event_notification_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """イベント通知統計情報の取得"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # 通知履歴から統計を取得
            notifications = await self.notification_history_repository.find_by_date_range(
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            
            # イベント関連の通知のみフィルタ
            event_notifications = [
                n for n in notifications
                if n.pattern_type in ["new_event", "forecast_change", "actual_announcement"]
            ]
            
            stats = {
                "total_event_notifications": len(event_notifications),
                "new_event_notifications": len([n for n in event_notifications if n.pattern_type == "new_event"]),
                "forecast_change_notifications": len([n for n in event_notifications if n.pattern_type == "forecast_change"]),
                "actual_announcement_notifications": len([n for n in event_notifications if n.pattern_type == "actual_announcement"]),
                "notifications_by_importance": {},
                "notifications_by_country": {}
            }
            
            # 重要度別・国別統計
            for notification in event_notifications:
                importance = notification.notification_data.get("importance", "unknown")
                country = notification.notification_data.get("country", "unknown")
                
                if importance not in stats["notifications_by_importance"]:
                    stats["notifications_by_importance"][importance] = 0
                stats["notifications_by_importance"][importance] += 1
                
                if country not in stats["notifications_by_country"]:
                    stats["notifications_by_country"][country] = 0
                stats["notifications_by_country"][country] += 1
            
            return {
                "success": True,
                "statistics": stats,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting event notification statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 通知サービスのヘルスチェック
            service_health = await self.notification_service.health_check()
            
            # リポジトリのヘルスチェック
            repository_health = await self.notification_history_repository.health_check()
            
            return service_health and repository_health
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
