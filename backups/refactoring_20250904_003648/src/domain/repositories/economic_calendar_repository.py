"""
経済カレンダーリポジトリインターフェース
経済イベントデータのCRUD操作を定義
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from decimal import Decimal

from src.domain.entities.economic_event import EconomicEvent, Importance


class EconomicCalendarRepository(ABC):
    """経済カレンダーリポジトリインターフェース"""
    
    @abstractmethod
    async def save(self, event: EconomicEvent) -> EconomicEvent:
        """
        経済イベントを保存
        
        Args:
            event: 保存する経済イベント
            
        Returns:
            EconomicEvent: 保存された経済イベント
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, event_id: int) -> Optional[EconomicEvent]:
        """
        IDで経済イベントを検索
        
        Args:
            event_id: イベントID
            
        Returns:
            Optional[EconomicEvent]: 見つかった経済イベント
        """
        pass
    
    @abstractmethod
    async def find_by_event_id(self, event_id: str) -> Optional[EconomicEvent]:
        """
        イベントIDで経済イベントを検索
        
        Args:
            event_id: イベントの一意ID
            
        Returns:
            Optional[EconomicEvent]: 見つかった経済イベント
        """
        pass
    
    @abstractmethod
    async def find_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None
    ) -> List[EconomicEvent]:
        """
        日付範囲で経済イベントを検索
        
        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）
            
        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        pass
    
    @abstractmethod
    async def find_by_country(
        self, 
        country: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[EconomicEvent]:
        """
        国名で経済イベントを検索
        
        Args:
            country: 国名
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            
        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        pass
    
    @abstractmethod
    async def find_by_importance(
        self, 
        importance: Importance,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[EconomicEvent]:
        """
        重要度で経済イベントを検索
        
        Args:
            importance: 重要度
            start_date: 開始日（オプション）
            end_date: 終了日（オプション）
            
        Returns:
            List[EconomicEvent]: 見つかった経済イベントのリスト
        """
        pass
    
    @abstractmethod
    async def find_today_events(
        self,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None
    ) -> List[EconomicEvent]:
        """
        今日の経済イベントを検索
        
        Args:
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）
            
        Returns:
            List[EconomicEvent]: 今日の経済イベントのリスト
        """
        pass
    
    @abstractmethod
    async def find_weekly_events(
        self,
        start_date: date,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None
    ) -> List[EconomicEvent]:
        """
        週間の経済イベントを検索
        
        Args:
            start_date: 週の開始日
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）
            
        Returns:
            List[EconomicEvent]: 週間の経済イベントのリスト
        """
        pass
    
    @abstractmethod
    async def find_recent_changes(
        self,
        hours: int = 24,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None
    ) -> List[EconomicEvent]:
        """
        最近の変更された経済イベントを検索
        
        Args:
            hours: 何時間前まで（デフォルト: 24時間）
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）
            
        Returns:
            List[EconomicEvent]: 変更された経済イベントのリスト
        """
        pass
    
    @abstractmethod
    async def update_actual_value(
        self, 
        event_id: str, 
        actual_value: Decimal,
        updated_at: Optional[datetime] = None
    ) -> Optional[EconomicEvent]:
        """
        実際値を更新
        
        Args:
            event_id: イベントID
            actual_value: 実際値
            updated_at: 更新日時（オプション）
            
        Returns:
            Optional[EconomicEvent]: 更新された経済イベント
        """
        pass
    
    @abstractmethod
    async def update_forecast_value(
        self, 
        event_id: str, 
        forecast_value: Decimal,
        updated_at: Optional[datetime] = None
    ) -> Optional[EconomicEvent]:
        """
        予測値を更新
        
        Args:
            event_id: イベントID
            forecast_value: 予測値
            updated_at: 更新日時（オプション）
            
        Returns:
            Optional[EconomicEvent]: 更新された経済イベント
        """
        pass
    
    @abstractmethod
    async def delete(self, event_id: int) -> bool:
        """
        経済イベントを削除
        
        Args:
            event_id: イベントID
            
        Returns:
            bool: 削除成功フラグ
        """
        pass
    
    @abstractmethod
    async def count_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None
    ) -> int:
        """
        日付範囲での経済イベント数を取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）
            
        Returns:
            int: 経済イベント数
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
