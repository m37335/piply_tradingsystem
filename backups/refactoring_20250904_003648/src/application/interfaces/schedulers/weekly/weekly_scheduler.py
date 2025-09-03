"""
週次スケジューラー
週次データ取得スケジューラーの実装
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from src.application.interfaces.schedulers.base import BaseScheduler
from src.application.interfaces.schedulers.weekly import WeeklySchedulerConfig
from src.application.use_cases.fetch import FetchWeeklyEventsUseCase
from src.application.use_cases.ai_report import GenerateAIReportUseCase
from src.application.use_cases.notification import SendEventNotificationsUseCase


class WeeklyScheduler(BaseScheduler):
    """週次スケジューラー"""
    
    def __init__(
        self,
        config: WeeklySchedulerConfig,
        fetch_weekly_use_case: FetchWeeklyEventsUseCase,
        generate_ai_report_use_case: GenerateAIReportUseCase,
        send_notifications_use_case: SendEventNotificationsUseCase
    ):
        super().__init__(config)
        self.weekly_config = config
        self.fetch_weekly_use_case = fetch_weekly_use_case
        self.generate_ai_report_use_case = generate_ai_report_use_case
        self.send_notifications_use_case = send_notifications_use_case
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute_task(self) -> Dict[str, Any]:
        """週次タスクの実行"""
        try:
            self.logger.info("Starting weekly scheduler execution")
            
            # 翌週の開始日を取得
            next_week_start = self._get_next_week_start()
            
            # 週次データ取得
            fetch_result = await self._execute_weekly_fetch(next_week_start)
            
            # AI分析レポート生成
            ai_report_result = None
            if self.weekly_config.include_ai_analysis:
                ai_report_result = await self._execute_ai_analysis(fetch_result)
            
            # 通知送信
            notification_result = None
            if self.weekly_config.include_notifications:
                notification_result = await self._execute_notifications(fetch_result)
            
            # 実行結果の集約
            result = {
                "success": True,
                "fetch_result": fetch_result,
                "ai_report_result": ai_report_result,
                "notification_result": notification_result,
                "execution_date": datetime.utcnow().isoformat(),
                "next_week_start": next_week_start.isoformat()
            }
            
            self.logger.info("Weekly scheduler execution completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in weekly scheduler execution: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_date": datetime.utcnow().isoformat()
            }
    
    async def _execute_weekly_fetch(self, week_start: datetime) -> Dict[str, Any]:
        """週次データ取得の実行"""
        try:
            self.logger.info(f"Executing weekly fetch for week starting: {week_start}")
            
            result = await self.fetch_weekly_use_case.execute(
                start_date=week_start,
                countries=self.weekly_config.target_countries,
                importances=self.weekly_config.target_importances
            )
            
            self.logger.info(f"Weekly fetch completed: {result.get('events_fetched', 0)} events")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in weekly fetch: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_ai_analysis(self, fetch_result: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析の実行"""
        try:
            if not fetch_result.get("success"):
                return {
                    "success": False,
                    "error": "Fetch result not available for AI analysis"
                }
            
            self.logger.info("Executing AI analysis for weekly events")
            
            # 取得されたイベントを使用してAI分析を実行
            # 実際の実装では、fetch_resultからイベントリストを取得する必要がある
            result = await self.generate_ai_report_use_case.generate_reports_for_important_events(
                events=[],  # 実際のイベントリストを渡す
                target_events=[
                    "Consumer Price Index (CPI)",
                    "Gross Domestic Product (GDP)",
                    "Employment Report",
                    "Interest Rate Decision"
                ]
            )
            
            self.logger.info(f"AI analysis completed: {result.get('reports_generated', 0)} reports")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in AI analysis: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _execute_notifications(self, fetch_result: Dict[str, Any]) -> Dict[str, Any]:
        """通知送信の実行"""
        try:
            if not fetch_result.get("success"):
                return {
                    "success": False,
                    "error": "Fetch result not available for notifications"
                }
            
            self.logger.info("Executing notifications for weekly events")
            
            # 取得されたイベントを使用して通知を送信
            # 実際の実装では、fetch_resultからイベントリストを取得する必要がある
            result = await self.send_notifications_use_case.send_bulk_notifications(
                events=[],  # 実際のイベントリストを渡す
                notification_type="weekly_summary",
                message_template="📅 **週次経済指標サマリー**\n**国**: {country}\n**指標**: {event_name}\n**日時**: {date} {time}\n**重要度**: {importance}"
            )
            
            self.logger.info(f"Notifications completed: {result.get('successful', 0)} sent")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in notifications: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_next_week_start(self) -> datetime:
        """翌週の開始日を取得"""
        today = datetime.utcnow()
        
        # 指定された曜日までの日数を計算
        target_day = self.weekly_config.execution_day.lower()
        days_ahead = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }
        
        target_days_ahead = days_ahead.get(target_day, 0)
        current_weekday = today.weekday()
        
        # 翌週の指定曜日を計算
        days_until_next = (target_days_ahead - current_weekday) % 7
        if days_until_next == 0:
            days_until_next = 7  # 翌週の同じ曜日
        
        next_week_start = today + timedelta(days=days_until_next)
        
        # 指定時刻に設定
        next_week_start = next_week_start.replace(
            hour=self.weekly_config.execution_time.hour,
            minute=self.weekly_config.execution_time.minute,
            second=0,
            microsecond=0
        )
        
        return next_week_start
    
    def is_due(self) -> bool:
        """実行タイミングかどうかチェック"""
        try:
            next_execution = self._get_next_week_start()
            now = datetime.utcnow()
            
            # 実行時刻を過ぎているかチェック
            return now >= next_execution
            
        except Exception as e:
            self.logger.error(f"Error checking if scheduler is due: {e}")
            return False
    
    async def get_weekly_statistics(self) -> Dict[str, Any]:
        """週次統計情報の取得"""
        try:
            # 各ユースケースの統計情報を取得
            fetch_stats = await self.fetch_weekly_use_case.get_fetch_statistics()
            ai_report_stats = await self.generate_ai_report_use_case.get_ai_report_statistics()
            notification_stats = await self.send_notifications_use_case.get_notification_statistics()
            
            return {
                "success": True,
                "fetch_statistics": fetch_stats,
                "ai_report_statistics": ai_report_stats,
                "notification_statistics": notification_stats,
                "scheduler_config": self.weekly_config.to_dict()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting weekly statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
