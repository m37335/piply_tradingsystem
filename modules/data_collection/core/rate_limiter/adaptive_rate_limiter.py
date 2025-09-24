"""
適応的レート制限器実装

成功率に基づいてレート制限を動的に調整する適応的レート制限器を実装します。
"""

import time
from typing import Optional

from .token_bucket import TokenBucket


class AdaptiveRateLimiter:
    """適応的レート制限器"""
    
    def __init__(
        self,
        initial_capacity: int,
        initial_refill_rate: float,
        min_refill_rate: float = 0.1,
        max_refill_rate: float = 10.0,
        adjustment_factor: float = 0.1,
        success_threshold: float = 0.8,
    ):
        """
        適応的レート制限器を初期化
        
        Args:
            initial_capacity: 初期バケット容量
            initial_refill_rate: 初期補充率
            min_refill_rate: 最小補充率
            max_refill_rate: 最大補充率
            adjustment_factor: 調整係数
            success_threshold: 成功率の閾値
        """
        self.token_bucket = TokenBucket(initial_capacity, initial_refill_rate)
        self.min_refill_rate = min_refill_rate
        self.max_refill_rate = max_refill_rate
        self.adjustment_factor = adjustment_factor
        self.success_threshold = success_threshold
        
        # 統計情報
        self.total_requests = 0
        self.successful_requests = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60  # 1分間隔で調整
    
    def consume(self, tokens: int = 1) -> bool:
        """
        トークンを消費
        
        Args:
            tokens: 消費するトークン数
            
        Returns:
            トークンが消費できた場合True、そうでなければFalse
        """
        self.total_requests += 1
        
        if self.token_bucket.consume(tokens):
            self.successful_requests += 1
            self._adjust_rate_if_needed()
            return True
        
        self._adjust_rate_if_needed()
        return False
    
    def record_success(self) -> None:
        """成功を記録"""
        self.successful_requests += 1
        self.total_requests += 1
        self._adjust_rate_if_needed()
    
    def record_failure(self) -> None:
        """失敗を記録"""
        self.total_requests += 1
        self._adjust_rate_if_needed()
    
    def _adjust_rate_if_needed(self) -> None:
        """必要に応じてレートを調整"""
        now = time.time()
        
        if now - self.last_adjustment < self.adjustment_interval:
            return
        
        if self.total_requests == 0:
            return
        
        success_rate = self.successful_requests / self.total_requests
        
        if success_rate > self.success_threshold:
            # 成功率が高い場合、レートを上げる
            new_rate = min(
                self.max_refill_rate,
                self.token_bucket.refill_rate * (1 + self.adjustment_factor)
            )
        else:
            # 成功率が低い場合、レートを下げる
            new_rate = max(
                self.min_refill_rate,
                self.token_bucket.refill_rate * (1 - self.adjustment_factor)
            )
        
        self.token_bucket.refill_rate = new_rate
        self.last_adjustment = now
        
        # 統計をリセット
        self.total_requests = 0
        self.successful_requests = 0
    
    def get_tokens_available(self) -> int:
        """利用可能なトークン数を取得"""
        return self.token_bucket.get_tokens_available()
    
    def get_refill_rate(self) -> float:
        """現在の補充率を取得"""
        return self.token_bucket.refill_rate
    
    def get_success_rate(self) -> float:
        """現在の成功率を取得"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
