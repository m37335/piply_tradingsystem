"""
Investpyバリデーター

データ検証とビジネスルール検証
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date

from src.domain.entities import EconomicEvent
from src.infrastructure.config.investpy import InvestpyConfig


class InvestpyValidator:
    """
    Investpyバリデーター
    
    取得したデータの検証、ビジネスルールの適用を行う
    """

    def __init__(self, config: InvestpyConfig):
        """
        初期化
        
        Args:
            config: Investpy設定
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    def validate_fetch_parameters(
        self,
        from_date: str,
        to_date: str,
        countries: List[str],
        importances: List[str],
    ) -> bool:
        """
        取得パラメータの検証
        
        Args:
            from_date: 開始日
            to_date: 終了日
            countries: 対象国リスト
            importances: 重要度リスト
            
        Returns:
            bool: 検証結果
            
        Raises:
            ValueError: パラメータが無効な場合
        """
        try:
            # 日付形式の検証
            self._validate_date_format(from_date)
            self._validate_date_format(to_date)

            # 日付の論理的整合性検証
            self._validate_date_range(from_date, to_date)

            # 国リストの検証
            self._validate_countries(countries)

            # 重要度リストの検証
            self._validate_importances(importances)

            self.logger.debug("取得パラメータ検証完了")
            return True

        except ValueError as e:
            self.logger.error(f"パラメータ検証エラー: {e}")
            raise

    def validate_economic_event(self, event: EconomicEvent) -> bool:
        """
        経済イベントの検証
        
        Args:
            event: 検証対象の経済イベント
            
        Returns:
            bool: 検証結果
        """
        try:
            # 必須フィールドの検証
            if not self._validate_required_fields(event):
                return False

            # データ型の検証
            if not self._validate_data_types(event):
                return False

            # ビジネスルールの検証
            if not self._validate_business_rules(event):
                return False

            # 値の妥当性検証
            if not self._validate_value_ranges(event):
                return False

            return True

        except Exception as e:
            self.logger.warning(f"イベント検証エラー: {e}, event_id: {event.event_id}")
            return False

    def validate_data_quality(self, events: List[EconomicEvent]) -> Dict[str, Any]:
        """
        データ品質の検証
        
        Args:
            events: 検証対象のイベントリスト
            
        Returns:
            Dict[str, Any]: データ品質レポート
        """
        if not events:
            return {
                "total_events": 0,
                "quality_score": 0.0,
                "issues": ["データが空です"],
            }

        total_events = len(events)
        quality_issues = []
        
        # 重複チェック
        event_ids = [event.event_id for event in events]
        duplicates = len(event_ids) - len(set(event_ids))
        if duplicates > 0:
            quality_issues.append(f"重複イベント: {duplicates}件")

        # 必須フィールドの欠損チェック
        missing_event_names = sum(
            1 for event in events if not event.event_name or event.event_name.strip() == ""
        )
        if missing_event_names > 0:
            quality_issues.append(f"イベント名欠損: {missing_event_names}件")

        # 日付の妥当性チェック
        invalid_dates = sum(
            1 for event in events 
            if not isinstance(event.date_utc, datetime)
        )
        if invalid_dates > 0:
            quality_issues.append(f"無効な日付: {invalid_dates}件")

        # 重要度の分布チェック
        importance_counts = {}
        for event in events:
            importance = event.importance or "unknown"
            importance_counts[importance] = importance_counts.get(importance, 0) + 1

        # 予測値の精度チェック
        forecast_accuracy = self._calculate_forecast_accuracy(events)
        if forecast_accuracy < 0.7:
            quality_issues.append(f"予測値精度低下: {forecast_accuracy:.2%}")

        # 全体的な品質スコア計算
        quality_score = max(0.0, 1.0 - len(quality_issues) * 0.1)

        return {
            "total_events": total_events,
            "quality_score": quality_score,
            "issues": quality_issues,
            "duplicates": duplicates,
            "missing_event_names": missing_event_names,
            "invalid_dates": invalid_dates,
            "importance_distribution": importance_counts,
            "forecast_accuracy": forecast_accuracy,
        }

    def _validate_date_format(self, date_str: str) -> bool:
        """
        日付形式の検証
        """
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
            return True
        except ValueError:
            raise ValueError(f"無効な日付形式: {date_str} (期待形式: dd/mm/yyyy)")

    def _validate_date_range(self, from_date: str, to_date: str) -> bool:
        """
        日付範囲の検証
        """
        from_dt = datetime.strptime(from_date, "%d/%m/%Y")
        to_dt = datetime.strptime(to_date, "%d/%m/%Y")

        if from_dt > to_dt:
            raise ValueError(f"開始日が終了日より後です: {from_date} > {to_date}")

        # 最大範囲の検証（例: 1年以内）
        max_days = 365
        if (to_dt - from_dt).days > max_days:
            raise ValueError(f"日付範囲が大きすぎます: {(to_dt - from_dt).days}日 > {max_days}日")

        return True

    def _validate_countries(self, countries: List[str]) -> bool:
        """
        国リストの検証
        """
        if not countries:
            raise ValueError("国リストが空です")

        valid_countries = [
            "japan", "united states", "euro zone", "eurozone",
            "united kingdom", "australia", "canada", "switzerland",
            "new zealand", "china", "south korea"
        ]

        invalid_countries = [
            country for country in countries
            if country.lower() not in valid_countries
        ]

        if invalid_countries:
            self.logger.warning(f"サポートされていない国: {invalid_countries}")

        return True

    def _validate_importances(self, importances: List[str]) -> bool:
        """
        重要度リストの検証
        """
        if not importances:
            raise ValueError("重要度リストが空です")

        valid_importances = ["low", "medium", "high"]
        invalid_importances = [
            importance for importance in importances
            if importance.lower() not in valid_importances
        ]

        if invalid_importances:
            raise ValueError(f"無効な重要度: {invalid_importances}")

        return True

    def _validate_required_fields(self, event: EconomicEvent) -> bool:
        """
        必須フィールドの検証
        """
        required_fields = [
            ("event_id", event.event_id),
            ("event_name", event.event_name),
            ("country", event.country),
            ("importance", event.importance),
            ("date_utc", event.date_utc),
        ]

        for field_name, field_value in required_fields:
            if not field_value or (isinstance(field_value, str) and field_value.strip() == ""):
                self.logger.warning(f"必須フィールド欠損: {field_name}")
                return False

        return True

    def _validate_data_types(self, event: EconomicEvent) -> bool:
        """
        データ型の検証
        """
        try:
            # 日付型の検証
            if not isinstance(event.date_utc, datetime):
                self.logger.warning(f"無効な日付型: {type(event.date_utc)}")
                return False

            # 数値型の検証
            numeric_fields = [
                event.actual_value, event.forecast_value, event.previous_value
            ]
            for value in numeric_fields:
                if value is not None and not isinstance(value, (int, float)):
                    self.logger.warning(f"無効な数値型: {type(value)}")
                    return False

            return True

        except Exception as e:
            self.logger.warning(f"データ型検証エラー: {e}")
            return False

    def _validate_business_rules(self, event: EconomicEvent) -> bool:
        """
        ビジネスルールの検証
        """
        # 重要度の検証
        valid_importances = ["low", "medium", "high"]
        if event.importance.lower() not in valid_importances:
            self.logger.warning(f"無効な重要度: {event.importance}")
            return False

        # 日付の合理性検証（過去1年～未来1年の範囲）
        now = datetime.utcnow()
        one_year_ago = datetime(now.year - 1, now.month, now.day)
        one_year_ahead = datetime(now.year + 1, now.month, now.day)

        if not (one_year_ago <= event.date_utc <= one_year_ahead):
            self.logger.warning(f"日付が範囲外: {event.date_utc}")
            return False

        # 数値の合理性検証
        numeric_values = [
            event.actual_value, event.forecast_value, event.previous_value
        ]
        for value in numeric_values:
            if value is not None and abs(value) > 1000000:  # 100万を超える値は疑わしい
                self.logger.warning(f"異常に大きな数値: {value}")
                return False

        return True

    def _validate_value_ranges(self, event: EconomicEvent) -> bool:
        """
        値の範囲検証
        """
        # イベント名の長さ検証
        if len(event.event_name) > 500:
            self.logger.warning(f"イベント名が長すぎます: {len(event.event_name)}文字")
            return False

        # 国名の検証
        if len(event.country) > 100:
            self.logger.warning(f"国名が長すぎます: {len(event.country)}文字")
            return False

        return True

    def _calculate_forecast_accuracy(self, events: List[EconomicEvent]) -> float:
        """
        予測値の精度を計算
        """
        accurate_forecasts = 0
        total_forecasts = 0

        for event in events:
            if (event.forecast_value is not None and 
                event.actual_value is not None):
                total_forecasts += 1
                
                # 10%以内の誤差を精度とみなす
                if event.forecast_value != 0:
                    error_rate = abs(
                        (event.actual_value - event.forecast_value) / 
                        event.forecast_value
                    )
                    if error_rate <= 0.1:
                        accurate_forecasts += 1

        return accurate_forecasts / total_forecasts if total_forecasts > 0 else 0.0

    def get_validation_rules(self) -> Dict[str, Any]:
        """
        検証ルールの取得
        
        Returns:
            Dict[str, Any]: 検証ルール
        """
        return {
            "required_fields": [
                "event_id", "event_name", "country", "importance", "date_utc"
            ],
            "valid_importances": ["low", "medium", "high"],
            "date_range_max_days": 365,
            "max_event_name_length": 500,
            "max_country_name_length": 100,
            "max_numeric_value": 1000000,
            "forecast_accuracy_threshold": 0.1,
        }

    def get_validator_stats(self) -> Dict[str, Any]:
        """
        バリデーター統計情報を取得
        
        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            "validator": "InvestpyValidator",
            "config": {
                "default_countries": self.config.default_countries,
                "default_importances": self.config.default_importances,
                "max_events": self.config.max_events,
            },
            "validation_rules": self.get_validation_rules(),
        }
