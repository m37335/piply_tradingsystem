"""
LLM分析設定

LLM分析に関する設定を管理します。
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class LLMProvider(Enum):
    """LLMプロバイダー"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"


class AnalysisType(Enum):
    """分析タイプ"""

    MARKET_SENTIMENT = "market_sentiment"
    PRICE_PATTERN = "price_pattern"
    RISK_ASSESSMENT = "risk_assessment"
    TREND_ANALYSIS = "trend_analysis"
    VOLATILITY_ANALYSIS = "volatility_analysis"
    SUPPORT_RESISTANCE = "support_resistance"


class AnalysisFrequency(Enum):
    """分析頻度"""

    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    ON_DEMAND = "on_demand"


@dataclass
class LLMConfig:
    """LLM設定"""

    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-4"
    api_key: str = ""
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout_seconds: int = 60
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """環境変数から設定を読み込み"""
        provider_str = os.getenv("LLM_PROVIDER", "openai")
        provider = LLMProvider(provider_str)

        return cls(
            provider=provider,
            model_name=os.getenv("LLM_MODEL", "gpt-4"),
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL"),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4000")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.1")),
            timeout_seconds=int(os.getenv("LLM_TIMEOUT", "60")),
            retry_attempts=int(os.getenv("LLM_RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=float(os.getenv("LLM_RETRY_DELAY", "1.0")),
        )


@dataclass
class AnalysisConfig:
    """分析設定"""

    analysis_types: List[AnalysisType]
    frequency: AnalysisFrequency
    symbols: List[str]
    timeframes: List[str]
    lookback_periods: int = 100
    confidence_threshold: float = 0.7
    enable_technical_indicators: bool = True
    enable_news_sentiment: bool = True
    enable_social_sentiment: bool = False

    @classmethod
    def from_env(cls) -> "AnalysisConfig":
        """環境変数から設定を読み込み"""
        analysis_types_str = os.getenv(
            "LLM_ANALYSIS_TYPES", "market_sentiment,price_pattern,risk_assessment"
        )
        analysis_types = [
            AnalysisType(t.strip()) for t in analysis_types_str.split(",")
        ]

        frequency_str = os.getenv("LLM_ANALYSIS_FREQUENCY", "hourly")
        frequency = AnalysisFrequency(frequency_str)

        symbols_str = os.getenv("LLM_ANALYSIS_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN,TSLA")
        symbols = [s.strip() for s in symbols_str.split(",")]

        timeframes_str = os.getenv("LLM_ANALYSIS_TIMEFRAMES", "1h,4h,1d")
        timeframes = [tf.strip() for tf in timeframes_str.split(",")]

        return cls(
            analysis_types=analysis_types,
            frequency=frequency,
            symbols=symbols,
            timeframes=timeframes,
            lookback_periods=int(os.getenv("LLM_ANALYSIS_LOOKBACK_PERIODS", "100")),
            confidence_threshold=float(
                os.getenv("LLM_ANALYSIS_CONFIDENCE_THRESHOLD", "0.7")
            ),
            enable_technical_indicators=os.getenv(
                "LLM_ANALYSIS_ENABLE_TECHNICAL_INDICATORS", "true"
            ).lower()
            == "true",
            enable_news_sentiment=os.getenv(
                "LLM_ANALYSIS_ENABLE_NEWS_SENTIMENT", "true"
            ).lower()
            == "true",
            enable_social_sentiment=os.getenv(
                "LLM_ANALYSIS_ENABLE_SOCIAL_SENTIMENT", "false"
            ).lower()
            == "true",
        )


@dataclass
class DataPreparationConfig:
    """データ準備設定"""

    enable_data_aggregation: bool = True
    aggregation_window_minutes: int = 60
    enable_outlier_detection: bool = True
    outlier_threshold: float = 3.0
    enable_missing_data_interpolation: bool = True
    interpolation_method: str = "linear"
    enable_data_validation: bool = True
    validation_rules: List[str] = None

    def __post_init__(self):
        if self.validation_rules is None:
            self.validation_rules = [
                "price_positive",
                "high_ge_low",
                "volume_positive",
                "timestamp_sequential",
            ]

    @classmethod
    def from_env(cls) -> "DataPreparationConfig":
        """環境変数から設定を読み込み"""
        validation_rules_str = os.getenv(
            "LLM_DATA_VALIDATION_RULES",
            "price_positive,high_ge_low,volume_positive,timestamp_sequential",
        )
        validation_rules = [rule.strip() for rule in validation_rules_str.split(",")]

        return cls(
            enable_data_aggregation=os.getenv(
                "LLM_DATA_ENABLE_AGGREGATION", "true"
            ).lower()
            == "true",
            aggregation_window_minutes=int(
                os.getenv("LLM_DATA_AGGREGATION_WINDOW", "60")
            ),
            enable_outlier_detection=os.getenv(
                "LLM_DATA_ENABLE_OUTLIER_DETECTION", "true"
            ).lower()
            == "true",
            outlier_threshold=float(os.getenv("LLM_DATA_OUTLIER_THRESHOLD", "3.0")),
            enable_missing_data_interpolation=os.getenv(
                "LLM_DATA_ENABLE_INTERPOLATION", "true"
            ).lower()
            == "true",
            interpolation_method=os.getenv("LLM_DATA_INTERPOLATION_METHOD", "linear"),
            enable_data_validation=os.getenv(
                "LLM_DATA_ENABLE_VALIDATION", "true"
            ).lower()
            == "true",
            validation_rules=validation_rules,
        )


@dataclass
class QualityControlConfig:
    """品質管理設定"""

    enable_quality_scoring: bool = True
    quality_metrics: List[str] = None
    quality_threshold: float = 0.8
    enable_human_feedback: bool = False
    feedback_collection_interval: int = 24  # 時間
    enable_consistency_check: bool = True
    consistency_threshold: float = 0.9

    def __post_init__(self):
        if self.quality_metrics is None:
            self.quality_metrics = [
                "accuracy",
                "relevance",
                "consistency",
                "completeness",
                "timeliness",
            ]

    @classmethod
    def from_env(cls) -> "QualityControlConfig":
        """環境変数から設定を読み込み"""
        quality_metrics_str = os.getenv(
            "LLM_QUALITY_METRICS",
            "accuracy,relevance,consistency,completeness,timeliness",
        )
        quality_metrics = [metric.strip() for metric in quality_metrics_str.split(",")]

        return cls(
            enable_quality_scoring=os.getenv(
                "LLM_QUALITY_ENABLE_SCORING", "true"
            ).lower()
            == "true",
            quality_metrics=quality_metrics,
            quality_threshold=float(os.getenv("LLM_QUALITY_THRESHOLD", "0.8")),
            enable_human_feedback=os.getenv(
                "LLM_QUALITY_ENABLE_HUMAN_FEEDBACK", "false"
            ).lower()
            == "true",
            feedback_collection_interval=int(
                os.getenv("LLM_QUALITY_FEEDBACK_INTERVAL", "24")
            ),
            enable_consistency_check=os.getenv(
                "LLM_QUALITY_ENABLE_CONSISTENCY_CHECK", "true"
            ).lower()
            == "true",
            consistency_threshold=float(
                os.getenv("LLM_QUALITY_CONSISTENCY_THRESHOLD", "0.9")
            ),
        )


@dataclass
class LLMAnalysisSettings:
    """LLM分析設定"""

    llm: LLMConfig
    analysis: AnalysisConfig
    data_preparation: DataPreparationConfig
    quality_control: QualityControlConfig
    enable_caching: bool = True
    cache_ttl_seconds: int = 3600
    enable_monitoring: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "LLMAnalysisSettings":
        """環境変数から設定を読み込み"""
        return cls(
            llm=LLMConfig.from_env(),
            analysis=AnalysisConfig.from_env(),
            data_preparation=DataPreparationConfig.from_env(),
            quality_control=QualityControlConfig.from_env(),
            enable_caching=os.getenv("LLM_ANALYSIS_ENABLE_CACHING", "true").lower()
            == "true",
            cache_ttl_seconds=int(os.getenv("LLM_ANALYSIS_CACHE_TTL", "3600")),
            enable_monitoring=os.getenv(
                "LLM_ANALYSIS_ENABLE_MONITORING", "true"
            ).lower()
            == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書に変換"""
        return {
            "llm": {
                "provider": self.llm.provider.value,
                "model_name": self.llm.model_name,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "timeout_seconds": self.llm.timeout_seconds,
                "retry_attempts": self.llm.retry_attempts,
            },
            "analysis": {
                "analysis_types": [t.value for t in self.analysis.analysis_types],
                "frequency": self.analysis.frequency.value,
                "symbols": self.analysis.symbols,
                "timeframes": self.analysis.timeframes,
                "lookback_periods": self.analysis.lookback_periods,
                "confidence_threshold": self.analysis.confidence_threshold,
                "enable_technical_indicators": self.analysis.enable_technical_indicators,
                "enable_news_sentiment": self.analysis.enable_news_sentiment,
                "enable_social_sentiment": self.analysis.enable_social_sentiment,
            },
            "data_preparation": {
                "enable_data_aggregation": self.data_preparation.enable_data_aggregation,
                "aggregation_window_minutes": self.data_preparation.aggregation_window_minutes,
                "enable_outlier_detection": self.data_preparation.enable_outlier_detection,
                "outlier_threshold": self.data_preparation.outlier_threshold,
                "enable_missing_data_interpolation": self.data_preparation.enable_missing_data_interpolation,
                "interpolation_method": self.data_preparation.interpolation_method,
                "enable_data_validation": self.data_preparation.enable_data_validation,
                "validation_rules": self.data_preparation.validation_rules,
            },
            "quality_control": {
                "enable_quality_scoring": self.quality_control.enable_quality_scoring,
                "quality_metrics": self.quality_control.quality_metrics,
                "quality_threshold": self.quality_control.quality_threshold,
                "enable_human_feedback": self.quality_control.enable_human_feedback,
                "feedback_collection_interval": self.quality_control.feedback_collection_interval,
                "enable_consistency_check": self.quality_control.enable_consistency_check,
                "consistency_threshold": self.quality_control.consistency_threshold,
            },
            "enable_caching": self.enable_caching,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "enable_monitoring": self.enable_monitoring,
            "log_level": self.log_level,
        }
