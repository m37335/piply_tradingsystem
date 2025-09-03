"""
Investpy設定クラス
investpyライブラリの設定を管理
"""

import os
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class InvestpyConfig:
    """Investpy設定"""
    
    # 基本設定
    default_timezone: str = "GMT +9:00"
    time_filter: str = "time_only"
    
    # デフォルト国・重要度
    default_countries: List[str] = field(default_factory=lambda: [
        "japan", "united states", "euro zone", 
        "united kingdom", "australia", "canada"
    ])
    default_importances: List[str] = field(default_factory=lambda: [
        "high", "medium"
    ])
    
    # リトライ設定
    retry_attempts: int = 3
    retry_delay: int = 5
    
    # データ取得設定
    max_events_per_request: int = 1000
    cache_duration: int = 3600  # 秒
    
    # ログ設定
    enable_debug_logging: bool = False
    log_api_calls: bool = True
    
    @property
    def max_events(self) -> int:
        """最大イベント数（エイリアス）"""
        return self.max_events_per_request
    
    @classmethod
    def from_env(cls) -> "InvestpyConfig":
        """環境変数から設定を読み込み"""
        return cls(
            default_timezone=os.getenv("INVESTPY_DEFAULT_TIMEZONE", "GMT +9:00"),
            time_filter=os.getenv("INVESTPY_TIME_FILTER", "time_only"),
            default_countries=cls._parse_countries_from_env(),
            default_importances=cls._parse_importances_from_env(),
            retry_attempts=int(os.getenv("INVESTPY_RETRY_ATTEMPTS", "3")),
            retry_delay=int(os.getenv("INVESTPY_RETRY_DELAY", "5")),
            max_events_per_request=int(os.getenv("INVESTPY_MAX_EVENTS", "1000")),
            cache_duration=int(os.getenv("INVESTPY_CACHE_DURATION", "3600")),
            enable_debug_logging=os.getenv("INVESTPY_DEBUG", "false").lower() == "true",
            log_api_calls=os.getenv("INVESTPY_LOG_API", "true").lower() == "true"
        )
    
    @staticmethod
    def _parse_countries_from_env() -> List[str]:
        """環境変数から国リストを解析"""
        countries_str = os.getenv("INVESTPY_DEFAULT_COUNTRIES", "")
        if countries_str:
            return [country.strip() for country in countries_str.split(",")]
        default_countries = [
            "japan", "united states", "euro zone", 
            "united kingdom", "australia", "canada"
        ]
        return default_countries
    
    @staticmethod
    def _parse_importances_from_env() -> List[str]:
        """環境変数から重要度リストを解析"""
        importances_str = os.getenv("INVESTPY_DEFAULT_IMPORTANCES", "")
        if importances_str:
            return [importance.strip() for importance in importances_str.split(",")]
        return ["high", "medium"]
    
    def validate(self) -> bool:
        """設定の妥当性を検証"""
        logger = logging.getLogger(self.__class__.__name__)
        
        # タイムゾーンの検証
        valid_timezones = ["GMT +9:00", "GMT +0:00", "GMT -5:00"]
        if self.default_timezone not in valid_timezones:
            logger.error(f"Invalid timezone: {self.default_timezone}")
            return False
        
        # 時間フィルターの検証
        valid_filters = ["time_only", "date_only", "both"]
        if self.time_filter not in valid_filters:
            logger.error(f"Invalid time filter: {self.time_filter}")
            return False
        
        # 国の検証
        valid_countries = [
            "japan", "united states", "euro zone", "united kingdom", 
            "australia", "canada", "china", "switzerland", "new zealand"
        ]
        for country in self.default_countries:
            if country not in valid_countries:
                logger.error(f"Invalid country: {country}")
                return False
        
        # 重要度の検証
        valid_importances = ["low", "medium", "high"]
        for importance in self.default_importances:
            if importance not in valid_importances:
                logger.error(f"Invalid importance: {importance}")
                return False
        
        # 数値の検証
        if self.retry_attempts < 1 or self.retry_attempts > 10:
            logger.error(f"Invalid retry attempts: {self.retry_attempts}")
            return False
        
        if self.retry_delay < 1 or self.retry_delay > 60:
            logger.error(f"Invalid retry delay: {self.retry_delay}")
            return False
        
        if self.max_events_per_request < 1 or self.max_events_per_request > 10000:
            logger.error(f"Invalid max events: {self.max_events_per_request}")
            return False
        
        if self.cache_duration < 0 or self.cache_duration > 86400:
            logger.error(f"Invalid cache duration: {self.cache_duration}")
            return False
        
        logger.info("Investpy configuration validation passed")
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得"""
        return {
            "default_timezone": self.default_timezone,
            "time_filter": self.time_filter,
            "default_countries": self.default_countries,
            "default_importances": self.default_importances,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "max_events_per_request": self.max_events_per_request,
            "cache_duration": self.cache_duration,
            "enable_debug_logging": self.enable_debug_logging,
            "log_api_calls": self.log_api_calls
        }
    
    def get_country_filter(self, countries: Optional[List[str]] = None) -> List[str]:
        """国フィルターを取得"""
        return countries or self.default_countries
    
    def get_importance_filter(self, importances: Optional[List[str]] = None) -> List[str]:
        """重要度フィルターを取得"""
        return importances or self.default_importances
    
    def is_debug_enabled(self) -> bool:
        """デバッグログが有効かどうか"""
        return self.enable_debug_logging
    
    def should_log_api_calls(self) -> bool:
        """API呼び出しをログに記録するかどうか"""
        return self.log_api_calls
