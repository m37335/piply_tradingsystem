"""
スケジューラー設定

スケジューラーに関する設定を管理します。
"""

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskPriority(Enum):
    """タスク優先度"""

    LOW = 1
    NORMAL = 5
    HIGH = 8
    CRITICAL = 10


class TaskStatus(Enum):
    """タスクステータス"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MarketStatus(Enum):
    """市場ステータス"""

    OPEN = "open"
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    AFTER_HOURS = "after_hours"
    HOLIDAY = "holiday"


@dataclass
class MarketHoursConfig:
    """市場時間設定"""

    timezone: str = "UTC"
    open_time: str = "09:30"
    close_time: str = "16:00"
    pre_market_start: str = "04:00"
    after_hours_end: str = "20:00"
    weekdays_only: bool = True
    holidays: List[str] = None

    def __post_init__(self):
        if self.holidays is None:
            self.holidays = []

    @classmethod
    def from_env(cls) -> "MarketHoursConfig":
        """環境変数から設定を読み込み"""
        holidays_str = os.getenv("MARKET_HOLIDAYS", "")
        holidays = [h.strip() for h in holidays_str.split(",") if h.strip()]

        return cls(
            timezone=os.getenv("MARKET_TIMEZONE", "UTC"),
            open_time=os.getenv("MARKET_OPEN_TIME", "09:30"),
            close_time=os.getenv("MARKET_CLOSE_TIME", "16:00"),
            pre_market_start=os.getenv("MARKET_PRE_MARKET_START", "04:00"),
            after_hours_end=os.getenv("MARKET_AFTER_HOURS_END", "20:00"),
            weekdays_only=os.getenv("MARKET_WEEKDAYS_ONLY", "true").lower() == "true",
            holidays=holidays,
        )


@dataclass
class TaskSchedulerConfig:
    """タスクスケジューラー設定"""

    max_concurrent_tasks: int = 10
    task_timeout_seconds: int = 300
    retry_attempts: int = 3
    retry_delay_seconds: float = 60.0
    cleanup_interval_seconds: int = 3600
    max_task_history: int = 1000

    @classmethod
    def from_env(cls) -> "TaskSchedulerConfig":
        """環境変数から設定を読み込み"""
        return cls(
            max_concurrent_tasks=int(os.getenv("SCHEDULER_MAX_CONCURRENT_TASKS", "10")),
            task_timeout_seconds=int(os.getenv("SCHEDULER_TASK_TIMEOUT", "300")),
            retry_attempts=int(os.getenv("SCHEDULER_RETRY_ATTEMPTS", "3")),
            retry_delay_seconds=float(os.getenv("SCHEDULER_RETRY_DELAY", "60.0")),
            cleanup_interval_seconds=int(
                os.getenv("SCHEDULER_CLEANUP_INTERVAL", "3600")
            ),
            max_task_history=int(os.getenv("SCHEDULER_MAX_TASK_HISTORY", "1000")),
        )


@dataclass
class DataCollectionTaskConfig:
    """データ収集タスク設定"""

    symbols: List[str]
    timeframes: List[str]
    collection_interval_seconds: int = 300  # 5分
    backfill_interval_days: int = 1
    priority: TaskPriority = TaskPriority.HIGH
    market_aware: bool = True

    @classmethod
    def from_env(cls) -> "DataCollectionTaskConfig":
        """環境変数から設定を読み込み"""
        symbols_str = os.getenv("DATA_COLLECTION_SYMBOLS", "AAPL,MSFT,GOOGL,AMZN,TSLA")
        symbols = [s.strip() for s in symbols_str.split(",")]

        timeframes_str = os.getenv("DATA_COLLECTION_TIMEFRAMES", "1m,5m,1h,1d")
        timeframes = [tf.strip() for tf in timeframes_str.split(",")]

        priority_str = os.getenv("DATA_COLLECTION_PRIORITY", "high")
        priority = TaskPriority[priority_str.upper()]

        return cls(
            symbols=symbols,
            timeframes=timeframes,
            collection_interval_seconds=int(
                os.getenv("DATA_COLLECTION_INTERVAL", "300")
            ),
            backfill_interval_days=int(
                os.getenv("DATA_COLLECTION_BACKFILL_INTERVAL", "1")
            ),
            priority=priority,
            market_aware=os.getenv("DATA_COLLECTION_MARKET_AWARE", "true").lower()
            == "true",
        )


@dataclass
class SchedulerSettings:
    """スケジューラー設定"""

    market_hours: MarketHoursConfig
    task_scheduler: TaskSchedulerConfig
    data_collection: DataCollectionTaskConfig
    enable_market_aware_scheduling: bool = True
    enable_task_persistence: bool = True
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "SchedulerSettings":
        """環境変数から設定を読み込み"""
        return cls(
            market_hours=MarketHoursConfig.from_env(),
            task_scheduler=TaskSchedulerConfig.from_env(),
            data_collection=DataCollectionTaskConfig.from_env(),
            enable_market_aware_scheduling=os.getenv(
                "ENABLE_MARKET_AWARE_SCHEDULING", "true"
            ).lower()
            == "true",
            enable_task_persistence=os.getenv("ENABLE_TASK_PERSISTENCE", "true").lower()
            == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書に変換"""
        return {
            "market_hours": {
                "timezone": self.market_hours.timezone,
                "open_time": self.market_hours.open_time,
                "close_time": self.market_hours.close_time,
                "pre_market_start": self.market_hours.pre_market_start,
                "after_hours_end": self.market_hours.after_hours_end,
                "weekdays_only": self.market_hours.weekdays_only,
                "holidays": self.market_hours.holidays,
            },
            "task_scheduler": {
                "max_concurrent_tasks": self.task_scheduler.max_concurrent_tasks,
                "task_timeout_seconds": self.task_scheduler.task_timeout_seconds,
                "retry_attempts": self.task_scheduler.retry_attempts,
                "retry_delay_seconds": self.task_scheduler.retry_delay_seconds,
                "cleanup_interval_seconds": self.task_scheduler.cleanup_interval_seconds,
                "max_task_history": self.task_scheduler.max_task_history,
            },
            "data_collection": {
                "symbols": self.data_collection.symbols,
                "timeframes": self.data_collection.timeframes,
                "collection_interval_seconds": self.data_collection.collection_interval_seconds,
                "backfill_interval_days": self.data_collection.backfill_interval_days,
                "priority": self.data_collection.priority.value,
                "market_aware": self.data_collection.market_aware,
            },
            "enable_market_aware_scheduling": self.enable_market_aware_scheduling,
            "enable_task_persistence": self.enable_task_persistence,
            "log_level": self.log_level,
        }
