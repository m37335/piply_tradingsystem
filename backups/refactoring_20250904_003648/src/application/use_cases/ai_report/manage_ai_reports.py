"""
AIレポート管理ユースケース
AI分析レポートの管理を担当
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from src.domain.repositories.ai_report_repository import AIReportRepository
from src.domain.entities.ai_report import AIReport, ReportType


class ManageAIReportsUseCase:
    """AIレポート管理ユースケース"""
    
    def __init__(self, ai_report_repository: AIReportRepository):
        self.ai_report_repository = ai_report_repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_reports_by_event_id(
        self,
        event_id: int,
        report_type: Optional[ReportType] = None
    ) -> Dict[str, Any]:
        """
        イベントIDでレポートを取得
        
        Args:
            event_id: イベントID
            report_type: レポートタイプ（フィルタ）
            
        Returns:
            Dict[str, Any]: 取得結果
        """
        try:
            self.logger.info(f"Getting reports for event ID: {event_id}")
            
            reports = await self.ai_report_repository.find_by_event_id(
                event_id=event_id,
                report_type=report_type
            )
            
            return {
                "success": True,
                "reports": reports,
                "count": len(reports),
                "event_id": event_id
            }
            
        except Exception as e:
            self.logger.error(f"Error getting reports by event ID: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_high_confidence_reports(
        self,
        min_confidence: float = 0.7,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        高信頼度レポートを取得
        
        Args:
            min_confidence: 最小信頼度
            limit: 取得件数上限
            
        Returns:
            Dict[str, Any]: 取得結果
        """
        try:
            self.logger.info(f"Getting high confidence reports: min_confidence={min_confidence}")
            
            reports = await self.ai_report_repository.find_high_confidence_reports(
                min_confidence=min_confidence,
                limit=limit
            )
            
            return {
                "success": True,
                "reports": reports,
                "count": len(reports),
                "min_confidence": min_confidence
            }
            
        except Exception as e:
            self.logger.error(f"Error getting high confidence reports: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_recent_reports(
        self,
        hours: int = 24,
        report_types: Optional[List[ReportType]] = None
    ) -> Dict[str, Any]:
        """
        最近のレポートを取得
        
        Args:
            hours: 何時間前まで
            report_types: レポートタイプリスト（フィルタ）
            
        Returns:
            Dict[str, Any]: 取得結果
        """
        try:
            self.logger.info(f"Getting recent reports: hours={hours}")
            
            reports = await self.ai_report_repository.find_recent_reports(
                hours=hours,
                report_types=report_types
            )
            
            return {
                "success": True,
                "reports": reports,
                "count": len(reports),
                "hours": hours
            }
            
        except Exception as e:
            self.logger.error(f"Error getting recent reports: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_old_reports(
        self,
        days_old: int = 30
    ) -> Dict[str, Any]:
        """
        古いレポートを削除
        
        Args:
            days_old: 何日前より古いレポートを削除するか
            
        Returns:
            Dict[str, Any]: 削除結果
        """
        try:
            self.logger.info(f"Deleting old reports: days_old={days_old}")
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # 古いレポートを取得
            old_reports = await self.ai_report_repository.find_by_date_range(
                start_date=datetime.min.date(),
                end_date=cutoff_date.date()
            )
            
            # 削除実行
            deleted_count = 0
            for report in old_reports:
                try:
                    success = await self.ai_report_repository.delete(report.id)
                    if success:
                        deleted_count += 1
                except Exception as e:
                    self.logger.error(f"Error deleting report {report.id}: {e}")
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "total_old_reports": len(old_reports),
                "days_old": days_old
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting old reports: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_report_confidence(
        self,
        report_id: int,
        new_confidence: float
    ) -> Dict[str, Any]:
        """
        レポートの信頼度を更新
        
        Args:
            report_id: レポートID
            new_confidence: 新しい信頼度
            
        Returns:
            Dict[str, Any]: 更新結果
        """
        try:
            self.logger.info(f"Updating report confidence: report_id={report_id}, confidence={new_confidence}")
            
            updated_report = await self.ai_report_repository.update_confidence_score(
                report_id=report_id,
                confidence_score=new_confidence
            )
            
            if updated_report:
                return {
                    "success": True,
                    "report": updated_report,
                    "new_confidence": new_confidence
                }
            else:
                return {
                    "success": False,
                    "error": "Report not found"
                }
            
        except Exception as e:
            self.logger.error(f"Error updating report confidence: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_report_statistics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """レポート統計情報の取得"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=7)
            if not end_date:
                end_date = datetime.utcnow()
            
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
            self.logger.error(f"Error getting report statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            return await self.ai_report_repository.health_check()
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
