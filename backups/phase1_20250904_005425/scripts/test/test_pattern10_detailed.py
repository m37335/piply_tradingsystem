"""
パターン10詳細テストスクリプト

ダブルトップ/ボトムパターンの詳細テストと条件分析
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.double_top_bottom_detector import (
    DoubleTopBottomDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern10DetailedTester:
    """パターン10詳細テスター"""

    def __init__(self):
        self.detector = DoubleTopBottomDetector()

    async def test_pattern10_detailed(self) -> Dict:
        """パターン10詳細テスト実行"""
        logger.info("=== パターン10詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")

            # テストデータ作成
            logger.info(f"パターン10用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern10_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン10検出成功！（テストケース {test_case}）")
                logger.info(f"   信頼度: {result['confidence_score']}")
                logger.info(f"   条件: {result['conditions_met']}")
                logger.info("🎉 パターン10が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern10_test_data(self, test_case: int) -> Dict:
        """パターン10用テストデータ作成"""
        return {
            "D1": self._create_d1_data(test_case),
            "H4": self._create_h4_data(test_case),
            "H1": self._create_h1_data(test_case),
            "M5": self._create_m5_data(test_case),
        }

    def _create_d1_data(self, test_case: int) -> Dict:
        """D1データ作成（ダブルトップ/ボトムパターン）"""
        # 価格データ（ダブルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

        # 価格データを作成
        prices = []
        for i in range(50):
            if test_case == 1:
                # ケース1: 標準的なダブルトップ
                if i < 20:
                    price = 150.0 + i * 0.01
                elif i < 30:
                    price = 150.2 - (i - 20) * 0.005
                elif i < 40:
                    price = 150.15 + (i - 30) * 0.005
                else:
                    price = 150.2 - (i - 40) * 0.005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 15:
                    price = 150.0 + i * 0.01
                elif i < 25:
                    price = 150.15 - (i - 15) * 0.005
                elif i < 35:
                    price = 150.125 + (i - 25) * 0.005
                else:
                    price = 150.15 - (i - 35) * 0.005
            elif test_case == 3:
                # ケース3: ダブルボトム
                if i < 20:
                    price = 150.0 - i * 0.01
                elif i < 30:
                    price = 149.8 + (i - 20) * 0.005
                elif i < 40:
                    price = 149.85 - (i - 30) * 0.005
                else:
                    price = 149.8 + (i - 40) * 0.005
            else:
                # ケース4: 完全なダブルトップ
                if i < 20:
                    price = 150.0 + i * 0.01
                elif i < 25:
                    price = 150.2 - (i - 20) * 0.01
                elif i < 35:
                    price = 150.15 + (i - 25) * 0.01
                else:
                    price = 150.2 - (i - 35) * 0.01

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

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {"current_value": 65, "values": [50 + i * 0.3 for i in range(50)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(50)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(50)]),
                "histogram": [0.05 + i * 0.002 for i in range(50)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.5 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.5 for p in prices]),
                "std": [0.5] * 50,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h4_data(self, test_case: int) -> Dict:
        """H4データ作成（ダブルトップ/ボトムパターン）"""
        # 価格データ（ダブルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=300, freq="4H")

        # 価格データを作成
        prices = []
        for i in range(300):
            if test_case == 1:
                # ケース1: 標準的なダブルトップ
                if i < 120:
                    price = 150.0 + i * 0.001
                elif i < 180:
                    price = 150.12 - (i - 120) * 0.0005
                elif i < 240:
                    price = 150.09 + (i - 180) * 0.0005
                else:
                    price = 150.12 - (i - 240) * 0.0005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 100:
                    price = 150.0 + i * 0.001
                elif i < 160:
                    price = 150.1 - (i - 100) * 0.0005
                elif i < 220:
                    price = 150.075 + (i - 160) * 0.0005
                else:
                    price = 150.1 - (i - 220) * 0.0005
            elif test_case == 3:
                # ケース3: ダブルボトム
                if i < 120:
                    price = 150.0 - i * 0.001
                elif i < 180:
                    price = 149.88 + (i - 120) * 0.0005
                elif i < 240:
                    price = 149.91 - (i - 180) * 0.0005
                else:
                    price = 149.88 + (i - 240) * 0.0005
            else:
                # ケース4: 完全なダブルトップ
                if i < 120:
                    price = 150.0 + i * 0.001
                elif i < 150:
                    price = 150.12 - (i - 120) * 0.001
                elif i < 210:
                    price = 150.09 + (i - 150) * 0.001
                else:
                    price = 150.12 - (i - 210) * 0.001

            prices.append(
                {
                    "Date": dates[i],
                    "Open": price - 0.005,
                    "High": price + 0.01,
                    "Low": price - 0.01,
                    "Close": price,
                    "Volume": 1000 + i,
                }
            )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {"current_value": 65, "values": [50 + i * 0.1 for i in range(300)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.001 for i in range(300)]),
                "signal": pd.Series([0.05 + i * 0.0008 for i in range(300)]),
                "histogram": [0.05 + i * 0.0002 for i in range(300)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.3 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.3 for p in prices]),
                "std": [0.3] * 300,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self, test_case: int) -> Dict:
        """H1データ作成（ダブルトップ/ボトムパターン）"""
        # 価格データ（ダブルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=1200, freq="H")

        # 価格データを作成
        prices = []
        for i in range(1200):
            if test_case == 1:
                # ケース1: 標準的なダブルトップ
                if i < 480:
                    price = 150.0 + i * 0.0001
                elif i < 720:
                    price = 150.048 - (i - 480) * 0.00005
                elif i < 960:
                    price = 150.036 + (i - 720) * 0.00005
                else:
                    price = 150.048 - (i - 960) * 0.00005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 400:
                    price = 150.0 + i * 0.0001
                elif i < 640:
                    price = 150.04 - (i - 400) * 0.00005
                elif i < 880:
                    price = 150.03 + (i - 640) * 0.00005
                else:
                    price = 150.04 - (i - 880) * 0.00005
            elif test_case == 3:
                # ケース3: ダブルボトム
                if i < 480:
                    price = 150.0 - i * 0.0001
                elif i < 720:
                    price = 149.952 + (i - 480) * 0.00005
                elif i < 960:
                    price = 149.964 - (i - 720) * 0.00005
                else:
                    price = 149.952 + (i - 960) * 0.00005
            else:
                # ケース4: 完全なダブルトップ
                if i < 480:
                    price = 150.0 + i * 0.0001
                elif i < 600:
                    price = 150.048 - (i - 480) * 0.0001
                elif i < 840:
                    price = 150.036 + (i - 600) * 0.0001
                else:
                    price = 150.048 - (i - 840) * 0.0001

            prices.append(
                {
                    "Date": dates[i],
                    "Open": price - 0.002,
                    "High": price + 0.005,
                    "Low": price - 0.005,
                    "Close": price,
                    "Volume": 1000 + i,
                }
            )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 65,
                "values": [50 + i * 0.02 for i in range(1200)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.0001 for i in range(1200)]),
                "signal": pd.Series([0.05 + i * 0.00008 for i in range(1200)]),
                "histogram": [0.05 + i * 0.00002 for i in range(1200)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.15 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.15 for p in prices]),
                "std": [0.15] * 1200,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self, test_case: int) -> Dict:
        """M5データ作成（ダブルトップ/ボトムパターン）"""
        # 価格データ（ダブルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=14400, freq="5min")

        # 価格データを作成
        prices = []
        for i in range(14400):
            if test_case == 1:
                # ケース1: 標準的なダブルトップ
                if i < 5760:
                    price = 150.0 + i * 0.00001
                elif i < 8640:
                    price = 150.0576 - (i - 5760) * 0.000005
                elif i < 11520:
                    price = 150.0432 + (i - 8640) * 0.000005
                else:
                    price = 150.0576 - (i - 11520) * 0.000005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 4800:
                    price = 150.0 + i * 0.00001
                elif i < 7680:
                    price = 150.048 - (i - 4800) * 0.000005
                elif i < 10560:
                    price = 150.036 + (i - 7680) * 0.000005
                else:
                    price = 150.048 - (i - 10560) * 0.000005
            elif test_case == 3:
                # ケース3: ダブルボトム
                if i < 5760:
                    price = 150.0 - i * 0.00001
                elif i < 8640:
                    price = 149.9424 + (i - 5760) * 0.000005
                elif i < 11520:
                    price = 149.9568 - (i - 8640) * 0.000005
                else:
                    price = 149.9424 + (i - 11520) * 0.000005
            else:
                # ケース4: 完全なダブルトップ
                if i < 5760:
                    price = 150.0 + i * 0.00001
                elif i < 7200:
                    price = 150.0576 - (i - 5760) * 0.00001
                elif i < 10080:
                    price = 150.0432 + (i - 7200) * 0.00001
                else:
                    price = 150.0576 - (i - 10080) * 0.00001

            prices.append(
                {
                    "Date": dates[i],
                    "Open": price - 0.0005,
                    "High": price + 0.001,
                    "Low": price - 0.001,
                    "Close": price,
                    "Volume": 1000 + i,
                }
            )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 65,
                "values": [50 + i * 0.002 for i in range(14400)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.00001 for i in range(14400)]),
                "signal": pd.Series([0.05 + i * 0.000008 for i in range(14400)]),
                "histogram": [0.05 + i * 0.000002 for i in range(14400)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.05 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.05 for p in prices]),
                "std": [0.05] * 14400,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _analyze_conditions(self, test_data: Dict) -> Dict:
        """条件分析"""
        conditions_analysis = {}

        for timeframe in ["D1", "H4", "H1", "M5"]:
            if timeframe in test_data:
                price_data = test_data[timeframe]["price_data"]

                # ダブルトップ検出
                double_top_result = self.detector._detect_double_top(price_data)

                # ダブルボトム検出
                double_bottom_result = self.detector._detect_double_bottom(price_data)

                conditions_analysis[timeframe] = {
                    "double_top": double_top_result,
                    "double_bottom": double_bottom_result,
                    "either_pattern": double_top_result or double_bottom_result,
                }

        return conditions_analysis


async def main():
    """メイン関数"""
    tester = Pattern10DetailedTester()
    result = await tester.test_pattern10_detailed()

    if result:
        print("\n✅ パターン10検出成功！")
        print(f"信頼度: {result['confidence_score']}")
        print(f"条件: {result['conditions_met']}")
    else:
        print("\n❌ パターン10は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
