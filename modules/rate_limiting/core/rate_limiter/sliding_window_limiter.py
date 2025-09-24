"""
スライディングウィンドウ制限器

スライディングウィンドウアルゴリズムを使用したレート制限を実装します。
"""

import time
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass

from .rate_limit_config import RateLimitConfig


@dataclass
class WindowEntry:
    """ウィンドウエントリ"""
    timestamp: float
    count: int = 1


class SlidingWindowLimiter:
    """スライディングウィンドウ制限器"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.windows: Dict[str, deque] = {}
        self._lock = None  # 実際の実装ではasyncio.Lockを使用
    
    def is_allowed(self, key: str, tokens: int = 1) -> bool:
        """
        リクエストが許可されるかチェック
        
        Args:
            key: 制限キー
            tokens: トークン数
            
        Returns:
            許可されるかどうか
        """
        now = time.time()
        
        # ウィンドウを取得または作成
        if key not in self.windows:
            self.windows[key] = deque()
        
        window = self.windows[key]
        
        # 古いエントリを削除
        cutoff_time = now - self.config.window_size
        while window and window[0].timestamp <= cutoff_time:
            window.popleft()
        
        # 現在のリクエスト数を計算
        current_count = sum(entry.count for entry in window)
        
        # 制限をチェック
        if current_count + tokens <= self.config.max_requests:
            # 新しいエントリを追加
            window.append(WindowEntry(timestamp=now, count=tokens))
            return True
        
        return False
    
    def get_remaining_tokens(self, key: str) -> int:
        """
        残りトークン数を取得
        
        Args:
            key: 制限キー
            
        Returns:
            残りトークン数
        """
        now = time.time()
        
        if key not in self.windows:
            return self.config.max_requests
        
        window = self.windows[key]
        
        # 古いエントリを削除
        cutoff_time = now - self.config.window_size
        while window and window[0].timestamp <= cutoff_time:
            window.popleft()
        
        # 現在のリクエスト数を計算
        current_count = sum(entry.count for entry in window)
        
        return max(0, self.config.max_requests - current_count)
    
    def get_reset_time(self, key: str) -> float:
        """
        リセット時間を取得
        
        Args:
            key: 制限キー
            
        Returns:
            リセット時間
        """
        if key not in self.windows or not self.windows[key]:
            return time.time()
        
        oldest_entry = self.windows[key][0]
        return oldest_entry.timestamp + self.config.window_size
    
    def reset(self, key: str) -> None:
        """
        制限をリセット
        
        Args:
            key: 制限キー
        """
        if key in self.windows:
            del self.windows[key]
    
    def get_stats(self, key: str) -> Dict[str, any]:
        """
        統計情報を取得
        
        Args:
            key: 制限キー
            
        Returns:
            統計情報
        """
        now = time.time()
        
        if key not in self.windows:
            return {
                "current_requests": 0,
                "max_requests": self.config.max_requests,
                "window_size": self.config.window_size,
                "remaining_requests": self.config.max_requests,
                "reset_time": now
            }
        
        window = self.windows[key]
        
        # 古いエントリを削除
        cutoff_time = now - self.config.window_size
        while window and window[0].timestamp <= cutoff_time:
            window.popleft()
        
        current_requests = sum(entry.count for entry in window)
        
        return {
            "current_requests": current_requests,
            "max_requests": self.config.max_requests,
            "window_size": self.config.window_size,
            "remaining_requests": max(0, self.config.max_requests - current_requests),
            "reset_time": self.get_reset_time(key)
        }
