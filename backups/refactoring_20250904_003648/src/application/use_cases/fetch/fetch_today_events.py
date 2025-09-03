"""
当日イベント取得ユースケース

当日の経済イベントを取得するユースケース
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.domain.services.investpy import InvestpyService
from src.infrastructure.database.repositories.sql import (
    SQLEconomicCalendarRepository
)


class FetchTodayEventsUseCase:
    """
    当日イベント取得ユースケース
    
    当日の経済イベントを取得する
    """

    def __init__(
        self,
        investpy_service: InvestpyService,
        repository: SQLEconomicCalendarRepository,
    ):
        """
        初期化
        
        Args:
            investpy_service: Investpyサービス
            repository: 経済カレンダーリポジトリ
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.investpy_service = investpy_service
        self.repository = repository

    async def execute(
        self,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        当日イベント取得の実行
        
        Args:
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            self.logger.info("当日イベント取得開始")
            start_time = datetime.utcnow()
            
            # デフォルト値の設定
            if not countries:
                countries = ["japan", "united states", "euro zone", "united kingdom"]
            if not importances:
                importances = ["high", "medium"]
            
            # 当日の日付
            today = datetime.utcnow().strftime("%d/%m/%Y")
            
            # データ取得
            df = await self.investpy_service.fetch_today_events()
            
            if df.empty:
                self.logger.info("当日のイベントはありません")
                return {
                    "success": True,
                    "message": "当日のイベントはありません",
                    "records_fetched": 0,
                    "records_updated": 0,
                    "records_new": 0,
                    "fetch_type": "daily",
                    "date": today,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            
            # フィルタリング
            filtered_df = df[
                (df["country"].isin(countries)) &
                (df["importance"].isin(importances))
            ]
            
            # データベースへの保存
            saved_events = await self._save_events_to_database(filtered_df, "daily")
            
            # 結果の集計
            result = {
                "success": True,
                "message": "当日イベント取得が完了しました",
                "records_fetched": len(filtered_df),
                "records_updated": saved_events["updated"],
                "records_new": saved_events["new"],
                "fetch_type": "daily",
                "date": today,
                "countries": countries,
                "importances": importances,
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"当日イベント取得完了: "
                f"{result['records_fetched']}件取得, "
                f"{result['records_new']}件新規, "
                f"{result['records_updated']}件更新"
            )
            
            return result

        except Exception as e:
            self.logger.error(f"当日イベント取得エラー: {e}")
            return {
                "success": False,
                "message": f"当日イベント取得中にエラーが発生しました: {str(e)}",
                "error": str(e),
                "fetch_type": "daily",
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }

    async def _save_events_to_database(
        self, df, fetch_type: str
    ) -> Dict[str, int]:
        """
        イベントをデータベースに保存
        
        Args:
            df: 取得されたDataFrame
            fetch_type: 取得タイプ
            
        Returns:
            Dict[str, int]: 保存結果
        """
        try:
            new_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                try:
                    # イベントデータの作成
                    event_data = {
                        "event_id": str(row.get("id", "")),
                        "date_utc": row.get("date_utc"),
                        "time_utc": row.get("time_utc"),
                        "country": row.get("country", ""),
                        "zone": row.get("zone", ""),
                        "event_name": row.get("event_name", ""),
                        "importance": row.get("importance", "low"),
                        "actual_value": row.get("actual_value"),
                        "forecast_value": row.get("forecast_value"),
                        "previous_value": row.get("previous_value"),
                        "currency": row.get("currency", ""),
                        "unit": row.get("unit", ""),
                        "category": row.get("category", "")
                    }
                    
                    # 既存イベントの確認
                    existing_event = await self.repository.get_by_event_id(
                        event_data["event_id"]
                    )
                    
                    if existing_event:
                        # 更新
                        await self.repository.update(existing_event.id, event_data)
                        updated_count += 1
                    else:
                        # 新規作成
                        await self.repository.create(event_data)
                        new_count += 1
                        
                except Exception as e:
                    self.logger.error(f"イベント保存エラー: {e}")
                    continue
            
            return {
                "new": new_count,
                "updated": updated_count
            }

        except Exception as e:
            self.logger.error(f"データベース保存エラー: {e}")
            return {"new": 0, "updated": 0}

    async def get_today_events_summary(self) -> Dict[str, Any]:
        """当日イベントのサマリーを取得"""
        try:
            today = datetime.utcnow().strftime("%Y-%m-%d")
            
            # データベースから当日のイベントを取得
            events = await self.repository.get_events_by_date_range(
                start_date=today,
                end_date=today
            )
            
            # 統計情報の集計
            total_events = len(events)
            high_importance = len([e for e in events if e.importance.value == "high"])
            medium_importance = len([e for e in events if e.importance.value == "medium"])
            low_importance = len([e for e in events if e.importance.value == "low"])
            
            # 国別集計
            countries = {}
            for event in events:
                country = event.country
                if country not in countries:
                    countries[country] = 0
                countries[country] += 1
            
            return {
                "date": today,
                "total_events": total_events,
                "high_importance": high_importance,
                "medium_importance": medium_importance,
                "low_importance": low_importance,
                "countries": countries,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"当日イベントサマリー取得エラー: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
