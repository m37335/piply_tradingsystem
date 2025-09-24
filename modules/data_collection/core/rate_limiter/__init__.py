"""
レート制限管理システム

Yahoo Finance APIの制限に対応するためのレート制限機能を提供します。
"""

from .adaptive_rate_limiter import AdaptiveRateLimiter
from .circuit_breaker import CircuitBreaker, CircuitState
from .fallback_strategy import (
    AlternativeProviderFallbackStrategy,
    CacheFallbackStrategy,
    DefaultValueFallbackStrategy,
    FallbackStrategy,
    OldDataFallbackStrategy,
    RetryFallbackStrategy,
)
from .leaky_bucket import LeakyBucket
from .rate_limiter import RateLimiter, RateLimitManager
from .sliding_window import SlidingWindow
from .token_bucket import TokenBucket

__all__ = [
    "RateLimiter",
    "RateLimitManager",
    "TokenBucket",
    "LeakyBucket",
    "SlidingWindow",
    "AdaptiveRateLimiter",
    "CircuitBreaker",
    "CircuitState",
    "FallbackStrategy",
    "CacheFallbackStrategy",
    "AlternativeProviderFallbackStrategy",
    "OldDataFallbackStrategy",
    "DefaultValueFallbackStrategy",
    "RetryFallbackStrategy",
]
