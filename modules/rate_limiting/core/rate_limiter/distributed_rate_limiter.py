"""
分散レート制限器

分散環境でのレート制限を実装します。
"""

import time
from typing import Dict, Optional, Any
from dataclasses import dataclass

from .rate_limit_config import RateLimitConfig


@dataclass
class DistributedConfig:
    """分散設定"""
    node_id: str
    sync_interval: float
    max_drift: float


class DistributedRateLimiter:
    """分散レート制限器"""
    
    def __init__(self, config: RateLimitConfig, distributed_config: DistributedConfig):
        self.config = config
        self.distributed_config = distributed_config
        self.local_requests: Dict[str, int] = {}
        self.last_sync = time.time()
        self.sync_data: Dict[str, Any] = {}
    
    def is_allowed(self, key: str, tokens: int = 1) -> bool:
        """
        リクエストが許可されるかチェック
        
        Args:
            key: 制限キー
            tokens: トークン数
            
        Returns:
            許可されるかどうか
        """
        # 同期を実行
        self._sync_if_needed()
        
        # ローカルリクエスト数を取得
        local_count = self.local_requests.get(key, 0)
        
        # 分散リクエスト数を取得
        distributed_count = self._get_distributed_count(key)
        
        # 制限をチェック
        total_count = local_count + distributed_count
        if total_count + tokens <= self.config.max_requests:
            # ローカルリクエスト数を更新
            self.local_requests[key] = local_count + tokens
            return True
        
        return False
    
    def _sync_if_needed(self) -> None:
        """必要に応じて同期を実行"""
        now = time.time()
        
        if now - self.last_sync >= self.distributed_config.sync_interval:
            self._sync_with_other_nodes()
            self.last_sync = now
    
    def _sync_with_other_nodes(self) -> None:
        """他のノードと同期"""
        # 実際の実装では、Redisやデータベースを使用して同期
        # ここでは簡易実装
        pass
    
    def _get_distributed_count(self, key: str) -> int:
        """
        分散リクエスト数を取得
        
        Args:
            key: 制限キー
            
        Returns:
            分散リクエスト数
        """
        # 実際の実装では、他のノードからのリクエスト数を取得
        # ここでは簡易実装
        return 0
    
    def get_remaining_tokens(self, key: str) -> int:
        """
        残りトークン数を取得
        
        Args:
            key: 制限キー
            
        Returns:
            残りトークン数
        """
        self._sync_if_needed()
        
        local_count = self.local_requests.get(key, 0)
        distributed_count = self._get_distributed_count(key)
        total_count = local_count + distributed_count
        
        return max(0, self.config.max_requests - total_count)
    
    def get_reset_time(self, key: str) -> float:
        """
        リセット時間を取得
        
        Args:
            key: 制限キー
            
        Returns:
            リセット時間
        """
        return time.time() + self.config.window_size
    
    def get_stats(self, key: str) -> Dict[str, any]:
        """
        統計情報を取得
        
        Args:
            key: 制限キー
            
        Returns:
            統計情報
        """
        self._sync_if_needed()
        
        local_count = self.local_requests.get(key, 0)
        distributed_count = self._get_distributed_count(key)
        total_count = local_count + distributed_count
        
        return {
            "local_requests": local_count,
            "distributed_requests": distributed_count,
            "total_requests": total_count,
            "max_requests": self.config.max_requests,
            "remaining_requests": max(0, self.config.max_requests - total_count),
            "node_id": self.distributed_config.node_id,
            "last_sync": self.last_sync
        }
