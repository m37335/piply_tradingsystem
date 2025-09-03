"""
経済カレンダーデータ取得ユースケース

経済カレンダーデータの取得を統合するメインユースケース
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.domain.services.investpy import InvestpyService
from src.domain.entities import EconomicEvent
from src.infrastructure.database.repositories.sql import (
    SQLEconomicCalendarRepository
)


class FetchEconomicCalendarUseCase:
    """
    経済カレンダーデータ取得ユースケース
    
    経済カレンダーデータの取得を統合する
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
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
        fetch_type: str = "manual"
    ) -> Dict[str, Any]:
        """
        経済カレンダーデータ取得の実行
        
        Args:
            from_date: 開始日（DD/MM/YYYY形式）
            to_date: 終了日（DD/MM/YYYY形式）
            countries: 対象国リスト
            importances: 重要度リスト
            fetch_type: 取得タイプ（manual, weekly, daily, realtime）
            
        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            self.logger.info(f"経済カレンダーデータ取得開始: {fetch_type}")
            start_time = datetime.utcnow()
            
            # デフォルト値の設定
            if not from_date:
                from_date = datetime.utcnow().strftime("%d/%m/%Y")
            if not to_date:
                to_date = (datetime.utcnow() + timedelta(days=7)).strftime("%d/%m/%Y")
            if not countries:
                countries = ["japan", "united states", "euro zone", "united kingdom"]
            if not importances:
                importances = ["high", "medium"]
            
            # データ取得
            df = await self.investpy_service.fetch_economic_calendar(
                from_date=from_date,
                to_date=to_date,
                countries=countries,
                importances=importances
            )
            
            if df.empty:
                self.logger.warning("取得されたデータが空です")
                return {
                    "success": False,
                    "message": "データが取得できませんでした",
                    "records_fetched": 0,
                    "records_updated": 0,
                    "records_new": 0,
                    "fetch_type": fetch_type,
                    "duration": (datetime.utcnow() - start_time).total_seconds()
                }
            
            # データベースへの保存
            saved_events = await self._save_events_to_database(df, fetch_type)
            
            # 結果の集計
            result = {
                "success": True,
                "message": "データ取得が完了しました",
                "records_fetched": len(df),
                "records_updated": saved_events["updated"],
                "records_new": saved_events["new"],
                "fetch_type": fetch_type,
                "from_date": from_date,
                "to_date": to_date,
                "countries": countries,
                "importances": importances,
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(
                f"経済カレンダーデータ取得完了: "
                f"{result['records_fetched']}件取得, "
                f"{result['records_new']}件新規, "
                f"{result['records_updated']}件更新"
            )
            
            return result

        except Exception as e:
            self.logger.error(f"経済カレンダーデータ取得エラー: {e}")
            return {
                "success": False,
                "message": f"データ取得中にエラーが発生しました: {str(e)}",
                "error": str(e),
                "fetch_type": fetch_type,
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

    async def get_fetch_statistics(self) -> Dict[str, Any]:
        """取得統計情報を取得"""
        try:
            # リポジトリから統計情報を取得
            stats = await self.repository.get_statistics()
            
            # Investpyサービスの統計情報
            investpy_stats = self.investpy_service.get_stats()
            
            return {
                "repository_stats": stats,
                "investpy_stats": investpy_stats,
                "last_fetch": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {
                "error": str(e),
                "last_fetch": datetime.utcnow().isoformat()
            }

    async def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # Investpyサービスの確認
            investpy_health = self.investpy_service.health_check()
            
            # リポジトリの確認
            repo_health = await self.repository.health_check()
            
            return investpy_health and repo_health
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
