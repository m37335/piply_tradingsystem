"""
レート制限設定

レート制限管理に関する設定を管理します。
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum


class RateLimitStrategy(Enum):
    """レート制限戦略"""
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"


class LoadBalancingStrategy(Enum):
    """ロードバランシング戦略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    HEALTH_BASED = "health_based"
    RANDOM = "random"
    LEAST_RESPONSE_TIME = "least_response_time"


class FallbackStrategy(Enum):
    """フォールバック戦略"""
    CACHE = "cache"
    ALTERNATIVE_PROVIDER = "alternative_provider"
    STALE_DATA = "stale_data"
    DEFAULT_VALUE = "default_value"
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class RateLimitConfig:
    """レート制限設定"""
    strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE
    requests_per_second: float = 10.0
    burst_capacity: int = 50
    window_size_seconds: int = 60
    adaptive_enabled: bool = True
    min_requests_per_second: float = 0.1
    max_requests_per_second: float = 100.0
    adaptation_factor: float = 0.1
    
    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """環境変数から設定を読み込み"""
        strategy_str = os.getenv("RATE_LIMIT_STRATEGY", "adaptive")
        strategy = RateLimitStrategy(strategy_str)
        
        return cls(
            strategy=strategy,
            requests_per_second=float(os.getenv("RATE_LIMIT_RPS", "10.0")),
            burst_capacity=int(os.getenv("RATE_LIMIT_BURST", "50")),
            window_size_seconds=int(os.getenv("RATE_LIMIT_WINDOW", "60")),
            adaptive_enabled=os.getenv("RATE_LIMIT_ADAPTIVE", "true").lower() == "true",
            min_requests_per_second=float(os.getenv("RATE_LIMIT_MIN_RPS", "0.1")),
            max_requests_per_second=float(os.getenv("RATE_LIMIT_MAX_RPS", "100.0")),
            adaptation_factor=float(os.getenv("RATE_LIMIT_ADAPTATION_FACTOR", "0.1"))
        )


@dataclass
class CircuitBreakerConfig:
    """サーキットブレーカー設定"""
    failure_threshold: int = 5
    recovery_timeout: int = 60
    success_threshold: int = 3
    timeout: Optional[int] = None
    monitoring_enabled: bool = True
    metrics_window_size: int = 100
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> "CircuitBreakerConfig":
        """環境変数から設定を読み込み"""
        return cls(
            failure_threshold=int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")),
            recovery_timeout=int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60")),
            success_threshold=int(os.getenv("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "3")),
            timeout=int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "0")) or None,
            monitoring_enabled=os.getenv("CIRCUIT_BREAKER_MONITORING", "true").lower() == "true",
            metrics_window_size=int(os.getenv("CIRCUIT_BREAKER_METRICS_WINDOW", "100")),
            health_check_interval=int(os.getenv("CIRCUIT_BREAKER_HEALTH_CHECK_INTERVAL", "30"))
        )


@dataclass
class LoadBalancerConfig:
    """ロードバランサー設定"""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.HEALTH_BASED
    health_check_interval: int = 30
    health_check_timeout: int = 5
    failure_threshold: int = 3
    recovery_threshold: int = 2
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    @classmethod
    def from_env(cls) -> "LoadBalancerConfig":
        """環境変数から設定を読み込み"""
        strategy_str = os.getenv("LOAD_BALANCER_STRATEGY", "health_based")
        strategy = LoadBalancingStrategy(strategy_str)
        
        return cls(
            strategy=strategy,
            health_check_interval=int(os.getenv("LOAD_BALANCER_HEALTH_CHECK_INTERVAL", "30")),
            health_check_timeout=int(os.getenv("LOAD_BALANCER_HEALTH_CHECK_TIMEOUT", "5")),
            failure_threshold=int(os.getenv("LOAD_BALANCER_FAILURE_THRESHOLD", "3")),
            recovery_threshold=int(os.getenv("LOAD_BALANCER_RECOVERY_THRESHOLD", "2")),
            max_retries=int(os.getenv("LOAD_BALANCER_MAX_RETRIES", "3")),
            retry_delay_seconds=float(os.getenv("LOAD_BALANCER_RETRY_DELAY", "1.0"))
        )


