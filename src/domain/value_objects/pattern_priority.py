"""
パターン優先度値オブジェクト

通知パターンの優先度を管理する値オブジェクト
"""

from enum import Enum
from typing import Optional


class PatternPriority(Enum):
    """パターン優先度の列挙型"""

    # 高優先度（即座通知）
    HIGH = 100  # パターン1: 強力なトレンド転換シグナル
    VERY_HIGH = 90  # パターン6: 複合シグナル強化

    # 中優先度（1-2週間後）
    MEDIUM = 70  # パターン2, 2-2, 3, 4: 各種チャンス・警戒シグナル

    # 低優先度（3-4週間後）
    LOW = 50  # パターン5: RSI50ライン攻防

    @classmethod
    def from_pattern_number(cls, pattern_number: int) -> "PatternPriority":
        """パターン番号から優先度を取得"""
        priority_map = {
            1: cls.HIGH,
            2: cls.MEDIUM,
            3: cls.MEDIUM,
            4: cls.MEDIUM,
            5: cls.LOW,
            6: cls.VERY_HIGH,
        }
        return priority_map.get(pattern_number, cls.LOW)

    @classmethod
    def from_string(cls, priority_str: str) -> Optional["PatternPriority"]:
        """文字列から優先度を取得"""
        try:
            return cls[priority_str.upper()]
        except KeyError:
            return None

    def get_notification_delay(self) -> int:
        """優先度に基づく通知遅延時間（秒）を取得"""
        delay_map = {
            self.VERY_HIGH: 0,  # 即座通知
            self.HIGH: 0,  # 即座通知
            self.MEDIUM: 300,  # 5分遅延
            self.LOW: 600,  # 10分遅延
        }
        return delay_map.get(self, 600)

    def get_color(self) -> str:
        """優先度に基づくDiscord通知色を取得"""
        color_map = {
            self.VERY_HIGH: "0x800080",  # 紫（最高優先度）
            self.HIGH: "0xFF0000",  # 赤（高優先度）
            self.MEDIUM: "0x00FF00",  # 緑（中優先度）
            self.LOW: "0x808080",  # グレー（低優先度）
        }
        return color_map.get(self, "0x808080")

    def __str__(self) -> str:
        return f"{self.name} ({self.value})"

    def __repr__(self) -> str:
        return f"PatternPriority.{self.name}"
