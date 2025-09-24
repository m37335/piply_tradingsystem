"""
リーキーバケット実装

レート制限のためのリーキーバケットアルゴリズムを実装します。
"""

import time
from typing import Optional


class LeakyBucket:
    """リーキーバケット"""
    
    def __init__(self, capacity: int, leak_rate: float):
        """
        リーキーバケットを初期化
        
        Args:
            capacity: バケットの容量（最大リクエスト数）
            leak_rate: 1秒あたりのリーク率
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.level = 0
        self.last_leak = time.time()
    
    def add_request(self) -> bool:
        """
        リクエストを追加
        
        Returns:
            リクエストが追加できた場合True、そうでなければFalse
        """
        self._leak()
        
        if self.level < self.capacity:
            self.level += 1
            return True
        return False
    
    def _leak(self) -> None:
        """バケットからリーク"""
        now = time.time()
        time_passed = now - self.last_leak
        leaked = time_passed * self.leak_rate
        
        self.level = max(0, self.level - leaked)
        self.last_leak = now
    
    def get_level(self) -> int:
        """現在のバケットレベルを取得"""
        self._leak()
        return int(self.level)
    
    def get_time_until_available(self) -> float:
        """次のリクエストが利用可能になるまでの時間を取得"""
        if self.level < self.capacity:
            return 0.0
        
        return 1.0 / self.leak_rate
