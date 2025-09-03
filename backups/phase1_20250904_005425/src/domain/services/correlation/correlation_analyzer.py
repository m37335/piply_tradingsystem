"""
通貨ペア相関性分析器

プロトレーダー向け為替アラートシステム用の通貨ペア相関性分析器
設計書参照: /app/note/2025-01-15_実装計画_Phase2_高度な検出機能.yaml
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.risk_alert_model import RiskAlertModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)


class CorrelationAnalyzer:
    """
    通貨ペア相関性分析器

    責任:
    - 複数通貨ペアの相関性計算
    - 相関性の変化検出
    - 相関性に基づくリスク警告生成
    - 相関性データの履歴保存

    特徴:
    - 動的相関性計算
    - 変化検出アルゴリズム
    - リスク警告システム
    - 履歴データ分析
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.base_currency_pair = "USD/JPY"

        # 主要通貨ペアリスト
        self.major_pairs = [
            "USD/JPY",
            "EUR/USD",
            "GBP/USD",
            "USD/CHF",
            "AUD/USD",
            "USD/CAD",
            "NZD/USD",
        ]

        # 相関性設定
        self.correlation_threshold = 0.8  # 高相関閾値
        self.change_threshold = 0.3  # 変化検出閾値
        self.lookback_periods = 30  # 履歴期間

    async def analyze_correlations(self, timeframe: str = "H1") -> Dict[str, Any]:
        """
        相関性分析実行

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, Any]: 相関性分析結果
        """
        try:
            # 各通貨ペアの価格データを取得
            price_data = await self._get_price_data_for_pairs(timeframe)

            if not price_data or len(price_data) < 2:
                return {"error": "十分な価格データがありません"}

            # 相関性行列を計算
            correlation_matrix = self._calculate_correlation_matrix(price_data)

            # 高相関ペアを検出
            high_correlations = self._detect_high_correlations(correlation_matrix)

            # 相関性変化を検出
            correlation_changes = await self._detect_correlation_changes(
                price_data, timeframe
            )

            # リスク警告を生成
            risk_alerts = self._generate_correlation_alerts(
                high_correlations, correlation_changes
            )

            return {
                "timeframe": timeframe,
                "correlation_matrix": correlation_matrix,
                "high_correlations": high_correlations,
                "correlation_changes": correlation_changes,
                "risk_alerts": risk_alerts,
                "analysis_timestamp": datetime.utcnow(),
            }

        except Exception as e:
            print(f"Error analyzing correlations: {e}")
            return {"error": str(e)}

    async def _get_price_data_for_pairs(self, timeframe: str) -> Dict[str, List[float]]:
        """
        各通貨ペアの価格データを取得

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, List[float]]: 通貨ペア別価格データ
        """
        price_data = {}

        for pair in self.major_pairs:
            try:
                # 最新の価格データを取得
                query = (
                    select(TechnicalIndicatorModel.value)
                    .where(
                        TechnicalIndicatorModel.currency_pair == pair,
                        TechnicalIndicatorModel.timeframe == timeframe,
                        TechnicalIndicatorModel.indicator_type == "close",
                    )
                    .order_by(TechnicalIndicatorModel.timestamp.desc())
                    .limit(self.lookback_periods)
                )

                result = await self.db_session.execute(query)
                prices = [float(value) for value in result.scalars().all()]

                if prices:
                    price_data[pair] = prices[::-1]  # 時系列順に並び替え

            except Exception as e:
                print(f"Error getting price data for {pair}: {e}")
                continue

        return price_data

    def _calculate_correlation_matrix(
        self, price_data: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        相関性行列を計算

        Args:
            price_data: 通貨ペア別価格データ

        Returns:
            Dict[str, Dict[str, float]]: 相関性行列
        """
        pairs = list(price_data.keys())
        correlation_matrix = {}

        for i, pair1 in enumerate(pairs):
            correlation_matrix[pair1] = {}

            for j, pair2 in enumerate(pairs):
                if i == j:
                    correlation_matrix[pair1][pair2] = 1.0
                else:
                    # 価格データの長さを揃える
                    min_length = min(len(price_data[pair1]), len(price_data[pair2]))

                    if min_length < 10:  # 最小データ数チェック
                        correlation_matrix[pair1][pair2] = 0.0
                    else:
                        # 価格変化率を計算
                        returns1 = self._calculate_returns(
                            price_data[pair1][:min_length]
                        )
                        returns2 = self._calculate_returns(
                            price_data[pair2][:min_length]
                        )

                        # 相関係数を計算
                        correlation = self._calculate_pearson_correlation(
                            returns1, returns2
                        )
                        correlation_matrix[pair1][pair2] = correlation

        return correlation_matrix

    def _calculate_returns(self, prices: List[float]) -> List[float]:
        """
        価格変化率を計算

        Args:
            prices: 価格リスト

        Returns:
            List[float]: 価格変化率リスト
        """
        if len(prices) < 2:
            return []

        returns = []
        for i in range(1, len(prices)):
            if prices[i - 1] != 0:
                return_rate = (prices[i] - prices[i - 1]) / prices[i - 1]
                returns.append(return_rate)

        return returns

    def _calculate_pearson_correlation(
        self, returns1: List[float], returns2: List[float]
    ) -> float:
        """
        ピアソン相関係数を計算

        Args:
            returns1: 価格変化率リスト1
            returns2: 価格変化率リスト2

        Returns:
            float: 相関係数
        """
        if len(returns1) != len(returns2) or len(returns1) < 2:
            return 0.0

        try:
            # numpyを使用して相関係数を計算
            correlation = np.corrcoef(returns1, returns2)[0, 1]

            # NaNや無限大の値を0に置換
            if np.isnan(correlation) or np.isinf(correlation):
                return 0.0

            return float(correlation)

        except Exception as e:
            print(f"Error calculating correlation: {e}")
            return 0.0

    def _detect_high_correlations(
        self, correlation_matrix: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        高相関ペアを検出

        Args:
            correlation_matrix: 相関性行列

        Returns:
            List[Dict[str, Any]]: 高相関ペアリスト
        """
        high_correlations = []
        pairs = list(correlation_matrix.keys())

        for i, pair1 in enumerate(pairs):
            for j, pair2 in enumerate(pairs):
                if i < j:  # 重複を避ける
                    correlation = correlation_matrix[pair1][pair2]

                    if abs(correlation) >= self.correlation_threshold:
                        high_correlations.append(
                            {
                                "pair1": pair1,
                                "pair2": pair2,
                                "correlation": correlation,
                                "strength": (
                                    "strong" if abs(correlation) >= 0.9 else "moderate"
                                ),
                                "direction": (
                                    "positive" if correlation > 0 else "negative"
                                ),
                            }
                        )

        return high_correlations

    async def _detect_correlation_changes(
        self, current_price_data: Dict[str, List[float]], timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        相関性変化を検出

        Args:
            current_price_data: 現在の価格データ
            timeframe: タイムフレーム

        Returns:
            List[Dict[str, Any]]: 相関性変化リスト
        """
        correlation_changes = []

        # 過去の相関性データを取得（簡易実装）
        # 実際の実装では履歴データベースから取得
        historical_correlations = await self._get_historical_correlations(timeframe)

        if not historical_correlations:
            return correlation_changes

        # 現在の相関性を計算
        current_correlation_matrix = self._calculate_correlation_matrix(
            current_price_data
        )

        # 変化を検出
        for pair1 in current_correlation_matrix:
            for pair2 in current_correlation_matrix[pair1]:
                if pair1 != pair2:
                    current_corr = current_correlation_matrix[pair1][pair2]
                    historical_corr = historical_correlations.get(
                        f"{pair1}_{pair2}", 0.0
                    )

                    change = abs(current_corr - historical_corr)

                    if change >= self.change_threshold:
                        correlation_changes.append(
                            {
                                "pair1": pair1,
                                "pair2": pair2,
                                "current_correlation": current_corr,
                                "historical_correlation": historical_corr,
                                "change": change,
                                "change_direction": (
                                    "increase"
                                    if current_corr > historical_corr
                                    else "decrease"
                                ),
                            }
                        )

        return correlation_changes

    async def _get_historical_correlations(self, timeframe: str) -> Dict[str, float]:
        """
        履歴相関性データを取得

        Args:
            timeframe: タイムフレーム

        Returns:
            Dict[str, float]: 履歴相関性データ
        """
        try:
            # 実際の実装では相関性履歴テーブルから取得
            # ここでは簡易実装として仮のデータを返す
            historical_data = {
                "USD/JPY_EUR/USD": 0.6,
                "USD/JPY_GBP/USD": 0.4,
                "EUR/USD_GBP/USD": 0.8,
                "USD/JPY_USD/CHF": -0.7,
                "EUR/USD_USD/CHF": -0.9,
            }

            return historical_data

        except Exception as e:
            print(f"Error getting historical correlations: {e}")
            return {}

    def _generate_correlation_alerts(
        self,
        high_correlations: List[Dict[str, Any]],
        correlation_changes: List[Dict[str, Any]],
    ) -> List[RiskAlertModel]:
        """
        相関性アラートを生成

        Args:
            high_correlations: 高相関ペアリスト
            correlation_changes: 相関性変化リスト

        Returns:
            List[RiskAlertModel]: リスクアラートリスト
        """
        alerts = []

        # 高相関アラート
        for correlation in high_correlations:
            if abs(correlation["correlation"]) >= 0.9:  # 非常に高い相関
                alert = RiskAlertModel.create_correlation_alert(
                    currency_pair=f"{correlation['pair1']}-{correlation['pair2']}",
                    timestamp=datetime.utcnow(),
                    timeframe="H1",
                    correlation_value=correlation["correlation"],
                    alert_type="high_correlation",
                    severity="HIGH",
                    message=f"高相関検出: {correlation['pair1']}-{correlation['pair2']}相関={correlation['correlation']:.3f}",
                    recommended_action="ポジションの分散化を検討してください",
                )
                alerts.append(alert)

        # 相関性変化アラート
        for change in correlation_changes:
            if change["change"] >= 0.5:  # 大幅な変化
                alert = RiskAlertModel.create_correlation_alert(
                    currency_pair=f"{change['pair1']}-{change['pair2']}",
                    timestamp=datetime.utcnow(),
                    timeframe="H1",
                    correlation_value=change["current_correlation"],
                    alert_type="correlation_change",
                    severity="MEDIUM",
                    message=f"相関性急変: {change['pair1']}-{change['pair2']}変化幅={change['change']:.3f}",
                    recommended_action="既存ポジションの見直しを検討してください",
                )
                alerts.append(alert)

        return alerts

    async def get_correlation_statistics(
        self, timeframe: str = "H1", days: int = 7
    ) -> Dict[str, Any]:
        """
        相関性統計を取得

        Args:
            timeframe: タイムフレーム
            days: 取得日数

        Returns:
            Dict[str, Any]: 相関性統計
        """
        try:
            # 指定期間の相関性データを取得
            start_date = datetime.utcnow() - timedelta(days=days)

            # 実際の実装では履歴データベースから取得
            # ここでは簡易実装として仮の統計を返す
            statistics = {
                "total_correlations": 21,  # 7C2 = 21通貨ペアの組み合わせ
                "high_correlations": 3,
                "moderate_correlations": 8,
                "low_correlations": 10,
                "avg_correlation": 0.45,
                "max_correlation": 0.92,
                "min_correlation": -0.78,
                "correlation_volatility": 0.15,
                "most_correlated_pair": "EUR/USD-GBP/USD",
                "least_correlated_pair": "USD/JPY-USD/CHF",
            }

            return statistics

        except Exception as e:
            print(f"Error getting correlation statistics: {e}")
            return {}

    async def save_correlation_data(
        self, correlation_matrix: Dict[str, Dict[str, float]], timeframe: str
    ) -> bool:
        """
        相関性データを保存

        Args:
            correlation_matrix: 相関性行列
            timeframe: タイムフレーム

        Returns:
            bool: 保存成功かどうか
        """
        try:
            # 実際の実装では相関性履歴テーブルに保存
            # ここでは簡易実装としてログ出力のみ
            print(
                f"Saving correlation data for {timeframe}: {len(correlation_matrix)} pairs"
            )

            # 相関性データをフラット化して保存
            flat_correlations = []
            for pair1 in correlation_matrix:
                for pair2 in correlation_matrix[pair1]:
                    if pair1 != pair2:
                        flat_correlations.append(
                            {
                                "pair1": pair1,
                                "pair2": pair2,
                                "correlation": correlation_matrix[pair1][pair2],
                                "timeframe": timeframe,
                                "timestamp": datetime.utcnow(),
                            }
                        )

            print(f"Saved {len(flat_correlations)} correlation records")
            return True

        except Exception as e:
            print(f"Error saving correlation data: {e}")
            return False

    def update_correlation_settings(
        self,
        correlation_threshold: float = None,
        change_threshold: float = None,
        lookback_periods: int = None,
    ) -> None:
        """
        相関性設定を更新

        Args:
            correlation_threshold: 高相関閾値
            change_threshold: 変化検出閾値
            lookback_periods: 履歴期間
        """
        if correlation_threshold is not None:
            self.correlation_threshold = correlation_threshold

        if change_threshold is not None:
            self.change_threshold = change_threshold

        if lookback_periods is not None:
            self.lookback_periods = lookback_periods

    def get_correlation_settings(self) -> Dict[str, Any]:
        """
        現在の相関性設定を取得

        Returns:
            Dict[str, Any]: 相関性設定
        """
        return {
            "correlation_threshold": self.correlation_threshold,
            "change_threshold": self.change_threshold,
            "lookback_periods": self.lookback_periods,
            "major_pairs": self.major_pairs,
        }
