"""
トレンド強度計算器

プロトレーダー向け為替アラートシステム用のトレンド強度計算器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.technical_indicator_model import TechnicalIndicatorModel


class TrendStrengthCalculator:
    """
    トレンド強度計算器

    責任:
    - 移動平均線の傾き計算
    - ADXによるトレンド強度測定
    - 複数指標の重み付け計算
    - トレンド強度スコア正規化

    特徴:
    - 複数指標組み合わせ
    - 動的重み付け
    - スコア正規化
    - 履歴データ分析
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"

    async def calculate_trend_strength(self, timeframe: str = "H1") -> Dict[str, Any]:
        """
        トレンド強度計算

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: トレンド強度分析結果
        """
        try:
            # 移動平均線の傾きを計算
            ma_slope = await self._calculate_ma_slope(timeframe)
            
            # ADXによるトレンド強度を測定
            adx_strength = await self._calculate_adx_strength(timeframe)
            
            # 価格モメンタムを計算
            price_momentum = await self._calculate_price_momentum(timeframe)
            
            # ボラティリティ調整を計算
            volatility_adjustment = await self._calculate_volatility_adjustment(timeframe)
            
            # 統合トレンド強度スコアを計算
            integrated_score = self._calculate_integrated_score(
                ma_slope, adx_strength, price_momentum, volatility_adjustment
            )
            
            # トレンド方向を判定
            trend_direction = self._determine_trend_direction(ma_slope, price_momentum)
            
            return {
                "timeframe": timeframe,
                "trend_direction": trend_direction,
                "strength_score": integrated_score,
                "ma_slope": ma_slope,
                "adx_strength": adx_strength,
                "price_momentum": price_momentum,
                "volatility_adjustment": volatility_adjustment,
                "timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error calculating trend strength: {e}")
            return {}

    async def _calculate_ma_slope(self, timeframe: str) -> Dict[str, Any]:
        """
        移動平均線の傾きを計算

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: 移動平均線傾き分析結果
        """
        try:
            # 過去20期間の移動平均データを取得
            ma_data = await self._get_ma_data(timeframe, periods=20)
            
            if len(ma_data) < 10:
                return {"slope": 0, "strength": 0, "direction": "neutral"}

            # 線形回帰による傾き計算
            slope = self._calculate_linear_slope(ma_data)
            
            # 傾き強度を正規化（0-100）
            strength = min(100, abs(slope) * 1000)
            
            # 方向判定
            if slope > 0.001:
                direction = "uptrend"
            elif slope < -0.001:
                direction = "downtrend"
            else:
                direction = "sideways"

            return {
                "slope": slope,
                "strength": strength,
                "direction": direction,
                "ma_values": ma_data[-5:],  # 最新5期間
            }

        except Exception as e:
            print(f"Error calculating MA slope: {e}")
            return {"slope": 0, "strength": 0, "direction": "neutral"}

    async def _calculate_adx_strength(self, timeframe: str) -> Dict[str, Any]:
        """
        ADXによるトレンド強度を測定

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: ADX強度分析結果
        """
        try:
            # 最新のADXデータを取得
            adx_data = await self._get_adx_data(timeframe, periods=5)
            
            if not adx_data:
                return {"adx_value": 0, "strength": 0, "trend_quality": "weak"}

            current_adx = adx_data[-1]
            
            # ADX強度を正規化（0-100）
            strength = min(100, current_adx)
            
            # トレンド品質判定
            if current_adx > 25:
                trend_quality = "strong"
            elif current_adx > 20:
                trend_quality = "moderate"
            else:
                trend_quality = "weak"

            return {
                "adx_value": current_adx,
                "strength": strength,
                "trend_quality": trend_quality,
                "adx_history": adx_data,
            }

        except Exception as e:
            print(f"Error calculating ADX strength: {e}")
            return {"adx_value": 0, "strength": 0, "trend_quality": "weak"}

    async def _calculate_price_momentum(self, timeframe: str) -> Dict[str, Any]:
        """
        価格モメンタムを計算

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: 価格モメンタム分析結果
        """
        try:
            # 過去10期間の価格データを取得
            price_data = await self._get_price_data(timeframe, periods=10)
            
            if len(price_data) < 5:
                return {"momentum": 0, "strength": 0, "direction": "neutral"}

            # 価格変化率を計算
            price_changes = []
            for i in range(1, len(price_data)):
                change = (price_data[i] - price_data[i-1]) / price_data[i-1] * 100
                price_changes.append(change)

            # 平均モメンタム
            avg_momentum = sum(price_changes) / len(price_changes)
            
            # モメンタム強度を正規化（0-100）
            strength = min(100, abs(avg_momentum) * 10)
            
            # 方向判定
            if avg_momentum > 0.1:
                direction = "bullish"
            elif avg_momentum < -0.1:
                direction = "bearish"
            else:
                direction = "neutral"

            return {
                "momentum": avg_momentum,
                "strength": strength,
                "direction": direction,
                "price_changes": price_changes[-3:],  # 最新3期間
            }

        except Exception as e:
            print(f"Error calculating price momentum: {e}")
            return {"momentum": 0, "strength": 0, "direction": "neutral"}

    async def _calculate_volatility_adjustment(self, timeframe: str) -> Dict[str, Any]:
        """
        ボラティリティ調整を計算

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: ボラティリティ調整結果
        """
        try:
            # ATRデータを取得
            atr_data = await self._get_atr_data(timeframe, periods=10)
            
            if not atr_data:
                return {"adjustment": 1.0, "factor": 1.0, "volatility_level": "normal"}

            current_atr = atr_data[-1]
            avg_atr = sum(atr_data[:-1]) / len(atr_data[:-1]) if len(atr_data) > 1 else current_atr
            
            # ボラティリティ比率
            volatility_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
            
            # 調整係数（高ボラティリティ時は調整を強める）
            if volatility_ratio > 1.5:
                adjustment = 0.8  # 高ボラティリティ時は調整を強める
                volatility_level = "high"
            elif volatility_ratio < 0.7:
                adjustment = 1.2  # 低ボラティリティ時は調整を弱める
                volatility_level = "low"
            else:
                adjustment = 1.0
                volatility_level = "normal"

            return {
                "adjustment": adjustment,
                "factor": volatility_ratio,
                "volatility_level": volatility_level,
                "current_atr": current_atr,
                "avg_atr": avg_atr,
            }

        except Exception as e:
            print(f"Error calculating volatility adjustment: {e}")
            return {"adjustment": 1.0, "factor": 1.0, "volatility_level": "normal"}

    def _calculate_integrated_score(
        self,
        ma_slope: Dict[str, Any],
        adx_strength: Dict[str, Any],
        price_momentum: Dict[str, Any],
        volatility_adjustment: Dict[str, Any],
    ) -> int:
        """
        統合トレンド強度スコアを計算

        Args:
            ma_slope: 移動平均線傾き分析結果
            adx_strength: ADX強度分析結果
            price_momentum: 価格モメンタム分析結果
            volatility_adjustment: ボラティリティ調整結果

        Returns:
            int: 統合スコア（0-100）
        """
        # 重み付け計算
        ma_weight = 0.35    # 35%
        adx_weight = 0.30   # 30%
        momentum_weight = 0.25  # 25%
        volatility_weight = 0.10  # 10%

        # 各要素のスコア
        ma_score = ma_slope.get("strength", 0)
        adx_score = adx_strength.get("strength", 0)
        momentum_score = price_momentum.get("strength", 0)
        volatility_score = 100 - (volatility_adjustment.get("factor", 1.0) - 1.0) * 50

        # 統合スコア計算
        integrated_score = (
            ma_score * ma_weight +
            adx_score * adx_weight +
            momentum_score * momentum_weight +
            volatility_score * volatility_weight
        )

        # ボラティリティ調整を適用
        adjustment = volatility_adjustment.get("adjustment", 1.0)
        adjusted_score = integrated_score * adjustment

        return min(100, max(0, int(adjusted_score)))

    def _determine_trend_direction(
        self, ma_slope: Dict[str, Any], price_momentum: Dict[str, Any]
    ) -> str:
        """
        トレンド方向を判定

        Args:
            ma_slope: 移動平均線傾き分析結果
            price_momentum: 価格モメンタム分析結果

        Returns:
            str: トレンド方向
        """
        ma_direction = ma_slope.get("direction", "neutral")
        momentum_direction = price_momentum.get("direction", "neutral")

        # 両方とも同じ方向の場合
        if ma_direction == momentum_direction:
            return ma_direction
        
        # 移動平均線の方向を優先
        if ma_direction in ["uptrend", "downtrend"]:
            return ma_direction
        
        # モメンタムの方向を確認
        if momentum_direction in ["bullish", "bearish"]:
            return "uptrend" if momentum_direction == "bullish" else "downtrend"
        
        return "sideways"

    def _calculate_linear_slope(self, data: List[float]) -> float:
        """
        線形回帰による傾き計算

        Args:
            data: データリスト

        Returns:
            float: 傾き
        """
        if len(data) < 2:
            return 0.0

        n = len(data)
        x_sum = sum(range(n))
        y_sum = sum(data)
        xy_sum = sum(i * data[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))

        # 最小二乗法による傾き計算
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
        
        return slope

    async def _get_ma_data(self, timeframe: str, periods: int) -> List[float]:
        """
        移動平均データを取得

        Args:
            timeframe: タイムフレーム
            periods: 取得期間数

        Returns:
            List[float]: 移動平均データ
        """
        try:
            query = select(TechnicalIndicatorModel.value).where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.indicator_type == "SMA_20",
            ).order_by(TechnicalIndicatorModel.timestamp.desc()).limit(periods)

            result = await self.db_session.execute(query)
            ma_values = [float(value) for value in result.scalars().all()]
            
            return ma_values[::-1]  # 時系列順に並び替え

        except Exception as e:
            print(f"Error getting MA data: {e}")
            return []

    async def _get_adx_data(self, timeframe: str, periods: int) -> List[float]:
        """
        ADXデータを取得

        Args:
            timeframe: タイムフレーム
            periods: 取得期間数

        Returns:
            List[float]: ADXデータ
        """
        try:
            query = select(TechnicalIndicatorModel.value).where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.indicator_type == "ADX",
            ).order_by(TechnicalIndicatorModel.timestamp.desc()).limit(periods)

            result = await self.db_session.execute(query)
            adx_values = [float(value) for value in result.scalars().all()]
            
            return adx_values[::-1]  # 時系列順に並び替え

        except Exception as e:
            print(f"Error getting ADX data: {e}")
            return []

    async def _get_price_data(self, timeframe: str, periods: int) -> List[float]:
        """
        価格データを取得

        Args:
            timeframe: タイムフレーム
            periods: 取得期間数

        Returns:
            List[float]: 価格データ
        """
        try:
            query = select(TechnicalIndicatorModel.value).where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.indicator_type == "close",
            ).order_by(TechnicalIndicatorModel.timestamp.desc()).limit(periods)

            result = await self.db_session.execute(query)
            price_values = [float(value) for value in result.scalars().all()]
            
            return price_values[::-1]  # 時系列順に並び替え

        except Exception as e:
            print(f"Error getting price data: {e}")
            return []

    async def _get_atr_data(self, timeframe: str, periods: int) -> List[float]:
        """
        ATRデータを取得

        Args:
            timeframe: タイムフレーム
            periods: 取得期間数

        Returns:
            List[float]: ATRデータ
        """
        try:
            query = select(TechnicalIndicatorModel.value).where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.indicator_type == "ATR",
            ).order_by(TechnicalIndicatorModel.timestamp.desc()).limit(periods)

            result = await self.db_session.execute(query)
            atr_values = [float(value) for value in result.scalars().all()]
            
            return atr_values[::-1]  # 時系列順に並び替え

        except Exception as e:
            print(f"Error getting ATR data: {e}")
            return []

    async def get_trend_strength_history(
        self, timeframe: str = "H1", days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        トレンド強度履歴を取得

        Args:
            timeframe: タイムフレーム
            days: 取得日数

        Returns:
            List[Dict[str, Any]]: トレンド強度履歴
        """
        try:
            history = []
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # 日次でトレンド強度を計算
            current_date = start_date
            while current_date <= datetime.utcnow():
                # その日のトレンド強度を計算（簡易実装）
                strength_data = await self.calculate_trend_strength(timeframe)
                
                if strength_data:
                    history.append({
                        "date": current_date.date(),
                        "strength_score": strength_data.get("strength_score", 0),
                        "trend_direction": strength_data.get("trend_direction", "unknown"),
                        "ma_slope": strength_data.get("ma_slope", {}),
                        "adx_strength": strength_data.get("adx_strength", {}),
                    })
                
                current_date += timedelta(days=1)
            
            return history

        except Exception as e:
            print(f"Error getting trend strength history: {e}")
            return []
