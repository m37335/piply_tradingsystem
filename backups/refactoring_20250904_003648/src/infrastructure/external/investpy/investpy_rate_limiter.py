"""
investpyレート制限
investpyライブラリのAPI呼び出し制限を管理
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional


class InvestpyRateLimiter:
    """investpyレート制限"""
    
    def __init__(self, max_requests_per_minute: int = 30):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_requests_per_minute = max_requests_per_minute
        self.request_times: list = []
        self.last_request_time: Optional[datetime] = None
    
    async def wait_if_needed(self) -> None:
        """
        必要に応じて待機
        
        レート制限に達している場合は適切な時間待機
        """
        now = datetime.now()
        
        # 1分以上前のリクエストを削除
        self.request_times = [
            req_time for req_time in self.request_times
            if now - req_time < timedelta(minutes=1)
        ]
        
        # レート制限チェック
        if len(self.request_times) >= self.max_requests_per_minute:
            wait_time = self._calculate_wait_time()
            self.logger.info(f"Rate limit reached. Waiting {wait_time} seconds")
            await asyncio.sleep(wait_time)
        
        # リクエスト時間を記録
        self.request_times.append(now)
        self.last_request_time = now
    
    def _calculate_wait_time(self) -> float:
        """
        待機時間を計算
        
        Returns:
            float: 待機時間（秒）
        """
        if not self.request_times:
            return 0.0
        
        # 最も古いリクエストから1分経過するまでの時間
        oldest_request = min(self.request_times)
        wait_until = oldest_request + timedelta(minutes=1)
        wait_time = (wait_until - datetime.now()).total_seconds()
        
        return max(wait_time, 0.0)
    
    def get_rate_limit_status(self) -> dict:
        """
        レート制限の状態を取得
        
        Returns:
            dict: レート制限の状態
        """
        now = datetime.now()
        
        # 1分以内のリクエスト数をカウント
        recent_requests = [
            req_time for req_time in self.request_times
            if now - req_time < timedelta(minutes=1)
        ]
        
        return {
            "current_requests": len(recent_requests),
            "max_requests": self.max_requests_per_minute,
            "remaining_requests": max(
                0, self.max_requests_per_minute - len(recent_requests)
            ),
            "last_request_time": (
                self.last_request_time.isoformat() if self.last_request_time else None
            )
        }
    
    def is_rate_limited(self) -> bool:
        """
        レート制限されているかどうかを判定
        
        Returns:
            bool: レート制限されている場合True
        """
        now = datetime.now()
        recent_requests = [
            req_time for req_time in self.request_times
            if now - req_time < timedelta(minutes=1)
        ]
        
        return len(recent_requests) >= self.max_requests_per_minute
