"""
経済指標プロバイダーの基底クラス

すべての経済指標プロバイダーが実装すべきインターフェースを定義します。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from ...data_persistence.models.economic_indicators import (
    EconomicIndicatorModel, IndicatorType, ImpactLevel, Frequency
)
from ...data_persistence.models.economic_calendar import (
    EconomicCalendarModel, CalendarStatus
)


@dataclass
class EconomicDataResult:
    """経済指標データ取得結果"""
    success: bool
    data: List[EconomicIndicatorModel]
    calendar_data: List[EconomicCalendarModel]
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


class BaseEconomicProvider(ABC):
    """経済指標プロバイダーの基底クラス"""
    
    def __init__(self, name: str):
        self.name = name
        self._is_available = True
    
    @abstractmethod
    async def get_economic_indicators(
        self,
        country: str,
        indicator_type: Optional[IndicatorType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EconomicDataResult:
        """経済指標データを取得"""
        pass
    
    @abstractmethod
    async def get_economic_calendar(
        self,
        country: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> EconomicDataResult:
        """経済指標カレンダーを取得"""
        pass
    
    @abstractmethod
    async def get_available_countries(self) -> List[str]:
        """利用可能な国一覧を取得"""
        pass
    
    @abstractmethod
    async def get_available_indicators(self, country: str) -> List[str]:
        """利用可能な経済指標一覧を取得"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """プロバイダーが利用可能かチェック"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        pass
    
    def _validate_economic_data(self, data: List[EconomicIndicatorModel]) -> List[EconomicIndicatorModel]:
        """経済指標データの妥当性をチェック"""
        validated_data = []
        
        for item in data:
            # 基本的な妥当性チェック
            if (item.value is not None and 
                item.release_date is not None and
                item.period_start <= item.period_end):
                validated_data.append(item)
        
        return validated_data
    
    def _calculate_impact_level(self, indicator_type: IndicatorType, country: str) -> ImpactLevel:
        """経済指標の影響レベルを計算"""
        # 高影響指標
        high_impact_indicators = {
            IndicatorType.GDP,
            IndicatorType.INTEREST_RATE,
            IndicatorType.INFLATION,
            IndicatorType.UNEMPLOYMENT
        }
        
        # 重要指標（主要国の場合）
        critical_countries = {"US", "JP", "EU", "GB", "CH"}
        critical_indicators = {
            IndicatorType.INTEREST_RATE,
            IndicatorType.GDP
        }
        
        if indicator_type in critical_indicators and country in critical_countries:
            return ImpactLevel.CRITICAL
        elif indicator_type in high_impact_indicators:
            return ImpactLevel.HIGH
        else:
            return ImpactLevel.MEDIUM
    
    def _determine_currency_impact(self, country: str, indicator_type: IndicatorType) -> Optional[str]:
        """通貨への影響を判定"""
        currency_mapping = {
            "US": "USD",
            "JP": "JPY", 
            "EU": "EUR",
            "GB": "GBP",
            "CH": "CHF",
            "AU": "AUD",
            "CA": "CAD",
            "NZ": "NZD"
        }
        
        # 金利とGDPは特に通貨に影響
        currency_sensitive_indicators = {
            IndicatorType.INTEREST_RATE,
            IndicatorType.GDP,
            IndicatorType.INFLATION
        }
        
        if indicator_type in currency_sensitive_indicators:
            return currency_mapping.get(country)
        
        return None
    
    def _calculate_quality_score(self, data: EconomicIndicatorModel) -> float:
        """データ品質スコアを計算"""
        score = 1.0
        
        # 値の妥当性チェック
        if data.value is None:
            score -= 0.5
        
        # 予想値と前回値の妥当性チェック
        if data.forecast_value is not None and data.previous_value is not None:
            if abs(data.value - data.forecast_value) / abs(data.forecast_value) > 0.5:
                score -= 0.1
        
        # 発表情報の妥当性チェック
        if data.release_date > datetime.now() + timedelta(days=1):
            score -= 0.2
        
        # 期間の妥当性チェック
        if data.period_start > data.period_end:
            score -= 0.3
        
        return max(0.0, score)
