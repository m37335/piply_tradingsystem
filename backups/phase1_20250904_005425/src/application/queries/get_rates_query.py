"""
Get Rates Query
為替レート取得クエリ

設計書参照:
- アプリケーション層設計_20250809.md

為替レートデータの検索・取得を行うクエリ
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ...domain.entities.exchange_rate import ExchangeRateEntity
from ...utils.logging_config import get_application_logger
from .base import BaseQuery

logger = get_application_logger()


class SortOrder(Enum):
    """ソート順序"""

    ASC = "asc"
    DESC = "desc"


class SortField(Enum):
    """ソートフィールド"""

    TIMESTAMP = "timestamp"
    RATE = "rate"
    VOLUME = "volume"
    CREATED_AT = "created_at"


@dataclass
class GetRatesQuery(BaseQuery[List[ExchangeRateEntity]]):
    """
    為替レート取得クエリ

    責任:
    - 為替レートの検索条件指定
    - ページング・ソート・フィルタリング
    - パフォーマンス最適化
    """

    # フィルタリング条件
    currency_pairs: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    sources: Optional[List[str]] = None
    min_rate: Optional[float] = None
    max_rate: Optional[float] = None

    # ページング
    limit: int = 100
    offset: int = 0

    # ソート
    sort_field: SortField = SortField.TIMESTAMP
    sort_order: SortOrder = SortOrder.DESC

    # その他オプション
    include_stale: bool = False
    max_age_minutes: int = 60

    def __post_init__(self) -> None:
        """
        初期化後処理
        バリデーションとデフォルト値設定
        """
        super().__post_init__()
        self.validate()

        # デフォルト時間範囲の設定
        if not self.start_time and not self.end_time:
            self.end_time = datetime.utcnow()
            self.start_time = self.end_time - timedelta(hours=24)  # デフォルト24時間

        # メタデータに追加情報を設定
        self.add_metadata(
            "currency_pairs_count",
            len(self.currency_pairs) if self.currency_pairs else 0,
        )
        self.add_metadata("time_range_hours", self._get_time_range_hours())
        self.add_metadata("estimated_records", self._estimate_record_count())

    def validate(self) -> None:
        """
        クエリのバリデーション

        Raises:
            ValueError: バリデーションエラー
        """
        super().validate()

        # 通貨ペアの検証
        if self.currency_pairs:
            if len(self.currency_pairs) > 50:
                raise ValueError("Too many currency pairs (max: 50)")

            for pair in self.currency_pairs:
                if not isinstance(pair, str) or len(pair.strip()) == 0:
                    raise ValueError(f"Invalid currency pair: {pair}")

        # 時間範囲の検証
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError("Start time must be before end time")

            # 最大90日の制限
            if (self.end_time - self.start_time).days > 90:
                raise ValueError("Time range cannot exceed 90 days")

        # レート範囲の検証
        if self.min_rate is not None and self.min_rate < 0:
            raise ValueError("Min rate cannot be negative")

        if self.max_rate is not None and self.max_rate < 0:
            raise ValueError("Max rate cannot be negative")

        if (
            self.min_rate is not None
            and self.max_rate is not None
            and self.min_rate >= self.max_rate
        ):
            raise ValueError("Min rate must be less than max rate")

        # ページングの検証
        if self.limit <= 0 or self.limit > 10000:
            raise ValueError("Limit must be between 1 and 10000")

        if self.offset < 0:
            raise ValueError("Offset cannot be negative")

        # 最大経過時間の検証
        if self.max_age_minutes <= 0 or self.max_age_minutes > 43200:  # 30日
            raise ValueError("Max age minutes must be between 1 and 43200")

    def _get_time_range_hours(self) -> Optional[float]:
        """
        時間範囲を時間単位で取得

        Returns:
            Optional[float]: 時間範囲（時間）
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        return None

    def _estimate_record_count(self) -> int:
        """
        推定レコード数を計算

        Returns:
            int: 推定レコード数
        """
        base_count = self.limit

        # 時間範囲による推定
        hours = self._get_time_range_hours()
        if hours:
            # 1時間あたり平均60レコード（1分間隔）と仮定
            estimated = int(hours * 60)
            if self.currency_pairs:
                estimated *= len(self.currency_pairs)
            base_count = min(estimated, self.limit)

        return base_count

    def get_normalized_currency_pairs(self) -> Optional[List[str]]:
        """
        正規化された通貨ペアを取得

        Returns:
            Optional[List[str]]: 正規化された通貨ペアリスト
        """
        if not self.currency_pairs:
            return None

        normalized = []
        for pair in self.currency_pairs:
            pair = pair.strip().upper()
            if "/" not in pair and len(pair) == 6:
                # USDJPY -> USD/JPY
                pair = f"{pair[:3]}/{pair[3:]}"
            normalized.append(pair)

        return normalized

    def get_filter_conditions(self) -> Dict[str, Any]:
        """
        フィルタ条件を辞書形式で取得

        Returns:
            Dict[str, Any]: フィルタ条件
        """
        conditions = {}

        if self.currency_pairs:
            conditions["currency_pairs"] = self.get_normalized_currency_pairs()

        if self.start_time:
            conditions["start_time"] = self.start_time

        if self.end_time:
            conditions["end_time"] = self.end_time

        if self.sources:
            conditions["sources"] = self.sources

        if self.min_rate is not None:
            conditions["min_rate"] = self.min_rate

        if self.max_rate is not None:
            conditions["max_rate"] = self.max_rate

        if not self.include_stale:
            conditions["max_age_minutes"] = self.max_age_minutes

        return conditions

    def get_pagination_info(self) -> Dict[str, int]:
        """
        ページング情報を取得

        Returns:
            Dict[str, int]: ページング情報
        """
        return {
            "limit": self.limit,
            "offset": self.offset,
            "page": (self.offset // self.limit) + 1,
            "per_page": self.limit,
        }

    def get_sort_info(self) -> Dict[str, str]:
        """
        ソート情報を取得

        Returns:
            Dict[str, str]: ソート情報
        """
        return {"field": self.sort_field.value, "order": self.sort_order.value}

    def is_large_query(self) -> bool:
        """
        大量データ取得クエリかどうかを判定

        Returns:
            bool: 大量データ取得の場合True
        """
        # 複数条件で大量データと判定
        conditions = [
            self.limit > 1000,
            len(self.currency_pairs) > 10 if self.currency_pairs else False,
            self._get_time_range_hours()
            and self._get_time_range_hours() > 24 * 7,  # 1週間以上
            self._estimate_record_count() > 5000,
        ]

        return any(conditions)

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換

        Returns:
            Dict[str, Any]: クエリの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "currency_pairs": self.currency_pairs,
                "normalized_pairs": self.get_normalized_currency_pairs(),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "sources": self.sources,
                "min_rate": self.min_rate,
                "max_rate": self.max_rate,
                "limit": self.limit,
                "offset": self.offset,
                "sort_field": self.sort_field.value,
                "sort_order": self.sort_order.value,
                "include_stale": self.include_stale,
                "max_age_minutes": self.max_age_minutes,
                "filter_conditions": self.get_filter_conditions(),
                "pagination_info": self.get_pagination_info(),
                "sort_info": self.get_sort_info(),
                "is_large_query": self.is_large_query(),
            }
        )
        return base_dict

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: クエリの文字列表現
        """
        conditions = []

        if self.currency_pairs:
            pairs_str = ", ".join(self.currency_pairs[:2])
            if len(self.currency_pairs) > 2:
                pairs_str += f" (+{len(self.currency_pairs) - 2})"
            conditions.append(f"pairs=[{pairs_str}]")

        if self.start_time and self.end_time:
            hours = self._get_time_range_hours()
            conditions.append(f"timeRange={hours:.1f}h")

        conditions.append(f"limit={self.limit}")

        return f"GetRatesQuery({', '.join(conditions)})"
