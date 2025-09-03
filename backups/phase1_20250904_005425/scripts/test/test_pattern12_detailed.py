"""
パターン12詳細テストスクリプト

フラッグパターンの詳細テストと条件分析
"""

import asyncio
import logging
from typing import Dict

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.flag_pattern_detector import (
    FlagPatternDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern12DetailedTester:
    """パターン12詳細テスター"""

    def __init__(self):
        self.detector = FlagPatternDetector()

    async def test_pattern12_detailed(self) -> Dict:
        """パターン12詳細テスト実行"""
        logger.info("=== パターン12詳細テスト開始 ===")

        # 複数のテストケースを試行
        for test_case in range(1, 5):  # 4つのテストケース
            logger.info(f"テストケース {test_case} を試行中...")

            # テストデータ作成
            logger.info(f"パターン12用テストデータ作成中...（テストケース {test_case}）")
            test_data = self._create_pattern12_test_data(test_case)
            logger.info("✅ テストデータ作成完了")

            # 検出実行
            result = self.detector.detect(test_data)

            if result:
                logger.info(f"✅ パターン12検出成功！（テストケース {test_case}）")
                logger.info(f"   信頼度: {result['confidence_score']}")
                logger.info(f"   条件: {result['conditions_met']}")
                logger.info("🎉 パターン12が正常に検出されました！")
                return result
            else:
                logger.info(f"❌ テストケース {test_case} では検出されませんでした")
                # 条件分析
                conditions_analysis = self._analyze_conditions(test_data)
                logger.info(f"   条件分析: {conditions_analysis}")

        logger.info("❌ すべてのテストケースで検出されませんでした")
        return {}

    def _create_pattern12_test_data(self, test_case: int) -> Dict:
        """パターン12用テストデータ作成"""
        return {
            "D1": self._create_d1_data(test_case),
            "H4": self._create_h4_data(test_case),
            "H1": self._create_h1_data(test_case),
            "M5": self._create_m5_data(test_case),
        }

    def _create_d1_data(self, test_case: int) -> Dict:
        """D1データ作成（フラッグパターン）"""
        # 価格データ（ブルフラッグパターン）
        dates = pd.date_range(start="2024-01-01", periods=40, freq="D")

        # 価格データを作成
        prices = []
        for i in range(40):
            if test_case == 1:
                # ケース1: 標準的なブルフラッグ
                if i < 20:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.02
                else:
                    # フラッグ（横ばいまたは軽微な下降）
                    flag_start = 150.4
                    flag_decline = (i - 20) * 0.005
                    price = flag_start - flag_decline
            elif test_case == 2:
                # ケース2: より短いフラッグ
                if i < 25:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.015
                else:
                    # 短いフラッグ
                    flag_start = 150.375
                    flag_decline = (i - 25) * 0.01
                    price = flag_start - flag_decline
            elif test_case == 3:
                # ケース3: ベアフラッグ
                if i < 20:
                    # 下降トレンド（ポール）
                    price = 150.0 - i * 0.02
                else:
                    # フラッグ（横ばいまたは軽微な上昇）
                    flag_start = 149.6
                    flag_rise = (i - 20) * 0.005
                    price = flag_start + flag_rise
            else:
                # ケース4: 完全なブルフラッグ
                if i < 20:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.02
                else:
                    # 完全なフラッグ（横ばい）
                    price = 150.4 - (i - 20) * 0.002

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.3 for i in range(40)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(40)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(40)]),
                "histogram": [0.05 + i * 0.002 for i in range(40)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.5 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.5 for p in prices]),
                "std": [0.5] * 40,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h4_data(self, test_case: int) -> Dict:
        """H4データ作成（フラッグパターン）"""
        # 価格データ（ブルフラッグパターン）
        dates = pd.date_range(start="2024-01-01", periods=240, freq="4H")

        # 価格データを作成
        prices = []
        for i in range(240):
            if test_case == 1:
                # ケース1: 標準的なブルフラッグ
                if i < 120:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.001
                else:
                    # フラッグ（横ばいまたは軽微な下降）
                    flag_start = 150.12
                    flag_decline = (i - 120) * 0.0005
                    price = flag_start - flag_decline
            elif test_case == 2:
                # ケース2: より短いフラッグ
                if i < 150:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.0008
                else:
                    # 短いフラッグ
                    flag_start = 150.12
                    flag_decline = (i - 150) * 0.001
                    price = flag_start - flag_decline
            elif test_case == 3:
                # ケース3: ベアフラッグ
                if i < 120:
                    # 下降トレンド（ポール）
                    price = 150.0 - i * 0.001
                else:
                    # フラッグ（横ばいまたは軽微な上昇）
                    flag_start = 149.88
                    flag_rise = (i - 120) * 0.0005
                    price = flag_start + flag_rise
            else:
                # ケース4: 完全なブルフラッグ
                if i < 120:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.001
                else:
                    # 完全なフラッグ（横ばい）
                    price = 150.12 - (i - 120) * 0.0002

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.1 for i in range(240)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.001 for i in range(240)]),
                "signal": pd.Series([0.05 + i * 0.0008 for i in range(240)]),
                "histogram": [0.05 + i * 0.0002 for i in range(240)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.3 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.3 for p in prices]),
                "std": [0.3] * 240,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self, test_case: int) -> Dict:
        """H1データ作成（フラッグパターン）"""
        # 価格データ（ブルフラッグパターン）
        dates = pd.date_range(start="2024-01-01", periods=960, freq="H")

        # 価格データを作成
        prices = []
        for i in range(960):
            if test_case == 1:
                # ケース1: 標準的なブルフラッグ
                if i < 480:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.0001
                else:
                    # フラッグ（横ばいまたは軽微な下降）
                    flag_start = 150.048
                    flag_decline = (i - 480) * 0.00005
                    price = flag_start - flag_decline
            elif test_case == 2:
                # ケース2: より短いフラッグ
                if i < 600:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.00008
                else:
                    # 短いフラッグ
                    flag_start = 150.048
                    flag_decline = (i - 600) * 0.0001
                    price = flag_start - flag_decline
            elif test_case == 3:
                # ケース3: ベアフラッグ
                if i < 480:
                    # 下降トレンド（ポール）
                    price = 150.0 - i * 0.0001
                else:
                    # フラッグ（横ばいまたは軽微な上昇）
                    flag_start = 149.952
                    flag_rise = (i - 480) * 0.00005
                    price = flag_start + flag_rise
            else:
                # ケース4: 完全なブルフラッグ
                if i < 480:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.0001
                else:
                    # 完全なフラッグ（横ばい）
                    price = 150.048 - (i - 480) * 0.00002

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
            "rsi": {"current_value": 65, "values": [50 + i * 0.02 for i in range(960)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.0001 for i in range(960)]),
                "signal": pd.Series([0.05 + i * 0.00008 for i in range(960)]),
                "histogram": [0.05 + i * 0.00002 for i in range(960)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.15 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.15 for p in prices]),
                "std": [0.15] * 960,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self, test_case: int) -> Dict:
        """M5データ作成（フラッグパターン）"""
        # 価格データ（ブルフラッグパターン）
        dates = pd.date_range(start="2024-01-01", periods=11520, freq="5min")

        # 価格データを作成
        prices = []
        for i in range(11520):
            if test_case == 1:
                # ケース1: 標準的なブルフラッグ
                if i < 5760:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.00001
                else:
                    # フラッグ（横ばいまたは軽微な下降）
                    flag_start = 150.0576
                    flag_decline = (i - 5760) * 0.000005
                    price = flag_start - flag_decline
            elif test_case == 2:
                # ケース2: より短いフラッグ
                if i < 7200:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.000008
                else:
                    # 短いフラッグ
                    flag_start = 150.0576
                    flag_decline = (i - 7200) * 0.00001
                    price = flag_start - flag_decline
            elif test_case == 3:
                # ケース3: ベアフラッグ
                if i < 5760:
                    # 下降トレンド（ポール）
                    price = 150.0 - i * 0.00001
                else:
                    # フラッグ（横ばいまたは軽微な上昇）
                    flag_start = 149.9424
                    flag_rise = (i - 5760) * 0.000005
                    price = flag_start + flag_rise
            else:
                # ケース4: 完全なブルフラッグ
                if i < 5760:
                    # 上昇トレンド（ポール）
                    price = 150.0 + i * 0.00001
                else:
                    # 完全なフラッグ（横ばい）
                    price = 150.0576 - (i - 5760) * 0.000002

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
                "values": [50 + i * 0.002 for i in range(11520)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.00001 for i in range(11520)]),
                "signal": pd.Series([0.05 + i * 0.000008 for i in range(11520)]),
                "histogram": [0.05 + i * 0.000002 for i in range(11520)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.05 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.05 for p in prices]),
                "std": [0.05] * 11520,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _analyze_conditions(self, test_data: Dict) -> Dict:
        """条件分析"""
        conditions_analysis = {}

        for timeframe in ["D1", "H4", "H1", "M5"]:
            if timeframe in test_data:
                price_data = test_data[timeframe]["price_data"]

                # ブルフラッグ検出
                bull_flag_result = self.detector._detect_bull_flag(price_data)

                # ベアフラッグ検出
                bear_flag_result = self.detector._detect_bear_flag(price_data)

                conditions_analysis[timeframe] = {
                    "bull_flag": bull_flag_result,
                    "bear_flag": bear_flag_result,
                    "either_pattern": bull_flag_result or bear_flag_result,
                }

        return conditions_analysis


async def main():
    """メイン関数"""
    tester = Pattern12DetailedTester()
    result = await tester.test_pattern12_detailed()

    if result:
        print("\n✅ パターン12検出成功！")
        print(f"信頼度: {result['confidence_score']}")
        print(f"条件: {result['conditions_met']}")
    else:
        print("\n❌ パターン12は検出されませんでした")


if __name__ == "__main__":
    asyncio.run(main())
