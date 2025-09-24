"""
メインタスクスケジューラー

タスクのスケジューリング、実行、管理を統合的に行います。
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
import heapq

from .scheduled_task import ScheduledTask, TaskStatus, TaskPriority, TaskType, TaskResult
from .task_executor import TaskExecutor

logger = logging.getLogger(__name__)


@dataclass
class SchedulerStats:
    """スケジューラー統計"""
    total_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    uptime_seconds: float = 0.0
    start_time: Optional[datetime] = None


class TaskScheduler:
    """メインタスクスケジューラー"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.executor = TaskExecutor(max_concurrent_tasks)
        self.tasks: Dict[str, ScheduledTask] = {}
        self.task_queue: List[ScheduledTask] = []  # 優先度付きキュー
        self.stats = SchedulerStats()
        self._running = False
        self._shutdown = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        # 市場時間設定
        self.market_hours = {
            "monday": {"open": "09:00", "close": "17:00"},
            "tuesday": {"open": "09:00", "close": "17:00"},
            "wednesday": {"open": "09:00", "close": "17:00"},
            "thursday": {"open": "09:00", "close": "17:00"},
            "friday": {"open": "09:00", "close": "17:00"},
            "saturday": {"open": "09:00", "close": "15:00"},
            "sunday": {"open": "09:00", "close": "15:00"}
        }
    
    async def start(self) -> None:
        """スケジューラーを開始"""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info("Starting task scheduler...")
        self._running = True
        self._shutdown = False
        self.stats.start_time = datetime.now()
        
        # スケジューラータスクを開始
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        logger.info("Task scheduler started")
    
    async def stop(self) -> None:
        """スケジューラーを停止"""
        if not self._running:
            logger.warning("Scheduler is not running")
            return
        
        logger.info("Stopping task scheduler...")
        self._shutdown = True
        self._running = False
        
        # スケジューラータスクをキャンセル
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        
        # 実行エンジンをシャットダウン
        await self.executor.shutdown()
        
        logger.info("Task scheduler stopped")
    
    async def add_task(
        self,
        task_type: TaskType,
        name: str,
        function: Callable,
        scheduled_time: datetime,
        description: str = "",
        args: tuple = (),
        kwargs: Dict[str, Any] = None,
        interval: Optional[timedelta] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout: Optional[timedelta] = None,
        market_hours_only: bool = False,
        skip_weekends: bool = True,
        skip_holidays: bool = True
    ) -> str:
        """タスクを追加"""
        if kwargs is None:
            kwargs = {}
        
        task = ScheduledTask(
            task_id="",  # 自動生成
            task_type=task_type,
            name=name,
            description=description,
            function=function,
            args=args,
            kwargs=kwargs,
            scheduled_time=scheduled_time,
            interval=interval,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            market_hours_only=market_hours_only,
            skip_weekends=skip_weekends,
            skip_holidays=skip_holidays
        )
        
        self.tasks[task.task_id] = task
        self.stats.total_tasks += 1
        self.stats.pending_tasks += 1
        
        # 優先度付きキューに追加
        heapq.heappush(self.task_queue, (-task.priority.value, task.scheduled_time, task))
        
        logger.info(f"Task added: {task.task_id} - {name}")
        return task.task_id
    
    async def remove_task(self, task_id: str) -> bool:
        """タスクを削除"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        task.cancel()
        
        # キューから削除
        self.task_queue = [
            item for item in self.task_queue 
            if item[2].task_id != task_id
        ]
        heapq.heapify(self.task_queue)
        
        del self.tasks[task_id]
        self.stats.pending_tasks -= 1
        
        logger.info(f"Task removed: {task_id}")
        return True
    
    async def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """タスクを取得"""
        return self.tasks.get(task_id)
    
    async def get_tasks_by_type(self, task_type: TaskType) -> List[ScheduledTask]:
        """タイプ別にタスクを取得"""
        return [task for task in self.tasks.values() if task.task_type == task_type]
    
    async def get_tasks_by_status(self, status: TaskStatus) -> List[ScheduledTask]:
        """ステータス別にタスクを取得"""
        return [task for task in self.tasks.values() if task.status == status]
    
    async def get_upcoming_tasks(self, limit: int = 10) -> List[ScheduledTask]:
        """今後のタスクを取得"""
        upcoming = []
        for task in self.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.SCHEDULED]:
                upcoming.append(task)
        
        # 実行時間でソート
        upcoming.sort(key=lambda t: t.next_run or t.scheduled_time)
        return upcoming[:limit]
    
    async def _scheduler_loop(self) -> None:
        """スケジューラーのメインループ"""
        logger.info("Scheduler loop started")
        
        while not self._shutdown:
            try:
                # 実行可能なタスクを取得
                ready_tasks = await self._get_ready_tasks()
                
                if ready_tasks:
                    logger.info(f"Executing {len(ready_tasks)} ready tasks")
                    
                    # タスクを並行実行
                    results = await self.executor.execute_tasks_concurrently(ready_tasks)
                    
                    # 統計を更新
                    self._update_stats_from_results(results)
                
                # 次の実行時間まで待機
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(5)  # エラー時は少し長めに待機
        
        logger.info("Scheduler loop stopped")
    
    async def _get_ready_tasks(self) -> List[ScheduledTask]:
        """実行可能なタスクを取得"""
        ready_tasks = []
        now = datetime.now()
        
        # キューから実行可能なタスクを取得
        temp_queue = []
        
        while self.task_queue:
            priority, scheduled_time, task = heapq.heappop(self.task_queue)
            
            # タスクが存在し、実行可能かチェック
            if task.task_id in self.tasks and task.is_ready_to_run():
                # 市場時間チェック
                if task.market_hours_only:
                    if not task.can_run_in_market_hours(self.market_hours):
                        temp_queue.append((priority, scheduled_time, task))
                        continue
                
                ready_tasks.append(task)
                
                # 同時実行制限チェック
                if len(ready_tasks) >= self.executor.max_concurrent_tasks:
                    break
            else:
                # 実行不可能なタスクはキューに戻す
                temp_queue.append((priority, scheduled_time, task))
        
        # キューを復元
        for item in temp_queue:
            heapq.heappush(self.task_queue, item)
        
        return ready_tasks
    
    def _update_stats_from_results(self, results: List[TaskResult]) -> None:
        """実行結果から統計を更新"""
        for result in results:
            if result.success:
                self.stats.completed_tasks += 1
                self.stats.pending_tasks -= 1
            else:
                self.stats.failed_tasks += 1
        
        self.stats.running_tasks = len(self.executor.get_running_tasks())
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        if self.stats.start_time:
            self.stats.uptime_seconds = (datetime.now() - self.stats.start_time).total_seconds()
        
        executor_stats = self.executor.get_execution_stats()
        
        return {
            "scheduler": {
                "total_tasks": self.stats.total_tasks,
                "pending_tasks": self.stats.pending_tasks,
                "running_tasks": self.stats.running_tasks,
                "completed_tasks": self.stats.completed_tasks,
                "failed_tasks": self.stats.failed_tasks,
                "cancelled_tasks": self.stats.cancelled_tasks,
                "uptime_seconds": self.stats.uptime_seconds,
                "is_running": self._running
            },
            "executor": executor_stats,
            "task_queue_size": len(self.task_queue)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        return {
            "status": "healthy" if self._running and not self._shutdown else "unhealthy",
            "is_running": self._running,
            "is_shutdown": self._shutdown,
            "total_tasks": len(self.tasks),
            "queue_size": len(self.task_queue),
            "running_tasks": len(self.executor.get_running_tasks()),
            "uptime_seconds": self.stats.uptime_seconds
        }
