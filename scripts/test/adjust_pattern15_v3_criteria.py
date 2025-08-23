"""
パターン15 V3 基準値調整と詳細分析スクリプト

検出数を増やすための基準値調整と、検出パターンの詳細分析（角度・価格推移）
"""

import asyncio
import logging
import math
from datetime import datetime
from typing import Dict, List

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector_v3 import (
    SupportResistanceDetectorV3,
)
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15V3CriteriaAdjuster:
    """パターン15 V3 基準値調整器"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "1ヶ月", "days": 30},
            {"name": "3ヶ月", "days": 90},
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
        ]

        # 基準値調整パターン
        self.adjustment_patterns = [
            {
                "name": "現在設定",
                "adjustments": {
                    "5m": {
                        "min_peaks": 2,
                        "buffer_percentile": 20,
                        "min_line_strength": 0.4,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                    "1h": {
                        "min_peaks": 3,
                        "buffer_percentile": 15,
                        "min_line_strength": 0.6,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                    "1d": {
                        "min_peaks": 4,
                        "buffer_percentile": 10,
                        "min_line_strength": 0.8,
                        "max_angle": 20,
                        "price_tolerance": 0.002,
                    },
                },
            },
            {
                "name": "緩和設定1",
                "adjustments": {
                    "5m": {
                        "min_peaks": 2,
                        "buffer_percentile": 25,
                        "min_line_strength": 0.3,
                        "max_angle": 60,
                        "price_tolerance": 0.008,
                    },
                    "1h": {
                        "min_peaks": 2,
                        "buffer_percentile": 20,
                        "min_line_strength": 0.5,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                    "1d": {
                        "min_peaks": 3,
                        "buffer_percentile": 15,
                        "min_line_strength": 0.7,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                },
            },
            {
                "name": "緩和設定2",
                "adjustments": {
                    "5m": {
                        "min_peaks": 1,
                        "buffer_percentile": 30,
                        "min_line_strength": 0.2,
                        "max_angle": 75,
                        "price_tolerance": 0.01,
                    },
                    "1h": {
                        "min_peaks": 2,
                        "buffer_percentile": 25,
                        "min_line_strength": 0.4,
                        "max_angle": 60,
                        "price_tolerance": 0.008,
                    },
                    "1d": {
                        "min_peaks": 2,
                        "buffer_percentile": 20,
                        "min_line_strength": 0.6,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                },
            },
        ]

    async def adjust_and_analyze(self) -> Dict:
        """基準値調整と詳細分析"""
        logger.info("=== パターン15 V3 基準値調整と詳細分析開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            results = {}
            for pattern in self.adjustment_patterns:
                logger.info(f"調整パターン: {pattern['name']}")
                pattern_results = {}

                for timeframe in self.timeframes:
                    logger.info(f"  時間足: {timeframe}")
                    timeframe_results = {}

                    for period in self.test_periods:
                        logger.info(f"    期間: {period['name']}")
                        result = await self._test_with_adjusted_criteria(
                            timeframe, period, pattern["adjustments"][timeframe]
                        )
                        timeframe_results[period["name"]] = result

                    # 時間足別統計
                    timeframe_stats = self._analyze_timeframe_statistics(
                        timeframe_results
                    )
                    timeframe_results["statistics"] = timeframe_stats

                    pattern_results[timeframe] = timeframe_results

                # 調整パターン別統計
                pattern_stats = self._analyze_pattern_statistics(pattern_results)
                pattern_results["statistics"] = pattern_stats

                results[pattern["name"]] = pattern_results

            # 全体比較分析
            comparison = self._compare_adjustment_patterns(results)

            # データベース接続終了
            await db_manager.close()

            return {
                "adjustment_results": results,
                "comparison": comparison,
                "analysis_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"基準値調整エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _test_with_adjusted_criteria(
        self, timeframe: str, period: Dict, adjustments: Dict
    ) -> Dict:
        """調整された基準値でテスト"""
        try:
            # データ取得
            data = await self._fetch_market_data(period["days"])
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"      取得データ: {len(data)}件")

            # カスタムデテクター作成
            detector = self._create_custom_detector(timeframe, adjustments)

            # パターン検出
            detection = detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_with_price_trend(
                    detection, data, timeframe, period, adjustments
                )
                return {
                    "detected": True,
                    "detection": detection,
                    "analysis": detailed_analysis,
                    "data_points": len(data),
                    "period_days": period["days"],
                    "adjustments": adjustments,
                }
            else:
                return {
                    "detected": False,
                    "data_points": len(data),
                    "period_days": period["days"],
                    "adjustments": adjustments,
                }

        except Exception as e:
            logger.error(f"調整基準値テストエラー: {e}")
            return {"error": str(e)}

    def _create_custom_detector(
        self, timeframe: str, adjustments: Dict
    ) -> SupportResistanceDetectorV3:
        """カスタムデテクター作成"""
        detector = SupportResistanceDetectorV3(timeframe)

        # 基準値を調整
        detector.min_peaks = adjustments["min_peaks"]
        detector.buffer_percentile = adjustments["buffer_percentile"]
        detector.min_line_strength = adjustments["min_line_strength"]
        detector.max_angle = adjustments["max_angle"]
        detector.price_tolerance = adjustments["price_tolerance"]

        return detector

    def _analyze_detection_with_price_trend(
        self,
        detection: Dict,
        data: pd.DataFrame,
        timeframe: str,
        period: Dict,
        adjustments: Dict,
    ) -> Dict:
        """価格推移を含む詳細分析"""
        try:
            analysis = {}

            # 基本情報
            pattern_data = detection.get("pattern_data", {})
            equation = pattern_data.get("equation", {})
            current_analysis = pattern_data.get("current_analysis", {})

            analysis["basic_info"] = {
                "pattern_type": detection.get("pattern_type"),
                "confidence": detection.get("confidence_score"),
                "direction": detection.get("direction"),
                "strategy": detection.get("strategy"),
                "entry_condition": detection.get("entry_condition"),
                "timeframe": timeframe,
                "period": period["name"],
                "adjustments": adjustments,
            }

            # 数学的パラメータ
            analysis["mathematical"] = {
                "slope": equation.get("slope"),
                "intercept": equation.get("intercept"),
                "angle": equation.get("angle"),
                "equation_score": equation.get("score"),
                "angle_description": self._get_angle_description(
                    equation.get("angle", 0)
                ),
            }

            # ライン強度
            analysis["strength"] = {
                "line_strength": pattern_data.get("strength"),
                "peak_count": len(pattern_data.get("peaks", []))
                if detection.get("pattern_type") == "resistance_line"
                else len(pattern_data.get("troughs", [])),
                "peak_indices": pattern_data.get("peaks", [])[:5]
                if detection.get("pattern_type") == "resistance_line"
                else pattern_data.get("troughs", [])[:5],
            }

            # 現在価格との関係
            analysis["current_relation"] = {
                "relation": current_analysis.get("relation"),
                "strength": current_analysis.get("strength"),
                "distance": current_analysis.get("distance"),
                "line_price": current_analysis.get("line_price"),
                "current_price": current_analysis.get("current_price"),
                "price_difference": abs(
                    current_analysis.get("line_price", 0)
                    - current_analysis.get("current_price", 0)
                ),
            }

            # 価格推移分析
            analysis["price_trend"] = self._analyze_price_trend(
                data, equation, pattern_data
            )

            # 角度分析
            analysis["angle_analysis"] = self._analyze_angle_details(
                equation, data, pattern_data
            )

            return analysis

        except Exception as e:
            logger.error(f"価格推移分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_price_trend(
        self, data: pd.DataFrame, equation: Dict, pattern_data: Dict
    ) -> Dict:
        """価格推移の詳細分析"""
        try:
            analysis = {}

            # ライン方程式
            slope = equation.get("slope", 0)
            intercept = equation.get("intercept", 0)

            # 価格データの基本統計
            high_prices = data["High"].values
            low_prices = data["Low"].values
            close_prices = data["Close"].values

            analysis["price_statistics"] = {
                "high_prices": {
                    "min": float(np.min(high_prices)),
                    "max": float(np.max(high_prices)),
                    "mean": float(np.mean(high_prices)),
                    "std": float(np.std(high_prices)),
                    "range": float(np.max(high_prices) - np.min(high_prices)),
                },
                "low_prices": {
                    "min": float(np.min(low_prices)),
                    "max": float(np.max(low_prices)),
                    "mean": float(np.mean(low_prices)),
                    "std": float(np.std(low_prices)),
                    "range": float(np.max(low_prices) - np.min(low_prices)),
                },
                "close_prices": {
                    "min": float(np.min(close_prices)),
                    "max": float(np.max(close_prices)),
                    "mean": float(np.mean(close_prices)),
                    "std": float(np.std(close_prices)),
                    "range": float(np.max(close_prices) - np.min(close_prices)),
                },
            }

            # ライン上の価格ポイント
            line_prices = []
            for i in range(len(data)):
                line_price = slope * i + intercept
                line_prices.append(line_price)

            analysis["line_analysis"] = {
                "line_prices": {
                    "min": float(np.min(line_prices)),
                    "max": float(np.max(line_prices)),
                    "mean": float(np.mean(line_prices)),
                    "std": float(np.std(line_prices)),
                },
                "price_deviation": {
                    "mean_deviation": float(
                        np.mean(np.abs(np.array(close_prices) - np.array(line_prices)))
                    ),
                    "max_deviation": float(
                        np.max(np.abs(np.array(close_prices) - np.array(line_prices)))
                    ),
                },
            }

            # ピーク/ボトムの価格分析
            peaks = pattern_data.get("peaks", [])
            troughs = pattern_data.get("troughs", [])

            if peaks:
                peak_prices = [high_prices[i] for i in peaks]
                analysis["peak_analysis"] = {
                    "peak_prices": peak_prices,
                    "peak_price_stats": {
                        "min": float(np.min(peak_prices)),
                        "max": float(np.max(peak_prices)),
                        "mean": float(np.mean(peak_prices)),
                        "std": float(np.std(peak_prices)),
                    },
                }

            if troughs:
                trough_prices = [low_prices[i] for i in troughs]
                analysis["trough_analysis"] = {
                    "trough_prices": trough_prices,
                    "trough_price_stats": {
                        "min": float(np.min(trough_prices)),
                        "max": float(np.max(trough_prices)),
                        "mean": float(np.mean(trough_prices)),
                        "std": float(np.std(trough_prices)),
                    },
                }

            return analysis

        except Exception as e:
            logger.error(f"価格推移分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_angle_details(
        self, equation: Dict, data: pd.DataFrame, pattern_data: Dict
    ) -> Dict:
        """角度の詳細分析"""
        try:
            analysis = {}

            angle = equation.get("angle", 0)
            slope = equation.get("slope", 0)

            analysis["angle_basic"] = {
                "angle_degrees": angle,
                "slope": slope,
                "angle_description": self._get_angle_description(angle),
                "is_horizontal": abs(angle) < 5,
                "is_vertical": abs(angle) > 85,
            }

            # 角度の強度分析
            abs_angle = abs(angle)
            if abs_angle < 5:
                angle_strength = 1.0
                angle_category = "水平"
            elif abs_angle < 15:
                angle_strength = 0.9
                angle_category = "緩やか"
            elif abs_angle < 30:
                angle_strength = 0.7
                angle_category = "中程度"
            elif abs_angle < 45:
                angle_strength = 0.5
                angle_category = "急"
            else:
                angle_strength = 0.3
                angle_category = "非常に急"

            analysis["angle_strength"] = {
                "strength": angle_strength,
                "category": angle_category,
                "confidence_boost": angle_strength * 0.1,  # 信頼度への影響
            }

            # トレンド方向
            if angle > 0:
                trend_direction = "上昇"
                trend_strength = min(abs_angle / 45.0, 1.0)
            elif angle < 0:
                trend_direction = "下降"
                trend_strength = min(abs_angle / 45.0, 1.0)
            else:
                trend_direction = "横ばい"
                trend_strength = 0.0

            analysis["trend_analysis"] = {
                "direction": trend_direction,
                "strength": trend_strength,
                "is_trending": abs_angle > 5,
            }

            return analysis

        except Exception as e:
            logger.error(f"角度詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_timeframe_statistics(self, timeframe_results: Dict) -> Dict:
        """時間足別統計分析"""
        try:
            stats = {
                "total_periods": len(
                    [k for k in timeframe_results.keys() if k != "statistics"]
                ),
                "detection_count": 0,
                "detection_rate": 0.0,
                "period_detections": {},
                "confidence_by_period": {},
                "strength_by_period": {},
                "angle_by_period": {},
                "pattern_type_distribution": {},
            }

            for period_name, result in timeframe_results.items():
                if period_name == "statistics":
                    continue

                if result.get("detected", False):
                    stats["detection_count"] += 1
                    stats["period_detections"][period_name] = True

                    # 信頼度統計
                    confidence = result["detection"].get("confidence_score", 0)
                    if period_name not in stats["confidence_by_period"]:
                        stats["confidence_by_period"][period_name] = []
                    stats["confidence_by_period"][period_name].append(confidence)

                    # 強度統計
                    strength = result["analysis"]["strength"]["line_strength"]
                    if period_name not in stats["strength_by_period"]:
                        stats["strength_by_period"][period_name] = []
                    stats["strength_by_period"][period_name].append(strength)

                    # 角度統計
                    angle = result["analysis"]["mathematical"]["angle"]
                    if period_name not in stats["angle_by_period"]:
                        stats["angle_by_period"][period_name] = []
                    stats["angle_by_period"][period_name].append(angle)

                    # パターンタイプ統計
                    pattern_type = result["detection"].get("pattern_type", "unknown")
                    stats["pattern_type_distribution"][pattern_type] = (
                        stats["pattern_type_distribution"].get(pattern_type, 0) + 1
                    )
                else:
                    stats["period_detections"][period_name] = False

            # 検出率計算
            stats["detection_rate"] = stats["detection_count"] / stats["total_periods"]

            # 期間別平均値計算
            for period_name in stats["confidence_by_period"]:
                stats["confidence_by_period"][period_name] = sum(
                    stats["confidence_by_period"][period_name]
                ) / len(stats["confidence_by_period"][period_name])

            for period_name in stats["strength_by_period"]:
                stats["strength_by_period"][period_name] = sum(
                    stats["strength_by_period"][period_name]
                ) / len(stats["strength_by_period"][period_name])

            for period_name in stats["angle_by_period"]:
                stats["angle_by_period"][period_name] = sum(
                    stats["angle_by_period"][period_name]
                ) / len(stats["angle_by_period"][period_name])

            return stats

        except Exception as e:
            logger.error(f"時間足別統計分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_pattern_statistics(self, pattern_results: Dict) -> Dict:
        """調整パターン別統計分析"""
        try:
            stats = {
                "total_timeframes": len(pattern_results),
                "total_detections": 0,
                "overall_detection_rate": 0.0,
                "timeframe_detection_summary": {},
                "best_performing_timeframe": None,
                "highest_confidence": 0.0,
                "highest_strength": 0.0,
            }

            total_periods = 0
            timeframe_performance = {}

            for timeframe, timeframe_results in pattern_results.items():
                if timeframe == "statistics":
                    continue

                timeframe_stats = timeframe_results.get("statistics", {})
                detection_count = timeframe_stats.get("detection_count", 0)
                total_periods_tf = timeframe_stats.get("total_periods", 0)

                stats["total_detections"] += detection_count
                total_periods += total_periods_tf

                detection_rate = timeframe_stats.get("detection_rate", 0.0)
                timeframe_performance[timeframe] = detection_rate

                stats["timeframe_detection_summary"][timeframe] = {
                    "detection_count": detection_count,
                    "total_periods": total_periods_tf,
                    "detection_rate": detection_rate,
                }

                # 最高信頼度・強度の追跡
                confidence_by_period = timeframe_stats.get("confidence_by_period", {})
                strength_by_period = timeframe_stats.get("strength_by_period", {})

                for period_name, confidences in confidence_by_period.items():
                    if confidences and max(confidences) > stats["highest_confidence"]:
                        stats["highest_confidence"] = max(confidences)

                for period_name, strengths in strength_by_period.items():
                    if strengths and max(strengths) > stats["highest_strength"]:
                        stats["highest_strength"] = max(strengths)

            # 全体検出率
            if total_periods > 0:
                stats["overall_detection_rate"] = (
                    stats["total_detections"] / total_periods
                )

            # 最高パフォーマンス時間足
            if timeframe_performance:
                stats["best_performing_timeframe"] = max(
                    timeframe_performance, key=timeframe_performance.get
                )

            return stats

        except Exception as e:
            logger.error(f"調整パターン統計分析エラー: {e}")
            return {"error": str(e)}

    def _compare_adjustment_patterns(self, results: Dict) -> Dict:
        """調整パターンの比較分析"""
        try:
            comparison = {
                "pattern_comparison": {},
                "best_pattern": None,
                "improvement_analysis": {},
            }

            for pattern_name, pattern_results in results.items():
                pattern_stats = pattern_results.get("statistics", {})

                comparison["pattern_comparison"][pattern_name] = {
                    "total_detections": pattern_stats.get("total_detections", 0),
                    "overall_detection_rate": pattern_stats.get(
                        "overall_detection_rate", 0.0
                    ),
                    "highest_confidence": pattern_stats.get("highest_confidence", 0.0),
                    "highest_strength": pattern_stats.get("highest_strength", 0.0),
                    "best_timeframe": pattern_stats.get(
                        "best_performing_timeframe", "N/A"
                    ),
                }

            # 最高パフォーマンスパターンの特定
            best_pattern = max(
                comparison["pattern_comparison"].items(),
                key=lambda x: (
                    x[1]["total_detections"],
                    x[1]["overall_detection_rate"],
                ),
            )
            comparison["best_pattern"] = best_pattern[0]

            # 改善分析
            current_pattern = comparison["pattern_comparison"]["現在設定"]
            for pattern_name, pattern_data in comparison["pattern_comparison"].items():
                if pattern_name != "現在設定":
                    improvement = {
                        "detection_increase": pattern_data["total_detections"]
                        - current_pattern["total_detections"],
                        "rate_improvement": pattern_data["overall_detection_rate"]
                        - current_pattern["overall_detection_rate"],
                        "confidence_change": pattern_data["highest_confidence"]
                        - current_pattern["highest_confidence"],
                        "strength_change": pattern_data["highest_strength"]
                        - current_pattern["highest_strength"],
                    }
                    comparison["improvement_analysis"][pattern_name] = improvement

            return comparison

        except Exception as e:
            logger.error(f"調整パターン比較分析エラー: {e}")
            return {"error": str(e)}

    def _get_angle_description(self, angle: float) -> str:
        """角度の説明を取得"""
        abs_angle = abs(angle)
        if abs_angle < 5:
            return "ほぼ水平"
        elif abs_angle < 15:
            return "緩やかな上昇" if angle > 0 else "緩やかな下降"
        elif abs_angle < 30:
            return "中程度の上昇" if angle > 0 else "中程度の下降"
        elif abs_angle < 45:
            return "急な上昇" if angle > 0 else "急な下降"
        else:
            return "非常に急な上昇" if angle > 0 else "非常に急な下降"

    async def _fetch_market_data(self, days: int) -> pd.DataFrame:
        """市場データ取得"""
        try:
            async with db_manager.get_session() as session:
                query = text(
                    """
                    SELECT
                        timestamp as Date,
                        open_price as Open,
                        high_price as High,
                        low_price as Low,
                        close_price as Close,
                        volume as Volume
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT :days
                """
                )

                result = await session.execute(query, {"days": days})
                rows = result.fetchall()

                if not rows:
                    return pd.DataFrame()

                data = pd.DataFrame(
                    rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
                )

                data = data.sort_values("Date").reset_index(drop=True)
                return data

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return pd.DataFrame()


async def main():
    """メイン関数"""
    adjuster = Pattern15V3CriteriaAdjuster()
    results = await adjuster.adjust_and_analyze()

    if "error" in results:
        print(f"\n❌ 調整エラー: {results['error']}")
        return

    print("\n=== パターン15 V3 基準値調整と詳細分析結果 ===")

    # 調整パターン比較
    comparison = results.get("comparison", {})
    print(f"\n📊 調整パターン比較:")

    pattern_comparison = comparison.get("pattern_comparison", {})
    for pattern_name, pattern_data in pattern_comparison.items():
        print(f"\n🔧 {pattern_name}:")
        print(f"  総検出件数: {pattern_data['total_detections']}")
        print(f"  全体検出率: {pattern_data['overall_detection_rate']:.1%}")
        print(f"  最高信頼度: {pattern_data['highest_confidence']:.3f}")
        print(f"  最高強度: {pattern_data['highest_strength']:.3f}")
        print(f"  最高パフォーマンス時間足: {pattern_data['best_timeframe']}")

    # 最高パフォーマンスパターン
    best_pattern = comparison.get("best_pattern", "N/A")
    print(f"\n🏆 最高パフォーマンスパターン: {best_pattern}")

    # 改善分析
    improvement_analysis = comparison.get("improvement_analysis", {})
    if improvement_analysis:
        print(f"\n📈 改善分析:")
        for pattern_name, improvement in improvement_analysis.items():
            print(f"\n  {pattern_name}:")
            print(f"    検出件数増加: {improvement['detection_increase']}")
            print(f"    検出率改善: {improvement['rate_improvement']:.1%}")
            print(f"    信頼度変化: {improvement['confidence_change']:+.3f}")
            print(f"    強度変化: {improvement['strength_change']:+.3f}")

    # 詳細結果
    print(f"\n📋 詳細結果:")
    adjustment_results = results.get("adjustment_results", {})

    for pattern_name, pattern_results in adjustment_results.items():
        print(f"\n🔧 {pattern_name}:")

        for timeframe, timeframe_data in pattern_results.items():
            if timeframe == "statistics":
                continue

            print(f"\n  📊 {timeframe}:")

            # 時間足別統計
            tf_stats = timeframe_data.get("statistics", {})
            print(f"    検出件数: {tf_stats.get('detection_count', 0)}")
            print(f"    検出率: {tf_stats.get('detection_rate', 0):.1%}")

            # 詳細結果
            for period_name, result in timeframe_data.items():
                if period_name == "statistics":
                    continue

                if "error" in result:
                    print(f"      ❌ {period_name}: {result['error']}")
                    continue

                print(f"      📊 {period_name} ({result['data_points']}件):")

                if result.get("detected", False):
                    detection = result["detection"]
                    analysis = result["analysis"]

                    # 基本情報
                    basic = analysis.get("basic_info", {})
                    print(f"        ✅ 検出成功!")
                    print(f"          パターン: {basic.get('pattern_type')}")
                    print(f"          信頼度: {basic.get('confidence', 0):.3f}")
                    print(f"          方向: {basic.get('direction')}")

                    # 数学的パラメータ
                    math_info = analysis.get("mathematical", {})
                    print(
                        f"          角度: {math_info.get('angle', 0):.2f}度 ({math_info.get('angle_description', '')})"
                    )
                    print(f"          方程式スコア: {math_info.get('equation_score', 0):.3f}")

                    # ライン強度
                    strength = analysis.get("strength", {})
                    print(f"          ライン強度: {strength.get('line_strength', 0):.3f}")
                    print(f"          ピーク数: {strength.get('peak_count', 0)}件")

                    # 価格推移分析
                    price_trend = analysis.get("price_trend", {})
                    if "price_statistics" in price_trend:
                        price_stats = price_trend["price_statistics"]
                        high_stats = price_stats.get("high_prices", {})
                        print(
                            f"          価格範囲: {high_stats.get('min', 0):.5f} - {high_stats.get('max', 0):.5f}"
                        )
                        print(f"          価格変動: {high_stats.get('range', 0):.5f}")

                    # 角度分析
                    angle_analysis = analysis.get("angle_analysis", {})
                    if "angle_basic" in angle_analysis:
                        angle_basic = angle_analysis["angle_basic"]
                        print(
                            f"          角度カテゴリ: {angle_basic.get('angle_description', '')}"
                        )
                        print(
                            f"          水平ライン: {'✅' if angle_basic.get('is_horizontal', False) else '❌'}"
                        )

                    if "trend_analysis" in angle_analysis:
                        trend = angle_analysis["trend_analysis"]
                        print(f"          トレンド方向: {trend.get('direction', '')}")
                        print(f"          トレンド強度: {trend.get('strength', 0):.3f}")

                    # 現在価格との関係
                    relation = analysis.get("current_relation", {})
                    print(f"          関係: {relation.get('relation')}")
                    print(f"          価格差: {relation.get('price_difference', 0):.5f}")

                else:
                    print(f"        ❌ 検出なし")


if __name__ == "__main__":
    asyncio.run(main())
