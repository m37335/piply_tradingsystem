"""
市場時間対応スケジューラー

市場の開閉時間を考慮したスケジューリング機能を提供します。
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from .market_hours_manager import MarketHoursManager, MarketStatus

logger = logging.getLogger(__name__)


class TaskScheduleType(Enum):
    """タスクスケジュールタイプ"""
    MARKET_HOURS_ONLY = "market_hours_only"  # 市場時間のみ
    EXTENDED_HOURS = "extended_hours"  # 延長時間含む
    ALWAYS = "always"  # 常時実行
    CUSTOM = "custom"  # カスタム


class MarketAwareScheduler:
    """市場時間対応スケジューラー"""
    
    def __init__(self, market_hours_manager: MarketHoursManager):
        self.market_hours_manager = market_hours_manager
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self._running = False
    
    async def start(self) -> None:
        """スケジューラーを開始"""
        if self._running:
            logger.warning("Market aware scheduler is already running")
            return
        
        self._running = True
        logger.info("Market aware scheduler started")
    
    async def stop(self) -> None:
        """スケジューラーを停止"""
        if not self._running:
            return
        
        self._running = False
        
        # 実行中のタスクをキャンセル
        for task_id, task in self.running_tasks.items():
            if not task.done():
                task.cancel()
        
        # タスクの完了を待機
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("Market aware scheduler stopped")
    
    async def schedule_task(
        self,
        task_id: str,
        func: callable,
        schedule_type: TaskScheduleType,
        interval_seconds: Optional[int] = None,
        cron_expression: Optional[str] = None,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 1,
        market_conditions: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        タスクをスケジュール
        
        Args:
            task_id: タスクID
            func: 実行する関数
            schedule_type: スケジュールタイプ
            interval_seconds: 実行間隔（秒）
            cron_expression: Cron式
            args: 関数の引数
            kwargs: 関数のキーワード引数
            priority: 優先度
            market_conditions: 市場条件
        """
        if kwargs is None:
            kwargs = {}
        
        if market_conditions is None:
            market_conditions = {}
        
        task_info = {
            "task_id": task_id,
            "func": func,
            "schedule_type": schedule_type,
            "interval_seconds": interval_seconds,
            "cron_expression": cron_expression,
            "args": args,
            "kwargs": kwargs,
            "priority": priority,
            "market_conditions": market_conditions,
            "created_at": datetime.now(),
            "last_run": None,
            "next_run": None,
            "run_count": 0,
            "error_count": 0
        }
        
        self.scheduled_tasks[task_id] = task_info
        
        # タスクを開始
        if self._running:
            await self._start_task(task_id)
        
        logger.info(f"Task {task_id} scheduled with type {schedule_type.value}")
    
    async def _start_task(self, task_id: str) -> None:
        """タスクを開始"""
        if task_id not in self.scheduled_tasks:
            return
        
        task_info = self.scheduled_tasks[task_id]
        
        # 既に実行中の場合は停止
        if task_id in self.running_tasks:
            await self._stop_task(task_id)
        
        # タスクを開始
        task = asyncio.create_task(self._task_worker(task_id))
        self.running_tasks[task_id] = task
        
        logger.info(f"Task {task_id} started")
    
    async def _stop_task(self, task_id: str) -> None:
        """タスクを停止"""
        if task_id in self.running_tasks:
            task = self.running_tasks[task_id]
            if not task.done():
                task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self.running_tasks[task_id]
            logger.info(f"Task {task_id} stopped")
    
    async def _task_worker(self, task_id: str) -> None:
        """タスクワーカー"""
        task_info = self.scheduled_tasks[task_id]
        
        while self._running and task_id in self.scheduled_tasks:
            try:
                # 市場条件をチェック
                if await self._should_run_task(task_id):
                    # タスクを実行
                    await self._execute_task(task_id)
                
                # 次の実行まで待機
                await self._wait_for_next_execution(task_id)
                
            except asyncio.CancelledError:
                logger.info(f"Task {task_id} worker cancelled")
                break
            except Exception as e:
                logger.error(f"Task {task_id} worker error: {e}")
                task_info["error_count"] += 1
                
                # エラーが多すぎる場合はタスクを停止
                if task_info["error_count"] > 10:
                    logger.error(f"Task {task_id} has too many errors, stopping")
                    break
                
                # エラー時は少し長めに待機
                await asyncio.sleep(60)
    
    async def _should_run_task(self, task_id: str) -> bool:
        """
        タスクを実行すべきかチェック
        
        Args:
            task_id: タスクID
            
        Returns:
            実行すべきかどうか
        """
        task_info = self.scheduled_tasks[task_id]
        schedule_type = task_info["schedule_type"]
        
        # 市場状況を取得
        market_status = await self.market_hours_manager.get_market_status()
        
        # スケジュールタイプに応じて判定
        if schedule_type == TaskScheduleType.ALWAYS:
            return True
        elif schedule_type == TaskScheduleType.MARKET_HOURS_ONLY:
            return market_status == MarketStatus.OPEN
        elif schedule_type == TaskScheduleType.EXTENDED_HOURS:
            return market_status in [MarketStatus.OPEN, MarketStatus.PRE_MARKET, MarketStatus.AFTER_HOURS]
        elif schedule_type == TaskScheduleType.CUSTOM:
            return await self._check_custom_conditions(task_id, market_status)
        
        return False
    
    async def _check_custom_conditions(
        self,
        task_id: str,
        market_status: MarketStatus
    ) -> bool:
        """
        カスタム条件をチェック
        
        Args:
            task_id: タスクID
            market_status: 市場状況
            
        Returns:
            条件を満たすかどうか
        """
        task_info = self.scheduled_tasks[task_id]
        market_conditions = task_info.get("market_conditions", {})
        
        # 市場状況の条件
        allowed_statuses = market_conditions.get("allowed_statuses", [])
        if allowed_statuses and market_status.value not in allowed_statuses:
            return False
        
        # 時間帯の条件
        allowed_hours = market_conditions.get("allowed_hours", [])
        if allowed_hours:
            current_hour = datetime.now().hour
            if current_hour not in allowed_hours:
                return False
        
        # 曜日の条件
        allowed_weekdays = market_conditions.get("allowed_weekdays", [])
        if allowed_weekdays:
            current_weekday = datetime.now().weekday()
            if current_weekday not in allowed_weekdays:
                return False
        
        return True
    
    async def _execute_task(self, task_id: str) -> None:
        """
        タスクを実行
        
        Args:
            task_id: タスクID
        """
        task_info = self.scheduled_tasks[task_id]
        
        try:
            # タスクを実行
            if asyncio.iscoroutinefunction(task_info["func"]):
                await task_info["func"](*task_info["args"], **task_info["kwargs"])
            else:
                task_info["func"](*task_info["args"], **task_info["kwargs"])
            
            # 実行情報を更新
            task_info["last_run"] = datetime.now()
            task_info["run_count"] += 1
            task_info["error_count"] = 0  # 成功時はエラーカウントをリセット
            
            logger.debug(f"Task {task_id} executed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {e}")
            task_info["error_count"] += 1
            raise
    
    async def _wait_for_next_execution(self, task_id: str) -> None:
        """
        次の実行まで待機
        
        Args:
            task_id: タスクID
        """
        task_info = self.scheduled_tasks[task_id]
        
        if task_info["interval_seconds"]:
            # 間隔ベースの実行
            await asyncio.sleep(task_info["interval_seconds"])
        elif task_info["cron_expression"]:
            # Cron式ベースの実行（簡易実装）
            await self._wait_for_cron_next(task_id)
        else:
            # デフォルトは1分間隔
            await asyncio.sleep(60)
    
    async def _wait_for_cron_next(self, task_id: str) -> None:
        """
        Cron式の次の実行まで待機（簡易実装）
        
        Args:
            task_id: タスクID
        """
        # 簡易実装：1分間隔でチェック
        await asyncio.sleep(60)
    
    async def cancel_task(self, task_id: str) -> None:
        """
        タスクをキャンセル
        
        Args:
            task_id: タスクID
        """
        if task_id in self.scheduled_tasks:
            await self._stop_task(task_id)
            del self.scheduled_tasks[task_id]
            logger.info(f"Task {task_id} cancelled")
    
    async def pause_task(self, task_id: str) -> None:
        """
        タスクを一時停止
        
        Args:
            task_id: タスクID
        """
        if task_id in self.running_tasks:
            await self._stop_task(task_id)
            logger.info(f"Task {task_id} paused")
    
    async def resume_task(self, task_id: str) -> None:
        """
        タスクを再開
        
        Args:
            task_id: タスクID
        """
        if task_id in self.scheduled_tasks and self._running:
            await self._start_task(task_id)
            logger.info(f"Task {task_id} resumed")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        タスクのステータスを取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスクステータス、またはNone
        """
        if task_id not in self.scheduled_tasks:
            return None
        
        task_info = self.scheduled_tasks[task_id]
        is_running = task_id in self.running_tasks
        
        return {
            "task_id": task_id,
            "is_running": is_running,
            "schedule_type": task_info["schedule_type"].value,
            "last_run": task_info["last_run"],
            "next_run": task_info["next_run"],
            "run_count": task_info["run_count"],
            "error_count": task_info["error_count"],
            "created_at": task_info["created_at"],
            "priority": task_info["priority"]
        }
    
    def get_all_tasks_status(self) -> Dict[str, Dict[str, Any]]:
        """
        すべてのタスクのステータスを取得
        
        Returns:
            すべてのタスクステータス
        """
        return {
            task_id: self.get_task_status(task_id)
            for task_id in self.scheduled_tasks.keys()
        }
    
    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """
        スケジューラーの統計を取得
        
        Returns:
            統計情報
        """
        total_tasks = len(self.scheduled_tasks)
        running_tasks = len(self.running_tasks)
        
        # タスクタイプ別の統計
        task_types = {}
        for task_info in self.scheduled_tasks.values():
            schedule_type = task_info["schedule_type"].value
            task_types[schedule_type] = task_types.get(schedule_type, 0) + 1
        
        # エラー統計
        total_errors = sum(
            task_info["error_count"]
            for task_info in self.scheduled_tasks.values()
        )
        
        return {
            "total_tasks": total_tasks,
            "running_tasks": running_tasks,
            "paused_tasks": total_tasks - running_tasks,
            "task_types": task_types,
            "total_errors": total_errors,
            "scheduler_running": self._running
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        ヘルスチェック
        
        Returns:
            ヘルス情報
        """
        try:
            # 市場時間管理のヘルスチェック
            market_health = await self.market_hours_manager.health_check()
            
            # スケジューラーの統計
            stats = await self.get_scheduler_stats()
            
            # ヘルス状態を決定
            health_status = "healthy"
            if stats["total_errors"] > 10:
                health_status = "degraded"
            elif stats["total_errors"] > 50:
                health_status = "unhealthy"
            
            return {
                "status": health_status,
                "scheduler_running": self._running,
                "market_hours": market_health,
                "statistics": stats
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
