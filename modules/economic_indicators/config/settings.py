"""
経済指標モジュールの設定

経済指標データ収集と管理の設定を管理します。
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ...data_persistence.models.economic_indicators import ImpactLevel, IndicatorType


class EconomicDataProvider(Enum):
    """経済指標データプロバイダー"""

    TRADING_ECONOMICS = "trading_economics"
    FRED = "fred"
    INVESTING_CALENDAR = "investing_calendar"


@dataclass
class TradingEconomicsConfig:
    """Trading Economics API設定"""

    api_key: str
    rate_limit_requests_per_hour: int = 1000
    rate_limit_burst_capacity: int = 50
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5  # 秒


@dataclass
class FREDConfig:
    """FRED API設定"""

    api_key: str
    rate_limit_requests_per_hour: int = 120
    rate_limit_burst_capacity: int = 10
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5  # 秒


@dataclass
class CollectionConfig:
    """収集設定"""

    countries: List[str]
    indicator_types: List[IndicatorType]
    update_interval_hours: int = 6
    calendar_lookahead_days: int = 30
    historical_days: int = 365
    priority_indicators: List[IndicatorType] = None

    def __post_init__(self):
        if self.priority_indicators is None:
            self.priority_indicators = [
                IndicatorType.GDP,
                IndicatorType.INTEREST_RATE,
                IndicatorType.INFLATION,
                IndicatorType.UNEMPLOYMENT,
            ]


@dataclass
class EconomicIndicatorsSettings:
    """経済指標モジュールの設定"""

    # プロバイダー設定
    primary_provider: EconomicDataProvider = EconomicDataProvider.TRADING_ECONOMICS
    trading_economics: TradingEconomicsConfig = field(
        default_factory=lambda: TradingEconomicsConfig(api_key="")
    )
    fred: FREDConfig = field(default_factory=lambda: FREDConfig(api_key=""))

    # 収集設定
    collection: CollectionConfig = field(
        default_factory=lambda: CollectionConfig(
            countries=[
                "US",
                "JP",
                "EU",
                "GB",
                "CH",
                "AU",
                "CA",
                "NZ",
                "DE",
                "FR",
                "IT",
                "ES",
                "CN",
                "KR",
                "IN",
                "BR",
            ],
            indicator_types=[
                IndicatorType.GDP,
                IndicatorType.INFLATION,
                IndicatorType.UNEMPLOYMENT,
                IndicatorType.INTEREST_RATE,
                IndicatorType.TRADE_BALANCE,
                IndicatorType.CONSUMER_CONFIDENCE,
                IndicatorType.MANUFACTURING_PMI,
                IndicatorType.SERVICES_PMI,
                IndicatorType.RETAIL_SALES,
                IndicatorType.INDUSTRIAL_PRODUCTION,
            ],
        )
    )

    # ログ設定
    log_level: str = "INFO"
    log_file: str = "economic_indicators.log"

    # 監視設定
    health_check_interval: int = 300  # 5分
    metrics_retention_days: int = 30

    # データ品質設定
    min_quality_score: float = 0.7
    enable_data_validation: bool = True
    enable_impact_analysis: bool = True

    # アラート設定
    enable_high_impact_alerts: bool = True
    alert_before_hours: int = 24  # 高影響イベントの何時間前にアラート

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書に変換"""
        return {
            "primary_provider": self.primary_provider.value,
            "trading_economics": {
                "rate_limit_requests_per_hour": self.trading_economics.rate_limit_requests_per_hour,
                "rate_limit_burst_capacity": self.trading_economics.rate_limit_burst_capacity,
                "request_timeout": self.trading_economics.request_timeout,
                "retry_attempts": self.trading_economics.retry_attempts,
                "retry_delay": self.trading_economics.retry_delay,
            },
            "fred": {
                "rate_limit_requests_per_hour": self.fred.rate_limit_requests_per_hour,
                "rate_limit_burst_capacity": self.fred.rate_limit_burst_capacity,
                "request_timeout": self.fred.request_timeout,
                "retry_attempts": self.fred.retry_attempts,
                "retry_delay": self.fred.retry_delay,
            },
            "collection": {
                "countries": self.collection.countries,
                "indicator_types": [t.value for t in self.collection.indicator_types],
                "update_interval_hours": self.collection.update_interval_hours,
                "calendar_lookahead_days": self.collection.calendar_lookahead_days,
                "historical_days": self.collection.historical_days,
                "priority_indicators": [
                    t.value for t in self.collection.priority_indicators
                ],
            },
            "log_level": self.log_level,
            "log_file": self.log_file,
            "health_check_interval": self.health_check_interval,
            "metrics_retention_days": self.metrics_retention_days,
            "min_quality_score": self.min_quality_score,
            "enable_data_validation": self.enable_data_validation,
            "enable_impact_analysis": self.enable_impact_analysis,
            "enable_high_impact_alerts": self.enable_high_impact_alerts,
            "alert_before_hours": self.alert_before_hours,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EconomicIndicatorsSettings":
        """辞書から設定を作成"""
        settings = cls()

        if "primary_provider" in data:
            settings.primary_provider = EconomicDataProvider(data["primary_provider"])

        if "trading_economics" in data:
            te_data = data["trading_economics"]
            settings.trading_economics = TradingEconomicsConfig(
                api_key=te_data.get("api_key", ""),
                rate_limit_requests_per_hour=te_data.get(
                    "rate_limit_requests_per_hour", 1000
                ),
                rate_limit_burst_capacity=te_data.get("rate_limit_burst_capacity", 50),
                request_timeout=te_data.get("request_timeout", 30),
                retry_attempts=te_data.get("retry_attempts", 3),
                retry_delay=te_data.get("retry_delay", 5),
            )

        if "fred" in data:
            fred_data = data["fred"]
            settings.fred = FREDConfig(
                api_key=fred_data.get("api_key", ""),
                rate_limit_requests_per_hour=fred_data.get(
                    "rate_limit_requests_per_hour", 120
                ),
                rate_limit_burst_capacity=fred_data.get(
                    "rate_limit_burst_capacity", 10
                ),
                request_timeout=fred_data.get("request_timeout", 30),
                retry_attempts=fred_data.get("retry_attempts", 3),
                retry_delay=fred_data.get("retry_delay", 5),
            )

        if "collection" in data:
            coll_data = data["collection"]
            settings.collection = CollectionConfig(
                countries=coll_data.get("countries", []),
                indicator_types=[
                    IndicatorType(t) for t in coll_data.get("indicator_types", [])
                ],
                update_interval_hours=coll_data.get("update_interval_hours", 6),
                calendar_lookahead_days=coll_data.get("calendar_lookahead_days", 30),
                historical_days=coll_data.get("historical_days", 365),
                priority_indicators=[
                    IndicatorType(t) for t in coll_data.get("priority_indicators", [])
                ],
            )

        if "log_level" in data:
            settings.log_level = data["log_level"]

        if "log_file" in data:
            settings.log_file = data["log_file"]

        if "health_check_interval" in data:
            settings.health_check_interval = data["health_check_interval"]

        if "metrics_retention_days" in data:
            settings.metrics_retention_days = data["metrics_retention_days"]

        if "min_quality_score" in data:
            settings.min_quality_score = data["min_quality_score"]

        if "enable_data_validation" in data:
            settings.enable_data_validation = data["enable_data_validation"]

        if "enable_impact_analysis" in data:
            settings.enable_impact_analysis = data["enable_impact_analysis"]

        if "enable_high_impact_alerts" in data:
            settings.enable_high_impact_alerts = data["enable_high_impact_alerts"]

        if "alert_before_hours" in data:
            settings.alert_before_hours = data["alert_before_hours"]

        return settings
