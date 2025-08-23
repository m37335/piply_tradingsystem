"""
パターン15 V3 時間足別テストスクリプト

時間足別最適化版パターン15 V3を各時間足でテストする
"""

import asyncio
import logging
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector_v3 import SupportResistanceDetectorV3
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15V3TimeframeTester:
    """パターン15 V3 時間足別テスター"""

    def __init__(self):
        self.timeframes = ["5m", "1h", "1d"]

    async def test_all_timeframes(self) -> Dict:
        """全時間足でのテスト実行"""
        logger.info("=== パターン15 V3 時間足別テスト開始 ===")

        try:
            # データベース接続
            await db_manager.initialize("sqlite+aiosqlite:///./data/exchange_analytics.db")
            logger.info("✅ データベース接続完了")

            results = {}
            for timeframe in self.timeframes:
                logger.info(f"テスト時間足: {timeframe}")
                result = await self._test_single_timeframe(timeframe)
                results[timeframe] = result

            # 統計分析
            statistics = self._analyze_timeframe_statistics(results)

            # データベース接続終了
            await db_manager.close()

            return {
                "timeframe_results": results,
                "statistics": statistics
            }

        except Exception as e:
            logger.error(f"パターン15 V3時間足別テストエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _test_single_timeframe(self, timeframe: str) -> Dict:
        """単一時間足のテスト"""
        try:
            # 時間足別のデータ量を設定
            if timeframe == "5m":
                data_days = 30  # 5分足: 30日分
            elif timeframe == "1h":
                data_days = 90  # 1時間足: 90日分
            else:  # 1d
                data_days = 365  # 日足: 1年分

            # データ取得
            data = await self._fetch_market_data(data_days)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"  取得データ: {len(data)}件")

            # 時間足別デテクター作成
            detector = SupportResistanceDetectorV3(timeframe)

            # パターン検出
            detection = detector.detect(data)

            if detection:
                # 詳細分析
                detailed_analysis = self._analyze_detection_detailed(detection, data, timeframe)
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
            logger.error(f"時間足テストエラー: {e}")
            return {"error": str(e)}

    def _analyze_detection_detailed(self, detection: Dict, data: pd.DataFrame, timeframe: str) -> Dict:
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
                "timeframe": timeframe
            }

            # 時間足別パラメータ
            analysis["timeframe_parameters"] = {
                "min_peaks": pattern_data.get("timeframe") == "5m" and 2 or (pattern_data.get("timeframe") == "1h" and 3 or 4),
                "analysis_period": pattern_data.get("timeframe") == "5m" and 60 or (pattern_data.get("timeframe") == "1h" and 168 or 60),
                "buffer_percentile": pattern_data.get("timeframe") == "5m" and 20 or (pattern_data.get("timeframe") == "1h" and 15 or 10),
                "min_line_strength": pattern_data.get("timeframe") == "5m" and 0.4 or (pattern_data.get("timeframe") == "1h" and 0.6 or 0.8),
                "max_angle": pattern_data.get("timeframe") == "5m" and 45 or (pattern_data.get("timeframe") == "1h" and 30 or 20)
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
                "data_points": len(data),
                "timeframe": timeframe
            }

            return analysis

        except Exception as e:
            logger.error(f"検出詳細分析エラー: {e}")
            return {"error": str(e)}

    def _analyze_timeframe_statistics(self, results: Dict) -> Dict:
        """時間足別統計分析"""
        try:
            stats = {
                "total_timeframes": len(results),
                "detection_count": 0,
                "detection_rate": 0.0,
                "timeframe_detections": {},
                "confidence_by_timeframe": {},
                "strength_by_timeframe": {},
                "angle_by_timeframe": {},
                "relation_by_timeframe": {}
            }

            for timeframe, result in results.items():
                if result.get("detected", False):
                    stats["detection_count"] += 1
                    stats["timeframe_detections"][timeframe] = True
                    
                    # 信頼度統計
                    confidence = result["detection"].get("confidence_score", 0)
                    if timeframe not in stats["confidence_by_timeframe"]:
                        stats["confidence_by_timeframe"][timeframe] = []
                    stats["confidence_by_timeframe"][timeframe].append(confidence)
                    
                    # 強度統計
                    strength = result["analysis"]["strength"]["line_strength"]
                    if timeframe not in stats["strength_by_timeframe"]:
                        stats["strength_by_timeframe"][timeframe] = []
                    stats["strength_by_timeframe"][timeframe].append(strength)
                    
                    # 角度統計
                    angle = result["analysis"]["mathematical"]["angle"]
                    if timeframe not in stats["angle_by_timeframe"]:
                        stats["angle_by_timeframe"][timeframe] = []
                    stats["angle_by_timeframe"][timeframe].append(angle)
                    
                    # 関係性統計
                    relation = result["analysis"]["current_relation"]["relation"]
                    if timeframe not in stats["relation_by_timeframe"]:
                        stats["relation_by_timeframe"][timeframe] = {}
                    stats["relation_by_timeframe"][timeframe][relation] = stats["relation_by_timeframe"][timeframe].get(relation, 0) + 1
                else:
                    stats["timeframe_detections"][timeframe] = False

            # 検出率計算
            stats["detection_rate"] = stats["detection_count"] / stats["total_timeframes"]

            # 時間足別平均値計算
            for timeframe in stats["confidence_by_timeframe"]:
                stats["confidence_by_timeframe"][timeframe] = sum(stats["confidence_by_timeframe"][timeframe]) / len(stats["confidence_by_timeframe"][timeframe])

            for timeframe in stats["strength_by_timeframe"]:
                stats["strength_by_timeframe"][timeframe] = sum(stats["strength_by_timeframe"][timeframe]) / len(stats["strength_by_timeframe"][timeframe])

            for timeframe in stats["angle_by_timeframe"]:
                stats["angle_by_timeframe"][timeframe] = sum(stats["angle_by_timeframe"][timeframe]) / len(stats["angle_by_timeframe"][timeframe])

            return stats

        except Exception as e:
            logger.error(f"時間足別統計分析エラー: {e}")
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
    tester = Pattern15V3TimeframeTester()
    results = await tester.test_all_timeframes()
    
    if "error" in results:
        print(f"\n❌ テストエラー: {results['error']}")
        return
    
    print("\n=== パターン15 V3 時間足別テスト結果 ===")
    
    # 統計サマリー
    statistics = results.get("statistics", {})
    print(f"\n📊 統計サマリー:")
    print(f"  テスト時間足数: {statistics.get('total_timeframes', 0)}")
    print(f"  検出件数: {statistics.get('detection_count', 0)}")
    print(f"  検出率: {statistics.get('detection_rate', 0):.1%}")
    
    # 時間足別検出状況
    timeframe_detections = statistics.get("timeframe_detections", {})
    if timeframe_detections:
        print(f"  時間足別検出状況:")
        for timeframe, detected in timeframe_detections.items():
            status = "✅ 検出" if detected else "❌ 未検出"
            print(f"    {timeframe}: {status}")
    
    # 時間足別信頼度
    confidence_by_timeframe = statistics.get("confidence_by_timeframe", {})
    if confidence_by_timeframe:
        print(f"  時間足別平均信頼度:")
        for timeframe, confidence in confidence_by_timeframe.items():
            print(f"    {timeframe}: {confidence:.3f}")
    
    # 時間足別強度
    strength_by_timeframe = statistics.get("strength_by_timeframe", {})
    if strength_by_timeframe:
        print(f"  時間足別平均強度:")
        for timeframe, strength in strength_by_timeframe.items():
            print(f"    {timeframe}: {strength:.3f}")
    
    # 時間足別角度
    angle_by_timeframe = statistics.get("angle_by_timeframe", {})
    if angle_by_timeframe:
        print(f"  時間足別平均角度:")
        for timeframe, angle in angle_by_timeframe.items():
            print(f"    {timeframe}: {angle:.2f}度")
    
    # 詳細結果
    print(f"\n📋 詳細結果:")
    timeframe_results = results.get("timeframe_results", {})
    
    for timeframe, result in timeframe_results.items():
        if "error" in result:
            print(f"\n❌ {timeframe}: {result['error']}")
            continue
            
        print(f"\n📊 {timeframe} ({result['data_points']}件):")
        
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
            
            # 時間足別パラメータ
            tf_params = analysis.get("timeframe_parameters", {})
            print(f"  ⚙️ 時間足別パラメータ:")
            print(f"    最小ピーク数: {tf_params.get('min_peaks')}")
            print(f"    分析期間: {tf_params.get('analysis_period')}ポイント")
            print(f"    バッファ百分位: {tf_params.get('buffer_percentile')}%")
            print(f"    最小ライン強度: {tf_params.get('min_line_strength')}")
            print(f"    最大角度: {tf_params.get('max_angle')}度")
            
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
            print(f"    時間足: {timing.get('timeframe', '')}")
            
        else:
            print(f"  ❌ 検出なし")


if __name__ == "__main__":
    asyncio.run(main())
