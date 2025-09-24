"""
ロードバランサー

複数のAPIプロバイダー間での負荷分散を提供します。
"""

import asyncio
import logging
import random
import time
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """ロードバランシング戦略"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    HEALTH_BASED = "health_based"
    RANDOM = "random"
    LEAST_RESPONSE_TIME = "least_response_time"


@dataclass
class ProviderStats:
    """プロバイダー統計"""
    name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    last_request_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_failure_time: Optional[float] = None
    consecutive_failures: int = 0
    is_healthy: bool = True
    weight: float = 1.0


@dataclass
class LoadBalancerConfig:
    """ロードバランサー設定"""
    strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN
    health_check_interval: int = 30  # 秒
    health_check_timeout: int = 5    # 秒
    failure_threshold: int = 3       # 連続失敗閾値
    recovery_threshold: int = 2      # 回復閾値
    max_retries: int = 3             # 最大リトライ回数
    retry_delay: float = 1.0         # リトライ遅延（秒）


class LoadBalancer:
    """ロードバランサー"""
    
    def __init__(self, config: LoadBalancerConfig):
        self.config = config
        self.providers: Dict[str, Any] = {}
        self.provider_stats: Dict[str, ProviderStats] = {}
        self.current_index = 0
        self._lock = asyncio.Lock()
        self._health_check_task: Optional[asyncio.Task] = None
        self._started = False
    
    async def start(self) -> None:
        """ロードバランサーを開始"""
        if self._started:
            return
        
        self._started = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Load balancer started")
    
    async def stop(self) -> None:
        """ロードバランサーを停止"""
        if not self._started:
            return
        
        self._started = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Load balancer stopped")
    
    def add_provider(self, name: str, provider: Any, weight: float = 1.0) -> None:
        """プロバイダーを追加"""
        self.providers[name] = provider
        self.provider_stats[name] = ProviderStats(
            name=name,
            weight=weight
        )
        logger.info(f"Provider {name} added with weight {weight}")
    
    def remove_provider(self, name: str) -> None:
        """プロバイダーを削除"""
        if name in self.providers:
            del self.providers[name]
            del self.provider_stats[name]
            logger.info(f"Provider {name} removed")
    
    async def execute_request(
        self,
        request_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """リクエストを実行"""
        if not self.providers:
            raise NoAvailableProvidersException("No providers available")
        
        last_exception = None
        
        for attempt in range(self.config.max_retries):
            try:
                # プロバイダーを選択
                provider_name = await self._select_provider()
                if not provider_name:
                    raise NoAvailableProvidersException("No healthy providers available")
                
                provider = self.providers[provider_name]
                stats = self.provider_stats[provider_name]
                
                # リクエストを実行
                start_time = time.time()
                result = await request_func(provider, *args, **kwargs)
                response_time = time.time() - start_time
                
                # 成功を記録
                await self._record_success(provider_name, response_time)
                
                return result
                
            except Exception as e:
                last_exception = e
                if provider_name:
                    await self._record_failure(provider_name)
                
                logger.warning(f"Request failed with provider {provider_name}: {e}")
                
                # 最後の試行でない場合は待機
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        # すべての試行が失敗
        raise LoadBalancerException(f"All retry attempts failed. Last error: {last_exception}")
    
    async def _select_provider(self) -> Optional[str]:
        """プロバイダーを選択"""
        async with self._lock:
            healthy_providers = [
                name for name, stats in self.provider_stats.items()
                if stats.is_healthy
            ]
            
            if not healthy_providers:
                return None
            
            if self.config.strategy == LoadBalancingStrategy.ROUND_ROBIN:
                return await self._round_robin_selection(healthy_providers)
            elif self.config.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
                return await self._weighted_round_robin_selection(healthy_providers)
            elif self.config.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
                return await self._least_connections_selection(healthy_providers)
            elif self.config.strategy == LoadBalancingStrategy.HEALTH_BASED:
                return await self._health_based_selection(healthy_providers)
            elif self.config.strategy == LoadBalancingStrategy.RANDOM:
                return await self._random_selection(healthy_providers)
            elif self.config.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
                return await self._least_response_time_selection(healthy_providers)
            else:
                return await self._round_robin_selection(healthy_providers)
    
    async def _round_robin_selection(self, healthy_providers: List[str]) -> str:
        """ラウンドロビン選択"""
        if not healthy_providers:
            return None
        
        provider = healthy_providers[self.current_index % len(healthy_providers)]
        self.current_index += 1
        return provider
    
    async def _weighted_round_robin_selection(self, healthy_providers: List[str]) -> str:
        """重み付きラウンドロビン選択"""
        if not healthy_providers:
            return None
        
        # 重みに基づいて選択
        total_weight = sum(self.provider_stats[name].weight for name in healthy_providers)
        if total_weight == 0:
            return await self._round_robin_selection(healthy_providers)
        
        # 重み付きラウンドロビン（簡易実装）
        weighted_providers = []
        for name in healthy_providers:
            weight = int(self.provider_stats[name].weight * 10)  # 重みを10倍して整数化
            weighted_providers.extend([name] * weight)
        
        if weighted_providers:
            return weighted_providers[self.current_index % len(weighted_providers)]
        else:
            return await self._round_robin_selection(healthy_providers)
    
    async def _least_connections_selection(self, healthy_providers: List[str]) -> str:
        """最小接続数選択"""
        if not healthy_providers:
            return None
        
        # 現在のリクエスト数を比較（簡易実装）
        min_requests = min(
            self.provider_stats[name].total_requests
            for name in healthy_providers
        )
        
        candidates = [
            name for name in healthy_providers
            if self.provider_stats[name].total_requests == min_requests
        ]
        
        return random.choice(candidates)
    
    async def _health_based_selection(self, healthy_providers: List[str]) -> str:
        """ヘルスベース選択"""
        if not healthy_providers:
            return None
        
        # 成功率に基づいて選択
        best_providers = []
        best_success_rate = 0.0
        
        for name in healthy_providers:
            stats = self.provider_stats[name]
            if stats.total_requests > 0:
                success_rate = stats.successful_requests / stats.total_requests
                if success_rate > best_success_rate:
                    best_success_rate = success_rate
                    best_providers = [name]
                elif success_rate == best_success_rate:
                    best_providers.append(name)
            else:
                # リクエストがない場合は重みで判断
                best_providers.append(name)
        
        return random.choice(best_providers)
    
    async def _random_selection(self, healthy_providers: List[str]) -> str:
        """ランダム選択"""
        if not healthy_providers:
            return None
        
        return random.choice(healthy_providers)
    
    async def _least_response_time_selection(self, healthy_providers: List[str]) -> str:
        """最小応答時間選択"""
        if not healthy_providers:
            return None
        
        # 平均応答時間が最小のプロバイダーを選択
        min_response_time = float('inf')
        best_providers = []
        
        for name in healthy_providers:
            stats = self.provider_stats[name]
            if stats.avg_response_time < min_response_time:
                min_response_time = stats.avg_response_time
                best_providers = [name]
            elif stats.avg_response_time == min_response_time:
                best_providers.append(name)
        
        return random.choice(best_providers)
    
    async def _record_success(self, provider_name: str, response_time: float) -> None:
        """成功を記録"""
        stats = self.provider_stats[provider_name]
        stats.total_requests += 1
        stats.successful_requests += 1
        stats.total_response_time += response_time
        stats.avg_response_time = stats.total_response_time / stats.total_requests
        stats.last_request_time = time.time()
        stats.last_success_time = time.time()
        stats.consecutive_failures = 0
        
        # ヘルス状態を更新
        if not stats.is_healthy and stats.consecutive_failures == 0:
            stats.is_healthy = True
            logger.info(f"Provider {provider_name} marked as healthy")
    
    async def _record_failure(self, provider_name: str) -> None:
        """失敗を記録"""
        stats = self.provider_stats[provider_name]
        stats.total_requests += 1
        stats.failed_requests += 1
        stats.last_request_time = time.time()
        stats.last_failure_time = time.time()
        stats.consecutive_failures += 1
        
        # 連続失敗閾値をチェック
        if stats.consecutive_failures >= self.config.failure_threshold:
            stats.is_healthy = False
            logger.warning(f"Provider {provider_name} marked as unhealthy due to {stats.consecutive_failures} consecutive failures")
    
    async def _health_check_loop(self) -> None:
        """ヘルスチェックループ"""
        while self._started:
            try:
                await self._perform_health_checks()
                await asyncio.sleep(self.config.health_check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(5)
    
    async def _perform_health_checks(self) -> None:
        """ヘルスチェックを実行"""
        for name, provider in self.providers.items():
            try:
                # プロバイダーのヘルスチェックメソッドを呼び出し
                if hasattr(provider, 'health_check'):
                    health_result = await asyncio.wait_for(
                        provider.health_check(),
                        timeout=self.config.health_check_timeout
                    )
                    
                    stats = self.provider_stats[name]
                    if health_result and stats.consecutive_failures >= self.config.recovery_threshold:
                        stats.is_healthy = True
                        stats.consecutive_failures = 0
                        logger.info(f"Provider {name} recovered through health check")
                
            except Exception as e:
                logger.warning(f"Health check failed for provider {name}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_requests = sum(stats.total_requests for stats in self.provider_stats.values())
        total_successful = sum(stats.successful_requests for stats in self.provider_stats.values())
        
        return {
            "config": {
                "strategy": self.config.strategy.value,
                "health_check_interval": self.config.health_check_interval,
                "failure_threshold": self.config.failure_threshold,
                "max_retries": self.config.max_retries
            },
            "overall": {
                "total_requests": total_requests,
                "successful_requests": total_successful,
                "success_rate": (total_successful / max(1, total_requests) * 100),
                "healthy_providers": sum(1 for stats in self.provider_stats.values() if stats.is_healthy),
                "total_providers": len(self.provider_stats)
            },
            "providers": {
                name: {
                    "total_requests": stats.total_requests,
                    "successful_requests": stats.successful_requests,
                    "failed_requests": stats.failed_requests,
                    "success_rate": (stats.successful_requests / max(1, stats.total_requests) * 100),
                    "avg_response_time": stats.avg_response_time,
                    "consecutive_failures": stats.consecutive_failures,
                    "is_healthy": stats.is_healthy,
                    "weight": stats.weight
                }
                for name, stats in self.provider_stats.items()
            }
        }


class NoAvailableProvidersException(Exception):
    """利用可能なプロバイダーがない例外"""
    pass


class LoadBalancerException(Exception):
    """ロードバランサーの一般的な例外"""
    pass
