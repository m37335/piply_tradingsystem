"""
フォールバック管理システム

API障害時の代替戦略を提供します。
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class FallbackStrategy(Enum):
    """フォールバック戦略"""
    CACHE = "cache"
    ALTERNATIVE_PROVIDER = "alternative_provider"
    STALE_DATA = "stale_data"
    DEFAULT_VALUE = "default_value"
    RETRY = "retry"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass
class FallbackConfig:
    """フォールバック設定"""
    strategies: List[FallbackStrategy]
    cache_ttl_seconds: int = 300  # 5分
    stale_data_threshold_seconds: int = 3600  # 1時間
    max_retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    default_values: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.default_values is None:
            self.default_values = {}


@dataclass
class FallbackStats:
    """フォールバック統計"""
    total_fallbacks: int = 0
    cache_hits: int = 0
    alternative_provider_used: int = 0
    stale_data_used: int = 0
    default_value_used: int = 0
    retry_successful: int = 0
    circuit_breaker_triggered: int = 0


class FallbackManager:
    """フォールバック管理システム"""
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        self.stats = FallbackStats()
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.alternative_providers: Dict[str, Any] = {}
        self._lock = asyncio.Lock()
    
    def add_alternative_provider(self, name: str, provider: Any) -> None:
        """代替プロバイダーを追加"""
        self.alternative_providers[name] = provider
        logger.info(f"Alternative provider {name} added")
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        cache_key: str,
        *args,
        **kwargs
    ) -> Any:
        """フォールバック付きでリクエストを実行"""
        async with self._lock:
            self.stats.total_fallbacks += 1
            
            # 戦略に従ってフォールバックを試行
            for strategy in self.config.strategies:
                try:
                    if strategy == FallbackStrategy.CACHE:
                        result = await self._try_cache_fallback(cache_key)
                        if result is not None:
                            return result
                    
                    elif strategy == FallbackStrategy.ALTERNATIVE_PROVIDER:
                        result = await self._try_alternative_provider_fallback(primary_func, *args, **kwargs)
                        if result is not None:
                            return result
                    
                    elif strategy == FallbackStrategy.STALE_DATA:
                        result = await self._try_stale_data_fallback(cache_key)
                        if result is not None:
                            return result
                    
                    elif strategy == FallbackStrategy.DEFAULT_VALUE:
                        result = await self._try_default_value_fallback(cache_key)
                        if result is not None:
                            return result
                    
                    elif strategy == FallbackStrategy.RETRY:
                        result = await self._try_retry_fallback(primary_func, *args, **kwargs)
                        if result is not None:
                            return result
                    
                    elif strategy == FallbackStrategy.CIRCUIT_BREAKER:
                        # サーキットブレーカーは他のコンポーネントで処理
                        continue
                
                except Exception as e:
                    logger.warning(f"Fallback strategy {strategy.value} failed: {e}")
                    continue
            
            # すべてのフォールバック戦略が失敗
            raise FallbackException("All fallback strategies failed")
    
    async def _try_cache_fallback(self, cache_key: str) -> Optional[Any]:
        """キャッシュフォールバックを試行"""
        if cache_key not in self.cache:
            return None
        
        cache_entry = self.cache[cache_key]
        current_time = time.time()
        
        # TTLチェック
        if current_time - cache_entry["timestamp"] > self.config.cache_ttl_seconds:
            # キャッシュが期限切れ
            del self.cache[cache_key]
            return None
        
        self.stats.cache_hits += 1
        logger.info(f"Cache fallback successful for key: {cache_key}")
        return cache_entry["data"]
    
    async def _try_alternative_provider_fallback(
        self,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """代替プロバイダーフォールバックを試行"""
        for name, provider in self.alternative_providers.items():
            try:
                # 代替プロバイダーで同じ関数を実行
                result = await primary_func(provider, *args, **kwargs)
                
                self.stats.alternative_provider_used += 1
                logger.info(f"Alternative provider {name} fallback successful")
                return result
                
            except Exception as e:
                logger.warning(f"Alternative provider {name} failed: {e}")
                continue
        
        return None
    
    async def _try_stale_data_fallback(self, cache_key: str) -> Optional[Any]:
        """古いデータフォールバックを試行"""
        if cache_key not in self.cache:
            return None
        
        cache_entry = self.cache[cache_key]
        current_time = time.time()
        
        # 古いデータの閾値チェック
        if current_time - cache_entry["timestamp"] > self.config.stale_data_threshold_seconds:
            # データが古すぎる
            return None
        
        self.stats.stale_data_used += 1
        logger.info(f"Stale data fallback successful for key: {cache_key}")
        return cache_entry["data"]
    
    async def _try_default_value_fallback(self, cache_key: str) -> Optional[Any]:
        """デフォルト値フォールバックを試行"""
        if cache_key in self.config.default_values:
            self.stats.default_value_used += 1
            logger.info(f"Default value fallback used for key: {cache_key}")
            return self.config.default_values[cache_key]
        
        return None
    
    async def _try_retry_fallback(
        self,
        primary_func: Callable,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """リトライフォールバックを試行"""
        last_exception = None
        
        for attempt in range(self.config.max_retry_attempts):
            try:
                result = await primary_func(*args, **kwargs)
                self.stats.retry_successful += 1
                logger.info(f"Retry fallback successful after {attempt + 1} attempts")
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning(f"Retry attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay_seconds)
        
        # すべてのリトライが失敗
        logger.error(f"All retry attempts failed. Last error: {last_exception}")
        return None
    
    async def cache_data(self, key: str, data: Any) -> None:
        """データをキャッシュに保存"""
        async with self._lock:
            self.cache[key] = {
                "data": data,
                "timestamp": time.time()
            }
            logger.debug(f"Data cached for key: {key}")
    
    async def get_cached_data(self, key: str) -> Optional[Any]:
        """キャッシュからデータを取得"""
        async with self._lock:
            if key not in self.cache:
                return None
            
            cache_entry = self.cache[key]
            current_time = time.time()
            
            # TTLチェック
            if current_time - cache_entry["timestamp"] > self.config.cache_ttl_seconds:
                del self.cache[key]
                return None
            
            return cache_entry["data"]
    
    async def invalidate_cache(self, key: Optional[str] = None) -> None:
        """キャッシュを無効化"""
        async with self._lock:
            if key:
                if key in self.cache:
                    del self.cache[key]
                    logger.info(f"Cache invalidated for key: {key}")
            else:
                self.cache.clear()
                logger.info("All cache invalidated")
    
    async def cleanup_expired_cache(self) -> None:
        """期限切れキャッシュをクリーンアップ"""
        async with self._lock:
            current_time = time.time()
            expired_keys = []
            
            for key, entry in self.cache.items():
                if current_time - entry["timestamp"] > self.config.cache_ttl_seconds:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            "config": {
                "strategies": [s.value for s in self.config.strategies],
                "cache_ttl_seconds": self.config.cache_ttl_seconds,
                "stale_data_threshold_seconds": self.config.stale_data_threshold_seconds,
                "max_retry_attempts": self.config.max_retry_attempts,
                "retry_delay_seconds": self.config.retry_delay_seconds
            },
            "stats": {
                "total_fallbacks": self.stats.total_fallbacks,
                "cache_hits": self.stats.cache_hits,
                "alternative_provider_used": self.stats.alternative_provider_used,
                "stale_data_used": self.stats.stale_data_used,
                "default_value_used": self.stats.default_value_used,
                "retry_successful": self.stats.retry_successful,
                "circuit_breaker_triggered": self.stats.circuit_breaker_triggered
            },
            "cache": {
                "total_entries": len(self.cache),
                "keys": list(self.cache.keys())
            },
            "alternative_providers": {
                "count": len(self.alternative_providers),
                "names": list(self.alternative_providers.keys())
            }
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        cache_health = "healthy" if len(self.cache) < 1000 else "warning"  # キャッシュサイズチェック
        
        provider_health = {}
        for name, provider in self.alternative_providers.items():
            try:
                if hasattr(provider, 'health_check'):
                    health_result = await provider.health_check()
                    provider_health[name] = "healthy" if health_result else "unhealthy"
                else:
                    provider_health[name] = "unknown"
            except Exception:
                provider_health[name] = "error"
        
        overall_health = "healthy"
        if any(status == "unhealthy" for status in provider_health.values()):
            overall_health = "degraded"
        if all(status == "error" for status in provider_health.values()):
            overall_health = "unhealthy"
        
        return {
            "status": overall_health,
            "cache_health": cache_health,
            "provider_health": provider_health,
            "cache_size": len(self.cache),
            "alternative_providers_count": len(self.alternative_providers)
        }


class FallbackException(Exception):
    """フォールバックの例外"""
    pass
