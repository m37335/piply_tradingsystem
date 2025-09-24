"""
カレンダー管理システム

経済指標の発表スケジュールを管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from modules.data_persistence.models.economic_calendar import (
    EconomicCalendarModel, CalendarStatus
)

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """カレンダーイベント"""
    calendar_id: str
    country: str
    indicator_name: str
    scheduled_release: datetime
    impact_level: str
    currency_impact: Optional[str] = None
    forecast_value: Optional[float] = None
    previous_value: Optional[float] = None
    status: str = "scheduled"


class CalendarManager:
    """カレンダー管理システム"""
    
    def __init__(self):
        self.events: Dict[str, CalendarEvent] = {}
        self.country_events: Dict[str, List[str]] = {}
        self.currency_events: Dict[str, List[str]] = {}
        self.impact_events: Dict[str, List[str]] = {}
    
    def add_event(self, event: CalendarEvent) -> None:
        """
        イベントを追加
        
        Args:
            event: カレンダーイベント
        """
        self.events[event.calendar_id] = event
        
        # 国別インデックス
        if event.country not in self.country_events:
            self.country_events[event.country] = []
        self.country_events[event.country].append(event.calendar_id)
        
        # 通貨別インデックス
        if event.currency_impact:
            if event.currency_impact not in self.currency_events:
                self.currency_events[event.currency_impact] = []
            self.currency_events[event.currency_impact].append(event.calendar_id)
        
        # 影響度別インデックス
        if event.impact_level not in self.impact_events:
            self.impact_events[event.impact_level] = []
        self.impact_events[event.impact_level].append(event.calendar_id)
        
        logger.info(f"Added calendar event: {event.calendar_id}")
    
    def remove_event(self, calendar_id: str) -> bool:
        """
        イベントを削除
        
        Args:
            calendar_id: カレンダーID
            
        Returns:
            削除が成功したかどうか
        """
        if calendar_id not in self.events:
            return False
        
        event = self.events[calendar_id]
        
        # インデックスから削除
        if event.country in self.country_events:
            self.country_events[event.country].remove(calendar_id)
            if not self.country_events[event.country]:
                del self.country_events[event.country]
        
        if event.currency_impact and event.currency_impact in self.currency_events:
            self.currency_events[event.currency_impact].remove(calendar_id)
            if not self.currency_events[event.currency_impact]:
                del self.currency_events[event.currency_impact]
        
        if event.impact_level in self.impact_events:
            self.impact_events[event.impact_level].remove(calendar_id)
            if not self.impact_events[event.impact_level]:
                del self.impact_events[event.impact_level]
        
        # イベントを削除
        del self.events[calendar_id]
        
        logger.info(f"Removed calendar event: {calendar_id}")
        return True
    
    def get_event(self, calendar_id: str) -> Optional[CalendarEvent]:
        """
        イベントを取得
        
        Args:
            calendar_id: カレンダーID
            
        Returns:
            カレンダーイベント、またはNone
        """
        return self.events.get(calendar_id)
    
    def get_events_by_country(self, country: str) -> List[CalendarEvent]:
        """
        国別のイベントを取得
        
        Args:
            country: 国名
            
        Returns:
            イベントのリスト
        """
        event_ids = self.country_events.get(country, [])
        return [self.events[event_id] for event_id in event_ids if event_id in self.events]
    
    def get_events_by_currency(self, currency: str) -> List[CalendarEvent]:
        """
        通貨別のイベントを取得
        
        Args:
            currency: 通貨コード
            
        Returns:
            イベントのリスト
        """
        event_ids = self.currency_events.get(currency, [])
        return [self.events[event_id] for event_id in event_ids if event_id in self.events]
    
    def get_events_by_impact(self, impact_level: str) -> List[CalendarEvent]:
        """
        影響度別のイベントを取得
        
        Args:
            impact_level: 影響度
            
        Returns:
            イベントのリスト
        """
        event_ids = self.impact_events.get(impact_level, [])
        return [self.events[event_id] for event_id in event_ids if event_id in self.events]
    
    def get_events_in_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[CalendarEvent]:
        """
        指定期間内のイベントを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            イベントのリスト
        """
        events = []
        for event in self.events.values():
            if start_date <= event.scheduled_release <= end_date:
                events.append(event)
        
        # 日時でソート
        events.sort(key=lambda x: x.scheduled_release)
        return events
    
    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """
        今後のイベントを取得
        
        Args:
            hours: 取得する時間範囲（時間）
            
        Returns:
            イベントのリスト
        """
        now = datetime.now()
        end_time = now + timedelta(hours=hours)
        return self.get_events_in_range(now, end_time)
    
    def get_today_events(self) -> List[CalendarEvent]:
        """
        今日のイベントを取得
        
        Returns:
            イベントのリスト
        """
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        end_of_day = datetime.combine(today, datetime.max.time())
        return self.get_events_in_range(start_of_day, end_of_day)
    
    def get_high_impact_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[CalendarEvent]:
        """
        高影響度のイベントを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            高影響度イベントのリスト
        """
        high_impact_events = self.get_events_by_impact("high")
        
        if start_date and end_date:
            return [
                event for event in high_impact_events
                if start_date <= event.scheduled_release <= end_date
            ]
        
        return high_impact_events
    
    def update_event_status(
        self,
        calendar_id: str,
        status: str,
        actual_release: Optional[datetime] = None
    ) -> bool:
        """
        イベントのステータスを更新
        
        Args:
            calendar_id: カレンダーID
            status: 新しいステータス
            actual_release: 実際の発表日時
            
        Returns:
            更新が成功したかどうか
        """
        if calendar_id not in self.events:
            return False
        
        event = self.events[calendar_id]
        event.status = status
        
        if actual_release:
            # 実際の発表日時を設定（この場合はCalendarEventを拡張する必要がある）
            pass
        
        logger.info(f"Updated event status: {calendar_id} -> {status}")
        return True
    
    def get_events_by_indicator(self, indicator_name: str) -> List[CalendarEvent]:
        """
        指標別のイベントを取得
        
        Args:
            indicator_name: 指標名
            
        Returns:
            イベントのリスト
        """
        events = []
        for event in self.events.values():
            if event.indicator_name.lower() == indicator_name.lower():
                events.append(event)
        
        # 日時でソート
        events.sort(key=lambda x: x.scheduled_release)
        return events
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        total_events = len(self.events)
        
        # 国別統計
        country_stats = {}
        for country, event_ids in self.country_events.items():
            country_stats[country] = len(event_ids)
        
        # 通貨別統計
        currency_stats = {}
        for currency, event_ids in self.currency_events.items():
            currency_stats[currency] = len(event_ids)
        
        # 影響度別統計
        impact_stats = {}
        for impact, event_ids in self.impact_events.items():
            impact_stats[impact] = len(event_ids)
        
        # 今日のイベント数
        today_events = len(self.get_today_events())
        
        # 今後のイベント数（24時間）
        upcoming_events = len(self.get_upcoming_events(24))
        
        return {
            "total_events": total_events,
            "country_statistics": country_stats,
            "currency_statistics": currency_stats,
            "impact_statistics": impact_stats,
            "today_events": today_events,
            "upcoming_events_24h": upcoming_events
        }
    
    def export_events(self) -> Dict[str, Any]:
        """
        イベントをエクスポート
        
        Returns:
            エクスポートされたイベント
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "events": [
                {
                    "calendar_id": event.calendar_id,
                    "country": event.country,
                    "indicator_name": event.indicator_name,
                    "scheduled_release": event.scheduled_release.isoformat(),
                    "impact_level": event.impact_level,
                    "currency_impact": event.currency_impact,
                    "forecast_value": event.forecast_value,
                    "previous_value": event.previous_value,
                    "status": event.status
                }
                for event in self.events.values()
            ],
            "statistics": self.get_statistics()
        }
    
    def import_events(self, events_data: List[Dict[str, Any]]) -> int:
        """
        イベントをインポート
        
        Args:
            events_data: イベントデータ
            
        Returns:
            インポートされたイベント数
        """
        imported_count = 0
        
        for event_data in events_data:
            try:
                event = CalendarEvent(
                    calendar_id=event_data["calendar_id"],
                    country=event_data["country"],
                    indicator_name=event_data["indicator_name"],
                    scheduled_release=datetime.fromisoformat(event_data["scheduled_release"]),
                    impact_level=event_data["impact_level"],
                    currency_impact=event_data.get("currency_impact"),
                    forecast_value=event_data.get("forecast_value"),
                    previous_value=event_data.get("previous_value"),
                    status=event_data.get("status", "scheduled")
                )
                
                self.add_event(event)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Failed to import event {event_data}: {e}")
        
        return imported_count
    
    def clear_old_events(self, days: int = 30) -> int:
        """
        古いイベントをクリア
        
        Args:
            days: 保持する日数
            
        Returns:
            削除されたイベント数
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        events_to_remove = []
        for calendar_id, event in self.events.items():
            if event.scheduled_release < cutoff_date:
                events_to_remove.append(calendar_id)
        
        for calendar_id in events_to_remove:
            self.remove_event(calendar_id)
        
        return len(events_to_remove)
    
    def get_events_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        イベントサマリーを取得
        
        Args:
            days: サマリーを取得する日数
            
        Returns:
            イベントサマリー
        """
        end_date = datetime.now() + timedelta(days=days)
        events = self.get_events_in_range(datetime.now(), end_date)
        
        # 日別のイベント数
        daily_events = {}
        for event in events:
            date_key = event.scheduled_release.date().isoformat()
            if date_key not in daily_events:
                daily_events[date_key] = []
            daily_events[date_key].append(event)
        
        # 高影響度イベント
        high_impact_events = [e for e in events if e.impact_level == "high"]
        
        # 通貨別イベント
        currency_events = {}
        for event in events:
            if event.currency_impact:
                if event.currency_impact not in currency_events:
                    currency_events[event.currency_impact] = []
                currency_events[event.currency_impact].append(event)
        
        return {
            "total_events": len(events),
            "high_impact_events": len(high_impact_events),
            "daily_events": {
                date: len(events_list) for date, events_list in daily_events.items()
            },
            "currency_events": {
                currency: len(events_list) for currency, events_list in currency_events.items()
            },
            "next_high_impact": (
                high_impact_events[0].scheduled_release.isoformat()
                if high_impact_events else None
            )
        }
