"""
優先度管理システム

データ収集タスクの優先度を管理します。
"""

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple


class TaskPriority(Enum):
    """タスク優先度"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskType(Enum):
    """タスクタイプ"""
    BACKFILL = "backfill"
    REAL_TIME = "real_time"
    MANUAL = "manual"
    RETRY = "retry"


@dataclass
class TaskInfo:
    """タスク情報"""
    task_id: str
    symbol: str
    timeframe: str
    priority: TaskPriority
    task_type: TaskType
    created_at: float
    last_attempt: Optional[float] = None
    attempt_count: int = 0
    max_attempts: int = 3
    data_age_seconds: Optional[float] = None


class PriorityManager:
    """優先度管理システム"""
    
    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.priority_weights = {
            TaskPriority.LOW: 1.0,
            TaskPriority.NORMAL: 2.0,
            TaskPriority.HIGH: 4.0,
            TaskPriority.CRITICAL: 8.0,
        }
        self.type_weights = {
            TaskType.CRITICAL: 10.0,
            TaskType.REAL_TIME: 5.0,
            TaskType.MANUAL: 3.0,
            TaskType.BACKFILL: 1.0,
            TaskType.RETRY: 2.0,
        }
    
    def add_task(
        self,
        task_id: str,
        symbol: str,
        timeframe: str,
        priority: TaskPriority,
        task_type: TaskType,
        data_age_seconds: Optional[float] = None,
    ) -> None:
        """
        タスクを追加
        
        Args:
            task_id: タスクID
            symbol: シンボル
            timeframe: タイムフレーム
            priority: 優先度
            task_type: タスクタイプ
            data_age_seconds: データの年齢（秒）
        """
        task_info = TaskInfo(
            task_id=task_id,
            symbol=symbol,
            timeframe=timeframe,
            priority=priority,
            task_type=task_type,
            created_at=time.time(),
            data_age_seconds=data_age_seconds,
        )
        self.tasks[task_id] = task_info
    
    def remove_task(self, task_id: str) -> None:
        """
        タスクを削除
        
        Args:
            task_id: タスクID
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
    
    def update_task_attempt(self, task_id: str, success: bool) -> None:
        """
        タスクの実行結果を更新
        
        Args:
            task_id: タスクID
            success: 成功したかどうか
        """
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        task.last_attempt = time.time()
        task.attempt_count += 1
        
        if success:
            # 成功した場合はタスクを削除
            self.remove_task(task_id)
        elif task.attempt_count >= task.max_attempts:
            # 最大試行回数に達した場合はタスクを削除
            self.remove_task(task_id)
    
    def get_next_task(self) -> Optional[TaskInfo]:
        """
        次の実行すべきタスクを取得
        
        Returns:
            次のタスク、またはNone
        """
        if not self.tasks:
            return None
        
        # 優先度スコアを計算
        scored_tasks = []
        for task in self.tasks.values():
            score = self._calculate_priority_score(task)
            scored_tasks.append((score, task))
        
        # スコアの降順でソート
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        
        return scored_tasks[0][1] if scored_tasks else None
    
    def get_tasks_by_priority(self, priority: TaskPriority) -> List[TaskInfo]:
        """
        指定された優先度のタスクを取得
        
        Args:
            priority: 優先度
            
        Returns:
            タスクのリスト
        """
        return [
            task for task in self.tasks.values()
            if task.priority == priority
        ]
    
    def get_tasks_by_symbol(self, symbol: str) -> List[TaskInfo]:
        """
        指定されたシンボルのタスクを取得
        
        Args:
            symbol: シンボル
            
        Returns:
            タスクのリスト
        """
        return [
            task for task in self.tasks.values()
            if task.symbol == symbol
        ]
    
    def get_tasks_by_timeframe(self, timeframe: str) -> List[TaskInfo]:
        """
        指定されたタイムフレームのタスクを取得
        
        Args:
            timeframe: タイムフレーム
            
        Returns:
            タスクのリスト
        """
        return [
            task for task in self.tasks.values()
            if task.timeframe == timeframe
        ]
    
    def _calculate_priority_score(self, task: TaskInfo) -> float:
        """
        タスクの優先度スコアを計算
        
        Args:
            task: タスク情報
            
        Returns:
            優先度スコア
        """
        # 基本優先度スコア
        base_score = self.priority_weights.get(task.priority, 1.0)
        
        # タスクタイプスコア
        type_score = self.type_weights.get(task.task_type, 1.0)
        
        # データの年齢による調整
        age_score = 1.0
        if task.data_age_seconds is not None:
            # データが古いほど優先度を上げる
            age_score = min(10.0, task.data_age_seconds / 3600)  # 1時間で10倍
        
        # 試行回数による調整
        attempt_penalty = 1.0 - (task.attempt_count * 0.1)
        attempt_penalty = max(0.1, attempt_penalty)
        
        # 待機時間による調整
        wait_time = time.time() - task.created_at
        wait_score = min(5.0, wait_time / 300)  # 5分で5倍
        
        # 最終スコア
        final_score = (
            base_score * type_score * age_score * attempt_penalty * wait_score
        )
        
        return final_score
    
    def get_statistics(self) -> Dict[str, any]:
        """
        統計情報を取得
        
        Returns:
            統計情報
        """
        total_tasks = len(self.tasks)
        tasks_by_priority = {}
        tasks_by_type = {}
        
        for task in self.tasks.values():
            # 優先度別
            priority_name = task.priority.name
            tasks_by_priority[priority_name] = tasks_by_priority.get(priority_name, 0) + 1
            
            # タイプ別
            type_name = task.task_type.value
            tasks_by_type[type_name] = tasks_by_type.get(type_name, 0) + 1
        
        return {
            "total_tasks": total_tasks,
            "tasks_by_priority": tasks_by_priority,
            "tasks_by_type": tasks_by_type,
            "oldest_task_age": self._get_oldest_task_age(),
            "average_wait_time": self._get_average_wait_time(),
        }
    
    def _get_oldest_task_age(self) -> float:
        """最も古いタスクの年齢を取得"""
        if not self.tasks:
            return 0.0
        
        oldest_time = min(task.created_at for task in self.tasks.values())
        return time.time() - oldest_time
    
    def _get_average_wait_time(self) -> float:
        """平均待機時間を取得"""
        if not self.tasks:
            return 0.0
        
        current_time = time.time()
        total_wait_time = sum(
            current_time - task.created_at
            for task in self.tasks.values()
        )
        
        return total_wait_time / len(self.tasks)
    
    def cleanup_old_tasks(self, max_age_seconds: float = 3600) -> int:
        """
        古いタスクをクリーンアップ
        
        Args:
            max_age_seconds: 最大年齢（秒）
            
        Returns:
            削除されたタスク数
        """
        current_time = time.time()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if current_time - task.created_at > max_age_seconds:
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self.tasks[task_id]
        
        return len(tasks_to_remove)
    
    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """
        タスク情報を取得
        
        Args:
            task_id: タスクID
            
        Returns:
            タスク情報、またはNone
        """
        return self.tasks.get(task_id)
    
    def update_task_priority(self, task_id: str, new_priority: TaskPriority) -> bool:
        """
        タスクの優先度を更新
        
        Args:
            task_id: タスクID
            new_priority: 新しい優先度
            
        Returns:
            更新が成功したかどうか
        """
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].priority = new_priority
        return True
    
    def get_high_priority_tasks(self, limit: int = 10) -> List[TaskInfo]:
        """
        高優先度のタスクを取得
        
        Args:
            limit: 取得するタスク数の上限
            
        Returns:
            高優先度のタスクのリスト
        """
        high_priority_tasks = [
            task for task in self.tasks.values()
            if task.priority in [TaskPriority.HIGH, TaskPriority.CRITICAL]
        ]
        
        # 優先度スコアでソート
        scored_tasks = [
            (self._calculate_priority_score(task), task)
            for task in high_priority_tasks
        ]
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        
        return [task for _, task in scored_tasks[:limit]]
