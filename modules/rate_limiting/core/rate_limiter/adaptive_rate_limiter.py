"""
適応的レート制限器

動的にレート制限を調整する適応的レート制限器を実装します。
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass

from .rate_limit_config import RateLimitConfig, RateLimitAlgorithm


@dataclass
class AdaptiveConfig:
    """適応的設定"""
    min_requests: int
    max_requests: int
    adjustment_factor: float
    success_threshold: float
    failure_threshold: float


class AdaptiveRateLimiter:
    """適応的レート制限器"""
    
    def __init__(self, config: RateLimitConfig, adaptive_config: AdaptiveConfig):
        self.config = config
        self.adaptive_config = adaptive_config
        self.current_requests = config.max_requests
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = time.time()
        self.adjustment_interval = 60.0  # 1分間隔で調整
    
    def is_allowed(self, key: str, tokens: int = 1) -> bool:
        """
        リクエストが許可されるかチェック
        
        Args:
            key: 制限キー
            tokens: トークン数
            
        Returns:
            許可されるかどうか
        """
        # 適応的調整を実行
        self._adaptive_adjustment()
        
        # 現在の制限でチェック
        return tokens <= self.current_requests
    
    def record_success(self) -> None:
        """成功を記録"""
        self.success_count += 1
        self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self) -> None:
        """失敗を記録"""
        self.failure_count += 1
        self.success_count = max(0, self.success_count - 1)
    
    def _adaptive_adjustment(self) -> None:
        """適応的調整を実行"""
        now = time.time()
        
        # 調整間隔をチェック
        if now - self.last_adjustment < self.adjustment_interval:
            return
        
        # 成功率を計算
        total_requests = self.success_count + self.failure_count
        if total_requests == 0:
            return
        
        success_rate = self.success_count / total_requests
        
        # 調整を実行
        if success_rate >= self.adaptive_config.success_threshold:
            # 成功率が高い場合は制限を緩和
            self.current_requests = min(
                self.adaptive_config.max_requests,
                int(self.current_requests * (1 + self.adaptive_config.adjustment_factor))
            )
        elif success_rate <= self.adaptive_config.failure_threshold:
            # 成功率が低い場合は制限を強化
            self.current_requests = max(
                self.adaptive_config.min_requests,
                int(self.current_requests * (1 - self.adaptive_config.adjustment_factor))
            )
        
        # 統計をリセット
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = now
    
    def get_remaining_tokens(self, key: str) -> int:
        """
        残りトークン数を取得
        
        Args:
            key: 制限キー
            
        Returns:
            残りトークン数
        """
        return self.current_requests
    
    def get_reset_time(self, key: str) -> float:
        """
        リセット時間を取得
        
        Args:
            key: 制限キー
            
        Returns:
            リセット時間
        """
        return self.last_adjustment + self.adjustment_interval
    
    def get_stats(self, key: str) -> Dict[str, any]:
        """
        統計情報を取得
        
        Args:
            key: 制限キー
            
        Returns:
            統計情報
        """
        total_requests = self.success_count + self.failure_count
        success_rate = self.success_count / total_requests if total_requests > 0 else 0.0
        
        return {
            "current_requests": self.current_requests,
            "min_requests": self.adaptive_config.min_requests,
            "max_requests": self.adaptive_config.max_requests,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": success_rate,
            "last_adjustment": self.last_adjustment,
            "next_adjustment": self.get_reset_time(key)
        }
