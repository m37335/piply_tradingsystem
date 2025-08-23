**旧ファイル名**: `補足設計_Application層_20250809.md`  

# Application Layer 補足設計

**作成日**: 2025 年 8 月 9 日
**対象**: Application Layer の不足コンポーネント補完
**依存関係**: 基本 Application Layer 設計を拡張

## 1. Exception Handling (例外処理)

### 1.1 Application Layer 例外クラス

#### src/application/exceptions/base_exceptions.py
```python
"""アプリケーション層例外クラス"""
from abc import ABC
from typing import Dict, Any, Optional

class ApplicationException(Exception, ABC):
    """アプリケーション層基底例外"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        self.cause = cause

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で例外情報を返す"""
        return {
            'error_type': self.__class__.__name__,
            'error_code': self.error_code,
            'message': self.message,
            'details': self.details,
            'cause': str(self.cause) if self.cause else None
        }

class ValidationException(ApplicationException):
    """バリデーション例外"""

    def __init__(self, message: str, field_errors: Dict[str, str] = None):
        super().__init__(message, "VALIDATION_ERROR")
        self.field_errors = field_errors or {}
        self.details['field_errors'] = self.field_errors

class BusinessRuleException(ApplicationException):
    """ビジネスルール違反例外"""

    def __init__(self, message: str, rule_name: str = None):
        super().__init__(message, "BUSINESS_RULE_VIOLATION")
        if rule_name:
            self.details['rule_name'] = rule_name

class ResourceNotFoundException(ApplicationException):
    """リソース未発見例外"""

    def __init__(self, resource_type: str, resource_id: Any):
        message = f"{resource_type} with ID {resource_id} not found"
        super().__init__(message, "RESOURCE_NOT_FOUND")
        self.details.update({
            'resource_type': resource_type,
            'resource_id': str(resource_id)
        })

class ExternalServiceException(ApplicationException):
    """外部サービス例外"""

    def __init__(self, service_name: str, message: str, status_code: int = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.details.update({
            'service_name': service_name,
            'status_code': status_code
        })

class ConcurrencyException(ApplicationException):
    """並行処理例外"""

    def __init__(self, message: str = "Resource is being modified by another process"):
        super().__init__(message, "CONCURRENCY_CONFLICT")

class RateLimitException(ApplicationException):
    """レート制限例外"""

    def __init__(self, limit: int, window_seconds: int, retry_after: int = None):
        message = f"Rate limit exceeded: {limit} requests per {window_seconds} seconds"
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
        self.details.update({
            'limit': limit,
            'window_seconds': window_seconds,
            'retry_after': retry_after
        })

class ConfigurationException(ApplicationException):
    """設定例外"""

    def __init__(self, config_key: str, message: str = None):
        default_message = f"Invalid or missing configuration: {config_key}"
        super().__init__(message or default_message, "CONFIGURATION_ERROR")
        self.details['config_key'] = config_key
```

### 1.2 Exception Handler

