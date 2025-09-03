"""
ボリンジャーバンドエントリー検出器

プロトレーダー向け為替アラートシステム用のボリンジャーバンドエントリー検出器
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


class BollingerBandsEntryDetector:
    """
    ボリンジャーバンドエントリー検出器

    責任:
    - ボリンジャーバンドベースのエントリーシグナル検出
    - バンドタッチ条件の分析
    - 出来高との組み合わせ分析
    - RSIとの組み合わせ分析

    特徴:
    - バンドタッチ検出
    - 出来高分析
    - 複数指標組み合わせ
    - 動的リスク管理
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"

    async def detect_bb_entry_signals(
        self, timeframe: str = "M5"
    ) -> List[EntrySignalModel]:
        """
        ボリンジャーバンドベースのエントリーシグナル検出

        買いシグナル条件:
        - 価格が下バンドにタッチ
        - RSI < 40 (過売り傾向)
        - 出来高 > 平均出来高の1.5倍

        売りシグナル条件:
        - 価格が上バンドにタッチ
        - RSI > 60 (過買い傾向)
        - 出来高 > 平均出来高の1.5倍

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

        # ボリンジャーバンド条件チェック
        bb_upper = indicators.get("BB_upper")
        bb_lower = indicators.get("BB_lower")
        bb_middle = indicators.get("BB_middle")
        rsi = indicators.get("RSI")
        volume = indicators.get("volume")
        avg_volume = indicators.get("avg_volume")

        if all([bb_upper, bb_lower, bb_middle, rsi, volume, avg_volume]):
            # 買いシグナル（下バンドタッチ）
            if self._check_buy_conditions(
                current_price, bb_lower, rsi, volume, avg_volume
            ):
                signal = await self._create_buy_signal(
                    current_price=current_price,
                    bb_lower=bb_lower,
                    bb_middle=bb_middle,
                    indicators=indicators,
                    timeframe=timeframe,
                )
                if signal:
                    signals.append(signal)

            # 売りシグナル（上バンドタッチ）
            elif self._check_sell_conditions(
                current_price, bb_upper, rsi, volume, avg_volume
            ):
                signal = await self._create_sell_signal(
                    current_price=current_price,
                    bb_upper=bb_upper,
                    bb_middle=bb_middle,
                    indicators=indicators,
                    timeframe=timeframe,
                )
                if signal:
                    signals.append(signal)

        return signals

    def _check_buy_conditions(
        self,
        current_price: float,
        bb_lower: float,
        rsi: float,
        volume: float,
        avg_volume: float,
    ) -> bool:
        """
        買いシグナル条件チェック

        Args:
            current_price: 現在価格
            bb_lower: 下バンド
            rsi: RSI値
            volume: 出来高
            avg_volume: 平均出来高

        Returns:
            bool: 買いシグナル条件を満たすかどうか
        """
        return (
            current_price <= bb_lower * 1.001  # 0.1%以内で下バンドタッチ
            and rsi < 40  # 過売り傾向
            and volume > avg_volume * 1.5  # 出来高増加
        )

    def _check_sell_conditions(
        self,
        current_price: float,
        bb_upper: float,
        rsi: float,
        volume: float,
        avg_volume: float,
    ) -> bool:
        """
        売りシグナル条件チェック

        Args:
            current_price: 現在価格
            bb_upper: 上バンド
            rsi: RSI値
            volume: 出来高
            avg_volume: 平均出来高

        Returns:
            bool: 売りシグナル条件を満たすかどうか
        """
        return (
            current_price >= bb_upper * 0.999  # 0.1%以内で上バンドタッチ
            and rsi > 60  # 過買い傾向
            and volume > avg_volume * 1.5  # 出来高増加
        )

    async def _create_buy_signal(
        self,
        current_price: float,
        bb_lower: float,
        bb_middle: float,
        indicators: Dict[str, Any],
        timeframe: str,
    ) -> Optional[EntrySignalModel]:
        """
        買いシグナル作成

        Args:
            current_price: 現在価格
            bb_lower: 下バンド
            bb_middle: ミドルバンド
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Optional[EntrySignalModel]: 買いシグナル
        """
        # ストップロス: 下バンドの0.5%下
        stop_loss = bb_lower * 0.995
        # 利益確定: ミドルバンド
        take_profit = bb_middle

        # 信頼度スコア計算
        confidence_score = self._calculate_bb_confidence(indicators, "BUY")

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
        bb_upper: float,
        bb_middle: float,
        indicators: Dict[str, Any],
        timeframe: str,
    ) -> Optional[EntrySignalModel]:
        """
        売りシグナル作成

        Args:
            current_price: 現在価格
            bb_upper: 上バンド
            bb_middle: ミドルバンド
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Optional[EntrySignalModel]: 売りシグナル
        """
        # ストップロス: 上バンドの0.5%上
        stop_loss = bb_upper * 1.005
        # 利益確定: ミドルバンド
        take_profit = bb_middle

        # 信頼度スコア計算
        confidence_score = self._calculate_bb_confidence(indicators, "SELL")

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

    def _calculate_bb_confidence(
        self, indicators: Dict[str, Any], signal_type: str
    ) -> int:
        """
        ボリンジャーバンド信頼度スコア計算

        Args:
            indicators: 指標データ
            signal_type: シグナルタイプ

        Returns:
            int: 信頼度スコア（0-100）
        """
        score = 50  # ベーススコア

        # バンドタッチスコア
        bb_upper = indicators.get("BB_upper")
        bb_lower = indicators.get("BB_lower")
        current_price = indicators.get("close")

        if bb_upper and bb_lower and current_price:
            if signal_type == "BUY" and current_price <= bb_lower * 1.001:
                score += 25
            elif signal_type == "SELL" and current_price >= bb_upper * 0.999:
                score += 25

        # RSIスコア
        rsi = indicators.get("RSI", 50)
        if signal_type == "BUY" and rsi < 40:
            score += 15
        elif signal_type == "SELL" and rsi > 60:
            score += 15

        # 出来高スコア
        volume = indicators.get("volume", 0)
        avg_volume = indicators.get("avg_volume", 1)
        if volume > avg_volume * 1.5:
            score += 10

        # バンド幅スコア
        bb_width = indicators.get("BB_width", 0)
        if 0.02 <= bb_width <= 0.05:  # 適正なバンド幅
            score += 10

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
            "trend": self._determine_bb_trend(indicators),
            "volatility": self._determine_bb_volatility(indicators),
            "momentum": self._determine_bb_momentum(indicators),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _determine_bb_trend(self, indicators: Dict[str, Any]) -> str:
        """
        ボリンジャーバンドトレンド判定

        Args:
            indicators: 指標データ

        Returns:
            str: トレンド方向
        """
        bb_middle = indicators.get("BB_middle")
        current_price = indicators.get("close")

        if bb_middle and current_price:
            if current_price > bb_middle:
                return "uptrend"
            elif current_price < bb_middle:
                return "downtrend"
        return "sideways"

    def _determine_bb_volatility(self, indicators: Dict[str, Any]) -> str:
        """
        ボリンジャーバンドボラティリティ判定

        Args:
            indicators: 指標データ

        Returns:
            str: ボラティリティレベル
        """
        bb_width = indicators.get("BB_width", 0)
        if bb_width < 0.02:
            return "low"
        elif bb_width < 0.05:
            return "normal"
        else:
            return "high"

    def _determine_bb_momentum(self, indicators: Dict[str, Any]) -> str:
        """
        ボリンジャーバンドモメンタム判定

        Args:
            indicators: 指標データ

        Returns:
            str: モメンタム方向
        """
        bb_upper = indicators.get("BB_upper")
        bb_lower = indicators.get("BB_lower")
        current_price = indicators.get("close")

        if bb_upper and bb_lower and current_price:
            if current_price <= bb_lower * 1.001:
                return "oversold"
            elif current_price >= bb_upper * 0.999:
                return "overbought"
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
