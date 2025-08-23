"""
パターン14詳細テストスクリプト

ウェッジパターンの詳細テストと条件分析
"""

import asyncio
import logging
import math
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.wedge_pattern_detector import (
    WedgePatternDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern14DetailedTester:
    """パターン14詳細テスター"""

    def __init__(self):
        self.detector = WedgePatternDetector()

    async def test_pattern14_detailed(self) -> Dict:
        """パターン14詳細テスト実行"""
        logger.info("=== パターン14詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")

            # テストデータ作成
            logger.info(f"パターン14用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern14_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン14検出成功！（テストケース {test_case}）")
                logger.info(f"   パターンタイプ: {result.get('pattern_type', 'unknown')}")
                logger.info(f"   方向: {result.get('direction', 'unknown')}")
                logger.info("🎉 パターン14が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern14_test_data(self, test_case: int) -> pd.DataFrame:
        """パターン14用テストデータ作成"""
        # 価格データ（ウェッジパターン）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

        # 価格データを作成
        prices = []
        for i in range(100):
            if test_case == 1:
                # ケース1: 標準的な上昇ウェッジ
                if i < 50:
                    # 上昇トレンド（収束）
                    base_price = 150.0 + i * 0.01
                    # 収束する振幅
                    amplitude = 0.5 - (i * 0.008)
                    price = base_price + amplitude * math.sin(i * 0.3)
                else:
                    # ブレイクアウト
                    price = 150.5 + (i - 50) * 0.02
            elif test_case == 2:
                # ケース2: 下降ウェッジ
                if i < 50:
                    # 下降トレンド（収束）
                    base_price = 150.0 - i * 0.01
                    # 収束する振幅
                    amplitude = 0.5 - (i * 0.008)
                    price = base_price + amplitude * math.sin(i * 0.3)
                else:
                    # ブレイクアウト
                    price = 149.5 + (i - 50) * 0.02
            elif test_case == 3:
                # ケース3: より短いウェッジ
                if i < 30:
                    # 短い上昇ウェッジ
                    base_price = 150.0 + i * 0.015
                    amplitude = 0.3 - (i * 0.01)
                    price = base_price + amplitude * math.sin(i * 0.4)
                else:
                    # ブレイクアウト
                    price = 150.45 + (i - 30) * 0.025
            else:
                # ケース4: 完全なウェッジ
                if i < 60:
                    # 完全な上昇ウェッジ
                    base_price = 150.0 + i * 0.008
                    amplitude = 0.6 - (i * 0.01)
                    price = base_price + amplitude * math.sin(i * 0.25)
                else:
                    # ブレイクアウト
                    price = 150.48 + (i - 60) * 0.03

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
            # 上昇ウェッジ検出
            rising_wedge_result = self.detector._detect_rising_wedge(test_data)

            # 下降ウェッジ検出
            falling_wedge_result = self.detector._detect_falling_wedge(test_data)

            return {
                "rising_wedge": rising_wedge_result is not None,
                "falling_wedge": falling_wedge_result is not None,
                "either_pattern": (rising_wedge_result is not None)
                or (falling_wedge_result is not None),
            }
        except Exception as e:
            logger.error(f"条件分析エラー: {e}")
            return {
                "rising_wedge": False,
                "falling_wedge": False,
                "either_pattern": False,
                "error": str(e),
            }


async def main():
    """メイン関数"""
    tester = Pattern14DetailedTester()
    result = await tester.test_pattern14_detailed()

    if result:
        print("\n✅ パターン14検出成功！")
        print(f"パターンタイプ: {result.get('pattern_type', 'unknown')}")
        print(f"方向: {result.get('direction', 'unknown')}")
    else:
        print("\n❌ パターン14は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
