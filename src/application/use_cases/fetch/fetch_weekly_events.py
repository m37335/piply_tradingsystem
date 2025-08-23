"""
週間イベント取得ユースケース

週間の経済イベントを取得するユースケース
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.domain.services.investpy import InvestpyService
from src.infrastructure.database.repositories.sql import (
    SQLEconomicCalendarRepository
)


class FetchWeeklyEventsUseCase:
    """
    週間イベント取得ユースケース
    
    週間の経済イベントを取得する
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
        start_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        週間イベント取得の実行
        
        Args:
            start_date: 開始日（DD/MM/YYYY形式）
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            self.logger.info("週間イベント取得開始")
            start_time = datetime.utcnow()
            
            # デフォルト値の設定
            if not start_date:
                # 翌週の月曜日を開始日とする
                today = datetime.utcnow()
                days_until_monday = (7 - today.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                start_date = (today + timedelta(days=days_until_monday)).strftime("%d/%m/%Y")
            
            if not countries:
                countries = ["japan", "united states", "euro zone", "united kingdom"]
            if not importances:
                importances = ["high", "medium"]
            
            # 終了日（開始日から7日後）
            start_dt = datetime.strptime(start_date, "%d/%m/%Y")
            end_dt = start_dt + timedelta(days=6)
            end_date = end_dt.strftime("%d/%m/%Y")
            
            # データ取得
            df = await self.investpy_service.fetch_weekly_events(start_date)
            
            if df.empty:
                self.logger.info("週間のイベントはありません")
                return {
                    "success": True,
                    "message": "週間のイベントはありません",
                    "records_fetched": 0,
                    "records_updated": 0,
                    "records_new": 0,
                    "fetch_type": "weekly",
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            
            # フィルタリング
            filtered_df = df[
                (df["country"].isin(countries)) &
                (df["importance"].isin(importances))
            ]
            
            # データベースへの保存
            saved_events = await self._save_events_to_database(filtered_df, "weekly")
            
            # 結果の集計
            result = {
                "success": True,
                "message": "週間イベント取得が完了しました",
                "records_fetched": len(filtered_df),
                "records_updated": saved_events["updated"],
                "records_new": saved_events["new"],
                "fetch_type": "weekly",
                "start_date": start_date,
                "end_date": end_date,
                "countries": countries,
                "importances": importances,
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"週間イベント取得完了: "
                f"{result['records_fetched']}件取得, "
                f"{result['records_new']}件新規, "
                f"{result['records_updated']}件更新"
            )
            
            return result

        except Exception as e:
            self.logger.error(f"週間イベント取得エラー: {e}")
            return {
                "success": False,
                "message": f"週間イベント取得中にエラーが発生しました: {str(e)}",
                "error": str(e),
                "fetch_type": "weekly",
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

    async def get_weekly_events_summary(
        self, start_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """週間イベントのサマリーを取得"""
        try:
            if not start_date:
                # 翌週の月曜日を開始日とする
                today = datetime.utcnow()
                days_until_monday = (7 - today.weekday()) % 7
                if days_until_monday == 0:
                    days_until_monday = 7
                start_date = (today + timedelta(days=days_until_monday)).strftime("%Y-%m-%d")
            
            # 終了日
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = start_dt + timedelta(days=6)
            end_date = end_dt.strftime("%Y-%m-%d")
            
            # データベースから週間のイベントを取得
            events = await self.repository.get_events_by_date_range(
                start_date=start_date,
                end_date=end_date
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
            
            # 日別集計
            daily_events = {}
            for event in events:
                date = event.date_utc.strftime("%Y-%m-%d")
                if date not in daily_events:
                    daily_events[date] = 0
                daily_events[date] += 1
            
            return {
                "start_date": start_date,
                "end_date": end_date,
                "total_events": total_events,
                "high_importance": high_importance,
                "medium_importance": medium_importance,
                "low_importance": low_importance,
                "countries": countries,
                "daily_events": daily_events,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"週間イベントサマリー取得エラー: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
