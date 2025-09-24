"""
高度なレート制限器

複数のレート制限アルゴリズムを組み合わせた高度なレート制限機能を提供します。
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import math

logger = logging.getLogger(__name__)


class RateLimitAlgorithm(Enum):
    """レート制限アルゴリズム"""
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    ADAPTIVE = "adaptive"


class RateLimitTier(Enum):
    """レート制限ティア"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class RateLimitConfig:
    """レート制限設定"""
    algorithm: RateLimitAlgorithm
    requests_per_second: float
    burst_capacity: int
    window_size_seconds: int = 60
    tier: RateLimitTier = RateLimitTier.FREE
    
    # 適応的制限の設定
    adaptive_enabled: bool = False
    min_requests_per_second: float = 0.1
    max_requests_per_second: float = 100.0
    adaptation_factor: float = 0.1
    
    # 分散制限の設定
    distributed_enabled: bool = False
    node_count: int = 1
    sync_interval_seconds: int = 10


@dataclass
class RateLimitStats:
    """レート制限統計"""
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    current_tokens: float = 0.0
    last_refill_time: float = 0.0
    window_start_time: float = 0.0
    window_request_count: int = 0


class AdvancedRateLimiter:
    """高度なレート制限器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.stats = RateLimitStats()
        self._lock = asyncio.Lock()
        
        # アルゴリズム固有の状態
        self._tokens = config.burst_capacity
        self._last_refill = time.time()
        self._window_requests: List[float] = []
        self._circuit_breaker_state = "closed"  # closed, open, half_open
        self._circuit_breaker_failures = 0
        self._circuit_breaker_last_failure = 0.0
        
        # 適応的制限の状態
        self._current_rate = config.requests_per_second
        self._success_count = 0
        self._failure_count = 0
        self._last_adaptation = time.time()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """トークンを取得（リクエスト許可）"""
        async with self._lock:
            # サーキットブレーカーチェック
            if not await self._check_circuit_breaker():
                return False
            
            # レート制限チェック
            if not await self._check_rate_limit(tokens):
                self.stats.blocked_requests += 1
                return False
            
            # トークンを消費
            await self._consume_tokens(tokens)
            self.stats.allowed_requests += 1
            self.stats.total_requests += 1
            
            # サーキットブレーカーの成功を記録
            await self._record_success()
            
            return True
    
    async def wait_for_availability(self, tokens: int = 1) -> None:
        """利用可能になるまで待機"""
        while not await self.acquire(tokens):
            # 次の利用可能時間を計算
            wait_time = await self._calculate_wait_time(tokens)
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            else:
                await asyncio.sleep(0.1)  # 最小待機時間
    
    async def _check_circuit_breaker(self) -> bool:
        """サーキットブレーカーの状態をチェック"""
        current_time = time.time()
        
        if self._circuit_breaker_state == "open":
            # オープン状態：一定時間後にハーフオープンに移行
            if current_time - self._circuit_breaker_last_failure > 60:  # 60秒
                self._circuit_breaker_state = "half_open"
                logger.info("Circuit breaker moved to half-open state")
                return True
            return False
        
        elif self._circuit_breaker_state == "half_open":
            # ハーフオープン状態：テストリクエストを許可
            return True
        
        else:  # closed
            # クローズ状態：通常通り許可
            return True
    
    async def _check_rate_limit(self, tokens: int) -> bool:
        """レート制限をチェック"""
        current_time = time.time()
        
        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            return await self._check_token_bucket(tokens, current_time)
        elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            return await self._check_leaky_bucket(tokens, current_time)
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return await self._check_sliding_window(tokens, current_time)
        elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return await self._check_fixed_window(tokens, current_time)
        elif self.config.algorithm == RateLimitAlgorithm.ADAPTIVE:
            return await self._check_adaptive(tokens, current_time)
        else:
            return False
    
    async def _check_token_bucket(self, tokens: int, current_time: float) -> bool:
        """トークンバケットアルゴリズム"""
        # トークンをリフィル
        time_passed = current_time - self._last_refill
        tokens_to_add = time_passed * self.config.requests_per_second
        self._tokens = min(self.config.burst_capacity, self._tokens + tokens_to_add)
        self._last_refill = current_time
        
        # トークンが十分かチェック
        return self._tokens >= tokens
    
    async def _check_leaky_bucket(self, tokens: int, current_time: float) -> bool:
        """リーキーバケットアルゴリズム"""
        # リーク処理
        time_passed = current_time - self._last_refill
        leaked_tokens = time_passed * self.config.requests_per_second
        self._tokens = max(0, self._tokens - leaked_tokens)
        self._last_refill = current_time
        
        # バケットに空きがあるかチェック
        return self._tokens + tokens <= self.config.burst_capacity
    
    async def _check_sliding_window(self, tokens: int, current_time: float) -> bool:
        """スライディングウィンドウアルゴリズム"""
        window_start = current_time - self.config.window_size_seconds
        
        # 古いリクエストを削除
        self._window_requests = [req_time for req_time in self._window_requests if req_time > window_start]
        
        # ウィンドウ内のリクエスト数が制限以下かチェック
        max_requests = self.config.requests_per_second * self.config.window_size_seconds
        return len(self._window_requests) + tokens <= max_requests
    
    async def _check_fixed_window(self, tokens: int, current_time: float) -> bool:
        """固定ウィンドウアルゴリズム"""
        window_start = int(current_time / self.config.window_size_seconds) * self.config.window_size_seconds
        
        # 新しいウィンドウの場合、カウントをリセット
        if window_start != self.stats.window_start_time:
            self.stats.window_start_time = window_start
            self.stats.window_request_count = 0
        
        # ウィンドウ内のリクエスト数が制限以下かチェック
        max_requests = self.config.requests_per_second * self.config.window_size_seconds
        return self.stats.window_request_count + tokens <= max_requests
    
    async def _check_adaptive(self, tokens: int, current_time: float) -> bool:
        """適応的レート制限アルゴリズム"""
        # 適応的レート調整
        if self.config.adaptive_enabled:
            await self._adapt_rate(current_time)
        
        # 現在のレートでトークンバケットをチェック
        return await self._check_token_bucket(tokens, current_time)
    
    async def _adapt_rate(self, current_time: float) -> None:
        """レートを適応的に調整"""
        if current_time - self._last_adaptation < 10:  # 10秒間隔で調整
            return
        
        total_requests = self._success_count + self._failure_count
        if total_requests < 10:  # 十分なデータがない場合は調整しない
            return
        
        success_rate = self._success_count / total_requests
        
        if success_rate > 0.95:  # 成功率が高い場合、レートを上げる
            self._current_rate = min(
                self.config.max_requests_per_second,
                self._current_rate * (1 + self.config.adaptation_factor)
            )
        elif success_rate < 0.8:  # 成功率が低い場合、レートを下げる
            self._current_rate = max(
                self.config.min_requests_per_second,
                self._current_rate * (1 - self.config.adaptation_factor)
            )
        
        # 統計をリセット
        self._success_count = 0
        self._failure_count = 0
        self._last_adaptation = current_time
        
        logger.info(f"Adaptive rate adjusted to {self._current_rate:.2f} req/s")
    
    async def _consume_tokens(self, tokens: int) -> None:
        """トークンを消費"""
        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            self._tokens -= tokens
        elif self.config.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
            self._tokens += tokens
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            self._window_requests.append(time.time())
        elif self.config.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            self.stats.window_request_count += tokens
    
    async def _calculate_wait_time(self, tokens: int) -> float:
        """待機時間を計算"""
        current_time = time.time()
        
        if self.config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
            if self._tokens < tokens:
                tokens_needed = tokens - self._tokens
                return tokens_needed / self.config.requests_per_second
        
        elif self.config.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            if self._window_requests:
                oldest_request = min(self._window_requests)
                window_end = oldest_request + self.config.window_size_seconds
                return max(0, window_end - current_time)
        
        return 0.0
    
    async def _record_success(self) -> None:
        """成功を記録"""
        self._success_count += 1
        self._circuit_breaker_failures = 0
        
        if self._circuit_breaker_state == "half_open":
            self._circuit_breaker_state = "closed"
            logger.info("Circuit breaker moved to closed state")
    
    async def record_failure(self) -> None:
        """失敗を記録"""
        self._failure_count += 1
        self._circuit_breaker_failures += 1
        self._circuit_breaker_last_failure = time.time()
        
        # サーキットブレーカーをオープン
        if self._circuit_breaker_failures >= 5:  # 5回連続失敗
            self._circuit_breaker_state = "open"
            logger.warning("Circuit breaker opened due to failures")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        current_time = time.time()
        
        return {
            "config": {
                "algorithm": self.config.algorithm.value,
                "requests_per_second": self.config.requests_per_second,
                "burst_capacity": self.config.burst_capacity,
                "window_size_seconds": self.config.window_size_seconds,
                "tier": self.config.tier.value
            },
            "stats": {
                "total_requests": self.stats.total_requests,
                "allowed_requests": self.stats.allowed_requests,
                "blocked_requests": self.stats.blocked_requests,
                "success_rate": (
                    self.stats.allowed_requests / max(1, self.stats.total_requests) * 100
                ),
                "current_tokens": self._tokens,
                "current_rate": self._current_rate if self.config.adaptive_enabled else self.config.requests_per_second
            },
            "circuit_breaker": {
                "state": self._circuit_breaker_state,
                "failures": self._circuit_breaker_failures,
                "last_failure": self._circuit_breaker_last_failure
            },
            "adaptive": {
                "enabled": self.config.adaptive_enabled,
                "success_count": self._success_count,
                "failure_count": self._failure_count,
                "last_adaptation": self._last_adaptation
            }
        }
    
    async def reset(self) -> None:
        """レート制限器をリセット"""
        async with self._lock:
            self._tokens = self.config.burst_capacity
            self._last_refill = time.time()
            self._window_requests.clear()
            self._circuit_breaker_state = "closed"
            self._circuit_breaker_failures = 0
            self._current_rate = self.config.requests_per_second
            self._success_count = 0
            self._failure_count = 0
            self._last_adaptation = time.time()
            
            # 統計をリセット
            self.stats = RateLimitStats()
            
            logger.info("Rate limiter reset")
