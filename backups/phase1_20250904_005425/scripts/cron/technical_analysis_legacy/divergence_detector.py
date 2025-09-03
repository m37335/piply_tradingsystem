#!/usr/bin/env python3
"""
ダイバージェンス検出システム

価格とテクニカル指標の乖離を分析し、ダイバージェンスを検出する機能
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)

console = Console()


class DivergenceType(Enum):
    """ダイバージェンスタイプ"""

    BULLISH = "強気ダイバージェンス"  # 価格下落、指標上昇
    BEARISH = "弱気ダイバージェンス"  # 価格上昇、指標下落
    HIDDEN_BULLISH = "隠れ強気ダイバージェンス"  # 価格上昇、指標下落（調整後）
    HIDDEN_BEARISH = "隠れ弱気ダイバージェンス"  # 価格下落、指標上昇（調整後）


@dataclass
class DivergenceSignal:
    """ダイバージェンスシグナル"""

    divergence_type: DivergenceType
    indicator: str
    timeframe: str
    price_high: float
    price_low: float
    indicator_high: float
    indicator_low: float
    confidence: float
    timestamp: datetime
    description: str


class DivergenceDetector:
    """ダイバージェンス検出システム"""

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair = currency_pair
        self.session: Optional[AsyncSession] = None

    async def detect_divergences(
        self, timeframe: str, days: int = 7
    ) -> List[DivergenceSignal]:
        """
        ダイバージェンスを検出

        Args:
            timeframe: 時間足
            days: 分析期間

        Returns:
            List[DivergenceSignal]: 検出されたダイバージェンス
        """
        try:
            # 価格データとテクニカル指標データを取得
            price_data = await self._get_price_data(timeframe, days)
            indicator_data = await self._get_indicator_data(timeframe, days)

            if price_data.empty or indicator_data.empty:
                return []

            # 各指標でダイバージェンスを検出
            divergences = []

            # RSIダイバージェンス
            rsi_divergences = self._detect_rsi_divergence(price_data, indicator_data)
            divergences.extend(rsi_divergences)

            # MACDダイバージェンス
            macd_divergences = self._detect_macd_divergence(price_data, indicator_data)
            divergences.extend(macd_divergences)

            # ストキャスティクスダイバージェンス
            stoch_divergences = self._detect_stochastic_divergence(
                price_data, indicator_data
            )
            divergences.extend(stoch_divergences)

            return divergences

        except Exception as e:
            console.print(f"❌ ダイバージェンス検出エラー: {e}")
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

    async def _get_indicator_data(self, timeframe: str, days: int) -> pd.DataFrame:
        """テクニカル指標データを取得"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        query = (
            select(TechnicalIndicatorModel)
            .where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
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

    def _detect_rsi_divergence(
        self, price_data: pd.DataFrame, indicator_data: pd.DataFrame
    ) -> List[DivergenceSignal]:
        """RSIダイバージェンスを検出"""
        divergences = []

        if "RSI" not in indicator_data.columns:
            return divergences

        # データを結合
        merged_data = pd.merge(
            price_data,
            indicator_data[["timestamp", "RSI"]],
            on="timestamp",
            how="inner",
        )

        if len(merged_data) < 20:
            return divergences

        # 高値と安値を検出
        price_highs = self._find_peaks(merged_data["high"].values)
        price_lows = self._find_peaks(-merged_data["low"].values)  # 安値を検出するため負の値を使用
        rsi_highs = self._find_peaks(merged_data["RSI"].values)
        rsi_lows = self._find_peaks(-merged_data["RSI"].values)

        # 強気ダイバージェンス（価格下落、RSI上昇）
        bullish_div = self._check_bullish_divergence(
            merged_data, price_lows, rsi_lows, "RSI", timeframe="M5"
        )
        if bullish_div:
            divergences.append(bullish_div)

        # 弱気ダイバージェンス（価格上昇、RSI下落）
        bearish_div = self._check_bearish_divergence(
            merged_data, price_highs, rsi_highs, "RSI", timeframe="M5"
        )
        if bearish_div:
            divergences.append(bearish_div)

        return divergences

    def _detect_macd_divergence(
        self, price_data: pd.DataFrame, indicator_data: pd.DataFrame
    ) -> List[DivergenceSignal]:
        """MACDダイバージェンスを検出"""
        divergences = []

        if "MACD" not in indicator_data.columns:
            return divergences

        # データを結合
        merged_data = pd.merge(
            price_data,
            indicator_data[["timestamp", "MACD"]],
            on="timestamp",
            how="inner",
        )

        if len(merged_data) < 20:
            return divergences

        # 高値と安値を検出
        price_highs = self._find_peaks(merged_data["high"].values)
        price_lows = self._find_peaks(-merged_data["low"].values)
        macd_highs = self._find_peaks(merged_data["MACD"].values)
        macd_lows = self._find_peaks(-merged_data["MACD"].values)

        # 強気ダイバージェンス
        bullish_div = self._check_bullish_divergence(
            merged_data, price_lows, macd_lows, "MACD", timeframe="M5"
        )
        if bullish_div:
            divergences.append(bullish_div)

        # 弱気ダイバージェンス
        bearish_div = self._check_bearish_divergence(
            merged_data, price_highs, macd_highs, "MACD", timeframe="M5"
        )
        if bearish_div:
            divergences.append(bearish_div)

        return divergences

    def _detect_stochastic_divergence(
        self, price_data: pd.DataFrame, indicator_data: pd.DataFrame
    ) -> List[DivergenceSignal]:
        """ストキャスティクスダイバージェンスを検出"""
        divergences = []

        if "STOCH" not in indicator_data.columns:
            return divergences

        # データを結合
        merged_data = pd.merge(
            price_data,
            indicator_data[["timestamp", "STOCH"]],
            on="timestamp",
            how="inner",
        )

        if len(merged_data) < 20:
            return divergences

        # 高値と安値を検出
        price_highs = self._find_peaks(merged_data["high"].values)
        price_lows = self._find_peaks(-merged_data["low"].values)
        stoch_highs = self._find_peaks(merged_data["STOCH"].values)
        stoch_lows = self._find_peaks(-merged_data["STOCH"].values)

        # 強気ダイバージェンス
        bullish_div = self._check_bullish_divergence(
            merged_data, price_lows, stoch_lows, "STOCH", timeframe="M5"
        )
        if bullish_div:
            divergences.append(bullish_div)

        # 弱気ダイバージェンス
        bearish_div = self._check_bearish_divergence(
            merged_data, price_highs, stoch_highs, "STOCH", timeframe="M5"
        )
        if bearish_div:
            divergences.append(bearish_div)

        return divergences

    def _find_peaks(self, data: np.ndarray, window: int = 5) -> List[int]:
        """ピーク（極値）を検出"""
        peaks = []
        for i in range(window, len(data) - window):
            if all(data[i] >= data[j] for j in range(i - window, i)) and all(
                data[i] >= data[j] for j in range(i + 1, i + window + 1)
            ):
                peaks.append(i)
        return peaks

    def _check_bullish_divergence(
        self,
        data: pd.DataFrame,
        price_lows: List[int],
        indicator_lows: List[int],
        indicator: str,
        timeframe: str,
    ) -> Optional[DivergenceSignal]:
        """強気ダイバージェンスをチェック"""
        if len(price_lows) < 2 or len(indicator_lows) < 2:
            return None

        # 最新の2つのピークを比較
        recent_price_low = price_lows[-1]
        previous_price_low = price_lows[-2]
        recent_indicator_low = indicator_lows[-1]
        previous_indicator_low = indicator_lows[-2]

        # 価格が下落、指標が上昇しているかチェック
        if (
            data.iloc[recent_price_low]["low"] < data.iloc[previous_price_low]["low"]
            and data.iloc[recent_indicator_low][indicator]
            > data.iloc[previous_indicator_low][indicator]
        ):
            confidence = self._calculate_divergence_confidence(
                data,
                recent_price_low,
                previous_price_low,
                recent_indicator_low,
                previous_indicator_low,
            )

            return DivergenceSignal(
                divergence_type=DivergenceType.BULLISH,
                indicator=indicator,
                timeframe=timeframe,
                price_high=data.iloc[recent_price_low]["high"],
                price_low=data.iloc[recent_price_low]["low"],
                indicator_high=data.iloc[recent_indicator_low][indicator],
                indicator_low=data.iloc[recent_indicator_low][indicator],
                confidence=confidence,
                timestamp=data.iloc[recent_price_low]["timestamp"],
                description=f"価格下落、{indicator}上昇の強気ダイバージェンス",
            )

        return None

    def _check_bearish_divergence(
        self,
        data: pd.DataFrame,
        price_highs: List[int],
        indicator_highs: List[int],
        indicator: str,
        timeframe: str,
    ) -> Optional[DivergenceSignal]:
        """弱気ダイバージェンスをチェック"""
        if len(price_highs) < 2 or len(indicator_highs) < 2:
            return None

        # 最新の2つのピークを比較
        recent_price_high = price_highs[-1]
        previous_price_high = price_highs[-2]
        recent_indicator_high = indicator_highs[-1]
        previous_indicator_high = indicator_highs[-2]

        # 価格が上昇、指標が下落しているかチェック
        if (
            data.iloc[recent_price_high]["high"]
            > data.iloc[previous_price_high]["high"]
            and data.iloc[recent_indicator_high][indicator]
            < data.iloc[previous_indicator_high][indicator]
        ):
            confidence = self._calculate_divergence_confidence(
                data,
                recent_price_high,
                previous_price_high,
                recent_indicator_high,
                previous_indicator_high,
            )

            return DivergenceSignal(
                divergence_type=DivergenceType.BEARISH,
                indicator=indicator,
                timeframe=timeframe,
                price_high=data.iloc[recent_price_high]["high"],
                price_low=data.iloc[recent_price_high]["low"],
                indicator_high=data.iloc[recent_indicator_high][indicator],
                indicator_low=data.iloc[recent_indicator_high][indicator],
                confidence=confidence,
                timestamp=data.iloc[recent_price_high]["timestamp"],
                description=f"価格上昇、{indicator}下落の弱気ダイバージェンス",
            )

        return None

    def _calculate_divergence_confidence(
        self,
        data: pd.DataFrame,
        price_peak1: int,
        price_peak2: int,
        indicator_peak1: int,
        indicator_peak2: int,
    ) -> float:
        """ダイバージェンスの信頼度を計算"""
        # ピーク間の距離と価格変動の大きさから信頼度を計算
        price_change = abs(
            data.iloc[price_peak1]["close"] - data.iloc[price_peak2]["close"]
        )
        indicator_change = abs(
            data.iloc[indicator_peak1]["close"] - data.iloc[indicator_peak2]["close"]
        )

        # 基本的な信頼度（0.5-0.9の範囲）
        base_confidence = 0.5

        # 価格変動が大きいほど信頼度が高い
        if price_change > 1.0:
            base_confidence += 0.2
        elif price_change > 0.5:
            base_confidence += 0.1

        # 指標変動が大きいほど信頼度が高い
        if indicator_change > 10:
            base_confidence += 0.2
        elif indicator_change > 5:
            base_confidence += 0.1

        return min(base_confidence, 0.9)

    def display_divergences(self, divergences: List[DivergenceSignal]) -> None:
        """ダイバージェンスを表示"""
        if not divergences:
            console.print("📊 ダイバージェンスは検出されませんでした")
            return

        console.print(f"\n🎯 ダイバージェンス検出結果 ({len(divergences)}件)")
        console.print("=" * 60)

        # 強気ダイバージェンスと弱気ダイバージェンスを分類
        bullish_divs = [
            d
            for d in divergences
            if d.divergence_type
            in [DivergenceType.BULLISH, DivergenceType.HIDDEN_BULLISH]
        ]
        bearish_divs = [
            d
            for d in divergences
            if d.divergence_type
            in [DivergenceType.BEARISH, DivergenceType.HIDDEN_BEARISH]
        ]

        if bullish_divs:
            console.print(f"\n🟢 強気ダイバージェンス ({len(bullish_divs)}件):")
            for i, div in enumerate(bullish_divs, 1):
                console.print(f"  {i}. {div.indicator} - 信頼度: {div.confidence:.2f}")
                console.print(f"     {div.description}")
                console.print(f"     検出時刻: {div.timestamp.strftime('%Y-%m-%d %H:%M')}")

        if bearish_divs:
            console.print(f"\n🔴 弱気ダイバージェンス ({len(bearish_divs)}件):")
            for i, div in enumerate(bearish_divs, 1):
                console.print(f"  {i}. {div.indicator} - 信頼度: {div.confidence:.2f}")
                console.print(f"     {div.description}")
                console.print(f"     検出時刻: {div.timestamp.strftime('%Y-%m-%d %H:%M')}")

        # 総合評価
        console.print(f"\n📋 総合評価:")
        if len(bullish_divs) > len(bearish_divs):
            console.print(f"  🟢 強気傾向 ({len(bullish_divs)} vs {len(bearish_divs)})")
        elif len(bearish_divs) > len(bullish_divs):
            console.print(f"  🔴 弱気傾向 ({len(bearish_divs)} vs {len(bullish_divs)})")
        else:
            console.print(f"  ⚪ 中立 ({len(bullish_divs)} vs {len(bearish_divs)})")

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

    parser = argparse.ArgumentParser(description="ダイバージェンス検出システム")
    parser.add_argument("--timeframe", "-tf", default="M5", help="時間足 (M5, H1, H4, D1)")
    parser.add_argument("--days", "-d", type=int, default=7, help="分析期間（日数）")
    parser.add_argument("--currency-pair", "-p", default="USD/JPY", help="通貨ペア")

    args = parser.parse_args()

    detector = DivergenceDetector(args.currency_pair)

    if not await detector.initialize():
        return

    try:
        # ダイバージェンス検出
        divergences = await detector.detect_divergences(args.timeframe, args.days)

        # 結果表示
        detector.display_divergences(divergences)

    except Exception as e:
        console.print(f"❌ 実行エラー: {e}")

    finally:
        await detector.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
