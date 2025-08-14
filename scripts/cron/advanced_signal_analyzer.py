#!/usr/bin/env python3
"""
高度なシグナル分析システム

複数指標の組み合わせ分析、トレンド分析、強度計算、信頼度評価を含む
包括的なシグナル分析システム
"""

import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.models.technical_indicator_model import TechnicalIndicatorModel
from src.infrastructure.database.models.price_data_model import PriceDataModel

console = Console()


class SignalType(Enum):
    """シグナルタイプ"""
    BUY = "買い"
    SELL = "売り"
    HOLD = "ホールド"
    STRONG_BUY = "強力買い"
    STRONG_SELL = "強力売り"


class SignalStrength(Enum):
    """シグナル強度"""
    WEAK = "弱い"
    MODERATE = "中程度"
    STRONG = "強い"
    VERY_STRONG = "非常に強い"


@dataclass
class SignalAnalysis:
    """シグナル分析結果"""
    signal_type: SignalType
    strength: SignalStrength
    confidence: float  # 0.0-1.0
    indicators: List[str]
    reasoning: str
    timestamp: datetime
    value: float


class AdvancedSignalAnalyzer:
    """高度なシグナル分析システム"""

    def __init__(self, currency_pair: str = "USD/JPY"):
        self.currency_pair = currency_pair
        self.session: Optional[AsyncSession] = None

    async def analyze_comprehensive_signals(self, timeframe: str, days: int = 7) -> Dict[str, Any]:
        """
        包括的なシグナル分析を実行

        Args:
            timeframe: 時間足
            days: 分析期間

        Returns:
            Dict[str, Any]: 分析結果
        """
        try:
            # データ取得
            data = await self._get_technical_data(timeframe, days)
            if data.empty:
                return {"error": f"{timeframe}のデータがありません"}

            # 各種分析を実行
            results = {
                "current_signals": await self._analyze_current_signals(data),
                "trend_analysis": await self._analyze_trends(data),
                "divergence_analysis": await self._analyze_divergences(data),
                "support_resistance": await self._analyze_support_resistance(data),
                "volatility_analysis": await self._analyze_volatility(data),
                "momentum_analysis": await self._analyze_momentum(data),
                "summary": await self._generate_summary(data)
            }

            return results

        except Exception as e:
            console.print(f"❌ シグナル分析エラー: {e}")
            return {"error": str(e)}

    async def _get_technical_data(self, timeframe: str, days: int) -> pd.DataFrame:
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
            .order_by(TechnicalIndicatorModel.timestamp.desc())
            .limit(1000)  # データ量を制限
        )

        result = await self.session.execute(query)
        indicators = result.scalars().all()

        # DataFrameに変換
        data = []
        for indicator in indicators:
            data.append({
                "timestamp": indicator.timestamp,
                "indicator_type": indicator.indicator_type,
                "value": float(indicator.value) if indicator.value is not None else None,
                "parameters": indicator.parameters
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
            
            # タイムスタンプでソート（最新が上に来るように）
            df = df.sort_values('timestamp', ascending=False).reset_index(drop=True)
            
            # デバッグ情報を表示
            console.print(f"📊 {timeframe}時間足のデータ取得状況:")
            console.print(f"  取得件数: {len(df)}件")
            console.print(f"  最新タイムスタンプ: {df['timestamp'].max()}")
            console.print(f"  指標: {list(df.columns[1:])}")
            if len(df) > 0:
                latest = df.iloc[0]
                console.print(f"  最新RSI: {latest.get('RSI', 'N/A')}")
                console.print(f"  最新MACD: {latest.get('MACD', 'N/A')}")
                console.print(f"  最新STOCH: {latest.get('STOCH', 'N/A')}")

        return df

    async def _analyze_current_signals(self, data: pd.DataFrame) -> List[SignalAnalysis]:
        """現在のシグナルを分析"""
        signals = []
        
        if data.empty:
            return signals

        latest = data.iloc[0]
        
        # RSI分析
        if "RSI" in data.columns and not pd.isna(latest["RSI"]):
            rsi_signal = self._analyze_rsi_signal(latest["RSI"])
            if rsi_signal:
                signals.append(rsi_signal)

        # MACD分析
        if "MACD" in data.columns and not pd.isna(latest["MACD"]):
            macd_signal = self._analyze_macd_signal(latest["MACD"])
            if macd_signal:
                signals.append(macd_signal)

        # ストキャスティクス分析
        if "STOCH" in data.columns and not pd.isna(latest["STOCH"]):
            stoch_signal = self._analyze_stochastic_signal(latest["STOCH"])
            if stoch_signal:
                signals.append(stoch_signal)

        # ボリンジャーバンド分析
        if "BB" in data.columns and not pd.isna(latest["BB"]):
            bb_signal = self._analyze_bollinger_signal(data)
            if bb_signal:
                signals.append(bb_signal)

        return signals

    def _analyze_rsi_signal(self, rsi_value: float) -> Optional[SignalAnalysis]:
        """RSIシグナル分析"""
        if rsi_value >= 80:
            return SignalAnalysis(
                signal_type=SignalType.STRONG_SELL,
                strength=SignalStrength.VERY_STRONG,
                confidence=0.9,
                indicators=["RSI"],
                reasoning=f"RSIが極端な過買い圏（{rsi_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=rsi_value
            )
        elif rsi_value >= 70:
            return SignalAnalysis(
                signal_type=SignalType.SELL,
                strength=SignalStrength.STRONG,
                confidence=0.7,
                indicators=["RSI"],
                reasoning=f"RSIが過買い圏（{rsi_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=rsi_value
            )
        elif rsi_value <= 20:
            return SignalAnalysis(
                signal_type=SignalType.STRONG_BUY,
                strength=SignalStrength.VERY_STRONG,
                confidence=0.9,
                indicators=["RSI"],
                reasoning=f"RSIが極端な過売り圏（{rsi_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=rsi_value
            )
        elif rsi_value <= 30:
            return SignalAnalysis(
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG,
                confidence=0.7,
                indicators=["RSI"],
                reasoning=f"RSIが過売り圏（{rsi_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=rsi_value
            )
        
        return None

    def _analyze_macd_signal(self, macd_value: float) -> Optional[SignalAnalysis]:
        """MACDシグナル分析"""
        if macd_value > 0.05:
            return SignalAnalysis(
                signal_type=SignalType.STRONG_BUY,
                strength=SignalStrength.STRONG,
                confidence=0.8,
                indicators=["MACD"],
                reasoning=f"MACDが強い陽性（{macd_value:.3f}）を示している",
                timestamp=datetime.now(),
                value=macd_value
            )
        elif macd_value > 0:
            return SignalAnalysis(
                signal_type=SignalType.BUY,
                strength=SignalStrength.MODERATE,
                confidence=0.6,
                indicators=["MACD"],
                reasoning=f"MACDが陽性（{macd_value:.3f}）を示している",
                timestamp=datetime.now(),
                value=macd_value
            )
        elif macd_value < -0.05:
            return SignalAnalysis(
                signal_type=SignalType.STRONG_SELL,
                strength=SignalStrength.STRONG,
                confidence=0.8,
                indicators=["MACD"],
                reasoning=f"MACDが強い陰性（{macd_value:.3f}）を示している",
                timestamp=datetime.now(),
                value=macd_value
            )
        elif macd_value < 0:
            return SignalAnalysis(
                signal_type=SignalType.SELL,
                strength=SignalStrength.MODERATE,
                confidence=0.6,
                indicators=["MACD"],
                reasoning=f"MACDが陰性（{macd_value:.3f}）を示している",
                timestamp=datetime.now(),
                value=macd_value
            )
        
        return None

    def _analyze_stochastic_signal(self, stoch_value: float) -> Optional[SignalAnalysis]:
        """ストキャスティクスシグナル分析"""
        if stoch_value >= 90:
            return SignalAnalysis(
                signal_type=SignalType.STRONG_SELL,
                strength=SignalStrength.VERY_STRONG,
                confidence=0.9,
                indicators=["STOCH"],
                reasoning=f"ストキャスティクスが極端な過買い圏（{stoch_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=stoch_value
            )
        elif stoch_value >= 80:
            return SignalAnalysis(
                signal_type=SignalType.SELL,
                strength=SignalStrength.STRONG,
                confidence=0.7,
                indicators=["STOCH"],
                reasoning=f"ストキャスティクスが過買い圏（{stoch_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=stoch_value
            )
        elif stoch_value <= 10:
            return SignalAnalysis(
                signal_type=SignalType.STRONG_BUY,
                strength=SignalStrength.VERY_STRONG,
                confidence=0.9,
                indicators=["STOCH"],
                reasoning=f"ストキャスティクスが極端な過売り圏（{stoch_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=stoch_value
            )
        elif stoch_value <= 20:
            return SignalAnalysis(
                signal_type=SignalType.BUY,
                strength=SignalStrength.STRONG,
                confidence=0.7,
                indicators=["STOCH"],
                reasoning=f"ストキャスティクスが過売り圏（{stoch_value:.2f}）を示している",
                timestamp=datetime.now(),
                value=stoch_value
            )
        
        return None

    def _analyze_bollinger_signal(self, data: pd.DataFrame) -> Optional[SignalAnalysis]:
        """ボリンジャーバンドシグナル分析"""
        if "BB" not in data.columns or data.empty:
            return None

        latest_bb = data.iloc[0]["BB"]
        if pd.isna(latest_bb):
            return None

        # ボリンジャーバンドの位置を分析
        # 実際の実装では価格データと組み合わせて分析
        return SignalAnalysis(
            signal_type=SignalType.HOLD,
            strength=SignalStrength.WEAK,
            confidence=0.3,
            indicators=["BB"],
            reasoning=f"ボリンジャーバンド位置: {latest_bb:.2f}",
            timestamp=datetime.now(),
            value=latest_bb
        )

    async def _analyze_trends(self, data: pd.DataFrame) -> Dict[str, Any]:
        """トレンド分析"""
        if data.empty:
            return {"error": "データがありません"}

        trends = {}
        
        # RSIトレンド
        if "RSI" in data.columns:
            rsi_trend = self._calculate_trend(data["RSI"])
            trends["RSI"] = rsi_trend

        # MACDトレンド
        if "MACD" in data.columns:
            macd_trend = self._calculate_trend(data["MACD"])
            trends["MACD"] = macd_trend

        return trends

    def _calculate_trend(self, series: pd.Series) -> Dict[str, Any]:
        """トレンド計算"""
        if len(series) < 2:
            return {"direction": "不明", "strength": 0, "slope": 0}

        # 線形回帰でトレンドを計算
        x = np.arange(len(series))
        y = series.dropna().values
        
        if len(y) < 2:
            return {"direction": "不明", "strength": 0, "slope": 0}

        slope, intercept = np.polyfit(x[:len(y)], y, 1)
        
        # トレンド方向
        if slope > 0.1:
            direction = "上昇"
        elif slope < -0.1:
            direction = "下降"
        else:
            direction = "横ばい"

        # トレンド強度（R²値）
        y_pred = slope * x[:len(y)] + intercept
        r_squared = 1 - np.sum((y - y_pred) ** 2) / np.sum((y - np.mean(y)) ** 2)
        
        return {
            "direction": direction,
            "strength": r_squared,
            "slope": slope,
            "current_value": y[-1] if len(y) > 0 else None
        }

    async def _analyze_divergences(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """ダイバージェンス分析"""
        divergences = []
        
        # 価格データも取得してダイバージェンスを検出
        # 実装例：RSIと価格のダイバージェンス
        
        return divergences

    async def _analyze_support_resistance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """サポート・レジスタンス分析"""
        # 移動平均線をサポート・レジスタンスとして分析
        support_resistance = {}
        
        if "SMA" in data.columns:
            sma_values = data["SMA"].dropna()
            if not sma_values.empty:
                support_resistance["SMA"] = {
                    "current": sma_values.iloc[0],
                    "support": sma_values.min(),
                    "resistance": sma_values.max()
                }

        return support_resistance

    async def _analyze_volatility(self, data: pd.DataFrame) -> Dict[str, Any]:
        """ボラティリティ分析"""
        volatility = {}
        
        if "ATR" in data.columns:
            atr_values = data["ATR"].dropna()
            if not atr_values.empty:
                current_atr = atr_values.iloc[0]
                avg_atr = atr_values.mean()
                
                volatility["ATR"] = {
                    "current": current_atr,
                    "average": avg_atr,
                    "level": "高" if current_atr > avg_atr * 1.5 else "低" if current_atr < avg_atr * 0.5 else "中"
                }

        return volatility

    async def _analyze_momentum(self, data: pd.DataFrame) -> Dict[str, Any]:
        """モメンタム分析"""
        momentum = {}
        
        # RSIモメンタム
        if "RSI" in data.columns:
            rsi_values = data["RSI"].dropna()
            if len(rsi_values) >= 2:
                rsi_momentum = rsi_values.iloc[0] - rsi_values.iloc[1]
                momentum["RSI"] = {
                    "momentum": rsi_momentum,
                    "direction": "上昇" if rsi_momentum > 0 else "下降",
                    "strength": abs(rsi_momentum)
                }

        return momentum

    async def _generate_summary(self, data: pd.DataFrame) -> Dict[str, Any]:
        """総合サマリー生成"""
        if data.empty:
            return {"error": "データがありません"}

        # 現在のシグナルを取得
        current_signals = await self._analyze_current_signals(data)
        
        # シグナルカウント
        buy_signals = len([s for s in current_signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]])
        sell_signals = len([s for s in current_signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]])
        
        # 平均信頼度
        avg_confidence = np.mean([s.confidence for s in current_signals]) if current_signals else 0
        
        # 総合判断
        if buy_signals > sell_signals and avg_confidence > 0.6:
            overall_signal = "買い"
        elif sell_signals > buy_signals and avg_confidence > 0.6:
            overall_signal = "売り"
        else:
            overall_signal = "ホールド"

        return {
            "overall_signal": overall_signal,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "avg_confidence": avg_confidence,
            "total_signals": len(current_signals)
        }

    def display_analysis_results(self, results: Dict[str, Any]) -> None:
        """分析結果を表示"""
        if "error" in results:
            console.print(f"❌ {results['error']}")
            return

        console.print("\n🎯 高度なシグナル分析結果")
        console.print("=" * 60)

        # 総合サマリー
        if "summary" in results:
            summary = results["summary"]
            console.print(f"\n📊 総合判断: {summary['overall_signal']}")
            console.print(f"買いシグナル: {summary['buy_signals']}件")
            console.print(f"売りシグナル: {summary['sell_signals']}件")
            console.print(f"平均信頼度: {summary['avg_confidence']:.2f}")

        # 現在のシグナル
        if "current_signals" in results:
            signals = results["current_signals"]
            if signals:
                console.print("\n🔔 現在のシグナル:")
                for signal in signals:
                    emoji = "🟢" if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else "🔴"
                    console.print(f"  {emoji} {signal.signal_type.value} ({signal.strength.value}) - {signal.reasoning}")
                    console.print(f"     信頼度: {signal.confidence:.2f}")

        # トレンド分析
        if "trend_analysis" in results:
            trends = results["trend_analysis"]
            if trends:
                console.print("\n📈 トレンド分析:")
                for indicator, trend in trends.items():
                    if "error" not in trend:
                        console.print(f"  {indicator}: {trend['direction']} (強度: {trend['strength']:.2f})")

        # ボラティリティ分析
        if "volatility_analysis" in results:
            volatility = results["volatility_analysis"]
            if volatility:
                console.print("\n📊 ボラティリティ分析:")
                for indicator, vol in volatility.items():
                    console.print(f"  {indicator}: {vol['level']} (現在: {vol['current']:.3f})")

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
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="高度なシグナル分析システム")
    parser.add_argument("--timeframe", "-tf", default="M5", help="時間足 (M5, H1, H4, D1)")
    parser.add_argument("--days", "-d", type=int, default=7, help="分析期間（日数）")
    parser.add_argument("--currency-pair", "-p", default="USD/JPY", help="通貨ペア")
    
    args = parser.parse_args()
    
    analyzer = AdvancedSignalAnalyzer(args.currency_pair)
    
    if not await analyzer.initialize():
        return

    try:
        # 分析実行
        results = await analyzer.analyze_comprehensive_signals(args.timeframe, args.days)
        
        # 結果表示
        analyzer.display_analysis_results(results)

    except Exception as e:
        console.print(f"❌ 実行エラー: {e}")
    
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
