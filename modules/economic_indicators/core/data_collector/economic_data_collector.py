"""
経済指標データコレクター

経済指標データの収集と管理を統合的に行います。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from ...providers.base_economic_provider import BaseEconomicProvider, EconomicDataResult
from ...providers.trading_economics import TradingEconomicsProvider
from modules.data_persistence.models.economic_indicators import (
    EconomicIndicatorModel, IndicatorType, ImpactLevel
)
from modules.data_persistence.models.economic_calendar import (
    EconomicCalendarModel, CalendarStatus
)

logger = logging.getLogger(__name__)


@dataclass
class CollectionConfig:
    """収集設定"""
    countries: List[str]
    indicator_types: List[IndicatorType]
    update_interval_hours: int = 6
    calendar_lookahead_days: int = 30
    historical_days: int = 365


class EconomicDataCollector:
    """経済指標データコレクター"""
    
    def __init__(self, config: CollectionConfig):
        self.config = config
        self.providers: Dict[str, BaseEconomicProvider] = {}
        self.fallback_providers: List[BaseEconomicProvider] = []
        
        # 統計情報
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'indicators_collected': 0,
            'calendar_events_collected': 0
        }
    
    def add_provider(self, name: str, provider: BaseEconomicProvider) -> None:
        """プロバイダーを追加"""
        self.providers[name] = provider
    
    def add_fallback_provider(self, provider: BaseEconomicProvider) -> None:
        """フォールバックプロバイダーを追加"""
        self.fallback_providers.append(provider)
    
    async def collect_economic_indicators(
        self,
        country: str,
        indicator_type: Optional[IndicatorType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[EconomicIndicatorModel]:
        """経済指標データを収集"""
        self.stats['total_requests'] += 1
        
        try:
            # メインプロバイダーで試行
            for provider_name, provider in self.providers.items():
                if not provider.is_available():
                    continue
                
                try:
                    result = await provider.get_economic_indicators(
                        country, indicator_type, start_date, end_date
                    )
                    
                    if result.success:
                        self.stats['successful_requests'] += 1
                        self.stats['indicators_collected'] += len(result.data)
                        return result.data
                    else:
                        logger.warning(f"Provider {provider_name} failed: {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"Provider {provider_name} error: {e}")
                    continue
            
            # フォールバックプロバイダーで試行
            for provider in self.fallback_providers:
                if not provider.is_available():
                    continue
                
                try:
                    result = await provider.get_economic_indicators(
                        country, indicator_type, start_date, end_date
                    )
                    
                    if result.success:
                        self.stats['successful_requests'] += 1
                        self.stats['indicators_collected'] += len(result.data)
                        return result.data
                        
                except Exception as e:
                    logger.error(f"Fallback provider error: {e}")
                    continue
            
            # すべてのプロバイダーが失敗
            self.stats['failed_requests'] += 1
            return []
            
        except Exception as e:
            logger.error(f"Economic indicators collection error: {e}")
            self.stats['failed_requests'] += 1
            return []
    
    async def collect_economic_calendar(
        self,
        country: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[EconomicCalendarModel]:
        """経済指標カレンダーを収集"""
        self.stats['total_requests'] += 1
        
        try:
            # メインプロバイダーで試行
            for provider_name, provider in self.providers.items():
                if not provider.is_available():
                    continue
                
                try:
                    result = await provider.get_economic_calendar(
                        country, start_date, end_date
                    )
                    
                    if result.success:
                        self.stats['successful_requests'] += 1
                        self.stats['calendar_events_collected'] += len(result.calendar_data)
                        return result.calendar_data
                    else:
                        logger.warning(f"Provider {provider_name} failed: {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"Provider {provider_name} error: {e}")
                    continue
            
            # フォールバックプロバイダーで試行
            for provider in self.fallback_providers:
                if not provider.is_available():
                    continue
                
                try:
                    result = await provider.get_economic_calendar(
                        country, start_date, end_date
                    )
                    
                    if result.success:
                        self.stats['successful_requests'] += 1
                        self.stats['calendar_events_collected'] += len(result.calendar_data)
                        return result.calendar_data
                        
                except Exception as e:
                    logger.error(f"Fallback provider error: {e}")
                    continue
            
            # すべてのプロバイダーが失敗
            self.stats['failed_requests'] += 1
            return []
            
        except Exception as e:
            logger.error(f"Economic calendar collection error: {e}")
            self.stats['failed_requests'] += 1
            return []
    
    async def collect_all_indicators(self) -> Dict[str, List[EconomicIndicatorModel]]:
        """すべての設定された国と指標を収集"""
        results = {}
        
        for country in self.config.countries:
            for indicator_type in self.config.indicator_types:
                logger.info(f"Collecting {indicator_type.value} for {country}")
                
                # 過去1年分のデータを収集
                end_date = datetime.now()
                start_date = end_date - timedelta(days=self.config.historical_days)
                
                indicators = await self.collect_economic_indicators(
                    country, indicator_type, start_date, end_date
                )
                
                key = f"{country}_{indicator_type.value}"
                results[key] = indicators
                
                # プロバイダー間の待機時間
                await asyncio.sleep(1)
        
        return results
    
    async def collect_upcoming_calendar(self) -> List[EconomicCalendarModel]:
        """今後の経済指標カレンダーを収集"""
        end_date = datetime.now() + timedelta(days=self.config.calendar_lookahead_days)
        
        calendar_events = await self.collect_economic_calendar(
            start_date=datetime.now(),
            end_date=end_date
        )
        
        return calendar_events
    
    async def collect_high_impact_events(self) -> List[EconomicCalendarModel]:
        """高影響の経済指標イベントを収集"""
        all_events = await self.collect_upcoming_calendar()
        
        # 高影響イベントのみをフィルタリング
        high_impact_events = [
            event for event in all_events
            if event.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]
        ]
        
        return high_impact_events
    
    async def collect_today_events(self) -> List[EconomicCalendarModel]:
        """今日の経済指標イベントを収集"""
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        today_events = await self.collect_economic_calendar(
            start_date=datetime.combine(today, datetime.min.time()),
            end_date=datetime.combine(tomorrow, datetime.min.time())
        )
        
        return today_events
    
    async def health_check(self) -> Dict[str, bool]:
        """ヘルスチェック"""
        health_status = {}
        
        # プロバイダーのヘルスチェック
        for name, provider in self.providers.items():
            try:
                health_status[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = False
        
        # フォールバックプロバイダーのヘルスチェック
        for i, provider in enumerate(self.fallback_providers):
            try:
                health_status[f"fallback_{i}"] = await provider.health_check()
            except Exception as e:
                logger.error(f"Fallback health check failed: {e}")
                health_status[f"fallback_{i}"] = False
        
        return health_status
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_requests'] / max(1, self.stats['total_requests'])
            ) * 100,
            'config': {
                'countries': self.config.countries,
                'indicator_types': [t.value for t in self.config.indicator_types],
                'update_interval_hours': self.config.update_interval_hours,
                'calendar_lookahead_days': self.config.calendar_lookahead_days,
                'historical_days': self.config.historical_days
            }
        }
