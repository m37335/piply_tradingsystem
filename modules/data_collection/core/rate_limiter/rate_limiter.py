"""
レート制限管理のメインクラス

Yahoo Finance APIの制限に対応するためのレート制限機能を提供します。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional


class RateLimitStrategy(Enum):
    """レート制限戦略の種類"""

    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class RateLimitConfig:
    """レート制限設定"""

    strategy: RateLimitStrategy
    max_requests: int
    time_window: int  # 秒
    burst_capacity: Optional[int] = None
    refill_rate: Optional[float] = None  # リクエスト/秒


class RateLimiter(ABC):
    """レート制限の抽象基底クラス"""

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._lock = asyncio.Lock()

    @abstractmethod
    async def acquire(self, tokens: int = 1) -> bool:
        """トークンを取得（リクエスト許可）"""
        pass

    @abstractmethod
    async def wait_for_availability(self, tokens: int = 1) -> None:
        """利用可能になるまで待機"""
        pass

    @abstractmethod
    def get_remaining_tokens(self) -> int:
        """残りトークン数を取得"""
        pass

    @abstractmethod
    def get_reset_time(self) -> float:
        """リセット時間を取得"""
        pass


class YahooFinanceRateLimiter(RateLimiter):
    """Yahoo Finance API専用のレート制限管理"""

    def __init__(self):
        # Yahoo Finance APIの制限: 2000リクエスト/時間
        config = RateLimitConfig(
            strategy=RateLimitStrategy.TOKEN_BUCKET,
            max_requests=2000,
            time_window=3600,  # 1時間
            burst_capacity=100,  # バースト容量
            refill_rate=2000 / 3600,  # 約0.56リクエスト/秒
        )
        super().__init__(config)
        self._tokens = config.burst_capacity
        self._last_refill = time.time()

    async def acquire(self, tokens: int = 1) -> bool:
        """トークンを取得（リクエスト許可）"""
        async with self._lock:
            await self._refill_tokens()

            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    async def wait_for_availability(self, tokens: int = 1) -> None:
        """利用可能になるまで待機"""
        while not await self.acquire(tokens):
            # 次のリフィルまで待機
            next_refill = self._last_refill + (1 / self.config.refill_rate)
            wait_time = max(0, next_refill - time.time())
            await asyncio.sleep(wait_time)

    def get_remaining_tokens(self) -> int:
        """残りトークン数を取得"""
        return int(self._tokens)

    def get_reset_time(self) -> float:
        """リセット時間を取得"""
        return self._last_refill + (1 / self.config.refill_rate)

    async def _refill_tokens(self) -> None:
        """トークンをリフィル"""
        now = time.time()
        time_passed = now - self._last_refill

        # 経過時間に基づいてトークンを追加
        tokens_to_add = time_passed * self.config.refill_rate
        self._tokens = min(self.config.burst_capacity, self._tokens + tokens_to_add)
        self._last_refill = now


class RateLimitManager:
    """複数のレート制限器を管理"""

    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        self._default_limiter = YahooFinanceRateLimiter()

    def add_limiter(self, name: str, limiter: RateLimiter) -> None:
        """レート制限器を追加"""
        self._limiters[name] = limiter

    def get_limiter(self, name: str) -> RateLimiter:
        """レート制限器を取得"""
        return self._limiters.get(name, self._default_limiter)

    async def acquire_all(self, tokens: int = 1) -> bool:
        """すべてのレート制限器からトークンを取得"""
        for limiter in self._limiters.values():
            if not await limiter.acquire(tokens):
                return False
        return True

    async def wait_for_all_availability(self, tokens: int = 1) -> None:
        """すべてのレート制限器が利用可能になるまで待機"""
        tasks = [
            limiter.wait_for_availability(tokens) for limiter in self._limiters.values()
        ]
        await asyncio.gather(*tasks)


# 後方互換性のためのエクスポート
from .rate_limit_manager import RateLimitManager
