"""
パターン11詳細テストスクリプト

トリプルトップ/ボトムパターンの詳細テストと条件分析
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.triple_top_bottom_detector import (
    TripleTopBottomDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern11DetailedTester:
    """パターン11詳細テスター"""

    def __init__(self):
        self.detector = TripleTopBottomDetector()

    async def test_pattern11_detailed(self) -> Dict:
        """パターン11詳細テスト実行"""
        logger.info("=== パターン11詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")
            
            # テストデータ作成
            logger.info(f"パターン11用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern11_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン11検出成功！（テストケース {test_case}）")
                logger.info(f"   信頼度: {result['confidence_score']}")
                logger.info(f"   条件: {result['conditions_met']}")
                logger.info("🎉 パターン11が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern11_test_data(self, test_case: int) -> Dict:
        """パターン11用テストデータ作成"""
        return {
            "D1": self._create_d1_data(test_case),
            "H4": self._create_h4_data(test_case),
            "H1": self._create_h1_data(test_case),
            "M5": self._create_m5_data(test_case),
        }

    def _create_d1_data(self, test_case: int) -> Dict:
        """D1データ作成（トリプルトップ/ボトムパターン）"""
        # 価格データ（トリプルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=60, freq="D")

        # 価格データを作成
        prices = []
        for i in range(60):
            if test_case == 1:
                # ケース1: 標準的なトリプルトップ
                if i < 15:
                    price = 150.0 + i * 0.01
                elif i < 25:
                    price = 150.15 - (i - 15) * 0.005
                elif i < 35:
                    price = 150.125 + (i - 25) * 0.005
                elif i < 45:
                    price = 150.15 - (i - 35) * 0.005
                elif i < 55:
                    price = 150.125 + (i - 45) * 0.005
                else:
                    price = 150.15 - (i - 55) * 0.005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 12:
                    price = 150.0 + i * 0.01
                elif i < 22:
                    price = 150.12 - (i - 12) * 0.005
                elif i < 32:
                    price = 150.095 + (i - 22) * 0.005
                elif i < 42:
                    price = 150.12 - (i - 32) * 0.005
                elif i < 52:
                    price = 150.095 + (i - 42) * 0.005
                else:
                    price = 150.12 - (i - 52) * 0.005
            elif test_case == 3:
                # ケース3: トリプルボトム
                if i < 15:
                    price = 150.0 - i * 0.01
                elif i < 25:
                    price = 149.85 + (i - 15) * 0.005
                elif i < 35:
                    price = 149.875 - (i - 25) * 0.005
                elif i < 45:
                    price = 149.85 + (i - 35) * 0.005
                elif i < 55:
                    price = 149.875 - (i - 45) * 0.005
                else:
                    price = 149.85 + (i - 55) * 0.005
            else:
                # ケース4: 完全なトリプルトップ
                if i < 15:
                    price = 150.0 + i * 0.01
                elif i < 20:
                    price = 150.15 - (i - 15) * 0.01
                elif i < 30:
                    price = 150.125 + (i - 20) * 0.01
                elif i < 35:
                    price = 150.15 - (i - 30) * 0.01
                elif i < 45:
                    price = 150.125 + (i - 35) * 0.01
                elif i < 50:
                    price = 150.15 - (i - 45) * 0.01
                else:
                    price = 150.125 + (i - 50) * 0.01

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.3 for i in range(60)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(60)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(60)]),
                "histogram": [0.05 + i * 0.002 for i in range(60)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.5 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.5 for p in prices]),
                "std": [0.5] * 60,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h4_data(self, test_case: int) -> Dict:
        """H4データ作成（トリプルトップ/ボトムパターン）"""
        # 価格データ（トリプルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=360, freq="4H")

        # 価格データを作成
        prices = []
        for i in range(360):
            if test_case == 1:
                # ケース1: 標準的なトリプルトップ
                if i < 90:
                    price = 150.0 + i * 0.001
                elif i < 150:
                    price = 150.09 - (i - 90) * 0.0005
                elif i < 210:
                    price = 150.075 + (i - 150) * 0.0005
                elif i < 270:
                    price = 150.09 - (i - 210) * 0.0005
                elif i < 330:
                    price = 150.075 + (i - 270) * 0.0005
                else:
                    price = 150.09 - (i - 330) * 0.0005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 72:
                    price = 150.0 + i * 0.001
                elif i < 132:
                    price = 150.072 - (i - 72) * 0.0005
                elif i < 192:
                    price = 150.06 + (i - 132) * 0.0005
                elif i < 252:
                    price = 150.072 - (i - 192) * 0.0005
                elif i < 312:
                    price = 150.06 + (i - 252) * 0.0005
                else:
                    price = 150.072 - (i - 312) * 0.0005
            elif test_case == 3:
                # ケース3: トリプルボトム
                if i < 90:
                    price = 150.0 - i * 0.001
                elif i < 150:
                    price = 149.91 + (i - 90) * 0.0005
                elif i < 210:
                    price = 149.925 - (i - 150) * 0.0005
                elif i < 270:
                    price = 149.91 + (i - 210) * 0.0005
                elif i < 330:
                    price = 149.925 - (i - 270) * 0.0005
                else:
                    price = 149.91 + (i - 330) * 0.0005
            else:
                # ケース4: 完全なトリプルトップ
                if i < 90:
                    price = 150.0 + i * 0.001
                elif i < 120:
                    price = 150.09 - (i - 90) * 0.001
                elif i < 180:
                    price = 150.075 + (i - 120) * 0.001
                elif i < 210:
                    price = 150.09 - (i - 180) * 0.001
                elif i < 270:
                    price = 150.075 + (i - 210) * 0.001
                elif i < 300:
                    price = 150.09 - (i - 270) * 0.001
                else:
                    price = 150.075 + (i - 300) * 0.001

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.1 for i in range(360)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.001 for i in range(360)]),
                "signal": pd.Series([0.05 + i * 0.0008 for i in range(360)]),
                "histogram": [0.05 + i * 0.0002 for i in range(360)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.3 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.3 for p in prices]),
                "std": [0.3] * 360,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self, test_case: int) -> Dict:
        """H1データ作成（トリプルトップ/ボトムパターン）"""
        # 価格データ（トリプルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=1440, freq="H")

        # 価格データを作成
        prices = []
        for i in range(1440):
            if test_case == 1:
                # ケース1: 標準的なトリプルトップ
                if i < 360:
                    price = 150.0 + i * 0.0001
                elif i < 600:
                    price = 150.036 - (i - 360) * 0.00005
                elif i < 840:
                    price = 150.03 + (i - 600) * 0.00005
                elif i < 1080:
                    price = 150.036 - (i - 840) * 0.00005
                elif i < 1320:
                    price = 150.03 + (i - 1080) * 0.00005
                else:
                    price = 150.036 - (i - 1320) * 0.00005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 288:
                    price = 150.0 + i * 0.0001
                elif i < 528:
                    price = 150.0288 - (i - 288) * 0.00005
                elif i < 768:
                    price = 150.024 + (i - 528) * 0.00005
                elif i < 1008:
                    price = 150.0288 - (i - 768) * 0.00005
                elif i < 1248:
                    price = 150.024 + (i - 1008) * 0.00005
                else:
                    price = 150.0288 - (i - 1248) * 0.00005
            elif test_case == 3:
                # ケース3: トリプルボトム
                if i < 360:
                    price = 150.0 - i * 0.0001
                elif i < 600:
                    price = 149.964 + (i - 360) * 0.00005
                elif i < 840:
                    price = 149.97 - (i - 600) * 0.00005
                elif i < 1080:
                    price = 149.964 + (i - 840) * 0.00005
                elif i < 1320:
                    price = 149.97 - (i - 1080) * 0.00005
                else:
                    price = 149.964 + (i - 1320) * 0.00005
            else:
                # ケース4: 完全なトリプルトップ
                if i < 360:
                    price = 150.0 + i * 0.0001
                elif i < 480:
                    price = 150.036 - (i - 360) * 0.0001
                elif i < 720:
                    price = 150.03 + (i - 480) * 0.0001
                elif i < 840:
                    price = 150.036 - (i - 720) * 0.0001
                elif i < 1080:
                    price = 150.03 + (i - 840) * 0.0001
                elif i < 1200:
                    price = 150.036 - (i - 1080) * 0.0001
                else:
                    price = 150.03 + (i - 1200) * 0.0001

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.02 for i in range(1440)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.0001 for i in range(1440)]),
                "signal": pd.Series([0.05 + i * 0.00008 for i in range(1440)]),
                "histogram": [0.05 + i * 0.00002 for i in range(1440)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.15 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.15 for p in prices]),
                "std": [0.15] * 1440,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self, test_case: int) -> Dict:
        """M5データ作成（トリプルトップ/ボトムパターン）"""
        # 価格データ（トリプルトップパターン）
        dates = pd.date_range(start="2024-01-01", periods=17280, freq="5min")

        # 価格データを作成
        prices = []
        for i in range(17280):
            if test_case == 1:
                # ケース1: 標準的なトリプルトップ
                if i < 4320:
                    price = 150.0 + i * 0.00001
                elif i < 7200:
                    price = 150.0432 - (i - 4320) * 0.000005
                elif i < 10080:
                    price = 150.036 + (i - 7200) * 0.000005
                elif i < 12960:
                    price = 150.0432 - (i - 10080) * 0.000005
                elif i < 15840:
                    price = 150.036 + (i - 12960) * 0.000005
                else:
                    price = 150.0432 - (i - 15840) * 0.000005
            elif test_case == 2:
                # ケース2: より近いピーク
                if i < 3456:
                    price = 150.0 + i * 0.00001
                elif i < 6336:
                    price = 150.03456 - (i - 3456) * 0.000005
                elif i < 9216:
                    price = 150.0288 + (i - 6336) * 0.000005
                elif i < 12096:
                    price = 150.03456 - (i - 9216) * 0.000005
                elif i < 14976:
                    price = 150.0288 + (i - 12096) * 0.000005
                else:
                    price = 150.03456 - (i - 14976) * 0.000005
            elif test_case == 3:
                # ケース3: トリプルボトム
                if i < 4320:
                    price = 150.0 - i * 0.00001
                elif i < 7200:
                    price = 149.9568 + (i - 4320) * 0.000005
                elif i < 10080:
                    price = 149.964 - (i - 7200) * 0.000005
                elif i < 12960:
                    price = 149.9568 + (i - 10080) * 0.000005
                elif i < 15840:
                    price = 149.964 - (i - 12960) * 0.000005
                else:
                    price = 149.9568 + (i - 15840) * 0.000005
            else:
                # ケース4: 完全なトリプルトップ
                if i < 4320:
                    price = 150.0 + i * 0.00001
                elif i < 5760:
                    price = 150.0432 - (i - 4320) * 0.00001
                elif i < 8640:
                    price = 150.036 + (i - 5760) * 0.00001
                elif i < 10080:
                    price = 150.0432 - (i - 8640) * 0.00001
                elif i < 12960:
                    price = 150.036 + (i - 10080) * 0.00001
                elif i < 14400:
                    price = 150.0432 - (i - 12960) * 0.00001
                else:
                    price = 150.036 + (i - 14400) * 0.00001

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.002 for i in range(17280)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.00001 for i in range(17280)]),
                "signal": pd.Series([0.05 + i * 0.000008 for i in range(17280)]),
                "histogram": [0.05 + i * 0.000002 for i in range(17280)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.05 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.05 for p in prices]),
                "std": [0.05] * 17280,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _analyze_conditions(self, test_data: Dict) -> Dict:
        """条件分析"""
        conditions_analysis = {}

        for timeframe in ["D1", "H4", "H1", "M5"]:
            if timeframe in test_data:
                price_data = test_data[timeframe]["price_data"]
                
                # トリプルトップ検出
                triple_top_result = self.detector._detect_triple_top(price_data)
                
                # トリプルボトム検出
                triple_bottom_result = self.detector._detect_triple_bottom(price_data)
                
                conditions_analysis[timeframe] = {
                    "triple_top": triple_top_result,
                    "triple_bottom": triple_bottom_result,
                    "either_pattern": triple_top_result or triple_bottom_result
                }

        return conditions_analysis


async def main():
    """メイン関数"""
    tester = Pattern11DetailedTester()
    result = await tester.test_pattern11_detailed()
    
    if result:
        print("\n✅ パターン11検出成功！")
        print(f"信頼度: {result['confidence_score']}")
        print(f"条件: {result['conditions_met']}")
    else:
        print("\n❌ パターン11は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
