"""
キャッシュフォールバック

キャッシュを使用したフォールバック戦略を実装します。
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass

from .fallback_config import FallbackConfig, FallbackStrategy


@dataclass
class CacheEntry:
    """キャッシュエントリ"""
    data: Any
    timestamp: float
    ttl: float
    access_count: int = 0


class CacheFallback:
    """キャッシュフォールバック"""
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        self.cache: Dict[str, CacheEntry] = {}
        self.max_cache_size = config.max_cache_size
        self.default_ttl = config.cache_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        キャッシュからデータを取得
        
        Args:
            key: キャッシュキー
            
        Returns:
            キャッシュされたデータ、またはNone
        """
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        
        # TTLチェック
        if time.time() - entry.timestamp > entry.ttl:
            del self.cache[key]
            return None
        
        # アクセス回数を増加
        entry.access_count += 1
        
        return entry.data
    
    def set(self, key: str, data: Any, ttl: Optional[float] = None) -> None:
        """
        キャッシュにデータを設定
        
        Args:
            key: キャッシュキー
            data: データ
            ttl: 有効期限（秒）
        """
        if ttl is None:
            ttl = self.default_ttl
        
        # キャッシュサイズ制限をチェック
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()
        
        entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            ttl=ttl
        )
        
        self.cache[key] = entry
    
    def delete(self, key: str) -> bool:
        """
        キャッシュからデータを削除
        
        Args:
            key: キャッシュキー
            
        Returns:
            削除が成功したかどうか
        """
        if key in self.cache:
            del self.cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """キャッシュをクリア"""
        self.cache.clear()
    
    def _evict_oldest(self) -> None:
        """最も古いエントリを削除"""
        if not self.cache:
            return
        
        # 最も古いエントリを検索
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k].timestamp)
        del self.cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        total_entries = len(self.cache)
        total_accesses = sum(entry.access_count for entry in self.cache.values())
        avg_accesses = total_accesses / total_entries if total_entries > 0 else 0.0
        
        # 有効期限切れのエントリ数をカウント
        now = time.time()
        expired_entries = sum(
            1 for entry in self.cache.values()
            if now - entry.timestamp > entry.ttl
        )
        
        return {
            "total_entries": total_entries,
            "max_cache_size": self.max_cache_size,
            "total_accesses": total_accesses,
            "average_accesses": avg_accesses,
            "expired_entries": expired_entries,
            "cache_hit_rate": 0.0  # 実際の実装では計算
        }
    
    def cleanup_expired(self) -> int:
        """
        有効期限切れのエントリをクリーンアップ
        
        Returns:
            削除されたエントリ数
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if now - entry.timestamp > entry.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        return len(expired_keys)