#### src/application/exceptions/exception_handler.py
```python
"""例外ハンドラー"""
import logging
from typing import Dict, Any, Tuple
from .base_exceptions import (
    ApplicationException,
    ValidationException,
    BusinessRuleException,
    ResourceNotFoundException,
    ExternalServiceException,
    ConcurrencyException,
    RateLimitException,
    ConfigurationException
)

logger = logging.getLogger(__name__)

class ExceptionHandler:
    """アプリケーション例外ハンドラー"""

    def __init__(self):
        self.error_mappings = {
            ValidationException: (400, "BAD_REQUEST"),
            BusinessRuleException: (422, "UNPROCESSABLE_ENTITY"),
            ResourceNotFoundException: (404, "NOT_FOUND"),
            ExternalServiceException: (503, "SERVICE_UNAVAILABLE"),
            ConcurrencyException: (409, "CONFLICT"),
            RateLimitException: (429, "TOO_MANY_REQUESTS"),
            ConfigurationException: (500, "INTERNAL_SERVER_ERROR")
        }

    def handle_exception(self, exception: Exception) -> Tuple[Dict[str, Any], int]:
        """例外を処理してレスポンス形式に変換"""

        if isinstance(exception, ApplicationException):
            return self._handle_application_exception(exception)
        else:
            return self._handle_unknown_exception(exception)

    def _handle_application_exception(
        self,
        exception: ApplicationException
    ) -> Tuple[Dict[str, Any], int]:
        """アプリケーション例外の処理"""

        # ログレベル決定
        log_level = self._get_log_level(exception)

        # ログ出力
        if log_level == "ERROR":
            logger.error(
                f"Application exception: {exception.error_code}",
                extra={
                    'exception_type': type(exception).__name__,
                    'error_code': exception.error_code,
                    'message': exception.message,
                    'details': exception.details,
                    'cause': str(exception.cause) if exception.cause else None
                },
                exc_info=True
            )
        elif log_level == "WARNING":
            logger.warning(
                f"Application warning: {exception.error_code}",
                extra=exception.to_dict()
            )

        # HTTP ステータスコード決定
        status_code, status_text = self.error_mappings.get(
            type(exception),
            (500, "INTERNAL_SERVER_ERROR")
        )

        # レスポンス作成
        response = {
            'status': 'error',
            'error': {
                'code': exception.error_code,
                'message': exception.message,
                'type': type(exception).__name__
            }
        }

        # 詳細情報の追加（開発環境のみ）
        if self._should_include_details(exception):
            response['error']['details'] = exception.details

        return response, status_code

    def _handle_unknown_exception(self, exception: Exception) -> Tuple[Dict[str, Any], int]:
        """不明な例外の処理"""

        logger.error(
            f"Unhandled exception: {type(exception).__name__}",
            extra={
                'exception_type': type(exception).__name__,
                'message': str(exception)
            },
            exc_info=True
        )

        response = {
            'status': 'error',
            'error': {
                'code': 'INTERNAL_SERVER_ERROR',
                'message': 'An unexpected error occurred',
                'type': 'UnknownException'
            }
        }

        return response, 500

    def _get_log_level(self, exception: ApplicationException) -> str:
        """例外タイプに基づくログレベル決定"""

        warning_exceptions = (
            ValidationException,
            ResourceNotFoundException,
            RateLimitException
        )

        if isinstance(exception, warning_exceptions):
            return "WARNING"
        else:
            return "ERROR"

    def _should_include_details(self, exception: ApplicationException) -> bool:
        """詳細情報を含めるべきかの判定"""
        # 本番環境では機密情報を隠す
        import os
        is_development = os.getenv('ENVIRONMENT', 'development') == 'development'

        # バリデーションエラーは常に詳細を返す
        if isinstance(exception, ValidationException):
            return True

        # その他は開発環境のみ
        return is_development
```

## 2. DTOs (データ転送オブジェクト) 拡張

### 2.1 Analysis DTOs

