"""
レート制限設定

レート制限の設定を管理します。
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class RateLimitAlgorithm(Enum):
    """レート制限アルゴリズム"""

    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimitConfig:
    """レート制限設定"""

    max_requests: int
    window_size: float  # 秒
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    burst_capacity: Optional[int] = None
    refill_rate: Optional[float] = None
