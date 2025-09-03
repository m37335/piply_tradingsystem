"""
Exchange Rate Domain Service
為替レートドメインサービス

設計書参照:
- 詳細内部設計_20250809.md

ドメインロジックを集約するサービス
エンティティ間のビジネスルールやドメイン固有の計算を担当
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from ...utils.logging_config import get_domain_logger
from ..entities.exchange_rate import ExchangeRateEntity
from ..repositories.exchange_rate_repository import ExchangeRateRepository
from ..value_objects.currency import CurrencyPair, ExchangeRate, Price

logger = get_domain_logger()


class ExchangeRateService:
    """
    為替レートドメインサービス

    責任:
    - 為替レート間の関係性の管理
    - ドメイン固有の計算ロジック
    - ビジネスルールの適用
    - データ整合性の保証
    """

    def __init__(self, exchange_rate_repository: ExchangeRateRepository):
        self._repository = exchange_rate_repository

    async def calculate_cross_rate(
        self, base_pair: CurrencyPair, quote_pair: CurrencyPair
    ) -> Optional[ExchangeRate]:
        """
        クロスレートの計算

        例: USD/JPY と EUR/USD から EUR/JPY を計算

        Args:
            base_pair: 基準通貨ペア
            quote_pair: 相手通貨ペア

        Returns:
            Optional[ExchangeRate]: 計算されたクロスレート
        """
        logger.debug(f"Calculating cross rate from {base_pair} and {quote_pair}")

        # 最新レートを取得
        base_rate = await self._repository.find_latest_by_currency_pair(base_pair)
        quote_rate = await self._repository.find_latest_by_currency_pair(quote_pair)

        if not base_rate or not quote_rate:
            logger.warning("Cannot calculate cross rate: missing rate data")
            return None

        # データが古すぎる場合は計算しない
        if base_rate.is_stale() or quote_rate.is_stale():
            logger.warning("Cannot calculate cross rate: stale data")
            return None

        # クロスレート計算ロジック
        try:
            if base_pair.quote == quote_pair.base:
                # 直接計算: USD/JPY * EUR/USD = EUR/JPY
                cross_rate = Price(base_rate.rate.value * quote_rate.rate.value)
                cross_pair = CurrencyPair(quote_pair.quote, base_pair.quote)
            elif base_pair.base == quote_pair.quote:
                # 逆算: USD/JPY / USD/EUR = EUR/JPY
                cross_rate = Price(base_rate.rate.value / quote_rate.rate.value)
                cross_pair = CurrencyPair(quote_pair.base, base_pair.quote)
            else:
                logger.warning(
                    f"Cannot calculate cross rate: no common currency between {base_pair} and {quote_pair}"
                )
                return None

            logger.info(f"Calculated cross rate: {cross_pair} = {cross_rate}")
            return ExchangeRate(cross_pair, cross_rate)

        except Exception as e:
            logger.error(f"Error calculating cross rate: {e}")
            return None

    async def detect_arbitrage_opportunity(
        self, currency_pairs: List[CurrencyPair], threshold_percentage: float = 0.1
    ) -> List[Dict[str, any]]:
        """
        アービトラージ機会の検出

        Args:
            currency_pairs: チェックする通貨ペアのリスト
            threshold_percentage: 機会とみなす最小利益率

        Returns:
            List[Dict]: 検出されたアービトラージ機会のリスト
        """
        logger.debug(
            f"Detecting arbitrage opportunities for {len(currency_pairs)} pairs"
        )

        opportunities = []

        # 全ての通貨ペアの最新レートを取得
        latest_rates = await self._repository.find_latest_rates_for_pairs(
            currency_pairs
        )

        # 三角アービトラージの検出
        for i, pair1 in enumerate(currency_pairs):
            for j, pair2 in enumerate(currency_pairs[i + 1 :], i + 1):
                for k, pair3 in enumerate(currency_pairs[j + 1 :], j + 1):
                    opportunity = await self._check_triangular_arbitrage(
                        pair1, pair2, pair3, latest_rates, threshold_percentage
                    )
                    if opportunity:
                        opportunities.append(opportunity)

        logger.info(f"Detected {len(opportunities)} arbitrage opportunities")
        return opportunities

    async def _check_triangular_arbitrage(
        self,
        pair1: CurrencyPair,
        pair2: CurrencyPair,
        pair3: CurrencyPair,
        rates: Dict[str, ExchangeRateEntity],
        threshold: float,
    ) -> Optional[Dict[str, any]]:
        """
        三角アービトラージのチェック
        """
        # 実装の簡略化のため、基本ロジックのみ
        try:
            rate1 = rates.get(str(pair1))
            rate2 = rates.get(str(pair2))
            rate3 = rates.get(str(pair3))

            if not all([rate1, rate2, rate3]):
                return None

            # 簡単な三角アービトラージ計算
            # 実際の実装では、通貨の組み合わせを詳細に分析する必要がある
            implied_rate = rate1.rate.value * rate2.rate.value
            actual_rate = rate3.rate.value

            profit_percentage = float(
                abs(implied_rate - actual_rate) / actual_rate * 100
            )

            if profit_percentage > threshold:
                return {
                    "type": "triangular_arbitrage",
                    "pairs": [str(pair1), str(pair2), str(pair3)],
                    "profit_percentage": profit_percentage,
                    "timestamp": datetime.utcnow(),
                }

        except Exception as e:
            logger.error(f"Error checking triangular arbitrage: {e}")

        return None

    async def calculate_volatility(
        self, currency_pair: CurrencyPair, period_hours: int = 24
    ) -> Optional[float]:
        """
        ボラティリティの計算

        Args:
            currency_pair: 計算対象の通貨ペア
            period_hours: 計算期間（時間）

        Returns:
            Optional[float]: ボラティリティ（標準偏差）
        """
        logger.debug(
            f"Calculating volatility for {currency_pair} over {period_hours} hours"
        )

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=period_hours)

        rates = await self._repository.find_by_time_range(
            currency_pair, start_time, end_time
        )

        if len(rates) < 2:
            logger.warning("Insufficient data to calculate volatility")
            return None

        # 価格変化率の計算
        price_changes = []
        for i in range(1, len(rates)):
            prev_rate = rates[i - 1].rate.value
            curr_rate = rates[i].rate.value

            if prev_rate > 0:
                change = float((curr_rate - prev_rate) / prev_rate)
                price_changes.append(change)

        if not price_changes:
            return None

        # 標準偏差の計算
        mean_change = sum(price_changes) / len(price_changes)
        variance = sum((x - mean_change) ** 2 for x in price_changes) / len(
            price_changes
        )
        volatility = variance**0.5

        logger.info(f"Calculated volatility for {currency_pair}: {volatility:.6f}")
        return volatility

    async def validate_rate_consistency(
        self, rate: ExchangeRateEntity, tolerance_percentage: float = 5.0
    ) -> bool:
        """
        為替レートの整合性チェック

        Args:
            rate: チェックする為替レート
            tolerance_percentage: 許容誤差率

        Returns:
            bool: 整合性がある場合True
        """
        logger.debug(f"Validating rate consistency for {rate.currency_pair}")

        # 最近の類似レートとの比較
        recent_rates = await self._repository.find_by_currency_pair(
            rate.currency_pair, limit=10
        )

        if not recent_rates:
            logger.info("No recent rates for comparison, accepting new rate")
            return True

        # 最新レートとの差異をチェック
        latest_rate = recent_rates[0]
        if latest_rate.rate.value > 0:
            diff_percentage = float(
                abs(rate.rate.value - latest_rate.rate.value)
                / latest_rate.rate.value
                * 100
            )

            if diff_percentage > tolerance_percentage:
                logger.warning(
                    f"Rate consistency check failed: {diff_percentage:.2f}% difference "
                    f"exceeds tolerance of {tolerance_percentage}%"
                )
                return False

        logger.debug("Rate consistency check passed")
        return True

    async def get_rate_trend(
        self, currency_pair: CurrencyPair, period_hours: int = 24
    ) -> Dict[str, any]:
        """
        為替レートのトレンド分析

        Args:
            currency_pair: 分析対象の通貨ペア
            period_hours: 分析期間（時間）

        Returns:
            Dict[str, any]: トレンド分析結果
        """
        logger.debug(f"Analyzing trend for {currency_pair} over {period_hours} hours")

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=period_hours)

        rates = await self._repository.find_by_time_range(
            currency_pair, start_time, end_time
        )

        if len(rates) < 2:
            return {"trend": "insufficient_data", "confidence": 0.0}

        # 簡単なトレンド分析（線形近似）
        start_rate = rates[-1].rate.value  # 最も古いレート
        end_rate = rates[0].rate.value  # 最新レート

        change_percentage = float((end_rate - start_rate) / start_rate * 100)

        if change_percentage > 0.5:
            trend = "upward"
        elif change_percentage < -0.5:
            trend = "downward"
        else:
            trend = "sideways"

        # 信頼度の計算（データ点数に基づく簡易計算）
        confidence = min(len(rates) / 100.0, 1.0)

        result = {
            "trend": trend,
            "change_percentage": change_percentage,
            "confidence": confidence,
            "data_points": len(rates),
            "period_hours": period_hours,
        }

        logger.info(
            f"Trend analysis for {currency_pair}: {trend} ({change_percentage:.2f}%)"
        )
        return result
