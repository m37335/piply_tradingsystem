"""
スケジューラーサービス

タスクスケジューリングの統合サービスを提供します。
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import time

from ..config.settings import SchedulerSettings, TaskPriority, TaskStatus, MarketStatus
from ..core.market_aware_scheduler.market_hours_manager import MarketHoursManager
from ..core.task_scheduler.task_scheduler import TaskScheduler
from ..core.task_scheduler.data_collection_tasks import DataCollectionTasks

logger = logging.getLogger(__name__)


class SchedulerService:
    """スケジューラーサービス"""
    
    def __init__(self, settings: SchedulerSettings):
        self.settings = settings
        self.market_hours_manager = MarketHoursManager(settings.market_hours)
        self.task_scheduler = TaskScheduler(settings.task_scheduler)
        self.data_collection_tasks = DataCollectionTasks(settings.data_collection)
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self) -> None:
        """サービスを開始"""
        if self._running:
            logger.warning("Scheduler service is already running")
            return
        
        try:
            # タスクスケジューラーを開始
            await self.task_scheduler.start()
            
            # データ収集タスクを登録
            await self._register_data_collection_tasks()
            
            # サービスを開始
            self._running = True
            
            # メインループを開始
            main_task = asyncio.create_task(self._main_loop())
            self._tasks.append(main_task)
            
            logger.info("Scheduler service started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler service: {e}")
            await self.stop()
            raise
    
    async def stop(self) -> None:
        """サービスを停止"""
        if not self._running:
            return
        
        self._running = False
        
        # 実行中のタスクをキャンセル
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # タスクの完了を待機
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        
        # タスクスケジューラーを停止
        await self.task_scheduler.stop()
        
        logger.info("Scheduler service stopped")
    
    async def _main_loop(self) -> None:
        """メインループ"""
        logger.info("Scheduler main loop started")
        
        while self._running:
            try:
                # 市場状況をチェック
                market_status = await self.market_hours_manager.get_market_status()
                
                # 市場状況に応じてタスクを調整
                await self._adjust_tasks_for_market_status(market_status)
                
                # タスクスケジューラーの状態をチェック
                await self._check_scheduler_health()
                
                # 次のチェックまで待機
                await asyncio.sleep(60)  # 1分間隔
                
            except asyncio.CancelledError:
                logger.info("Scheduler main loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler main loop: {e}")
                await asyncio.sleep(30)  # エラー時は30秒待機
    
    async def _register_data_collection_tasks(self) -> None:
        """データ収集タスクを登録"""
        logger.info("Registering data collection tasks")
        
        # 継続的データ収集タスク
        for symbol in self.settings.data_collection.symbols:
            for timeframe in self.settings.data_collection.timeframes:
                task_name = f"data_collection_{symbol}_{timeframe}"
                
                # タスクを登録
                await self.task_scheduler.schedule_task(
                    name=task_name,
                    func=self.data_collection_tasks.collect_latest_data,
                    args=(symbol, timeframe),
                    interval_seconds=self.settings.data_collection.collection_interval_seconds,
                    priority=self.settings.data_collection.priority,
                    market_aware=self.settings.data_collection.market_aware
                )
                
                logger.info(f"Registered task: {task_name}")
        
        # バックフィルタスク（日次）
        backfill_task_name = "data_collection_backfill"
        await self.task_scheduler.schedule_task(
            name=backfill_task_name,
            func=self.data_collection_tasks.run_daily_backfill,
            args=(),
            interval_seconds=86400,  # 24時間
            priority=TaskPriority.NORMAL,
            market_aware=False  # バックフィルは市場時間に関係なく実行
        )
        
        logger.info(f"Registered task: {backfill_task_name}")
    
    async def _adjust_tasks_for_market_status(self, market_status: MarketStatus) -> None:
        """市場状況に応じてタスクを調整"""
        if not self.settings.enable_market_aware_scheduling:
            return
        
        if market_status == MarketStatus.OPEN:
            # 市場が開いている間は高頻度でデータ収集
            await self._adjust_collection_frequency(300)  # 5分間隔
        elif market_status == MarketStatus.PRE_MARKET:
            # プレマーケット中は中頻度でデータ収集
            await self._adjust_collection_frequency(600)  # 10分間隔
        elif market_status == MarketStatus.AFTER_HOURS:
            # アフターハワーズ中は低頻度でデータ収集
            await self._adjust_collection_frequency(1800)  # 30分間隔
        else:  # CLOSED, HOLIDAY
            # 市場が閉まっている間は最小限のデータ収集
            await self._adjust_collection_frequency(3600)  # 1時間間隔
    
    async def _adjust_collection_frequency(self, interval_seconds: int) -> None:
        """データ収集頻度を調整"""
        for symbol in self.settings.data_collection.symbols:
            for timeframe in self.settings.data_collection.timeframes:
                task_name = f"data_collection_{symbol}_{timeframe}"
                
                # タスクの間隔を更新
                await self.task_scheduler.update_task_interval(task_name, interval_seconds)
    
    async def _check_scheduler_health(self) -> None:
        """スケジューラーのヘルスチェック"""
        try:
            # タスクスケジューラーの統計を取得
            stats = await self.task_scheduler.get_stats()
            
            # 失敗したタスクがある場合は警告
            if stats.get("failed_tasks", 0) > 0:
                logger.warning(f"Scheduler has {stats['failed_tasks']} failed tasks")
            
            # 実行中のタスク数が上限に近い場合は警告
            max_concurrent = self.settings.task_scheduler.max_concurrent_tasks
            running_tasks = stats.get("running_tasks", 0)
            if running_tasks > max_concurrent * 0.8:
                logger.warning(f"Scheduler has {running_tasks} running tasks (limit: {max_concurrent})")
                
        except Exception as e:
            logger.error(f"Error checking scheduler health: {e}")
    
    async def schedule_custom_task(
        self,
        name: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        market_aware: bool = False
    ) -> None:
        """カスタムタスクをスケジュール"""
        if kwargs is None:
            kwargs = {}
        
        await self.task_scheduler.schedule_task(
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            priority=priority,
            market_aware=market_aware
        )
        
        logger.info(f"Custom task scheduled: {name}")
    
    async def cancel_task(self, name: str) -> None:
        """タスクをキャンセル"""
        await self.task_scheduler.cancel_task(name)
        logger.info(f"Task cancelled: {name}")
    
    async def get_task_status(self, name: str) -> Dict[str, Any]:
        """タスクのステータスを取得"""
        return await self.task_scheduler.get_task_status(name)
    
    async def get_all_tasks_status(self) -> Dict[str, Any]:
        """すべてのタスクのステータスを取得"""
        return await self.task_scheduler.get_all_tasks_status()
    
    async def get_market_status(self) -> Dict[str, Any]:
        """市場状況を取得"""
        market_status = await self.market_hours_manager.get_market_status()
        market_info = await self.market_hours_manager.get_market_info()
        
        return {
            "status": market_status.value,
            "info": market_info
        }
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """スケジューラーの統計を取得"""
        task_stats = await self.task_scheduler.get_stats()
        market_status = await self.get_market_status()
        
        return {
            "service_running": self._running,
            "active_tasks": len(self._tasks),
            "task_scheduler": task_stats,
            "market_status": market_status,
            "settings": self.settings.to_dict()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        try:
            # タスクスケジューラーのヘルスチェック
            scheduler_health = await self.task_scheduler.health_check()
            
            # 市場時間管理のヘルスチェック
            market_health = await self.market_hours_manager.health_check()
            
            # 全体のヘルス状態を決定
            overall_health = "healthy"
            if scheduler_health.get("status") != "healthy":
                overall_health = "unhealthy"
            elif market_health.get("status") != "healthy":
                overall_health = "degraded"
            
            return {
                "status": overall_health,
                "service_running": self._running,
                "scheduler": scheduler_health,
                "market_hours": market_health,
                "active_tasks": len(self._tasks)
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def trigger_manual_task(self, name: str) -> Dict[str, Any]:
        """手動でタスクを実行"""
        try:
            result = await self.task_scheduler.trigger_task(name)
            return {
                "success": True,
                "task_name": name,
                "result": result
            }
        except Exception as e:
            logger.error(f"Failed to trigger manual task {name}: {e}")
            return {
                "success": False,
                "task_name": name,
                "error": str(e)
            }
    
    async def get_task_history(self, name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """タスクの履歴を取得"""
        return await self.task_scheduler.get_task_history(name, limit)
    
    async def cleanup_old_tasks(self) -> None:
        """古いタスクをクリーンアップ"""
        await self.task_scheduler.cleanup_old_tasks()
        logger.info("Old tasks cleaned up")
