"""
マルチタイムフレーム統合分析器

プロトレーダー向け為替アラートシステム用のマルチタイムフレーム統合分析器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.technical_indicator_model import TechnicalIndicatorModel
from src.infrastructure.database.models.entry_signal_model import EntrySignalModel


class MultiTimeframeAnalyzer:
    """
    マルチタイムフレーム統合分析器

    責任:
    - 複数タイムフレームのデータ統合分析
    - 時間軸間の一貫性チェック
    - 統合信頼度スコア計算
    - トレンド方向性判定

    特徴:
    - 5つのタイムフレーム対応（M5, M15, H1, H4, D1）
    - 重み付け分析
    - 一貫性スコアリング
    - 統合シグナル生成
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"
        self.timeframes = ["M5", "M15", "H1", "H4", "D1"]
        
        # タイムフレーム重み付け（短時間軸ほど重みが高い）
        self.timeframe_weights = {
            "M5": 0.35,   # 35%
            "M15": 0.25,  # 25%
            "H1": 0.20,   # 20%
            "H4": 0.15,   # 15%
            "D1": 0.05    # 5%
        }

    async def analyze_multi_timeframe_signals(self) -> List[EntrySignalModel]:
        """
        マルチタイムフレーム統合シグナル分析

        Returns:
            List[EntrySignalModel]: 統合されたエントリーシグナル
        """
        signals = []

        # 各タイムフレームの分析結果を取得
        timeframe_analyses = {}
        for timeframe in self.timeframes:
            analysis = await self._analyze_single_timeframe(timeframe)
            if analysis:
                timeframe_analyses[timeframe] = analysis

        if not timeframe_analyses:
            return signals

        # 統合分析実行
        integrated_signals = self._integrate_timeframe_analyses(timeframe_analyses)
        
        # 一貫性チェック
        for signal in integrated_signals:
            if self._check_timeframe_consistency(signal, timeframe_analyses):
                signals.append(signal)

        return signals

    async def _analyze_single_timeframe(self, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        単一タイムフレーム分析

        Args:
            timeframe: タイムフレーム

        Returns:
            Optional[Dict[str, Any]]: 分析結果
        """
        try:
            # 最新の指標データを取得
            indicators = await self._get_latest_indicators(timeframe)
            if not indicators:
                return None

            # トレンド分析
            trend_analysis = self._analyze_trend(indicators, timeframe)
            
            # モメンタム分析
            momentum_analysis = self._analyze_momentum(indicators, timeframe)
            
            # ボラティリティ分析
            volatility_analysis = self._analyze_volatility(indicators, timeframe)

            return {
                "timeframe": timeframe,
                "indicators": indicators,
                "trend": trend_analysis,
                "momentum": momentum_analysis,
                "volatility": volatility_analysis,
                "timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error analyzing timeframe {timeframe}: {e}")
            return None

    def _analyze_trend(self, indicators: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
        """
        トレンド分析

        Args:
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: トレンド分析結果
        """
        sma_20 = indicators.get("SMA_20")
        sma_50 = indicators.get("SMA_50")
        current_price = indicators.get("close")
        
        if not all([sma_20, sma_50, current_price]):
            return {"direction": "unknown", "strength": 0, "confidence": 0}

        # トレンド方向判定
        if current_price > sma_20 > sma_50:
            direction = "uptrend"
            strength = min(100, ((current_price - sma_50) / sma_50) * 1000)
        elif current_price < sma_20 < sma_50:
            direction = "downtrend"
            strength = min(100, ((sma_50 - current_price) / sma_50) * 1000)
        else:
            direction = "sideways"
            strength = 0

        # 信頼度計算
        confidence = self._calculate_trend_confidence(indicators, direction)

        return {
            "direction": direction,
            "strength": strength,
            "confidence": confidence,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "current_price": current_price,
        }

    def _analyze_momentum(self, indicators: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
        """
        モメンタム分析

        Args:
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: モメンタム分析結果
        """
        rsi = indicators.get("RSI", 50)
        macd_hist = indicators.get("MACD_histogram", 0)
        stoch_k = indicators.get("STOCH_K", 50)
        stoch_d = indicators.get("STOCH_D", 50)

        # モメンタム方向判定
        momentum_score = 0
        
        # RSIスコア
        if rsi < 30:
            momentum_score += 25  # 過売り
        elif rsi > 70:
            momentum_score -= 25  # 過買い
        
        # MACDスコア
        if macd_hist > 0:
            momentum_score += 25
        else:
            momentum_score -= 25
        
        # ストキャスティクススコア
        if stoch_k < 20 and stoch_d < 20:
            momentum_score += 25
        elif stoch_k > 80 and stoch_d > 80:
            momentum_score -= 25

        # モメンタム方向判定
        if momentum_score > 25:
            direction = "bullish"
        elif momentum_score < -25:
            direction = "bearish"
        else:
            direction = "neutral"

        return {
            "direction": direction,
            "score": momentum_score,
            "rsi": rsi,
            "macd_histogram": macd_hist,
            "stoch_k": stoch_k,
            "stoch_d": stoch_d,
        }

    def _analyze_volatility(self, indicators: Dict[str, Any], timeframe: str) -> Dict[str, Any]:
        """
        ボラティリティ分析

        Args:
            indicators: 指標データ
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: ボラティリティ分析結果
        """
        atr = indicators.get("ATR", 0)
        bb_width = indicators.get("BB_width", 0)
        
        # ボラティリティレベル判定
        if atr < 0.02:
            level = "low"
        elif atr < 0.05:
            level = "normal"
        else:
            level = "high"

        # ボラティリティスコア（0-100）
        volatility_score = min(100, (atr / 0.05) * 100)

        return {
            "level": level,
            "score": volatility_score,
            "atr": atr,
            "bb_width": bb_width,
        }

    def _integrate_timeframe_analyses(
        self, timeframe_analyses: Dict[str, Dict[str, Any]]
    ) -> List[EntrySignalModel]:
        """
        タイムフレーム分析結果を統合

        Args:
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            List[EntrySignalModel]: 統合されたシグナル
        """
        signals = []

        # 統合トレンド分析
        integrated_trend = self._integrate_trends(timeframe_analyses)
        
        # 統合モメンタム分析
        integrated_momentum = self._integrate_momentums(timeframe_analyses)
        
        # 統合ボラティリティ分析
        integrated_volatility = self._integrate_volatilities(timeframe_analyses)

        # シグナル生成条件チェック
        if self._should_generate_buy_signal(integrated_trend, integrated_momentum, integrated_volatility):
            signal = self._create_integrated_buy_signal(
                integrated_trend, integrated_momentum, integrated_volatility, timeframe_analyses
            )
            if signal:
                signals.append(signal)

        elif self._should_generate_sell_signal(integrated_trend, integrated_momentum, integrated_volatility):
            signal = self._create_integrated_sell_signal(
                integrated_trend, integrated_momentum, integrated_volatility, timeframe_analyses
            )
            if signal:
                signals.append(signal)

        return signals

    def _integrate_trends(self, timeframe_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        トレンド分析結果を統合

        Args:
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Dict[str, Any]: 統合されたトレンド分析
        """
        trend_scores = {"uptrend": 0, "downtrend": 0, "sideways": 0}
        weighted_confidence = 0
        total_weight = 0

        for timeframe, analysis in timeframe_analyses.items():
            weight = self.timeframe_weights.get(timeframe, 0)
            trend = analysis["trend"]
            
            if trend["direction"] in trend_scores:
                trend_scores[trend["direction"]] += weight * trend["strength"]
            
            weighted_confidence += weight * trend["confidence"]
            total_weight += weight

        # 主要トレンド方向を決定
        primary_trend = max(trend_scores, key=trend_scores.get)
        
        # 平均信頼度
        avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0

        return {
            "direction": primary_trend,
            "strength": trend_scores[primary_trend],
            "confidence": avg_confidence,
            "scores": trend_scores,
        }

    def _integrate_momentums(self, timeframe_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        モメンタム分析結果を統合

        Args:
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Dict[str, Any]: 統合されたモメンタム分析
        """
        momentum_scores = {"bullish": 0, "bearish": 0, "neutral": 0}
        weighted_score = 0
        total_weight = 0

        for timeframe, analysis in timeframe_analyses.items():
            weight = self.timeframe_weights.get(timeframe, 0)
            momentum = analysis["momentum"]
            
            if momentum["direction"] in momentum_scores:
                momentum_scores[momentum["direction"]] += weight
            
            weighted_score += weight * momentum["score"]
            total_weight += weight

        # 主要モメンタム方向を決定
        primary_momentum = max(momentum_scores, key=momentum_scores.get)
        
        # 平均スコア
        avg_score = weighted_score / total_weight if total_weight > 0 else 0

        return {
            "direction": primary_momentum,
            "score": avg_score,
            "scores": momentum_scores,
        }

    def _integrate_volatilities(self, timeframe_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        ボラティリティ分析結果を統合

        Args:
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Dict[str, Any]: 統合されたボラティリティ分析
        """
        volatility_levels = {"low": 0, "normal": 0, "high": 0}
        weighted_score = 0
        total_weight = 0

        for timeframe, analysis in timeframe_analyses.items():
            weight = self.timeframe_weights.get(timeframe, 0)
            volatility = analysis["volatility"]
            
            if volatility["level"] in volatility_levels:
                volatility_levels[volatility["level"]] += weight
            
            weighted_score += weight * volatility["score"]
            total_weight += weight

        # 主要ボラティリティレベルを決定
        primary_level = max(volatility_levels, key=volatility_levels.get)
        
        # 平均スコア
        avg_score = weighted_score / total_weight if total_weight > 0 else 0

        return {
            "level": primary_level,
            "score": avg_score,
            "levels": volatility_levels,
        }

    def _should_generate_buy_signal(
        self,
        integrated_trend: Dict[str, Any],
        integrated_momentum: Dict[str, Any],
        integrated_volatility: Dict[str, Any],
    ) -> bool:
        """
        買いシグナル生成条件チェック

        Args:
            integrated_trend: 統合トレンド分析
            integrated_momentum: 統合モメンタム分析
            integrated_volatility: 統合ボラティリティ分析

        Returns:
            bool: 買いシグナルを生成すべきかどうか
        """
        return (
            integrated_trend["direction"] == "uptrend" and
            integrated_trend["confidence"] >= 60 and
            integrated_momentum["direction"] == "bullish" and
            integrated_volatility["level"] in ["normal", "low"]
        )

    def _should_generate_sell_signal(
        self,
        integrated_trend: Dict[str, Any],
        integrated_momentum: Dict[str, Any],
        integrated_volatility: Dict[str, Any],
    ) -> bool:
        """
        売りシグナル生成条件チェック

        Args:
            integrated_trend: 統合トレンド分析
            integrated_momentum: 統合モメンタム分析
            integrated_volatility: 統合ボラティリティ分析

        Returns:
            bool: 売りシグナルを生成すべきかどうか
        """
        return (
            integrated_trend["direction"] == "downtrend" and
            integrated_trend["confidence"] >= 60 and
            integrated_momentum["direction"] == "bearish" and
            integrated_volatility["level"] in ["normal", "low"]
        )

    def _create_integrated_buy_signal(
        self,
        integrated_trend: Dict[str, Any],
        integrated_momentum: Dict[str, Any],
        integrated_volatility: Dict[str, Any],
        timeframe_analyses: Dict[str, Dict[str, Any]],
    ) -> Optional[EntrySignalModel]:
        """
        統合買いシグナル作成

        Args:
            integrated_trend: 統合トレンド分析
            integrated_momentum: 統合モメンタム分析
            integrated_volatility: 統合ボラティリティ分析
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Optional[EntrySignalModel]: 買いシグナル
        """
        # 現在価格を取得（簡易実装）
        current_price = 150.000
        
        # ストップロスと利益確定を計算
        stop_loss = current_price * 0.995  # 0.5%下
        take_profit = current_price * 1.015  # 1.5%上
        
        # 統合信頼度スコア計算
        confidence_score = self._calculate_integrated_confidence(
            integrated_trend, integrated_momentum, integrated_volatility
        )
        
        # 統合指標データ
        integrated_indicators = self._create_integrated_indicators(timeframe_analyses)
        
        # 市場状況
        market_conditions = {
            "trend": integrated_trend["direction"],
            "momentum": integrated_momentum["direction"],
            "volatility": integrated_volatility["level"],
            "trend_confidence": integrated_trend["confidence"],
            "momentum_score": integrated_momentum["score"],
            "volatility_score": integrated_volatility["score"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        return EntrySignalModel.create_buy_signal(
            currency_pair=self.currency_pair,
            timestamp=datetime.utcnow(),
            timeframe="MULTI",  # マルチタイムフレーム
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence_score=confidence_score,
            indicators_used=integrated_indicators,
            market_conditions=market_conditions,
        )

    def _create_integrated_sell_signal(
        self,
        integrated_trend: Dict[str, Any],
        integrated_momentum: Dict[str, Any],
        integrated_volatility: Dict[str, Any],
        timeframe_analyses: Dict[str, Dict[str, Any]],
    ) -> Optional[EntrySignalModel]:
        """
        統合売りシグナル作成

        Args:
            integrated_trend: 統合トレンド分析
            integrated_momentum: 統合モメンタム分析
            integrated_volatility: 統合ボラティリティ分析
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Optional[EntrySignalModel]: 売りシグナル
        """
        # 現在価格を取得（簡易実装）
        current_price = 150.000
        
        # ストップロスと利益確定を計算
        stop_loss = current_price * 1.005  # 0.5%上
        take_profit = current_price * 0.985  # 1.5%下
        
        # 統合信頼度スコア計算
        confidence_score = self._calculate_integrated_confidence(
            integrated_trend, integrated_momentum, integrated_volatility
        )
        
        # 統合指標データ
        integrated_indicators = self._create_integrated_indicators(timeframe_analyses)
        
        # 市場状況
        market_conditions = {
            "trend": integrated_trend["direction"],
            "momentum": integrated_momentum["direction"],
            "volatility": integrated_volatility["level"],
            "trend_confidence": integrated_trend["confidence"],
            "momentum_score": integrated_momentum["score"],
            "volatility_score": integrated_volatility["score"],
            "timestamp": datetime.utcnow().isoformat(),
        }

        return EntrySignalModel.create_sell_signal(
            currency_pair=self.currency_pair,
            timestamp=datetime.utcnow(),
            timeframe="MULTI",  # マルチタイムフレーム
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence_score=confidence_score,
            indicators_used=integrated_indicators,
            market_conditions=market_conditions,
        )

    def _calculate_integrated_confidence(
        self,
        integrated_trend: Dict[str, Any],
        integrated_momentum: Dict[str, Any],
        integrated_volatility: Dict[str, Any],
    ) -> int:
        """
        統合信頼度スコア計算

        Args:
            integrated_trend: 統合トレンド分析
            integrated_momentum: 統合モメンタム分析
            integrated_volatility: 統合ボラティリティ分析

        Returns:
            int: 統合信頼度スコア（0-100）
        """
        # トレンド信頼度（40%）
        trend_score = integrated_trend["confidence"] * 0.4
        
        # モメンタム信頼度（35%）
        momentum_score = min(100, (integrated_momentum["score"] + 100) / 2) * 0.35
        
        # ボラティリティ信頼度（25%）
        volatility_score = (100 - integrated_volatility["score"]) * 0.25  # 低ボラティリティほど高スコア
        
        total_score = trend_score + momentum_score + volatility_score
        
        return min(100, max(0, int(total_score)))

    def _create_integrated_indicators(self, timeframe_analyses: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        統合指標データ作成

        Args:
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            Dict[str, Any]: 統合指標データ
        """
        integrated_indicators = {}
        
        for timeframe, analysis in timeframe_analyses.items():
            prefix = f"{timeframe}_"
            indicators = analysis["indicators"]
            
            for key, value in indicators.items():
                integrated_indicators[f"{prefix}{key}"] = value
        
        return integrated_indicators

    def _check_timeframe_consistency(
        self, signal: EntrySignalModel, timeframe_analyses: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        タイムフレーム一貫性チェック

        Args:
            signal: エントリーシグナル
            timeframe_analyses: タイムフレーム分析結果

        Returns:
            bool: 一貫性があるかどうか
        """
        # 上位3つのタイムフレームで一貫性をチェック
        key_timeframes = ["M5", "M15", "H1"]
        consistent_count = 0
        
        for timeframe in key_timeframes:
            if timeframe in timeframe_analyses:
                analysis = timeframe_analyses[timeframe]
                trend = analysis["trend"]["direction"]
                momentum = analysis["momentum"]["direction"]
                
                if signal.signal_type == "BUY":
                    if trend == "uptrend" and momentum == "bullish":
                        consistent_count += 1
                elif signal.signal_type == "SELL":
                    if trend == "downtrend" and momentum == "bearish":
                        consistent_count += 1
        
        # 2つ以上のタイムフレームで一貫性がある場合にTrue
        return consistent_count >= 2

    def _calculate_trend_confidence(self, indicators: Dict[str, Any], direction: str) -> int:
        """
        トレンド信頼度計算

        Args:
            indicators: 指標データ
            direction: トレンド方向

        Returns:
            int: 信頼度スコア（0-100）
        """
        score = 50  # ベーススコア
        
        # 移動平均の傾き
        sma_20 = indicators.get("SMA_20")
        sma_50 = indicators.get("SMA_50")
        
        if sma_20 and sma_50:
            if direction == "uptrend" and sma_20 > sma_50:
                score += 20
            elif direction == "downtrend" and sma_20 < sma_50:
                score += 20
        
        # 価格位置
        current_price = indicators.get("close")
        if current_price and sma_20:
            if direction == "uptrend" and current_price > sma_20:
                score += 15
            elif direction == "downtrend" and current_price < sma_20:
                score += 15
        
        # MACD
        macd_hist = indicators.get("MACD_histogram", 0)
        if direction == "uptrend" and macd_hist > 0:
            score += 15
        elif direction == "downtrend" and macd_hist < 0:
            score += 15
        
        return min(score, 100)

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
            latest_timestamp_query = select(TechnicalIndicatorModel.timestamp).where(
                TechnicalIndicatorModel.currency_pair == self.currency_pair,
                TechnicalIndicatorModel.timeframe == timeframe,
            ).order_by(TechnicalIndicatorModel.timestamp.desc()).limit(1)

            result = await self.db_session.execute(latest_timestamp_query)
            latest_timestamp = result.scalar()

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
            print(f"Error getting latest indicators for {timeframe}: {e}")
            return {}

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
            print(f"Error saving multi-timeframe signals: {e}")
            await self.db_session.rollback()
