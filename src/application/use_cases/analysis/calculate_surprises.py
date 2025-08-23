"""
サプライズ計算ユースケース
経済イベントのサプライズ（予測値と実際値の差）を計算するユースケース
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from src.domain.services.data_analysis import DataAnalysisService
from src.domain.repositories.economic_calendar_repository import EconomicCalendarRepository
from src.domain.entities.economic_event import EconomicEvent, Importance


class CalculateSurprisesUseCase:
    """サプライズ計算ユースケース"""
    
    def __init__(
        self,
        data_analysis_service: DataAnalysisService,
        repository: EconomicCalendarRepository
    ):
        self.data_analysis_service = data_analysis_service
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def execute(
        self,
        start_date: date,
        end_date: date,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None
    ) -> Dict[str, Any]:
        """
        サプライズ計算を実行
        
        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）
            
        Returns:
            Dict[str, Any]: 計算結果
        """
        try:
            self.logger.info(f"Starting surprise calculation: {start_date} to {end_date}")
            
            # イベントを取得
            events = await self.repository.find_by_date_range(
                start_date=start_date,
                end_date=end_date,
                countries=countries,
                importances=importances
            )
            
            # サプライズを計算
            surprises = await self._calculate_surprises(events)
            
            # 統計情報を計算
            statistics = await self._calculate_surprise_statistics(surprises)
            
            # 重要度別の分析
            importance_analysis = await self._analyze_by_importance(surprises)
            
            # 国別の分析
            country_analysis = await self._analyze_by_country(surprises)
            
            result = {
                "success": True,
                "surprises": surprises,
                "statistics": statistics,
                "importance_analysis": importance_analysis,
                "country_analysis": country_analysis,
                "analysis_date": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Surprise calculation completed: {len(surprises)} surprises found")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in surprise calculation: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_date": datetime.utcnow().isoformat()
            }
    
    async def _calculate_surprises(self, events: List[EconomicEvent]) -> List[Dict[str, Any]]:
        """サプライズを計算"""
        surprises = []
        
        for event in events:
            if event.has_actual_value and event.has_forecast_value:
                # サプライズ計算
                surprise_result = await self.data_analysis_service.calculate_surprise(event)
                
                if surprise_result["has_surprise"]:
                    surprises.append({
                        "event_id": event.event_id,
                        "event_name": event.event_name,
                        "country": event.country,
                        "importance": event.importance.value,
                        "forecast_value": float(event.forecast_value),
                        "actual_value": float(event.actual_value),
                        "surprise_percentage": surprise_result["surprise_percentage"],
                        "surprise_direction": surprise_result["surprise_direction"],
                        "surprise_magnitude": surprise_result["surprise_magnitude"],
                        "date": event.date_utc.isoformat()
                    })
        
        return surprises
    
    async def _calculate_surprise_statistics(
        self, 
        surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """サプライズの統計情報を計算"""
        if not surprises:
            return {
                "total_surprises": 0,
                "average_surprise_percentage": 0.0,
                "max_surprise_percentage": 0.0,
                "min_surprise_percentage": 0.0,
                "positive_surprises": 0,
                "negative_surprises": 0,
                "high_magnitude_surprises": 0
            }
        
        surprise_percentages = [surprise["surprise_percentage"] for surprise in surprises]
        positive_surprises = len([s for s in surprises if s["surprise_direction"] == "positive"])
        negative_surprises = len([s for s in surprises if s["surprise_direction"] == "negative"])
        high_magnitude = len([s for s in surprises if s["surprise_magnitude"] == "high"])
        
        return {
            "total_surprises": len(surprises),
            "average_surprise_percentage": sum(surprise_percentages) / len(surprise_percentages),
            "max_surprise_percentage": max(surprise_percentages),
            "min_surprise_percentage": min(surprise_percentages),
            "positive_surprises": positive_surprises,
            "negative_surprises": negative_surprises,
            "high_magnitude_surprises": high_magnitude
        }
    
    async def _analyze_by_importance(
        self, 
        surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """重要度別の分析"""
        importance_stats = {}
        
        for surprise in surprises:
            importance = surprise["importance"]
            if importance not in importance_stats:
                importance_stats[importance] = {
                    "count": 0,
                    "total_surprise_percentage": 0.0,
                    "positive_surprises": 0,
                    "negative_surprises": 0,
                    "high_magnitude": 0
                }
            
            importance_stats[importance]["count"] += 1
            importance_stats[importance]["total_surprise_percentage"] += surprise["surprise_percentage"]
            
            if surprise["surprise_direction"] == "positive":
                importance_stats[importance]["positive_surprises"] += 1
            else:
                importance_stats[importance]["negative_surprises"] += 1
            
            if surprise["surprise_magnitude"] == "high":
                importance_stats[importance]["high_magnitude"] += 1
        
        # 平均値を計算
        for importance in importance_stats:
            count = importance_stats[importance]["count"]
            if count > 0:
                importance_stats[importance]["average_surprise_percentage"] = (
                    importance_stats[importance]["total_surprise_percentage"] / count
                )
        
        return importance_stats
    
    async def _analyze_by_country(
        self, 
        surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """国別の分析"""
        country_stats = {}
        
        for surprise in surprises:
            country = surprise["country"]
            if country not in country_stats:
                country_stats[country] = {
                    "count": 0,
                    "total_surprise_percentage": 0.0,
                    "positive_surprises": 0,
                    "negative_surprises": 0,
                    "high_magnitude": 0
                }
            
            country_stats[country]["count"] += 1
            country_stats[country]["total_surprise_percentage"] += surprise["surprise_percentage"]
            
            if surprise["surprise_direction"] == "positive":
                country_stats[country]["positive_surprises"] += 1
            else:
                country_stats[country]["negative_surprises"] += 1
            
            if surprise["surprise_magnitude"] == "high":
                country_stats[country]["high_magnitude"] += 1
        
        # 平均値を計算
        for country in country_stats:
            count = country_stats[country]["count"]
            if count > 0:
                country_stats[country]["average_surprise_percentage"] = (
                    country_stats[country]["total_surprise_percentage"] / count
                )
        
        return country_stats
    
    async def get_surprise_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """サプライズ統計情報を取得"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=7)
            if not end_date:
                end_date = date.today()
            
            # 最近のサプライズを取得
            events = await self.repository.find_by_date_range(
                start_date=start_date,
                end_date=end_date
            )
            
            surprises = await self._calculate_surprises(events)
            statistics = await self._calculate_surprise_statistics(surprises)
            
            return {
                "success": True,
                "statistics": statistics,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting surprise statistics: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な接続テスト
            test_events = await self.repository.find_by_date_range(
                start_date=date.today(),
                end_date=date.today(),
                limit=1
            )
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
