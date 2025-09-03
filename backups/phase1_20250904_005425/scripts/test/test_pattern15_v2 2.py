"""
パターン15 V2 テストスクリプト

根本的再実装された角度付きサポート/レジスタンスライン検出器をテストする
"""

import asyncio
import logging
from datetime import datetime
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


class Pattern15V2Tester:
    """パターン15 V2 テスター"""

    def __init__(self):
        self.detector = SupportResistanceDetectorV2()

    async def test_pattern15_v2(self) -> Dict:
        """パターン15 V2のテスト実行"""
        logger.info("=== パターン15 V2 テスト開始 ===")

        try:
            # データベース接続
            await db_manager.initialize("sqlite+aiosqlite:///./data/exchange_analytics.db")
            logger.info("✅ データベース接続完了")

            # 複数の期間でテスト
            test_periods = [
                ("直近1週間", 7),
                ("直近2週間", 14),
                ("直近1ヶ月", 30),
                ("直近3ヶ月", 90),
            ]

            results = {}
            for period_name, days in test_periods:
                logger.info(f"テスト期間: {period_name}")
                result = await self._test_single_period(period_name, days)
                results[period_name] = result

            # データベース接続終了
            await db_manager.close()

            return results

        except Exception as e:
            logger.error(f"パターン15 V2テストエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _test_single_period(self, period_name: str, days: int) -> Dict:
        """単一期間のテスト"""
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
                detailed_analysis = self._analyze_detection(detection, data)
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
            logger.error(f"期間テストエラー: {e}")
            return {"error": str(e)}

    def _analyze_detection(self, detection: Dict, data: pd.DataFrame) -> Dict:
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
                "strategy": detection.get("strategy")
            }

            # 数学的パラメータ
            analysis["mathematical"] = {
                "slope": equation.get("slope"),
                "intercept": equation.get("intercept"),
                "angle": equation.get("angle"),
                "equation_score": equation.get("score")
            }

            # ライン強度
            analysis["strength"] = {
                "line_strength": pattern_data.get("strength"),
                "peak_count": len(pattern_data.get("peaks", [])) if detection.get("pattern_type") == "resistance_line" else len(pattern_data.get("troughs", []))
            }

            # 現在価格との関係
            analysis["current_relation"] = {
                "relation": current_analysis.get("relation"),
                "strength": current_analysis.get("strength"),
                "distance": current_analysis.get("distance"),
                "line_price": current_analysis.get("line_price"),
                "current_price": current_analysis.get("current_price")
            }

            return analysis

        except Exception as e:
            logger.error(f"検出分析エラー: {e}")
            return {"error": str(e)}

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
    tester = Pattern15V2Tester()
    results = await tester.test_pattern15_v2()
    
    if "error" in results:
        print(f"\n❌ テストエラー: {results['error']}")
        return
    
    print("\n=== パターン15 V2 テスト結果 ===")
    
    for period_name, result in results.items():
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
            
            # 数学的パラメータ
            math_info = analysis.get("mathematical", {})
            print(f"  📐 数学的パラメータ:")
            print(f"    傾き: {math_info.get('slope', 0):.6f}")
            print(f"    角度: {math_info.get('angle', 0):.2f}度")
            print(f"    切片: {math_info.get('intercept', 0):.5f}")
            print(f"    方程式スコア: {math_info.get('equation_score', 0):.3f}")
            
            # ライン強度
            strength = analysis.get("strength", {})
            print(f"  💪 ライン強度:")
            print(f"    強度: {strength.get('line_strength', 0):.3f}")
            print(f"    ピーク数: {strength.get('peak_count', 0)}件")
            
            # 現在価格との関係
            relation = analysis.get("current_relation", {})
            print(f"  📍 現在価格との関係:")
            print(f"    関係: {relation.get('relation')}")
            print(f"    強度: {relation.get('strength', 0):.3f}")
            print(f"    距離: {relation.get('distance', 0):.3f}")
            print(f"    ライン価格: {relation.get('line_price', 0):.5f}")
            print(f"    現在価格: {relation.get('current_price', 0):.5f}")
            
        else:
            print(f"  ❌ 検出なし")


if __name__ == "__main__":
    asyncio.run(main())
