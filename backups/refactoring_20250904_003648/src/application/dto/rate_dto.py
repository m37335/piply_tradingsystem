"""
Rate DTOs
為替レート関連DTO

設計書参照:
- アプリケーション層設計_20250809.md
- 補足設計_Application層_20250809.md

為替レートデータの転送用DTO
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from .base_dto import BaseDTO, PaginatedDTO


@dataclass
class ExchangeRateDTO(BaseDTO):
    """
    為替レートDTO

    責任:
    - 単一為替レートデータの転送
    - エンティティ↔DTO変換
    - APIレスポンス用データ構造
    """

    id: Optional[int] = None
    uuid: Optional[str] = None
    currency_pair: str = ""
    rate: float = 0.0
    bid_rate: Optional[float] = None
    ask_rate: Optional[float] = None
    spread: Optional[float] = None
    high_rate: Optional[float] = None
    low_rate: Optional[float] = None
    open_rate: Optional[float] = None
    close_rate: Optional[float] = None
    volume: Optional[int] = None
    source: str = ""
    timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> None:
        """
        為替レートDTOのバリデーション
        """
        if not self.currency_pair:
            raise ValueError("Currency pair is required")

        if self.rate <= 0:
            raise ValueError("Rate must be positive")

        if self.bid_rate is not None and self.bid_rate < 0:
            raise ValueError("Bid rate cannot be negative")

        if self.ask_rate is not None and self.ask_rate < 0:
            raise ValueError("Ask rate cannot be negative")

        if (
            self.bid_rate is not None
            and self.ask_rate is not None
            and self.bid_rate > self.ask_rate
        ):
            raise ValueError("Bid rate cannot be higher than ask rate")

    @classmethod
    def from_entity(cls, entity) -> "ExchangeRateDTO":
        """
        ExchangeRateEntityからDTOを作成

        Args:
            entity: ExchangeRateEntity

        Returns:
            ExchangeRateDTO: 変換されたDTO
        """
        return cls(
            id=entity.id,
            uuid=entity.uuid,
            currency_pair=str(entity.currency_pair),
            rate=float(entity.rate),
            bid_rate=float(entity.bid_rate) if entity.bid_rate else None,
            ask_rate=float(entity.ask_rate) if entity.ask_rate else None,
            spread=float(entity.spread) if entity.spread else None,
            high_rate=float(entity.high_rate) if entity.high_rate else None,
            low_rate=float(entity.low_rate) if entity.low_rate else None,
            open_rate=float(entity.open_rate) if entity.open_rate else None,
            close_rate=float(entity.close_rate) if entity.close_rate else None,
            volume=entity.volume,
            source=entity.source,
            timestamp=entity.timestamp,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def to_entity(self):
        """
        DTOからExchangeRateEntityを作成

        Returns:
            ExchangeRateEntity: 変換されたエンティティ
        """
        from decimal import Decimal

        from ...domain.entities.exchange_rate import ExchangeRateEntity
        from ...domain.value_objects.currency import CurrencyCode, CurrencyPair, Price

        # 通貨ペアの解析
        base_code, quote_code = self.currency_pair.split("/")
        currency_pair = CurrencyPair(
            base=CurrencyCode(base_code), quote=CurrencyCode(quote_code)
        )

        # Price オブジェクトの作成
        rate = Price(Decimal(str(self.rate)))
        spread = Price(Decimal(str(self.spread))) if self.spread else None
        bid_rate = Price(Decimal(str(self.bid_rate))) if self.bid_rate else None
        ask_rate = Price(Decimal(str(self.ask_rate))) if self.ask_rate else None
        high_rate = Price(Decimal(str(self.high_rate))) if self.high_rate else None
        low_rate = Price(Decimal(str(self.low_rate))) if self.low_rate else None
        open_rate = Price(Decimal(str(self.open_rate))) if self.open_rate else None
        close_rate = Price(Decimal(str(self.close_rate))) if self.close_rate else None

        return ExchangeRateEntity(
            currency_pair=currency_pair,
            rate=rate,
            spread=spread,
            bid_rate=bid_rate,
            ask_rate=ask_rate,
            high_rate=high_rate,
            low_rate=low_rate,
            open_rate=open_rate,
            close_rate=close_rate,
            volume=self.volume,
            source=self.source,
            timestamp=self.timestamp,
        )

    def get_change_percentage(self, previous_rate: float) -> Optional[float]:
        """
        前回レートからの変化率を計算

        Args:
            previous_rate: 前回のレート

        Returns:
            Optional[float]: 変化率（パーセント）
        """
        if previous_rate <= 0:
            return None

        return ((self.rate - previous_rate) / previous_rate) * 100

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


@dataclass
class ExchangeRateListDTO(PaginatedDTO):
    """
    為替レートリストDTO

    責任:
    - 複数為替レートデータの転送
    - ページング情報付きリスト
    """

    items: List[ExchangeRateDTO]
    currency_pairs: Optional[List[str]] = None
    time_range_start: Optional[datetime] = None
    time_range_end: Optional[datetime] = None
    data_sources: Optional[List[str]] = None

    def validate(self) -> None:
        """
        為替レートリストDTOのバリデーション
        """
        super().validate()

        if not isinstance(self.items, list):
            raise ValueError("Items must be a list")

        for item in self.items:
            if not isinstance(item, ExchangeRateDTO):
                raise ValueError("All items must be ExchangeRateDTO instances")

    @classmethod
    def from_entities(
        cls,
        entities: List,
        total_count: int,
        page: int = 1,
        per_page: int = 100,
        **kwargs,
    ) -> "ExchangeRateListDTO":
        """
        エンティティリストからDTOを作成

        Args:
            entities: ExchangeRateEntityのリスト
            total_count: 総件数
            page: ページ番号
            per_page: ページサイズ
            **kwargs: その他のパラメータ

        Returns:
            ExchangeRateListDTO: 変換されたDTO
        """
        items = [ExchangeRateDTO.from_entity(entity) for entity in entities]

        return cls(
            items=items, total_count=total_count, page=page, per_page=per_page, **kwargs
        )

    def get_currency_pairs_summary(self) -> Dict[str, int]:
        """
        通貨ペア別のデータ件数サマリーを取得

        Returns:
            Dict[str, int]: 通貨ペア別件数
        """
        summary = {}
        for item in self.items:
            pair = item.currency_pair
            summary[pair] = summary.get(pair, 0) + 1
        return summary

    def get_sources_summary(self) -> Dict[str, int]:
        """
        データソース別のデータ件数サマリーを取得

        Returns:
            Dict[str, int]: データソース別件数
        """
        summary = {}
        for item in self.items:
            source = item.source
            summary[source] = summary.get(source, 0) + 1
        return summary

    def get_time_range_summary(self) -> Dict[str, Any]:
        """
        時間範囲のサマリーを取得

        Returns:
            Dict[str, Any]: 時間範囲情報
        """
        if not self.items:
            return {"start": None, "end": None, "duration_hours": 0}

        timestamps = [item.timestamp for item in self.items if item.timestamp]
        if not timestamps:
            return {"start": None, "end": None, "duration_hours": 0}

        start_time = min(timestamps)
        end_time = max(timestamps)
        duration = (end_time - start_time).total_seconds() / 3600

        return {
            "start": start_time,
            "end": end_time,
            "duration_hours": round(duration, 2),
        }


@dataclass
class RateStatisticsDTO(BaseDTO):
    """
    為替レート統計DTO

    責任:
    - 為替レートの統計情報転送
    - 分析結果データ構造
    """

    currency_pair: str
    period_start: datetime
    period_end: datetime
    min_rate: float
    max_rate: float
    avg_rate: float
    median_rate: Optional[float] = None
    std_deviation: Optional[float] = None
    volatility: Optional[float] = None
    data_points: int = 0
    trading_volume: Optional[int] = None

    def validate(self) -> None:
        """
        統計DTOのバリデーション
        """
        if not self.currency_pair:
            raise ValueError("Currency pair is required")

        if self.period_start >= self.period_end:
            raise ValueError("Period start must be before period end")

        if self.min_rate <= 0 or self.max_rate <= 0 or self.avg_rate <= 0:
            raise ValueError("Rates must be positive")

        if self.min_rate > self.max_rate:
            raise ValueError("Min rate cannot be higher than max rate")

        if self.data_points < 0:
            raise ValueError("Data points cannot be negative")

    def get_price_range(self) -> float:
        """
        価格レンジを取得

        Returns:
            float: 価格レンジ（max - min）
        """
        return self.max_rate - self.min_rate

    def get_price_range_percentage(self) -> float:
        """
        価格レンジの割合を取得

        Returns:
            float: 価格レンジの割合
        """
        return (self.get_price_range() / self.min_rate) * 100

    def get_period_duration_hours(self) -> float:
        """
        期間の長さを時間単位で取得

        Returns:
            float: 期間の長さ（時間）
        """
        return (self.period_end - self.period_start).total_seconds() / 3600


@dataclass
class RateFetchResultDTO(BaseDTO):
    """
    為替レート取得結果DTO

    責任:
    - レート取得処理の結果転送
    - 処理統計情報
    """

    command_id: str
    currency_pairs: List[str]
    source: str
    interval: str
    fetched_records: int = 0
    saved_records: int = 0
    skipped_records: int = 0
    processing_time: float = 0.0
    errors: List[str] = None
    success: bool = True
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """
        初期化後処理
        """
        if self.errors is None:
            self.errors = []

        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

        # エラーがある場合は success フラグを更新
        if self.errors:
            object.__setattr__(self, "success", False)

        super().__post_init__()

    def validate(self) -> None:
        """
        取得結果DTOのバリデーション
        """
        if not self.command_id:
            raise ValueError("Command ID is required")

        if not self.currency_pairs:
            raise ValueError("Currency pairs are required")

        if self.fetched_records < 0:
            raise ValueError("Fetched records cannot be negative")

        if self.saved_records < 0:
            raise ValueError("Saved records cannot be negative")

        if self.skipped_records < 0:
            raise ValueError("Skipped records cannot be negative")

        if self.processing_time < 0:
            raise ValueError("Processing time cannot be negative")

    def get_success_rate(self) -> float:
        """
        成功率を取得

        Returns:
            float: 成功率（0-100）
        """
        if self.fetched_records == 0:
            return 0.0

        return (self.saved_records / self.fetched_records) * 100

    def get_skip_rate(self) -> float:
        """
        スキップ率を取得

        Returns:
            float: スキップ率（0-100）
        """
        if self.fetched_records == 0:
            return 0.0

        return (self.skipped_records / self.fetched_records) * 100

    def get_processing_summary(self) -> Dict[str, Any]:
        """
        処理サマリーを取得

        Returns:
            Dict[str, Any]: 処理サマリー
        """
        return {
            "total_pairs": len(self.currency_pairs),
            "fetched_records": self.fetched_records,
            "saved_records": self.saved_records,
            "skipped_records": self.skipped_records,
            "success_rate": round(self.get_success_rate(), 2),
            "skip_rate": round(self.get_skip_rate(), 2),
            "processing_time": round(self.processing_time, 3),
            "errors_count": len(self.errors),
            "records_per_second": (
                round(self.fetched_records / self.processing_time, 2)
                if self.processing_time > 0
                else 0
            ),
        }
