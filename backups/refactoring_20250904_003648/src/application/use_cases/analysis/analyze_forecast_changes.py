"""
予測値変更分析ユースケース
経済イベントの予測値変更を分析するユースケース
"""

import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.repositories.economic_calendar_repository import (
    EconomicCalendarRepository,
)
from src.domain.services.data_analysis import DataAnalysisService


class AnalyzeForecastChangesUseCase:
    """予測値変更分析ユースケース"""

    def __init__(
        self,
        data_analysis_service: DataAnalysisService,
        repository: EconomicCalendarRepository,
    ):
        self.data_analysis_service = data_analysis_service
        self.repository = repository
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(
        self,
        start_date: date,
        end_date: date,
        countries: Optional[List[str]] = None,
        importances: Optional[List[Importance]] = None,
    ) -> Dict[str, Any]:
        """
        予測値変更分析を実行

        Args:
            start_date: 開始日
            end_date: 終了日
            countries: 国名リスト（フィルタ）
            importances: 重要度リスト（フィルタ）

        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            self.logger.info(
                f"Starting forecast change analysis: {start_date} to {end_date}"
            )

            # イベントを取得
            events = await self.repository.find_by_date_range(
                start_date=start_date,
                end_date=end_date,
                countries=countries,
                importances=importances,
            )

            # 予測値変更を検出
            forecast_changes = await self._detect_forecast_changes(events)

            # 統計情報を計算
            statistics = await self._calculate_forecast_change_statistics(
                forecast_changes
            )

            # 重要度別の分析
            importance_analysis = await self._analyze_by_importance(forecast_changes)

            # 国別の分析
            country_analysis = await self._analyze_by_country(forecast_changes)

            result = {
                "success": True,
                "forecast_changes": forecast_changes,
                "statistics": statistics,
                "importance_analysis": importance_analysis,
                "country_analysis": country_analysis,
                "analysis_date": datetime.utcnow().isoformat(),
            }

            self.logger.info(
                f"Forecast change analysis completed: {len(forecast_changes)} changes found"
            )
            return result

        except Exception as e:
            self.logger.error(f"Error in forecast change analysis: {e}")
            return {
                "success": False,
                "error": str(e),
                "analysis_date": datetime.utcnow().isoformat(),
            }

    async def _detect_forecast_changes(
        self, events: List[EconomicEvent]
    ) -> List[Dict[str, Any]]:
        """予測値変更を検出"""
        changes = []

        for event in events:
            if event.has_forecast_value and event.has_previous_value:
                # 予測値変更の検出
                change_result = await self.data_analysis_service.detect_forecast_change(
                    event
                )

                if change_result["has_change"]:
                    changes.append(
                        {
                            "event_id": event.event_id,
                            "event_name": event.event_name,
                            "country": event.country,
                            "importance": event.importance.value,
                            "old_forecast": float(event.previous_value),
                            "new_forecast": float(event.forecast_value),
                            "change_percentage": change_result["change_percentage"],
                            "change_direction": change_result["change_direction"],
                            "date": event.date_utc.isoformat(),
                        }
                    )

        return changes

    async def _calculate_forecast_change_statistics(
        self, forecast_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """予測値変更の統計情報を計算"""
        if not forecast_changes:
            return {
                "total_changes": 0,
                "average_change_percentage": 0.0,
                "max_change_percentage": 0.0,
                "min_change_percentage": 0.0,
                "improvements": 0,
                "deteriorations": 0,
            }

        change_percentages = [
            change["change_percentage"] for change in forecast_changes
        ]
        improvements = len(
            [c for c in forecast_changes if c["change_direction"] == "improvement"]
        )
        deteriorations = len(
            [c for c in forecast_changes if c["change_direction"] == "deterioration"]
        )

        return {
            "total_changes": len(forecast_changes),
            "average_change_percentage": sum(change_percentages)
            / len(change_percentages),
            "max_change_percentage": max(change_percentages),
            "min_change_percentage": min(change_percentages),
            "improvements": improvements,
            "deteriorations": deteriorations,
        }

    async def _analyze_by_importance(
        self, forecast_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """重要度別の分析"""
        importance_stats = {}

        for change in forecast_changes:
            importance = change["importance"]
            if importance not in importance_stats:
                importance_stats[importance] = {
                    "count": 0,
                    "total_change_percentage": 0.0,
                    "improvements": 0,
                    "deteriorations": 0,
                }

            importance_stats[importance]["count"] += 1
            importance_stats[importance]["total_change_percentage"] += change[
                "change_percentage"
            ]

            if change["change_direction"] == "improvement":
                importance_stats[importance]["improvements"] += 1
            else:
                importance_stats[importance]["deteriorations"] += 1

        # 平均値を計算
        for importance in importance_stats:
            count = importance_stats[importance]["count"]
            if count > 0:
                importance_stats[importance]["average_change_percentage"] = (
                    importance_stats[importance]["total_change_percentage"] / count
                )

        return importance_stats

    async def _analyze_by_country(
        self, forecast_changes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """国別の分析"""
        country_stats = {}

        for change in forecast_changes:
            country = change["country"]
            if country not in country_stats:
                country_stats[country] = {
                    "count": 0,
                    "total_change_percentage": 0.0,
                    "improvements": 0,
                    "deteriorations": 0,
                }

            country_stats[country]["count"] += 1
            country_stats[country]["total_change_percentage"] += change[
                "change_percentage"
            ]

            if change["change_direction"] == "improvement":
                country_stats[country]["improvements"] += 1
            else:
                country_stats[country]["deteriorations"] += 1

        # 平均値を計算
        for country in country_stats:
            count = country_stats[country]["count"]
            if count > 0:
                country_stats[country]["average_change_percentage"] = (
                    country_stats[country]["total_change_percentage"] / count
                )

        return country_stats

    async def get_forecast_change_statistics(
        self, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """予測値変更統計情報を取得"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=7)
            if not end_date:
                end_date = date.today()

            # 最近の予測値変更を取得
            events = await self.repository.find_by_date_range(
                start_date=start_date, end_date=end_date
            )

            forecast_changes = await self._detect_forecast_changes(events)
            statistics = await self._calculate_forecast_change_statistics(
                forecast_changes
            )

            return {
                "success": True,
                "statistics": statistics,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
            }

        except Exception as e:
            self.logger.error(f"Error getting forecast change statistics: {e}")
            return {"success": False, "error": str(e)}

    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本的な接続テスト
            test_events = await self.repository.find_by_date_range(
                start_date=date.today(), end_date=date.today(), limit=1
            )
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
