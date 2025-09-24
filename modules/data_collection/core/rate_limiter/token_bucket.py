"""
トークンバケット実装

レート制限のためのトークンバケットアルゴリズムを実装します。
"""

import time
from typing import Optional


class TokenBucket:
    """トークンバケット"""

    def __init__(self, capacity: int, refill_rate: float):
        """
        トークンバケットを初期化

        Args:
            capacity: バケットの容量（最大トークン数）
            refill_rate: 1秒あたりのトークン補充率
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        トークンを消費

        Args:
            tokens: 消費するトークン数

        Returns:
            トークンが消費できた場合True、そうでなければFalse
        """
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self) -> None:
        """トークンを補充"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now

    def get_tokens_available(self) -> int:
        """利用可能なトークン数を取得"""
        self._refill()
        return int(self.tokens)

    def get_time_until_refill(self) -> float:
        """次のトークン補充までの時間を取得"""
        if self.tokens >= self.capacity:
            return 0.0

        tokens_needed = 1
        return tokens_needed / self.refill_rate
