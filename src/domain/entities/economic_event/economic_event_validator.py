"""
経済イベントバリデーター
EconomicEventのバリデーション機能を提供
"""

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal
from typing import Any, List

from .economic_event import EconomicEvent, Importance


@dataclass
class ValidationError:
    """バリデーションエラー"""

    field: str
    message: str
    value: Any = None


class EconomicEventValidator:
    """経済イベントバリデーター"""

    def __init__(self):
        self.errors: List[ValidationError] = []

    def validate(self, event: EconomicEvent) -> bool:
        """
        経済イベントの完全なバリデーション

        Args:
            event: バリデーション対象のEconomicEvent

        Returns:
            bool: バリデーション成功時True
        """
        self.errors.clear()

        # 必須フィールドの検証
        self._validate_required_fields(event)

        # データ型の検証
        self._validate_data_types(event)

        # 値の範囲検証
        self._validate_value_ranges(event)

        # ビジネスルールの検証
        self._validate_business_rules(event)

        return len(self.errors) == 0

    def _validate_required_fields(self, event: EconomicEvent) -> None:
        """必須フィールドの検証"""
        if not event.event_id:
            self.errors.append(ValidationError("event_id", "event_idは必須です"))

        if not event.date_utc:
            self.errors.append(ValidationError("date_utc", "date_utcは必須です"))

        if not event.country:
            self.errors.append(ValidationError("country", "countryは必須です"))

        if not event.event_name:
            self.errors.append(ValidationError("event_name", "event_nameは必須です"))

    def _validate_data_types(self, event: EconomicEvent) -> None:
        """データ型の検証"""
        if not isinstance(event.event_id, str):
            self.errors.append(
                ValidationError(
                    "event_id",
                    "event_idは文字列である必要があります",
                    type(event.event_id),
                )
            )

        if not isinstance(event.date_utc, datetime):
            self.errors.append(
                ValidationError(
                    "date_utc",
                    "date_utcはdatetimeである必要があります",
                    type(event.date_utc),
                )
            )

        if event.time_utc is not None and not isinstance(event.time_utc, time):
            self.errors.append(
                ValidationError(
                    "time_utc",
                    "time_utcはtimeである必要があります",
                    type(event.time_utc),
                )
            )

        if not isinstance(event.country, str):
            self.errors.append(
                ValidationError(
                    "country",
                    "countryは文字列である必要があります",
                    type(event.country),
                )
            )

        if not isinstance(event.event_name, str):
            self.errors.append(
                ValidationError(
                    "event_name",
                    "event_nameは文字列である必要があります",
                    type(event.event_name),
                )
            )

        if not isinstance(event.importance, Importance):
            self.errors.append(
                ValidationError(
                    "importance",
                    "importanceはImportance列挙型である必要があります",
                    type(event.importance),
                )
            )

    def _validate_value_ranges(self, event: EconomicEvent) -> None:
        """値の範囲検証"""
        # 日付の妥当性
        if event.date_utc:
            if event.date_utc.year < 2000 or event.date_utc.year > 2030:
                self.errors.append(
                    ValidationError(
                        "date_utc",
                        "date_utcは2000年から2030年の間である必要があります",
                        event.date_utc.year,
                    )
                )

        # 数値の妥当性
        for field_name, value in [
            ("actual_value", event.actual_value),
            ("forecast_value", event.forecast_value),
            ("previous_value", event.previous_value),
        ]:
            if value is not None:
                if not isinstance(value, Decimal):
                    self.errors.append(
                        ValidationError(
                            field_name,
                            f"{field_name}はDecimalである必要があります",
                            type(value),
                        )
                    )
                elif value < -1e12 or value > 1e12:
                    self.errors.append(
                        ValidationError(
                            field_name,
                            f"{field_name}は-1e12から1e12の範囲である必要があります",
                            value,
                        )
                    )

    def _validate_business_rules(self, event: EconomicEvent) -> None:
        """ビジネスルールの検証"""
        # 国名の妥当性
        valid_countries = [
            "japan",
            "united states",
            "euro zone",
            "united kingdom",
            "australia",
            "canada",
            "switzerland",
            "new zealand",
        ]

        if event.country.lower() not in valid_countries:
            self.errors.append(
                ValidationError(
                    "country",
                    f"countryは有効な国名である必要があります: {valid_countries}",
                    event.country,
                )
            )

        # 通貨の妥当性
        if event.currency:
            valid_currencies = ["USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF", "NZD"]
            if event.currency.upper() not in valid_currencies:
                self.errors.append(
                    ValidationError(
                        "currency",
                        f"currencyは有効な通貨コードである必要があります: {valid_currencies}",
                        event.currency,
                    )
                )

        # 実際値と予測値の整合性
        if (
            event.has_actual_value
            and event.has_forecast_value
            and event.actual_value == event.forecast_value
        ):
            # 実際値と予測値が同じ場合は警告（エラーではない）
            pass

    def validate_for_notification(self, event: EconomicEvent) -> bool:
        """
        通知対象としてのバリデーション

        Args:
            event: バリデーション対象のEconomicEvent

        Returns:
            bool: 通知対象として妥当な場合True
        """
        self.errors.clear()

        # 基本バリデーション
        if not self.validate(event):
            return False

        # 通知条件の検証
        if not event.is_medium_or_higher:
            self.errors.append(
                ValidationError(
                    "importance",
                    "通知対象は中重要度以上である必要があります",
                    event.importance.value,
                )
            )

        # 今後のイベントである必要がある
        if not event.is_upcoming:
            self.errors.append(
                ValidationError(
                    "date_utc",
                    "通知対象は今後のイベントである必要があります",
                    event.date_utc,
                )
            )

        return len(self.errors) == 0

    def validate_for_ai_analysis(self, event: EconomicEvent) -> bool:
        """
        AI分析対象としてのバリデーション

        Args:
            event: バリデーション対象のEconomicEvent

        Returns:
            bool: AI分析対象として妥当な場合True
        """
        self.errors.clear()

        # 基本バリデーション
        if not self.validate(event):
            return False

        # AI分析条件の検証
        if not event.is_high_importance:
            self.errors.append(
                ValidationError(
                    "importance",
                    "AI分析対象は高重要度である必要があります",
                    event.importance.value,
                )
            )

        # 特定のイベントタイプのみ
        target_events = [
            "Consumer Price Index (CPI)",
            "Gross Domestic Product (GDP)",
            "Employment Report",
            "Interest Rate Decision",
            "Bank of Japan Policy Rate",
            "Federal Reserve Interest Rate Decision",
            "ECB Interest Rate Decision",
            "Bank of England Interest Rate Decision",
            "Non-Farm Payrolls",
            "Eurozone CPI",
            "UK CPI",
        ]

        if not any(target in event.event_name for target in target_events):
            self.errors.append(
                ValidationError(
                    "event_name",
                    "AI分析対象は特定のイベントタイプである必要があります",
                    event.event_name,
                )
            )

        return len(self.errors) == 0

    def get_errors(self) -> List[ValidationError]:
        """バリデーションエラーを取得"""
        return self.errors.copy()

    def get_error_messages(self) -> List[str]:
        """バリデーションエラーメッセージを取得"""
        return [f"{error.field}: {error.message}" for error in self.errors]

    def has_errors(self) -> bool:
        """エラーがあるかどうか"""
        return len(self.errors) > 0
