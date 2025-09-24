"""
Investing.com カレンダープロバイダー

Investing.comの経済カレンダーから経済指標データを取得します。
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
from bs4 import BeautifulSoup

from .base_economic_provider import BaseEconomicProvider, EconomicDataResult

logger = logging.getLogger(__name__)


class InvestingCalendarProvider(BaseEconomicProvider):
    """Investing.comカレンダープロバイダー"""
    
    def __init__(self):
        """Investing.comカレンダープロバイダーを初期化"""
        super().__init__("Investing.com")
        self.base_url = "https://www.investing.com/economic-calendar"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> None:
        """プロバイダーを初期化"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        logger.info("Investing.com calendar provider initialized")
    
    async def close(self) -> None:
        """プロバイダーを閉じる"""
        if self.session:
            await self.session.close()
        logger.info("Investing.com calendar provider closed")
    
    async def get_economic_calendar(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        countries: Optional[List[str]] = None,
        importance: Optional[List[str]] = None
    ) -> EconomicDataResult:
        """
        経済カレンダーを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国リスト
            importance: 重要度リスト (low, medium, high)
            
        Returns:
            経済カレンダーデータ
        """
        try:
            if not self.session:
                await self.initialize()
            
            # パラメータを準備
            params = {}
            
            if start_date:
                params["dateFrom"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["dateTo"] = end_date.strftime("%Y-%m-%d")
            
            # 国フィルター
            if countries:
                country_codes = self._get_country_codes(countries)
                if country_codes:
                    params["country[]"] = country_codes
            
            # 重要度フィルター
            if importance:
                importance_map = {
                    "low": "1",
                    "medium": "2", 
                    "high": "3"
                }
                importance_codes = [importance_map.get(imp.lower(), "2") for imp in importance]
                if importance_codes:
                    params["importance[]"] = importance_codes
            
            # APIリクエスト
            async with self.session.get(self.base_url, params=params) as response:
                if response.status == 200:
                    html_content = await response.text()
                    return self._parse_calendar_html(html_content, start_date, end_date)
                else:
                    logger.error(f"Investing.com API error: {response.status}")
                    return EconomicDataResult(
                        success=False,
                        error_message=f"HTTP error: {response.status}",
                        data=None
                    )
        
        except Exception as e:
            logger.error(f"Error fetching Investing.com calendar: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    def _parse_calendar_html(
        self,
        html_content: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> EconomicDataResult:
        """
        HTMLコンテンツを解析
        
        Args:
            html_content: HTMLコンテンツ
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            経済カレンダーデータ
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # カレンダーテーブルを探す
            calendar_table = soup.find('table', {'id': 'economicCalendarData'})
            
            if not calendar_table:
                return EconomicDataResult(
                    success=False,
                    error_message="Calendar table not found",
                    data=None
                )
            
            events = []
            rows = calendar_table.find_all('tr', {'class': 'js-event-item'})
            
            for row in rows:
                event_data = self._parse_event_row(row)
                if event_data:
                    events.append(event_data)
            
            return EconomicDataResult(
                success=True,
                data={
                    "events": events,
                    "total_events": len(events),
                    "start_date": start_date,
                    "end_date": end_date,
                    "source": "Investing.com"
                },
                metadata={
                    "provider": "Investing.com",
                    "parsed_at": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing Investing.com HTML: {e}")
            return EconomicDataResult(
                success=False,
                error_message=f"Parse error: {e}",
                data=None
            )
    
    def _parse_event_row(self, row) -> Optional[Dict[str, Any]]:
        """
        イベント行を解析
        
        Args:
            row: HTML行要素
            
        Returns:
            イベントデータ、またはNone
        """
        try:
            cells = row.find_all('td')
            
            if len(cells) < 6:
                return None
            
            # 時間
            time_cell = cells[0]
            time_text = time_cell.get_text(strip=True)
            
            # 通貨
            currency_cell = cells[1]
            currency = currency_cell.get_text(strip=True)
            
            # 重要度
            importance_cell = cells[2]
            importance_icon = importance_cell.find('i')
            importance = "medium"  # デフォルト
            if importance_icon:
                icon_class = importance_icon.get('class', [])
                if 'iconBull' in icon_class:
                    importance = "high"
                elif 'iconBear' in icon_class:
                    importance = "low"
            
            # イベント名
            event_cell = cells[3]
            event_name = event_cell.get_text(strip=True)
            
            # 実際の値
            actual_cell = cells[4]
            actual_value = actual_cell.get_text(strip=True)
            
            # 予想値
            forecast_cell = cells[5]
            forecast_value = forecast_cell.get_text(strip=True)
            
            # 前回値
            previous_cell = cells[6] if len(cells) > 6 else None
            previous_value = previous_cell.get_text(strip=True) if previous_cell else None
            
            return {
                "time": time_text,
                "currency": currency,
                "importance": importance,
                "event_name": event_name,
                "actual_value": actual_value,
                "forecast_value": forecast_value,
                "previous_value": previous_value,
                "parsed_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.warning(f"Error parsing event row: {e}")
            return None
    
    def _get_country_codes(self, countries: List[str]) -> List[str]:
        """
        国名から国コードを取得
        
        Args:
            countries: 国名リスト
            
        Returns:
            国コードリスト
        """
        country_mapping = {
            "united states": "5",
            "usa": "5",
            "us": "5",
            "japan": "35",
            "germany": "17",
            "united kingdom": "4",
            "uk": "4",
            "france": "22",
            "italy": "10",
            "spain": "26",
            "canada": "6",
            "australia": "25",
            "china": "37",
            "india": "14",
            "brazil": "32",
            "russia": "56",
            "south korea": "11",
            "mexico": "39",
            "switzerland": "12",
            "netherlands": "21",
            "sweden": "8",
            "norway": "15",
            "denmark": "24",
            "finland": "23",
            "poland": "53",
            "czech republic": "55",
            "hungary": "54",
            "turkey": "33",
            "south africa": "110",
            "new zealand": "43",
            "singapore": "36",
            "hong kong": "34",
            "taiwan": "38",
            "thailand": "41",
            "malaysia": "42",
            "indonesia": "40",
            "philippines": "45",
            "vietnam": "47",
            "israel": "27",
            "saudi arabia": "48",
            "uae": "49",
            "egypt": "20",
            "nigeria": "60",
            "kenya": "57",
            "morocco": "58",
            "argentina": "29",
            "chile": "30",
            "colombia": "31",
            "peru": "44",
            "venezuela": "46"
        }
        
        country_codes = []
        for country in countries:
            country_lower = country.lower()
            if country_lower in country_mapping:
                country_codes.append(country_mapping[country_lower])
        
        return country_codes
    
    async def get_currency_events(
        self,
        currency: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EconomicDataResult:
        """
        通貨別のイベントを取得
        
        Args:
            currency: 通貨コード
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            通貨イベントデータ
        """
        try:
            # 通貨から国を推定
            currency_to_country = {
                "USD": ["united states"],
                "EUR": ["germany", "france", "italy", "spain"],
                "JPY": ["japan"],
                "GBP": ["united kingdom"],
                "CAD": ["canada"],
                "AUD": ["australia"],
                "CHF": ["switzerland"],
                "CNY": ["china"],
                "INR": ["india"],
                "BRL": ["brazil"],
                "RUB": ["russia"],
                "KRW": ["south korea"],
                "MXN": ["mexico"],
                "SEK": ["sweden"],
                "NOK": ["norway"],
                "DKK": ["denmark"],
                "PLN": ["poland"],
                "CZK": ["czech republic"],
                "HUF": ["hungary"],
                "TRY": ["turkey"],
                "ZAR": ["south africa"],
                "NZD": ["new zealand"],
                "SGD": ["singapore"],
                "HKD": ["hong kong"],
                "TWD": ["taiwan"],
                "THB": ["thailand"],
                "MYR": ["malaysia"],
                "IDR": ["indonesia"],
                "PHP": ["philippines"],
                "VND": ["vietnam"],
                "ILS": ["israel"],
                "SAR": ["saudi arabia"],
                "AED": ["uae"],
                "EGP": ["egypt"],
                "NGN": ["nigeria"],
                "KES": ["kenya"],
                "MAD": ["morocco"],
                "ARS": ["argentina"],
                "CLP": ["chile"],
                "COP": ["colombia"],
                "PEN": ["peru"],
                "VES": ["venezuela"]
            }
            
            countries = currency_to_country.get(currency.upper(), [])
            
            if not countries:
                return EconomicDataResult(
                    success=False,
                    error_message=f"Unknown currency: {currency}",
                    data=None
                )
            
            # 経済カレンダーを取得
            result = await self.get_economic_calendar(
                start_date=start_date,
                end_date=end_date,
                countries=countries
            )
            
            if result.success and result.data:
                # 通貨でフィルタリング
                events = result.data.get("events", [])
                filtered_events = [
                    event for event in events
                    if event.get("currency", "").upper() == currency.upper()
                ]
                
                result.data["events"] = filtered_events
                result.data["total_events"] = len(filtered_events)
                result.data["currency"] = currency
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching currency events: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    async def get_high_impact_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EconomicDataResult:
        """
        高影響度のイベントを取得
        
        Args:
            start_date: 開始日
            end_date: 終了日
            
        Returns:
            高影響度イベントデータ
        """
        try:
            result = await self.get_economic_calendar(
                start_date=start_date,
                end_date=end_date,
                importance=["high"]
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Error fetching high impact events: {e}")
            return EconomicDataResult(
                success=False,
                error_message=str(e),
                data=None
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック
        
        Returns:
            ヘルス情報
        """
        try:
            # 今日のカレンダーを取得してヘルスチェック
            today = datetime.now()
            result = await self.get_economic_calendar(
                start_date=today,
                end_date=today
            )
            
            return {
                "status": "healthy" if result.success else "unhealthy",
                "provider": "Investing.com",
                "website_accessible": result.success,
                "error": result.error_message if not result.success else None
            }
        
        except Exception as e:
            logger.error(f"Investing.com health check failed: {e}")
            return {
                "status": "unhealthy",
                "provider": "Investing.com",
                "website_accessible": False,
                "error": str(e)
            }
