#!/usr/bin/env python3
"""
モメンタム分析システム

指標の変化速度を分析する機能
"""

import asyncio
import pandas as pd
import numpy as np
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.table import Table
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.technical_indicator_model import TechnicalIndicatorModel

console = Console()


class MomentumType(Enum):
    """モメンタムタイプ"""
    STRONG_UP = "強い上昇"
    UP = "上昇"
    NEUTRAL = "中立"
    DOWN = "下降"
    STRONG_DOWN = "強い下降"


@dataclass
class MomentumSignal:
    """モメンタムシグナル"""
    indicator: str
    momentum_type: MomentumType
    current_value: float
    previous_value: float
    change_rate: float  # 変化率（%）
    velocity: float  # 変化速度
    timeframe: str
    timestamp: datetime
    description: str


class MomentumAnalyzer:
    """モメンタム分析システム"""

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair = currency_pair
        self.session: Optional[AsyncSession] = None

    async def analyze_momentum(self, timeframe: str, days: int = 7) -> Dict[str, List[MomentumSignal]]:
        """
        モメンタムを分析

        Args:
            timeframe: 時間足
            days: 分析期間

        Returns:
            Dict[str, List[MomentumSignal]]: 各指標のモメンタム分析結果
        """
        try:
            # テクニカル指標データを取得
            indicator_data = await self._get_indicator_data(timeframe, days)

            if indicator_data.empty:
                return {}

            # 各指標でモメンタムを分析
            results = {}
            
            # RSIモメンタム
            rsi_momentum = self._analyze_rsi_momentum(indicator_data, timeframe)
            if rsi_momentum:
                results["RSI"] = rsi_momentum

            # MACDモメンタム
            macd_momentum = self._analyze_macd_momentum(indicator_data, timeframe)
            if macd_momentum:
                results["MACD"] = macd_momentum

            # ストキャスティクスモメンタム
            stoch_momentum = self._analyze_stochastic_momentum(indicator_data, timeframe)
            if stoch_momentum:
                results["STOCH"] = stoch_momentum

            # 移動平均線モメンタム
            ma_momentum = self._analyze_ma_momentum(indicator_data, timeframe)
            if ma_momentum:
                results["MA"] = ma_momentum

            return results

        except Exception as e:
            console.print(f"❌ モメンタム分析エラー: {e}")
            return {}

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
                TechnicalIndicatorModel.timestamp <= end_date
            )
            .order_by(TechnicalIndicatorModel.timestamp.asc())
        )

        result = await self.session.execute(query)
        indicators = result.scalars().all()

        data = []
        for indicator in indicators:
            data.append({
                "timestamp": indicator.timestamp,
                "indicator_type": indicator.indicator_type,
                "value": float(indicator.value) if indicator.value is not None else None
            })

        df = pd.DataFrame(data)
        if not df.empty:
            # ピボットテーブルで指標別に整理
            df = df.pivot_table(
                index="timestamp",
                columns="indicator_type",
                values="value",
                aggfunc="first"
            ).reset_index()

        return df

    def _analyze_rsi_momentum(self, data: pd.DataFrame, timeframe: str) -> List[MomentumSignal]:
        """RSIモメンタムを分析"""
        signals = []
        
        if "RSI" not in data.columns:
            return signals

        rsi_values = data["RSI"].dropna()
        if len(rsi_values) < 2:
            return signals

        # 最新の値と前の値を比較
        current_rsi = rsi_values.iloc[-1]
        previous_rsi = rsi_values.iloc[-2]
        
        # 変化率を計算
        change_rate = ((current_rsi - previous_rsi) / previous_rsi) * 100
        velocity = current_rsi - previous_rsi

        # モメンタムタイプを決定
        momentum_type = self._determine_momentum_type(velocity, change_rate)
        
        # 説明を生成
        description = self._generate_momentum_description("RSI", current_rsi, previous_rsi, change_rate)

        signals.append(MomentumSignal(
            indicator="RSI",
            momentum_type=momentum_type,
            current_value=current_rsi,
            previous_value=previous_rsi,
            change_rate=change_rate,
            velocity=velocity,
            timeframe=timeframe,
            timestamp=data["timestamp"].iloc[-1],
            description=description
        ))

        return signals

    def _analyze_macd_momentum(self, data: pd.DataFrame, timeframe: str) -> List[MomentumSignal]:
        """MACDモメンタムを分析"""
        signals = []
        
        if "MACD" not in data.columns:
            return signals

        macd_values = data["MACD"].dropna()
        if len(macd_values) < 2:
            return signals

        # 最新の値と前の値を比較
        current_macd = macd_values.iloc[-1]
        previous_macd = macd_values.iloc[-2]
        
        # 変化率を計算（MACDは負の値も取るため、絶対値で計算）
        change_rate = ((current_macd - previous_macd) / abs(previous_macd)) * 100 if previous_macd != 0 else 0
        velocity = current_macd - previous_macd

        # モメンタムタイプを決定
        momentum_type = self._determine_momentum_type(velocity, change_rate)
        
        # 説明を生成
        description = self._generate_momentum_description("MACD", current_macd, previous_macd, change_rate)

        signals.append(MomentumSignal(
            indicator="MACD",
            momentum_type=momentum_type,
            current_value=current_macd,
            previous_value=previous_macd,
            change_rate=change_rate,
            velocity=velocity,
            timeframe=timeframe,
            timestamp=data["timestamp"].iloc[-1],
            description=description
        ))

        return signals

    def _analyze_stochastic_momentum(self, data: pd.DataFrame, timeframe: str) -> List[MomentumSignal]:
        """ストキャスティクスモメンタムを分析"""
        signals = []
        
        if "STOCH" not in data.columns:
            return signals

        stoch_values = data["STOCH"].dropna()
        if len(stoch_values) < 2:
            return signals

        # 最新の値と前の値を比較
        current_stoch = stoch_values.iloc[-1]
        previous_stoch = stoch_values.iloc[-2]
        
        # 変化率を計算
        change_rate = ((current_stoch - previous_stoch) / previous_stoch) * 100
        velocity = current_stoch - previous_stoch

        # モメンタムタイプを決定
        momentum_type = self._determine_momentum_type(velocity, change_rate)
        
        # 説明を生成
        description = self._generate_momentum_description("ストキャスティクス", current_stoch, previous_stoch, change_rate)

        signals.append(MomentumSignal(
            indicator="STOCH",
            momentum_type=momentum_type,
            current_value=current_stoch,
            previous_value=previous_stoch,
            change_rate=change_rate,
            velocity=velocity,
            timeframe=timeframe,
            timestamp=data["timestamp"].iloc[-1],
            description=description
        ))

        return signals

    def _analyze_ma_momentum(self, data: pd.DataFrame, timeframe: str) -> List[MomentumSignal]:
        """移動平均線モメンタムを分析"""
        signals = []
        
        for ma_type in ["SMA", "EMA"]:
            if ma_type not in data.columns:
                continue

            ma_values = data[ma_type].dropna()
            if len(ma_values) < 2:
                continue

            # 最新の値と前の値を比較
            current_ma = ma_values.iloc[-1]
            previous_ma = ma_values.iloc[-2]
            
            # 変化率を計算
            change_rate = ((current_ma - previous_ma) / previous_ma) * 100
            velocity = current_ma - previous_ma

            # モメンタムタイプを決定
            momentum_type = self._determine_momentum_type(velocity, change_rate)
            
            # 説明を生成
            description = self._generate_momentum_description(ma_type, current_ma, previous_ma, change_rate)

            signals.append(MomentumSignal(
                indicator=ma_type,
                momentum_type=momentum_type,
                current_value=current_ma,
                previous_value=previous_ma,
                change_rate=change_rate,
                velocity=velocity,
                timeframe=timeframe,
                timestamp=data["timestamp"].iloc[-1],
                description=description
            ))

        return signals

    def _determine_momentum_type(self, velocity: float, change_rate: float) -> MomentumType:
        """モメンタムタイプを決定"""
        # 変化率と速度の両方を考慮
        if change_rate > 5.0 or velocity > 5.0:
            return MomentumType.STRONG_UP
        elif change_rate > 1.0 or velocity > 1.0:
            return MomentumType.UP
        elif change_rate < -5.0 or velocity < -5.0:
            return MomentumType.STRONG_DOWN
        elif change_rate < -1.0 or velocity < -1.0:
            return MomentumType.DOWN
        else:
            return MomentumType.NEUTRAL

    def _generate_momentum_description(self, indicator: str, current: float, previous: float, change_rate: float) -> str:
        """モメンタム説明を生成"""
        if change_rate > 0:
            direction = "上昇"
            emoji = "📈"
        else:
            direction = "下降"
            emoji = "📉"

        return f"{emoji} {indicator}が{abs(change_rate):.2f}%{direction} ({previous:.2f} → {current:.2f})"

    def display_momentum_analysis(self, results: Dict[str, List[MomentumSignal]]) -> None:
        """モメンタム分析結果を表示"""
        if not results:
            console.print("📊 モメンタム分析結果はありません")
            return

        console.print(f"\n🎯 モメンタム分析結果")
        console.print("=" * 50)

        for indicator, signals in results.items():
            console.print(f"\n📊 {indicator}モメンタム:")
            
            for signal in signals:
                emoji = "🟢" if signal.momentum_type in [MomentumType.STRONG_UP, MomentumType.UP] else \
                       "🔴" if signal.momentum_type in [MomentumType.STRONG_DOWN, MomentumType.DOWN] else "⚪"
                
                console.print(f"  {emoji} {signal.momentum_type.value}")
                console.print(f"     変化率: {signal.change_rate:+.2f}%")
                console.print(f"     速度: {signal.velocity:+.3f}")
                console.print(f"     説明: {signal.description}")

        # 総合モメンタム評価
        console.print(f"\n📋 総合モメンタム評価:")
        total_signals = sum(len(signals) for signals in results.values())
        up_signals = sum(1 for signals in results.values() 
                        for signal in signals 
                        if signal.momentum_type in [MomentumType.STRONG_UP, MomentumType.UP])
        down_signals = sum(1 for signals in results.values() 
                          for signal in signals 
                          if signal.momentum_type in [MomentumType.STRONG_DOWN, MomentumType.DOWN])
        
        if up_signals > down_signals:
            overall_momentum = "上昇傾向"
            emoji = "🟢"
        elif down_signals > up_signals:
            overall_momentum = "下降傾向"
            emoji = "🔴"
        else:
            overall_momentum = "中立"
            emoji = "⚪"
            
        console.print(f"  {emoji} {overall_momentum} (上昇: {up_signals}件, 下降: {down_signals}件)")

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
    
    parser = argparse.ArgumentParser(description="モメンタム分析システム")
    parser.add_argument("--timeframe", "-tf", default="M5", help="時間足 (M5, H1, H4, D1)")
    parser.add_argument("--days", "-d", type=int, default=7, help="分析期間（日数）")
    parser.add_argument("--currency-pair", "-p", default="USD/JPY", help="通貨ペア")
    
    args = parser.parse_args()
    
    analyzer = MomentumAnalyzer(args.currency_pair)
    
    if not await analyzer.initialize():
        return

    try:
        # モメンタム分析
        results = await analyzer.analyze_momentum(args.timeframe, args.days)
        
        # 結果表示
        analyzer.display_momentum_analysis(results)

    except Exception as e:
        console.print(f"❌ 実行エラー: {e}")
    
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
