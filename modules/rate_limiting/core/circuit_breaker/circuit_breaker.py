"""
サーキットブレーカー

API障害時の保護機能を提供します。
"""

import asyncio
import time
import logging
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """サーキットブレーカーの状態"""
    CLOSED = "closed"      # 通常動作
    OPEN = "open"         # 障害発生、リクエスト拒否
    HALF_OPEN = "half_open" # テスト中、限定的にリクエスト許可


@dataclass
class CircuitBreakerConfig:
    """サーキットブレーカー設定"""
    failure_threshold: int = 5          # 失敗閾値
    recovery_timeout: int = 60          # 回復タイムアウト（秒）
    success_threshold: int = 3          # 成功閾値（ハーフオープン時）
    timeout: Optional[int] = None       # リクエストタイムアウト（秒）
    
    # 監視設定
    monitoring_enabled: bool = True
    metrics_window_size: int = 100      # メトリクスウィンドウサイズ
    health_check_interval: int = 30     # ヘルスチェック間隔（秒）


@dataclass
class CircuitBreakerStats:
    """サーキットブレーカー統計"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    circuit_breaker_trips: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None


class CircuitBreaker:
    """サーキットブレーカー"""
    
    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.stats = CircuitBreakerStats()
        
        # 状態管理
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.time()
        
        # メトリクス
        self.request_history: list = []
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """関数をサーキットブレーカー経由で実行"""
        async with self._lock:
            # 状態チェック
            if not await self._can_execute():
                raise CircuitBreakerOpenException(f"Circuit breaker {self.name} is open")
            
            # リクエストを記録
            self.stats.total_requests += 1
            start_time = time.time()
            
            try:
                # タイムアウト設定
                if self.config.timeout:
                    result = await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
                else:
                    result = await func(*args, **kwargs)
                
                # 成功を記録
                await self._record_success()
                self.stats.successful_requests += 1
                self.stats.last_success_time = time.time()
                
                return result
                
            except asyncio.TimeoutError:
                # タイムアウト
                await self._record_failure("timeout")
                self.stats.timeout_requests += 1
                raise CircuitBreakerTimeoutException(f"Circuit breaker {self.name} timeout")
                
            except Exception as e:
                # その他のエラー
                await self._record_failure(str(e))
                self.stats.failed_requests += 1
                raise CircuitBreakerException(f"Circuit breaker {self.name} failure: {e}")
    
    async def _can_execute(self) -> bool:
        """実行可能かチェック"""
        current_time = time.time()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        elif self.state == CircuitState.OPEN:
            # 回復タイムアウトをチェック
            if current_time - self.last_failure_time >= self.config.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                self.last_state_change = current_time
                logger.info(f"Circuit breaker {self.name} moved to half-open state")
                return True
            return False
        
        elif self.state == CircuitState.HALF_OPEN:
            # ハーフオープン状態では限定的に許可
            return True
        
        return False
    
    async def _record_success(self) -> None:
        """成功を記録"""
        current_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            # 成功閾値に達した場合、クローズ状態に戻る
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_state_change = current_time
                logger.info(f"Circuit breaker {self.name} moved to closed state")
        
        elif self.state == CircuitState.CLOSED:
            # クローズ状態では失敗カウントをリセット
            self.failure_count = 0
    
    async def _record_failure(self, error_message: str) -> None:
        """失敗を記録"""
        current_time = time.time()
        self.failure_count += 1
        self.last_failure_time = current_time
        self.stats.last_failure_time = current_time
        
        # リクエスト履歴に追加
        if self.config.monitoring_enabled:
            self.request_history.append({
                "timestamp": current_time,
                "success": False,
                "error": error_message
            })
            
            # 履歴サイズを制限
            if len(self.request_history) > self.config.metrics_window_size:
                self.request_history = self.request_history[-self.config.metrics_window_size:]
        
        # 失敗閾値に達した場合、オープン状態に移行
        if self.failure_count >= self.config.failure_threshold:
            if self.state != CircuitState.OPEN:
                self.state = CircuitState.OPEN
                self.last_state_change = current_time
                self.stats.circuit_breaker_trips += 1
                logger.warning(f"Circuit breaker {self.name} opened due to {self.failure_count} failures")
    
    def get_state(self) -> Dict[str, Any]:
        """現在の状態を取得"""
        current_time = time.time()
        
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_state_change": self.last_state_change,
            "time_in_current_state": current_time - self.last_state_change,
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        total_requests = self.stats.total_requests
        success_rate = (
            self.stats.successful_requests / max(1, total_requests) * 100
        )
        
        return {
            "name": self.name,
            "total_requests": total_requests,
            "successful_requests": self.stats.successful_requests,
            "failed_requests": self.stats.failed_requests,
            "timeout_requests": self.stats.timeout_requests,
            "success_rate": success_rate,
            "circuit_breaker_trips": self.stats.circuit_breaker_trips,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "current_state": self.state.value
        }
    
    def get_health_metrics(self) -> Dict[str, Any]:
        """ヘルスメトリクスを取得"""
        if not self.config.monitoring_enabled or not self.request_history:
            return {"status": "no_data"}
        
        current_time = time.time()
        window_start = current_time - 300  # 過去5分間
        
        # ウィンドウ内のリクエストをフィルタリング
        recent_requests = [
            req for req in self.request_history
            if req["timestamp"] >= window_start
        ]
        
        if not recent_requests:
            return {"status": "no_recent_data"}
        
        successful_recent = sum(1 for req in recent_requests if req["success"])
        total_recent = len(recent_requests)
        recent_success_rate = successful_recent / total_recent * 100
        
        # エラー分布
        error_distribution = {}
        for req in recent_requests:
            if not req["success"]:
                error = req["error"]
                error_distribution[error] = error_distribution.get(error, 0) + 1
        
        return {
            "status": "healthy" if recent_success_rate > 80 else "unhealthy",
            "recent_success_rate": recent_success_rate,
            "recent_requests": total_recent,
            "error_distribution": error_distribution,
            "current_state": self.state.value,
            "time_in_current_state": current_time - self.last_state_change
        }
    
    async def reset(self) -> None:
        """サーキットブレーカーをリセット"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = 0.0
            self.last_state_change = time.time()
            self.request_history.clear()
            
            # 統計をリセット
            self.stats = CircuitBreakerStats()
            
            logger.info(f"Circuit breaker {self.name} reset")


class CircuitBreakerOpenException(Exception):
    """サーキットブレーカーがオープン状態の例外"""
    pass


class CircuitBreakerTimeoutException(Exception):
    """サーキットブレーカーのタイムアウト例外"""
    pass


class CircuitBreakerException(Exception):
    """サーキットブレーカーの一般的な例外"""
    pass
