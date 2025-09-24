"""
サーキットブレーカーマネージャー

複数のサーキットブレーカーを管理します。
"""

import time
from typing import Dict, Optional, Any
from dataclasses import dataclass

from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitState


@dataclass
class CircuitBreakerStats:
    """サーキットブレーカー統計"""
    name: str
    state: CircuitState
    failure_count: int
    success_count: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    total_requests: int


class CircuitBreakerManager:
    """サーキットブレーカーマネージャー"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.stats: Dict[str, CircuitBreakerStats] = {}
    
    def create_circuit_breaker(
        self,
        name: str,
        config: CircuitBreakerConfig
    ) -> CircuitBreaker:
        """
        サーキットブレーカーを作成
        
        Args:
            name: サーキットブレーカー名
            config: 設定
            
        Returns:
            サーキットブレーカー
        """
        circuit_breaker = CircuitBreaker(config)
        self.circuit_breakers[name] = circuit_breaker
        
        # 統計を初期化
        self.stats[name] = CircuitBreakerStats(
            name=name,
            state=CircuitState.CLOSED,
            failure_count=0,
            success_count=0,
            last_failure_time=None,
            last_success_time=None,
            total_requests=0
        )
        
        return circuit_breaker
    
    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """
        サーキットブレーカーを取得
        
        Args:
            name: サーキットブレーカー名
            
        Returns:
            サーキットブレーカー、またはNone
        """
        return self.circuit_breakers.get(name)
    
    def remove_circuit_breaker(self, name: str) -> bool:
        """
        サーキットブレーカーを削除
        
        Args:
            name: サーキットブレーカー名
            
        Returns:
            削除が成功したかどうか
        """
        if name in self.circuit_breakers:
            del self.circuit_breakers[name]
            del self.stats[name]
            return True
        return False
    
    def execute_with_circuit_breaker(
        self,
        name: str,
        func: callable,
        *args,
        **kwargs
    ) -> Any:
        """
        サーキットブレーカーで関数を実行
        
        Args:
            name: サーキットブレーカー名
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
            
        Raises:
            Exception: サーキットブレーカーが開いている場合
        """
        circuit_breaker = self.get_circuit_breaker(name)
        if not circuit_breaker:
            raise ValueError(f"Circuit breaker '{name}' not found")
        
        # 統計を更新
        self.stats[name].total_requests += 1
        
        try:
            result = circuit_breaker.execute(func, *args, **kwargs)
            
            # 成功を記録
            self.stats[name].success_count += 1
            self.stats[name].last_success_time = time.time()
            self.stats[name].state = circuit_breaker.state
            
            return result
        
        except Exception as e:
            # 失敗を記録
            self.stats[name].failure_count += 1
            self.stats[name].last_failure_time = time.time()
            self.stats[name].state = circuit_breaker.state
            
            raise e
    
    def get_circuit_breaker_stats(self, name: str) -> Optional[CircuitBreakerStats]:
        """
        サーキットブレーカーの統計を取得
        
        Args:
            name: サーキットブレーカー名
            
        Returns:
            統計情報、またはNone
        """
        return self.stats.get(name)
    
    def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """
        すべての統計を取得
        
        Returns:
            統計情報の辞書
        """
        return self.stats.copy()
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        ヘルスサマリーを取得
        
        Returns:
            ヘルスサマリー
        """
        total_circuit_breakers = len(self.circuit_breakers)
        open_circuit_breakers = sum(
            1 for stats in self.stats.values()
            if stats.state == CircuitState.OPEN
        )
        half_open_circuit_breakers = sum(
            1 for stats in self.stats.values()
            if stats.state == CircuitState.HALF_OPEN
        )
        closed_circuit_breakers = sum(
            1 for stats in self.stats.values()
            if stats.state == CircuitState.CLOSED
        )
        
        return {
            "total_circuit_breakers": total_circuit_breakers,
            "open_circuit_breakers": open_circuit_breakers,
            "half_open_circuit_breakers": half_open_circuit_breakers,
            "closed_circuit_breakers": closed_circuit_breakers,
            "health_status": "healthy" if open_circuit_breakers == 0 else "degraded"
        }
    
    def reset_circuit_breaker(self, name: str) -> bool:
        """
        サーキットブレーカーをリセット
        
        Args:
            name: サーキットブレーカー名
            
        Returns:
            リセットが成功したかどうか
        """
        circuit_breaker = self.get_circuit_breaker(name)
        if not circuit_breaker:
            return False
        
        circuit_breaker.reset()
        
        # 統計をリセット
        if name in self.stats:
            self.stats[name].failure_count = 0
            self.stats[name].success_count = 0
            self.stats[name].last_failure_time = None
            self.stats[name].last_success_time = None
            self.stats[name].state = CircuitState.CLOSED
        
        return True
    
    def reset_all_circuit_breakers(self) -> int:
        """
        すべてのサーキットブレーカーをリセット
        
        Returns:
            リセットされたサーキットブレーカーの数
        """
        reset_count = 0
        
        for name in self.circuit_breakers:
            if self.reset_circuit_breaker(name):
                reset_count += 1
        
        return reset_count
