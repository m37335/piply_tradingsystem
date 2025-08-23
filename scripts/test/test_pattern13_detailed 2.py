"""
パターン13詳細テストスクリプト

三尊天井/逆三尊パターンの詳細テストと条件分析
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.three_buddhas_detector import (
    ThreeBuddhasDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern13DetailedTester:
    """パターン13詳細テスター"""

    def __init__(self):
        self.detector = ThreeBuddhasDetector()

    async def test_pattern13_detailed(self) -> Dict:
        """パターン13詳細テスト実行"""
        logger.info("=== パターン13詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")
            
            # テストデータ作成
            logger.info(f"パターン13用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern13_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン13検出成功！（テストケース {test_case}）")
                logger.info(f"   パターンタイプ: {result.get('pattern_type', 'unknown')}")
                logger.info(f"   方向: {result.get('direction', 'unknown')}")
                logger.info("🎉 パターン13が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern13_test_data(self, test_case: int) -> pd.DataFrame:
        """パターン13用テストデータ作成"""
        # 価格データ（三尊天井パターン）
        dates = pd.date_range(start="2024-01-01", periods=80, freq="D")

        # 価格データを作成
        prices = []
        for i in range(80):
            if test_case == 1:
                # ケース1: 標準的な三尊天井
                if i < 20:
                    price = 150.0 + i * 0.01
                elif i < 30:
                    price = 150.2 - (i - 20) * 0.005
                elif i < 40:
                    price = 150.15 + (i - 30) * 0.015  # 中央ピーク（最も高い）
                elif i < 50:
                    price = 150.3 - (i - 40) * 0.005
                elif i < 60:
                    price = 150.25 + (i - 50) * 0.01
                else:
                    price = 150.35 - (i - 60) * 0.005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 15:
                    price = 150.0 + i * 0.01
                elif i < 25:
                    price = 150.15 - (i - 15) * 0.005
                elif i < 35:
                    price = 150.125 + (i - 25) * 0.02  # 中央ピーク
                elif i < 45:
                    price = 150.325 - (i - 35) * 0.005
                elif i < 55:
                    price = 150.3 + (i - 45) * 0.01
                else:
                    price = 150.4 - (i - 55) * 0.005
            elif test_case == 3:
                # ケース3: 逆三尊
                if i < 20:
                    price = 150.0 - i * 0.01
                elif i < 30:
                    price = 149.8 + (i - 20) * 0.005
                elif i < 40:
                    price = 149.85 - (i - 30) * 0.015  # 中央ボトム（最も低い）
                elif i < 50:
                    price = 149.7 + (i - 40) * 0.005
                elif i < 60:
                    price = 149.75 - (i - 50) * 0.01
                else:
                    price = 149.65 + (i - 60) * 0.005
            else:
                # ケース4: 完全な三尊天井
                if i < 20:
                    price = 150.0 + i * 0.01
                elif i < 25:
                    price = 150.2 - (i - 20) * 0.01
                elif i < 35:
                    price = 150.15 + (i - 25) * 0.02  # 中央ピーク
                elif i < 40:
                    price = 150.35 - (i - 35) * 0.01
                elif i < 50:
                    price = 150.3 + (i - 40) * 0.01
                else:
                    price = 150.4 - (i - 50) * 0.01

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
            # 三尊天井検出
            three_buddhas_top_result = self.detector._detect_three_buddhas_top(test_data)
            
            # 逆三尊検出
            inverse_three_buddhas_result = self.detector._detect_inverse_three_buddhas(test_data)
            
            return {
                "three_buddhas_top": three_buddhas_top_result is not None,
                "inverse_three_buddhas": inverse_three_buddhas_result is not None,
                "either_pattern": (three_buddhas_top_result is not None) or (inverse_three_buddhas_result is not None)
            }
        except Exception as e:
            logger.error(f"条件分析エラー: {e}")
            return {
                "three_buddhas_top": False,
                "inverse_three_buddhas": False,
                "either_pattern": False,
                "error": str(e)
            }


async def main():
    """メイン関数"""
    tester = Pattern13DetailedTester()
    result = await tester.test_pattern13_detailed()
    
    if result:
        print("\n✅ パターン13検出成功！")
        print(f"パターンタイプ: {result.get('pattern_type', 'unknown')}")
        print(f"方向: {result.get('direction', 'unknown')}")
    else:
        print("\n❌ パターン13は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
