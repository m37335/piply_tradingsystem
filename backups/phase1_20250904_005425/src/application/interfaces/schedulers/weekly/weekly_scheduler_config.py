"""
週次スケジューラー設定
週次データ取得スケジューラーの設定を管理
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import time

from src.application.interfaces.schedulers.base import SchedulerConfig


@dataclass
class WeeklySchedulerConfig(SchedulerConfig):
    """週次スケジューラー設定"""
    
    # 週次スケジュール設定
    execution_day: str = "sunday"  # 実行曜日
    execution_time: time = field(default_factory=lambda: time(9, 0))  # 実行時刻 (09:00)
    timezone: str = "Asia/Tokyo"  # タイムゾーン
    
    # データ取得設定
    target_countries: List[str] = field(default_factory=lambda: [
        "japan", "united states", "euro zone", "united kingdom", "australia", "canada"
    ])
    target_importances: List[str] = field(default_factory=lambda: ["high", "medium"])
    
    # 週次取得設定
    weeks_ahead: int = 2  # 何週先まで取得するか
    include_ai_analysis: bool = True  # AI分析を含めるか
    include_notifications: bool = True  # 通知を含めるか
    
    # エラー処理設定
    retry_on_failure: bool = True
    max_retries: int = 3
    retry_delay_minutes: int = 30
    
    # ログ設定
    log_execution_details: bool = True
    log_performance_metrics: bool = True
    
    def validate(self) -> bool:
        """設定の検証"""
        if not super().validate():
            return False
        
        # 曜日の検証
        valid_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        if self.execution_day.lower() not in valid_days:
            return False
        
        # 週数の検証
        if self.weeks_ahead < 1 or self.weeks_ahead > 8:
            return False
        
        # リトライ設定の検証
        if self.max_retries < 0 or self.max_retries > 10:
            return False
        
        if self.retry_delay_minutes < 1 or self.retry_delay_minutes > 1440:
            return False
        
        return True
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        base_dict = super().to_dict()
        weekly_dict = {
            "execution_day": self.execution_day,
            "execution_time": self.execution_time.strftime("%H:%M"),
            "timezone": self.timezone,
            "target_countries": self.target_countries,
            "target_importances": self.target_importances,
            "weeks_ahead": self.weeks_ahead,
            "include_ai_analysis": self.include_ai_analysis,
            "include_notifications": self.include_notifications,
            "retry_on_failure": self.retry_on_failure,
            "max_retries": self.max_retries,
            "retry_delay_minutes": self.retry_delay_minutes,
            "log_execution_details": self.log_execution_details,
            "log_performance_metrics": self.log_performance_metrics
        }
        base_dict.update(weekly_dict)
        return base_dict
    
    @classmethod
    def from_dict(cls, data: dict) -> "WeeklySchedulerConfig":
        """辞書から設定を復元"""
        base_config = SchedulerConfig.from_dict(data)
        
        # 時刻の復元
        execution_time = time.fromisoformat(data.get("execution_time", "09:00"))
        
        return cls(
            name=base_config.name,
            description=base_config.description,
            enabled=base_config.enabled,
            max_retries=base_config.max_retries,
            retry_delay=base_config.retry_delay,
            timeout=base_config.timeout,
            execution_day=data.get("execution_day", "sunday"),
            execution_time=execution_time,
            timezone=data.get("timezone", "Asia/Tokyo"),
            target_countries=data.get("target_countries", []),
            target_importances=data.get("target_importances", []),
            weeks_ahead=data.get("weeks_ahead", 2),
            include_ai_analysis=data.get("include_ai_analysis", True),
            include_notifications=data.get("include_notifications", True),
            retry_on_failure=data.get("retry_on_failure", True),
            max_retries=data.get("max_retries", 3),
            retry_delay_minutes=data.get("retry_delay_minutes", 30),
            log_execution_details=data.get("log_execution_details", True),
            log_performance_metrics=data.get("log_performance_metrics", True)
        )
