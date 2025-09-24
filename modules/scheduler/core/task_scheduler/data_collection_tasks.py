"""
データ収集タスク

各種データ収集タスクの定義と実装を提供します。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .scheduled_task import TaskType, TaskPriority
from modules.data_collection.main import DataCollectionService
from modules.data_collection.config.settings import DataCollectionSettings, DataCollectionMode
from modules.economic_indicators.core.data_collector.economic_data_collector import EconomicDataCollector
from modules.economic_indicators.config.settings import EconomicIndicatorsSettings

logger = logging.getLogger(__name__)


@dataclass
class DataCollectionTaskConfig:
    """データ収集タスク設定"""
    symbols: List[str]
    timeframes: List[str]
    update_interval_minutes: int = 5
    priority: TaskPriority = TaskPriority.HIGH
    market_hours_only: bool = True


class DataCollectionTasks:
    """データ収集タスククラス"""
    
    def __init__(
        self,
        data_collection_service: DataCollectionService,
        economic_data_collector: EconomicDataCollector
    ):
        self.data_collection_service = data_collection_service
        self.economic_data_collector = economic_data_collector
    
    async def collect_price_data_task(
        self,
        symbols: List[str],
        timeframes: List[str],
        priority: TaskPriority = TaskPriority.HIGH
    ) -> Dict[str, Any]:
        """価格データ収集タスク"""
        logger.info(f"Starting price data collection for {symbols} {timeframes}")
        
        try:
            results = {}
            
            for symbol in symbols:
                for timeframe in timeframes:
                    logger.info(f"Collecting {symbol} {timeframe}")
                    
                    # 最新データを収集
                    price_data = await self.data_collection_service.collector.collect_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=datetime.now() - timedelta(minutes=10),
                        end_date=datetime.now(),
                        priority=priority.value
                    )
                    
                    if price_data:
                        # データベースに保存
                        save_result = await self.data_collection_service.database_saver.save_price_data(price_data)
                        
                        results[f"{symbol}_{timeframe}"] = {
                            "success": True,
                            "records_collected": len(price_data),
                            "records_saved": save_result.saved_count,
                            "quality_score": save_result.quality_metrics.get("avg_quality_score", 0) if save_result.quality_metrics else 0
                        }
                        
                        logger.info(f"Collected {len(price_data)} records for {symbol} {timeframe}")
                    else:
                        results[f"{symbol}_{timeframe}"] = {
                            "success": False,
                            "error": "No data collected"
                        }
                        
                        logger.warning(f"No data collected for {symbol} {timeframe}")
            
            return {
                "success": True,
                "results": results,
                "total_symbols": len(symbols),
                "total_timeframes": len(timeframes),
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Price data collection task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
    
    async def collect_economic_indicators_task(
        self,
        countries: List[str],
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Dict[str, Any]:
        """経済指標データ収集タスク"""
        logger.info(f"Starting economic indicators collection for {countries}")
        
        try:
            results = {}
            
            for country in countries:
                logger.info(f"Collecting economic indicators for {country}")
                
                # 経済指標データを収集
                indicators = await self.economic_data_collector.collect_economic_indicators(
                    country=country,
                    start_date=datetime.now() - timedelta(days=30),
                    end_date=datetime.now()
                )
                
                if indicators:
                    results[country] = {
                        "success": True,
                        "indicators_collected": len(indicators),
                        "latest_indicators": [
                            {
                                "name": ind.indicator_name,
                                "value": ind.value,
                                "release_date": ind.release_date.isoformat(),
                                "impact_level": ind.impact_level.value
                            }
                            for ind in indicators[:5]  # 最新5件
                        ]
                    }
                    
                    logger.info(f"Collected {len(indicators)} indicators for {country}")
                else:
                    results[country] = {
                        "success": False,
                        "error": "No indicators collected"
                    }
                    
                    logger.warning(f"No indicators collected for {country}")
            
            return {
                "success": True,
                "results": results,
                "total_countries": len(countries),
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Economic indicators collection task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
    
    async def collect_economic_calendar_task(
        self,
        lookahead_days: int = 7,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> Dict[str, Any]:
        """経済指標カレンダー収集タスク"""
        logger.info(f"Starting economic calendar collection for {lookahead_days} days")
        
        try:
            # 今後の経済指標カレンダーを収集
            calendar_events = await self.economic_data_collector.collect_upcoming_calendar()
            
            if calendar_events:
                # 高影響イベントをフィルタリング
                high_impact_events = [
                    event for event in calendar_events
                    if event.impact_level.value in ["high", "critical"]
                ]
                
                results = {
                    "success": True,
                    "total_events": len(calendar_events),
                    "high_impact_events": len(high_impact_events),
                    "upcoming_events": [
                        {
                            "country": event.country,
                            "indicator_name": event.indicator_name,
                            "scheduled_release": event.scheduled_release.isoformat(),
                            "impact_level": event.impact_level.value,
                            "currency_impact": event.currency_impact
                        }
                        for event in calendar_events[:10]  # 最新10件
                    ],
                    "high_impact_upcoming": [
                        {
                            "country": event.country,
                            "indicator_name": event.indicator_name,
                            "scheduled_release": event.scheduled_release.isoformat(),
                            "impact_level": event.impact_level.value,
                            "currency_impact": event.currency_impact
                        }
                        for event in high_impact_events[:5]  # 高影響5件
                    ]
                }
                
                logger.info(f"Collected {len(calendar_events)} calendar events, {len(high_impact_events)} high impact")
            else:
                results = {
                    "success": False,
                    "error": "No calendar events collected"
                }
                
                logger.warning("No calendar events collected")
            
            return {
                **results,
                "execution_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Economic calendar collection task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
    
    async def health_check_task(self) -> Dict[str, Any]:
        """ヘルスチェックタスク"""
        logger.info("Starting health check task")
        
        try:
            # データ収集サービスのヘルスチェック
            data_collection_health = await self.data_collection_service.collector.health_check()
            
            # 経済指標コレクターのヘルスチェック
            economic_health = await self.economic_data_collector.health_check()
            
            # 統計情報を取得
            data_collection_stats = self.data_collection_service.collector.get_stats()
            economic_stats = self.economic_data_collector.get_stats()
            
            results = {
                "success": True,
                "data_collection": {
                    "health": data_collection_health,
                    "stats": data_collection_stats
                },
                "economic_indicators": {
                    "health": economic_health,
                    "stats": economic_stats
                },
                "overall_health": "healthy" if all(
                    all(status for status in health.values()) 
                    for health in [data_collection_health, economic_health]
                ) else "unhealthy"
            }
            
            logger.info(f"Health check completed: {results['overall_health']}")
            return results
            
        except Exception as e:
            logger.error(f"Health check task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "overall_health": "unhealthy",
                "execution_time": datetime.now().isoformat()
            }
    
    async def cleanup_old_data_task(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """古いデータのクリーンアップタスク"""
        logger.info(f"Starting cleanup task for data older than {days_to_keep} days")
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 古い価格データを削除
            deleted_price_data = await self.data_collection_service.database_saver.delete_old_data(cutoff_date)
            
            results = {
                "success": True,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted_price_data_records": deleted_price_data,
                "execution_time": datetime.now().isoformat()
            }
            
            logger.info(f"Cleanup completed: {deleted_price_data} price data records deleted")
            return results
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": datetime.now().isoformat()
            }
