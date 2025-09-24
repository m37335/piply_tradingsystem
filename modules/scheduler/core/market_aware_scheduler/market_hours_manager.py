"""
市場時間管理

各市場の営業時間とタイムゾーンを管理します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, time, timedelta
from dataclasses import dataclass
from enum import Enum
import pytz

logger = logging.getLogger(__name__)


class Market(Enum):
    """市場"""
    TOKYO = "tokyo"        # 東京証券取引所
    NEW_YORK = "new_york"  # ニューヨーク証券取引所
    LONDON = "london"      # ロンドン証券取引所
    SYDNEY = "sydney"      # シドニー証券取引所
    FRANKFURT = "frankfurt" # フランクフルト証券取引所
    HONG_KONG = "hong_kong" # 香港証券取引所
    SINGAPORE = "singapore" # シンガポール証券取引所


class MarketStatus(Enum):
    """市場ステータス"""
    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    HOLIDAY = "holiday"


@dataclass
class MarketHours:
    """市場営業時間"""
    market: Market
    timezone: str
    open_time: time
    close_time: time
    days: List[str]  # 営業日（monday, tuesday, etc.）
    extended_hours: bool = False
    pre_market_open: Optional[time] = None
    after_hours_close: Optional[time] = None


class MarketHoursManager:
    """市場時間管理クラス"""
    
    def __init__(self):
        self.market_hours: Dict[Market, MarketHours] = {}
        self._initialize_default_market_hours()
    
    def _initialize_default_market_hours(self) -> None:
        """デフォルトの市場営業時間を初期化"""
        
        # 東京証券取引所
        self.market_hours[Market.TOKYO] = MarketHours(
            market=Market.TOKYO,
            timezone="Asia/Tokyo",
            open_time=time(9, 0),
            close_time=time(15, 0),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"]
        )
        
        # ニューヨーク証券取引所
        self.market_hours[Market.NEW_YORK] = MarketHours(
            market=Market.NEW_YORK,
            timezone="America/New_York",
            open_time=time(9, 30),
            close_time=time(16, 0),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"],
            extended_hours=True,
            pre_market_open=time(4, 0),
            after_hours_close=time(20, 0)
        )
        
        # ロンドン証券取引所
        self.market_hours[Market.LONDON] = MarketHours(
            market=Market.LONDON,
            timezone="Europe/London",
            open_time=time(8, 0),
            close_time=time(16, 30),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"]
        )
        
        # シドニー証券取引所
        self.market_hours[Market.SYDNEY] = MarketHours(
            market=Market.SYDNEY,
            timezone="Australia/Sydney",
            open_time=time(10, 0),
            close_time=time(16, 0),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"]
        )
        
        # フランクフルト証券取引所
        self.market_hours[Market.FRANKFURT] = MarketHours(
            market=Market.FRANKFURT,
            timezone="Europe/Berlin",
            open_time=time(9, 0),
            close_time=time(17, 30),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"]
        )
        
        # 香港証券取引所
        self.market_hours[Market.HONG_KONG] = MarketHours(
            market=Market.HONG_KONG,
            timezone="Asia/Hong_Kong",
            open_time=time(9, 30),
            close_time=time(16, 0),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"]
        )
        
        # シンガポール証券取引所
        self.market_hours[Market.SINGAPORE] = MarketHours(
            market=Market.SINGAPORE,
            timezone="Asia/Singapore",
            open_time=time(9, 0),
            close_time=time(17, 0),
            days=["monday", "tuesday", "wednesday", "thursday", "friday"]
        )
    
    def is_market_open(self, market: Market, check_time: Optional[datetime] = None) -> bool:
        """市場が開いているかチェック"""
        if check_time is None:
            check_time = datetime.now()
        
        market_hours = self.market_hours.get(market)
        if not market_hours:
            return False
        
        # タイムゾーンを変換
        market_tz = pytz.timezone(market_hours.timezone)
        market_time = check_time.astimezone(market_tz)
        
        # 曜日チェック
        day_name = market_time.strftime("%A").lower()
        if day_name not in market_hours.days:
            return False
        
        # 時間チェック
        current_time = market_time.time()
        
        if market_hours.extended_hours:
            # 延長取引時間を考慮
            if (market_hours.pre_market_open and 
                market_hours.pre_market_open <= current_time < market_hours.open_time):
                return True  # プレマーケット
            
            if (market_hours.after_hours_close and 
                market_hours.close_time < current_time <= market_hours.after_hours_close):
                return True  # アフターハワーズ
        
        # 通常営業時間
        return market_hours.open_time <= current_time <= market_hours.close_time
    
    def get_market_status(self, market: Market, check_time: Optional[datetime] = None) -> str:
        """市場の状態を取得"""
        if check_time is None:
            check_time = datetime.now()
        
        market_hours = self.market_hours.get(market)
        if not market_hours:
            return "unknown"
        
        # タイムゾーンを変換
        market_tz = pytz.timezone(market_hours.timezone)
        market_time = check_time.astimezone(market_tz)
        
        # 曜日チェック
        day_name = market_time.strftime("%A").lower()
        if day_name not in market_hours.days:
            return "closed"
        
        current_time = market_time.time()
        
        if market_hours.extended_hours:
            # 延長取引時間を考慮
            if (market_hours.pre_market_open and 
                market_hours.pre_market_open <= current_time < market_hours.open_time):
                return "pre_market"
            
            if (market_hours.after_hours_close and 
                market_hours.close_time < current_time <= market_hours.after_hours_close):
                return "after_hours"
        
        # 通常営業時間
        if market_hours.open_time <= current_time <= market_hours.close_time:
            return "open"
        else:
            return "closed"
    
    def get_next_market_open(self, market: Market, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """次の市場開始時間を取得"""
        if from_time is None:
            from_time = datetime.now()
        
        market_hours = self.market_hours.get(market)
        if not market_hours:
            return None
        
        market_tz = pytz.timezone(market_hours.timezone)
        market_time = from_time.astimezone(market_tz)
        
        # 次の営業日を探す
        for days_ahead in range(8):  # 最大1週間先まで
            check_date = market_time + timedelta(days=days_ahead)
            day_name = check_date.strftime("%A").lower()
            
            if day_name in market_hours.days:
                # 営業日の開始時間を計算
                next_open = market_tz.localize(
                    datetime.combine(check_date.date(), market_hours.open_time)
                )
                
                # 過去の時間でない場合のみ返す
                if next_open > from_time:
                    return next_open
        
        return None
    
    def get_next_market_close(self, market: Market, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """次の市場終了時間を取得"""
        if from_time is None:
            from_time = datetime.now()
        
        market_hours = self.market_hours.get(market)
        if not market_hours:
            return None
        
        market_tz = pytz.timezone(market_hours.timezone)
        market_time = from_time.astimezone(market_tz)
        
        # 現在の営業日の終了時間をチェック
        day_name = market_time.strftime("%A").lower()
        if day_name in market_hours.days:
            today_close = market_tz.localize(
                datetime.combine(market_time.date(), market_hours.close_time)
            )
            
            if today_close > from_time:
                return today_close
        
        # 次の営業日の終了時間を取得
        return self.get_next_market_open(market, from_time) + timedelta(
            hours=(market_hours.close_time.hour - market_hours.open_time.hour),
            minutes=(market_hours.close_time.minute - market_hours.open_time.minute)
        )
    
    def get_market_hours_info(self, market: Market) -> Dict[str, Any]:
        """市場営業時間情報を取得"""
        market_hours = self.market_hours.get(market)
        if not market_hours:
            return {}
        
        return {
            "market": market.value,
            "timezone": market_hours.timezone,
            "open_time": market_hours.open_time.strftime("%H:%M"),
            "close_time": market_hours.close_time.strftime("%H:%M"),
            "days": market_hours.days,
            "extended_hours": market_hours.extended_hours,
            "pre_market_open": market_hours.pre_market_open.strftime("%H:%M") if market_hours.pre_market_open else None,
            "after_hours_close": market_hours.after_hours_close.strftime("%H:%M") if market_hours.after_hours_close else None
        }
    
    def get_all_markets_status(self, check_time: Optional[datetime] = None) -> Dict[str, str]:
        """すべての市場の状態を取得"""
        if check_time is None:
            check_time = datetime.now()
        
        status = {}
        for market in Market:
            status[market.value] = self.get_market_status(market, check_time)
        
        return status
    
    def is_any_market_open(self, markets: List[Market], check_time: Optional[datetime] = None) -> bool:
        """指定された市場のいずれかが開いているかチェック"""
        for market in markets:
            if self.is_market_open(market, check_time):
                return True
        return False
    
    def get_market_overlap_periods(self, market1: Market, market2: Market) -> List[Dict[str, Any]]:
        """2つの市場の重複時間を取得"""
        # 簡易実装：詳細な重複時間計算は複雑なため、基本的な情報のみ返す
        status1 = self.get_market_status(market1)
        status2 = self.get_market_status(market2)
        
        if status1 == "open" and status2 == "open":
            return [{"status": "overlap", "markets": [market1.value, market2.value]}]
        
        return []
