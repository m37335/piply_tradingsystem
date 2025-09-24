"""
スケジュールされたタスク

データ収集タスクの定義と管理を提供します。
"""

import asyncio
import logging
from typing import Any, Callable, Dict, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """タスクステータス"""
    PENDING = "pending"        # 待機中
    SCHEDULED = "scheduled"    # スケジュール済み
    RUNNING = "running"        # 実行中
    COMPLETED = "completed"    # 完了
    FAILED = "failed"         # 失敗
    CANCELLED = "cancelled"    # キャンセル
    RETRYING = "retrying"      # リトライ中


class TaskPriority(Enum):
    """タスク優先度"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskType(Enum):
    """タスクタイプ"""
    DATA_COLLECTION = "data_collection"
    ECONOMIC_INDICATORS = "economic_indicators"
    LLM_ANALYSIS = "llm_analysis"
    HEALTH_CHECK = "health_check"
    CLEANUP = "cleanup"
    NOTIFICATION = "notification"


@dataclass
class TaskResult:
    """タスク実行結果"""
    success: bool
    data: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduledTask:
    """スケジュールされたタスク"""
    
    # 基本情報
    task_id: str
    task_type: TaskType
    name: str
    description: str
    
    # 実行情報
    function: Callable
    scheduled_time: datetime
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    interval: Optional[timedelta] = None  # 繰り返し間隔
    max_retries: int = 3
    retry_delay: timedelta = field(default_factory=lambda: timedelta(minutes=5))
    
    # 優先度と制約
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[timedelta] = None
    dependencies: List[str] = field(default_factory=list)  # 依存タスクID
    
    # 市場制約
    market_hours_only: bool = False
    skip_weekends: bool = True
    skip_holidays: bool = True
    
    # 実行制御
    max_concurrent: int = 1
    resource_requirements: Dict[str, Any] = field(default_factory=dict)
    
    # 状態管理
    status: TaskStatus = TaskStatus.PENDING
    retry_count: int = 0
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 結果
    last_result: Optional[TaskResult] = None
    execution_history: List[TaskResult] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        
        if self.next_run is None:
            self.next_run = self.scheduled_time
    
    def is_ready_to_run(self) -> bool:
        """タスクが実行可能かチェック"""
        now = datetime.now()
        
        # 基本的な実行条件チェック
        if self.status not in [TaskStatus.PENDING, TaskStatus.SCHEDULED]:
            return False
        
        if self.next_run and now < self.next_run:
            return False
        
        # リトライ制限チェック
        if self.retry_count >= self.max_retries:
            return False
        
        # 依存関係チェック
        if self.dependencies:
            # 依存タスクの完了チェック（実装は外部で行う）
            pass
        
        return True
    
    def can_run_in_market_hours(self, market_hours: Dict[str, Any]) -> bool:
        """市場時間内で実行可能かチェック"""
        if not self.market_hours_only:
            return True
        
        now = datetime.now()
        current_day = now.strftime("%A").lower()
        
        # 週末チェック
        if self.skip_weekends and current_day in ['saturday', 'sunday']:
            return False
        
        # 祝日チェック（簡易実装）
        if self.skip_holidays:
            # 祝日チェックの実装
            pass
        
        # 市場時間チェック
        if current_day in market_hours:
            market_open = market_hours[current_day]['open']
            market_close = market_hours[current_day]['close']
            
            current_time = now.time()
            if market_open <= current_time <= market_close:
                return True
        
        return False
    
    def calculate_next_run(self) -> Optional[datetime]:
        """次の実行時間を計算"""
        if not self.interval:
            return None
        
        if self.last_run:
            return self.last_run + self.interval
        else:
            return self.scheduled_time + self.interval
    
    def mark_as_running(self) -> None:
        """タスクを実行中にマーク"""
        self.status = TaskStatus.RUNNING
        self.updated_at = datetime.now()
    
    def mark_as_completed(self, result: TaskResult) -> None:
        """タスクを完了にマーク"""
        self.status = TaskStatus.COMPLETED
        self.last_run = datetime.now()
        self.last_result = result
        self.execution_history.append(result)
        self.retry_count = 0
        self.next_run = self.calculate_next_run()
        self.updated_at = datetime.now()
    
    def mark_as_failed(self, result: TaskResult) -> None:
        """タスクを失敗にマーク"""
        self.retry_count += 1
        
        if self.retry_count >= self.max_retries:
            self.status = TaskStatus.FAILED
        else:
            self.status = TaskStatus.RETRYING
            self.next_run = datetime.now() + self.retry_delay
        
        self.last_result = result
        self.execution_history.append(result)
        self.updated_at = datetime.now()
    
    def cancel(self) -> None:
        """タスクをキャンセル"""
        self.status = TaskStatus.CANCELLED
        self.updated_at = datetime.now()
    
    def reset(self) -> None:
        """タスクをリセット"""
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.next_run = self.scheduled_time
        self.updated_at = datetime.now()
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """実行統計を取得"""
        total_runs = len(self.execution_history)
        successful_runs = sum(1 for r in self.execution_history if r.success)
        failed_runs = total_runs - successful_runs
        
        avg_execution_time = 0.0
        if total_runs > 0:
            avg_execution_time = sum(r.execution_time for r in self.execution_history) / total_runs
        
        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "success_rate": (successful_runs / total_runs * 100) if total_runs > 0 else 0,
            "avg_execution_time": avg_execution_time,
            "retry_count": self.retry_count,
            "last_run": self.last_run,
            "next_run": self.next_run
        }