#### src/application/dto/analysis_dto.py
```python
"""分析関連DTO"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

class SignalStrength(Enum):
    """シグナル強度"""
    VERY_WEAK = "very_weak"
    WEAK = "weak"
    MEDIUM = "medium"
    STRONG = "strong"
    VERY_STRONG = "very_strong"

class TrendDirection(Enum):
    """トレンド方向"""
    BULLISH = "bullish"
    BEARISH = "bearish"
    SIDEWAYS = "sideways"
    MIXED = "mixed"

@dataclass
class TechnicalIndicatorDTO:
    """テクニカル指標DTO"""
    id: Optional[int]
    currency_pair: str
    indicator_type: str
    timestamp: datetime
    value: Decimal
    signal_strength: SignalStrength
    parameters: Dict[str, Any]
    confidence: Optional[Decimal] = None
    metadata: Optional[Dict[str, Any]] = None

    @classmethod
    def from_entity(cls, entity) -> 'TechnicalIndicatorDTO':
        """エンティティから変換"""
        return cls(
            id=entity.id,
            currency_pair=entity.currency_pair,
            indicator_type=entity.indicator_type,
            timestamp=entity.timestamp,
            value=entity.value,
            signal_strength=SignalStrength(entity.get_signal_strength()),
            parameters=entity.parameters,
            confidence=entity.confidence,
            metadata=entity.metadata
        )

    def to_dict(self) -> Dict[str, Any]:
        """辞書変換"""
        return {
            'id': self.id,
            'currency_pair': self.currency_pair,
            'indicator_type': self.indicator_type,
            'timestamp': self.timestamp.isoformat(),
            'value': str(self.value),
            'signal_strength': self.signal_strength.value,
            'parameters': self.parameters,
            'confidence': str(self.confidence) if self.confidence else None,
            'metadata': self.metadata
        }

@dataclass
class MarketAnalysisDTO:
    """市場分析DTO"""
    currency_pair: str
    analysis_timestamp: datetime
    trend_direction: TrendDirection
    trend_strength: SignalStrength
    support_levels: List[Decimal]
    resistance_levels: List[Decimal]
    volatility: Decimal
    volume_trend: Optional[str] = None
    key_events: Optional[List[str]] = None
    recommendation: Optional[str] = None
    confidence_score: Optional[Decimal] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書変換"""
        return {
            'currency_pair': self.currency_pair,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'trend_direction': self.trend_direction.value,
            'trend_strength': self.trend_strength.value,
            'support_levels': [str(level) for level in self.support_levels],
            'resistance_levels': [str(level) for level in self.resistance_levels],
            'volatility': str(self.volatility),
            'volume_trend': self.volume_trend,
            'key_events': self.key_events,
            'recommendation': self.recommendation,
            'confidence_score': str(self.confidence_score) if self.confidence_score else None
        }

@dataclass
class AIAnalysisRequestDTO:
    """AI分析リクエストDTO"""
    currency_pairs: List[str]
    analysis_type: str  # "trend", "signal", "comprehensive"
    timeframe: str      # "1h", "4h", "1d"
    include_fundamentals: bool = False
    custom_parameters: Optional[Dict[str, Any]] = None

    def validate(self):
        """バリデーション"""
        if not self.currency_pairs:
            raise ValueError("Currency pairs are required")

        if len(self.currency_pairs) > 10:
            raise ValueError("Too many currency pairs (max: 10)")

        valid_types = ["trend", "signal", "comprehensive", "custom"]
        if self.analysis_type not in valid_types:
            raise ValueError(f"Invalid analysis type: {self.analysis_type}")

        valid_timeframes = ["1m", "5m", "15m", "1h", "4h", "1d", "1w"]
        if self.timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {self.timeframe}")

@dataclass
class AIAnalysisResponseDTO:
    """AI分析レスポンスDTO"""
    request_id: str
    analysis_timestamp: datetime
    currency_pairs: List[str]
    market_summary: str
    technical_analysis: str
    signals: List[Dict[str, Any]]
    confidence_score: Decimal
    processing_time_ms: int
    model_version: str
    recommendations: Optional[List[Dict[str, Any]]] = None
    risk_assessment: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """辞書変換"""
        return {
            'request_id': self.request_id,
            'analysis_timestamp': self.analysis_timestamp.isoformat(),
            'currency_pairs': self.currency_pairs,
            'market_summary': self.market_summary,
            'technical_analysis': self.technical_analysis,
            'signals': self.signals,
            'confidence_score': str(self.confidence_score),
            'processing_time_ms': self.processing_time_ms,
            'model_version': self.model_version,
            'recommendations': self.recommendations,
            'risk_assessment': self.risk_assessment
        }
```

### 2.2 Alert DTOs

