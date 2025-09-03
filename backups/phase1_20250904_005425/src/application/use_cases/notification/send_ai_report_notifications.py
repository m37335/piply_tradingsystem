"""
AIレポート通知ユースケース
AI分析レポートの通知を管理するユースケース
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.domain.services.notification import NotificationService
from src.domain.repositories.notification_history_repository import NotificationHistoryRepository
from src.domain.entities.economic_event import EconomicEvent
from src.domain.entities.ai_report import AIReport, ReportType
from .send_notifications import SendNotificationsUseCase, NotificationRequest


class SendAIReportNotificationsUseCase:
    """AIレポート通知ユースケース"""
    
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
    
    async def send_ai_report_notifications(
        self,
        reports: List[AIReport],
        include_summary: bool = True
    ) -> Dict[str, Any]:
        """
        AIレポート通知を送信
        
        Args:
            reports: 通知対象のAIレポートリスト
            include_summary: サマリーを含めるかどうか
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(f"Sending AI report notifications: {len(reports)} reports")
            
            # 高信頼度のレポートのみ通知
            high_confidence_reports = [r for r in reports if r.is_high_confidence]
            
            if not high_confidence_reports:
                return {
                    "success": True,
                    "message": "No high confidence reports to notify",
                    "reports_processed": 0
                }
            
            # 通知リクエストの作成
            requests = []
            for report in high_confidence_reports:
                message_content = self._create_ai_report_message(report, include_summary)
                
                request = NotificationRequest(
                    event=None,  # AIレポートはイベントに紐づかない場合がある
                    notification_type="ai_report",
                    message_content=message_content,
                    priority="high" if report.is_high_confidence else "normal"
                )
                requests.append(request)
            
            # 通知送信
            return await self.send_notifications_uc.execute(requests)
            
        except Exception as e:
            self.logger.error(f"Error sending AI report notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_pre_event_report_notifications(
        self,
        reports: List[AIReport]
    ) -> Dict[str, Any]:
        """
        事前レポート通知を送信
        
        Args:
            reports: 事前レポートのリスト
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(f"Sending pre-event report notifications: {len(reports)} reports")
            
            # 事前レポートのみフィルタ
            pre_event_reports = [r for r in reports if r.is_pre_event]
            
            if not pre_event_reports:
                return {
                    "success": True,
                    "message": "No pre-event reports to notify",
                    "reports_processed": 0
                }
            
            # 通知リクエストの作成
            requests = []
            for report in pre_event_reports:
                message_content = self._create_pre_event_report_message(report)
                
                request = NotificationRequest(
                    event=None,
                    notification_type="ai_pre_event_report",
                    message_content=message_content,
                    priority="high"
                )
                requests.append(request)
            
            # 通知送信
            return await self.send_notifications_uc.execute(requests)
            
        except Exception as e:
            self.logger.error(f"Error sending pre-event report notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def send_post_event_report_notifications(
        self,
        reports: List[AIReport]
    ) -> Dict[str, Any]:
        """
        事後レポート通知を送信
        
        Args:
            reports: 事後レポートのリスト
            
        Returns:
            Dict[str, Any]: 送信結果
        """
        try:
            self.logger.info(f"Sending post-event report notifications: {len(reports)} reports")
            
            # 事後レポートのみフィルタ
            post_event_reports = [r for r in reports if r.is_post_event]
            
            if not post_event_reports:
                return {
                    "success": True,
                    "message": "No post-event reports to notify",
                    "reports_processed": 0
                }
            
            # 通知リクエストの作成
            requests = []
            for report in post_event_reports:
                message_content = self._create_post_event_report_message(report)
                
                request = NotificationRequest(
                    event=None,
                    notification_type="ai_post_event_report",
                    message_content=message_content,
                    priority="high"
                )
                requests.append(request)
            
            # 通知送信
            return await self.send_notifications_uc.execute(requests)
            
        except Exception as e:
            self.logger.error(f"Error sending post-event report notifications: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _create_ai_report_message(self, report: AIReport, include_summary: bool) -> str:
        """AIレポートメッセージの作成"""
        confidence_emoji = "🎯" if report.is_high_confidence else "⚠️"
        
        message = (
            f"🤖 **AI分析レポート**\n"
            f"**レポートタイプ**: {report.report_type.value}\n"
            f"**信頼度**: {report.confidence_score:.2f} {confidence_emoji}\n"
            f"**生成日時**: {report.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if report.has_prediction:
            prediction = report.usd_jpy_prediction
            message += (
                f"**ドル円予測**: {prediction.direction.value.upper()} "
                f"({prediction.strength.value})\n"
            )
        
        if include_summary and report.summary:
            message += f"\n**サマリー**: {report.summary[:200]}..."
        
        return message
    
    def _create_pre_event_report_message(self, report: AIReport) -> str:
        """事前レポートメッセージの作成"""
        confidence_emoji = "🎯" if report.is_high_confidence else "⚠️"
        
        message = (
            f"🔮 **事前AI分析**\n"
            f"**信頼度**: {report.confidence_score:.2f} {confidence_emoji}\n"
            f"**生成日時**: {report.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if report.has_prediction:
            prediction = report.usd_jpy_prediction
            message += (
                f"**ドル円予測**: {prediction.direction.value.upper()} "
                f"({prediction.strength.value})\n"
            )
        
        if report.summary:
            message += f"\n**分析サマリー**: {report.summary[:150]}..."
        
        return message
    
    def _create_post_event_report_message(self, report: AIReport) -> str:
        """事後レポートメッセージの作成"""
        confidence_emoji = "🎯" if report.is_high_confidence else "⚠️"
        
        message = (
            f"📊 **事後AI分析**\n"
            f"**信頼度**: {report.confidence_score:.2f} {confidence_emoji}\n"
            f"**生成日時**: {report.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if report.has_prediction:
            prediction = report.usd_jpy_prediction
            message += (
                f"**ドル円影響**: {prediction.direction.value.upper()} "
                f"({prediction.strength.value})\n"
            )
        
        if report.summary:
            message += f"\n**分析結果**: {report.summary[:150]}..."
        
        return message
    
    async def get_ai_report_notification_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """AIレポート通知統計情報の取得"""
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
            
            # AIレポート関連の通知のみフィルタ
            ai_report_notifications = [
                n for n in notifications
                if n.pattern_type in ["ai_report", "ai_pre_event_report", "ai_post_event_report"]
            ]
            
            stats = {
                "total_ai_report_notifications": len(ai_report_notifications),
                "ai_report_notifications": len([n for n in ai_report_notifications if n.pattern_type == "ai_report"]),
                "pre_event_report_notifications": len([n for n in ai_report_notifications if n.pattern_type == "ai_pre_event_report"]),
                "post_event_report_notifications": len([n for n in ai_report_notifications if n.pattern_type == "ai_post_event_report"]),
                "notifications_by_confidence": {},
                "notifications_by_report_type": {}
            }
            
            # 信頼度別・レポートタイプ別統計
            for notification in ai_report_notifications:
                confidence = notification.notification_data.get("confidence_score", "unknown")
                report_type = notification.notification_data.get("report_type", "unknown")
                
                if confidence not in stats["notifications_by_confidence"]:
                    stats["notifications_by_confidence"][confidence] = 0
                stats["notifications_by_confidence"][confidence] += 1
                
                if report_type not in stats["notifications_by_report_type"]:
                    stats["notifications_by_report_type"][report_type] = 0
                stats["notifications_by_report_type"][report_type] += 1
            
            return {
                "success": True,
                "statistics": stats,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting AI report notification statistics: {e}")
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
