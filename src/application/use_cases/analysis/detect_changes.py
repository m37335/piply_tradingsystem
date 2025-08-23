"""
変更検出ユースケース

経済イベントの変更を検出するユースケース
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.domain.services.data_analysis import DataAnalysisService
from src.infrastructure.database.repositories.sql import (
    SQLEconomicCalendarRepository
)


class DetectChangesUseCase:
    """
    変更検出ユースケース
    
    経済イベントの変更を検出する
    """

    def __init__(
        self,
        data_analysis_service: DataAnalysisService,
        repository: SQLEconomicCalendarRepository,
    ):
        """
        初期化
        
        Args:
            data_analysis_service: データ分析サービス
            repository: 経済カレンダーリポジトリ
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_analysis_service = data_analysis_service
        self.repository = repository

    async def execute(
        self,
        hours_back: int = 24,
        importance_threshold: str = "medium"
    ) -> Dict[str, Any]:
        """
        変更検出の実行
        
        Args:
            hours_back: 何時間前からの変更を検出するか
            importance_threshold: 重要度閾値
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            self.logger.info(f"変更検出開始: {hours_back}時間前から")
            start_time = datetime.utcnow()
            
            # 指定時間前からのイベントを取得
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
            
            # データベースからイベントを取得
            events = await self.repository.get_events_since(cutoff_time)
            
            if not events:
                self.logger.info("検出対象のイベントがありません")
                return {
                    "success": True,
                    "message": "検出対象のイベントがありません",
                    "changes_detected": 0,
                    "forecast_changes": 0,
                    "actual_announcements": 0,
                    "hours_back": hours_back,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            
            # 重要度でフィルタリング
            importance_levels = ["high", "medium", "low"]
            threshold_index = importance_levels.index(importance_threshold)
            filtered_events = [
                event for event in events
                if importance_levels.index(event.importance.value) <= threshold_index
            ]
            
            # 変更検出の実行
            changes = await self._detect_changes(filtered_events)
            
            # 結果の集計
            result = {
                "success": True,
                "message": "変更検出が完了しました",
                "changes_detected": len(changes),
                "forecast_changes": len([c for c in changes if c["type"] == "forecast_change"]),
                "actual_announcements": len([c for c in changes if c["type"] == "actual_announcement"]),
                "hours_back": hours_back,
                "importance_threshold": importance_threshold,
                "changes": changes,
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"変更検出完了: {result['changes_detected']}件の変更を検出"
            )
            
            return result

        except Exception as e:
            self.logger.error(f"変更検出エラー: {e}")
            return {
                "success": False,
                "message": f"変更検出中にエラーが発生しました: {str(e)}",
                "error": str(e),
                "hours_back": hours_back,
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _detect_changes(self, events: List) -> List[Dict[str, Any]]:
        """
        変更の検出
        
        Args:
            events: イベントリスト
            
        Returns:
            List[Dict[str, Any]]: 検出された変更のリスト
        """
        try:
            changes = []
            
            for event in events:
                try:
                    # 予測値変更の検出
                    if event.forecast_value is not None:
                        # 過去の予測値と比較
                        previous_forecast = await self._get_previous_forecast(event)
                        if previous_forecast and previous_forecast != event.forecast_value:
                            change_data = {
                                "type": "forecast_change",
                                "event_id": event.event_id,
                                "event_name": event.event_name,
                                "country": event.country,
                                "importance": event.importance.value,
                                "old_forecast": previous_forecast,
                                "new_forecast": event.forecast_value,
                                "change_amount": event.forecast_value - previous_forecast,
                                "change_percentage": (
                                    (event.forecast_value - previous_forecast) / 
                                    previous_forecast * 100
                                ) if previous_forecast != 0 else 0,
                                "detected_at": datetime.utcnow().isoformat()
                            }
                            changes.append(change_data)
                    
                    # 実際値発表の検出
                    if event.actual_value is not None:
                        actual_announcement = {
                            "type": "actual_announcement",
                            "event_id": event.event_id,
                            "event_name": event.event_name,
                            "country": event.country,
                            "importance": event.importance.value,
                            "actual_value": event.actual_value,
                            "forecast_value": event.forecast_value,
                            "previous_value": event.previous_value,
                            "surprise": (
                                event.actual_value - event.forecast_value
                            ) if event.forecast_value is not None else None,
                            "detected_at": datetime.utcnow().isoformat()
                        }
                        changes.append(actual_announcement)
                        
                except Exception as e:
                    self.logger.error(f"イベント変更検出エラー: {e}")
                    continue
            
            return changes

        except Exception as e:
            self.logger.error(f"変更検出エラー: {e}")
            return []

    async def _get_previous_forecast(self, event) -> Optional[float]:
        """
        過去の予測値を取得
        
        Args:
            event: イベント
            
        Returns:
            Optional[float]: 過去の予測値
        """
        try:
            # 同じイベントの過去の予測値を取得
            previous_events = await self.repository.get_events_by_name_and_country(
                event_name=event.event_name,
                country=event.country,
                limit=5
            )
            
            for prev_event in previous_events:
                if (prev_event.id != event.id and 
                    prev_event.forecast_value is not None and
                    prev_event.date_utc < event.date_utc):
                    return prev_event.forecast_value
            
            return None

        except Exception as e:
            self.logger.error(f"過去予測値取得エラー: {e}")
            return None

    async def execute_realtime_monitoring(self) -> Dict[str, Any]:
        """リアルタイム監視の実行"""
        try:
            self.logger.info("リアルタイム監視開始")
            
            # 過去1時間の変更を検出
            result = await self.execute(hours_back=1, importance_threshold="high")
            
            # 重要な変更があればログ出力
            if result["success"] and result["changes_detected"] > 0:
                self.logger.info(
                    f"リアルタイム監視: {result['changes_detected']}件の変更を検出"
                )
                
                for change in result["changes"]:
                    if change["type"] == "forecast_change":
                        self.logger.info(
                            f"予測値変更: {change['event_name']} "
                            f"({change['country']}) - "
                            f"{change['old_forecast']} → {change['new_forecast']}"
                        )
                    elif change["type"] == "actual_announcement":
                        self.logger.info(
                            f"実際値発表: {change['event_name']} "
                            f"({change['country']}) - "
                            f"実際: {change['actual_value']}, "
                            f"予測: {change['forecast_value']}"
                        )
            
            return result

        except Exception as e:
            self.logger.error(f"リアルタイム監視エラー: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def get_change_statistics(self) -> Dict[str, Any]:
        """変更統計情報を取得"""
        try:
            # 過去24時間の変更を取得
            changes_result = await self.execute(hours_back=24)
            
            if not changes_result["success"]:
                return {"error": "統計情報の取得に失敗しました"}
            
            changes = changes_result.get("changes", [])
            
            # 統計情報の集計
            forecast_changes = [c for c in changes if c["type"] == "forecast_change"]
            actual_announcements = [c for c in changes if c["type"] == "actual_announcement"]
            
            # 国別統計
            countries = {}
            for change in changes:
                country = change["country"]
                if country not in countries:
                    countries[country] = {"forecast_changes": 0, "actual_announcements": 0}
                
                if change["type"] == "forecast_change":
                    countries[country]["forecast_changes"] += 1
                else:
                    countries[country]["actual_announcements"] += 1
            
            # 重要度別統計
            importance_stats = {"high": 0, "medium": 0, "low": 0}
            for change in changes:
                importance = change["importance"]
                if importance in importance_stats:
                    importance_stats[importance] += 1
            
            return {
                "total_changes": len(changes),
                "forecast_changes": len(forecast_changes),
                "actual_announcements": len(actual_announcements),
                "countries": countries,
                "importance_stats": importance_stats,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"変更統計情報取得エラー: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
