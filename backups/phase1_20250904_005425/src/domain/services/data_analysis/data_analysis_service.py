"""
データ分析サービス

経済データの分析、差分検出、サプライズ計算を統合する
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd

from src.domain.entities import EconomicEvent
from .forecast_change_detector import ForecastChangeDetector
from .surprise_calculator import SurpriseCalculator
from .event_filter import EventFilter


class DataAnalysisService:
    """
    データ分析サービス
    
    経済データの分析、差分検出、サプライズ計算を統合する
    """

    def __init__(
        self,
        change_detector: Optional[ForecastChangeDetector] = None,
        surprise_calculator: Optional[SurpriseCalculator] = None,
        event_filter: Optional[EventFilter] = None,
    ):
        """
        初期化
        
        Args:
            change_detector: 予測値変更検出器（オプション）
            surprise_calculator: サプライズ計算器（オプション）
            event_filter: イベントフィルター（オプション）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # コンポーネントの初期化
        self.change_detector = change_detector or ForecastChangeDetector()
        self.surprise_calculator = surprise_calculator or SurpriseCalculator()
        self.event_filter = event_filter or EventFilter()
        
        # 統計情報
        self._analysis_count = 0
        self._changes_detected = 0
        self._surprises_calculated = 0

    async def analyze_data_changes(
        self,
        old_events: List[EconomicEvent],
        new_events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """
        データ変更の分析
        
        Args:
            old_events: 変更前のイベントリスト
            new_events: 変更後のイベントリスト
            
        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            self.logger.info("データ変更分析を開始")
            self._analysis_count += 1
            
            # 予測値変更の検出
            forecast_changes = await self.change_detector.detect_changes(
                old_events, new_events
            )
            
            # 重要な変更のフィルタリング
            significant_changes = await self.event_filter.filter_significant_changes(
                forecast_changes
            )
            
            # 統計情報の更新
            self._changes_detected += len(forecast_changes)
            
            result = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "total_old_events": len(old_events),
                "total_new_events": len(new_events),
                "forecast_changes": forecast_changes,
                "significant_changes": significant_changes,
                "summary": {
                    "total_changes": len(forecast_changes),
                    "significant_changes": len(significant_changes),
                    "change_rate": len(forecast_changes) / max(1, len(old_events)),
                }
            }
            
            self.logger.info(
                f"データ変更分析完了: {len(forecast_changes)}件の変更を検出"
            )
            
            return result

        except Exception as e:
            self.logger.error(f"データ変更分析エラー: {e}")
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "forecast_changes": [],
                "significant_changes": [],
                "summary": {
                    "total_changes": 0,
                    "significant_changes": 0,
                    "change_rate": 0,
                }
            }

    async def calculate_event_surprises(
        self,
        events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """
        イベントサプライズの計算
        
        Args:
            events: 経済イベントリスト
            
        Returns:
            Dict[str, Any]: サプライズ計算結果
        """
        try:
            self.logger.info("サプライズ計算を開始")
            
            surprises = []
            significant_surprises = []
            
            for event in events:
                if event.has_actual_value and event.has_forecast_value:
                    surprise_data = await self.surprise_calculator.calculate_surprise(
                        event
                    )
                    
                    surprises.append({
                        "event_id": event.event_id,
                        "event_name": event.event_name,
                        "country": event.country,
                        "surprise_data": surprise_data
                    })
                    
                    # 有意なサプライズの判定
                    if self._is_significant_surprise(surprise_data):
                        significant_surprises.append(surprises[-1])
            
            # 統計情報の更新
            self._surprises_calculated += len(surprises)
            
            result = {
                "calculation_timestamp": datetime.utcnow().isoformat(),
                "total_events": len(events),
                "surprises": surprises,
                "significant_surprises": significant_surprises,
                "summary": {
                    "total_surprises": len(surprises),
                    "significant_surprises": len(significant_surprises),
                    "surprise_rate": len(surprises) / max(1, len(events)),
                }
            }
            
            self.logger.info(
                f"サプライズ計算完了: {len(surprises)}件のサプライズを計算"
            )
            
            return result

        except Exception as e:
            self.logger.error(f"サプライズ計算エラー: {e}")
            return {
                "calculation_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "surprises": [],
                "significant_surprises": [],
                "summary": {
                    "total_surprises": 0,
                    "significant_surprises": 0,
                    "surprise_rate": 0,
                }
            }

    async def analyze_market_impact(
        self,
        events: List[EconomicEvent],
        timeframe_hours: int = 24
    ) -> Dict[str, Any]:
        """
        市場影響分析
        
        Args:
            events: 経済イベントリスト
            timeframe_hours: 分析時間枠（時間）
            
        Returns:
            Dict[str, Any]: 市場影響分析結果
        """
        try:
            self.logger.info("市場影響分析を開始")
            
            # 高重要度イベントのフィルタリング
            high_impact_events = await self.event_filter.filter_high_impact_events(
                events
            )
            
            # 国別の影響分析
            country_impact = await self._analyze_country_impact(high_impact_events)
            
            # カテゴリ別の影響分析
            category_impact = await self._analyze_category_impact(high_impact_events)
            
            # タイミング分析
            timing_analysis = await self._analyze_timing_impact(
                high_impact_events, timeframe_hours
            )
            
            result = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "timeframe_hours": timeframe_hours,
                "total_events": len(events),
                "high_impact_events": len(high_impact_events),
                "country_impact": country_impact,
                "category_impact": category_impact,
                "timing_analysis": timing_analysis,
                "recommendations": await self._generate_recommendations(
                    high_impact_events, country_impact, category_impact
                )
            }
            
            self.logger.info("市場影響分析完了")
            
            return result

        except Exception as e:
            self.logger.error(f"市場影響分析エラー: {e}")
            return {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "high_impact_events": 0,
                "country_impact": {},
                "category_impact": {},
                "timing_analysis": {},
                "recommendations": []
            }

    async def compare_forecasts(
        self,
        events1: List[EconomicEvent],
        events2: List[EconomicEvent],
        comparison_name: str = "Forecast Comparison"
    ) -> Dict[str, Any]:
        """
        予測値の比較分析
        
        Args:
            events1: 比較対象1のイベントリスト
            events2: 比較対象2のイベントリスト
            comparison_name: 比較名
            
        Returns:
            Dict[str, Any]: 比較分析結果
        """
        try:
            self.logger.info(f"予測値比較分析を開始: {comparison_name}")
            
            # イベントIDでマッチング
            matched_pairs = await self._match_events_by_id(events1, events2)
            
            comparisons = []
            accuracy_stats = {"better": 0, "worse": 0, "same": 0}
            
            for event1, event2 in matched_pairs:
                comparison = await self._compare_event_forecasts(event1, event2)
                comparisons.append(comparison)
                
                # 精度統計の更新
                if comparison["accuracy_change"] > 0:
                    accuracy_stats["better"] += 1
                elif comparison["accuracy_change"] < 0:
                    accuracy_stats["worse"] += 1
                else:
                    accuracy_stats["same"] += 1
            
            result = {
                "comparison_timestamp": datetime.utcnow().isoformat(),
                "comparison_name": comparison_name,
                "total_matched_events": len(matched_pairs),
                "comparisons": comparisons,
                "accuracy_stats": accuracy_stats,
                "summary": {
                    "improvement_rate": accuracy_stats["better"] / max(1, len(matched_pairs)),
                    "degradation_rate": accuracy_stats["worse"] / max(1, len(matched_pairs)),
                    "stability_rate": accuracy_stats["same"] / max(1, len(matched_pairs)),
                }
            }
            
            self.logger.info(f"予測値比較分析完了: {len(matched_pairs)}件の比較")
            
            return result

        except Exception as e:
            self.logger.error(f"予測値比較分析エラー: {e}")
            return {
                "comparison_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "comparisons": [],
                "accuracy_stats": {"better": 0, "worse": 0, "same": 0},
                "summary": {
                    "improvement_rate": 0,
                    "degradation_rate": 0,
                    "stability_rate": 0,
                }
            }

    def _is_significant_surprise(self, surprise_data: Dict[str, Any]) -> bool:
        """有意なサプライズかどうかを判定"""
        if not surprise_data.get("surprise_percentage"):
            return False
        
        abs_surprise = abs(surprise_data["surprise_percentage"])
        return abs_surprise >= 0.2  # 20%以上のサプライズ

    async def _analyze_country_impact(
        self, events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """国別影響分析"""
        country_stats = {}
        
        for event in events:
            country = event.country
            if country not in country_stats:
                country_stats[country] = {
                    "event_count": 0,
                    "high_importance_count": 0,
                    "avg_impact_score": 0,
                }
            
            country_stats[country]["event_count"] += 1
            if event.is_high_importance:
                country_stats[country]["high_importance_count"] += 1
        
        # 影響スコアの計算
        for country, stats in country_stats.items():
            stats["avg_impact_score"] = (
                stats["high_importance_count"] / max(1, stats["event_count"])
            )
        
        return country_stats

    async def _analyze_category_impact(
        self, events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """カテゴリ別影響分析"""
        category_stats = {}
        
        for event in events:
            category = event.category or "Unknown"
            if category not in category_stats:
                category_stats[category] = {
                    "event_count": 0,
                    "avg_surprise": 0,
                    "high_impact_count": 0,
                }
            
            category_stats[category]["event_count"] += 1
            if event.is_high_importance:
                category_stats[category]["high_impact_count"] += 1
        
        return category_stats

    async def _analyze_timing_impact(
        self, events: List[EconomicEvent], timeframe_hours: int
    ) -> Dict[str, Any]:
        """タイミング影響分析"""
        current_time = datetime.utcnow()
        time_buckets = {"past": 0, "upcoming_24h": 0, "future": 0}
        
        for event in events:
            time_diff = (event.date_utc - current_time).total_seconds() / 3600
            
            if time_diff < 0:
                time_buckets["past"] += 1
            elif time_diff <= timeframe_hours:
                time_buckets["upcoming_24h"] += 1
            else:
                time_buckets["future"] += 1
        
        return time_buckets

    async def _generate_recommendations(
        self,
        events: List[EconomicEvent],
        country_impact: Dict[str, Any],
        category_impact: Dict[str, Any]
    ) -> List[str]:
        """推奨事項の生成"""
        recommendations = []
        
        # 高影響国の特定
        high_impact_countries = [
            country for country, stats in country_impact.items()
            if stats["avg_impact_score"] > 0.5
        ]
        
        if high_impact_countries:
            recommendations.append(
                f"注意すべき国: {', '.join(high_impact_countries)}"
            )
        
        # 高頻度カテゴリの特定
        high_freq_categories = [
            category for category, stats in category_impact.items()
            if stats["event_count"] > 5
        ]
        
        if high_freq_categories:
            recommendations.append(
                f"注目すべきカテゴリ: {', '.join(high_freq_categories)}"
            )
        
        return recommendations

    async def _match_events_by_id(
        self, events1: List[EconomicEvent], events2: List[EconomicEvent]
    ) -> List[Tuple[EconomicEvent, EconomicEvent]]:
        """イベントIDによるマッチング"""
        events2_dict = {event.event_id: event for event in events2}
        matched_pairs = []
        
        for event1 in events1:
            if event1.event_id in events2_dict:
                matched_pairs.append((event1, events2_dict[event1.event_id]))
        
        return matched_pairs

    async def _compare_event_forecasts(
        self, event1: EconomicEvent, event2: EconomicEvent
    ) -> Dict[str, Any]:
        """個別イベントの予測値比較"""
        comparison = {
            "event_id": event1.event_id,
            "event_name": event1.event_name,
            "forecast1": float(event1.forecast_value) if event1.forecast_value else None,
            "forecast2": float(event2.forecast_value) if event2.forecast_value else None,
            "forecast_change": None,
            "accuracy_change": 0,
        }
        
        if event1.forecast_value and event2.forecast_value:
            comparison["forecast_change"] = float(event2.forecast_value - event1.forecast_value)
            
            # 精度変化の計算（実際値がある場合）
            if event1.actual_value:
                actual = float(event1.actual_value)
                error1 = abs(float(event1.forecast_value) - actual)
                error2 = abs(float(event2.forecast_value) - actual)
                comparison["accuracy_change"] = error1 - error2  # 正の値は改善
        
        return comparison

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "service": "DataAnalysisService",
            "analysis_count": self._analysis_count,
            "changes_detected": self._changes_detected,
            "surprises_calculated": self._surprises_calculated,
            "components": {
                "change_detector": self.change_detector.get_stats(),
                "surprise_calculator": self.surprise_calculator.get_stats(),
                "event_filter": self.event_filter.get_stats(),
            }
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 各コンポーネントの確認
            change_detector_health = self.change_detector.health_check()
            surprise_calculator_health = self.surprise_calculator.health_check()
            event_filter_health = self.event_filter.health_check()
            
            return all([
                change_detector_health,
                surprise_calculator_health,
                event_filter_health,
            ])
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
