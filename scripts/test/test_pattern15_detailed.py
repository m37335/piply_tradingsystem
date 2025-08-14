"""
パターン15詳細テストスクリプト

レジスタンス/サポートライン検出の詳細テストと条件分析
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector import (
    SupportResistanceDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15DetailedTester:
    """パターン15詳細テスター"""

    def __init__(self):
        self.detector = SupportResistanceDetector()

    async def test_pattern15_detailed(self) -> Dict:
        """パターン15詳細テスト実行"""
        logger.info("=== パターン15詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")
            
            # テストデータ作成
            logger.info(f"パターン15用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern15_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン15検出成功！（テストケース {test_case}）")
                logger.info(f"   パターンタイプ: {result.get('pattern_type', 'unknown')}")
                logger.info(f"   方向: {result.get('direction', 'unknown')}")
                logger.info("🎉 パターン15が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern15_test_data(self, test_case: int) -> pd.DataFrame:
        """パターン15用テストデータ作成"""
        # 価格データ（レジスタンス/サポートライン）
        dates = pd.date_range(start="2024-01-01", periods=120, freq="D")

        # 価格データを作成
        prices = []
        for i in range(120):
            if test_case == 1:
                # ケース1: 標準的なレジスタンスライン
                if i < 40:
                    # レジスタンスライン付近での価格変動
                    base_price = 150.0 + i * 0.005
                    if i % 10 < 5:
                        price = base_price + 0.2  # レジスタンスライン
                    else:
                        price = base_price - 0.1
                elif i < 80:
                    # レジスタンスラインでの反発
                    base_price = 150.2
                    if i % 8 < 4:
                        price = base_price + 0.05
                    else:
                        price = base_price - 0.15
                else:
                    # ブレイクアウト
                    price = 150.25 + (i - 80) * 0.02
            elif test_case == 2:
                # ケース2: サポートライン
                if i < 40:
                    # サポートライン付近での価格変動
                    base_price = 150.0 - i * 0.005
                    if i % 10 < 5:
                        price = base_price - 0.2  # サポートライン
                    else:
                        price = base_price + 0.1
                elif i < 80:
                    # サポートラインでの反発
                    base_price = 149.8
                    if i % 8 < 4:
                        price = base_price - 0.05
                    else:
                        price = base_price + 0.15
                else:
                    # ブレイクアウト
                    price = 149.75 - (i - 80) * 0.02
            elif test_case == 3:
                # ケース3: より強いレジスタンスライン
                if i < 60:
                    # 強いレジスタンスライン
                    base_price = 150.0 + i * 0.003
                    if i % 6 < 3:
                        price = base_price + 0.15  # レジスタンスライン
                    else:
                        price = base_price - 0.08
                else:
                    # ブレイクアウト
                    price = 150.18 + (i - 60) * 0.025
            else:
                # ケース4: 複数のタッチポイント
                if i < 50:
                    # 複数回タッチするレジスタンスライン
                    base_price = 150.0 + i * 0.004
                    if i % 7 < 4:
                        price = base_price + 0.18  # レジスタンスライン
                    else:
                        price = base_price - 0.12
                elif i < 90:
                    # レジスタンスラインでの反発
                    base_price = 150.18
                    if i % 5 < 3:
                        price = base_price + 0.03
                    else:
                        price = base_price - 0.1
                else:
                    # ブレイクアウト
                    price = 150.21 + (i - 90) * 0.03

            prices.append(
                {
                    "Date": dates[i],
                    "Open": price - 0.05,
                    "High": price + 0.1,
                    "Low": price - 0.1,
                    "Close": price,
                    "Volume": 1000 + i * 10,
                }
            )

        return pd.DataFrame(prices)

    def _analyze_conditions(self, test_data: pd.DataFrame) -> Dict:
        """条件分析"""
        try:
            # 詳細な条件分析
            analysis = {}
            
            # 1. タッチポイント検出（レジスタンス）
            try:
                resistance_touch_points = self.detector._find_touch_points(test_data, "resistance")
                analysis["resistance_touch_points_count"] = len(resistance_touch_points)
                analysis["resistance_touch_points_sufficient"] = len(resistance_touch_points) >= self.detector.min_touch_points
            except Exception as e:
                analysis["resistance_touch_points_error"] = str(e)
            
            # 2. タッチポイント検出（サポート）
            try:
                support_touch_points = self.detector._find_touch_points(test_data, "support")
                analysis["support_touch_points_count"] = len(support_touch_points)
                analysis["support_touch_points_sufficient"] = len(support_touch_points) >= self.detector.min_touch_points
            except Exception as e:
                analysis["support_touch_points_error"] = str(e)
            
            # 3. レジスタンスライン詳細分析
            if analysis.get("resistance_touch_points_sufficient", False):
                try:
                    # ライン方程式計算
                    line_data = self.detector._calculate_line_equation(
                        resistance_touch_points, test_data, "High"
                    )
                    analysis["resistance_line_equation"] = line_data is not None
                    
                    if line_data:
                        # ライン強度検証
                        strength = self.detector._validate_line_strength(
                            resistance_touch_points, line_data
                        )
                        analysis["resistance_strength"] = strength
                        analysis["resistance_strength_sufficient"] = strength >= 0.3
                        
                        if analysis["resistance_strength_sufficient"]:
                            # ブレイクアウト検出
                            breakout = self.detector._detect_breakout(
                                test_data, line_data, "resistance"
                            )
                            analysis["resistance_breakout"] = breakout
                            
                            # ブレイクアウト強度の詳細分析
                            if breakout is None:
                                # ブレイクアウト強度を手動計算
                                slope = line_data["slope"]
                                intercept = line_data["intercept"]
                                current_index = len(test_data) - 1
                                current_price = test_data.iloc[-1]["Close"]
                                line_price = slope * current_index + intercept
                                
                                if current_price > line_price:
                                    breakout_strength = (current_price - line_price) / line_price
                                    analysis["resistance_breakout_strength"] = breakout_strength
                                    analysis["resistance_breakout_threshold"] = self.detector.breakout_threshold
                                    analysis["resistance_breakout_sufficient"] = breakout_strength > self.detector.breakout_threshold
                                else:
                                    analysis["resistance_breakout_strength"] = 0
                                    analysis["resistance_breakout_sufficient"] = False
                except Exception as e:
                    analysis["resistance_detailed_error"] = str(e)
            
            # 4. サポートライン詳細分析
            if analysis.get("support_touch_points_sufficient", False):
                try:
                    # ライン方程式計算
                    line_data = self.detector._calculate_line_equation(
                        support_touch_points, test_data, "Low"
                    )
                    analysis["support_line_equation"] = line_data is not None
                    
                    if line_data:
                        # ライン強度検証
                        strength = self.detector._validate_line_strength(
                            support_touch_points, line_data
                        )
                        analysis["support_strength"] = strength
                        analysis["support_strength_sufficient"] = strength >= 0.3
                        
                        if analysis["support_strength_sufficient"]:
                            # ブレイクアウト検出
                            breakout = self.detector._detect_breakout(
                                test_data, line_data, "support"
                            )
                            analysis["support_breakout"] = breakout
                except Exception as e:
                    analysis["support_detailed_error"] = str(e)
            
            # 5. レジスタンスライン検出（全体）
            try:
                resistance_line_result = self.detector._detect_resistance_line(test_data)
                analysis["resistance_line"] = resistance_line_result is not None
            except Exception as e:
                analysis["resistance_line_error"] = str(e)
            
            # 6. サポートライン検出（全体）
            try:
                support_line_result = self.detector._detect_support_line(test_data)
                analysis["support_line"] = support_line_result is not None
            except Exception as e:
                analysis["support_line_error"] = str(e)
            
            # 7. 最終結果
            analysis["either_pattern"] = (resistance_line_result is not None) or (support_line_result is not None)
            
            return analysis
            
        except Exception as e:
            logger.error(f"条件分析エラー: {e}")
            return {
                "resistance_line": False,
                "support_line": False,
                "either_pattern": False,
                "error": str(e)
            }


async def main():
    """メイン関数"""
    tester = Pattern15DetailedTester()
    result = await tester.test_pattern15_detailed()
    
    if result:
        print("\n✅ パターン15検出成功！")
        print(f"パターンタイプ: {result.get('pattern_type', 'unknown')}")
        print(f"方向: {result.get('direction', 'unknown')}")
    else:
        print("\n❌ パターン15は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
