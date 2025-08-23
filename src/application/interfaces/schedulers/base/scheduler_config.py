"""
スケジューラー設定

スケジューラーの共通設定を管理する
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SchedulerConfig:
    """
    スケジューラー設定
    
    スケジューラーの共通設定を管理する
    """
    
    # 基本設定
    enabled: bool = True
    name: str = "default_scheduler"
    description: str = "デフォルトスケジューラー"
    
    # 実行設定
    max_retries: int = 3
    retry_delay: int = 60  # 秒
    timeout: int = 300  # 秒
    
    # ログ設定
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # 監視設定
    health_check_enabled: bool = True
    health_check_interval: int = 300  # 秒
    
    # 統計設定
    stats_enabled: bool = True
    stats_retention_days: int = 30
    
    # エラー処理設定
    error_notification_enabled: bool = True
    error_threshold: int = 5
    error_cooldown: int = 3600  # 秒
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "enabled": self.enabled,
            "name": self.name,
            "description": self.description,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "log_level": self.log_level,
            "log_file": self.log_file,
            "health_check_enabled": self.health_check_enabled,
            "health_check_interval": self.health_check_interval,
            "stats_enabled": self.stats_enabled,
            "stats_retention_days": self.stats_retention_days,
            "error_notification_enabled": self.error_notification_enabled,
            "error_threshold": self.error_threshold,
            "error_cooldown": self.error_cooldown
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SchedulerConfig":
        """辞書からインスタンスを作成"""
        return cls(**data)
    
    def validate(self) -> bool:
        """設定の検証"""
        try:
            if self.max_retries < 0:
                return False
            if self.retry_delay < 0:
                return False
            if self.timeout < 0:
                return False
            if self.health_check_interval < 0:
                return False
            if self.stats_retention_days < 0:
                return False
            if self.error_threshold < 0:
                return False
            if self.error_cooldown < 0:
                return False
            
            return True
            
        except Exception:
            return False
