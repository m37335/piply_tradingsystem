"""
サプライズ計算器

経済指標の実際値と予測値の差分（サプライズ）を計算・分析する
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from src.domain.entities import EconomicEvent


class SurpriseCalculator:
    """
    サプライズ計算器

    経済指標のサプライズ（実際値と予測値の差分）を計算し、
    市場影響度を分析する
    """

    def __init__(self, surprise_threshold: float = 0.1):
        """
        初期化

        Args:
            surprise_threshold: サプライズ閾値（デフォルト10%）
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.surprise_threshold = surprise_threshold

        # 統計情報
        self._calculation_count = 0
        self._surprises_found = 0
        self._total_surprise_magnitude = 0.0

    async def calculate_surprise(self, event: EconomicEvent) -> Dict[str, Any]:
        """
        単一イベントのサプライズ計算

        Args:
            event: 経済イベント

        Returns:
            Dict[str, Any]: サプライズ計算結果
        """
        try:
            self._calculation_count += 1

            surprise_data = {
                "event_id": event.event_id,
                "event_name": event.event_name,
                "country": event.country,
                "importance": event.importance.value,
                "actual_value": (
                    float(event.actual_value) if event.actual_value else None
                ),
                "forecast_value": (
                    float(event.forecast_value) if event.forecast_value else None
                ),
                "previous_value": (
                    float(event.previous_value) if event.previous_value else None
                ),
                "surprise_amount": None,
                "surprise_percentage": None,
                "surprise_magnitude": "none",
                "market_impact": "low",
                "calculated_at": datetime.utcnow().isoformat(),
            }

            # サプライズの計算
            if event.actual_value is not None and event.forecast_value is not None:
                surprise_amount = event.actual_value - event.forecast_value
                surprise_data["surprise_amount"] = float(surprise_amount)

                # パーセンテージ計算
                if event.forecast_value != 0:
                    surprise_percentage = (
                        float(surprise_amount) / float(event.forecast_value)
                    ) * 100
                    surprise_data["surprise_percentage"] = surprise_percentage

                    # サプライズの分類
                    surprise_data["surprise_magnitude"] = (
                        self._classify_surprise_magnitude(abs(surprise_percentage))
                    )

                    # 市場影響度の推定
                    surprise_data["market_impact"] = await self._estimate_market_impact(
                        event, surprise_percentage
                    )

                    # 統計更新
                    if abs(surprise_percentage) >= (self.surprise_threshold * 100):
                        self._surprises_found += 1
                        self._total_surprise_magnitude += abs(surprise_percentage)

            # 前回値との比較
            if event.actual_value is not None and event.previous_value is not None:
                trend_change = event.actual_value - event.previous_value
                surprise_data["trend_change"] = float(trend_change)

                if event.previous_value != 0:
                    trend_percentage = (
                        float(trend_change) / float(event.previous_value)
                    ) * 100
                    surprise_data["trend_percentage"] = trend_percentage

            return surprise_data

        except Exception as e:
            self.logger.error(f"サプライズ計算エラー: {e}")
            return {
                "event_id": event.event_id,
                "error": str(e),
                "surprise_magnitude": "error",
                "market_impact": "unknown",
            }

    async def calculate_bulk_surprises(
        self, events: List[EconomicEvent]
    ) -> Dict[str, Any]:
        """
        複数イベントのサプライズ一括計算

        Args:
            events: 経済イベントリスト

        Returns:
            Dict[str, Any]: 一括計算結果
        """
        try:
            self.logger.info(f"一括サプライズ計算開始: {len(events)}件")

            surprises = []
            significant_surprises = []
            country_surprises = {}
            category_surprises = {}

            for event in events:
                surprise_data = await self.calculate_surprise(event)
                surprises.append(surprise_data)

                # 有意なサプライズの抽出
                if self._is_significant_surprise(surprise_data):
                    significant_surprises.append(surprise_data)

                # 国別集計
                country = event.country
                if country not in country_surprises:
                    country_surprises[country] = {"count": 0, "avg_surprise": 0}
                country_surprises[country]["count"] += 1

                surprise_pct = surprise_data.get("surprise_percentage", 0) or 0
                country_surprises[country]["avg_surprise"] += abs(surprise_pct)

                # カテゴリ別集計
                category = event.category or "Unknown"
                if category not in category_surprises:
                    category_surprises[category] = {"count": 0, "avg_surprise": 0}
                category_surprises[category]["count"] += 1
                category_surprises[category]["avg_surprise"] += abs(surprise_pct)

            # 平均値の計算
            for country_data in country_surprises.values():
                if country_data["count"] > 0:
                    country_data["avg_surprise"] /= country_data["count"]

            for category_data in category_surprises.values():
                if category_data["count"] > 0:
                    category_data["avg_surprise"] /= category_data["count"]

            result = {
                "calculation_timestamp": datetime.utcnow().isoformat(),
                "total_events": len(events),
                "total_surprises": len(surprises),
                "significant_surprises": len(significant_surprises),
                "surprises": surprises,
                "significant_surprises_list": significant_surprises,
                "country_analysis": country_surprises,
                "category_analysis": category_surprises,
                "summary": await self._generate_surprise_summary(surprises),
            }

            self.logger.info(
                f"一括サプライズ計算完了: {len(significant_surprises)}件の有意なサプライズ"
            )

            return result

        except Exception as e:
            self.logger.error(f"一括サプライズ計算エラー: {e}")
            return {
                "calculation_timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "surprises": [],
                "significant_surprises_list": [],
                "country_analysis": {},
                "category_analysis": {},
                "summary": {},
            }

    async def analyze_surprise_patterns(
        self, surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        サプライズパターンの分析

        Args:
            surprises: サプライズデータのリスト

        Returns:
            Dict[str, Any]: パターン分析結果
        """
        try:
            pattern_analysis = {
                "total_analyzed": len(surprises),
                "direction_analysis": {"positive": 0, "negative": 0, "neutral": 0},
                "magnitude_distribution": {
                    "small": 0,
                    "medium": 0,
                    "large": 0,
                    "extreme": 0,
                },
                "market_impact_distribution": {
                    "low": 0,
                    "medium": 0,
                    "high": 0,
                    "extreme": 0,
                },
                "consistency_analysis": await self._analyze_consistency(surprises),
                "correlation_analysis": await self._analyze_correlations(surprises),
            }

            for surprise in surprises:
                surprise_pct = surprise.get("surprise_percentage", 0)

                # 方向性の分析
                if surprise_pct is None:
                    pattern_analysis["direction_analysis"]["neutral"] += 1
                elif surprise_pct > 0:
                    pattern_analysis["direction_analysis"]["positive"] += 1
                elif surprise_pct < 0:
                    pattern_analysis["direction_analysis"]["negative"] += 1
                else:
                    pattern_analysis["direction_analysis"]["neutral"] += 1

                # 大きさの分析
                magnitude = surprise.get("surprise_magnitude", "none")
                if magnitude in pattern_analysis["magnitude_distribution"]:
                    pattern_analysis["magnitude_distribution"][magnitude] += 1

                # 市場影響の分析
                impact = surprise.get("market_impact", "low")
                if impact in pattern_analysis["market_impact_distribution"]:
                    pattern_analysis["market_impact_distribution"][impact] += 1

            return pattern_analysis

        except Exception as e:
            self.logger.error(f"サプライズパターン分析エラー: {e}")
            return {}

    def _classify_surprise_magnitude(self, abs_surprise_percentage: float) -> str:
        """サプライズの大きさを分類"""
        if abs_surprise_percentage >= 50.0:
            return "extreme"
        elif abs_surprise_percentage >= 20.0:
            return "large"
        elif abs_surprise_percentage >= 10.0:
            return "medium"
        elif abs_surprise_percentage >= 1.0:
            return "small"
        else:
            return "minimal"

    async def _estimate_market_impact(
        self, event: EconomicEvent, surprise_percentage: float
    ) -> str:
        """市場影響度の推定"""
        abs_surprise = abs(surprise_percentage)

        # 重要度による影響度の調整
        importance_multiplier = {"high": 1.5, "medium": 1.0, "low": 0.5}.get(
            event.importance.value, 1.0
        )

        adjusted_impact = abs_surprise * importance_multiplier

        if adjusted_impact >= 30.0:
            return "extreme"
        elif adjusted_impact >= 15.0:
            return "high"
        elif adjusted_impact >= 5.0:
            return "medium"
        else:
            return "low"

    def _is_significant_surprise(self, surprise_data: Dict[str, Any]) -> bool:
        """有意なサプライズかどうかを判定"""
        surprise_pct = surprise_data.get("surprise_percentage")
        if surprise_pct is None:
            return False

        abs_surprise = abs(surprise_pct)
        return abs_surprise >= (self.surprise_threshold * 100)

    async def _generate_surprise_summary(
        self, surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """サプライズサマリーの生成"""
        if not surprises:
            return {}

        valid_surprises = [
            s for s in surprises if s.get("surprise_percentage") is not None
        ]

        if not valid_surprises:
            return {"valid_surprises": 0}

        surprise_values = [abs(s["surprise_percentage"]) for s in valid_surprises]

        return {
            "valid_surprises": len(valid_surprises),
            "avg_surprise_magnitude": sum(surprise_values) / len(surprise_values),
            "max_surprise": max(surprise_values),
            "min_surprise": min(surprise_values),
            "surprise_rate": len(valid_surprises) / len(surprises),
            "significant_surprise_rate": len(
                [
                    s
                    for s in valid_surprises
                    if abs(s["surprise_percentage"]) >= (self.surprise_threshold * 100)
                ]
            )
            / len(valid_surprises),
        }

    async def _analyze_consistency(
        self, surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """一貫性の分析"""
        country_consistency = {}

        for surprise in surprises:
            country = surprise.get("country")
            surprise_pct = surprise.get("surprise_percentage")

            if country and surprise_pct is not None:
                if country not in country_consistency:
                    country_consistency[country] = {
                        "surprises": [],
                        "consistency_score": 0,
                    }
                country_consistency[country]["surprises"].append(surprise_pct)

        # 一貫性スコアの計算
        for country, data in country_consistency.items():
            surprises_list = data["surprises"]
            if len(surprises_list) > 1:
                # 標準偏差による一貫性評価
                mean_surprise = sum(surprises_list) / len(surprises_list)
                variance = sum((x - mean_surprise) ** 2 for x in surprises_list) / len(
                    surprises_list
                )
                std_dev = variance**0.5
                data["consistency_score"] = 1.0 / (
                    1.0 + std_dev
                )  # 低い標準偏差ほど高い一貫性

        return country_consistency

    async def _analyze_correlations(
        self, surprises: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """相関分析"""
        # 簡易的な相関分析
        importance_surprise_correlation = {"high": [], "medium": [], "low": []}

        for surprise in surprises:
            importance = surprise.get("importance")
            surprise_pct = surprise.get("surprise_percentage")

            if importance and surprise_pct is not None:
                importance_surprise_correlation[importance].append(abs(surprise_pct))

        # 重要度別平均サプライズ
        avg_by_importance = {}
        for importance, surprises_list in importance_surprise_correlation.items():
            if surprises_list:
                avg_by_importance[importance] = sum(surprises_list) / len(
                    surprises_list
                )

        return {"importance_surprise_correlation": avg_by_importance}

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        avg_surprise = (
            self._total_surprise_magnitude / max(1, self._surprises_found)
            if self._surprises_found > 0
            else 0
        )

        return {
            "calculator": "SurpriseCalculator",
            "calculation_count": self._calculation_count,
            "surprises_found": self._surprises_found,
            "surprise_threshold": self.surprise_threshold,
            "avg_surprise_magnitude": avg_surprise,
            "surprise_rate": self._surprises_found / max(1, self._calculation_count),
        }

    def health_check(self) -> bool:
        """ヘルスチェック"""
        try:
            # 基本設定の確認
            if self.surprise_threshold < 0:
                self.logger.error("サプライズ閾値が負の値です")
                return False

            return True

        except Exception as e:
            self.logger.error(f"ヘルスチェックエラー: {e}")
            return False

    def set_surprise_threshold(self, threshold: float) -> None:
        """サプライズ閾値の設定"""
        if threshold >= 0:
            self.surprise_threshold = threshold
            self.logger.info(f"サプライズ閾値を更新: {threshold}")
        else:
            self.logger.warning(f"無効なサプライズ閾値: {threshold}")

    def get_surprise_summary(self) -> Dict[str, Any]:
        """サプライズサマリーを取得"""
        return {
            "total_calculations": self._calculation_count,
            "total_surprises": self._surprises_found,
            "surprise_rate": self._surprises_found / max(1, self._calculation_count),
            "current_threshold": self.surprise_threshold,
            "avg_surprise_magnitude": (
                self._total_surprise_magnitude / max(1, self._surprises_found)
            ),
        }
