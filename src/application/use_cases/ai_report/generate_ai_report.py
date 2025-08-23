"""
AIレポート生成ユースケース
ChatGPTによるAI分析レポートの生成を管理するメインユースケース
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.domain.services.ai_analysis import AIAnalysisService
from src.domain.repositories.ai_report_repository import AIReportRepository
from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.entities.ai_report import AIReport, ReportType


class GenerateAIReportUseCase:
    """AIレポート生成ユースケース"""
    
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
        report_type: ReportType,
        importance_filter: Optional[List[Importance]] = None
    ) -> Dict[str, Any]:
        """
        AIレポート生成を実行
        
        Args:
            events: 分析対象のイベントリスト
            report_type: レポートタイプ
            importance_filter: 重要度フィルタ
            
        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            self.logger.info(f"Starting AI report generation: {len(events)} events, type: {report_type.value}")
            
            # 重要度フィルタリング
            if importance_filter:
                events = [e for e in events if e.importance in importance_filter]
            
            # 高重要度イベントのみ分析
            high_importance_events = [e for e in events if e.is_high_importance]
            
            if not high_importance_events:
                return {
                    "success": True,
                    "message": "No high importance events to analyze",
                    "reports_generated": 0
                }
            
            # AIレポート生成
            generated_reports = []
            for event in high_importance_events:
                try:
                    report = await self._generate_report_for_event(event, report_type)
                    if report:
                        generated_reports.append(report)
                except Exception as e:
                    self.logger.error(f"Error generating report for event {event.event_id}: {e}")
            
            # レポートの保存
            saved_reports = []
            for report in generated_reports:
                try:
                    saved_report = await self.ai_report_repository.save(report)
                    saved_reports.append(saved_report)
                except Exception as e:
                    self.logger.error(f"Error saving report {report.id}: {e}")
            
            result = {
                "success": True,
                "reports_generated": len(generated_reports),
                "reports_saved": len(saved_reports),
                "report_type": report_type.value,
                "generation_date": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"AI report generation completed: {len(saved_reports)} reports saved")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in AI report generation: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_date": datetime.utcnow().isoformat()
            }
    
    async def _generate_report_for_event(
        self,
        event: EconomicEvent,
        report_type: ReportType
    ) -> Optional[AIReport]:
        """個別イベントのレポート生成"""
        try:
            if report_type == ReportType.PRE_EVENT:
                return await self.ai_analysis_service.generate_pre_event_report(event)
            elif report_type == ReportType.POST_EVENT:
                return await self.ai_analysis_service.generate_post_event_report(event)
            elif report_type == ReportType.FORECAST_CHANGE:
                # 予測値変更レポートは別途実装
                return await self.ai_analysis_service.generate_forecast_change_report(event)
            else:
                self.logger.warning(f"Unknown report type: {report_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error generating report for event {event.event_id}: {e}")
            return None
    
    async def generate_bulk_reports(
        self,
        events: List[EconomicEvent],
        report_types: List[ReportType],
        importance_filter: Optional[List[Importance]] = None
    ) -> Dict[str, Any]:
        """
        一括レポート生成
        
        Args:
            events: 分析対象のイベントリスト
            report_types: レポートタイプリスト
            importance_filter: 重要度フィルタ
            
        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            self.logger.info(f"Starting bulk AI report generation: {len(events)} events, {len(report_types)} types")
            
            total_reports = 0
            successful_reports = 0
            
            for report_type in report_types:
                result = await self.execute(events, report_type, importance_filter)
                if result["success"]:
                    successful_reports += result["reports_generated"]
                total_reports += result["reports_generated"]
            
            return {
                "success": True,
                "total_reports_generated": total_reports,
                "successful_reports": successful_reports,
                "report_types_processed": len(report_types),
                "generation_date": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in bulk AI report generation: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_date": datetime.utcnow().isoformat()
            }
    
    async def generate_reports_for_important_events(
        self,
        events: List[EconomicEvent],
        target_events: List[str]
    ) -> Dict[str, Any]:
        """
        重要イベントのレポート生成
        
        Args:
            events: 分析対象のイベントリスト
            target_events: 対象イベント名リスト
            
        Returns:
            Dict[str, Any]: 生成結果
        """
        try:
            self.logger.info(f"Generating reports for important events: {len(target_events)} targets")
            
            # 対象イベントのフィルタリング
            target_events_filtered = [
                e for e in events
                if any(target in e.event_name for target in target_events)
            ]
            
            if not target_events_filtered:
                return {
                    "success": True,
                    "message": "No target events found",
                    "reports_generated": 0
                }
            
            # 事前・事後レポートの生成
            report_types = [ReportType.PRE_EVENT, ReportType.POST_EVENT]
            result = await self.generate_bulk_reports(
                target_events_filtered,
                report_types,
                importance_filter=[Importance.HIGH]
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error generating reports for important events: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_date": datetime.utcnow().isoformat()
            }
    
    async def get_ai_report_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """AIレポート統計情報の取得"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
            # レポート統計の取得
            stats = await self.ai_report_repository.get_statistics(
                start_date=start_date.date(),
                end_date=end_date.date()
            )
            
            return {
                "success": True,
                "statistics": stats,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting AI report statistics: {e}")
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
