"""
パターン15 V4 座標系ベース検出器テストスクリプト

TA-Libを使用した座標系ベースのサポート/レジスタンスライン検出テスト
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector_v4 import (
    SupportResistanceDetectorV4,
)
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15V4CoordinateSystemTester:
    """パターン15 V4 座標系ベース検出器テスター"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "1ヶ月", "days": 30},
            {"name": "3ヶ月", "days": 90},
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
        ]

    async def test_coordinate_system_detection(self) -> Dict:
        """座標系ベース検出のテスト"""
        logger.info("=== パターン15 V4 座標系ベース検出テスト開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 各時間足でのテスト
            results = {}
            for timeframe in self.timeframes:
                logger.info(f"時間足テスト: {timeframe}")
                timeframe_results = {}

                for period in self.test_periods:
                    logger.info(f"  期間: {period['name']}")
                    result = await self._test_single_period(timeframe, period)
                    timeframe_results[period["name"]] = result

                # 時間足別統計
                timeframe_stats = self._analyze_timeframe_statistics(timeframe_results)
                timeframe_results["statistics"] = timeframe_stats

                results[timeframe] = timeframe_results

            # 全体統計
            overall_stats = self._analyze_overall_statistics(results)

            # データベース接続終了
            await db_manager.close()

            return {
                "results": results,
                "overall_stats": overall_stats,
                "analysis_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"座標系ベース検出テストエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _test_single_period(self, timeframe: str, period: Dict) -> Dict:
        """単一期間でのテスト"""
        try:
            # データ取得
            data = await self._fetch_market_data(period["days"])
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"    取得データ: {len(data)}件")

            # 座標系ベース検出器作成
            detector = SupportResistanceDetectorV4(timeframe)

            # パターン検出
            detection = detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_with_details(
                    detection, data, timeframe, period
                )
                return {
                    "detected": True,
                    "detection": detection,
                    "analysis": detailed_analysis,
                    "data_points": len(data),
                    "period_days": period["days"],
                }
            else:
                return {
                    "detected": False,
                    "data_points": len(data),
                    "period_days": period["days"],
                }

        except Exception as e:
            logger.error(f"単一期間テストエラー: {e}")
            return {"error": str(e)}

    def _analyze_detection_with_details(
        self, detection: Dict, data: pd.DataFrame, timeframe: str, period: Dict
    ) -> Dict:
        """検出詳細分析"""
        try:
            analysis = {}

            # 基本情報
            pattern_data = detection.get("pattern_data", {})
            equation = pattern_data.get("equation", {})

            analysis["basic_info"] = {
                "pattern_type": detection.get("pattern_type"),
                "confidence": detection.get("confidence_score"),
                "direction": detection.get("direction"),
                "strategy": detection.get("strategy"),
                "timeframe": timeframe,
                "period": period["name"],
            }

            # 座標系パラメータ
            slope = equation.get("slope", 0)
            angle = equation.get("angle", 0)

            analysis["coordinate_system"] = {
                "slope": slope,
                "intercept": equation.get("intercept"),
                "angle": angle,
                "r_squared": equation.get("r_squared"),
                "line_length": pattern_data.get("line_length"),
                "points": pattern_data.get("points"),
                "slope_description": self._get_slope_description(slope),
                "angle_description": self._get_angle_description(angle),
            }

            # 検出品質分析
            analysis["detection_quality"] = self._analyze_detection_quality(
                data, pattern_data
            )

            return analysis

        except Exception as e:
            logger.error(f"検出詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_detection_quality(
        self, data: pd.DataFrame, pattern_data: Dict
    ) -> Dict:
        """検出品質分析"""
        try:
            analysis = {}

            # ライン強度
            strength = pattern_data.get("strength", 0)

            # 決定係数
            r_squared = pattern_data.get("equation", {}).get("r_squared", 0)

            # 現在価格関係
            current_analysis = pattern_data.get("current_analysis", {})

            analysis["quality_metrics"] = {
                "line_strength": strength,
                "r_squared": r_squared,
                "current_relation": current_analysis.get("relation"),
                "breakout_strength": current_analysis.get("breakout_strength", 0),
                "price_distance": current_analysis.get("distance", 0),
            }

            # 品質評価
            quality_score = strength * r_squared
            analysis["quality_score"] = quality_score

            if quality_score >= 0.8:
                quality_rating = "Excellent"
            elif quality_score >= 0.6:
                quality_rating = "Good"
            elif quality_score >= 0.4:
                quality_rating = "Fair"
            else:
                quality_rating = "Poor"

            analysis["quality_rating"] = quality_rating

            return analysis

        except Exception as e:
            logger.error(f"検出品質分析エラー: {e}")
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
                "slope_by_period": {},
                "angle_by_period": {},
                "quality_score_by_period": {},
                "line_types": {},
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

                    # 傾き統計
                    slope = result["analysis"]["coordinate_system"]["slope"]
                    if period_name not in stats["slope_by_period"]:
                        stats["slope_by_period"][period_name] = []
                    stats["slope_by_period"][period_name].append(slope)

                    # 角度統計
                    angle = result["analysis"]["coordinate_system"]["angle"]
                    if period_name not in stats["angle_by_period"]:
                        stats["angle_by_period"][period_name] = []
                    stats["angle_by_period"][period_name].append(angle)

                    # 品質スコア統計
                    quality_score = result["analysis"]["detection_quality"][
                        "quality_score"
                    ]
                    if period_name not in stats["quality_score_by_period"]:
                        stats["quality_score_by_period"][period_name] = []
                    stats["quality_score_by_period"][period_name].append(quality_score)

                    # ラインタイプ統計
                    line_type = result["detection"]["pattern_type"]
                    stats["line_types"][line_type] = (
                        stats["line_types"].get(line_type, 0) + 1
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

            for period_name in stats["slope_by_period"]:
                stats["slope_by_period"][period_name] = sum(
                    stats["slope_by_period"][period_name]
                ) / len(stats["slope_by_period"][period_name])

            for period_name in stats["angle_by_period"]:
                stats["angle_by_period"][period_name] = sum(
                    stats["angle_by_period"][period_name]
                ) / len(stats["angle_by_period"][period_name])

            for period_name in stats["quality_score_by_period"]:
                stats["quality_score_by_period"][period_name] = sum(
                    stats["quality_score_by_period"][period_name]
                ) / len(stats["quality_score_by_period"][period_name])

            return stats

        except Exception as e:
            logger.error(f"時間足別統計分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_overall_statistics(self, results: Dict) -> Dict:
        """全体統計分析"""
        try:
            stats = {
                "total_timeframes": len(results),
                "total_detections": 0,
                "overall_detection_rate": 0.0,
                "timeframe_detection_summary": {},
                "best_performing_timeframe": None,
                "highest_confidence": 0.0,
                "average_slope": 0.0,
                "average_quality_score": 0.0,
                "line_type_distribution": {},
                "monthly_estimate": 0.0,
            }

            total_periods = 0
            timeframe_performance = {}
            all_slopes = []
            all_quality_scores = []
            all_line_types = {}

            for timeframe, timeframe_results in results.items():
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

                # 傾きと品質スコアの収集
                slope_by_period = timeframe_stats.get("slope_by_period", {})
                quality_score_by_period = timeframe_stats.get(
                    "quality_score_by_period", {}
                )
                line_types = timeframe_stats.get("line_types", {})

                for period_name, slopes in slope_by_period.items():
                    all_slopes.extend(slopes)

                for period_name, scores in quality_score_by_period.items():
                    all_quality_scores.extend(scores)

                for line_type, count in line_types.items():
                    all_line_types[line_type] = all_line_types.get(line_type, 0) + count

                # 最高信頼度の追跡
                confidence_by_period = timeframe_stats.get("confidence_by_period", {})
                for period_name, confidences in confidence_by_period.items():
                    if confidences and max(confidences) > stats["highest_confidence"]:
                        stats["highest_confidence"] = max(confidences)

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

            # 平均傾きと品質スコア
            if all_slopes:
                stats["average_slope"] = sum(all_slopes) / len(all_slopes)
            if all_quality_scores:
                stats["average_quality_score"] = sum(all_quality_scores) / len(
                    all_quality_scores
                )

            # ラインタイプ分布
            stats["line_type_distribution"] = all_line_types

            # 月間推定
            stats["monthly_estimate"] = stats["total_detections"] / 12

            return stats

        except Exception as e:
            logger.error(f"全体統計分析エラー: {e}")
            return {"error": str(e)}

    def _get_slope_description(self, slope: float) -> str:
        """傾きの説明を取得"""
        abs_slope = abs(slope)
        if abs_slope < 0.0001:
            return "ほぼ水平"
        elif abs_slope < 0.001:
            return "緩やかな上昇" if slope > 0 else "緩やかな下降"
        elif abs_slope < 0.01:
            return "中程度の上昇" if slope > 0 else "中程度の下降"
        elif abs_slope < 0.1:
            return "急な上昇" if slope > 0 else "急な下降"
        else:
            return "非常に急な上昇" if slope > 0 else "非常に急な下降"

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
    tester = Pattern15V4CoordinateSystemTester()
    results = await tester.test_coordinate_system_detection()

    if "error" in results:
        print(f"\n❌ テストエラー: {results['error']}")
        return

    print("\n=== パターン15 V4 座標系ベース検出テスト結果 ===")

    # 全体統計
    overall_stats = results.get("overall_stats", {})
    print(f"\n📊 全体統計:")
    print(f"  総検出件数: {overall_stats.get('total_detections', 0)}")
    print(f"  全体検出率: {overall_stats.get('overall_detection_rate', 0):.1%}")
    print(f"  月間推定: {overall_stats.get('monthly_estimate', 0):.1f}件/月")
    print(f"  最高信頼度: {overall_stats.get('highest_confidence', 0):.3f}")
    print(f"  平均傾き: {overall_stats.get('average_slope', 0):.6f}")
    print(f"  平均品質スコア: {overall_stats.get('average_quality_score', 0):.3f}")

    # ラインタイプ分布
    line_types = overall_stats.get("line_type_distribution", {})
    if line_types:
        print(f"  ラインタイプ分布:")
        for line_type, count in line_types.items():
            print(f"    {line_type}: {count}件")

    # 時間足別結果
    results_data = results.get("results", {})
    print(f"\n🔧 時間足別結果:")

    for timeframe, timeframe_data in results_data.items():
        tf_stats = timeframe_data.get("statistics", {})
        print(f"\n  {timeframe}:")
        print(f"    検出件数: {tf_stats.get('detection_count', 0)}")
        print(f"    検出率: {tf_stats.get('detection_rate', 0):.1%}")

        # 詳細結果
        for period_name, result in timeframe_data.items():
            if period_name == "statistics":
                continue

            if result.get("detected", False):
                analysis = result.get("analysis", {})
                coordinate_system = analysis.get("coordinate_system", {})
                detection_quality = analysis.get("detection_quality", {})

                print(f"      {period_name}:")
                print(f"        パターン: {result['detection']['pattern_type']}")
                print(
                    f"        傾き: {coordinate_system['slope']:.6f} ({coordinate_system['slope_description']})"
                )
                print(f"        角度: {coordinate_system['angle']:.2f}度")
                print(f"        決定係数: {coordinate_system['r_squared']:.3f}")
                print(
                    f"        品質スコア: {detection_quality['quality_score']:.3f} ({detection_quality['quality_rating']})"
                )
                print(f"        信頼度: {result['detection']['confidence_score']:.3f}")
                print(f"        戦略: {result['detection']['strategy']}")


if __name__ == "__main__":
    asyncio.run(main())
