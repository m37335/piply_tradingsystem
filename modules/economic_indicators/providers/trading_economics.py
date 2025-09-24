"""
Trading Economics APIプロバイダー

Trading Economics APIを使用して経済指標データを取得します。
"""

import asyncio
import aiohttp
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from .base_economic_provider import BaseEconomicProvider, EconomicDataResult
from ...data_persistence.models.economic_indicators import (
    EconomicIndicatorModel, IndicatorType, ImpactLevel, Frequency
)
from ...data_persistence.models.economic_calendar import (
    EconomicCalendarModel, CalendarStatus
)

logger = logging.getLogger(__name__)


class TradingEconomicsProvider(BaseEconomicProvider):
    """Trading Economics APIプロバイダー"""
    
    def __init__(self, api_key: str):
        super().__init__("trading_economics")
        self.api_key = api_key
        self.base_url = "https://api.tradingeconomics.com"
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = None
    
    async def __aenter__(self):
        """非同期コンテキストマネージャーの開始"""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャーの終了"""
        if self._session:
            await self._session.close()
    
    async def get_economic_indicators(
        self,
        country: str,
        indicator_type: Optional[IndicatorType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EconomicDataResult:
        """経済指標データを取得"""
        try:
            # レート制限チェック
            if self._rate_limiter:
                await self._rate_limiter.wait_for_availability()
            
            # APIエンドポイントを構築
            url = f"{self.base_url}/historical"
            params = {
                "c": country,
                "f": "json",
                "key": self.api_key
            }
            
            if indicator_type:
                params["s"] = indicator_type.value
            
            if start_date:
                params["d1"] = start_date.strftime("%Y-%m-%d")
            
            if end_date:
                params["d2"] = end_date.strftime("%Y-%m-%d")
            
            # APIリクエストを実行
            async with self._session.get(url, params=params) as response:
                if response.status != 200:
                    return EconomicDataResult(
                        success=False,
                        data=[],
                        calendar_data=[],
                        error_message=f"API request failed with status {response.status}"
                    )
                
                data = await response.json()
            
            # データを変換
            indicators = []
            for item in data:
                try:
                    indicator = self._convert_to_indicator_model(item)
                    if indicator:
                        indicators.append(indicator)
                except Exception as e:
                    logger.warning(f"Failed to convert indicator data: {e}")
                    continue
            
            # データの妥当性チェック
            validated_indicators = self._validate_economic_data(indicators)
            
            return EconomicDataResult(
                success=True,
                data=validated_indicators,
                calendar_data=[],
                metadata={
                    'total_records': len(validated_indicators),
                    'country': country,
                    'indicator_type': indicator_type.value if indicator_type else None,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error fetching economic indicators: {e}")
            return EconomicDataResult(
                success=False,
                data=[],
                calendar_data=[],
                error_message=str(e)
            )
    
    async def get_economic_calendar(
        self,
        country: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EconomicDataResult:
        """経済指標カレンダーを取得"""
        try:
            # レート制限チェック
            if self._rate_limiter:
                await self._rate_limiter.wait_for_availability()
            
            # APIエンドポイントを構築
            url = f"{self.base_url}/calendar"
            params = {
                "f": "json",
                "key": self.api_key
            }
            
            if country:
                params["c"] = country
            
            if start_date:
                params["d1"] = start_date.strftime("%Y-%m-%d")
            
            if end_date:
                params["d2"] = end_date.strftime("%Y-%m-%d")
            
            # APIリクエストを実行
            async with self._session.get(url, params=params) as response:
                if response.status != 200:
                    return EconomicDataResult(
                        success=False,
                        data=[],
                        calendar_data=[],
                        error_message=f"API request failed with status {response.status}"
                    )
                
                data = await response.json()
            
            # データを変換
            calendar_events = []
            for item in data:
                try:
                    calendar_event = self._convert_to_calendar_model(item)
                    if calendar_event:
                        calendar_events.append(calendar_event)
                except Exception as e:
                    logger.warning(f"Failed to convert calendar data: {e}")
                    continue
            
            return EconomicDataResult(
                success=True,
                data=[],
                calendar_data=calendar_events,
                metadata={
                    'total_events': len(calendar_events),
                    'country': country,
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            )
            
        except Exception as e:
            logger.error(f"Error fetching economic calendar: {e}")
            return EconomicDataResult(
                success=False,
                data=[],
                calendar_data=[],
                error_message=str(e)
            )
    
    async def get_available_countries(self) -> List[str]:
        """利用可能な国一覧を取得"""
        # Trading Economicsの主要国コード
        return [
            "US", "JP", "EU", "GB", "CH", "AU", "CA", "NZ",
            "DE", "FR", "IT", "ES", "NL", "BE", "AT", "SE",
            "NO", "DK", "FI", "PL", "CZ", "HU", "SK", "SI",
            "CN", "KR", "IN", "BR", "MX", "AR", "CL", "CO",
            "ZA", "EG", "NG", "KE", "MA", "RU", "TR", "IL"
        ]
    
    async def get_available_indicators(self, country: str) -> List[str]:
        """利用可能な経済指標一覧を取得"""
        # 主要な経済指標
        return [
            "GDP", "GDP Growth Rate", "Inflation Rate", "Unemployment Rate",
            "Interest Rate", "Trade Balance", "Current Account",
            "Consumer Confidence", "Manufacturing PMI", "Services PMI",
            "Retail Sales", "Industrial Production", "Housing Starts",
            "Currency Reserves", "Government Debt", "Budget Balance"
        ]
    
    def is_available(self) -> bool:
        """プロバイダーが利用可能かチェック"""
        return self._is_available
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            if not self._session:
                return False
            
            # 簡単なテストリクエスト
            url = f"{self.base_url}/calendar"
            params = {
                "f": "json",
                "key": self.api_key,
                "d1": datetime.now().strftime("%Y-%m-%d"),
                "d2": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            }
            
            async with self._session.get(url, params=params) as response:
                if response.status == 200:
                    self._is_available = True
                    return True
                else:
                    self._is_available = False
                    return False
                    
        except Exception as e:
            logger.error(f"Trading Economics health check failed: {e}")
            self._is_available = False
            return False
    
    def _convert_to_indicator_model(self, data: Dict[str, Any]) -> Optional[EconomicIndicatorModel]:
        """APIデータをEconomicIndicatorModelに変換"""
        try:
            # 指標タイプを判定
            indicator_type = self._map_indicator_type(data.get("Category", ""))
            if not indicator_type:
                return None
            
            # 頻度を判定
            frequency = self._map_frequency(data.get("Frequency", ""))
            
            # 発表情報を解析
            release_date = datetime.fromisoformat(data["DateTime"].replace("Z", "+00:00"))
            
            # 期間を設定（デフォルトは前月）
            period_end = release_date.replace(day=1) - timedelta(days=1)
            period_start = period_end.replace(day=1)
            
            # 影響レベルを計算
            impact_level = self._calculate_impact_level(indicator_type, data.get("Country", ""))
            
            # 通貨影響を判定
            currency_impact = self._determine_currency_impact(data.get("Country", ""), indicator_type)
            
            # 品質スコアを計算
            quality_score = self._calculate_quality_score_from_raw_data(data)
            
            return EconomicIndicatorModel(
                indicator_id=f"{data.get('Country', '')}_{indicator_type.value}_{release_date.strftime('%Y%m%d')}",
                country=data.get("Country", ""),
                indicator_name=data.get("Category", ""),
                indicator_type=indicator_type,
                value=float(data.get("Actual", 0)),
                unit=data.get("Unit", ""),
                frequency=frequency,
                release_date=release_date,
                period_start=period_start,
                period_end=period_end,
                forecast_value=float(data.get("Forecast", 0)) if data.get("Forecast") else None,
                previous_value=float(data.get("Previous", 0)) if data.get("Previous") else None,
                impact_level=impact_level,
                currency_impact=currency_impact,
                source=self.name,
                data_quality_score=quality_score
            )
            
        except Exception as e:
            logger.error(f"Failed to convert indicator data: {e}")
            return None
    
    def _convert_to_calendar_model(self, data: Dict[str, Any]) -> Optional[EconomicCalendarModel]:
        """APIデータをEconomicCalendarModelに変換"""
        try:
            # 指標タイプを判定
            indicator_type = self._map_indicator_type(data.get("Category", ""))
            if not indicator_type:
                return None
            
            # 発表情報を解析
            scheduled_release = datetime.fromisoformat(data["DateTime"].replace("Z", "+00:00"))
            
            # 頻度を判定
            frequency = self._map_frequency(data.get("Frequency", ""))
            
            # 影響レベルを計算
            impact_level = self._calculate_impact_level(indicator_type, data.get("Country", ""))
            
            # 通貨影響を判定
            currency_impact = self._determine_currency_impact(data.get("Country", ""), indicator_type)
            
            # ステータスを判定
            status = CalendarStatus.SCHEDULED
            if data.get("Actual") is not None:
                status = CalendarStatus.RELEASED
            
            return EconomicCalendarModel(
                calendar_id=f"{data.get('Country', '')}_{indicator_type.value}_{scheduled_release.strftime('%Y%m%d_%H%M')}",
                country=data.get("Country", ""),
                indicator_name=data.get("Category", ""),
                indicator_type=indicator_type,
                scheduled_release=scheduled_release,
                frequency=frequency,
                impact_level=impact_level,
                currency_impact=currency_impact,
                forecast_value=float(data.get("Forecast", 0)) if data.get("Forecast") else None,
                previous_value=float(data.get("Previous", 0)) if data.get("Previous") else None,
                status=status,
                source=self.name
            )
            
        except Exception as e:
            logger.error(f"Failed to convert calendar data: {e}")
            return None
    
    def _map_indicator_type(self, category: str) -> Optional[IndicatorType]:
        """カテゴリをIndicatorTypeにマッピング"""
        mapping = {
            "GDP": IndicatorType.GDP,
            "GDP Growth Rate": IndicatorType.GDP,
            "Inflation Rate": IndicatorType.INFLATION,
            "Unemployment Rate": IndicatorType.UNEMPLOYMENT,
            "Interest Rate": IndicatorType.INTEREST_RATE,
            "Trade Balance": IndicatorType.TRADE_BALANCE,
            "Consumer Confidence": IndicatorType.CONSUMER_CONFIDENCE,
            "Manufacturing PMI": IndicatorType.MANUFACTURING_PMI,
            "Services PMI": IndicatorType.SERVICES_PMI,
            "Retail Sales": IndicatorType.RETAIL_SALES,
            "Industrial Production": IndicatorType.INDUSTRIAL_PRODUCTION,
            "Housing Starts": IndicatorType.HOUSING_STARTS,
            "Currency Reserves": IndicatorType.CURRENCY_RESERVES
        }
        return mapping.get(category)
    
    def _map_frequency(self, frequency: str) -> Frequency:
        """頻度をFrequencyにマッピング"""
        mapping = {
            "Daily": Frequency.DAILY,
            "Weekly": Frequency.WEEKLY,
            "Monthly": Frequency.MONTHLY,
            "Quarterly": Frequency.QUARTERLY,
            "Annually": Frequency.ANNUALLY
        }
        return mapping.get(frequency, Frequency.MONTHLY)
    
    def _calculate_quality_score_from_raw_data(self, data: Dict[str, Any]) -> float:
        """生データから品質スコアを計算"""
        score = 1.0
        
        # 必須フィールドの存在チェック
        required_fields = ["Country", "Category", "DateTime", "Actual"]
        for field in required_fields:
            if not data.get(field):
                score -= 0.2
        
        # 値の妥当性チェック
        if data.get("Actual") is None:
            score -= 0.3
        
        return max(0.0, score)
    
    def set_rate_limiter(self, rate_limiter):
        """レート制限器を設定"""
        self._rate_limiter = rate_limiter
