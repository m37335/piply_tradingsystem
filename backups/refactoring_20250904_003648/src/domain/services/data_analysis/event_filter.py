"""
イベントフィルター

経済イベントのフィルタリングと分類を行う
"""

import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from src.domain.entities import EconomicEvent


class EventFilter:
    """
    イベントフィルター
    
    経済イベントの重要度、国、カテゴリ等による
    フィルタリングと分類を行う
    """

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # デフォルトフィルター設定
        self.default_filters = {
            "importance_levels": ["high", "medium"],
            "target_countries": [
                "japan", "united states", "euro zone", 
                "united kingdom", "australia", "canada"
            ],
            "high_impact_categories": [
                "inflation", "employment", "interest_rate", 
                "gdp", "trade", "monetary_policy"
            ],
            "change_threshold": 0.1,  # 10%
            "surprise_threshold": 0.2  # 20%
        }
        
        # 統計情報
        self._filter_count = 0
        self._filtered_events = 0

    async def filter_high_impact_events(
        self, events: List[EconomicEvent]
    ) -> List[EconomicEvent]:
        """
        高影響度イベントのフィルタリング
        
        Args:
            events: 経済イベントリスト
            
        Returns:
            List[EconomicEvent]: 高影響度イベントのリスト
        """
        try:
            self.logger.debug("高影響度イベントフィルタリング開始")
            self._filter_count += 1
            
            high_impact_events = []
            
            for event in events:
                if await self._is_high_impact_event(event):
                    high_impact_events.append(event)
                    self._filtered_events += 1
            
            self.logger.debug(
                f"高影響度イベントフィルタリング完了: "
                f"{len(high_impact_events)}/{len(events)}件"
            )
            
            return high_impact_events

        except Exception as e:
            self.logger.error(f"高影響度イベントフィルタリングエラー: {e}")
            return []

    async def filter_by_importance(
        self, 
        events: List[EconomicEvent], 
        importance_levels: Optional[List[str]] = None
    ) -> List[EconomicEvent]:
        """
        重要度によるフィルタリング
        
        Args:
            events: 経済イベントリスト
            importance_levels: 対象重要度レベル
            
        Returns:
            List[EconomicEvent]: フィルタリング後のイベントリスト
        """
        if importance_levels is None:
            importance_levels = self.default_filters["importance_levels"]
        
        return [
            event for event in events
            if event.importance.value in importance_levels
        ]

    async def filter_by_countries(
        self, 
        events: List[EconomicEvent], 
        countries: Optional[List[str]] = None
    ) -> List[EconomicEvent]:
        """
        国によるフィルタリング
        
        Args:
            events: 経済イベントリスト
            countries: 対象国リスト
            
        Returns:
            List[EconomicEvent]: フィルタリング後のイベントリスト
        """
        if countries is None:
            countries = self.default_filters["target_countries"]
        
        countries_lower = [country.lower() for country in countries]
        
        return [
            event for event in events
            if event.country.lower() in countries_lower
        ]

    async def filter_by_time_range(
        self,
        events: List[EconomicEvent],
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        hours_ahead: Optional[int] = None
    ) -> List[EconomicEvent]:
        """
        時間範囲によるフィルタリング
        
        Args:
            events: 経済イベントリスト
            start_time: 開始時刻
            end_time: 終了時刻
            hours_ahead: 現在から何時間先まで（hours_aheadが指定された場合、start_time/end_timeは無視）
            
        Returns:
            List[EconomicEvent]: フィルタリング後のイベントリスト
        """
        try:
            current_time = datetime.utcnow()
            
            if hours_ahead is not None:
                start_time = current_time
                end_time = current_time + timedelta(hours=hours_ahead)
            
            if start_time is None:
                start_time = current_time
            if end_time is None:
                end_time = current_time + timedelta(days=7)  # デフォルト1週間
            
            filtered_events = [
                event for event in events
                if start_time <= event.date_utc <= end_time
            ]
            
            self.logger.debug(
                f"時間範囲フィルタリング: {len(filtered_events)}/{len(events)}件 "
                f"({start_time.isoformat()} - {end_time.isoformat()})"
            )
            
            return filtered_events

        except Exception as e:
            self.logger.error(f"時間範囲フィルタリングエラー: {e}")
            return events

    async def filter_significant_changes(
        self, changes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        有意な変更のフィルタリング
        
        Args:
            changes: 変更データのリスト
            
        Returns:
            List[Dict[str, Any]]: 有意な変更のリスト
        """
        try:
            threshold = self.default_filters["change_threshold"] * 100
            
            significant_changes = [
                change for change in changes
                if change.get("change_percentage") is not None
                and abs(change["change_percentage"]) >= threshold
            ]
            
            self.logger.debug(
                f"有意な変更フィルタリング: {len(significant_changes)}/{len(changes)}件"
            )
            
            return significant_changes

        except Exception as e:
            self.logger.error(f"有意な変更フィルタリングエラー: {e}")
            return changes

    async def filter_by_categories(
        self,
        events: List[EconomicEvent],
        categories: Optional[List[str]] = None,
        include_unknown: bool = False
    ) -> List[EconomicEvent]:
        """
        カテゴリによるフィルタリング
        
        Args:
            events: 経済イベントリスト
            categories: 対象カテゴリリスト
            include_unknown: 不明カテゴリを含めるか
            
        Returns:
            List[EconomicEvent]: フィルタリング後のイベントリスト
        """
        if categories is None:
            categories = self.default_filters["high_impact_categories"]
        
        filtered_events = []
        
        for event in events:
            event_categories = await self._extract_event_categories(event)
            
            # カテゴリマッチング
            if any(cat in categories for cat in event_categories):
                filtered_events.append(event)
            elif include_unknown and not event_categories:
                filtered_events.append(event)
        
        return filtered_events

    async def filter_upcoming_events(
        self,
        events: List[EconomicEvent],
        hours_ahead: int = 24,
        include_high_importance_only: bool = False
    ) -> List[EconomicEvent]:
        """
        今後のイベントのフィルタリング
        
        Args:
            events: 経済イベントリスト
            hours_ahead: 何時間先まで
            include_high_importance_only: 高重要度のみ含めるか
            
        Returns:
            List[EconomicEvent]: 今後のイベントリスト
        """
        try:
            current_time = datetime.utcnow()
            future_time = current_time + timedelta(hours=hours_ahead)
            
            upcoming_events = [
                event for event in events
                if current_time <= event.date_utc <= future_time
            ]
            
            if include_high_importance_only:
                upcoming_events = [
                    event for event in upcoming_events
                    if event.is_high_importance
                ]
            
            # 時刻順にソート
            upcoming_events.sort(key=lambda x: x.date_utc)
            
            self.logger.debug(
                f"今後のイベントフィルタリング: {len(upcoming_events)}件 "
                f"(今後{hours_ahead}時間)"
            )
            
            return upcoming_events

        except Exception as e:
            self.logger.error(f"今後のイベントフィルタリングエラー: {e}")
            return []

    async def classify_events_by_impact(
        self, events: List[EconomicEvent]
    ) -> Dict[str, List[EconomicEvent]]:
        """
        影響度による事象分類
        
        Args:
            events: 経済イベントリスト
            
        Returns:
            Dict[str, List[EconomicEvent]]: 影響度別イベント分類
        """
        classification = {
            "extreme_impact": [],
            "high_impact": [],
            "medium_impact": [],
            "low_impact": []
        }
        
        for event in events:
            impact_level = await self._assess_event_impact(event)
            classification[impact_level].append(event)
        
        return classification

    async def get_priority_events(
        self,
        events: List[EconomicEvent],
        max_count: int = 10
    ) -> List[EconomicEvent]:
        """
        優先度の高いイベントの取得
        
        Args:
            events: 経済イベントリスト
            max_count: 最大取得件数
            
        Returns:
            List[EconomicEvent]: 優先度順のイベントリスト
        """
        try:
            # イベントに優先度スコアを付与
            scored_events = []
            
            for event in events:
                score = await self._calculate_priority_score(event)
                scored_events.append((score, event))
            
            # スコア順でソート（降順）
            scored_events.sort(key=lambda x: x[0], reverse=True)
            
            # 上位イベントを取得
            priority_events = [event for score, event in scored_events[:max_count]]
            
            self.logger.debug(f"優先度イベント取得: {len(priority_events)}件")
            
            return priority_events

        except Exception as e:
            self.logger.error(f"優先度イベント取得エラー: {e}")
            return events[:max_count]

    async def _is_high_impact_event(self, event: EconomicEvent) -> bool:
        """高影響度イベントの判定"""
        # 重要度チェック
        if not event.is_medium_or_higher:
            return False
        
        # 国チェック
        if event.country.lower() not in [
            country.lower() for country in self.default_filters["target_countries"]
        ]:
            return False
        
        # カテゴリチェック
        event_categories = await self._extract_event_categories(event)
        high_impact_categories = self.default_filters["high_impact_categories"]
        
        if not any(cat in high_impact_categories for cat in event_categories):
            return False
        
        return True

    async def _extract_event_categories(self, event: EconomicEvent) -> List[str]:
        """イベントからカテゴリを抽出"""
        categories = []
        event_name_lower = event.event_name.lower()
        
        # イベント名からカテゴリを推定
        category_keywords = {
            "inflation": ["cpi", "inflation", "price", "ppi"],
            "employment": ["employment", "unemployment", "payroll", "jobs"],
            "interest_rate": ["interest rate", "policy rate", "fed", "boj", "ecb", "boe"],
            "gdp": ["gdp", "gross domestic product"],
            "trade": ["trade balance", "exports", "imports"],
            "monetary_policy": ["monetary policy", "fomc", "central bank"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in event_name_lower for keyword in keywords):
                categories.append(category)
        
        # 明示的なカテゴリがあれば追加
        if event.category:
            categories.append(event.category.lower())
        
        return list(set(categories))  # 重複除去

    async def _assess_event_impact(self, event: EconomicEvent) -> str:
        """イベント影響度の評価"""
        score = 0
        
        # 重要度による基本スコア
        importance_scores = {"high": 3, "medium": 2, "low": 1}
        score += importance_scores.get(event.importance.value, 1)
        
        # 国による重み
        major_countries = ["united states", "japan", "euro zone", "united kingdom"]
        if event.country.lower() in major_countries:
            score += 2
        
        # カテゴリによる重み
        event_categories = await self._extract_event_categories(event)
        high_impact_categories = ["interest_rate", "employment", "inflation"]
        if any(cat in high_impact_categories for cat in event_categories):
            score += 2
        
        # 影響度レベルの決定
        if score >= 7:
            return "extreme_impact"
        elif score >= 5:
            return "high_impact"
        elif score >= 3:
            return "medium_impact"
        else:
            return "low_impact"

    async def _calculate_priority_score(self, event: EconomicEvent) -> float:
        """優先度スコアの計算"""
        score = 0.0
        
        # 重要度スコア
        importance_scores = {"high": 10.0, "medium": 5.0, "low": 1.0}
        score += importance_scores.get(event.importance.value, 1.0)
        
        # 時間的緊急度（近い将来ほど高スコア）
        current_time = datetime.utcnow()
        time_diff_hours = (event.date_utc - current_time).total_seconds() / 3600
        
        if 0 <= time_diff_hours <= 24:
            score += 5.0  # 24時間以内
        elif 24 < time_diff_hours <= 72:
            score += 3.0  # 3日以内
        elif 72 < time_diff_hours <= 168:
            score += 1.0  # 1週間以内
        
        # 国による重み
        major_countries_weight = {
            "united states": 3.0,
            "japan": 2.5,
            "euro zone": 2.5,
            "united kingdom": 2.0,
            "canada": 1.5,
            "australia": 1.5
        }
        score += major_countries_weight.get(event.country.lower(), 0.5)
        
        # カテゴリによる重み
        event_categories = await self._extract_event_categories(event)
        category_weights = {
            "interest_rate": 3.0,
            "employment": 2.5,
            "inflation": 2.5,
            "gdp": 2.0,
            "trade": 1.5
        }
        
        for category in event_categories:
            score += category_weights.get(category, 0.5)
        
        return score

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "filter": "EventFilter",
            "filter_count": self._filter_count,
            "filtered_events": self._filtered_events,
            "filter_settings": self.default_filters,
            "filter_rate": self._filtered_events / max(1, self._filter_count)
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # フィルター設定の確認
            required_settings = [
                "importance_levels", "target_countries", 
                "high_impact_categories", "change_threshold", "surprise_threshold"
            ]
            
            for setting in required_settings:
                if setting not in self.default_filters:
                    self.logger.error(f"必須フィルター設定が不足: {setting}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False

    def update_filter_settings(self, new_settings: Dict[str, Any]) -> None:
        """フィルター設定の更新"""
        self.default_filters.update(new_settings)
        self.logger.info("フィルター設定を更新しました")

    def get_filter_summary(self) -> Dict[str, Any]:
        """フィルターサマリーを取得"""
        return {
            "total_filters_applied": self._filter_count,
            "total_events_filtered": self._filtered_events,
            "current_settings": self.default_filters,
            "filter_efficiency": self._filtered_events / max(1, self._filter_count)
        }
