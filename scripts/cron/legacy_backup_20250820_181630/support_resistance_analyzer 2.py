#!/usr/bin/env python3
"""
サポート・レジスタンス分析システム

移動平均線を活用した重要レベルの自動検出機能
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)

console = Console()


class LevelType(Enum):
    """レベルタイプ"""

    SUPPORT = "サポート"
    RESISTANCE = "レジスタンス"
    STRONG_SUPPORT = "強力サポート"
    STRONG_RESISTANCE = "強力レジスタンス"


@dataclass
class SupportResistanceLevel:
    """サポート・レジスタンスレベル"""

    level_type: LevelType
    price_level: float
    strength: float  # 0.0-1.0
    timeframe: str
    indicator: str
    timestamp: datetime
    description: str


class SupportResistanceAnalyzer:
    """サポート・レジスタンス分析システム"""

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair = currency_pair
        self.session: Optional[AsyncSession] = None

    async def analyze_support_resistance(
        self, timeframe: str, days: int = 30
    ) -> List[SupportResistanceLevel]:
        """
        サポート・レジスタンスを分析

        Args:
            timeframe: 時間足
            days: 分析期間

        Returns:
            List[SupportResistanceLevel]: 検出されたレベル
        """
        try:
            # 価格データと移動平均線データを取得
            price_data = await self._get_price_data(timeframe, days)
            ma_data = await self._get_moving_averages(timeframe, days)

            if price_data.empty or ma_data.empty:
                return []

            # レベルを検出
            levels = []

            # 移動平均線ベースのレベル
            ma_levels = self._detect_ma_levels(price_data, ma_data, timeframe)
            levels.extend(ma_levels)

            # ピボットポイントベースのレベル
            pivot_levels = self._detect_pivot_levels(price_data, timeframe)
            levels.extend(pivot_levels)

            # レベルを強度でソート
            levels.sort(key=lambda x: x.strength, reverse=True)

            return levels

        except Exception as e:
            console.print(f"❌ サポート・レジスタンス分析エラー: {e}")
            return []

    async def _get_price_data(self, timeframe: str, days: int) -> pd.DataFrame:
        """価格データを取得"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = (
            select(PriceDataModel)
            .where(
                PriceDataModel.currency_pair == self.currency_pair,
                PriceDataModel.timestamp >= start_date,
                PriceDataModel.timestamp <= end_date,
            )
            .order_by(PriceDataModel.timestamp.asc())
        )

        result = await self.session.execute(query)
        prices = result.scalars().all()

        data = []
        for price in prices:
            data.append(
                {
                    "timestamp": price.timestamp,
                    "open": float(price.open_price),
                    "high": float(price.high_price),
                    "low": float(price.low_price),
                    "close": float(price.close_price),
                    "volume": float(price.volume) if price.volume else 0,
                }
            )

        return pd.DataFrame(data)

    async def _get_moving_averages(self, timeframe: str, days: int) -> pd.DataFrame:
        """移動平均線データを取得"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = (
            select(TechnicalIndicatorModel)
            .where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.indicator_type.in_(["SMA", "EMA"]),
                TechnicalIndicatorModel.timestamp >= start_date,
                TechnicalIndicatorModel.timestamp <= end_date,
            )
            .order_by(TechnicalIndicatorModel.timestamp.asc())
        )

        result = await self.session.execute(query)
        indicators = result.scalars().all()

        data = []
        for indicator in indicators:
            data.append(
                {
                    "timestamp": indicator.timestamp,
                    "indicator_type": indicator.indicator_type,
                    "value": (
                        float(indicator.value) if indicator.value is not None else None
                    ),
                    "parameters": indicator.parameters,
                }
            )

        df = pd.DataFrame(data)
        if not df.empty:
            # ピボットテーブルで指標別に整理
            df = df.pivot_table(
                index="timestamp",
                columns="indicator_type",
                values="value",
                aggfunc="first",
            ).reset_index()

        return df

    def _detect_ma_levels(
        self, price_data: pd.DataFrame, ma_data: pd.DataFrame, timeframe: str
    ) -> List[SupportResistanceLevel]:
        """移動平均線ベースのレベルを検出"""
        levels = []

        # データを結合
        merged_data = pd.merge(price_data, ma_data, on="timestamp", how="inner")

        if merged_data.empty:
            return levels

        # 各移動平均線をチェック
        for ma_type in ["SMA", "EMA"]:
            if ma_type in merged_data.columns:
                ma_levels = self._analyze_ma_level(merged_data, ma_type, timeframe)
                levels.extend(ma_levels)

        return levels

    def _analyze_ma_level(
        self, data: pd.DataFrame, ma_type: str, timeframe: str
    ) -> List[SupportResistanceLevel]:
        """特定の移動平均線レベルを分析"""
        levels = []

        if ma_type not in data.columns:
            return levels

        # 最新の移動平均線値
        current_ma = data[ma_type].iloc[-1]
        current_price = data["close"].iloc[-1]

        # 移動平均線の強度を計算
        strength = self._calculate_ma_strength(data, ma_type)

        # 価格が移動平均線より上にあるか下にあるかでレベルタイプを決定
        if current_price > current_ma:
            # 価格が上にある場合、移動平均線はサポート
            level_type = (
                LevelType.STRONG_SUPPORT if strength > 0.7 else LevelType.SUPPORT
            )
            description = f"{ma_type}サポートレベル"
        else:
            # 価格が下にある場合、移動平均線はレジスタンス
            level_type = (
                LevelType.STRONG_RESISTANCE if strength > 0.7 else LevelType.RESISTANCE
            )
            description = f"{ma_type}レジスタンスレベル"

        levels.append(
            SupportResistanceLevel(
                level_type=level_type,
                price_level=current_ma,
                strength=strength,
                timeframe=timeframe,
                indicator=ma_type,
                timestamp=data["timestamp"].iloc[-1],
                description=description,
            )
        )

        return levels

    def _calculate_ma_strength(self, data: pd.DataFrame, ma_type: str) -> float:
        """移動平均線の強度を計算"""
        if ma_type not in data.columns:
            return 0.0

        # 移動平均線の傾きを計算
        ma_values = data[ma_type].dropna()
        if len(ma_values) < 2:
            return 0.5

        # 線形回帰で傾きを計算
        x = np.arange(len(ma_values))
        slope, _ = np.polyfit(x, ma_values, 1)

        # 価格との相関を計算
        price_values = data["close"].iloc[: len(ma_values)]
        correlation = np.corrcoef(ma_values, price_values)[0, 1]

        # 強度を計算（0.3-0.9の範囲）
        base_strength = 0.3
        slope_factor = min(abs(slope) * 10, 0.3)  # 傾きによる強度
        correlation_factor = abs(correlation) * 0.3  # 相関による強度

        return min(base_strength + slope_factor + correlation_factor, 0.9)

    def _detect_pivot_levels(
        self, price_data: pd.DataFrame, timeframe: str
    ) -> List[SupportResistanceLevel]:
        """ピボットポイントベースのレベルを検出"""
        levels = []

        if len(price_data) < 20:
            return levels

        # ピボットポイントを計算
        high = price_data["high"].max()
        low = price_data["low"].min()
        close = price_data["close"].iloc[-1]

        # 標準的なピボットポイント計算
        pivot = (high + low + close) / 3
        r1 = 2 * pivot - low
        s1 = 2 * pivot - high
        r2 = pivot + (high - low)
        s2 = pivot - (high - low)

        # 各レベルを追加
        levels.extend(
            [
                SupportResistanceLevel(
                    level_type=LevelType.RESISTANCE,
                    price_level=r2,
                    strength=0.8,
                    timeframe=timeframe,
                    indicator="Pivot",
                    timestamp=price_data["timestamp"].iloc[-1],
                    description="R2レジスタンスレベル",
                ),
                SupportResistanceLevel(
                    level_type=LevelType.RESISTANCE,
                    price_level=r1,
                    strength=0.7,
                    timeframe=timeframe,
                    indicator="Pivot",
                    timestamp=price_data["timestamp"].iloc[-1],
                    description="R1レジスタンスレベル",
                ),
                SupportResistanceLevel(
                    level_type=LevelType.SUPPORT,
                    price_level=s1,
                    strength=0.7,
                    timeframe=timeframe,
                    indicator="Pivot",
                    timestamp=price_data["timestamp"].iloc[-1],
                    description="S1サポートレベル",
                ),
                SupportResistanceLevel(
                    level_type=LevelType.SUPPORT,
                    price_level=s2,
                    strength=0.8,
                    timeframe=timeframe,
                    indicator="Pivot",
                    timestamp=price_data["timestamp"].iloc[-1],
                    description="S2サポートレベル",
                ),
            ]
        )

        return levels

    def display_levels(self, levels: List[SupportResistanceLevel]) -> None:
        """レベルを表示"""
        if not levels:
            console.print("📊 サポート・レジスタンスレベルは検出されませんでした")
            return

        console.print(f"\n🎯 サポート・レジスタンス分析結果 ({len(levels)}件)")
        console.print("=" * 60)

        # レジスタンスレベル
        resistance_levels = [l for l in levels if "レジスタンス" in l.level_type.value]
        if resistance_levels:
            console.print("\n🔴 レジスタンスレベル:")
            for i, level in enumerate(resistance_levels, 1):
                console.print(
                    f"  {i}. {level.price_level:.3f} (強度: {level.strength:.2f}) - {level.description}"
                )

        # サポートレベル
        support_levels = [l for l in levels if "サポート" in l.level_type.value]
        if support_levels:
            console.print("\n🟢 サポートレベル:")
            for i, level in enumerate(support_levels, 1):
                console.print(
                    f"  {i}. {level.price_level:.3f} (強度: {level.strength:.2f}) - {level.description}"
                )

        # 現在価格との関係
        console.print(f"\n📊 現在価格との関係:")
        current_price = 147.0  # 仮の現在価格
        console.print(f"  現在価格: {current_price:.3f}")

        nearest_resistance = min(
            [l.price_level for l in resistance_levels], default=float("inf")
        )
        nearest_support = max([l.price_level for l in support_levels], default=0)

        if nearest_resistance != float("inf"):
            console.print(
                f"  最寄りレジスタンス: {nearest_resistance:.3f} (距離: {nearest_resistance - current_price:.3f})"
            )
        if nearest_support != 0:
            console.print(
                f"  最寄りサポート: {nearest_support:.3f} (距離: {current_price - nearest_support:.3f})"
            )

    async def initialize(self) -> bool:
        """初期化処理"""
        try:
            self.session = await get_async_session()
            return True
        except Exception as e:
            console.print(f"❌ 初期化エラー: {e}")
            return False

    async def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        if self.session:
            await self.session.close()


async def main():
    """メイン実行関数"""
    import argparse

    parser = argparse.ArgumentParser(description="サポート・レジスタンス分析システム")
    parser.add_argument(
        "--timeframe", "-tf", default="H1", help="時間足 (M5, H1, H4, D1)"
    )
    parser.add_argument("--days", "-d", type=int, default=30, help="分析期間（日数）")
    parser.add_argument("--currency-pair", "-p", default="USD/JPY", help="通貨ペア")

    args = parser.parse_args()

    analyzer = SupportResistanceAnalyzer(args.currency_pair)

    if not await analyzer.initialize():
        return

    try:
        # サポート・レジスタンス分析
        levels = await analyzer.analyze_support_resistance(args.timeframe, args.days)

        # 結果表示
        analyzer.display_levels(levels)

    except Exception as e:
        console.print(f"❌ 実行エラー: {e}")

    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
