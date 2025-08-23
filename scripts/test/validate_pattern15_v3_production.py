"""
パターン15 V3 実運用検証スクリプト

実際の運用データベースを使用してパターン15 V3の包括的検証を実行
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

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


class Pattern15V3ProductionValidator:
    """パターン15 V3 実運用検証器"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "1週間", "days": 7},
            {"name": "2週間", "days": 14},
            {"name": "1ヶ月", "days": 30},
            {"name": "3ヶ月", "days": 90},
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
        ]

    async def validate_production(self) -> Dict:
        """実運用環境での包括的検証"""
        logger.info("=== パターン15 V3 実運用検証開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # データベース情報取得
            db_info = await self._get_database_info()
            logger.info(f"📊 データベース情報: {db_info}")

            results = {}
            for timeframe in self.timeframes:
                logger.info(f"検証時間足: {timeframe}")
                timeframe_results = {}

                for period in self.test_periods:
                    logger.info(f"  期間: {period['name']}")
                    result = await self._validate_single_period(timeframe, period)
                    timeframe_results[period["name"]] = result

                # 時間足別統計分析
                timeframe_stats = self._analyze_timeframe_statistics(timeframe_results)
                timeframe_results["statistics"] = timeframe_stats

                results[timeframe] = timeframe_results

            # 全体統計分析
            overall_stats = self._analyze_overall_statistics(results)

            # データベース接続終了
            await db_manager.close()

            return {
                "database_info": db_info,
                "timeframe_results": results,
                "overall_statistics": overall_stats,
                "validation_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"実運用検証エラー: {e}")
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
                total_records = count_result.scalar()

                # データ期間
                period_query = text(
                    """
                    SELECT
                        MIN(timestamp) as earliest_date,
                        MAX(timestamp) as latest_date
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                """
                )
                period_result = await session.execute(period_query)
                period_row = period_result.fetchone()

                # 最新データの詳細
                latest_query = text(
                    """
                    SELECT
                        timestamp,
                        open_price,
                        high_price,
                        low_price,
                        close_price,
                        volume
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT 1
                """
                )
                latest_result = await session.execute(latest_query)
                latest_row = latest_result.fetchone()

                return {
                    "total_records": total_records,
                    "earliest_date": period_row[0] if period_row else None,
                    "latest_date": period_row[1] if period_row else None,
                    "latest_data": {
                        "timestamp": latest_row[0] if latest_row else None,
                        "open": latest_row[1] if latest_row else None,
                        "high": latest_row[2] if latest_row else None,
                        "low": latest_row[3] if latest_row else None,
                        "close": latest_row[4] if latest_row else None,
                        "volume": latest_row[5] if latest_row else None,
                    },
                }

        except Exception as e:
            logger.error(f"データベース情報取得エラー: {e}")
            return {"error": str(e)}

    async def _validate_single_period(self, timeframe: str, period: Dict) -> Dict:
        """単一期間の検証"""
        try:
            # データ取得
            data = await self._fetch_market_data(period["days"])
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"    取得データ: {len(data)}件")

            # デテクター作成
            detector = SupportResistanceDetectorV3(timeframe)

            # パターン検出
            detection = detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_detailed(
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
            logger.error(f"期間検証エラー: {e}")
            return {"error": str(e)}

    def _analyze_detection_detailed(
        self, detection: Dict, data: pd.DataFrame, timeframe: str, period: Dict
    ) -> Dict:
        """検出結果の詳細分析"""
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
            }

            # 時間足別パラメータ
            analysis["timeframe_parameters"] = {
                "timeframe": timeframe,
                "min_peaks": pattern_data.get("timeframe") == "5m"
                and 2
                or (pattern_data.get("timeframe") == "1h" and 3 or 4),
                "analysis_period": pattern_data.get("timeframe") == "5m"
                and 60
                or (pattern_data.get("timeframe") == "1h" and 168 or 60),
                "buffer_percentile": pattern_data.get("timeframe") == "5m"
                and 20
                or (pattern_data.get("timeframe") == "1h" and 15 or 10),
                "min_line_strength": pattern_data.get("timeframe") == "5m"
                and 0.4
                or (pattern_data.get("timeframe") == "1h" and 0.6 or 0.8),
                "max_angle": pattern_data.get("timeframe") == "5m"
                and 45
                or (pattern_data.get("timeframe") == "1h" and 30 or 20),
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

            # 時間情報
            analysis["timing"] = {
                "detection_time": detection.get("detection_time"),
                "data_period": f"{data.iloc[0]['Date']} - {data.iloc[-1]['Date']}",
                "data_points": len(data),
                "timeframe": timeframe,
                "period_days": period["days"],
            }

            return analysis

        except Exception as e:
            logger.error(f"検出詳細分析エラー: {e}")
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
                "relation_by_period": {},
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

                    # 関係性統計
                    relation = result["analysis"]["current_relation"]["relation"]
                    if period_name not in stats["relation_by_period"]:
                        stats["relation_by_period"][period_name] = {}
                    stats["relation_by_period"][period_name][relation] = (
                        stats["relation_by_period"][period_name].get(relation, 0) + 1
                    )

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

    def _analyze_overall_statistics(self, results: Dict) -> Dict:
        """全体統計分析"""
        try:
            stats = {
                "total_timeframes": len(results),
                "total_detections": 0,
                "overall_detection_rate": 0.0,
                "timeframe_detection_summary": {},
                "best_performing_timeframe": None,
                "best_performing_period": None,
                "highest_confidence": 0.0,
                "highest_strength": 0.0,
                "pattern_type_summary": {},
                "angle_distribution": {},
                "relation_distribution": {},
            }

            total_periods = 0
            timeframe_performance = {}

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

                # パターンタイプ集計
                pattern_dist = timeframe_stats.get("pattern_type_distribution", {})
                for pattern_type, count in pattern_dist.items():
                    stats["pattern_type_summary"][pattern_type] = (
                        stats["pattern_type_summary"].get(pattern_type, 0) + count
                    )

                # 最高信頼度・強度の追跡
                confidence_by_period = timeframe_stats.get("confidence_by_period", {})
                strength_by_period = timeframe_stats.get("strength_by_period", {})

                for period_name, confidences in confidence_by_period.items():
                    if confidences and max(confidences) > stats["highest_confidence"]:
                        stats["highest_confidence"] = max(confidences)
                        stats["best_performing_timeframe"] = timeframe
                        stats["best_performing_period"] = period_name

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
            logger.error(f"全体統計分析エラー: {e}")
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
    validator = Pattern15V3ProductionValidator()
    results = await validator.validate_production()

    if "error" in results:
        print(f"\n❌ 検証エラー: {results['error']}")
        return

    print("\n=== パターン15 V3 実運用検証結果 ===")

    # データベース情報
    db_info = results.get("database_info", {})
    if "error" not in db_info:
        print(f"\n📊 データベース情報:")
        print(f"  総レコード数: {db_info.get('total_records', 0):,}件")
        print(
            f"  データ期間: {db_info.get('earliest_date', 'N/A')} - {db_info.get('latest_date', 'N/A')}"
        )
        latest_data = db_info.get("latest_data", {})
        if latest_data.get("timestamp"):
            print(
                f"  最新データ: {latest_data['timestamp']} (Close: {latest_data['close']})"
            )

    # 全体統計
    overall_stats = results.get("overall_statistics", {})
    print(f"\n📈 全体統計:")
    print(f"  テスト時間足数: {overall_stats.get('total_timeframes', 0)}")
    print(f"  総検出件数: {overall_stats.get('total_detections', 0)}")
    print(f"  全体検出率: {overall_stats.get('overall_detection_rate', 0):.1%}")
    print(f"  最高信頼度: {overall_stats.get('highest_confidence', 0):.3f}")
    print(f"  最高強度: {overall_stats.get('highest_strength', 0):.3f}")
    print(f"  最高パフォーマンス時間足: {overall_stats.get('best_performing_timeframe', 'N/A')}")

    # パターンタイプ集計
    pattern_summary = overall_stats.get("pattern_type_summary", {})
    if pattern_summary:
        print(f"  パターンタイプ集計:")
        for pattern_type, count in pattern_summary.items():
            print(f"    {pattern_type}: {count}件")

    # 時間足別結果
    print(f"\n📋 時間足別詳細結果:")
    timeframe_results = results.get("timeframe_results", {})

    for timeframe, timeframe_data in timeframe_results.items():
        print(f"\n📊 {timeframe}:")

        # 時間足別統計
        tf_stats = timeframe_data.get("statistics", {})
        print(f"  検出件数: {tf_stats.get('detection_count', 0)}")
        print(f"  検出率: {tf_stats.get('detection_rate', 0):.1%}")

        # 期間別検出状況
        period_detections = tf_stats.get("period_detections", {})
        if period_detections:
            print(f"  期間別検出状況:")
            for period, detected in period_detections.items():
                status = "✅ 検出" if detected else "❌ 未検出"
                print(f"    {period}: {status}")

        # 期間別信頼度
        confidence_by_period = tf_stats.get("confidence_by_period", {})
        if confidence_by_period:
            print(f"  期間別平均信頼度:")
            for period, confidence in confidence_by_period.items():
                print(f"    {period}: {confidence:.3f}")

        # 期間別強度
        strength_by_period = tf_stats.get("strength_by_period", {})
        if strength_by_period:
            print(f"  期間別平均強度:")
            for period, strength in strength_by_period.items():
                print(f"    {period}: {strength:.3f}")

        # 期間別角度
        angle_by_period = tf_stats.get("angle_by_period", {})
        if angle_by_period:
            print(f"  期間別平均角度:")
            for period, angle in angle_by_period.items():
                print(f"    {period}: {angle:.2f}度")

        # 詳細結果
        print(f"  詳細結果:")
        for period_name, result in timeframe_data.items():
            if period_name == "statistics":
                continue

            if "error" in result:
                print(f"    ❌ {period_name}: {result['error']}")
                continue

            print(f"    📊 {period_name} ({result['data_points']}件):")

            if result.get("detected", False):
                detection = result["detection"]
                analysis = result["analysis"]

                # 基本情報
                basic = analysis.get("basic_info", {})
                print(f"      ✅ 検出成功!")
                print(f"        パターン: {basic.get('pattern_type')}")
                print(f"        信頼度: {basic.get('confidence', 0):.3f}")
                print(f"        方向: {basic.get('direction')}")
                print(f"        戦略: {basic.get('strategy')}")

                # 数学的パラメータ
                math_info = analysis.get("mathematical", {})
                print(
                    f"        角度: {math_info.get('angle', 0):.2f}度 ({math_info.get('angle_description', '')})"
                )
                print(f"        方程式スコア: {math_info.get('equation_score', 0):.3f}")

                # ライン強度
                strength = analysis.get("strength", {})
                print(f"        ライン強度: {strength.get('line_strength', 0):.3f}")
                print(f"        ピーク数: {strength.get('peak_count', 0)}件")

                # 現在価格との関係
                relation = analysis.get("current_relation", {})
                print(f"        関係: {relation.get('relation')}")
                print(f"        価格差: {relation.get('price_difference', 0):.5f}")

            else:
                print(f"      ❌ 検出なし")


if __name__ == "__main__":
    asyncio.run(main())
