"""
Investpyサービス

経済カレンダーデータ取得のメインサービス
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Union

import pandas as pd
from dataclasses import asdict

from src.domain.entities import EconomicEvent
from src.infrastructure.external.investpy import InvestpyClient
from src.infrastructure.config.investpy import InvestpyConfig, TimezoneConfig
from .investpy_data_processor import InvestpyDataProcessor
from .investpy_timezone_handler import InvestpyTimezoneHandler
from .investpy_validator import InvestpyValidator


class InvestpyService:
    """
    Investpyサービス
    
    経済カレンダーデータの取得、処理、検証を統合管理する
    """

    def __init__(
        self,
        investpy_client: InvestpyClient,
        config: InvestpyConfig,
        timezone_config: TimezoneConfig,
        data_processor: Optional[InvestpyDataProcessor] = None,
        timezone_handler: Optional[InvestpyTimezoneHandler] = None,
        validator: Optional[InvestpyValidator] = None,
    ):
        """
        初期化
        
        Args:
            investpy_client: Investpyクライアント
            config: Investpy設定
            timezone_config: タイムゾーン設定
            data_processor: データ処理器（デフォルト値あり）
            timezone_handler: タイムゾーンハンドラー（デフォルト値あり）
            validator: バリデーター（デフォルト値あり）
        """
        self.investpy_client = investpy_client
        self.config = config
        self.timezone_config = timezone_config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # デフォルトのサブコンポーネントを作成
        self.data_processor = data_processor or InvestpyDataProcessor(
            config
        )
        self.timezone_handler = timezone_handler or InvestpyTimezoneHandler(
            timezone_config
        )
        self.validator = validator or InvestpyValidator(config)

    async def fetch_economic_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
    ) -> List[EconomicEvent]:
        """
        経済カレンダーデータを取得
        
        Args:
            from_date: 開始日（dd/mm/yyyy形式）
            to_date: 終了日（dd/mm/yyyy形式）
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            List[EconomicEvent]: 経済イベントリスト
            
        Raises:
            ValueError: パラメータが無効な場合
            RuntimeError: データ取得に失敗した場合
        """
        try:
            self.logger.info(
                f"経済カレンダーデータ取得開始: "
                f"from={from_date}, to={to_date}, "
                f"countries={countries}, importances={importances}"
            )

            # デフォルト値の設定
            countries = countries or self.config.default_countries
            importances = importances or self.config.default_importances

            # 日付の設定（デフォルトは今日から1週間）
            if not from_date or not to_date:
                from_date, to_date = self._get_default_date_range()

            # 入力値の検証
            self.validator.validate_fetch_parameters(
                from_date, to_date, countries, importances
            )

            # 生データの取得
            raw_data = await self.investpy_client.get_economic_calendar(
                from_date=from_date,
                to_date=to_date,
                countries=countries,
                importances=importances,
            )

            if raw_data.empty:
                self.logger.warning("取得されたデータが空です")
                return []

            # データ処理
            processed_data = self.data_processor.process_raw_data(raw_data)

            # タイムゾーン変換
            timezone_processed_data = (
                self.timezone_handler.convert_to_utc(processed_data)
            )

            # エンティティ変換
            events = self._convert_to_entities(timezone_processed_data)

            # 最終検証
            validated_events = [
                event for event in events 
                if self.validator.validate_economic_event(event)
            ]

            self.logger.info(
                f"経済カレンダーデータ取得完了: {len(validated_events)}件"
            )

            return validated_events

        except Exception as e:
            self.logger.error(f"経済カレンダーデータ取得エラー: {e}")
            raise RuntimeError(f"データ取得に失敗しました: {e}") from e

    async def fetch_today_events(
        self,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
    ) -> List[EconomicEvent]:
        """
        当日のイベントを取得
        
        Args:
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            List[EconomicEvent]: 当日の経済イベントリスト
        """
        today = datetime.now().strftime("%d/%m/%Y")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")

        return await self.fetch_economic_calendar(
            from_date=today,
            to_date=tomorrow,
            countries=countries,
            importances=importances,
        )

    async def fetch_weekly_events(
        self,
        start_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
    ) -> List[EconomicEvent]:
        """
        週間イベントを取得
        
        Args:
            start_date: 開始日（dd/mm/yyyy形式）
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            List[EconomicEvent]: 週間の経済イベントリスト
        """
        if not start_date:
            start_date = datetime.now().strftime("%d/%m/%Y")

        # 開始日から7日後を終了日とする
        start_dt = datetime.strptime(start_date, "%d/%m/%Y")
        end_dt = start_dt + timedelta(days=7)
        end_date = end_dt.strftime("%d/%m/%Y")

        return await self.fetch_economic_calendar(
            from_date=start_date,
            to_date=end_date,
            countries=countries,
            importances=importances,
        )

    async def fetch_events_for_date_range(
        self,
        days_ahead: int,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None,
    ) -> List[EconomicEvent]:
        """
        指定日数分のイベントを取得
        
        Args:
            days_ahead: 先読み日数
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            List[EconomicEvent]: 指定期間の経済イベントリスト
        """
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)

        from_date = today.strftime("%d/%m/%Y")
        to_date = end_date.strftime("%d/%m/%Y")

        return await self.fetch_economic_calendar(
            from_date=from_date,
            to_date=to_date,
            countries=countries,
            importances=importances,
        )

    def _get_default_date_range(self) -> tuple[str, str]:
        """
        デフォルトの日付範囲を取得
        
        Returns:
            tuple[str, str]: (開始日, 終了日)
        """
        today = datetime.now()
        end_date = today + timedelta(days=7)  # 1週間後まで

        from_date = today.strftime("%d/%m/%Y")
        to_date = end_date.strftime("%d/%m/%Y")

        return from_date, to_date

    def _convert_to_entities(self, df: pd.DataFrame) -> List[EconomicEvent]:
        """
        DataFrameをEconomicEventエンティティのリストに変換
        
        Args:
            df: 処理済みのDataFrame
            
        Returns:
            List[EconomicEvent]: 経済イベントリスト
        """
        events = []

        for _, row in df.iterrows():
            try:
                # DataFrameの行からEconomicEventを作成
                event_data = {
                    "event_id": str(row.get("event_id", "")),
                    "date_utc": row.get("date_utc", datetime.utcnow()),
                    "time_utc": row.get("time_utc"),
                    "country": str(row.get("country", "")),
                    "zone": str(row.get("zone", "")),
                    "event_name": str(row.get("event", "")),
                    "importance": str(row.get("importance", "low")),
                    "actual_value": self._safe_float_conversion(
                        row.get("actual")
                    ),
                    "forecast_value": self._safe_float_conversion(
                        row.get("forecast")
                    ),
                    "previous_value": self._safe_float_conversion(
                        row.get("previous")
                    ),
                    "currency": str(row.get("currency", "")),
                    "unit": str(row.get("unit", "")),
                    "category": str(row.get("category", "")),
                }

                event = EconomicEvent(**event_data)
                events.append(event)

            except Exception as e:
                self.logger.warning(
                    f"エンティティ変換スキップ: {e}, row: {dict(row)}"
                )
                continue

        return events

    def _safe_float_conversion(self, value: Any) -> Optional[float]:
        """
        安全なfloat変換
        
        Args:
            value: 変換対象値
            
        Returns:
            Optional[float]: 変換結果（失敗時はNone）
        """
        if pd.isna(value) or value is None:
            return None

        try:
            if isinstance(value, str):
                # パーセンテージ記号や通貨記号を除去
                cleaned_value = (
                    value.replace("%", "")
                    .replace("$", "")
                    .replace("€", "")
                    .replace("¥", "")
                    .replace(",", "")
                    .strip()
                )
                if cleaned_value == "" or cleaned_value == "-":
                    return None
                return float(cleaned_value)
            else:
                return float(value)
        except (ValueError, TypeError):
            return None

    async def get_service_stats(self) -> Dict[str, Any]:
        """
        サービス統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        try:
            client_stats = await self.investpy_client.get_connection_stats()
            
            return {
                "service": "InvestpyService",
                "config": {
                    "default_countries": self.config.default_countries,
                    "default_importances": self.config.default_importances,
                    "retry_attempts": self.config.retry_attempts,
                    "max_events": self.config.max_events,
                },
                "client_stats": client_stats,
                "timezone_config": {
                    "default_timezone": self.timezone_config.default_timezone,
                    "display_timezone": self.timezone_config.display_timezone,
                },
            }
        except Exception as e:
            self.logger.error(f"統計情報取得エラー: {e}")
            return {
                "service": "InvestpyService",
                "error": str(e),
            }

    async def health_check(self) -> bool:
        """
        ヘルスチェック
        
        Returns:
            bool: サービスが正常かどうか
        """
        try:
            # Investpyクライアントの接続確認
            connection_ok = await self.investpy_client.test_connection()
            
            # 設定の検証
            config_valid = self.config.validate()
            timezone_config_valid = self.timezone_config.validate()
            
            return connection_ok and config_valid and timezone_config_valid
            
        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False
