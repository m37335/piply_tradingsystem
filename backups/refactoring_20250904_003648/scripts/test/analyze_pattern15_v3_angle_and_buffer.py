"""
パターン15 V3 角度分析とバッファ調整スクリプト

角度が水平に近い理由の分析と、バッファのさらなる調整
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict

import numpy as np
import pandas as pd
from scipy.signal import find_peaks
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


class Pattern15V3AngleAndBufferAnalyzer:
    """パターン15 V3 角度分析とバッファ調整器"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "3ヶ月", "days": 90},
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
        ]

        # バッファ調整パターン（より細かい調整）
        self.buffer_adjustment_patterns = [
            {
                "name": "現在設定",
                "adjustments": {
                    "5m": {
                        "buffer_percentile": 20,
                        "min_peaks": 2,
                        "min_line_strength": 0.4,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                    "1h": {
                        "buffer_percentile": 15,
                        "min_peaks": 3,
                        "min_line_strength": 0.6,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                    "1d": {
                        "buffer_percentile": 10,
                        "min_peaks": 4,
                        "min_line_strength": 0.8,
                        "max_angle": 20,
                        "price_tolerance": 0.002,
                    },
                },
            },
            {
                "name": "バッファ拡大1",
                "adjustments": {
                    "5m": {
                        "buffer_percentile": 35,
                        "min_peaks": 2,
                        "min_line_strength": 0.3,
                        "max_angle": 60,
                        "price_tolerance": 0.008,
                    },
                    "1h": {
                        "buffer_percentile": 30,
                        "min_peaks": 2,
                        "min_line_strength": 0.5,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                    "1d": {
                        "buffer_percentile": 25,
                        "min_peaks": 3,
                        "min_line_strength": 0.7,
                        "max_angle": 30,
                        "price_tolerance": 0.003,
                    },
                },
            },
            {
                "name": "バッファ拡大2",
                "adjustments": {
                    "5m": {
                        "buffer_percentile": 50,
                        "min_peaks": 1,
                        "min_line_strength": 0.2,
                        "max_angle": 75,
                        "price_tolerance": 0.01,
                    },
                    "1h": {
                        "buffer_percentile": 40,
                        "min_peaks": 2,
                        "min_line_strength": 0.4,
                        "max_angle": 60,
                        "price_tolerance": 0.008,
                    },
                    "1d": {
                        "buffer_percentile": 35,
                        "min_peaks": 2,
                        "min_line_strength": 0.6,
                        "max_angle": 45,
                        "price_tolerance": 0.005,
                    },
                },
            },
            {
                "name": "バッファ縮小1",
                "adjustments": {
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
        ]

    async def analyze_angle_and_buffer(self) -> Dict:
        """角度分析とバッファ調整"""
        logger.info("=== パターン15 V3 角度分析とバッファ調整開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 角度分析
            angle_analysis = await self._analyze_angle_reasons()

            # バッファ調整テスト
            buffer_results = await self._test_buffer_adjustments()

            # データベース接続終了
            await db_manager.close()

            return {
                "angle_analysis": angle_analysis,
                "buffer_results": buffer_results,
                "analysis_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"角度分析とバッファ調整エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _analyze_angle_reasons(self) -> Dict:
        """角度が水平に近い理由の分析"""
        try:
            analysis = {}

            # データ取得（1年分）
            data = await self._fetch_market_data(365)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"角度分析用データ: {len(data)}件")

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
                    "coefficient_of_variation": float(
                        np.std(high_prices) / np.mean(high_prices)
                    ),
                },
                "low_prices": {
                    "min": float(np.min(low_prices)),
                    "max": float(np.max(low_prices)),
                    "mean": float(np.mean(low_prices)),
                    "std": float(np.std(low_prices)),
                    "range": float(np.max(low_prices) - np.min(low_prices)),
                    "coefficient_of_variation": float(
                        np.std(low_prices) / np.mean(low_prices)
                    ),
                },
                "close_prices": {
                    "min": float(np.min(close_prices)),
                    "max": float(np.max(close_prices)),
                    "mean": float(np.mean(close_prices)),
                    "std": float(np.std(close_prices)),
                    "range": float(np.max(close_prices) - np.min(close_prices)),
                    "coefficient_of_variation": float(
                        np.std(close_prices) / np.mean(close_prices)
                    ),
                },
            }

            # 価格変動の分析
            analysis["price_volatility"] = self._analyze_price_volatility(close_prices)

            # 極値の分析
            analysis["extremum_analysis"] = self._analyze_extremums(
                high_prices, low_prices
            )

            return analysis

        except Exception as e:
            logger.error(f"角度分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_price_volatility(self, prices: np.ndarray) -> Dict:
        """価格変動の分析"""
        try:
            analysis = {}

            # 価格変化率
            price_changes = np.diff(prices) / prices[:-1]

            analysis["price_changes"] = {
                "mean_change": float(np.mean(price_changes)),
                "std_change": float(np.std(price_changes)),
                "max_change": float(np.max(price_changes)),
                "min_change": float(np.min(price_changes)),
                "abs_mean_change": float(np.mean(np.abs(price_changes))),
            }

            # レンジ分析
            rolling_ranges = []
            for i in range(20, len(prices)):
                window = prices[i - 20 : i]
                rolling_ranges.append(np.max(window) - np.min(window))

            analysis["range_analysis"] = {
                "mean_rolling_range": float(np.mean(rolling_ranges)),
                "std_rolling_range": float(np.std(rolling_ranges)),
                "range_stability": float(
                    np.std(rolling_ranges) / np.mean(rolling_ranges)
                ),
            }

            return analysis

        except Exception as e:
            logger.error(f"価格変動分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_extremums(
        self, high_prices: np.ndarray, low_prices: np.ndarray
    ) -> Dict:
        """極値の分析"""
        try:
            analysis = {}

            # 高値の極大値
            high_peaks, _ = find_peaks(high_prices, distance=5)
            if len(high_peaks) > 0:
                peak_prices = high_prices[high_peaks]
                peak_intervals = np.diff(high_peaks)

                analysis["high_peaks"] = {
                    "count": len(high_peaks),
                    "mean_price": float(np.mean(peak_prices)),
                    "std_price": float(np.std(peak_prices)),
                    "price_range": float(np.max(peak_prices) - np.min(peak_prices)),
                    "mean_interval": float(np.mean(peak_intervals)),
                    "std_interval": float(np.std(peak_intervals)),
                }

            # 安値の極小値
            low_peaks, _ = find_peaks(-low_prices, distance=5)
            if len(low_peaks) > 0:
                trough_prices = low_prices[low_peaks]
                trough_intervals = np.diff(low_peaks)

                analysis["low_troughs"] = {
                    "count": len(low_peaks),
                    "mean_price": float(np.mean(trough_prices)),
                    "std_price": float(np.std(trough_prices)),
                    "price_range": float(np.max(trough_prices) - np.min(trough_prices)),
                    "mean_interval": float(np.mean(trough_intervals)),
                    "std_interval": float(np.std(trough_intervals)),
                }

            return analysis

        except Exception as e:
            logger.error(f"極値分析エラー: {e}")
            return {"error": str(e)}

    async def _test_buffer_adjustments(self) -> Dict:
        """バッファ調整のテスト"""
        try:
            results = {}

            for pattern in self.buffer_adjustment_patterns:
                logger.info(f"バッファ調整テスト: {pattern['name']}")
                pattern_results = {}

                for timeframe in self.timeframes:
                    logger.info(f"  時間足: {timeframe}")
                    timeframe_results = {}

                    for period in self.test_periods:
                        logger.info(f"    期間: {period['name']}")
                        result = await self._test_with_buffer_adjustment(
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

            return results

        except Exception as e:
            logger.error(f"バッファ調整テストエラー: {e}")
            return {"error": str(e)}

    async def _test_with_buffer_adjustment(
        self, timeframe: str, period: Dict, adjustments: Dict
    ) -> Dict:
        """バッファ調整でのテスト"""
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
                detailed_analysis = self._analyze_detection_with_angle_details(
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
            logger.error(f"バッファ調整テストエラー: {e}")
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

    def _analyze_detection_with_angle_details(
        self,
        detection: Dict,
        data: pd.DataFrame,
        timeframe: str,
        period: Dict,
        adjustments: Dict,
    ) -> Dict:
        """角度詳細を含む検出分析"""
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

            # 角度の詳細分析
            analysis["angle_analysis"] = self._analyze_angle_reasons_detailed(
                equation, data, pattern_data
            )

            # バッファ分析
            analysis["buffer_analysis"] = self._analyze_buffer_effectiveness(
                data, pattern_data, adjustments
            )

            return analysis

        except Exception as e:
            logger.error(f"角度詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_angle_reasons_detailed(
        self, equation: Dict, data: pd.DataFrame, pattern_data: Dict
    ) -> Dict:
        """角度が水平に近い理由の詳細分析"""
        try:
            analysis = {}

            angle = equation.get("angle", 0)
            slope = equation.get("slope", 0)

            # 角度の基本情報
            analysis["angle_basic"] = {
                "angle_degrees": angle,
                "slope": slope,
                "angle_abs": abs(angle),
                "is_horizontal": abs(angle) < 5,
                "is_vertical": abs(angle) > 85,
            }

            # 価格データの分析
            high_prices = data["High"].values
            low_prices = data["Low"].values
            close_prices = data["Close"].values

            # 価格の一貫性分析
            price_consistency = {
                "high_price_std": float(np.std(high_prices)),
                "low_price_std": float(np.std(low_prices)),
                "close_price_std": float(np.std(close_prices)),
                "price_range": float(np.max(high_prices) - np.min(low_prices)),
                "price_range_ratio": float(
                    (np.max(high_prices) - np.min(low_prices)) / np.mean(close_prices)
                ),
            }

            analysis["price_consistency"] = price_consistency

            # 極値の分析
            peaks = pattern_data.get("peaks", [])
            troughs = pattern_data.get("troughs", [])

            if peaks:
                peak_prices = [high_prices[i] for i in peaks]
                analysis["peak_analysis"] = {
                    "peak_prices": peak_prices,
                    "peak_price_std": float(np.std(peak_prices)),
                    "peak_price_range": float(
                        np.max(peak_prices) - np.min(peak_prices)
                    ),
                    "peak_price_mean": float(np.mean(peak_prices)),
                }

            if troughs:
                trough_prices = [low_prices[i] for i in troughs]
                analysis["trough_analysis"] = {
                    "trough_prices": trough_prices,
                    "trough_price_std": float(np.std(trough_prices)),
                    "trough_price_range": float(
                        np.max(trough_prices) - np.min(trough_prices)
                    ),
                    "trough_price_mean": float(np.mean(trough_prices)),
                }

            # 角度の理由分析
            analysis["angle_reasons"] = {
                "price_stability": price_consistency["price_range_ratio"]
                < 0.01,  # 価格が安定している
                "peak_uniformity": len(peaks) > 0
                and analysis.get("peak_analysis", {}).get("peak_price_std", 1)
                < 0.001,  # ピークが均一
                "trough_uniformity": len(troughs) > 0
                and analysis.get("trough_analysis", {}).get("trough_price_std", 1)
                < 0.001,  # ボトムが均一
                "timeframe_effect": timeframe in ["1h", "1d"],  # 時間足の影響
            }

            return analysis

        except Exception as e:
            logger.error(f"角度理由詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_buffer_effectiveness(
        self, data: pd.DataFrame, pattern_data: Dict, adjustments: Dict
    ) -> Dict:
        """バッファの効果分析"""
        try:
            analysis = {}

            buffer_percentile = adjustments["buffer_percentile"]
            high_prices = data["High"].values
            low_prices = data["Low"].values

            # バッファサイズの効果
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
                "high_buffer_ratio": float(high_buffer_points / len(high_prices)),
                "low_buffer_ratio": float(low_buffer_points / len(low_prices)),
                "total_buffer_points": int(high_buffer_points + low_buffer_points),
            }

            # バッファサイズと検出品質の関係
            peaks = pattern_data.get("peaks", [])
            troughs = pattern_data.get("troughs", [])

            analysis["detection_quality"] = {
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
            }

            return analysis

        except Exception as e:
            logger.error(f"バッファ効果分析エラー: {e}")
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
                "angle_by_period": {},
                "buffer_efficiency_by_period": {},
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

                    # 角度統計
                    angle = result["analysis"]["mathematical"]["angle"]
                    if period_name not in stats["angle_by_period"]:
                        stats["angle_by_period"][period_name] = []
                    stats["angle_by_period"][period_name].append(angle)

                    # バッファ効率統計
                    buffer_efficiency = result["analysis"]["buffer_analysis"][
                        "detection_quality"
                    ]["buffer_efficiency"]
                    if period_name not in stats["buffer_efficiency_by_period"]:
                        stats["buffer_efficiency_by_period"][period_name] = []
                    stats["buffer_efficiency_by_period"][period_name].append(
                        buffer_efficiency
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
        """調整パターン別統計分析"""
        try:
            stats = {
                "total_timeframes": len(pattern_results),
                "total_detections": 0,
                "overall_detection_rate": 0.0,
                "timeframe_detection_summary": {},
                "best_performing_timeframe": None,
                "highest_confidence": 0.0,
                "average_angle": 0.0,
                "average_buffer_efficiency": 0.0,
            }

            total_periods = 0
            timeframe_performance = {}
            all_angles = []
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

                # 角度とバッファ効率の収集
                angle_by_period = timeframe_stats.get("angle_by_period", {})
                buffer_efficiency_by_period = timeframe_stats.get(
                    "buffer_efficiency_by_period", {}
                )

                for period_name, angles in angle_by_period.items():
                    all_angles.extend(angles)

                for period_name, efficiencies in buffer_efficiency_by_period.items():
                    all_buffer_efficiencies.extend(efficiencies)

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

            # 平均角度とバッファ効率
            if all_angles:
                stats["average_angle"] = sum(all_angles) / len(all_angles)
            if all_buffer_efficiencies:
                stats["average_buffer_efficiency"] = sum(all_buffer_efficiencies) / len(
                    all_buffer_efficiencies
                )

            return stats

        except Exception as e:
            logger.error(f"調整パターン統計分析エラー: {e}")
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
    analyzer = Pattern15V3AngleAndBufferAnalyzer()
    results = await analyzer.analyze_angle_and_buffer()

    if "error" in results:
        print(f"\n❌ 分析エラー: {results['error']}")
        return

    print("\n=== パターン15 V3 角度分析とバッファ調整結果 ===")

    # 角度分析結果
    angle_analysis = results.get("angle_analysis", {})
    if "error" not in angle_analysis:
        print(f"\n📐 角度分析結果:")

        # 価格統計
        price_stats = angle_analysis.get("price_statistics", {})
        if price_stats:
            print(f"  価格統計:")
            high_stats = price_stats.get("high_prices", {})
            print(f"    高値:")
            print(
                f"      範囲: {high_stats.get('min', 0):.5f} - {high_stats.get('max', 0):.5f}"
            )
            print(f"      変動係数: {high_stats.get('coefficient_of_variation', 0):.5f}")

            low_stats = price_stats.get("low_prices", {})
            print(f"    安値:")
            print(
                f"      範囲: {low_stats.get('min', 0):.5f} - {low_stats.get('max', 0):.5f}"
            )
            print(f"      変動係数: {low_stats.get('coefficient_of_variation', 0):.5f}")

        # 価格変動分析
        volatility = angle_analysis.get("price_volatility", {})
        if volatility:
            print(f"  価格変動分析:")
            changes = volatility.get("price_changes", {})
            print(f"    平均変化率: {changes.get('mean_change', 0):.6f}")
            print(f"    絶対平均変化率: {changes.get('abs_mean_change', 0):.6f}")

            range_analysis = volatility.get("range_analysis", {})
            print(f"    レンジ安定性: {range_analysis.get('range_stability', 0):.5f}")

        # 極値分析
        extremum = angle_analysis.get("extremum_analysis", {})
        if extremum:
            print(f"  極値分析:")
            high_peaks = extremum.get("high_peaks", {})
            if high_peaks:
                print(f"    高値ピーク数: {high_peaks.get('count', 0)}")
                print(f"    高値ピーク価格範囲: {high_peaks.get('price_range', 0):.5f}")

            low_troughs = extremum.get("low_troughs", {})
            if low_troughs:
                print(f"    安値ボトム数: {low_troughs.get('count', 0)}")
                print(f"    安値ボトム価格範囲: {low_troughs.get('price_range', 0):.5f}")

    # バッファ調整結果
    buffer_results = results.get("buffer_results", {})
    print(f"\n🔧 バッファ調整結果:")

    for pattern_name, pattern_results in buffer_results.items():
        print(f"\n  {pattern_name}:")

        pattern_stats = pattern_results.get("statistics", {})
        print(f"    総検出件数: {pattern_stats.get('total_detections', 0)}")
        print(f"    全体検出率: {pattern_stats.get('overall_detection_rate', 0):.1%}")
        print(f"    最高信頼度: {pattern_stats.get('highest_confidence', 0):.3f}")
        print(f"    平均角度: {pattern_stats.get('average_angle', 0):.2f}度")
        print(f"    平均バッファ効率: {pattern_stats.get('average_buffer_efficiency', 0):.3f}")

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
                    angle_analysis = analysis.get("angle_analysis", {})
                    buffer_analysis = analysis.get("buffer_analysis", {})

                    print(f"        {period_name}:")
                    print(f"          角度: {analysis['mathematical']['angle']:.2f}度")
                    print(
                        f"          バッファ効率: {buffer_analysis.get('detection_quality', {}).get('buffer_efficiency', 0):.3f}"
                    )

                    angle_reasons = angle_analysis.get("angle_reasons", {})
                    print(
                        f"          価格安定性: {'✅' if angle_reasons.get('price_stability', False) else '❌'}"
                    )
                    print(
                        f"          ピーク均一性: {'✅' if angle_reasons.get('peak_uniformity', False) else '❌'}"
                    )


if __name__ == "__main__":
    asyncio.run(main())
