"""
フォールバック設定

フォールバック戦略の設定を管理します。
"""

from dataclasses import dataclass
from enum import Enum


class FallbackStrategy(Enum):
    """フォールバック戦略"""

    CACHE = "cache"
    ALTERNATIVE_PROVIDER = "alternative_provider"
    OLD_DATA = "old_data"
    DEFAULT_VALUE = "default_value"
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class FallbackConfig:
    """フォールバック設定"""

    strategy: FallbackStrategy = FallbackStrategy.CACHE
    cache_ttl: float = 300.0  # 秒
    max_cache_size: int = 1000
    retry_attempts: int = 3
    retry_delay: float = 1.0  # 秒
    alternative_providers: list = None

    def __post_init__(self):
        if self.alternative_providers is None:
            self.alternative_providers = []
