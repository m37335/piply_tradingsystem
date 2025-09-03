"""
パターン15 V3 さらなる基準緩和テストスクリプト

月50-100回の検出を目指した基準緩和
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

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


class Pattern15V3FurtherRelaxationTester:
    """パターン15 V3 さらなる基準緩和テスター"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "1ヶ月", "days": 30},
            {"name": "3ヶ月", "days": 90},
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
        ]

        # さらなる緩和設定パターン
        self.relaxation_patterns = [
            {
                "name": "現在設定（バッファ縮小1）",
                "settings": {
                    "5m": {
                        "buffer_percentile": 10,
                        "min_peaks": 3,
                        "min_line_strength": 0.5,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                    "1h": {
                        "buffer_percentile": 8,
                        "min_peaks": 4,
                        "min_line_strength": 0.7,
                        "max_angle": 20,
                        "price_tolerance": 0.002,
                    },
                    "1d": {
                        "buffer_percentile": 5,
                        "min_peaks": 5,
                        "min_line_strength": 0.9,
                        "max_angle": 15,
                        "price_tolerance": 0.001,
                    },
                },
            },
            {
                "name": "緩和設定1（バッファ拡大）",
                "settings": {
                    "5m": {
                        "buffer_percentile": 20,
                        "min_peaks": 2,
                        "min_line_strength": 0.3,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                    "1h": {
                        "buffer_percentile": 15,
                        "min_peaks": 3,
                        "min_line_strength": 0.5,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                    "1d": {
                        "buffer_percentile": 10,
                        "min_peaks": 4,
                        "min_line_strength": 0.7,
                        "max_angle": 20,
                        "price_tolerance": 0.002,
                    },
                },
            },
            {
                "name": "緩和設定2（大幅緩和）",
                "settings": {
                    "5m": {
                        "buffer_percentile": 30,
                        "min_peaks": 1,
                        "min_line_strength": 0.2,
                        "max_angle": 60,
                        "price_tolerance": 0.008,
                    },
                    "1h": {
                        "buffer_percentile": 25,
                        "min_peaks": 2,
                        "min_line_strength": 0.4,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                    "1d": {
                        "buffer_percentile": 20,
                        "min_peaks": 3,
                        "min_line_strength": 0.6,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                },
            },
            {
                "name": "緩和設定3（極限緩和）",
                "settings": {
                    "5m": {
                        "buffer_percentile": 40,
                        "min_peaks": 1,
                        "min_line_strength": 0.1,
                        "max_angle": 75,
                        "price_tolerance": 0.01,
                    },
                    "1h": {
                        "buffer_percentile": 35,
                        "min_peaks": 1,
                        "min_line_strength": 0.3,
                        "max_angle": 60,
                        "price_tolerance": 0.008,
                    },
                    "1d": {
                        "buffer_percentile": 30,
                        "min_peaks": 2,
                        "min_line_strength": 0.5,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                },
            },
        ]

    async def test_further_relaxation(self) -> Dict:
        """さらなる基準緩和のテスト"""
        logger.info("=== パターン15 V3 さらなる基準緩和テスト開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # データベース情報取得
            db_info = await self._get_database_info()

            # 各緩和設定でのテスト
            relaxation_results = await self._test_all_relaxation_patterns()

            # データベース接続終了
            await db_manager.close()

            return {
                "database_info": db_info,
                "relaxation_results": relaxation_results,
                "analysis_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"さらなる基準緩和テストエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _get_database_info(self) -> Dict:
        """データベース情報取得"""
        try:
            async with db_manager.get_session() as session:
                # 総レコード数
                count_query = text(
                    """
                    SELECT COUNT(*) as total_records
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    """
                )
                count_result = await session.execute(count_query)
                total_records = count_result.fetchone()[0]

                # データ期間
                period_query = text(
                    """
                    SELECT
                        MIN(timestamp) as start_date,
                        MAX(timestamp) as end_date
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    """
                )
                period_result = await session.execute(period_query)
                period_row = period_result.fetchone()
                start_date = period_row[0]
                end_date = period_row[1]

                return {
                    "total_records": total_records,
                    "start_date": str(start_date) if start_date else None,
                    "end_date": str(end_date) if end_date else None,
                    "data_span_days": (
                        (end_date - start_date).days if start_date and end_date else 0
                    ),
                }

        except Exception as e:
            logger.error(f"データベース情報取得エラー: {e}")
            return {"error": str(e)}

    async def _test_all_relaxation_patterns(self) -> Dict:
        """全緩和設定パターンのテスト"""
        try:
            results = {}

            for pattern in self.relaxation_patterns:
                logger.info(f"緩和設定テスト: {pattern['name']}")
                pattern_results = {}

                for timeframe in self.timeframes:
                    logger.info(f"  時間足: {timeframe}")
                    timeframe_results = {}

                    for period in self.test_periods:
                        logger.info(f"    期間: {period['name']}")
                        result = await self._test_with_relaxation_settings(
                            timeframe, period, pattern["settings"][timeframe]
                        )
                        timeframe_results[period["name"]] = result

                    # 時間足別統計
                    timeframe_stats = self._analyze_timeframe_statistics(
                        timeframe_results
                    )
                    timeframe_results["statistics"] = timeframe_stats

                    pattern_results[timeframe] = timeframe_results

                # 緩和パターン別統計
                pattern_stats = self._analyze_pattern_statistics(pattern_results)
                pattern_results["statistics"] = pattern_stats

                results[pattern["name"]] = pattern_results

            return results

        except Exception as e:
            logger.error(f"全緩和設定パターンテストエラー: {e}")
            return {"error": str(e)}

    async def _test_with_relaxation_settings(
        self, timeframe: str, period: Dict, settings: Dict
    ) -> Dict:
        """緩和設定でのテスト"""
        try:
            # データ取得
            data = await self._fetch_market_data(period["days"])
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"      取得データ: {len(data)}件")

            # 緩和されたデテクター作成
            detector = self._create_relaxed_detector(timeframe, settings)

            # パターン検出
            detection = detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_with_details(
                    detection, data, timeframe, period, settings
                )
                return {
                    "detected": True,
                    "detection": detection,
                    "analysis": detailed_analysis,
                    "data_points": len(data),
                    "period_days": period["days"],
                    "settings": settings,
                }
            else:
                return {
                    "detected": False,
                    "data_points": len(data),
                    "period_days": period["days"],
                    "settings": settings,
                }

        except Exception as e:
            logger.error(f"緩和設定テストエラー: {e}")
            return {"error": str(e)}

    def _create_relaxed_detector(
        self, timeframe: str, settings: Dict
    ) -> SupportResistanceDetectorV3:
        """緩和されたデテクター作成"""
        detector = SupportResistanceDetectorV3(timeframe)

        # 緩和設定を適用
        detector.min_peaks = settings["min_peaks"]
        detector.buffer_percentile = settings["buffer_percentile"]
        detector.min_line_strength = settings["min_line_strength"]
        detector.max_angle = settings["max_angle"]
        detector.price_tolerance = settings["price_tolerance"]

        return detector

    def _analyze_detection_with_details(
        self,
        detection: Dict,
        data: pd.DataFrame,
        timeframe: str,
        period: Dict,
        settings: Dict,
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
                "settings": settings,
            }

            # 数学的パラメータ
            slope = equation.get("slope", 0)
            angle = equation.get("angle", 0)

            analysis["mathematical"] = {
                "slope": slope,
                "intercept": equation.get("intercept"),
                "angle": angle,
                "equation_score": equation.get("score"),
                "slope_description": self._get_slope_description(slope),
                "angle_description": self._get_angle_description(angle),
            }

            # 検出品質分析
            analysis["detection_quality"] = self._analyze_detection_quality(
                data, pattern_data, settings
            )

            return analysis

        except Exception as e:
            logger.error(f"検出詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_detection_quality(
        self, data: pd.DataFrame, pattern_data: Dict, settings: Dict
    ) -> Dict:
        """検出品質分析"""
        try:
            analysis = {}

            # バッファ効果分析
            buffer_percentile = settings["buffer_percentile"]
            high_prices = data["High"].values
            low_prices = data["Low"].values

            high_threshold = np.percentile(high_prices, 100 - buffer_percentile)
            low_threshold = np.percentile(low_prices, buffer_percentile)

            high_buffer_points = np.sum(high_prices >= high_threshold)
            low_buffer_points = np.sum(low_prices <= low_threshold)

            analysis["buffer_effectiveness"] = {
                "buffer_percentile": buffer_percentile,
                "high_threshold": float(high_threshold),
                "low_threshold": float(low_threshold),
                "high_buffer_points": int(high_buffer_points),
                "low_buffer_points": int(low_buffer_points),
                "total_buffer_points": int(high_buffer_points + low_buffer_points),
                "buffer_coverage": float(
                    (high_buffer_points + low_buffer_points) / len(high_prices)
                ),
            }

            # 検出品質
            peaks = pattern_data.get("peaks", [])
            troughs = pattern_data.get("troughs", [])

            analysis["detection_metrics"] = {
                "peak_count": len(peaks),
                "trough_count": len(troughs),
                "total_extremums": len(peaks) + len(troughs),
                "buffer_efficiency": (
                    float(
                        (len(peaks) + len(troughs))
                        / (high_buffer_points + low_buffer_points)
                    )
                    if (high_buffer_points + low_buffer_points) > 0
                    else 0
                ),
                "line_strength": pattern_data.get("strength", 0),
            }

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
                "buffer_efficiency_by_period": {},
                "total_buffer_points": 0,
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
                    slope = result["analysis"]["mathematical"]["slope"]
                    if period_name not in stats["slope_by_period"]:
                        stats["slope_by_period"][period_name] = []
                    stats["slope_by_period"][period_name].append(slope)

                    # 角度統計
                    angle = result["analysis"]["mathematical"]["angle"]
                    if period_name not in stats["angle_by_period"]:
                        stats["angle_by_period"][period_name] = []
                    stats["angle_by_period"][period_name].append(angle)

                    # バッファ効率統計
                    buffer_efficiency = result["analysis"]["detection_quality"][
                        "detection_metrics"
                    ]["buffer_efficiency"]
                    if period_name not in stats["buffer_efficiency_by_period"]:
                        stats["buffer_efficiency_by_period"][period_name] = []
                    stats["buffer_efficiency_by_period"][period_name].append(
                        buffer_efficiency
                    )

                    # 総バッファポイント
                    total_buffer = result["analysis"]["detection_quality"][
                        "buffer_effectiveness"
                    ]["total_buffer_points"]
                    stats["total_buffer_points"] += total_buffer
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

            for period_name in stats["buffer_efficiency_by_period"]:
                stats["buffer_efficiency_by_period"][period_name] = sum(
                    stats["buffer_efficiency_by_period"][period_name]
                ) / len(stats["buffer_efficiency_by_period"][period_name])

            return stats

        except Exception as e:
            logger.error(f"時間足別統計分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_pattern_statistics(self, pattern_results: Dict) -> Dict:
        """緩和パターン別統計分析"""
        try:
            stats = {
                "total_timeframes": len(pattern_results),
                "total_detections": 0,
                "overall_detection_rate": 0.0,
                "timeframe_detection_summary": {},
                "best_performing_timeframe": None,
                "highest_confidence": 0.0,
                "average_slope": 0.0,
                "average_buffer_efficiency": 0.0,
                "total_buffer_points": 0,
            }

            total_periods = 0
            timeframe_performance = {}
            all_slopes = []
            all_buffer_efficiencies = []

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

                # 傾きとバッファ効率の収集
                slope_by_period = timeframe_stats.get("slope_by_period", {})
                buffer_efficiency_by_period = timeframe_stats.get(
                    "buffer_efficiency_by_period", {}
                )

                for period_name, slopes in slope_by_period.items():
                    all_slopes.extend(slopes)

                for period_name, efficiencies in buffer_efficiency_by_period.items():
                    all_buffer_efficiencies.extend(efficiencies)

                # 総バッファポイント
                total_buffer = timeframe_stats.get("total_buffer_points", 0)
                stats["total_buffer_points"] += total_buffer

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

            # 平均傾きとバッファ効率
            if all_slopes:
                stats["average_slope"] = sum(all_slopes) / len(all_slopes)
            if all_buffer_efficiencies:
                stats["average_buffer_efficiency"] = sum(all_buffer_efficiencies) / len(
                    all_buffer_efficiencies
                )

            return stats

        except Exception as e:
            logger.error(f"緩和パターン統計分析エラー: {e}")
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
    tester = Pattern15V3FurtherRelaxationTester()
    results = await tester.test_further_relaxation()

    if "error" in results:
        print(f"\n❌ テストエラー: {results['error']}")
        return

    print("\n=== パターン15 V3 さらなる基準緩和テスト結果 ===")

    # データベース情報
    db_info = results.get("database_info", {})
    if "error" not in db_info:
        print(f"\n📊 データベース情報:")
        print(f"  総レコード数: {db_info.get('total_records', 0):,}件")
        print(
            f"  データ期間: {db_info.get('start_date', 'N/A')} - {db_info.get('end_date', 'N/A')}"
        )
        print(f"  データ期間: {db_info.get('data_span_days', 0)}日")

    # 緩和結果
    relaxation_results = results.get("relaxation_results", {})
    print(f"\n🔧 緩和設定比較結果:")

    for pattern_name, pattern_results in relaxation_results.items():
        print(f"\n  {pattern_name}:")

        pattern_stats = pattern_results.get("statistics", {})
        print(f"    総検出件数: {pattern_stats.get('total_detections', 0)}")
        print(f"    全体検出率: {pattern_stats.get('overall_detection_rate', 0):.1%}")
        print(f"    最高信頼度: {pattern_stats.get('highest_confidence', 0):.3f}")
        print(f"    平均傾き: {pattern_stats.get('average_slope', 0):.6f}")
        print(f"    平均バッファ効率: {pattern_stats.get('average_buffer_efficiency', 0):.3f}")
        print(f"    総バッファポイント: {pattern_stats.get('total_buffer_points', 0)}")

        # 時間足別結果
        for timeframe, timeframe_data in pattern_results.items():
            if timeframe == "statistics":
                continue

            tf_stats = timeframe_data.get("statistics", {})
            print(
                f"      {timeframe}: {tf_stats.get('detection_count', 0)}件 ({tf_stats.get('detection_rate', 0):.1%})"
            )

            # 詳細結果
            for period_name, result in timeframe_data.items():
                if period_name == "statistics":
                    continue

                if result.get("detected", False):
                    analysis = result.get("analysis", {})
                    detection_quality = analysis.get("detection_quality", {})

                    print(f"        {period_name}:")
                    print(
                        f"          傾き: {analysis['mathematical']['slope']:.6f} ({analysis['mathematical']['slope_description']})"
                    )
                    print(f"          角度: {analysis['mathematical']['angle']:.2f}度")
                    print(
                        f"          バッファ効率: {detection_quality.get('detection_metrics', {}).get('buffer_efficiency', 0):.3f}"
                    )
                    print(
                        f"          バッファカバレッジ: {detection_quality.get('buffer_effectiveness', {}).get('buffer_coverage', 0):.1%}"
                    )


if __name__ == "__main__":
    asyncio.run(main())
