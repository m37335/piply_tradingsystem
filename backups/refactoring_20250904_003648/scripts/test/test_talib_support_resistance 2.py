"""
TA-Libを使用したサポート/レジスタンスライン検出テスト

TA-Libの線形回帰機能（LINEARREG, LINEARREG_SLOPE, LINEARREG_INTERCEPT）を使用
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import talib
from sqlalchemy import text

from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TALibSupportResistanceTester:
    """TA-Libサポート/レジスタンス検出テスター"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]
        self.test_periods = [
            {"name": "1ヶ月", "days": 30},
            {"name": "3ヶ月", "days": 90},
            {"name": "6ヶ月", "days": 180},
            {"name": "1年", "days": 365},
        ]

    async def test_talib_support_resistance(self) -> Dict:
        """TA-Libサポート/レジスタンス検出テスト"""
        logger.info("=== TA-Libサポート/レジスタンス検出テスト開始 ===")

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
            logger.error(f"TA-Libサポート/レジスタンス検出テストエラー: {e}")
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

            # TA-Libを使用したサポート/レジスタンス検出
            detections = self._detect_support_resistance_talib(data, timeframe)

            if detections:
                # 詳細分析
                detailed_analysis = self._analyze_detections_with_details(
                    detections, data, timeframe, period
                )
                return {
                    "detected": True,
                    "detections": detections,
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

    def _detect_support_resistance_talib(self, data: pd.DataFrame, timeframe: str) -> List[Dict]:
        """TA-Libを使用したサポート/レジスタンス検出"""
        try:
            detections = []
            
            # 価格データの準備
            high_prices = data['High'].values
            low_prices = data['Low'].values
            close_prices = data['Close'].values
            
            # 異なる時間期間での線形回帰
            time_periods = [14, 20, 30, 50]
            
            for period in time_periods:
                if len(close_prices) < period:
                    continue
                
                # 高値での線形回帰（レジスタンスライン）
                resistance_detection = self._detect_resistance_line_talib(
                    high_prices, close_prices, period, timeframe
                )
                if resistance_detection:
                    detections.append(resistance_detection)
                
                # 安値での線形回帰（サポートライン）
                support_detection = self._detect_support_line_talib(
                    low_prices, close_prices, period, timeframe
                )
                if support_detection:
                    detections.append(support_detection)
            
            logger.info(f"TA-Lib検出完了: {len(detections)}件")
            return detections
            
        except Exception as e:
            logger.error(f"TA-Lib検出エラー: {e}")
            return []

    def _detect_resistance_line_talib(self, high_prices: np.ndarray, close_prices: np.ndarray, 
                                    period: int, timeframe: str) -> Optional[Dict]:
        """TA-Libを使用したレジスタンスライン検出"""
        try:
            # 線形回帰の計算
            linear_reg = talib.LINEARREG(high_prices, timeperiod=period)
            slope = talib.LINEARREG_SLOPE(high_prices, timeperiod=period)
            intercept = talib.LINEARREG_INTERCEPT(high_prices, timeperiod=period)
            
            # 最新の値を使用
            current_slope = slope[-1]
            current_intercept = intercept[-1]
            current_line_value = linear_reg[-1]
            
            # 現在価格との関係
            current_price = close_prices[-1]
            
            # レジスタンスラインの条件チェック
            if current_price <= current_line_value * 1.02:  # 2%以内
                # 角度計算
                angle = np.degrees(np.arctan(current_slope))
                
                # 信頼度計算
                confidence = self._calculate_talib_confidence(
                    high_prices, linear_reg, current_price, current_line_value
                )
                
                return {
                    "line_type": "resistance",
                    "timeframe": timeframe,
                    "period": period,
                    "equation": {
                        "slope": current_slope,
                        "intercept": current_intercept,
                        "angle": angle,
                        "line_value": current_line_value
                    },
                    "current_price": current_price,
                    "confidence": confidence,
                    "relation": "BELOW_RESISTANCE" if current_price < current_line_value else "AT_RESISTANCE",
                    "distance": abs(current_price - current_line_value) / current_line_value
                }
            
            return None
            
        except Exception as e:
            logger.error(f"レジスタンスライン検出エラー: {e}")
            return None

    def _detect_support_line_talib(self, low_prices: np.ndarray, close_prices: np.ndarray, 
                                 period: int, timeframe: str) -> Optional[Dict]:
        """TA-Libを使用したサポートライン検出"""
        try:
            # 線形回帰の計算
            linear_reg = talib.LINEARREG(low_prices, timeperiod=period)
            slope = talib.LINEARREG_SLOPE(low_prices, timeperiod=period)
            intercept = talib.LINEARREG_INTERCEPT(low_prices, timeperiod=period)
            
            # 最新の値を使用
            current_slope = slope[-1]
            current_intercept = intercept[-1]
            current_line_value = linear_reg[-1]
            
            # 現在価格との関係
            current_price = close_prices[-1]
            
            # サポートラインの条件チェック
            if current_price >= current_line_value * 0.98:  # 2%以内
                # 角度計算
                angle = np.degrees(np.arctan(current_slope))
                
                # 信頼度計算
                confidence = self._calculate_talib_confidence(
                    low_prices, linear_reg, current_price, current_line_value
                )
                
                return {
                    "line_type": "support",
                    "timeframe": timeframe,
                    "period": period,
                    "equation": {
                        "slope": current_slope,
                        "intercept": current_intercept,
                        "angle": angle,
                        "line_value": current_line_value
                    },
                    "current_price": current_price,
                    "confidence": confidence,
                    "relation": "ABOVE_SUPPORT" if current_price > current_line_value else "AT_SUPPORT",
                    "distance": abs(current_price - current_line_value) / current_line_value
                }
            
            return None
            
        except Exception as e:
            logger.error(f"サポートライン検出エラー: {e}")
            return None

    def _calculate_talib_confidence(self, prices: np.ndarray, linear_reg: np.ndarray, 
                                  current_price: float, line_value: float) -> float:
        """TA-Lib検出の信頼度計算"""
        try:
            # 線形回帰の適合度を計算
            valid_reg = linear_reg[~np.isnan(linear_reg)]
            valid_prices = prices[~np.isnan(linear_reg)]
            
            if len(valid_reg) < 5:
                return 0.0
            
            # 決定係数（R²）の計算
            ss_res = np.sum((valid_prices - valid_reg) ** 2)
            ss_tot = np.sum((valid_prices - np.mean(valid_prices)) ** 2)
            
            if ss_tot == 0:
                return 0.0
            
            r_squared = 1 - (ss_res / ss_tot)
            
            # 現在価格との距離による補正
            distance_factor = 1.0 - min(abs(current_price - line_value) / line_value, 0.1)
            
            # 総合信頼度
            confidence = r_squared * distance_factor
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"信頼度計算エラー: {e}")
            return 0.0

    def _analyze_detections_with_details(self, detections: List[Dict], data: pd.DataFrame, 
                                       timeframe: str, period: Dict) -> Dict:
        """検出詳細分析"""
        try:
            analysis = {}

            # 基本統計
            analysis["basic_stats"] = {
                "total_detections": len(detections),
                "resistance_count": len([d for d in detections if d["line_type"] == "resistance"]),
                "support_count": len([d for d in detections if d["line_type"] == "support"]),
                "timeframe": timeframe,
                "period": period["name"],
            }

            # 期間別統計
            period_stats = {}
            for detection in detections:
                period_key = f"period_{detection['period']}"
                if period_key not in period_stats:
                    period_stats[period_key] = {
                        "count": 0,
                        "resistance": 0,
                        "support": 0,
                        "avg_confidence": 0.0,
                        "avg_angle": 0.0
                    }
                
                period_stats[period_key]["count"] += 1
                if detection["line_type"] == "resistance":
                    period_stats[period_key]["resistance"] += 1
                else:
                    period_stats[period_key]["support"] += 1
                
                period_stats[period_key]["avg_confidence"] += detection["confidence"]
                period_stats[period_key]["avg_angle"] += abs(detection["equation"]["angle"])
            
            # 平均値計算
            for period_key in period_stats:
                count = period_stats[period_key]["count"]
                if count > 0:
                    period_stats[period_key]["avg_confidence"] /= count
                    period_stats[period_key]["avg_angle"] /= count
            
            analysis["period_stats"] = period_stats

            # 品質分析
            if detections:
                confidences = [d["confidence"] for d in detections]
                angles = [abs(d["equation"]["angle"]) for d in detections]
                distances = [d["distance"] for d in detections]
                
                analysis["quality_analysis"] = {
                    "avg_confidence": np.mean(confidences),
                    "max_confidence": np.max(confidences),
                    "avg_angle": np.mean(angles),
                    "avg_distance": np.mean(distances),
                    "best_detection": max(detections, key=lambda x: x["confidence"])
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
                "avg_confidence_by_period": {},
                "avg_angle_by_period": {},
                "line_types": {},
            }

            for period_name, result in timeframe_results.items():
                if period_name == "statistics":
                    continue

                if result.get("detected", False):
                    stats["detection_count"] += 1
                    stats["period_detections"][period_name] = True

                    # 基本統計
                    basic_stats = result["analysis"]["basic_stats"]
                    stats["line_types"][period_name] = {
                        "resistance": basic_stats["resistance_count"],
                        "support": basic_stats["support_count"]
                    }

                    # 品質統計
                    quality_analysis = result["analysis"].get("quality_analysis", {})
                    if quality_analysis:
                        if period_name not in stats["avg_confidence_by_period"]:
                            stats["avg_confidence_by_period"][period_name] = []
                        stats["avg_confidence_by_period"][period_name].append(
                            quality_analysis["avg_confidence"]
                        )

                        if period_name not in stats["avg_angle_by_period"]:
                            stats["avg_angle_by_period"][period_name] = []
                        stats["avg_angle_by_period"][period_name].append(
                            quality_analysis["avg_angle"]
                        )
                else:
                    stats["period_detections"][period_name] = False

            # 検出率計算
            stats["detection_rate"] = stats["detection_count"] / stats["total_periods"]

            # 期間別平均値計算
            for period_name in stats["avg_confidence_by_period"]:
                stats["avg_confidence_by_period"][period_name] = sum(
                    stats["avg_confidence_by_period"][period_name]
                ) / len(stats["avg_confidence_by_period"][period_name])

            for period_name in stats["avg_angle_by_period"]:
                stats["avg_angle_by_period"][period_name] = sum(
                    stats["avg_angle_by_period"][period_name]
                ) / len(stats["avg_angle_by_period"][period_name])

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
                "average_confidence": 0.0,
                "line_type_distribution": {},
                "monthly_estimate": 0.0,
            }

            total_periods = 0
            timeframe_performance = {}
            all_confidences = []
            all_line_types = {"resistance": 0, "support": 0}

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

                # 信頼度とラインタイプの収集
                confidence_by_period = timeframe_stats.get("avg_confidence_by_period", {})
                line_types = timeframe_stats.get("line_types", {})

                for period_name, confidences in confidence_by_period.items():
                    all_confidences.extend(confidences)

                for period_name, line_type_counts in line_types.items():
                    all_line_types["resistance"] += line_type_counts.get("resistance", 0)
                    all_line_types["support"] += line_type_counts.get("support", 0)

                # 最高信頼度の追跡
                for period_name, confidences in confidence_by_period.items():
                    if confidences and max(confidences) > stats["highest_confidence"]:
                        stats["highest_confidence"] = max(confidences)

            # 全体検出率
            if total_periods > 0:
                stats["overall_detection_rate"] = stats["total_detections"] / total_periods

            # 最高パフォーマンス時間足
            if timeframe_performance:
                stats["best_performing_timeframe"] = max(
                    timeframe_performance, key=timeframe_performance.get
                )

            # 平均信頼度
            if all_confidences:
                stats["average_confidence"] = sum(all_confidences) / len(all_confidences)

            # ラインタイプ分布
            stats["line_type_distribution"] = all_line_types

            # 月間推定
            stats["monthly_estimate"] = stats["total_detections"] / 12

            return stats

        except Exception as e:
            logger.error(f"全体統計分析エラー: {e}")
            return {"error": str(e)}

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
    tester = TALibSupportResistanceTester()
    results = await tester.test_talib_support_resistance()
    
    if "error" in results:
        print(f"\n❌ テストエラー: {results['error']}")
        return
    
    print("\n=== TA-Libサポート/レジスタンス検出テスト結果 ===")
    
    # 全体統計
    overall_stats = results.get("overall_stats", {})
    print(f"\n📊 全体統計:")
    print(f"  総検出件数: {overall_stats.get('total_detections', 0)}")
    print(f"  全体検出率: {overall_stats.get('overall_detection_rate', 0):.1%}")
    print(f"  月間推定: {overall_stats.get('monthly_estimate', 0):.1f}件/月")
    print(f"  最高信頼度: {overall_stats.get('highest_confidence', 0):.3f}")
    print(f"  平均信頼度: {overall_stats.get('average_confidence', 0):.3f}")
    
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
                basic_stats = analysis.get("basic_stats", {})
                quality_analysis = analysis.get("quality_analysis", {})
                
                print(f"      {period_name}:")
                print(f"        総検出: {basic_stats['total_detections']}件")
                print(f"        レジスタンス: {basic_stats['resistance_count']}件")
                print(f"        サポート: {basic_stats['support_count']}件")
                
                if quality_analysis:
                    print(f"        平均信頼度: {quality_analysis['avg_confidence']:.3f}")
                    print(f"        最高信頼度: {quality_analysis['max_confidence']:.3f}")
                    print(f"        平均角度: {quality_analysis['avg_angle']:.2f}度")
                    
                    best_detection = quality_analysis['best_detection']
                    print(f"        最良検出: {best_detection['line_type']} (信頼度: {best_detection['confidence']:.3f})")


if __name__ == "__main__":
    asyncio.run(main())
