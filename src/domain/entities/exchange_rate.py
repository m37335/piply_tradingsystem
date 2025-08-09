"""
Exchange Rate Entity
為替レートエンティティ

設計書参照:
- 詳細内部設計_20250809.md

為替レートの履歴データを管理するエンティティ
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from ..value_objects.currency import CurrencyPair
from ..value_objects.currency import ExchangeRate as ExchangeRateVO
from ..value_objects.currency import Price
from .base import BaseEntity


@dataclass
class ExchangeRateEntity(BaseEntity):
    """
    為替レートエンティティ

    責任:
    - 為替レートの履歴データ管理
    - データの永続化ライフサイクル
    - ビジネスルールの適用
    """

    # Required fields - use factory to avoid default argument issue
    currency_pair: CurrencyPair = field(default=None)
    rate: Price = field(default=None)

    # Optional fields (with defaults)
    spread: Optional[Price] = None
    bid_rate: Optional[Price] = None
    ask_rate: Optional[Price] = None
    high_rate: Optional[Price] = None
    low_rate: Optional[Price] = None
    open_rate: Optional[Price] = None
    close_rate: Optional[Price] = None
    volume: Optional[int] = None
    source: str = "unknown"
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """
        初期化後処理
        必須フィールドの検証とビッド・アスクレートの自動計算
        """
        # 必須フィールドの検証
        if self.currency_pair is None:
            raise ValueError("currency_pair is required")
        if self.rate is None:
            raise ValueError("rate is required")

        super().__post_init__()

        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

        # スプレッドからビッド・アスクレートを計算
        if self.spread and not (self.bid_rate and self.ask_rate):
            self._calculate_bid_ask_from_spread()

    def _calculate_bid_ask_from_spread(self) -> None:
        """
        スプレッドからビッド・アスクレートを計算
        """
        if not self.spread:
            return

        from decimal import Decimal

        half_spread = self.spread.divide(Decimal("2"))

        if not self.bid_rate:
            object.__setattr__(self, "bid_rate", self.rate.subtract(half_spread))

        if not self.ask_rate:
            object.__setattr__(self, "ask_rate", self.rate.add(half_spread))

    def get_exchange_rate_vo(self) -> ExchangeRateVO:
        """
        為替レート値オブジェクトを取得

        Returns:
            ExchangeRateVO: 為替レート値オブジェクト
        """
        return ExchangeRateVO(
            pair=self.currency_pair, rate=self.rate, spread=self.spread
        )

    def is_stale(self, max_age_minutes: int = 5) -> bool:
        """
        データが古いかどうかを判定

        Args:
            max_age_minutes: 最大有効時間（分）

        Returns:
            bool: データが古い場合True
        """
        if not self.timestamp:
            return True

        age = datetime.utcnow() - self.timestamp
        return age.total_seconds() > (max_age_minutes * 60)

    def calculate_percentage_change(self, previous_rate: "ExchangeRateEntity") -> float:
        """
        前回レートからの変化率を計算

        Args:
            previous_rate: 前回の為替レート

        Returns:
            float: 変化率（パーセント）
        """
        if previous_rate.rate.value == 0:
            return 0.0

        change = self.rate.value - previous_rate.rate.value
        return float((change / previous_rate.rate.value) * 100)

    def is_within_range(self, min_rate: Price, max_rate: Price) -> bool:
        """
        指定された範囲内のレートかどうかを判定

        Args:
            min_rate: 最小レート
            max_rate: 最大レート

        Returns:
            bool: 範囲内の場合True
        """
        return min_rate.value <= self.rate.value <= max_rate.value

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換（エンティティ固有のフィールドを追加）

        Returns:
            Dict[str, Any]: エンティティの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "currency_pair": str(self.currency_pair),
                "rate": float(self.rate),
                "spread": float(self.spread) if self.spread else None,
                "bid_rate": float(self.bid_rate) if self.bid_rate else None,
                "ask_rate": float(self.ask_rate) if self.ask_rate else None,
                "high_rate": float(self.high_rate) if self.high_rate else None,
                "low_rate": float(self.low_rate) if self.low_rate else None,
                "open_rate": float(self.open_rate) if self.open_rate else None,
                "close_rate": float(self.close_rate) if self.close_rate else None,
                "volume": self.volume,
                "source": self.source,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            }
        )
        return base_dict

    def __str__(self) -> str:
        return f"ExchangeRate({self.currency_pair}: {self.rate} at {self.timestamp})"
