"""
パターン15 V2 本格検証スクリプト

実際の運用データベースを使用して、パターン15 V2の包括的な検証を実行する
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector_v2 import SupportResistanceDetectorV2
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15V2ProductionValidator:
    """パターン15 V2 本格検証器"""

    def __init__(self):
        self.detector = SupportResistanceDetectorV2()

    async def validate_pattern15_v2_production(self) -> Dict:
        """パターン15 V2の本格検証実行"""
        logger.info("=== パターン15 V2 本格検証開始 ===")

        try:
            # データベース接続
            await db_manager.initialize("sqlite+aiosqlite:///./data/exchange_analytics.db")
            logger.info("✅ データベース接続完了")

            # 複数の期間で検証
            validation_periods = [
                ("直近1週間", 7),
                ("直近2週間", 14),
                ("直近1ヶ月", 30),
                ("直近3ヶ月", 90),
                ("直近6ヶ月", 180),
                ("直近1年", 365),
            ]

            results = {}
            for period_name, days in validation_periods:
                logger.info(f"検証期間: {period_name}")
                result = await self._validate_single_period(period_name, days)
                results[period_name] = result

            # 統計分析
            statistics = self._analyze_statistics(results)

            # データベース接続終了
            await db_manager.close()

            return {
                "period_results": results,
                "statistics": statistics
            }

        except Exception as e:
            logger.error(f"パターン15 V2本格検証エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _validate_single_period(self, period_name: str, days: int) -> Dict:
        """単一期間の検証"""
        try:
            # データ取得
            data = await self._fetch_market_data(days)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"  取得データ: {len(data)}件")

            # パターン検出
            detection = self.detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_detailed(detection, data)
                return {
                    "detected": True,
                    "detection": detection,
                    "analysis": detailed_analysis,
                    "data_points": len(data)
                }
            else:
                return {
                    "detected": False,
                    "data_points": len(data)
                }

        except Exception as e:
            logger.error(f"期間検証エラー: {e}")
            return {"error": str(e)}

    def _analyze_detection_detailed(self, detection: Dict, data: pd.DataFrame) -> Dict:
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
                "entry_condition": detection.get("entry_condition")
            }

            # 数学的パラメータ
            analysis["mathematical"] = {
                "slope": equation.get("slope"),
                "intercept": equation.get("intercept"),
                "angle": equation.get("angle"),
                "equation_score": equation.get("score"),
                "angle_description": self._get_angle_description(equation.get("angle", 0))
            }

            # ライン強度
            analysis["strength"] = {
                "line_strength": pattern_data.get("strength"),
                "peak_count": len(pattern_data.get("peaks", [])) if detection.get("pattern_type") == "resistance_line" else len(pattern_data.get("troughs", [])),
                "peak_indices": pattern_data.get("peaks", [])[:5] if detection.get("pattern_type") == "resistance_line" else pattern_data.get("troughs", [])[:5]
            }

            # 現在価格との関係
            analysis["current_relation"] = {
                "relation": current_analysis.get("relation"),
                "strength": current_analysis.get("strength"),
                "distance": current_analysis.get("distance"),
                "line_price": current_analysis.get("line_price"),
                "current_price": current_analysis.get("current_price"),
                "price_difference": abs(current_analysis.get("line_price", 0) - current_analysis.get("current_price", 0))
            }

            # 時間情報
            analysis["timing"] = {
                "detection_time": detection.get("detection_time"),
                "data_period": f"{data.iloc[0]['Date']} - {data.iloc[-1]['Date']}",
                "data_points": len(data)
            }

            return analysis

        except Exception as e:
            logger.error(f"検出詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_statistics(self, results: Dict) -> Dict:
        """統計分析"""
        try:
            stats = {
                "total_periods": len(results),
                "detection_count": 0,
                "detection_rate": 0.0,
                "pattern_types": {},
                "confidence_stats": [],
                "strength_stats": [],
                "angle_stats": [],
                "relation_stats": {}
            }

            for period_name, result in results.items():
                if result.get("detected", False):
                    stats["detection_count"] += 1
                    
                    # パターンタイプ統計
                    pattern_type = result["detection"].get("pattern_type", "unknown")
                    stats["pattern_types"][pattern_type] = stats["pattern_types"].get(pattern_type, 0) + 1
                    
                    # 信頼度統計
                    confidence = result["detection"].get("confidence_score", 0)
                    stats["confidence_stats"].append(confidence)
                    
                    # 強度統計
                    strength = result["analysis"]["strength"]["line_strength"]
                    stats["strength_stats"].append(strength)
                    
                    # 角度統計
                    angle = result["analysis"]["mathematical"]["angle"]
                    stats["angle_stats"].append(angle)
                    
                    # 関係性統計
                    relation = result["analysis"]["current_relation"]["relation"]
                    stats["relation_stats"][relation] = stats["relation_stats"].get(relation, 0) + 1

            # 検出率計算
            stats["detection_rate"] = stats["detection_count"] / stats["total_periods"]

            # 統計値計算
            if stats["confidence_stats"]:
                stats["confidence_avg"] = sum(stats["confidence_stats"]) / len(stats["confidence_stats"])
                stats["confidence_min"] = min(stats["confidence_stats"])
                stats["confidence_max"] = max(stats["confidence_stats"])

            if stats["strength_stats"]:
                stats["strength_avg"] = sum(stats["strength_stats"]) / len(stats["strength_stats"])
                stats["strength_min"] = min(stats["strength_stats"])
                stats["strength_max"] = max(stats["strength_stats"])

            if stats["angle_stats"]:
                stats["angle_avg"] = sum(stats["angle_stats"]) / len(stats["angle_stats"])
                stats["angle_min"] = min(stats["angle_stats"])
                stats["angle_max"] = max(stats["angle_stats"])

            return stats

        except Exception as e:
            logger.error(f"統計分析エラー: {e}")
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
                query = text("""
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
                """)
                
                result = await session.execute(query, {"days": days})
                rows = result.fetchall()
                
                if not rows:
                    return pd.DataFrame()
                
                data = pd.DataFrame(rows, columns=[
                    "Date", "Open", "High", "Low", "Close", "Volume"
                ])
                
                data = data.sort_values("Date").reset_index(drop=True)
                return data

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return pd.DataFrame()


async def main():
    """メイン関数"""
    validator = Pattern15V2ProductionValidator()
    results = await validator.validate_pattern15_v2_production()
    
    if "error" in results:
        print(f"\n❌ 検証エラー: {results['error']}")
        return
    
    print("\n=== パターン15 V2 本格検証結果 ===")
    
    # 統計サマリー
    statistics = results.get("statistics", {})
    print(f"\n📊 統計サマリー:")
    print(f"  検証期間数: {statistics.get('total_periods', 0)}")
    print(f"  検出件数: {statistics.get('detection_count', 0)}")
    print(f"  検出率: {statistics.get('detection_rate', 0):.1%}")
    
    if statistics.get("confidence_stats"):
        print(f"  信頼度統計:")
        print(f"    平均: {statistics.get('confidence_avg', 0):.3f}")
        print(f"    最小: {statistics.get('confidence_min', 0):.3f}")
        print(f"    最大: {statistics.get('confidence_max', 0):.3f}")
    
    if statistics.get("strength_stats"):
        print(f"  ライン強度統計:")
        print(f"    平均: {statistics.get('strength_avg', 0):.3f}")
        print(f"    最小: {statistics.get('strength_min', 0):.3f}")
        print(f"    最大: {statistics.get('strength_max', 0):.3f}")
    
    if statistics.get("angle_stats"):
        print(f"  角度統計:")
        print(f"    平均: {statistics.get('angle_avg', 0):.2f}度")
        print(f"    最小: {statistics.get('angle_min', 0):.2f}度")
        print(f"    最大: {statistics.get('angle_max', 0):.2f}度")
    
    # パターンタイプ統計
    pattern_types = statistics.get("pattern_types", {})
    if pattern_types:
        print(f"  パターンタイプ分布:")
        for pattern_type, count in pattern_types.items():
            print(f"    {pattern_type}: {count}件")
    
    # 関係性統計
    relation_stats = statistics.get("relation_stats", {})
    if relation_stats:
        print(f"  現在価格との関係分布:")
        for relation, count in relation_stats.items():
            print(f"    {relation}: {count}件")
    
    # 詳細結果
    print(f"\n📋 詳細結果:")
    period_results = results.get("period_results", {})
    
    for period_name, result in period_results.items():
        if "error" in result:
            print(f"\n❌ {period_name}: {result['error']}")
            continue
            
        print(f"\n📊 {period_name} ({result['data_points']}件):")
        
        if result.get("detected", False):
            detection = result["detection"]
            analysis = result["analysis"]
            
            # 基本情報
            basic = analysis.get("basic_info", {})
            print(f"  ✅ 検出成功!")
            print(f"    パターン: {basic.get('pattern_type')}")
            print(f"    信頼度: {basic.get('confidence', 0):.3f}")
            print(f"    方向: {basic.get('direction')}")
            print(f"    戦略: {basic.get('strategy')}")
            print(f"    条件: {basic.get('entry_condition')}")
            
            # 数学的パラメータ
            math_info = analysis.get("mathematical", {})
            print(f"  📐 数学的パラメータ:")
            print(f"    傾き: {math_info.get('slope', 0):.6f}")
            print(f"    角度: {math_info.get('angle', 0):.2f}度 ({math_info.get('angle_description', '')})")
            print(f"    切片: {math_info.get('intercept', 0):.5f}")
            print(f"    方程式スコア: {math_info.get('equation_score', 0):.3f}")
            
            # ライン強度
            strength = analysis.get("strength", {})
            print(f"  💪 ライン強度:")
            print(f"    強度: {strength.get('line_strength', 0):.3f}")
            print(f"    ピーク数: {strength.get('peak_count', 0)}件")
            print(f"    ピークインデックス: {strength.get('peak_indices', [])}")
            
            # 現在価格との関係
            relation = analysis.get("current_relation", {})
            print(f"  📍 現在価格との関係:")
            print(f"    関係: {relation.get('relation')}")
            print(f"    強度: {relation.get('strength', 0):.3f}")
            print(f"    距離: {relation.get('distance', 0):.3f}")
            print(f"    価格差: {relation.get('price_difference', 0):.5f}")
            print(f"    ライン価格: {relation.get('line_price', 0):.5f}")
            print(f"    現在価格: {relation.get('current_price', 0):.5f}")
            
            # 時間情報
            timing = analysis.get("timing", {})
            print(f"  ⏰ 時間情報:")
            print(f"    検出時刻: {timing.get('detection_time', '')}")
            print(f"    データ期間: {timing.get('data_period', '')}")
            
        else:
            print(f"  ❌ 検出なし")


if __name__ == "__main__":
    asyncio.run(main())
