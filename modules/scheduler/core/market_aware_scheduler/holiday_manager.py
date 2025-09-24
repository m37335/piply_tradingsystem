"""
祝日管理システム

市場の祝日と休業日を管理します。
"""

import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Holiday:
    """祝日情報"""
    date: date
    name: str
    description: str = ""
    is_market_holiday: bool = True
    is_partial_day: bool = False  # 部分的な休業日かどうか


class HolidayManager:
    """祝日管理システム"""
    
    def __init__(self):
        self.holidays: Dict[date, Holiday] = {}
        self.market_holidays: Set[date] = set()
        self.partial_holidays: Set[date] = set()
        self._init_default_holidays()
    
    def _init_default_holidays(self) -> None:
        """デフォルトの祝日を初期化"""
        # 2024年の米国祝日（例）
        default_holidays = [
            Holiday(date(2024, 1, 1), "New Year's Day", "新年"),
            Holiday(date(2024, 1, 15), "Martin Luther King Jr. Day", "マーティン・ルーサー・キング・ジュニア記念日"),
            Holiday(date(2024, 2, 19), "Presidents' Day", "大統領の日"),
            Holiday(date(2024, 3, 29), "Good Friday", "聖金曜日"),
            Holiday(date(2024, 5, 27), "Memorial Day", "戦没将兵追悼記念日"),
            Holiday(date(2024, 6, 19), "Juneteenth", "ジュンティーンス"),
            Holiday(date(2024, 7, 4), "Independence Day", "独立記念日"),
            Holiday(date(2024, 9, 2), "Labor Day", "労働者の日"),
            Holiday(date(2024, 11, 28), "Thanksgiving Day", "感謝祭"),
            Holiday(date(2024, 12, 25), "Christmas Day", "クリスマス"),
        ]
        
        for holiday in default_holidays:
            self.add_holiday(holiday)
    
    def add_holiday(self, holiday: Holiday) -> None:
        """
        祝日を追加
        
        Args:
            holiday: 祝日情報
        """
        self.holidays[holiday.date] = holiday
        
        if holiday.is_market_holiday:
            self.market_holidays.add(holiday.date)
        
        if holiday.is_partial_day:
            self.partial_holidays.add(holiday.date)
        
        logger.info(f"Added holiday: {holiday.name} on {holiday.date}")
    
    def remove_holiday(self, holiday_date: date) -> bool:
        """
        祝日を削除
        
        Args:
            holiday_date: 祝日
        """
        if holiday_date in self.holidays:
            holiday = self.holidays[holiday_date]
            del self.holidays[holiday_date]
            
            if holiday.is_market_holiday:
                self.market_holidays.discard(holiday_date)
            
            if holiday.is_partial_day:
                self.partial_holidays.discard(holiday_date)
            
            logger.info(f"Removed holiday: {holiday.name} on {holiday_date}")
            return True
        
        return False
    
    def is_holiday(self, check_date: date) -> bool:
        """
        指定日が祝日かどうかチェック
        
        Args:
            check_date: チェックする日付
            
        Returns:
            祝日かどうか
        """
        return check_date in self.holidays
    
    def is_market_holiday(self, check_date: date) -> bool:
        """
        指定日が市場休業日かどうかチェック
        
        Args:
            check_date: チェックする日付
            
        Returns:
            市場休業日かどうか
        """
        return check_date in self.market_holidays
    
    def is_partial_holiday(self, check_date: date) -> bool:
        """
        指定日が部分的な休業日かどうかチェック
        
        Args:
            check_date: チェックする日付
            
        Returns:
            部分的な休業日かどうか
        """
        return check_date in self.partial_holidays
    
    def get_holiday(self, check_date: date) -> Optional[Holiday]:
        """
        指定日の祝日情報を取得
        
        Args:
            check_date: チェックする日付
            
        Returns:
            祝日情報、またはNone
        """
        return self.holidays.get(check_date)
    
    def get_holidays_in_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Holiday]:
        """
        指定期間内の祝日を取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            祝日のリスト
        """
        holidays = []
        current_date = start_date
        
        while current_date <= end_date:
            if current_date in self.holidays:
                holidays.append(self.holidays[current_date])
            current_date += timedelta(days=1)
        
        return holidays
    
    def get_market_holidays_in_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[Holiday]:
        """
        指定期間内の市場休業日を取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            市場休業日のリスト
        """
        holidays = self.get_holidays_in_range(start_date, end_date)
        return [h for h in holidays if h.is_market_holiday]
    
    def get_next_holiday(self, from_date: Optional[date] = None) -> Optional[Holiday]:
        """
        次の祝日を取得
        
        Args:
            from_date: 基準日（Noneの場合は今日）
            
        Returns:
            次の祝日、またはNone
        """
        if from_date is None:
            from_date = date.today()
        
        next_holiday = None
        next_holiday_date = None
        
        for holiday_date, holiday in self.holidays.items():
            if holiday_date > from_date:
                if next_holiday_date is None or holiday_date < next_holiday_date:
                    next_holiday = holiday
                    next_holiday_date = holiday_date
        
        return next_holiday
    
    def get_next_market_holiday(self, from_date: Optional[date] = None) -> Optional[Holiday]:
        """
        次の市場休業日を取得
        
        Args:
            from_date: 基準日（Noneの場合は今日）
            
        Returns:
            次の市場休業日、またはNone
        """
        if from_date is None:
            from_date = date.today()
        
        next_holiday = None
        next_holiday_date = None
        
        for holiday_date, holiday in self.holidays.items():
            if holiday_date > from_date and holiday.is_market_holiday:
                if next_holiday_date is None or holiday_date < next_holiday_date:
                    next_holiday = holiday
                    next_holiday_date = holiday_date
        
        return next_holiday
    
    def get_previous_holiday(self, from_date: Optional[date] = None) -> Optional[Holiday]:
        """
        前の祝日を取得
        
        Args:
            from_date: 基準日（Noneの場合は今日）
            
        Returns:
            前の祝日、またはNone
        """
        if from_date is None:
            from_date = date.today()
        
        previous_holiday = None
        previous_holiday_date = None
        
        for holiday_date, holiday in self.holidays.items():
            if holiday_date < from_date:
                if previous_holiday_date is None or holiday_date > previous_holiday_date:
                    previous_holiday = holiday
                    previous_holiday_date = holiday_date
        
        return previous_holiday
    
    def get_previous_market_holiday(self, from_date: Optional[date] = None) -> Optional[Holiday]:
        """
        前の市場休業日を取得
        
        Args:
            from_date: 基準日（Noneの場合は今日）
            
        Returns:
            前の市場休業日、またはNone
        """
        if from_date is None:
            from_date = date.today()
        
        previous_holiday = None
        previous_holiday_date = None
        
        for holiday_date, holiday in self.holidays.items():
            if holiday_date < from_date and holiday.is_market_holiday:
                if previous_holiday_date is None or holiday_date > previous_holiday_date:
                    previous_holiday = holiday
                    previous_holiday_date = holiday_date
        
        return previous_holiday
    
    def get_holiday_statistics(self) -> Dict[str, any]:
        """
        祝日の統計情報を取得
        
        Returns:
            統計情報
        """
        total_holidays = len(self.holidays)
        market_holidays = len(self.market_holidays)
        partial_holidays = len(self.partial_holidays)
        
        # 今年の祝日数
        current_year = date.today().year
        year_start = date(current_year, 1, 1)
        year_end = date(current_year, 12, 31)
        
        year_holidays = self.get_holidays_in_range(year_start, year_end)
        year_market_holidays = [h for h in year_holidays if h.is_market_holiday]
        
        return {
            "total_holidays": total_holidays,
            "market_holidays": market_holidays,
            "partial_holidays": partial_holidays,
            "current_year_holidays": len(year_holidays),
            "current_year_market_holidays": len(year_market_holidays),
            "next_holiday": self.get_next_holiday(),
            "next_market_holiday": self.get_next_market_holiday(),
        }
    
    def is_trading_day(self, check_date: date) -> bool:
        """
        指定日が取引日かどうかチェック
        
        Args:
            check_date: チェックする日付
            
        Returns:
            取引日かどうか
        """
        # 週末チェック
        if check_date.weekday() >= 5:  # 土曜日(5)または日曜日(6)
            return False
        
        # 市場休業日チェック
        if self.is_market_holiday(check_date):
            return False
        
        return True
    
    def get_next_trading_day(self, from_date: Optional[date] = None) -> date:
        """
        次の取引日を取得
        
        Args:
            from_date: 基準日（Noneの場合は今日）
            
        Returns:
            次の取引日
        """
        if from_date is None:
            from_date = date.today()
        
        next_date = from_date + timedelta(days=1)
        
        while not self.is_trading_day(next_date):
            next_date += timedelta(days=1)
        
        return next_date
    
    def get_previous_trading_day(self, from_date: Optional[date] = None) -> date:
        """
        前の取引日を取得
        
        Args:
            from_date: 基準日（Noneの場合は今日）
            
        Returns:
            前の取引日
        """
        if from_date is None:
            from_date = date.today()
        
        previous_date = from_date - timedelta(days=1)
        
        while not self.is_trading_day(previous_date):
            previous_date -= timedelta(days=1)
        
        return previous_date
    
    def get_trading_days_in_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[date]:
        """
        指定期間内の取引日を取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            取引日のリスト
        """
        trading_days = []
        current_date = start_date
        
        while current_date <= end_date:
            if self.is_trading_day(current_date):
                trading_days.append(current_date)
            current_date += timedelta(days=1)
        
        return trading_days
    
    def export_holidays(self) -> Dict[str, any]:
        """
        祝日情報をエクスポート
        
        Returns:
            祝日情報
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "holidays": [
                {
                    "date": holiday.date.isoformat(),
                    "name": holiday.name,
                    "description": holiday.description,
                    "is_market_holiday": holiday.is_market_holiday,
                    "is_partial_day": holiday.is_partial_day
                }
                for holiday in self.holidays.values()
            ],
            "statistics": self.get_holiday_statistics()
        }
    
    def import_holidays(self, holidays_data: List[Dict[str, any]]) -> int:
        """
        祝日情報をインポート
        
        Args:
            holidays_data: 祝日データ
            
        Returns:
            インポートされた祝日数
        """
        imported_count = 0
        
        for holiday_data in holidays_data:
            try:
                holiday = Holiday(
                    date=datetime.fromisoformat(holiday_data["date"]).date(),
                    name=holiday_data["name"],
                    description=holiday_data.get("description", ""),
                    is_market_holiday=holiday_data.get("is_market_holiday", True),
                    is_partial_day=holiday_data.get("is_partial_day", False)
                )
                
                self.add_holiday(holiday)
                imported_count += 1
                
            except Exception as e:
                logger.error(f"Failed to import holiday {holiday_data}: {e}")
        
        return imported_count