#### src/application/dto/alert_dto.py
```python
"""アラート関連DTO"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from enum import Enum

class AlertType(Enum):
    """アラートタイプ"""
    PRICE_THRESHOLD = "price_threshold"
    PRICE_CHANGE = "price_change"
    TECHNICAL_SIGNAL = "technical_signal"
    AI_RECOMMENDATION = "ai_recommendation"
    MARKET_EVENT = "market_event"

class AlertStatus(Enum):
    """アラート状態"""
    ACTIVE = "active"
    TRIGGERED = "triggered"
    PAUSED = "paused"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class AlertPriority(Enum):
    """アラート優先度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class CreateAlertDTO:
    """アラート作成DTO"""
    currency_pair: str
    alert_type: AlertType
    title: str
    description: str
    conditions: Dict[str, Any]
    notification_channels: List[str]
    priority: AlertPriority = AlertPriority.MEDIUM
    expires_at: Optional[datetime] = None
    repeat_interval: Optional[int] = None  # seconds

    def validate(self):
        """バリデーション"""
        if not self.currency_pair or len(self.currency_pair) != 6:
            raise ValueError("Invalid currency pair")

        if not self.title or len(self.title.strip()) == 0:
            raise ValueError("Title is required")

        if not self.conditions:
            raise ValueError("Conditions are required")

        if not self.notification_channels:
            raise ValueError("At least one notification channel is required")

        valid_channels = ["discord", "email", "webhook", "sms"]
        for channel in self.notification_channels:
            if channel not in valid_channels:
                raise ValueError(f"Invalid notification channel: {channel}")

@dataclass
class AlertDTO:
    """アラートDTO"""
    id: Optional[int]
    currency_pair: str
    alert_type: AlertType
    status: AlertStatus
    priority: AlertPriority
    title: str
    description: str
    conditions: Dict[str, Any]
    notification_channels: List[str]
    created_at: datetime
    triggered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    trigger_count: int = 0
    last_checked: Optional[datetime] = None

    @classmethod
    def from_entity(cls, entity) -> 'AlertDTO':
        """エンティティから変換"""
        return cls(
            id=entity.id,
            currency_pair=entity.currency_pair,
            alert_type=AlertType(entity.alert_type),
            status=AlertStatus(entity.status),
            priority=AlertPriority(entity.priority),
            title=entity.title,
            description=entity.description,
            conditions=entity.conditions,
            notification_channels=entity.notification_channels,
            created_at=entity.created_at,
            triggered_at=entity.triggered_at,
            expires_at=entity.expires_at,
            trigger_count=entity.trigger_count,
            last_checked=entity.last_checked
        )

    def to_dict(self) -> Dict[str, Any]:
        """辞書変換"""
        return {
            'id': self.id,
            'currency_pair': self.currency_pair,
            'alert_type': self.alert_type.value,
            'status': self.status.value,
            'priority': self.priority.value,
            'title': self.title,
            'description': self.description,
            'conditions': self.conditions,
            'notification_channels': self.notification_channels,
            'created_at': self.created_at.isoformat(),
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'trigger_count': self.trigger_count,
            'last_checked': self.last_checked.isoformat() if self.last_checked else None
        }

@dataclass
class AlertNotificationDTO:
    """アラート通知DTO"""
    alert_id: int
    currency_pair: str
    alert_title: str
    message: str
    priority: AlertPriority
    triggered_at: datetime
    current_price: Optional[Decimal] = None
    trigger_conditions: Optional[Dict[str, Any]] = None

    def to_discord_embed(self) -> Dict[str, Any]:
        """Discord Embed形式に変換"""
        color_map = {
            AlertPriority.LOW: 0x95a5a6,      # Gray
            AlertPriority.MEDIUM: 0x3498db,   # Blue
            AlertPriority.HIGH: 0xf39c12,     # Orange
            AlertPriority.CRITICAL: 0xe74c3c  # Red
        }

        embed = {
            "title": f"🚨 {self.alert_title}",
            "description": self.message,
            "color": color_map.get(self.priority, 0x3498db),
            "timestamp": self.triggered_at.isoformat(),
            "fields": [
                {
                    "name": "通貨ペア",
                    "value": self.currency_pair,
                    "inline": True
                },
                {
                    "name": "優先度",
                    "value": self.priority.value.upper(),
                    "inline": True
                }
            ]
        }

        if self.current_price:
            embed["fields"].append({
                "name": "現在価格",
                "value": str(self.current_price),
                "inline": True
            })

        return embed
```

## 3. Service Layer

### 3.1 Business Logic Services

