"""
価格データモデル

USD/JPY特化の5分おきデータ取得システム用の価格データモデル
設計書参照: /app/note/database_implementation_design_2025.md
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base

from ....utils.logging_config import get_infrastructure_logger
from .base import BaseModel

logger = get_infrastructure_logger()

Base = declarative_base()


class PriceDataModel(BaseModel):
    """
    価格データモデル

    責任:
    - USD/JPYの5分間隔価格データの保存
    - OHLCVデータの管理
    - データソース情報の記録
    - タイムスタンプ管理

    特徴:
    - USD/JPY特化設計
    - 高精度価格データ（DECIMAL(10,5)）
    - インデックス最適化
    - バリデーション機能
    """

    __tablename__ = "price_data"

    # 主キー（SQLite互換）
    id = Column(Integer, primary_key=True, autoincrement=True)

    # 通貨ペア（USD/JPY固定）
    currency_pair = Column(
        String(10),
        nullable=False,
        default="USD/JPY",
        comment="通貨ペア（USD/JPY固定）",
    )

    # タイムスタンプ（5分間隔）
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="5分間隔のタイムスタンプ",
    )

    # データの実際のタイムスタンプ（Yahoo Financeから取得）
    data_timestamp = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="データの実際のタイムスタンプ（Yahoo Financeから取得）",
    )

    # データ取得実行時刻
    fetched_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="データ取得実行時刻",
    )

    # OHLCVデータ
    open_price = Column(
        DECIMAL(10, 5),
        nullable=False,
        comment="始値",
    )

    high_price = Column(
        DECIMAL(10, 5),
        nullable=False,
        comment="高値",
    )

    low_price = Column(
        DECIMAL(10, 5),
        nullable=False,
        comment="安値",
    )

    close_price = Column(
        DECIMAL(10, 5),
        nullable=False,
        comment="終値",
    )

    volume = Column(
        BigInteger,
        nullable=True,
        comment="取引量（利用可能な場合）",
    )

    # データソース情報
    data_source = Column(
        String(50),
        nullable=False,
        default="Yahoo Finance",
        comment="データソース（Yahoo Finance等）",
    )

    # メタデータ
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        comment="作成日時",
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now(),
        onupdate=func.now(),
        comment="更新日時",
    )

    # インデックス
    __table_args__ = (
        # 通貨ペア・タイムスタンプ・データソースの複合ユニーク制約
        UniqueConstraint(
            "currency_pair",
            "timestamp",
            "data_source",
            name="idx_price_data_currency_timestamp_source",
        ),
        # タイムスタンプインデックス（降順）
        Index(
            "idx_price_data_timestamp",
            "timestamp",
            postgresql_ops={"timestamp": "DESC"},
        ),
        # 通貨ペアインデックス
        Index("idx_price_data_currency", "currency_pair"),
        # 複合インデックス（通貨ペア・タイムスタンプ降順）
        Index(
            "idx_price_data_currency_timestamp_composite",
            "currency_pair",
            "timestamp",
            postgresql_ops={"timestamp": "DESC"},
        ),
        # SQLite AUTOINCREMENT設定
        {"sqlite_autoincrement": True},
    )

    def __init__(
        self,
        currency_pair: str = "USD/JPY",
        timestamp: datetime = None,
        data_timestamp: datetime = None,
        fetched_at: datetime = None,
        open_price: float = None,
        high_price: float = None,
        low_price: float = None,
        close_price: float = None,
        volume: Optional[int] = None,
        data_source: str = "Yahoo Finance",
    ):
        """
        初期化

        Args:
            currency_pair: 通貨ペア（デフォルト: USD/JPY）
            timestamp: タイムスタンプ
            open_price: 始値
            high_price: 高値
            low_price: 安値
            close_price: 終値
            volume: 取引量
            data_source: データソース
        """
        super().__init__()
        self.currency_pair = currency_pair
        self.timestamp = timestamp or datetime.utcnow()
        self.data_timestamp = data_timestamp
        self.fetched_at = fetched_at or datetime.utcnow()
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.data_source = data_source

    def __repr__(self) -> str:
        """文字列表現"""
        return (
            f"<PriceDataModel("
            f"id={self.id}, "
            f"currency_pair='{self.currency_pair}', "
            f"timestamp='{self.timestamp}', "
            f"close_price={self.close_price}"
            f")>"
        )

    def to_dict(self) -> dict:
        """
        辞書形式に変換

        Returns:
            dict: 辞書形式のデータ
        """
        return {
            "id": self.id,
            "currency_pair": self.currency_pair,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "open_price": float(self.open_price) if self.open_price else None,
            "high_price": float(self.high_price) if self.high_price else None,
            "low_price": float(self.low_price) if self.low_price else None,
            "close_price": float(self.close_price) if self.close_price else None,
            "volume": self.volume,
            "data_source": self.data_source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PriceDataModel":
        """
        辞書からインスタンス作成

        Args:
            data: 辞書データ

        Returns:
            PriceDataModel: インスタンス
        """
        return cls(
            currency_pair=data.get("currency_pair", "USD/JPY"),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if data.get("timestamp")
                else None
            ),
            open_price=data.get("open_price"),
            high_price=data.get("high_price"),
            low_price=data.get("low_price"),
            close_price=data.get("close_price"),
            volume=data.get("volume"),
            data_source=data.get("data_source", "Yahoo Finance"),
        )

    def validate(self) -> bool:
        """
        データバリデーション

        Returns:
            bool: バリデーション結果
        """
        # 通貨ペアチェック
        if self.currency_pair != "USD/JPY":
            return False

        # 価格データチェック
        if not all(
            [
                self.open_price is not None,
                self.high_price is not None,
                self.low_price is not None,
                self.close_price is not None,
            ]
        ):
            return False

        # 価格の論理チェック（休日データを考慮して緩和）
        if self.high_price < self.low_price:
            return False

        # データクリーニング：OHLCの整合性を保つ
        max_oc = max(self.open_price, self.close_price)
        min_oc = min(self.open_price, self.close_price)

        # HighがOpen/Closeの最大値より小さい場合は修正
        if self.high_price < max_oc:
            logger.info(f"Correcting high price from {self.high_price} to {max_oc}")
            self.high_price = max_oc

        # LowがOpen/Closeの最小値より大きい場合は修正
        if self.low_price > min_oc:
            logger.info(f"Correcting low price from {self.low_price} to {min_oc}")
            self.low_price = min_oc

        # Volumeが0でも有効なデータの場合があるため、Volumeによる除外は行わない
        # データクリーニングによりOHLCの整合性を保つ

        # タイムスタンプチェック
        if self.timestamp is None:
            return False

        return True

    def get_price_change(self) -> Optional[float]:
        """
        価格変化率を取得

        Returns:
            Optional[float]: 価格変化率（%）
        """
        if self.open_price and self.close_price and self.open_price > 0:
            return ((self.close_price - self.open_price) / self.open_price) * 100
        return None

    def get_price_range(self) -> Optional[float]:
        """
        価格レンジを取得

        Returns:
            Optional[float]: 価格レンジ（高値 - 安値）
        """
        if self.high_price and self.low_price:
            return float(self.high_price - self.low_price)
        return None

    def get_typical_price(self) -> Optional[float]:
        """
        典型価格を取得（(高値 + 安値 + 終値) / 3）

        Returns:
            Optional[float]: 典型価格
        """
        if all([self.high_price, self.low_price, self.close_price]):
            return float((self.high_price + self.low_price + self.close_price) / 3)
        return None
