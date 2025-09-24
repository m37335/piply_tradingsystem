"""
スライディングウィンドウ実装

レート制限のためのスライディングウィンドウアルゴリズムを実装します。
"""

import time
from collections import deque
from typing import Optional


class SlidingWindow:
    """スライディングウィンドウ"""
    
    def __init__(self, window_size: int, max_requests: int):
        """
        スライディングウィンドウを初期化
        
        Args:
            window_size: ウィンドウサイズ（秒）
            max_requests: ウィンドウ内の最大リクエスト数
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests = deque()
    
    def add_request(self) -> bool:
        """
        リクエストを追加
        
        Returns:
            リクエストが追加できた場合True、そうでなければFalse
        """
        now = time.time()
        
        # 古いリクエストを削除
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        # リクエスト数をチェック
        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False
    
    def get_requests_count(self) -> int:
        """現在のウィンドウ内のリクエスト数を取得"""
        now = time.time()
        
        # 古いリクエストを削除
        while self.requests and self.requests[0] <= now - self.window_size:
            self.requests.popleft()
        
        return len(self.requests)
    
    def get_time_until_reset(self) -> float:
        """ウィンドウがリセットされるまでの時間を取得"""
        if not self.requests:
            return 0.0
        
        oldest_request = self.requests[0]
        return max(0.0, self.window_size - (time.time() - oldest_request))
