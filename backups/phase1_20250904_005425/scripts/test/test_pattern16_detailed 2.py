"""
パターン16詳細テストスクリプト

ロールリバーサル検出の詳細テストと条件分析
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.roll_reversal_detector import (
    RollReversalDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern16DetailedTester:
    """パターン16詳細テスター"""

    def __init__(self):
        self.detector = RollReversalDetector()

    async def test_pattern16_detailed(self) -> Dict:
        """パターン16詳細テスト実行"""
        logger.info("=== パターン16詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")
            
            # テストデータ作成
            logger.info(f"パターン16用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern16_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン16検出成功！（テストケース {test_case}）")
                logger.info(f"   パターンタイプ: {result.get('pattern_type', 'unknown')}")
                logger.info(f"   方向: {result.get('direction', 'unknown')}")
                logger.info("🎉 パターン16が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern16_test_data(self, test_case: int) -> pd.DataFrame:
        """パターン16用テストデータ作成"""
        # 価格データ（ロールリバーサルパターン）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="D")

        # 価格データを作成
        prices = []
        for i in range(100):
            if test_case == 1:
                # ケース1: 標準的な強気ロールリバーサル
                if i < 30:
                    # 下降トレンド（ロール）
                    base_price = 150.0 - i * 0.02
                    price = base_price + 0.1 * (i % 5 - 2)  # 小さな変動
                elif i < 50:
                    # リバーサル
                    base_price = 149.4 + (i - 30) * 0.03
                    price = base_price + 0.05 * (i % 3 - 1)
                else:
                    # 上昇トレンド
                    price = 150.0 + (i - 50) * 0.025
            elif test_case == 2:
                # ケース2: 弱気ロールリバーサル
                if i < 25:
                    # 上昇トレンド（ロール）
                    base_price = 150.0 + i * 0.015
                    price = base_price + 0.08 * (i % 4 - 1.5)
                elif i < 45:
                    # リバーサル
                    base_price = 150.375 - (i - 25) * 0.025
                    price = base_price - 0.03 * (i % 3 - 1)
                else:
                    # 下降トレンド
                    price = 149.5 - (i - 45) * 0.02
            elif test_case == 3:
                # ケース3: より短いロール
                if i < 20:
                    # 短い下降ロール
                    base_price = 150.0 - i * 0.025
                    price = base_price + 0.06 * (i % 3 - 1)
                elif i < 35:
                    # リバーサル
                    base_price = 149.5 + (i - 20) * 0.04
                    price = base_price + 0.04 * (i % 2 - 0.5)
                else:
                    # 上昇トレンド
                    price = 150.1 + (i - 35) * 0.03
            else:
                # ケース4: 強いモメンタム
                if i < 35:
                    # 強い下降ロール
                    base_price = 150.0 - i * 0.03
                    price = base_price + 0.12 * (i % 6 - 2.5)
                elif i < 55:
                    # 強いリバーサル
                    base_price = 148.95 + (i - 35) * 0.05
                    price = base_price + 0.08 * (i % 4 - 1.5)
                else:
                    # 強い上昇トレンド
                    price = 150.0 + (i - 55) * 0.035

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
            # 強気ロールリバーサル検出
            bullish_roll_result = self.detector._detect_bullish_roll_reversal(test_data)
            
            # 弱気ロールリバーサル検出
            bearish_roll_result = self.detector._detect_bearish_roll_reversal(test_data)
            
            return {
                "bullish_roll_reversal": bullish_roll_result is not None,
                "bearish_roll_reversal": bearish_roll_result is not None,
                "either_pattern": (bullish_roll_result is not None) or (bearish_roll_result is not None)
            }
        except Exception as e:
            logger.error(f"条件分析エラー: {e}")
            return {
                "bullish_roll_reversal": False,
                "bearish_roll_reversal": False,
                "either_pattern": False,
                "error": str(e)
            }


async def main():
    """メイン関数"""
    tester = Pattern16DetailedTester()
    result = await tester.test_pattern16_detailed()
    
    if result:
        print("\n✅ パターン16検出成功！")
        print(f"パターンタイプ: {result.get('pattern_type', 'unknown')}")
        print(f"方向: {result.get('direction', 'unknown')}")
    else:
        print("\n❌ パターン16は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
