"""
Currency Value Objects
通貨関連の値オブジェクト

設計書参照:
- 詳細内部設計_20250809.md

通貨ペア、価格、レートなどの値オブジェクトを定義
"""

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Optional

from .base import BaseValueObject


@dataclass(frozen=True)
class CurrencyCode(BaseValueObject):
    """
    通貨コード値オブジェクト
    ISO 4217 標準に準拠
    """

    code: str

    def _validate(self) -> None:
        """
        通貨コードのバリデーション
        ISO 4217形式（3文字の大文字）をチェック
        """
        if not isinstance(self.code, str):
            raise ValueError("Currency code must be a string")

        if not re.match(r"^[A-Z]{3}$", self.code):
            raise ValueError(
                f"Invalid currency code: {self.code}. "
                "Must be 3 uppercase letters (ISO 4217)"
            )

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class CurrencyPair(BaseValueObject):
    """
    通貨ペア値オブジェクト
    基軸通貨（base）と相手通貨（quote）のペア
    """

    base: CurrencyCode
    quote: CurrencyCode

    def _validate(self) -> None:
        """
        通貨ペアのバリデーション
        """
        if self.base == self.quote:
            raise ValueError("Base and quote currencies must be different")

    def reverse(self) -> "CurrencyPair":
        """
        通貨ペアを逆転

        Returns:
            CurrencyPair: 逆転した通貨ペア
        """
        return CurrencyPair(base=self.quote, quote=self.base)

    def __str__(self) -> str:
        return f"{self.base}/{self.quote}"


@dataclass(frozen=True)
class Price(BaseValueObject):
    """
    価格値オブジェクト
    高精度な金融計算のためDecimalを使用
    """

    value: Decimal
    precision: int = 5

    def __post_init__(self) -> None:
        # Decimalに変換
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

        # 精度を適用
        object.__setattr__(
            self,
            "value",
            self.value.quantize(
                Decimal("0." + "0" * self.precision), rounding=ROUND_HALF_UP
            ),
        )

        super().__post_init__()

    def _validate(self) -> None:
        """
        価格のバリデーション
        """
        if self.value < 0:
            raise ValueError("Price cannot be negative")

        if self.precision < 0 or self.precision > 10:
            raise ValueError("Precision must be between 0 and 10")

    def add(self, other: "Price") -> "Price":
        """
        価格の加算

        Args:
            other: 加算する価格

        Returns:
            Price: 加算結果
        """
        if self.precision != other.precision:
            raise ValueError("Cannot add prices with different precision")

        return Price(self.value + other.value, self.precision)

    def subtract(self, other: "Price") -> "Price":
        """
        価格の減算

        Args:
            other: 減算する価格

        Returns:
            Price: 減算結果
        """
        if self.precision != other.precision:
            raise ValueError("Cannot subtract prices with different precision")

        return Price(self.value - other.value, self.precision)

    def multiply(self, factor: Decimal) -> "Price":
        """
        価格の乗算

        Args:
            factor: 乗数

        Returns:
            Price: 乗算結果
        """
        return Price(self.value * Decimal(str(factor)), self.precision)

    def divide(self, divisor: Decimal) -> "Price":
        """
        価格の除算

        Args:
            divisor: 除数

        Returns:
            Price: 除算結果
        """
        if divisor == 0:
            raise ValueError("Cannot divide by zero")

        return Price(self.value / Decimal(str(divisor)), self.precision)

    def __float__(self) -> float:
        return float(self.value)

    def __str__(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class ExchangeRate(BaseValueObject):
    """
    為替レート値オブジェクト
    通貨ペアとその価格を組み合わせ
    """

    pair: CurrencyPair
    rate: Price
    spread: Optional[Price] = None

    def _validate(self) -> None:
        """
        為替レートのバリデーション
        """
        if self.rate.value <= 0:
            raise ValueError("Exchange rate must be positive")

        if self.spread and self.spread.value < 0:
            raise ValueError("Spread cannot be negative")

    def get_bid_rate(self) -> Price:
        """
        ビッドレート（買い値）を取得

        Returns:
            Price: ビッドレート
        """
        if self.spread:
            return self.rate.subtract(self.spread.divide(Decimal("2")))
        return self.rate

    def get_ask_rate(self) -> Price:
        """
        アスクレート（売り値）を取得

        Returns:
            Price: アスクレート
        """
        if self.spread:
            return self.rate.add(self.spread.divide(Decimal("2")))
        return self.rate

    def reverse(self) -> "ExchangeRate":
        """
        逆の為替レートを計算

        Returns:
            ExchangeRate: 逆転した為替レート
        """
        reversed_rate = Price(Decimal("1") / self.rate.value, self.rate.precision)

        reversed_spread = None
        if self.spread:
            # スプレッドも逆転計算
            bid = self.get_bid_rate()
            ask = self.get_ask_rate()

            reversed_ask = Price(Decimal("1") / bid.value, bid.precision)
            reversed_bid = Price(Decimal("1") / ask.value, ask.precision)

            reversed_spread = reversed_ask.subtract(reversed_bid)

        return ExchangeRate(
            pair=self.pair.reverse(), rate=reversed_rate, spread=reversed_spread
        )

    def __str__(self) -> str:
        if self.spread:
            return f"{self.pair}: {self.rate} (±{self.spread})"
        return f"{self.pair}: {self.rate}"
