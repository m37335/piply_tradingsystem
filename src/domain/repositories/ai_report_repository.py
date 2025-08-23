"""
AIレポートリポジトリインターフェース
AIレポートデータのCRUD操作を定義
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.domain.entities.ai_report import AIReport, ReportType


class AIReportRepository(ABC):
    """AIレポートリポジトリインターフェース"""
    
    @abstractmethod
    async def save(self, report: AIReport) -> AIReport:
        """
        AIレポートを保存
        
        Args:
            report: 保存するAIレポート
            
        Returns:
            AIReport: 保存されたAIレポート
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, report_id: int) -> Optional[AIReport]:
        """
        IDでAIレポートを検索
        
        Args:
            report_id: レポートID
            
        Returns:
            Optional[AIReport]: 見つかったAIレポート
        """
        pass
    
    @abstractmethod
    async def find_by_event_id(
        self, 
        event_id: int,
        report_type: Optional[ReportType] = None
    ) -> List[AIReport]:
        """
        イベントIDでAIレポートを検索
        
        Args:
            event_id: イベントID
            report_type: レポートタイプ（フィルタ）
            
        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        pass
    
    @abstractmethod
    async def find_by_report_type(
        self, 
        report_type: ReportType,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AIReport]:
        """
        レポートタイプでAIレポートを検索
        
        Args:
            report_type: レポートタイプ
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            
        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        pass
    
    @abstractmethod
    async def find_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        report_types: Optional[List[ReportType]] = None
    ) -> List[AIReport]:
        """
        日付範囲でAIレポートを検索
        
        Args:
            start_date: 開始日
            end_date: 終了日
            report_types: レポートタイプリスト（フィルタ）
            
        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        pass
    
    @abstractmethod
    async def find_high_confidence_reports(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        min_confidence: Optional[Decimal] = None
    ) -> List[AIReport]:
        """
        高信頼度のAIレポートを検索
        
        Args:
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            min_confidence: 最小信頼度（オプション）
            
        Returns:
            List[AIReport]: 高信頼度のAIレポートのリスト
        """
        pass
    
    @abstractmethod
    async def find_recent_reports(
        self,
        hours: int = 24,
        report_types: Optional[List[ReportType]] = None
    ) -> List[AIReport]:
        """
        最近のAIレポートを検索
        
        Args:
            hours: 何時間前まで（デフォルト: 24時間）
            report_types: レポートタイプリスト（フィルタ）
            
        Returns:
            List[AIReport]: 最近のAIレポートのリスト
        """
        pass
    
    @abstractmethod
    async def find_by_confidence_range(
        self,
        min_confidence: Decimal,
        max_confidence: Decimal,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[AIReport]:
        """
        信頼度範囲でAIレポートを検索
        
        Args:
            min_confidence: 最小信頼度
            max_confidence: 最大信頼度
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            
        Returns:
            List[AIReport]: 見つかったAIレポートのリスト
        """
        pass
    
    @abstractmethod
    async def update_confidence_score(
        self, 
        report_id: int, 
        confidence_score: Decimal,
        updated_at: Optional[datetime] = None
    ) -> Optional[AIReport]:
        """
        信頼度を更新
        
        Args:
            report_id: レポートID
            confidence_score: 信頼度
            updated_at: 更新日時（オプション）
            
        Returns:
            Optional[AIReport]: 更新されたAIレポート
        """
        pass
    
    @abstractmethod
    async def update_report_content(
        self, 
        report_id: int, 
        report_content: str,
        summary: Optional[str] = None,
        updated_at: Optional[datetime] = None
    ) -> Optional[AIReport]:
        """
        レポート内容を更新
        
        Args:
            report_id: レポートID
            report_content: レポート内容
            summary: サマリー（オプション）
            updated_at: 更新日時（オプション）
            
        Returns:
            Optional[AIReport]: 更新されたAIレポート
        """
        pass
    
    @abstractmethod
    async def delete(self, report_id: int) -> bool:
        """
        AIレポートを削除
        
        Args:
            report_id: レポートID
            
        Returns:
            bool: 削除成功フラグ
        """
        pass
    
    @abstractmethod
    async def count_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        report_types: Optional[List[ReportType]] = None
    ) -> int:
        """
        日付範囲でのAIレポート数を取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            report_types: レポートタイプリスト（フィルタ）
            
        Returns:
            int: AIレポート数
        """
        pass
    
    @abstractmethod
    async def get_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Args:
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            
        Returns:
            Dict[str, Any]: 統計情報
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        ヘルスチェック
        
        Returns:
            bool: 正常フラグ
        """
        pass
