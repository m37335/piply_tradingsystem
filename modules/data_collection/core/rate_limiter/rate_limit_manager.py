"""
レート制限管理システム

複数のレート制限アルゴリズムを統合管理します。
"""

import asyncio
import time
from typing import Dict, List, Optional

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
from .sliding_window import SlidingWindow
from .token_bucket import TokenBucket


class RateLimitManager:
    """レート制限管理システム"""
    
    def __init__(
        self,
        algorithm: str = "token_bucket",
        capacity: int = 100,
        refill_rate: float = 10.0,
        window_size: int = 60,
        max_requests: int = 100,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        """
        レート制限管理システムを初期化
        
        Args:
            algorithm: 使用するアルゴリズム ("token_bucket", "leaky_bucket", "sliding_window", "adaptive")
            capacity: バケット容量
            refill_rate: 補充率
            window_size: スライディングウィンドウサイズ（秒）
            max_requests: 最大リクエスト数
            failure_threshold: サーキットブレーカーの失敗閾値
            recovery_timeout: サーキットブレーカーの復旧タイムアウト
        """
        self.algorithm = algorithm
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.window_size = window_size
        self.max_requests = max_requests
        
        # レート制限器を初期化
        self._init_rate_limiter()
        
        # サーキットブレーカーを初期化
        self.circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        
        # フォールバック戦略を初期化
        self.fallback_strategies: List[FallbackStrategy] = []
        self._init_fallback_strategies()
        
        # 統計情報
        self.total_requests = 0
        self.allowed_requests = 0
        self.blocked_requests = 0
        self.fallback_requests = 0
    
    def _init_rate_limiter(self) -> None:
        """レート制限器を初期化"""
        if self.algorithm == "token_bucket":
            self.rate_limiter = TokenBucket(self.capacity, self.refill_rate)
        elif self.algorithm == "leaky_bucket":
            self.rate_limiter = LeakyBucket(self.capacity, self.refill_rate)
        elif self.algorithm == "sliding_window":
            self.rate_limiter = SlidingWindow(self.window_size, self.max_requests)
        elif self.algorithm == "adaptive":
            self.rate_limiter = AdaptiveRateLimiter(
                self.capacity, self.refill_rate
            )
        else:
            raise ValueError(f"Unknown algorithm: {self.algorithm}")
    
    def _init_fallback_strategies(self) -> None:
        """フォールバック戦略を初期化"""
        # キャッシュ戦略
        self.fallback_strategies.append(CacheFallbackStrategy())
        
        # 古いデータ戦略
        self.fallback_strategies.append(OldDataFallbackStrategy())
        
        # リトライ戦略
        self.fallback_strategies.append(RetryFallbackStrategy())
    
    async def execute_with_rate_limit(
        self, func, *args, fallback_enabled: bool = True, **kwargs
    ):
        """
        レート制限付きで関数を実行
        
        Args:
            func: 実行する関数
            *args: 関数の引数
            fallback_enabled: フォールバックを有効にするか
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
        """
        self.total_requests += 1
        
        # サーキットブレーカーのチェック
        if self.circuit_breaker.get_state() == CircuitState.OPEN:
            if fallback_enabled:
                return await self._execute_fallback(func, *args, **kwargs)
            else:
                raise Exception("Circuit breaker is open")
        
        # レート制限のチェック
        if not self._check_rate_limit():
            self.blocked_requests += 1
            if fallback_enabled:
                return await self._execute_fallback(func, *args, **kwargs)
            else:
                raise Exception("Rate limit exceeded")
        
        try:
            # サーキットブレーカー経由で関数を実行
            result = self.circuit_breaker.call(func, *args, **kwargs)
            self.allowed_requests += 1
            return result
        except Exception as e:
            if fallback_enabled:
                return await self._execute_fallback(func, *args, **kwargs)
            else:
                raise e
    
    def _check_rate_limit(self) -> bool:
        """レート制限をチェック"""
        if self.algorithm == "token_bucket":
            return self.rate_limiter.consume()
        elif self.algorithm == "leaky_bucket":
            return self.rate_limiter.add_request()
        elif self.algorithm == "sliding_window":
            return self.rate_limiter.add_request()
        elif self.algorithm == "adaptive":
            return self.rate_limiter.consume()
        else:
            return True
    
    async def _execute_fallback(self, func, *args, **kwargs):
        """フォールバック戦略を実行"""
        self.fallback_requests += 1
        
        for strategy in self.fallback_strategies:
            try:
                if isinstance(strategy, CacheFallbackStrategy):
                    # キャッシュからデータを取得
                    cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                    cached_result = await strategy.execute(cache_key)
                    if cached_result is not None:
                        return cached_result
                
                elif isinstance(strategy, OldDataFallbackStrategy):
                    # 古いデータから取得
                    data_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                    old_result = await strategy.execute(data_key)
                    if old_result is not None:
                        return old_result
                
                elif isinstance(strategy, RetryFallbackStrategy):
                    # リトライして実行
                    return await strategy.execute(func, *args, **kwargs)
                
                else:
                    # その他の戦略
                    return await strategy.execute(*args, **kwargs)
                    
            except Exception:
                continue
        
        # すべてのフォールバック戦略が失敗した場合
        raise Exception("All fallback strategies failed")
    
    def get_stats(self) -> Dict[str, any]:
        """統計情報を取得"""
        stats = {
            "algorithm": self.algorithm,
            "total_requests": self.total_requests,
            "allowed_requests": self.allowed_requests,
            "blocked_requests": self.blocked_requests,
            "fallback_requests": self.fallback_requests,
            "circuit_breaker_state": self.circuit_breaker.get_state().value,
            "circuit_breaker_failures": self.circuit_breaker.get_failure_count(),
        }
        
        # アルゴリズム固有の統計
        if self.algorithm == "token_bucket":
            stats["tokens_available"] = self.rate_limiter.get_tokens_available()
        elif self.algorithm == "leaky_bucket":
            stats["bucket_level"] = self.rate_limiter.get_level()
        elif self.algorithm == "sliding_window":
            stats["requests_in_window"] = self.rate_limiter.get_requests_count()
        elif self.algorithm == "adaptive":
            stats["tokens_available"] = self.rate_limiter.get_tokens_available()
            stats["refill_rate"] = self.rate_limiter.get_refill_rate()
            stats["success_rate"] = self.rate_limiter.get_success_rate()
        
        return stats
    
    def reset_stats(self) -> None:
        """統計情報をリセット"""
        self.total_requests = 0
        self.allowed_requests = 0
        self.blocked_requests = 0
        self.fallback_requests = 0
        self.circuit_breaker.reset()
    
    def add_fallback_strategy(self, strategy: FallbackStrategy) -> None:
        """フォールバック戦略を追加"""
        self.fallback_strategies.append(strategy)
    
    def remove_fallback_strategy(self, strategy: FallbackStrategy) -> None:
        """フォールバック戦略を削除"""
        if strategy in self.fallback_strategies:
            self.fallback_strategies.remove(strategy)
