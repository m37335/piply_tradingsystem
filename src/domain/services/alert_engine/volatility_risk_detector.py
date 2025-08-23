"""
ボラティリティリスク検出器

プロトレーダー向け為替アラートシステム用のボラティリティリスク検出器
設計書参照: /app/note/2025-01-15_アラートシステム_プロトレーダー向け為替アラートシステム設計書.md
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.risk_alert_model import RiskAlertModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)


class VolatilityRiskDetector:
    """
    ボラティリティリスク検出器

    責任:
    - ATRベースのボラティリティ急増検出
    - 価格変動の異常検出
    - 出来高スパイク検出
    - リスクレベル判定

    特徴:
    - 複数指標組み合わせ
    - 動的閾値調整
    - 重要度レベル判定
    - 推奨アクション生成
    """

    def __init__(self, db_session: AsyncSession):
        """
        初期化

        Args:
            db_session: データベースセッション
        """
        self.db_session = db_session
        self.currency_pair = "USD/JPY"

    async def detect_volatility_risk(
        self, timeframe: str = "M5"
    ) -> List[RiskAlertModel]:
        """
        ボラティリティリスク検出

        アラート条件:
        - ATRが過去20期間平均の2倍以上
        - 価格変動が過去24時間で3%以上
        - 出来高が過去平均の3倍以上

        Args:
            timeframe: タイムフレーム

        Returns:
            List[RiskAlertModel]: 検出されたリスクアラート
        """
        alerts = []

        # ATRデータを取得
        atr_data = await self._get_atr_data(timeframe, periods=20)
        if len(atr_data) < 20:
            return alerts

        current_atr = atr_data[-1]
        avg_atr = sum(atr_data[:-1]) / len(atr_data[:-1])

        # 価格変動データを取得
        price_change_24h = await self._get_price_change_24h()
        volume_ratio = await self._get_volume_ratio()

        # ボラティリティ急増チェック
        if self._check_volatility_spike(
            current_atr, avg_atr, price_change_24h, volume_ratio
        ):
            severity = self._determine_severity(current_atr, avg_atr)

            alert = RiskAlertModel.create_volatility_spike_alert(
                currency_pair=self.currency_pair,
                timestamp=datetime.utcnow(),
                timeframe=timeframe,
                current_atr=current_atr,
                avg_atr=avg_atr,
                price_change_24h=price_change_24h,
                volume_ratio=volume_ratio,
                severity=severity,
            )
            alerts.append(alert)

        return alerts

    def _check_volatility_spike(
        self,
        current_atr: float,
        avg_atr: float,
        price_change_24h: float,
        volume_ratio: float,
    ) -> bool:
        """
        ボラティリティ急増チェック

        Args:
            current_atr: 現在のATR
            avg_atr: 平均ATR
            price_change_24h: 24時間価格変動
            volume_ratio: 出来高比率

        Returns:
            bool: ボラティリティ急増かどうか
        """
        return (
            current_atr > avg_atr * 2.0  # ATR急増
            or abs(price_change_24h) > 3.0  # 価格変動急増
            or volume_ratio > 3.0  # 出来高急増
        )

    def _determine_severity(self, current_atr: float, avg_atr: float) -> str:
        """
        重要度レベル判定

        Args:
            current_atr: 現在のATR
            avg_atr: 平均ATR

        Returns:
            str: 重要度レベル
        """
        ratio = current_atr / avg_atr if avg_atr > 0 else 1.0

        if ratio > 4.0:
            return "CRITICAL"
        elif ratio > 3.0:
            return "HIGH"
        elif ratio > 2.0:
            return "MEDIUM"
        else:
            return "LOW"

    async def _get_atr_data(self, timeframe: str, periods: int = 20) -> List[float]:
        """
        ATRデータを取得

        Args:
            timeframe: タイムフレーム
            periods: 取得期間数

        Returns:
            List[float]: ATRデータリスト
        """
        try:
            # 最新のATRデータを取得
            atr_query = (
                select(TechnicalIndicatorModel.value)
                .where(
                    TechnicalIndicatorModel.currency_pair == self.currency_pair,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.indicator_type == "ATR",
                )
                .order_by(TechnicalIndicatorModel.timestamp.desc())
                .limit(periods)
            )

            result = await self.db_session.execute(atr_query)
            atr_values = result.scalars().all() if result else []

            return [float(value) for value in atr_values]

        except Exception as e:
            print(f"Error getting ATR data: {e}")
            return []

    async def _get_price_change_24h(self) -> float:
        """
        24時間価格変動を取得

        Returns:
            float: 24時間価格変動率（%）
        """
        try:
            # 24時間前の価格と現在価格を取得（簡易実装）
            # 実際の実装では価格データテーブルから取得
            current_price = 150.000
            price_24h_ago = 149.500

            if price_24h_ago > 0:
                return ((current_price - price_24h_ago) / price_24h_ago) * 100
            return 0.0

        except Exception as e:
            print(f"Error getting price change: {e}")
            return 0.0

    async def _get_volume_ratio(self) -> float:
        """
        出来高比率を取得

        Returns:
            float: 出来高比率
        """
        try:
            # 現在の出来高と平均出来高を取得（簡易実装）
            # 実際の実装では出来高データテーブルから取得
            current_volume = 1000000
            avg_volume = 500000

            if avg_volume > 0:
                return current_volume / avg_volume
            return 1.0

        except Exception as e:
            print(f"Error getting volume ratio: {e}")
            return 1.0

    async def save_alerts(self, alerts: List[RiskAlertModel]) -> None:
        """
        アラートをデータベースに保存

        Args:
            alerts: 保存するアラートリスト
        """
        try:
            for alert in alerts:
                if alert.validate():
                    self.db_session.add(alert)
            await self.db_session.commit()
        except Exception as e:
            print(f"Error saving alerts: {e}")
            await self.db_session.rollback()

    async def get_volatility_statistics(
        self, timeframe: str = "M5", days: int = 7
    ) -> Dict[str, Any]:
        """
        ボラティリティ統計を取得

        Args:
            timeframe: タイムフレーム
            days: 取得日数

        Returns:
            Dict[str, Any]: ボラティリティ統計
        """
        try:
            # 指定期間のATRデータを取得
            start_date = datetime.utcnow() - timedelta(days=days)

            atr_query = (
                select(TechnicalIndicatorModel.value)
                .where(
                    TechnicalIndicatorModel.currency_pair == self.currency_pair,
                    TechnicalIndicatorModel.timeframe == timeframe,
                    TechnicalIndicatorModel.indicator_type == "ATR",
                    TechnicalIndicatorModel.timestamp >= start_date,
                )
                .order_by(TechnicalIndicatorModel.timestamp)
            )

            result = await self.db_session.execute(atr_query)
            atr_values = [float(value) for value in result.scalars().all()]

            if not atr_values:
                return {}

            return {
                "min_atr": min(atr_values),
                "max_atr": max(atr_values),
                "avg_atr": sum(atr_values) / len(atr_values),
                "current_atr": atr_values[-1] if atr_values else 0,
                "volatility_trend": self._calculate_volatility_trend(atr_values),
                "spike_count": self._count_volatility_spikes(atr_values),
            }

        except Exception as e:
            print(f"Error getting volatility statistics: {e}")
            return {}

    def _calculate_volatility_trend(self, atr_values: List[float]) -> str:
        """
        ボラティリティトレンド計算

        Args:
            atr_values: ATR値リスト

        Returns:
            str: トレンド方向
        """
        if len(atr_values) < 2:
            return "stable"

        # 最近の値と過去の値を比較
        recent_avg = sum(atr_values[-5:]) / min(5, len(atr_values))
        older_avg = sum(atr_values[:-5]) / max(1, len(atr_values) - 5)

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        else:
            return "stable"

    def _count_volatility_spikes(self, atr_values: List[float]) -> int:
        """
        ボラティリティスパイク数をカウント

        Args:
            atr_values: ATR値リスト

        Returns:
            int: スパイク数
        """
        if len(atr_values) < 20:
            return 0

        spike_count = 0
        for i in range(20, len(atr_values)):
            # 過去20期間の平均
            avg_20 = sum(atr_values[i - 20 : i]) / 20
            current = atr_values[i]

            # 2倍以上の急増をスパイクとしてカウント
            if current > avg_20 * 2.0:
                spike_count += 1

        return spike_count
