"""
統合レート制限管理システム

レート制限、サーキットブレーカー、ロードバランサー、フォールバックを統合した管理システム
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from .rate_limiter.advanced_rate_limiter import AdvancedRateLimiter, RateLimitConfig, RateLimitAlgorithm
from .circuit_breaker.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState
from .load_balancer.load_balancer import LoadBalancer, LoadBalancerConfig, LoadBalancingStrategy
from .fallback_manager.fallback_manager import FallbackManager, FallbackConfig, FallbackStrategy

logger = logging.getLogger(__name__)


@dataclass
class IntegratedRateLimitConfig:
    """統合レート制限設定"""
    # レート制限設定
    rate_limit_algorithm: RateLimitAlgorithm = RateLimitAlgorithm.ADAPTIVE
    requests_per_second: float = 10.0
    burst_capacity: int = 50
    
    # サーキットブレーカー設定
    circuit_breaker_enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: int = 60
    
    # ロードバランサー設定
    load_balancing_strategy: LoadBalancingStrategy = LoadBalancingStrategy.HEALTH_BASED
    max_retries: int = 3
    
    # フォールバック設定
    fallback_strategies: List[FallbackStrategy] = None
    cache_ttl_seconds: int = 300
    
    def __post_init__(self):
        if self.fallback_strategies is None:
            self.fallback_strategies = [
                FallbackStrategy.CACHE,
                FallbackStrategy.ALTERNATIVE_PROVIDER,
                FallbackStrategy.STALE_DATA
            ]


class IntegratedRateLimitManager:
    """統合レート制限管理システム"""
    
    def __init__(self, config: IntegratedRateLimitConfig):
        self.config = config
        
        # レート制限器
        rate_limit_config = RateLimitConfig(
            algorithm=config.rate_limit_algorithm,
            requests_per_second=config.requests_per_second,
            burst_capacity=config.burst_capacity,
            adaptive_enabled=True
        )
        self.rate_limiter = AdvancedRateLimiter(rate_limit_config)
        
        # サーキットブレーカー
        if config.circuit_breaker_enabled:
            circuit_breaker_config = CircuitBreakerConfig(
                failure_threshold=config.failure_threshold,
                recovery_timeout=config.recovery_timeout
            )
            self.circuit_breaker = CircuitBreaker("integrated", circuit_breaker_config)
        else:
            self.circuit_breaker = None
        
        # ロードバランサー
        load_balancer_config = LoadBalancerConfig(
            strategy=config.load_balancing_strategy,
            max_retries=config.max_retries
        )
        self.load_balancer = LoadBalancer(load_balancer_config)
        
        # フォールバック管理
        fallback_config = FallbackConfig(
            strategies=config.fallback_strategies,
            cache_ttl_seconds=config.cache_ttl_seconds
        )
        self.fallback_manager = FallbackManager(fallback_config)
        
        # 統計
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limited_requests = 0
        self.circuit_breaker_blocked_requests = 0
        self.fallback_used_requests = 0
    
    async def start(self) -> None:
        """統合システムを開始"""
        await self.load_balancer.start()
        logger.info("Integrated rate limit manager started")
    
    async def stop(self) -> None:
        """統合システムを停止"""
        await self.load_balancer.stop()
        logger.info("Integrated rate limit manager stopped")
    
    def add_provider(self, name: str, provider: Any, weight: float = 1.0) -> None:
        """プロバイダーを追加"""
        self.load_balancer.add_provider(name, provider, weight)
        logger.info(f"Provider {name} added to integrated system")
    
    def add_alternative_provider(self, name: str, provider: Any) -> None:
        """代替プロバイダーを追加"""
        self.fallback_manager.add_alternative_provider(name, provider)
        logger.info(f"Alternative provider {name} added to fallback system")
    
    async def execute_request(
        self,
        request_func: Callable,
        cache_key: str,
        *args,
        **kwargs
    ) -> Any:
        """統合システムでリクエストを実行"""
        self.total_requests += 1
        
        try:
            # 1. レート制限チェック
            if not await self.rate_limiter.acquire():
                self.rate_limited_requests += 1
                logger.warning("Request rate limited")
                raise RateLimitExceededException("Rate limit exceeded")
            
            # 2. サーキットブレーカーチェック
            if self.circuit_breaker:
                try:
                    result = await self.circuit_breaker.call(
                        self._execute_with_load_balancer,
                        request_func,
                        cache_key,
                        *args,
                        **kwargs
                    )
                    self.successful_requests += 1
                    return result
                    
                except Exception as e:
                    self.circuit_breaker_blocked_requests += 1
                    logger.warning(f"Circuit breaker blocked request: {e}")
                    
                    # サーキットブレーカーがブロックした場合、フォールバックを試行
                    return await self._execute_with_fallback(request_func, cache_key, *args, **kwargs)
            else:
                # サーキットブレーカーが無効な場合、直接実行
                result = await self._execute_with_load_balancer(request_func, cache_key, *args, **kwargs)
                self.successful_requests += 1
                return result
                
        except Exception as e:
            self.failed_requests += 1
            logger.error(f"Request failed: {e}")
            
            # フォールバックを試行
            try:
                result = await self._execute_with_fallback(request_func, cache_key, *args, **kwargs)
                self.fallback_used_requests += 1
                return result
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise
    
    async def _execute_with_load_balancer(
        self,
        request_func: Callable,
        cache_key: str,
        *args,
        **kwargs
    ) -> Any:
        """ロードバランサー経由でリクエストを実行"""
        def wrapped_request(provider, *args, **kwargs):
            return request_func(provider, *args, **kwargs)
        
        result = await self.load_balancer.execute_request(wrapped_request, *args, **kwargs)
        
        # 結果をキャッシュに保存
        await self.fallback_manager.cache_data(cache_key, result)
        
        return result
    
    async def _execute_with_fallback(
        self,
        request_func: Callable,
        cache_key: str,
        *args,
        **kwargs
    ) -> Any:
        """フォールバック経由でリクエストを実行"""
        def wrapped_request(*args, **kwargs):
            return request_func(*args, **kwargs)
        
        result = await self.fallback_manager.execute_with_fallback(
            wrapped_request,
            cache_key,
            *args,
            **kwargs
        )
        
        return result
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        health_status = {
            "overall": "healthy",
            "components": {}
        }
        
        # レート制限器のヘルスチェック
        rate_limiter_stats = self.rate_limiter.get_stats()
        health_status["components"]["rate_limiter"] = {
            "status": "healthy",
            "stats": rate_limiter_stats
        }
        
        # サーキットブレーカーのヘルスチェック
        if self.circuit_breaker:
            circuit_breaker_state = self.circuit_breaker.get_state()
            health_status["components"]["circuit_breaker"] = {
                "status": "healthy" if circuit_breaker_state["state"] != "open" else "degraded",
                "state": circuit_breaker_state
            }
        else:
            health_status["components"]["circuit_breaker"] = {
                "status": "disabled"
            }
        
        # ロードバランサーのヘルスチェック
        load_balancer_stats = self.load_balancer.get_stats()
        healthy_providers = load_balancer_stats["overall"]["healthy_providers"]
        total_providers = load_balancer_stats["overall"]["total_providers"]
        
        health_status["components"]["load_balancer"] = {
            "status": "healthy" if healthy_providers > 0 else "unhealthy",
            "healthy_providers": healthy_providers,
            "total_providers": total_providers,
            "stats": load_balancer_stats
        }
        
        # フォールバック管理のヘルスチェック
        fallback_health = await self.fallback_manager.health_check()
        health_status["components"]["fallback_manager"] = fallback_health
        
        # 全体のヘルス状態を決定
        component_statuses = [
            comp["status"] for comp in health_status["components"].values()
            if comp["status"] != "disabled"
        ]
        
        if "unhealthy" in component_statuses:
            health_status["overall"] = "unhealthy"
        elif "degraded" in component_statuses:
            health_status["overall"] = "degraded"
        
        return health_status
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        success_rate = (
            self.successful_requests / max(1, self.total_requests) * 100
        )
        
        return {
            "overall": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate": success_rate,
                "rate_limited_requests": self.rate_limited_requests,
                "circuit_breaker_blocked_requests": self.circuit_breaker_blocked_requests,
                "fallback_used_requests": self.fallback_used_requests
            },
            "rate_limiter": self.rate_limiter.get_stats(),
            "circuit_breaker": self.circuit_breaker.get_state() if self.circuit_breaker else None,
            "load_balancer": self.load_balancer.get_stats(),
            "fallback_manager": self.fallback_manager.get_stats()
        }
    
    async def reset_stats(self) -> None:
        """統計をリセット"""
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.rate_limited_requests = 0
        self.circuit_breaker_blocked_requests = 0
        self.fallback_used_requests = 0
        
        await self.rate_limiter.reset()
        if self.circuit_breaker:
            await self.circuit_breaker.reset()
        
        logger.info("Integrated rate limit manager stats reset")


class RateLimitExceededException(Exception):
    """レート制限超過例外"""
    pass
