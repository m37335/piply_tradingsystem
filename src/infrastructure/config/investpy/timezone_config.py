"""
タイムゾーン設定クラス
タイムゾーン関連の設定を管理
"""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class TimezoneConfig:
    """タイムゾーン設定"""

    # デフォルトタイムゾーン
    default_timezone: str = "Asia/Tokyo"
    display_timezone: str = "Asia/Tokyo"

    # サポートするタイムゾーン
    supported_timezones: Dict[str, str] = None

    # 日付・時刻フォーマット
    date_format: str = "%Y-%m-%d"
    time_format: str = "%H:%M:%S"
    datetime_format: str = "%Y-%m-%d %H:%M:%S"

    # 夏時間設定
    enable_dst_handling: bool = True
    dst_start_month: int = 3
    dst_end_month: int = 11
    
    @property
    def dst_handling(self) -> bool:
        """夏時間処理の有効性（エイリアス）"""
        return self.enable_dst_handling

    def __post_init__(self):
        """初期化後の処理"""
        if self.supported_timezones is None:
            self.supported_timezones = {
                "Asia/Tokyo": "日本標準時 (JST)",
                "UTC": "協定世界時 (UTC)",
                "America/New_York": "東部標準時 (EST/EDT)",
                "Europe/London": "グリニッジ標準時 (GMT/BST)",
                "Europe/Berlin": "中央ヨーロッパ時間 (CET/CEST)",
                "Australia/Sydney": "オーストラリア東部時間 (AEST/AEDT)",
            }

    @classmethod
    def from_env(cls) -> "TimezoneConfig":
        """環境変数から設定を読み込み"""
        return cls(
            default_timezone=os.getenv("TIMEZONE_DEFAULT", "Asia/Tokyo"),
            display_timezone=os.getenv("TIMEZONE_DISPLAY", "Asia/Tokyo"),
            date_format=os.getenv("TIMEZONE_DATE_FORMAT", "%Y-%m-%d"),
            time_format=os.getenv("TIMEZONE_TIME_FORMAT", "%H:%M:%S"),
            datetime_format=os.getenv("TIMEZONE_DATETIME_FORMAT", "%Y-%m-%d %H:%M:%S"),
            enable_dst_handling=os.getenv("TIMEZONE_ENABLE_DST", "true").lower()
            == "true",
            dst_start_month=int(os.getenv("TIMEZONE_DST_START_MONTH", "3")),
            dst_end_month=int(os.getenv("TIMEZONE_DST_END_MONTH", "11")),
        )

    def validate(self) -> bool:
        """設定の妥当性を検証"""
        logger = logging.getLogger(self.__class__.__name__)

        # タイムゾーンの検証
        if self.default_timezone not in self.supported_timezones:
            logger.error(f"Unsupported default timezone: {self.default_timezone}")
            return False

        if self.display_timezone not in self.supported_timezones:
            logger.error(f"Unsupported display timezone: {self.display_timezone}")
            return False

        # フォーマットの検証
        required_format_chars = ["%Y", "%m", "%d", "%H", "%M", "%S"]
        for format_str in [self.date_format, self.time_format, self.datetime_format]:
            if not any(char in format_str for char in required_format_chars):
                logger.error(f"Invalid format string: {format_str}")
                return False

        # 夏時間設定の検証
        if self.dst_start_month < 1 or self.dst_start_month > 12:
            logger.error(f"Invalid DST start month: {self.dst_start_month}")
            return False

        if self.dst_end_month < 1 or self.dst_end_month > 12:
            logger.error(f"Invalid DST end month: {self.dst_end_month}")
            return False

        if self.dst_start_month >= self.dst_end_month:
            logger.error("DST start month must be before end month")
            return False

        logger.info("Timezone configuration validation passed")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """設定を辞書形式で取得"""
        return {
            "default_timezone": self.default_timezone,
            "display_timezone": self.display_timezone,
            "supported_timezones": self.supported_timezones,
            "date_format": self.date_format,
            "time_format": self.time_format,
            "datetime_format": self.datetime_format,
            "enable_dst_handling": self.enable_dst_handling,
            "dst_start_month": self.dst_start_month,
            "dst_end_month": self.dst_end_month,
        }

    def get_timezone_display_name(self, timezone: str) -> str:
        """タイムゾーンの表示名を取得"""
        return self.supported_timezones.get(timezone, timezone)

    def is_timezone_supported(self, timezone: str) -> bool:
        """タイムゾーンがサポートされているかどうか"""
        return timezone in self.supported_timezones

    def get_supported_timezone_list(self) -> list:
        """サポートされているタイムゾーンのリストを取得"""
        return list(self.supported_timezones.keys())

    def should_handle_dst(self) -> bool:
        """夏時間処理を有効にするかどうか"""
        return self.enable_dst_handling

    def get_dst_period(self) -> tuple:
        """夏時間期間を取得"""
        return (self.dst_start_month, self.dst_end_month)
