"""
予測値変更検出器

経済イベントの予測値変更を検出・分析する
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal

from src.domain.entities import EconomicEvent


class ForecastChangeDetector:
    """
    予測値変更検出器
    
    経済イベントの予測値変更を検出し、分析データを提供する
    """

    def __init__(self, change_threshold: float = 0.01):
        """
        初期化
        
        Args:
            change_threshold: 変更検出の閾値（デフォルト1%）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.change_threshold = change_threshold
        
        # 統計情報
        self._detection_count = 0
        self._changes_found = 0

    async def detect_changes(
        self,
        old_events: List[EconomicEvent],
        new_events: List[EconomicEvent]
    ) -> List[Dict[str, Any]]:
        """
        予測値変更の検出
        
        Args:
            old_events: 変更前のイベントリスト
            new_events: 変更後のイベントリスト
            
        Returns:
            List[Dict[str, Any]]: 検出された変更のリスト
        """
        try:
            self.logger.debug("予測値変更検出を開始")
            self._detection_count += 1
            
            # イベントIDでマッピング
            old_events_dict = {event.event_id: event for event in old_events}
            changes = []
            
            for new_event in new_events:
                if new_event.event_id in old_events_dict:
                    old_event = old_events_dict[new_event.event_id]
                    change_data = await self._analyze_event_change(old_event, new_event)
                    
                    if change_data and self._is_significant_change(change_data):
                        changes.append(change_data)
                        self._changes_found += 1
            
            self.logger.debug(f"予測値変更検出完了: {len(changes)}件の変更")
            
            return changes

        except Exception as e:
            self.logger.error(f"予測値変更検出エラー: {e}")
            return []

    async def detect_new_events(
        self,
        old_events: List[EconomicEvent],
        new_events: List[EconomicEvent]
    ) -> List[EconomicEvent]:
        """
        新規イベントの検出
        
        Args:
            old_events: 既存のイベントリスト
            new_events: 新しいイベントリスト
            
        Returns:
            List[EconomicEvent]: 新規イベントのリスト
        """
        try:
            old_event_ids = {event.event_id for event in old_events}
            new_events_only = [
                event for event in new_events
                if event.event_id not in old_event_ids
            ]
            
            self.logger.debug(f"新規イベント検出: {len(new_events_only)}件")
            
            return new_events_only

        except Exception as e:
            self.logger.error(f"新規イベント検出エラー: {e}")
            return []

    async def detect_removed_events(
        self,
        old_events: List[EconomicEvent],
        new_events: List[EconomicEvent]
    ) -> List[EconomicEvent]:
        """
        削除されたイベントの検出
        
        Args:
            old_events: 既存のイベントリスト
            new_events: 新しいイベントリスト
            
        Returns:
            List[EconomicEvent]: 削除されたイベントのリスト
        """
        try:
            new_event_ids = {event.event_id for event in new_events}
            removed_events = [
                event for event in old_events
                if event.event_id not in new_event_ids
            ]
            
            self.logger.debug(f"削除イベント検出: {len(removed_events)}件")
            
            return removed_events

        except Exception as e:
            self.logger.error(f"削除イベント検出エラー: {e}")
            return []

    async def analyze_change_patterns(
        self,
        changes: List[Dict[str, Any]],
        timeframe_hours: int = 24
    ) -> Dict[str, Any]:
        """
        変更パターンの分析
        
        Args:
            changes: 変更データのリスト
            timeframe_hours: 分析時間枠（時間）
            
        Returns:
            Dict[str, Any]: パターン分析結果
        """
        try:
            pattern_analysis = {
                "total_changes": len(changes),
                "change_types": {"increase": 0, "decrease": 0, "new_forecast": 0},
                "countries": {},
                "importance_levels": {},
                "magnitude_distribution": {"small": 0, "medium": 0, "large": 0},
                "timing_analysis": await self._analyze_change_timing(changes, timeframe_hours)
            }
            
            for change in changes:
                # 変更タイプの分類
                if change["change_type"] == "forecast_increase":
                    pattern_analysis["change_types"]["increase"] += 1
                elif change["change_type"] == "forecast_decrease":
                    pattern_analysis["change_types"]["decrease"] += 1
                else:
                    pattern_analysis["change_types"]["new_forecast"] += 1
                
                # 国別統計
                country = change["country"]
                if country not in pattern_analysis["countries"]:
                    pattern_analysis["countries"][country] = 0
                pattern_analysis["countries"][country] += 1
                
                # 重要度別統計
                importance = change["importance"]
                if importance not in pattern_analysis["importance_levels"]:
                    pattern_analysis["importance_levels"][importance] = 0
                pattern_analysis["importance_levels"][importance] += 1
                
                # 変更幅の分類
                magnitude = self._classify_change_magnitude(change["change_percentage"])
                pattern_analysis["magnitude_distribution"][magnitude] += 1
            
            return pattern_analysis

        except Exception as e:
            self.logger.error(f"変更パターン分析エラー: {e}")
            return {
                "total_changes": 0,
                "change_types": {"increase": 0, "decrease": 0, "new_forecast": 0},
                "countries": {},
                "importance_levels": {},
                "magnitude_distribution": {"small": 0, "medium": 0, "large": 0},
                "timing_analysis": {}
            }

    async def _analyze_event_change(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent
    ) -> Optional[Dict[str, Any]]:
        """個別イベントの変更分析"""
        change_data = {
            "event_id": new_event.event_id,
            "event_name": new_event.event_name,
            "country": new_event.country,
            "importance": new_event.importance.value,
            "date_utc": new_event.date_utc.isoformat(),
            "old_forecast": float(old_event.forecast_value) if old_event.forecast_value else None,
            "new_forecast": float(new_event.forecast_value) if new_event.forecast_value else None,
            "change_amount": None,
            "change_percentage": None,
            "change_type": "no_change",
            "detected_at": datetime.utcnow().isoformat()
        }
        
        # 予測値変更の分析
        if old_event.forecast_value and new_event.forecast_value:
            change_amount = new_event.forecast_value - old_event.forecast_value
            change_data["change_amount"] = float(change_amount)
            
            if old_event.forecast_value != 0:
                change_percentage = (float(change_amount) / float(old_event.forecast_value)) * 100
                change_data["change_percentage"] = change_percentage
                
                if change_percentage > 0:
                    change_data["change_type"] = "forecast_increase"
                elif change_percentage < 0:
                    change_data["change_type"] = "forecast_decrease"
        
        elif not old_event.forecast_value and new_event.forecast_value:
            # 新規予測値の追加
            change_data["change_type"] = "new_forecast_added"
            change_data["change_percentage"] = 100.0  # 新規追加として扱う
        
        elif old_event.forecast_value and not new_event.forecast_value:
            # 予測値の削除
            change_data["change_type"] = "forecast_removed"
            change_data["change_percentage"] = -100.0  # 削除として扱う
        
        # その他の変更も確認
        other_changes = []
        
        if old_event.importance != new_event.importance:
            other_changes.append({
                "field": "importance",
                "old_value": old_event.importance.value,
                "new_value": new_event.importance.value
            })
        
        if old_event.date_utc != new_event.date_utc:
            other_changes.append({
                "field": "date_utc",
                "old_value": old_event.date_utc.isoformat(),
                "new_value": new_event.date_utc.isoformat()
            })
        
        if other_changes:
            change_data["other_changes"] = other_changes
        
        return change_data if change_data["change_type"] != "no_change" else None

    def _is_significant_change(self, change_data: Dict[str, Any]) -> bool:
        """有意な変更かどうかを判定"""
        if not change_data.get("change_percentage"):
            return change_data["change_type"] in ["new_forecast_added", "forecast_removed"]
        
        abs_change = abs(change_data["change_percentage"])
        return abs_change >= (self.change_threshold * 100)

    def _classify_change_magnitude(self, change_percentage: Optional[float]) -> str:
        """変更幅の分類"""
        if not change_percentage:
            return "small"
        
        abs_change = abs(change_percentage)
        
        if abs_change >= 10.0:
            return "large"
        elif abs_change >= 5.0:
            return "medium"
        else:
            return "small"

    async def _analyze_change_timing(
        self,
        changes: List[Dict[str, Any]],
        timeframe_hours: int
    ) -> Dict[str, Any]:
        """変更タイミングの分析"""
        timing_stats = {
            "changes_by_hour": {},
            "recent_changes": 0,
            "upcoming_events": 0
        }
        
        current_time = datetime.utcnow()
        
        for change in changes:
            # 変更検出時刻の分析
            detected_time = datetime.fromisoformat(change["detected_at"].replace('Z', '+00:00'))
            hour = detected_time.hour
            
            if hour not in timing_stats["changes_by_hour"]:
                timing_stats["changes_by_hour"][hour] = 0
            timing_stats["changes_by_hour"][hour] += 1
            
            # 最近の変更カウント
            time_diff = (current_time - detected_time).total_seconds() / 3600
            if time_diff <= timeframe_hours:
                timing_stats["recent_changes"] += 1
            
            # 今後のイベントカウント
            event_time = datetime.fromisoformat(change["date_utc"].replace('Z', '+00:00'))
            if event_time > current_time:
                timing_stats["upcoming_events"] += 1
        
        return timing_stats

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "detector": "ForecastChangeDetector",
            "detection_count": self._detection_count,
            "changes_found": self._changes_found,
            "change_threshold": self.change_threshold,
            "detection_rate": self._changes_found / max(1, self._detection_count)
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本設定の確認
            if self.change_threshold < 0:
                self.logger.error("変更閾値が負の値です")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False

    def set_change_threshold(self, threshold: float) -> None:
        """変更閾値の設定"""
        if threshold >= 0:
            self.change_threshold = threshold
            self.logger.info(f"変更閾値を更新: {threshold}")
        else:
            self.logger.warning(f"無効な変更閾値: {threshold}")

    def get_change_summary(self) -> Dict[str, Any]:
        """変更サマリーを取得"""
        return {
            "total_detections": self._detection_count,
            "total_changes": self._changes_found,
            "change_rate": self._changes_found / max(1, self._detection_count),
            "current_threshold": self.change_threshold
        }
