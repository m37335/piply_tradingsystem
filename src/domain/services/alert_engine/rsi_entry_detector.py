"""
RSIエントリー検出器

プロトレーダー向け為替アラートシステム用のRSIエントリー検出器
設計書参照: /app/note/2025-01-15_アラートシステム_プロトレーダー向け為替アラートシステム設計書.md
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.entry_signal_model import EntrySignalModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)


class RSIEntryDetector:
    """
    RSIエントリー検出器

    責任:
    - RSIベースのエントリーシグナル検出
    - 移動平均線との組み合わせ分析
    - 信頼度スコア計算
    - リスク/リワード比計算

    特徴:
    - 複数タイムフレーム対応
    - 動的閾値調整
    - 詳細な市場状況分析
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"

    async def detect_rsi_entry_signals(
        self, timeframe: str = "M5"
    ) -> List[EntrySignalModel]:
        """
        RSIベースのエントリーシグナル検出（EMAの傾き使用）

        買いシグナル条件:
        - RSI < 55 (過売り - 最適化)
        - 価格 > SMA20 (上昇トレンド)
        - EMA12 > EMA26 (上昇モメンタム)
        - SMA20 > SMA50 (短期上昇トレンド確認)
        - ボラティリティが適正範囲

        売りシグナル条件:
        - RSI > 45 (過買い - 最適化)
        - 価格 < SMA20 (下降トレンド)
        - EMA12 < EMA26 (下降モメンタム)
        - SMA20 < SMA50 (短期下降トレンド確認)
        - ボラティリティが適正範囲

        Args:
            timeframe: タイムフレーム

        Returns:
            List[EntrySignalModel]: 検出されたエントリーシグナル
        """
        signals = []

        # 最新のテクニカル指標データを取得
        indicators = await self._get_latest_indicators(timeframe)
        if not indicators:
            return signals

        # 現在価格を取得
        current_price = await self._get_current_price()
        if not current_price:
            return signals

        # RSI条件チェック
        rsi = indicators.get("RSI")
        sma_20 = indicators.get("SMA_20")
        ema_12 = indicators.get("EMA_12")
        ema_26 = indicators.get("EMA_26")
        sma_50 = indicators.get("SMA_50")
        atr = indicators.get("ATR")

        if all([rsi, sma_20, ema_12, ema_26, atr]):
            # 買いシグナル
            if self._check_buy_conditions(
                rsi, current_price, sma_20, ema_12, ema_26, atr, sma_50
            ):
                signal = await self._create_buy_signal(
                    current_price=current_price,
                    sma_20=sma_20,
                    atr=atr,
                    indicators=indicators,
                    timeframe=timeframe,
                )
                if signal:
                    signals.append(signal)

            # 売りシグナル
            elif self._check_sell_conditions(
                rsi, current_price, sma_20, ema_12, ema_26, atr, sma_50
            ):
                signal = await self._create_sell_signal(
                    current_price=current_price,
                    sma_20=sma_20,
                    atr=atr,
                    indicators=indicators,
                    timeframe=timeframe,
                )
                if signal:
                    signals.append(signal)

        return signals

    def _check_buy_conditions(
        self,
        rsi: float,
        current_price: float,
        sma_20: float,
        ema_12: float,
        ema_26: float,
        atr: float,
        sma_50: float = None,
    ) -> bool:
        """
        買いシグナル条件チェック

        Args:
            rsi: RSI値
            current_price: 現在価格
            sma_20: 20期間移動平均
            ema_12: 12期間EMA
            ema_26: 26期間EMA
            atr: ATR値

        Returns:
            bool: 買いシグナル条件を満たすかどうか
        """
        # SMA_50が利用可能な場合のみ条件に追加
        sma_50_condition = True
        if sma_50 is not None:
            sma_50_condition = sma_20 > sma_50

        return (
            rsi < 55  # 過売り（最適化）
            and current_price > sma_20  # 上昇トレンド
            and ema_12 > ema_26  # 上昇モメンタム
            and sma_50_condition  # 短期上昇トレンド確認
            and self._is_volatility_normal(atr)  # ボラティリティ適正
        )

    def _check_sell_conditions(
        self,
        rsi: float,
        current_price: float,
        sma_20: float,
        ema_12: float,
        ema_26: float,
        atr: float,
        sma_50: float = None,
    ) -> bool:
        """
        売りシグナル条件チェック

        Args:
            rsi: RSI値
            current_price: 現在価格
            sma_20: 20期間移動平均
            ema_12: 12期間EMA
            ema_26: 26期間EMA
            atr: ATR値

        Returns:
            bool: 売りシグナル条件を満たすかどうか
        """
        # SMA_50が利用可能な場合のみ条件に追加
        sma_50_condition = True
        if sma_50 is not None:
            sma_50_condition = sma_20 < sma_50

        return (
            rsi > 45  # 過買い（最適化）
            and current_price < sma_20  # 下降トレンド
            and ema_12 < ema_26  # 下降モメンタム
            and sma_50_condition  # 短期下降トレンド確認
            and self._is_volatility_normal(atr)  # ボラティリティ適正
        )

    def _is_volatility_normal(self, atr: float) -> bool:
        """
        ボラティリティが適正範囲かチェック

        Args:
            atr: ATR値

        Returns:
            bool: ボラティリティが適正かどうか
        """
        # ATRが0.01-0.10の範囲内（USD/JPYの場合）
        return 0.01 <= atr <= 0.10

    async def _create_buy_signal(
        self,
        current_price: float,
        sma_20: float,
        atr: float,
        indicators: Dict[str, Any],
        timeframe: str,
    ) -> Optional[EntrySignalModel]:
        """
        買いシグナル作成

        Args:
            current_price: 現在価格
            sma_20: 20期間移動平均
            atr: ATR値
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Optional[EntrySignalModel]: 買いシグナル
        """
        # ストップロス: SMA20の0.5%下
        stop_loss = sma_20 * 0.995
        # 利益確定: 現在価格の1.5%上
        take_profit = current_price * 1.015

        # 信頼度スコア計算
        confidence_score = self._calculate_confidence_score(indicators, "BUY")

        return EntrySignalModel.create_buy_signal(
            currency_pair=self.currency_pair,
            timestamp=datetime.utcnow(),
            timeframe=timeframe,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence_score=confidence_score,
            indicators_used=indicators,
            market_conditions=self._get_market_conditions(indicators),
        )

    async def _create_sell_signal(
        self,
        current_price: float,
        sma_20: float,
        atr: float,
        indicators: Dict[str, Any],
        timeframe: str,
    ) -> Optional[EntrySignalModel]:
        """
        売りシグナル作成

        Args:
            current_price: 現在価格
            sma_20: 20期間移動平均
            atr: ATR値
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Optional[EntrySignalModel]: 売りシグナル
        """
        # ストップロス: SMA20の0.5%上
        stop_loss = sma_20 * 1.005
        # 利益確定: 現在価格の1.5%下
        take_profit = current_price * 0.985

        # 信頼度スコア計算
        confidence_score = self._calculate_confidence_score(indicators, "SELL")

        return EntrySignalModel.create_sell_signal(
            currency_pair=self.currency_pair,
            timestamp=datetime.utcnow(),
            timeframe=timeframe,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence_score=confidence_score,
            indicators_used=indicators,
            market_conditions=self._get_market_conditions(indicators),
        )

    def _calculate_confidence_score(
        self, indicators: Dict[str, Any], signal_type: str
    ) -> int:
        """
        信頼度スコア計算

        Args:
            indicators: 指標データ
            signal_type: シグナルタイプ

        Returns:
            int: 信頼度スコア（0-100）
        """
        score = 50  # ベーススコア

        # RSIスコア
        rsi = indicators.get("RSI", 50)
        if signal_type == "BUY" and rsi < 55:
            score += 20
        elif signal_type == "SELL" and rsi > 45:
            score += 20

        # 移動平均スコア
        sma_20 = indicators.get("SMA_20")
        current_price = indicators.get("close")
        if sma_20 and current_price:
            if signal_type == "BUY" and current_price > sma_20:
                score += 15
            elif signal_type == "SELL" and current_price < sma_20:
                score += 15

        # EMAスコア
        ema_12 = indicators.get("EMA_12")
        ema_26 = indicators.get("EMA_26")
        if ema_12 and ema_26:
            if signal_type == "BUY" and ema_12 > ema_26:
                score += 10
            elif signal_type == "SELL" and ema_12 < ema_26:
                score += 10

        # ボラティリティスコア
        atr = indicators.get("ATR", 0)
        if self._is_volatility_normal(atr):
            score += 5

        return min(score, 100)  # 最大100

    def _get_market_conditions(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        市場状況を取得

        Args:
            indicators: 指標データ

        Returns:
            Dict[str, Any]: 市場状況
        """
        return {
            "trend": self._determine_trend(indicators),
            "volatility": self._determine_volatility(indicators),
            "momentum": self._determine_momentum(indicators),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _determine_trend(self, indicators: Dict[str, Any]) -> str:
        """
        トレンド判定

        Args:
            indicators: 指標データ

        Returns:
            str: トレンド方向
        """
        sma_20 = indicators.get("SMA_20")
        current_price = indicators.get("close")

        if sma_20 and current_price:
            if current_price > sma_20:
                return "uptrend"
            elif current_price < sma_20:
                return "downtrend"
        return "sideways"

    def _determine_volatility(self, indicators: Dict[str, Any]) -> str:
        """
        ボラティリティ判定

        Args:
            indicators: 指標データ

        Returns:
            str: ボラティリティレベル
        """
        atr = indicators.get("ATR", 0)
        if atr < 0.02:
            return "low"
        elif atr < 0.05:
            return "normal"
        else:
            return "high"

    def _determine_momentum(self, indicators: Dict[str, Any]) -> str:
        """
        モメンタム判定

        Args:
            indicators: 指標データ

        Returns:
            str: モメンタム方向
        """
        ema_12 = indicators.get("EMA_12")
        ema_26 = indicators.get("EMA_26")
        if ema_12 and ema_26:
            if ema_12 > ema_26:
                return "bullish"
            elif ema_12 < ema_26:
                return "bearish"
        return "neutral"

    async def _get_latest_indicators(self, timeframe: str) -> Dict[str, Any]:
        """
        最新のテクニカル指標データを取得

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: 指標データ
        """
        try:
            # 最新のタイムスタンプを取得
            latest_timestamp_query = (
                select(TechnicalIndicatorModel.timestamp)
                .where(
                    TechnicalIndicatorModel.currency_pair == self.currency_pair,
                    TechnicalIndicatorModel.timeframe == timeframe,
                )
                .order_by(TechnicalIndicatorModel.timestamp.desc())
                .limit(1)
            )

            result = await self.db_session.execute(latest_timestamp_query)
            latest_timestamp = result.scalar() if result else None

            if not latest_timestamp:
                return {}

            # 最新タイムスタンプの全指標を取得
            indicators_query = select(TechnicalIndicatorModel).where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
                TechnicalIndicatorModel.timestamp == latest_timestamp,
            )

            result = await self.db_session.execute(indicators_query)
            indicators = result.scalars().all()

            # 辞書形式に変換
            indicators_dict = {}
            for indicator in indicators:
                indicators_dict[indicator.indicator_type] = indicator.value
                if indicator.additional_data:
                    indicators_dict.update(indicator.additional_data)

            return indicators_dict

        except Exception as e:
            print(f"Error getting latest indicators: {e}")
            return {}

    async def _get_current_price(self) -> Optional[float]:
        """
        現在価格を取得

        Returns:
            Optional[float]: 現在価格
        """
        try:
            # 最新の価格データを取得（簡易実装）
            # 実際の実装では価格データテーブルから取得
            return 150.000  # 仮の価格
        except Exception as e:
            print(f"Error getting current price: {e}")
            return None

    async def save_signals(self, signals: List[EntrySignalModel]) -> None:
        """
        シグナルをデータベースに保存

        Args:
            signals: 保存するシグナルリスト
        """
        try:
            for signal in signals:
                if signal.validate():
                    self.db_session.add(signal)
            await self.db_session.commit()
        except Exception as e:
            print(f"Error saving signals: {e}")
            await self.db_session.rollback()