#### src/application/services/market_analysis_service.py
```python
"""市場分析サービス"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
from ..dto.analysis_dto import MarketAnalysisDTO, TrendDirection, SignalStrength
from ..dto.rate_dto import RateDTO
from ...domain.entities.exchange_rate import ExchangeRate
from ...domain.services.analysis_service import AnalysisService
import numpy as np
import pandas as pd

class MarketAnalysisService:
    """市場分析ビジネスロジック"""

    def __init__(self, analysis_service: AnalysisService):
        self.analysis_service = analysis_service

    async def analyze_market_conditions(
        self,
        currency_pair: str,
        rates: List[ExchangeRate],
        timeframe: str = "1h"
    ) -> MarketAnalysisDTO:
        """総合市場分析"""

        if not rates or len(rates) < 20:
            raise ValueError("Insufficient data for analysis")

        # トレンド分析
        trend_direction, trend_strength = self._analyze_trend(rates)

        # サポート・レジスタンスレベル
        levels = self.analysis_service.identify_support_resistance_levels(rates)

        # ボラティリティ計算
        volatility = self.analysis_service.calculate_volatility(rates, period=20)

        # ボリューム分析
        volume_trend = self._analyze_volume_trend(rates)

        # 重要なイベント検出
        key_events = self._detect_key_events(rates)

        # 推奨事項生成
        recommendation = self._generate_recommendation(
            trend_direction, trend_strength, volatility, rates[-1]
        )

        # 信頼度スコア計算
        confidence_score = self._calculate_confidence_score(
            rates, trend_strength, volatility
        )

        return MarketAnalysisDTO(
            currency_pair=currency_pair,
            analysis_timestamp=datetime.utcnow(),
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            support_levels=levels["support"],
            resistance_levels=levels["resistance"],
            volatility=volatility or Decimal('0'),
            volume_trend=volume_trend,
            key_events=key_events,
            recommendation=recommendation,
            confidence_score=confidence_score
        )

    def _analyze_trend(self, rates: List[ExchangeRate]) -> tuple[TrendDirection, SignalStrength]:
        """トレンド分析"""
        if len(rates) < 10:
            return TrendDirection.SIDEWAYS, SignalStrength.WEAK

        # 短期・長期移動平均を計算
        short_window = 5
        long_window = 20

        prices = [float(rate.close_price) for rate in rates]

        if len(prices) < long_window:
            return TrendDirection.SIDEWAYS, SignalStrength.WEAK

        short_ma = np.mean(prices[-short_window:])
        long_ma = np.mean(prices[-long_window:])

        # トレンド方向判定
        if short_ma > long_ma * 1.01:  # 1%以上の差
            direction = TrendDirection.BULLISH
        elif short_ma < long_ma * 0.99:  # 1%以上の差
            direction = TrendDirection.BEARISH
        else:
            direction = TrendDirection.SIDEWAYS

        # トレンド強度判定
        price_changes = [
            (prices[i] - prices[i-1]) / prices[i-1]
            for i in range(1, len(prices))
        ]

        recent_changes = price_changes[-5:]
        avg_change = abs(np.mean(recent_changes))

        if avg_change > 0.02:  # 2%以上
            strength = SignalStrength.STRONG
        elif avg_change > 0.01:  # 1%以上
            strength = SignalStrength.MEDIUM
        else:
            strength = SignalStrength.WEAK

        return direction, strength

    def _analyze_volume_trend(self, rates: List[ExchangeRate]) -> Optional[str]:
        """ボリューム分析"""
        volumes = [rate.volume for rate in rates if rate.volume is not None]

        if len(volumes) < 5:
            return None

        recent_avg = np.mean(volumes[-5:])
        historical_avg = np.mean(volumes[:-5]) if len(volumes) > 5 else recent_avg

        if recent_avg > historical_avg * 1.2:
            return "increasing"
        elif recent_avg < historical_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _detect_key_events(self, rates: List[ExchangeRate]) -> List[str]:
        """重要イベント検出"""
        events = []

        if len(rates) < 5:
            return events

        # 急激な価格変動検出
        for i in range(1, len(rates)):
            current_price = float(rates[i].close_price)
            previous_price = float(rates[i-1].close_price)
            change_percent = abs((current_price - previous_price) / previous_price)

            if change_percent > 0.03:  # 3%以上の変動
                direction = "上昇" if current_price > previous_price else "下落"
                events.append(f"急激な{direction}: {change_percent:.2%}")

        # ギャップ検出
        for i in range(1, len(rates)):
            current_open = float(rates[i].open_price)
            previous_close = float(rates[i-1].close_price)
            gap_percent = abs((current_open - previous_close) / previous_close)

            if gap_percent > 0.01:  # 1%以上のギャップ
                gap_type = "上方" if current_open > previous_close else "下方"
                events.append(f"{gap_type}ギャップ: {gap_percent:.2%}")

        return events[-3:]  # 最新3つのイベント

    def _generate_recommendation(
        self,
        trend_direction: TrendDirection,
        trend_strength: SignalStrength,
        volatility: Optional[Decimal],
        latest_rate: ExchangeRate
    ) -> str:
        """推奨事項生成"""

        vol_level = "高" if volatility and volatility > Decimal('0.02') else "低"

        if trend_direction == TrendDirection.BULLISH:
            if trend_strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                return f"強い上昇トレンド継続の可能性。ボラティリティ{vol_level}。押し目買いを検討。"
            else:
                return f"弱い上昇傾向。ボラティリティ{vol_level}。慎重な買いポジション検討。"

        elif trend_direction == TrendDirection.BEARISH:
            if trend_strength in [SignalStrength.STRONG, SignalStrength.VERY_STRONG]:
                return f"強い下降トレンド継続の可能性。ボラティリティ{vol_level}。戻り売りを検討。"
            else:
                return f"弱い下降傾向。ボラティリティ{vol_level}。慎重な売りポジション検討。"

        else:
            return f"横ばい相場。ボラティリティ{vol_level}。レンジ取引または様子見推奨。"

    def _calculate_confidence_score(
        self,
        rates: List[ExchangeRate],
        trend_strength: SignalStrength,
        volatility: Optional[Decimal]
    ) -> Decimal:
        """信頼度スコア計算"""

        # 基本スコア（データ量による）
        data_score = min(len(rates) / 50, 1.0)  # 50以上で満点

        # トレンド強度スコア
        strength_map = {
            SignalStrength.VERY_WEAK: 0.1,
            SignalStrength.WEAK: 0.3,
            SignalStrength.MEDIUM: 0.6,
            SignalStrength.STRONG: 0.8,
            SignalStrength.VERY_STRONG: 1.0
        }
        trend_score = strength_map.get(trend_strength, 0.5)

        # ボラティリティスコア（適度なボラティリティが良い）
        if volatility:
            vol_float = float(volatility)
            if 0.005 <= vol_float <= 0.02:  # 適度なボラティリティ
                vol_score = 1.0
            elif vol_float < 0.005:  # 低すぎる
                vol_score = 0.6
            else:  # 高すぎる
                vol_score = 0.4
        else:
            vol_score = 0.5

        # 重み付き平均
        final_score = (data_score * 0.2 + trend_score * 0.5 + vol_score * 0.3)

        return Decimal(str(round(final_score, 3)))

    async def compare_currency_pairs(
        self,
        pairs_data: Dict[str, List[ExchangeRate]]
    ) -> Dict[str, Any]:
        """通貨ペア比較分析"""

        comparisons = {}

        for pair, rates in pairs_data.items():
            if len(rates) >= 20:
                analysis = await self.analyze_market_conditions(pair, rates)
                comparisons[pair] = {
                    'trend_direction': analysis.trend_direction.value,
                    'trend_strength': analysis.trend_strength.value,
                    'volatility': float(analysis.volatility),
                    'confidence_score': float(analysis.confidence_score),
                    'recommendation': analysis.recommendation
                }

        # ランキング作成
        rankings = {
            'strongest_bullish': self._rank_by_criteria(comparisons, 'bullish_strength'),
            'strongest_bearish': self._rank_by_criteria(comparisons, 'bearish_strength'),
            'highest_volatility': self._rank_by_criteria(comparisons, 'volatility'),
            'highest_confidence': self._rank_by_criteria(comparisons, 'confidence_score')
        }

        return {
            'individual_analysis': comparisons,
            'rankings': rankings,
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

    def _rank_by_criteria(self, comparisons: Dict[str, Any], criteria: str) -> List[Dict[str, Any]]:
        """条件別ランキング"""

        ranked_pairs = []

        for pair, data in comparisons.items():
            if criteria == 'bullish_strength':
                score = self._calculate_bullish_score(data)
            elif criteria == 'bearish_strength':
                score = self._calculate_bearish_score(data)
            elif criteria == 'volatility':
                score = data['volatility']
            elif criteria == 'confidence_score':
                score = data['confidence_score']
            else:
                score = 0

            ranked_pairs.append({
                'currency_pair': pair,
                'score': score,
                'trend_direction': data['trend_direction'],
                'trend_strength': data['trend_strength']
            })

        return sorted(ranked_pairs, key=lambda x: x['score'], reverse=True)

    def _calculate_bullish_score(self, data: Dict[str, Any]) -> float:
        """強気スコア計算"""
        if data['trend_direction'] != 'bullish':
            return 0

        strength_scores = {
            'very_weak': 0.1, 'weak': 0.3, 'medium': 0.6,
            'strong': 0.8, 'very_strong': 1.0
        }

        return strength_scores.get(data['trend_strength'], 0) * data['confidence_score']

    def _calculate_bearish_score(self, data: Dict[str, Any]) -> float:
        """弱気スコア計算"""
        if data['trend_direction'] != 'bearish':
            return 0

        strength_scores = {
            'very_weak': 0.1, 'weak': 0.3, 'medium': 0.6,
            'strong': 0.8, 'very_strong': 1.0
        }

        return strength_scores.get(data['trend_strength'], 0) * data['confidence_score']
```

この補足設計により、Application Layer がより堅牢で実用的なものになりました。例外処理、詳細なDTO、ビジネスロジックサービスが追加され、実際の開発で必要なコンポーネントが揃いました。
