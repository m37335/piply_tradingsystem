"""
経済イベントエンティティ
investpyから取得した経済指標データを表現するドメインエンティティ
"""

from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Optional

from src.domain.entities.base import BaseEntity


class Importance(Enum):
    """重要度の列挙型"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class EconomicEvent(BaseEntity):
    """
    経済イベントエンティティ
    
    経済指標の発表情報を表現するドメインエンティティ
    investpyから取得したデータを適切な形式に変換して保持
    """
    
    # 基本情報
    event_id: str = ""
    date_utc: datetime = field(default_factory=datetime.utcnow)
    country: str = ""
    event_name: str = ""
    time_utc: Optional[time] = None
    zone: Optional[str] = None

    # 重要度と値
    importance: Importance = Importance.LOW
    actual_value: Optional[Decimal] = None
    forecast_value: Optional[Decimal] = None
    previous_value: Optional[Decimal] = None

    # 単位情報
    currency: Optional[str] = None
    unit: Optional[str] = None
    category: Optional[str] = None

    # メタデータ
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """初期化後の処理"""
        if isinstance(self.importance, str):
            self.importance = Importance(self.importance)

        # 数値の変換
        if isinstance(self.actual_value, (int, float)):
            self.actual_value = Decimal(str(self.actual_value))
        if isinstance(self.forecast_value, (int, float)):
            self.forecast_value = Decimal(str(self.forecast_value))
        if isinstance(self.previous_value, (int, float)):
            self.previous_value = Decimal(str(self.previous_value))

    @property
    def is_high_importance(self) -> bool:
        """高重要度かどうか"""
        return self.importance == Importance.HIGH

    @property
    def is_medium_or_higher(self) -> bool:
        """中重要度以上かどうか"""
        return self.importance in [Importance.MEDIUM, Importance.HIGH]

    @property
    def has_actual_value(self) -> bool:
        """実際値があるかどうか"""
        return self.actual_value is not None

    @property
    def has_forecast_value(self) -> bool:
        """予測値があるかどうか"""
        return self.forecast_value is not None

    @property
    def has_previous_value(self) -> bool:
        """前回値があるかどうか"""
        return self.previous_value is not None

    @property
    def surprise_percentage(self) -> Optional[Decimal]:
        """サプライズ率を計算"""
        if not (self.has_actual_value and self.has_forecast_value):
            return None

        if self.forecast_value == 0:
            return None

        return ((self.actual_value - self.forecast_value) / self.forecast_value) * 100

    @property
    def forecast_change_percentage(self) -> Optional[Decimal]:
        """予測値変更率を計算"""
        if not (self.has_forecast_value and self.has_previous_value):
            return None

        if self.previous_value == 0:
            return None

        return ((self.forecast_value - self.previous_value) / self.previous_value) * 100

    @property
    def event_datetime_utc(self) -> datetime:
        """イベントの日時（UTC）を取得"""
        if self.time_utc:
            return datetime.combine(self.date_utc.date(), self.time_utc)
        return self.date_utc

    @property
    def is_upcoming(self) -> bool:
        """今後のイベントかどうか"""
        return self.event_datetime_utc > datetime.utcnow()

    @property
    def is_recent(self, hours: int = 24) -> bool:
        """最近のイベントかどうか"""
        now = datetime.utcnow()
        event_time = self.event_datetime_utc
        return abs((now - event_time).total_seconds()) <= hours * 3600

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "event_id": self.event_id,
            "date_utc": self.date_utc.isoformat(),
            "time_utc": self.time_utc.isoformat() if self.time_utc else None,
            "country": self.country,
            "zone": self.zone,
            "event_name": self.event_name,
            "importance": self.importance.value,
            "actual_value": (float(self.actual_value) if self.actual_value else None),
            "forecast_value": (
                float(self.forecast_value) if self.forecast_value else None
            ),
            "previous_value": (
                float(self.previous_value) if self.previous_value else None
            ),
            "currency": self.currency,
            "unit": self.unit,
            "category": self.category,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EconomicEvent":
        """辞書からインスタンスを作成"""
        # 日時の変換
        if "date_utc" in data and isinstance(data["date_utc"], str):
            data["date_utc"] = datetime.fromisoformat(data["date_utc"])

        if (
            "time_utc" in data
            and data["time_utc"]
            and isinstance(data["time_utc"], str)
        ):
            data["time_utc"] = time.fromisoformat(data["time_utc"])

        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])

        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        return cls(**data)

    def __eq__(self, other: object) -> bool:
        """等価性の比較"""
        if not isinstance(other, EconomicEvent):
            return False

        return (
            self.event_id == other.event_id
            and self.date_utc == other.date_utc
            and self.country == other.country
            and self.event_name == other.event_name
        )

    def __hash__(self) -> int:
        """ハッシュ値の計算"""
        return hash((self.event_id, self.date_utc, self.country, self.event_name))

    def __str__(self) -> str:
        """文字列表現"""
        return f"EconomicEvent({self.country} - {self.event_name} on {self.date_utc})"

    def __repr__(self) -> str:
        """詳細な文字列表現"""
        return (
            f"EconomicEvent("
            f"id={self.id}, "
            f"event_id='{self.event_id}', "
            f"country='{self.country}', "
            f"event_name='{self.event_name}', "
            f"importance={self.importance.value}, "
            f"date_utc={self.date_utc}"
            f")"
        )
