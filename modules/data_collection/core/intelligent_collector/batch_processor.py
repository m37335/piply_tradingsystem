"""
バッチ処理システム

データ収集のバッチ処理を管理します。
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Callable
from collections import defaultdict


@dataclass
class BatchItem:
    """バッチアイテム"""
    item_id: str
    data: Any
    priority: int = 1
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class BatchConfig:
    """バッチ設定"""
    max_batch_size: int = 100
    max_wait_time: float = 30.0  # 秒
    min_batch_size: int = 1
    priority_threshold: int = 5


class BatchProcessor:
    """バッチ処理システム"""
    
    def __init__(self, config: BatchConfig):
        self.config = config
        self.batches: Dict[str, List[BatchItem]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.processors: Dict[str, Callable] = {}
        self._lock = asyncio.Lock()
    
    def register_processor(self, batch_type: str, processor: Callable) -> None:
        """
        バッチプロセッサーを登録
        
        Args:
            batch_type: バッチタイプ
            processor: プロセッサー関数
        """
        self.processors[batch_type] = processor
    
    async def add_item(
        self,
        batch_type: str,
        item_id: str,
        data: Any,
        priority: int = 1,
    ) -> None:
        """
        バッチにアイテムを追加
        
        Args:
            batch_type: バッチタイプ
            item_id: アイテムID
            data: データ
            priority: 優先度
        """
        async with self._lock:
            item = BatchItem(
                item_id=item_id,
                data=data,
                priority=priority,
            )
            
            self.batches[batch_type].append(item)
            
            # バッチが満杯になった場合、即座に処理
            if len(self.batches[batch_type]) >= self.config.max_batch_size:
                await self._process_batch(batch_type)
            else:
                # タイマーを設定（まだ設定されていない場合）
                if batch_type not in self.batch_timers:
                    self.batch_timers[batch_type] = asyncio.create_task(
                        self._wait_and_process(batch_type)
                    )
    
    async def _wait_and_process(self, batch_type: str) -> None:
        """
        待機してからバッチを処理
        
        Args:
            batch_type: バッチタイプ
        """
        try:
            await asyncio.sleep(self.config.max_wait_time)
            async with self._lock:
                if batch_type in self.batches and self.batches[batch_type]:
                    await self._process_batch(batch_type)
        finally:
            # タイマーをクリーンアップ
            if batch_type in self.batch_timers:
                del self.batch_timers[batch_type]
    
    async def _process_batch(self, batch_type: str) -> None:
        """
        バッチを処理
        
        Args:
            batch_type: バッチタイプ
        """
        if batch_type not in self.batches or not self.batches[batch_type]:
            return
        
        # 最小バッチサイズをチェック
        if len(self.batches[batch_type]) < self.config.min_batch_size:
            return
        
        # バッチを取得してクリア
        batch_items = self.batches[batch_type].copy()
        self.batches[batch_type].clear()
        
        # タイマーをキャンセル
        if batch_type in self.batch_timers:
            self.batch_timers[batch_type].cancel()
            del self.batch_timers[batch_type]
        
        # プロセッサーが登録されている場合、処理を実行
        if batch_type in self.processors:
            try:
                processor = self.processors[batch_type]
                await processor(batch_items)
            except Exception as e:
                # エラーが発生した場合、アイテムを元に戻す
                self.batches[batch_type].extend(batch_items)
                raise e
    
    async def force_process(self, batch_type: str) -> None:
        """
        バッチを強制処理
        
        Args:
            batch_type: バッチタイプ
        """
        async with self._lock:
            await self._process_batch(batch_type)
    
    async def force_process_all(self) -> None:
        """すべてのバッチを強制処理"""
        async with self._lock:
            for batch_type in list(self.batches.keys()):
                await self._process_batch(batch_type)
    
    def get_batch_size(self, batch_type: str) -> int:
        """
        バッチサイズを取得
        
        Args:
            batch_type: バッチタイプ
            
        Returns:
            バッチサイズ
        """
        return len(self.batches.get(batch_type, []))
    
    def get_batch_info(self, batch_type: str) -> Dict[str, any]:
        """
        バッチ情報を取得
        
        Args:
            batch_type: バッチタイプ
            
        Returns:
            バッチ情報
        """
        batch_items = self.batches.get(batch_type, [])
        
        if not batch_items:
            return {
                "size": 0,
                "oldest_item_age": 0.0,
                "average_priority": 0.0,
                "has_timer": False,
            }
        
        current_time = time.time()
        oldest_item = min(batch_items, key=lambda x: x.created_at)
        average_priority = sum(item.priority for item in batch_items) / len(batch_items)
        
        return {
            "size": len(batch_items),
            "oldest_item_age": current_time - oldest_item.created_at,
            "average_priority": average_priority,
            "has_timer": batch_type in self.batch_timers,
        }
    
    def get_all_batch_info(self) -> Dict[str, Dict[str, any]]:
        """
        すべてのバッチ情報を取得
        
        Returns:
            すべてのバッチ情報
        """
        return {
            batch_type: self.get_batch_info(batch_type)
            for batch_type in self.batches.keys()
        }
    
    def clear_batch(self, batch_type: str) -> int:
        """
        バッチをクリア
        
        Args:
            batch_type: バッチタイプ
            
        Returns:
            クリアされたアイテム数
        """
        if batch_type not in self.batches:
            return 0
        
        item_count = len(self.batches[batch_type])
        self.batches[batch_type].clear()
        
        # タイマーもキャンセル
        if batch_type in self.batch_timers:
            self.batch_timers[batch_type].cancel()
            del self.batch_timers[batch_type]
        
        return item_count
    
    def clear_all_batches(self) -> Dict[str, int]:
        """
        すべてのバッチをクリア
        
        Returns:
            バッチタイプごとのクリアされたアイテム数
        """
        cleared_counts = {}
        
        for batch_type in list(self.batches.keys()):
            cleared_counts[batch_type] = self.clear_batch(batch_type)
        
        return cleared_counts
    
    def get_statistics(self) -> Dict[str, any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        total_items = sum(len(batch) for batch in self.batches.values())
        total_batches = len(self.batches)
        active_timers = len(self.batch_timers)
        
        return {
            "total_items": total_items,
            "total_batches": total_batches,
            "active_timers": active_timers,
            "registered_processors": len(self.processors),
            "batch_info": self.get_all_batch_info(),
        }
    
    async def wait_for_empty(self, timeout: Optional[float] = None) -> bool:
        """
        すべてのバッチが空になるまで待機
        
        Args:
            timeout: タイムアウト（秒）
            
        Returns:
            タイムアウトせずに完了したかどうか
        """
        start_time = time.time()
        
        while True:
            # すべてのバッチが空かチェック
            if not any(self.batches.values()):
                return True
            
            # タイムアウトチェック
            if timeout and (time.time() - start_time) > timeout:
                return False
            
            await asyncio.sleep(0.1)
    
    def update_config(self, new_config: BatchConfig) -> None:
        """
        設定を更新
        
        Args:
            new_config: 新しい設定
        """
        self.config = new_config
    
    def get_config(self) -> BatchConfig:
        """
        現在の設定を取得
        
        Returns:
            現在の設定
        """
        return self.config
