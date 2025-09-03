"""
事後レポート生成ユースケース
イベント後のAI分析レポート生成を管理
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.domain.services.ai_analysis import AIAnalysisService
from src.domain.repositories.ai_report_repository import AIReportRepository
from src.domain.entities.economic_event import EconomicEvent
from src.domain.entities.ai_report import ReportType


class GeneratePostEventReportUseCase:
    """事後レポート生成ユースケース"""
    
    def __init__(
        self,
        ai_analysis_service: AIAnalysisService,
        ai_report_repository: AIReportRepository
    ):
        self.ai_analysis_service = ai_analysis_service
        self.ai_report_repository = ai_report_repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute(
        self,
        events: List[EconomicEvent],
        hours_after_event: int = 2
    ) -> Dict[str, Any]:
        """
        事後レポート生成を実行
        
        Args:
            events: 分析対象のイベントリスト
            hours_after_event: イベント後何時間で生成するか
            
        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            self.logger.info(f"Starting post-event report generation: {len(events)} events")
            
            # 指定時間後のイベントをフィルタ
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_after_event)
            recent_events = [
                e for e in events
                if e.date_utc <= datetime.utcnow() and e.date_utc >= cutoff_time
            ]
            
            # 実際値がある高重要度イベントのみ
            target_events = [
                e for e in recent_events
                if e.is_high_importance and e.has_actual_value
            ]
            
            if not target_events:
                return {
                    "success": True,
                    "message": "No recent high importance events with actual values",
                    "reports_generated": 0
                }
            
            # 事後レポート生成
            generated_reports = []
            for event in target_events:
                try:
                    report = await self.ai_analysis_service.generate_post_event_report(event)
                    if report:
                        generated_reports.append(report)
                except Exception as e:
                    self.logger.error(f"Error generating post-event report for {event.event_id}: {e}")
            
            # レポートの保存
            saved_reports = []
            for report in generated_reports:
                try:
                    saved_report = await self.ai_report_repository.save(report)
                    saved_reports.append(saved_report)
                except Exception as e:
                    self.logger.error(f"Error saving post-event report {report.id}: {e}")
            
            result = {
                "success": True,
                "reports_generated": len(generated_reports),
                "reports_saved": len(saved_reports),
                "hours_after_event": hours_after_event,
                "generation_date": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Post-event report generation completed: {len(saved_reports)} reports")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in post-event report generation: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_date": datetime.utcnow().isoformat()
            }
    
    async def generate_for_surprise_events(
        self,
        events: List[EconomicEvent],
        surprise_threshold: float = 0.2
    ) -> Dict[str, Any]:
        """
        サプライズイベントの事後レポート生成
        
        Args:
            events: 分析対象のイベントリスト
            surprise_threshold: サプライズ閾値
            
        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            self.logger.info(f"Generating post-event reports for surprise events: threshold {surprise_threshold}")
            
            # サプライズイベントのフィルタリング
            surprise_events = []
            for event in events:
                if event.has_actual_value and event.has_forecast_value:
                    surprise_percent = abs(event.surprise_percentage or 0)
                    if surprise_percent >= surprise_threshold:
                        surprise_events.append(event)
            
            if not surprise_events:
                return {
                    "success": True,
                    "message": "No surprise events found",
                    "reports_generated": 0
                }
            
            # 事後レポート生成
            return await self.execute(surprise_events)
            
        except Exception as e:
            self.logger.error(f"Error generating post-event reports for surprise events: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_date": datetime.utcnow().isoformat()
            }
    
    async def get_post_event_report_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """事後レポート統計情報の取得"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # 事後レポートの統計取得
            reports = await self.ai_report_repository.find_by_report_type(
                ReportType.POST_EVENT,
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            
            stats = {
                "total_post_event_reports": len(reports),
                "high_confidence_reports": len([r for r in reports if r.is_high_confidence]),
                "reports_with_predictions": len([r for r in reports if r.has_prediction]),
                "average_confidence_score": 0.0
            }
            
            if reports:
                confidence_scores = [float(r.confidence_score) for r in reports]
                stats["average_confidence_score"] = sum(confidence_scores) / len(confidence_scores)
            
            return {
                "success": True,
                "statistics": stats,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting post-event report statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # AI分析サービスのヘルスチェック
            service_health = await self.ai_analysis_service.health_check()
            
            # リポジトリのヘルスチェック
            repository_health = await self.ai_report_repository.health_check()
            
            return service_health and repository_health
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
