"""
Fetch Rates Command
為替レート取得コマンド

設計書参照:
- アプリケーション層設計_20250809.md

外部APIから為替レートデータを取得するコマンド
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ...utils.logging_config import get_application_logger
from .base import BaseCommand

logger = get_application_logger()


class DataSource(Enum):
    """データソース種別"""

    ALPHA_VANTAGE = "alpha_vantage"
    YAHOO_FINANCE = "yahoo_finance"
    MOCK = "mock"


class TimeInterval(Enum):
    """時間間隔"""

    ONE_MINUTE = "1m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    ONE_HOUR = "1h"
    FOUR_HOURS = "4h"
    ONE_DAY = "1d"


@dataclass
class FetchRatesCommand(BaseCommand):
    """
    為替レート取得コマンド

    責任:
    - 外部APIからの為替レートデータ取得指示
    - 取得パラメータの管理とバリデーション
    - データソースの指定
    """

    # 必須フィールド
    currency_pairs: List[str] = None

    # オプションフィールド
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    interval: TimeInterval = TimeInterval.ONE_MINUTE
    source: DataSource = DataSource.ALPHA_VANTAGE
    max_records: int = 1000
    force_refresh: bool = False

    def __post_init__(self) -> None:
        """
        初期化後処理
        バリデーションとデフォルト値設定
        """
        if self.currency_pairs is None:
            self.currency_pairs = []

        super().__post_init__()
        self.validate()

        # メタデータに追加情報を設定
        self.add_metadata("currency_pairs_count", len(self.currency_pairs))
        self.add_metadata("data_source", self.source.value)
        self.add_metadata("time_interval", self.interval.value)

    def validate(self) -> None:
        """
        コマンドのバリデーション

        Raises:
            ValueError: バリデーションエラー
        """
        super().validate()

        if not self.currency_pairs:
            raise ValueError("Currency pairs are required")

        if len(self.currency_pairs) > 20:
            raise ValueError("Too many currency pairs (max: 20)")

        # 通貨ペア形式の検証
        for pair in self.currency_pairs:
            if not isinstance(pair, str):
                raise ValueError(f"Currency pair must be string: {pair}")

            # USD/JPY or USDJPY 形式をサポート
            if "/" in pair:
                parts = pair.split("/")
                if len(parts) != 2 or len(parts[0]) != 3 or len(parts[1]) != 3:
                    raise ValueError(f"Invalid currency pair format: {pair}")
            else:
                if len(pair) != 6:
                    raise ValueError(f"Invalid currency pair format: {pair}")

        # 時間範囲の検証
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValueError("Start time must be before end time")

        # レコード数の検証
        if self.max_records <= 0 or self.max_records > 10000:
            raise ValueError("Max records must be between 1 and 10000")

    def get_normalized_currency_pairs(self) -> List[str]:
        """
        正規化された通貨ペアを取得

        Returns:
            List[str]: USD/JPY形式に正規化された通貨ペアリスト
        """
        normalized = []
        for pair in self.currency_pairs:
            if "/" in pair:
                normalized.append(pair.upper())
            else:
                # USDJPY -> USD/JPY
                if len(pair) == 6:
                    base = pair[:3].upper()
                    quote = pair[3:].upper()
                    normalized.append(f"{base}/{quote}")
                else:
                    normalized.append(pair.upper())
        return normalized

    def get_lookback_hours(self) -> int:
        """
        デフォルトの取得期間（時間）を計算

        Returns:
            int: 取得期間（時間）
        """
        if self.start_time and self.end_time:
            return int((self.end_time - self.start_time).total_seconds() / 3600)

        # インターバル別デフォルト期間
        default_periods = {
            TimeInterval.ONE_MINUTE: 24,  # 1日分
            TimeInterval.FIVE_MINUTES: 120,  # 5日分
            TimeInterval.FIFTEEN_MINUTES: 360,  # 15日分
            TimeInterval.THIRTY_MINUTES: 720,  # 30日分
            TimeInterval.ONE_HOUR: 720,  # 30日分
            TimeInterval.FOUR_HOURS: 2160,  # 90日分
            TimeInterval.ONE_DAY: 8760,  # 1年分
        }

        return default_periods.get(self.interval, 24)

    def get_estimated_records(self) -> int:
        """
        推定取得レコード数を計算

        Returns:
            int: 推定レコード数
        """
        hours = self.get_lookback_hours()

        records_per_hour = {
            TimeInterval.ONE_MINUTE: 60,
            TimeInterval.FIVE_MINUTES: 12,
            TimeInterval.FIFTEEN_MINUTES: 4,
            TimeInterval.THIRTY_MINUTES: 2,
            TimeInterval.ONE_HOUR: 1,
            TimeInterval.FOUR_HOURS: 0.25,
            TimeInterval.ONE_DAY: 0.04,
        }

        per_hour = records_per_hour.get(self.interval, 1)
        total_records = int(hours * per_hour * len(self.currency_pairs))

        return min(total_records, self.max_records)

    def is_high_volume_request(self) -> bool:
        """
        高ボリュームリクエストかどうかを判定

        Returns:
            bool: 高ボリュームの場合True
        """
        estimated = self.get_estimated_records()
        return estimated > 5000 or len(self.currency_pairs) > 10

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換

        Returns:
            Dict[str, Any]: コマンドの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "currency_pairs": self.currency_pairs,
                "normalized_pairs": self.get_normalized_currency_pairs(),
                "start_time": self.start_time.isoformat() if self.start_time else None,
                "end_time": self.end_time.isoformat() if self.end_time else None,
                "interval": self.interval.value,
                "source": self.source.value,
                "max_records": self.max_records,
                "force_refresh": self.force_refresh,
                "estimated_records": self.get_estimated_records(),
                "is_high_volume": self.is_high_volume_request(),
            }
        )
        return base_dict

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: コマンドの文字列表現
        """
        pairs_str = ", ".join(self.currency_pairs[:3])
        if len(self.currency_pairs) > 3:
            pairs_str += f" (+{len(self.currency_pairs) - 3} more)"

        return (
            f"FetchRatesCommand("
            f"pairs=[{pairs_str}], "
            f"interval={self.interval.value}, "
            f"source={self.source.value})"
        )
