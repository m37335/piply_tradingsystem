"""
タスク実行エンジン

スケジュールされたタスクの実行を管理します。
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import traceback

from .scheduled_task import ScheduledTask, TaskResult, TaskStatus, TaskPriority

logger = logging.getLogger(__name__)


@dataclass
class ExecutionStats:
    """実行統計"""
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    avg_execution_time: float = 0.0
    concurrent_executions: int = 0
    max_concurrent_executions: int = 0


class TaskExecutor:
    """タスク実行エンジン"""
    
    def __init__(self, max_concurrent_tasks: int = 10):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.execution_stats = ExecutionStats()
        self._shutdown = False
        
        # スレッドプール（同期関数用）
        self.thread_pool = ThreadPoolExecutor(max_workers=max_concurrent_tasks)
    
    async def execute_task(self, task: ScheduledTask) -> TaskResult:
        """タスクを実行"""
        if self._shutdown:
            return TaskResult(
                success=False,
                error_message="Executor is shutting down"
            )
        
        # 同時実行制限チェック
        if len(self.running_tasks) >= self.max_concurrent_tasks:
            return TaskResult(
                success=False,
                error_message="Maximum concurrent tasks reached"
            )
        
        # タスクを実行中にマーク
        task.mark_as_running()
        
        start_time = time.time()
        task_id = task.task_id
        
        try:
            # タスクを実行
            if asyncio.iscoroutinefunction(task.function):
                # 非同期関数の場合
                result = await self._execute_async_task(task)
            else:
                # 同期関数の場合
                result = await self._execute_sync_task(task)
            
            execution_time = time.time() - start_time
            result.execution_time = execution_time
            
            # 統計を更新
            self._update_stats(result, execution_time)
            
            # タスクの状態を更新
            if result.success:
                task.mark_as_completed(result)
            else:
                task.mark_as_failed(result)
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_result = TaskResult(
                success=False,
                error_message=str(e),
                execution_time=execution_time,
                metadata={"traceback": traceback.format_exc()}
            )
            
            # 統計を更新
            self._update_stats(error_result, execution_time)
            
            # タスクの状態を更新
            task.mark_as_failed(error_result)
            
            logger.error(f"Task {task_id} execution failed: {e}")
            return error_result
        
        finally:
            # 実行中タスクから削除
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    async def _execute_async_task(self, task: ScheduledTask) -> TaskResult:
        """非同期タスクを実行"""
        try:
            # タイムアウト設定
            if task.timeout:
                result = await asyncio.wait_for(
                    task.function(*task.args, **task.kwargs),
                    timeout=task.timeout.total_seconds()
                )
            else:
                result = await task.function(*task.args, **task.kwargs)
            
            return TaskResult(
                success=True,
                data=result,
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "execution_method": "async"
                }
            )
            
        except asyncio.TimeoutError:
            return TaskResult(
                success=False,
                error_message=f"Task timed out after {task.timeout}",
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "execution_method": "async"
                }
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "execution_method": "async",
                    "traceback": traceback.format_exc()
                }
            )
    
    async def _execute_sync_task(self, task: ScheduledTask) -> TaskResult:
        """同期タスクを実行"""
        try:
            # スレッドプールで実行
            loop = asyncio.get_event_loop()
            
            if task.timeout:
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.thread_pool,
                        lambda: task.function(*task.args, **task.kwargs)
                    ),
                    timeout=task.timeout.total_seconds()
                )
            else:
                result = await loop.run_in_executor(
                    self.thread_pool,
                    lambda: task.function(*task.args, **task.kwargs)
                )
            
            return TaskResult(
                success=True,
                data=result,
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "execution_method": "sync"
                }
            )
            
        except asyncio.TimeoutError:
            return TaskResult(
                success=False,
                error_message=f"Task timed out after {task.timeout}",
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "execution_method": "sync"
                }
            )
        except Exception as e:
            return TaskResult(
                success=False,
                error_message=str(e),
                metadata={
                    "task_id": task.task_id,
                    "task_type": task.task_type.value,
                    "execution_method": "sync",
                    "traceback": traceback.format_exc()
                }
            )
    
    async def execute_tasks_concurrently(self, tasks: List[ScheduledTask]) -> List[TaskResult]:
        """複数のタスクを並行実行"""
        if not tasks:
            return []
        
        # 同時実行制限を考慮してタスクを分割
        concurrent_tasks = []
        results = []
        
        for task in tasks:
            if len(concurrent_tasks) < self.max_concurrent_tasks:
                concurrent_tasks.append(task)
            else:
                # 現在のバッチを実行
                batch_results = await asyncio.gather(
                    *[self.execute_task(t) for t in concurrent_tasks],
                    return_exceptions=True
                )
                results.extend(batch_results)
                
                # 新しいバッチを開始
                concurrent_tasks = [task]
        
        # 残りのタスクを実行
        if concurrent_tasks:
            batch_results = await asyncio.gather(
                *[self.execute_task(t) for t in concurrent_tasks],
                return_exceptions=True
            )
            results.extend(batch_results)
        
        return results
    
    def _update_stats(self, result: TaskResult, execution_time: float) -> None:
        """実行統計を更新"""
        self.execution_stats.total_executions += 1
        self.execution_stats.total_execution_time += execution_time
        
        if result.success:
            self.execution_stats.successful_executions += 1
        else:
            self.execution_stats.failed_executions += 1
        
        # 平均実行時間を更新
        self.execution_stats.avg_execution_time = (
            self.execution_stats.total_execution_time / 
            self.execution_stats.total_executions
        )
        
        # 最大同時実行数を更新
        current_concurrent = len(self.running_tasks)
        if current_concurrent > self.execution_stats.max_concurrent_executions:
            self.execution_stats.max_concurrent_executions = current_concurrent
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """実行統計を取得"""
        stats = self.execution_stats
        
        return {
            "total_executions": stats.total_executions,
            "successful_executions": stats.successful_executions,
            "failed_executions": stats.failed_executions,
            "success_rate": (
                stats.successful_executions / max(1, stats.total_executions) * 100
            ),
            "total_execution_time": stats.total_execution_time,
            "avg_execution_time": stats.avg_execution_time,
            "current_concurrent_executions": len(self.running_tasks),
            "max_concurrent_executions": stats.max_concurrent_executions,
            "max_concurrent_tasks": self.max_concurrent_tasks
        }
    
    def get_running_tasks(self) -> List[str]:
        """実行中のタスクIDリストを取得"""
        return list(self.running_tasks.keys())
    
    async def cancel_task(self, task_id: str) -> bool:
        """タスクをキャンセル"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True
        return False
    
    async def shutdown(self, timeout: float = 30.0) -> None:
        """実行エンジンをシャットダウン"""
        logger.info("Shutting down task executor...")
        self._shutdown = True
        
        # 実行中のタスクをキャンセル
        if self.running_tasks:
            logger.info(f"Cancelling {len(self.running_tasks)} running tasks...")
            await asyncio.gather(
                *[self.cancel_task(task_id) for task_id in self.running_tasks.keys()],
                return_exceptions=True
            )
        
        # スレッドプールをシャットダウン
        self.thread_pool.shutdown(wait=True, timeout=timeout)
        
        logger.info("Task executor shutdown completed")
