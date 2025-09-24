"""
サーキットブレーカー実装

API障害時の保護機能を提供するサーキットブレーカーを実装します。
"""

import time
from enum import Enum
from typing import Optional


class CircuitState(Enum):
    """サーキットブレーカーの状態"""
    CLOSED = "closed"      # 正常動作
    OPEN = "open"          # 障害発生、リクエスト拒否
    HALF_OPEN = "half_open"  # 復旧テスト中


class CircuitBreaker:
    """サーキットブレーカー"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception,
    ):
        """
        サーキットブレーカーを初期化
        
        Args:
            failure_threshold: 障害と判定する連続失敗回数
            recovery_timeout: 復旧テストまでの待機時間（秒）
            expected_exception: 監視する例外の種類
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
    
    def call(self, func, *args, **kwargs):
        """
        関数をサーキットブレーカー経由で実行
        
        Args:
            func: 実行する関数
            *args: 関数の引数
            **kwargs: 関数のキーワード引数
            
        Returns:
            関数の実行結果
            
        Raises:
            CircuitBreakerOpenException: サーキットブレーカーが開いている場合
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """復旧テストを試行すべきかチェック"""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """成功時の処理"""
        self.failure_count = 0
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # 復旧テストが成功した場合、サーキットを閉じる
            if self.success_count >= 3:  # 3回連続成功で復旧
                self.state = CircuitState.CLOSED
                self.success_count = 0
    
    def _on_failure(self) -> None:
        """失敗時の処理"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def get_state(self) -> CircuitState:
        """現在の状態を取得"""
        return self.state
    
    def get_failure_count(self) -> int:
        """失敗回数を取得"""
        return self.failure_count
    
    def get_success_count(self) -> int:
        """成功回数を取得"""
        return self.success_count
    
    def reset(self) -> None:
        """サーキットブレーカーをリセット"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None


class CircuitBreakerOpenException(Exception):
    """サーキットブレーカーが開いている場合の例外"""
    pass