@dataclass
class FallbackConfig:
    """フォールバック設定"""
    strategies: List[FallbackStrategy]
    cache_ttl_seconds: int = 300
    stale_data_threshold_seconds: int = 3600
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    default_values: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_values is None:
            self.default_values = {}
    
    @classmethod
    def from_env(cls) -> "FallbackConfig":
        """環境変数から設定を読み込み"""
        strategies_str = os.getenv("FALLBACK_STRATEGIES", "cache,alternative_provider,stale_data")
        strategies = [FallbackStrategy(s.strip()) for s in strategies_str.split(",")]
        
        return cls(
            strategies=strategies,
            cache_ttl_seconds=int(os.getenv("FALLBACK_CACHE_TTL", "300")),
            stale_data_threshold_seconds=int(os.getenv("FALLBACK_STALE_DATA_THRESHOLD", "3600")),
            max_retry_attempts=int(os.getenv("FALLBACK_MAX_RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=float(os.getenv("FALLBACK_RETRY_DELAY", "1.0"))
        )


@dataclass
class RateLimitingSettings:
    """レート制限設定"""
    rate_limit: RateLimitConfig
    circuit_breaker: CircuitBreakerConfig
    load_balancer: LoadBalancerConfig
    fallback: FallbackConfig
    enable_monitoring: bool = True
    log_level: str = "INFO"
    
    @classmethod
    def from_env(cls) -> "RateLimitingSettings":
        """環境変数から設定を読み込み"""
        return cls(
            rate_limit=RateLimitConfig.from_env(),
            circuit_breaker=CircuitBreakerConfig.from_env(),
            load_balancer=LoadBalancerConfig.from_env(),
            fallback=FallbackConfig.from_env(),
            enable_monitoring=os.getenv("RATE_LIMITING_MONITORING", "true").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書に変換"""
        return {
            "rate_limit": {
                "strategy": self.rate_limit.strategy.value,
                "requests_per_second": self.rate_limit.requests_per_second,
                "burst_capacity": self.rate_limit.burst_capacity,
                "window_size_seconds": self.rate_limit.window_size_seconds,
                "adaptive_enabled": self.rate_limit.adaptive_enabled,
                "min_requests_per_second": self.rate_limit.min_requests_per_second,
                "max_requests_per_second": self.rate_limit.max_requests_per_second,
                "adaptation_factor": self.rate_limit.adaptation_factor
            },
            "circuit_breaker": {
                "failure_threshold": self.circuit_breaker.failure_threshold,
                "recovery_timeout": self.circuit_breaker.recovery_timeout,
                "success_threshold": self.circuit_breaker.success_threshold,
                "timeout": self.circuit_breaker.timeout,
                "monitoring_enabled": self.circuit_breaker.monitoring_enabled,
                "metrics_window_size": self.circuit_breaker.metrics_window_size,
                "health_check_interval": self.circuit_breaker.health_check_interval
            },
            "load_balancer": {
                "strategy": self.load_balancer.strategy.value,
                "health_check_interval": self.load_balancer.health_check_interval,
                "health_check_timeout": self.load_balancer.health_check_timeout,
                "failure_threshold": self.load_balancer.failure_threshold,
                "recovery_threshold": self.load_balancer.recovery_threshold,
                "max_retries": self.load_balancer.max_retries,
                "retry_delay_seconds": self.load_balancer.retry_delay_seconds
            },
            "fallback": {
                "strategies": [s.value for s in self.fallback.strategies],
                "cache_ttl_seconds": self.fallback.cache_ttl_seconds,
                "stale_data_threshold_seconds": self.fallback.stale_data_threshold_seconds,
                "max_retry_attempts": self.fallback.max_retry_attempts,
                "retry_delay_seconds": self.fallback.retry_delay_seconds
            },
            "enable_monitoring": self.enable_monitoring,
            "log_level": self.log_level
        }
