"""
パターン15 V3 傾き分析と最適化スクリプト

バッファ縮小1を採用し、長期間データで傾き（slope）に焦点を当てた分析
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


class Pattern15V3SlopeAnalyzer:
    """パターン15 V3 傾き分析器"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
            {"name": "2年", "days": 730},
        ]
        
        # バッファ縮小1設定（採用）
        self.optimized_settings = {
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
        }

    async def analyze_slope_patterns(self) -> Dict:
        """傾きパターンの分析"""
        logger.info("=== パターン15 V3 傾き分析開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # データベース情報取得
            db_info = await self._get_database_info()
            
            # 長期間データでの傾き分析
            slope_analysis = await self._analyze_long_term_slopes()
            
            # 最適化された設定でのテスト
            optimization_results = await self._test_optimized_settings()

            # データベース接続終了
            await db_manager.close()

            return {
                "database_info": db_info,
                "slope_analysis": slope_analysis,
                "optimization_results": optimization_results,
                "analysis_time": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"傾き分析エラー: {e}")
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
                    "start_date": start_date.isoformat() if start_date else None,
                    "end_date": end_date.isoformat() if end_date else None,
                    "data_span_days": (
                        (end_date - start_date).days if start_date and end_date else 0
                    ),
                }

        except Exception as e:
            logger.error(f"データベース情報取得エラー: {e}")
            return {"error": str(e)}

    async def _analyze_long_term_slopes(self) -> Dict:
        """長期間データでの傾き分析"""
        try:
            analysis = {}

            # 最長期間のデータ取得
            max_period = max(self.test_periods, key=lambda x: x["days"])
            data = await self._fetch_market_data(max_period["days"])
            
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"長期間傾き分析用データ: {len(data)}件")

            # 基本統計
            analysis["basic_statistics"] = self._analyze_basic_statistics(data)

            # 傾きパターン分析
            analysis["slope_patterns"] = self._analyze_slope_patterns(data)

            return analysis

        except Exception as e:
            logger.error(f"長期間傾き分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_basic_statistics(self, data: pd.DataFrame) -> Dict:
        """基本統計分析"""
        try:
            high_prices = data["High"].values
            low_prices = data["Low"].values
            close_prices = data["Close"].values

            # 価格統計
            price_stats = {
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

            # 価格変化率分析
            price_changes = np.diff(close_prices) / close_prices[:-1]
            change_stats = {
                "mean_change": float(np.mean(price_changes)),
                "std_change": float(np.std(price_changes)),
                "max_change": float(np.max(price_changes)),
                "min_change": float(np.min(price_changes)),
                "abs_mean_change": float(np.mean(np.abs(price_changes))),
                "positive_changes_ratio": float(
                    np.sum(price_changes > 0) / len(price_changes)
                ),
            }

            return {
                "price_statistics": price_stats,
                "change_statistics": change_stats,
                "data_points": len(data),
            }

        except Exception as e:
            logger.error(f"基本統計分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_slope_patterns(self, data: pd.DataFrame) -> Dict:
        """傾きパターン分析"""
        try:
            analysis = {}

            close_prices = data["Close"].values

            # 線形回帰による全体傾き
            x = np.arange(len(close_prices))
            slope, intercept = np.polyfit(x, close_prices, 1)
            
            analysis["overall_trend"] = {
                "slope": float(slope),
                "intercept": float(intercept),
                "slope_per_day": float(slope),
                "slope_percentage": float(slope / np.mean(close_prices) * 100),
                "trend_direction": "上昇" if slope > 0 else "下降" if slope < 0 else "横ばい",
                "trend_strength": abs(slope) / np.std(close_prices),
            }

            # セグメント別傾き分析
            segment_size = len(close_prices) // 4
            segment_slopes = {}

            for i in range(4):
                start_idx = i * segment_size
                end_idx = (i + 1) * segment_size if i < 3 else len(close_prices)
                
                segment_prices = close_prices[start_idx:end_idx]
                segment_x = np.arange(len(segment_prices))
                
                if len(segment_prices) > 1:
                    seg_slope, seg_intercept = np.polyfit(segment_x, segment_prices, 1)
                    
                    segment_slopes[f"segment_{i+1}"] = {
                        "slope": float(seg_slope),
                        "intercept": float(seg_intercept),
                        "trend_direction": "上昇" if seg_slope > 0 else "下降" if seg_slope < 0 else "横ばい",
                        "data_points": len(segment_prices),
                    }

            analysis["segment_slopes"] = segment_slopes

            return analysis

        except Exception as e:
            logger.error(f"傾きパターン分析エラー: {e}")
            return {"error": str(e)}

    async def _test_optimized_settings(self) -> Dict:
        """最適化された設定でのテスト"""
        try:
            results = {}

            for timeframe in self.timeframes:
                logger.info(f"最適化設定テスト: {timeframe}")
                timeframe_results = {}

                for period in self.test_periods:
                    logger.info(f"  期間: {period['name']}")
                    result = await self._test_with_optimized_settings(
                        timeframe, period
                    )
                    timeframe_results[period["name"]] = result

                # 時間足別統計
                timeframe_stats = self._analyze_timeframe_statistics(timeframe_results)
                timeframe_results["statistics"] = timeframe_stats

                results[timeframe] = timeframe_results

            return results

        except Exception as e:
            logger.error(f"最適化設定テストエラー: {e}")
            return {"error": str(e)}

    async def _test_with_optimized_settings(
        self, timeframe: str, period: Dict
    ) -> Dict:
        """最適化された設定でのテスト"""
        try:
            # データ取得
            data = await self._fetch_market_data(period["days"])
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"    取得データ: {len(data)}件")

            # 最適化されたデテクター作成
            detector = self._create_optimized_detector(timeframe)

            # パターン検出
            detection = detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_with_slope_details(
                    detection, data, timeframe, period
                )
                return {
                    "detected": True,
                    "detection": detection,
                    "analysis": detailed_analysis,
                    "data_points": len(data),
                    "period_days": period["days"],
                    "settings": self.optimized_settings[timeframe],
                }
            else:
                return {
                    "detected": False,
                    "data_points": len(data),
                    "period_days": period["days"],
                    "settings": self.optimized_settings[timeframe],
                }

        except Exception as e:
            logger.error(f"最適化設定テストエラー: {e}")
            return {"error": str(e)}

    def _create_optimized_detector(self, timeframe: str) -> SupportResistanceDetectorV3:
        """最適化されたデテクター作成"""
        detector = SupportResistanceDetectorV3(timeframe)
        
        # バッファ縮小1設定を適用
        settings = self.optimized_settings[timeframe]
        detector.min_peaks = settings["min_peaks"]
        detector.buffer_percentile = settings["buffer_percentile"]
        detector.min_line_strength = settings["min_line_strength"]
        detector.max_angle = settings["max_angle"]
        detector.price_tolerance = settings["price_tolerance"]
        
        return detector

    def _analyze_detection_with_slope_details(
        self, detection: Dict, data: pd.DataFrame, timeframe: str, period: Dict
    ) -> Dict:
        """傾き詳細を含む検出分析"""
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
                "settings": self.optimized_settings[timeframe],
            }

            # 数学的パラメータ（傾き重視）
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

            # 傾きの詳細分析
            analysis["slope_analysis"] = self._analyze_slope_details(
                equation, data, pattern_data, timeframe
            )

            # バッファ分析
            analysis["buffer_analysis"] = self._analyze_buffer_effectiveness(
                data, pattern_data, self.optimized_settings[timeframe]
            )

            return analysis

        except Exception as e:
            logger.error(f"傾き詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_slope_details(
        self, equation: Dict, data: pd.DataFrame, pattern_data: Dict, timeframe: str
    ) -> Dict:
        """傾きの詳細分析"""
        try:
            analysis = {}

            slope = equation.get("slope", 0)
            angle = equation.get("angle", 0)

            # 傾きの基本情報
            analysis["slope_basic"] = {
                "slope_value": slope,
                "angle_degrees": angle,
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

            # 傾きの理由分析
            analysis["slope_reasons"] = {
                "price_stability": price_consistency["price_range_ratio"] < 0.01,
                "peak_uniformity": len(peaks) > 0
                and analysis.get("peak_analysis", {}).get("peak_price_std", 1) < 0.001,
                "trough_uniformity": len(troughs) > 0
                and analysis.get("trough_analysis", {}).get("trough_price_std", 1) < 0.001,
                "timeframe_effect": timeframe in ["1h", "1d"],
                "slope_magnitude": abs(slope) < 0.001,  # 傾きが非常に小さい
            }

            return analysis

        except Exception as e:
            logger.error(f"傾き詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_buffer_effectiveness(
        self, data: pd.DataFrame, pattern_data: Dict, settings: Dict
    ) -> Dict:
        """バッファの効果分析"""
        try:
            analysis = {}

            buffer_percentile = settings["buffer_percentile"]
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
                "slope_by_period": {},
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
    analyzer = Pattern15V3SlopeAnalyzer()
    results = await analyzer.analyze_slope_patterns()
    
    if "error" in results:
        print(f"\n❌ 分析エラー: {results['error']}")
        return
    
    print("\n=== パターン15 V3 傾き分析と最適化結果 ===")
    
    # データベース情報
    db_info = results.get("database_info", {})
    if "error" not in db_info:
        print(f"\n📊 データベース情報:")
        print(f"  総レコード数: {db_info.get('total_records', 0):,}件")
        print(f"  データ期間: {db_info.get('start_date', 'N/A')} - {db_info.get('end_date', 'N/A')}")
        print(f"  データ期間: {db_info.get('data_span_days', 0)}日")
    
    # 傾き分析結果
    slope_analysis = results.get("slope_analysis", {})
    if "error" not in slope_analysis:
        print(f"\n📈 傾き分析結果:")
        
        # 基本統計
        basic_stats = slope_analysis.get("basic_statistics", {})
        if basic_stats:
            print(f"  基本統計:")
            price_stats = basic_stats.get("price_statistics", {})
            high_stats = price_stats.get("high_prices", {})
            print(f"    高値範囲: {high_stats.get('min', 0):.5f} - {high_stats.get('max', 0):.5f}")
            print(f"    価格変動係数: {high_stats.get('coefficient_of_variation', 0):.5f}")
            
            change_stats = basic_stats.get("change_statistics", {})
            print(f"    平均変化率: {change_stats.get('mean_change', 0):.6f}")
            print(f"    絶対平均変化率: {change_stats.get('abs_mean_change', 0):.6f}")
            print(f"    上昇率: {change_stats.get('positive_changes_ratio', 0):.1%}")
        
        # 傾きパターン
        slope_patterns = slope_analysis.get("slope_patterns", {})
        if slope_patterns:
            print(f"  傾きパターン:")
            
            # 全体トレンド
            overall_trend = slope_patterns.get("overall_trend", {})
            if overall_trend:
                print(f"    全体トレンド:")
                print(f"      傾き: {overall_trend.get('slope', 0):.6f}")
                print(f"      方向: {overall_trend.get('trend_direction', '')}")
                print(f"      強度: {overall_trend.get('trend_strength', 0):.3f}")
                print(f"      日次変化率: {overall_trend.get('slope_percentage', 0):.4f}%")
            
            # セグメント傾き
            segment_slopes = slope_patterns.get("segment_slopes", {})
            for seg_name, seg_data in segment_slopes.items():
                print(f"    {seg_name}:")
                print(f"      傾き: {seg_data.get('slope', 0):.6f}")
                print(f"      方向: {seg_data.get('trend_direction', '')}")
    
    # 最適化結果
    optimization_results = results.get("optimization_results", {})
    print(f"\n🔧 最適化結果（バッファ縮小1採用）:")
    
    for timeframe, timeframe_data in optimization_results.items():
        print(f"\n  {timeframe}:")
        
        tf_stats = timeframe_data.get("statistics", {})
        print(f"    検出件数: {tf_stats.get('detection_count', 0)}")
        print(f"    検出率: {tf_stats.get('detection_rate', 0):.1%}")
        
        # 詳細結果
        for period_name, result in timeframe_data.items():
            if period_name == "statistics":
                continue
                
            if result.get("detected", False):
                analysis = result.get("analysis", {})
                slope_analysis = analysis.get("slope_analysis", {})
                buffer_analysis = analysis.get("buffer_analysis", {})
                
                print(f"      {period_name}:")
                print(f"        傾き: {analysis['mathematical']['slope']:.6f} ({analysis['mathematical']['slope_description']})")
                print(f"        角度: {analysis['mathematical']['angle']:.2f}度")
                print(f"        バッファ効率: {buffer_analysis.get('detection_quality', {}).get('buffer_efficiency', 0):.3f}")
                
                slope_reasons = slope_analysis.get("slope_reasons", {})
                print(f"        価格安定性: {'✅' if slope_reasons.get('price_stability', False) else '❌'}")
                print(f"        傾きの大きさ: {'✅' if slope_reasons.get('slope_magnitude', False) else '❌'}")


if __name__ == "__main__":
    asyncio.run(main())
