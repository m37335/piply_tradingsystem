"""
インテリジェントデータコレクター

レート制限を考慮した効率的なデータ収集機能を提供します。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from ...providers.base_provider import BaseDataProvider, TimeFrame, PriceData
from ...providers.yahoo_finance import YahooFinanceProvider
from ..rate_limiter.rate_limiter import RateLimitManager
from .priority_manager import PriorityManager
from .batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


class CollectionStrategy(Enum):
    """データ収集戦略"""
    PRIORITY_BASED = "priority_based"  # 優先度ベース
    BATCH_PROCESSING = "batch_processing"  # バッチ処理
    ADAPTIVE = "adaptive"  # 適応的


@dataclass
class CollectionTask:
    """データ収集タスク"""
    symbol: str
    timeframe: TimeFrame
    start_date: datetime
    end_date: datetime
    priority: int = 1  # 1-10 (10が最高優先度)
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class IntelligentDataCollector:
    """インテリジェントデータコレクター"""
    
    def __init__(
        self,
        rate_limit_manager: RateLimitManager,
        strategy: CollectionStrategy = CollectionStrategy.ADAPTIVE
    ):
        self.rate_limit_manager = rate_limit_manager
        self.strategy = strategy
        self.priority_manager = PriorityManager()
        self.batch_processor = BatchProcessor()
        
        # プロバイダー管理
        self.providers: Dict[str, BaseDataProvider] = {}
        self.fallback_providers: List[BaseDataProvider] = []
        
        # タスク管理
        self.pending_tasks: List[CollectionTask] = []
        self.completed_tasks: List[CollectionTask] = []
        self.failed_tasks: List[CollectionTask] = []
        
        # 統計情報
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'rate_limit_hits': 0,
            'fallback_usage': 0
        }
    
    def add_provider(self, name: str, provider: BaseDataProvider) -> None:
        """プロバイダーを追加"""
        self.providers[name] = provider
        
        # レート制限器を設定
        if hasattr(provider, 'set_rate_limiter'):
            limiter = self.rate_limit_manager.get_limiter(name)
            provider.set_rate_limiter(limiter)
    
    def add_fallback_provider(self, provider: BaseDataProvider) -> None:
        """フォールバックプロバイダーを追加"""
        self.fallback_providers.append(provider)
    
    async def collect_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        start_date: datetime,
        end_date: datetime,
        priority: int = 5
    ) -> List[PriceData]:
        """データを収集"""
        task = CollectionTask(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            priority=priority
        )
        
        return await self._execute_task(task)
    
    async def collect_batch_data(
        self,
        tasks: List[CollectionTask]
    ) -> Dict[str, List[PriceData]]:
        """バッチでデータを収集"""
        results = {}
        
        # タスクを優先度でソート
        sorted_tasks = self.priority_manager.sort_by_priority(tasks)
        
        # バッチ処理で実行
        for batch in self.batch_processor.create_batches(sorted_tasks, batch_size=10):
            batch_results = await self._execute_batch(batch)
            results.update(batch_results)
            
            # バッチ間の待機時間
            await asyncio.sleep(1)
        
        return results
    
    async def _execute_task(self, task: CollectionTask) -> List[PriceData]:
        """タスクを実行"""
        self.stats['total_requests'] += 1
        
        try:
            # メインプロバイダーで試行
            for provider_name, provider in self.providers.items():
                if not provider.is_available():
                    continue
                
                try:
                    # レート制限チェック
                    limiter = self.rate_limit_manager.get_limiter(provider_name)
                    if not await limiter.acquire():
                        self.stats['rate_limit_hits'] += 1
                        await limiter.wait_for_availability()
                    
                    # データ取得
                    result = await provider.get_historical_data(
                        task.symbol,
                        task.timeframe,
                        task.start_date,
                        task.end_date
                    )
                    
                    if result.success:
                        self.stats['successful_requests'] += 1
                        self.completed_tasks.append(task)
                        return result.data
                    else:
                        logger.warning(f"Provider {provider_name} failed: {result.error_message}")
                        
                except Exception as e:
                    logger.error(f"Provider {provider_name} error: {e}")
                    continue
            
            # フォールバックプロバイダーで試行
            for provider in self.fallback_providers:
                if not provider.is_available():
                    continue
                
                try:
                    result = await provider.get_historical_data(
                        task.symbol,
                        task.timeframe,
                        task.start_date,
                        task.end_date
                    )
                    
                    if result.success:
                        self.stats['successful_requests'] += 1
                        self.stats['fallback_usage'] += 1
                        self.completed_tasks.append(task)
                        return result.data
                        
                except Exception as e:
                    logger.error(f"Fallback provider error: {e}")
                    continue
            
            # すべてのプロバイダーが失敗
            self.stats['failed_requests'] += 1
            self.failed_tasks.append(task)
            return []
            
        except Exception as e:
            logger.error(f"Task execution error: {e}")
            self.stats['failed_requests'] += 1
            self.failed_tasks.append(task)
            return []
    
    async def _execute_batch(self, batch: List[CollectionTask]) -> Dict[str, List[PriceData]]:
        """バッチを実行"""
        results = {}
        
        # 並列実行
        tasks = [self._execute_task(task) for task in batch]
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                logger.error(f"Batch task {i} failed: {result}")
                results[batch[i].symbol] = []
            else:
                results[batch[i].symbol] = result
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self.stats,
            'pending_tasks': len(self.pending_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'success_rate': (
                self.stats['successful_requests'] / max(1, self.stats['total_requests'])
            ) * 100
        }
    
    async def health_check(self) -> Dict[str, bool]:
        """ヘルスチェック"""
        health_status = {}
        
        # プロバイダーのヘルスチェック
        for name, provider in self.providers.items():
            try:
                health_status[name] = await provider.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = False
        
        # フォールバックプロバイダーのヘルスチェック
        for i, provider in enumerate(self.fallback_providers):
            try:
                health_status[f"fallback_{i}"] = await provider.health_check()
            except Exception as e:
                logger.error(f"Fallback health check failed: {e}")
                health_status[f"fallback_{i}"] = False
        
        return health_status
