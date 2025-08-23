#!/usr/bin/env python3
"""
パターン9詳細テストスクリプト
パターン9（大陽線/大陰線引け坊主検出）専用の詳細テスト

パターン9の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.marubozu_detector import (
    MarubozuDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern9DetailedTester:
    """パターン9詳細テストクラス"""

    def __init__(self):
        self.detector = MarubozuDetector()

    async def test_pattern9_detailed(self) -> Dict:
        """パターン9詳細テスト実行"""
        logger.info("=== パターン9詳細テスト開始 ===")

        try:
            # 複数のテストケースを試す
            for test_case_index in range(4):  # 4つのケースを試す
                logger.info(f"テストケース {test_case_index + 1} を試行中...")

                # パターン9の条件を満たすテストデータを作成
                test_data = self._create_pattern9_test_data(test_case_index)

                # 検出テスト
                result = self.detector.detect(test_data)

                # 結果分析
                if result is not None:
                    logger.info(
                        f"✅ パターン9検出成功！（テストケース {test_case_index + 1}）"
                    )
                    logger.info(f"  信頼度: {result.get('confidence_score', 'N/A')}")
                    logger.info(f"  条件: {result.get('conditions_met', {})}")

                    return {
                        "success": True,
                        "detected": True,
                        "test_case": test_case_index + 1,
                        "confidence_score": result.get("confidence_score"),
                        "conditions_met": result.get("conditions_met"),
                        "pattern_info": result,
                    }
                else:
                    logger.info(
                        f"❌ テストケース {test_case_index + 1} では検出されませんでした"
                    )

                    # 条件の詳細分析
                    condition_analysis = self._analyze_conditions(test_data)
                    logger.info(f"  条件分析: {condition_analysis}")

            # すべてのケースで検出されなかった場合
            logger.info("❌ すべてのテストケースでパターン9は検出されませんでした")
            return {
                "success": True,
                "detected": False,
                "test_cases_tried": 4,
            }

        except Exception as e:
            logger.error(f"パターン9詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern9_test_data(self, test_case_index: int = 0) -> Dict:
        """パターン9の条件を満たすテストデータ作成"""
        logger.info(
            f"パターン9用テストデータ作成中...（テストケース {test_case_index + 1}）"
        )

        # パターン9の条件:
        # ヒゲ比率: 20%以下
        # 実体比率: 60%以上
        # ヒゲの欠如: 両方20%以下、または片方5%以下で他方30%以下

        test_data = {}

        # D1データ作成
        d1_data = self._create_d1_data()
        test_data["D1"] = d1_data

        # H4データ作成
        h4_data = self._create_h4_data()
        test_data["H4"] = h4_data

        # H1データ作成
        h1_data = self._create_h1_data()
        test_data["H1"] = h1_data

        # M5データ作成（テストケースインデックスを渡す）
        m5_data = self._create_m5_data(test_case_index)
        test_data["M5"] = m5_data

        logger.info("✅ テストデータ作成完了")
        return test_data

    def _create_d1_data(self) -> Dict:
        """D1データ作成（大陽線引け坊主）"""
        # 価格データ（引け坊主パターン）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

        # 価格データを作成
        prices = []
        for i in range(49):  # 最初の49日は通常の価格
            price = 150.0 + i * 0.01
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

        # 大陽線引け坊主（ヒゲが少なく、実体が大きい）
        prices.append(
            {
                "Date": dates[49],
                "Open": 150.49,
                "High": 150.60,  # 上ヒゲが小さい
                "Low": 150.50,  # 下ヒゲが小さい
                "Close": 150.58,  # 陽線
                "Volume": 1000 + 49 * 10,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {"current_value": 70, "values": [50 + i * 0.4 for i in range(50)]},
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

    def _create_h4_data(self) -> Dict:
        """H4データ作成（大陰線引け坊主）"""
        # 価格データ（引け坊主パターン）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")

        # 価格データを作成
        prices = []
        for i in range(99):  # 最初の99期間は通常の価格
            price = 150.0 + i * 0.005
            prices.append(
                {
                    "Date": dates[i],
                    "Open": price - 0.02,
                    "High": price + 0.05,
                    "Low": price - 0.05,
                    "Close": price,
                    "Volume": 1000 + i * 5,
                }
            )

        # 大陰線引け坊主（ヒゲが少なく、実体が大きい）
        prices.append(
            {
                "Date": dates[99],
                "Open": 150.495,
                "High": 150.50,  # 上ヒゲが小さい
                "Low": 150.40,  # 下ヒゲが小さい
                "Close": 150.42,  # 陰線
                "Volume": 1000 + 99 * 5,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 30,
                "values": [50 + (i % 10 - 5) * 0.5 for i in range(100)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(100)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(100)]),
                "histogram": [0.05 + i * 0.002 for i in range(100)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.3 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.3 for p in prices]),
                "std": [0.3] * 100,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self) -> Dict:
        """H1データ作成（大陽線引け坊主）"""
        # 価格データ（引け坊主パターン）
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")

        # 価格データを作成
        prices = []
        for i in range(199):  # 最初の199期間は通常の価格
            price = 150.0 + i * 0.002
            prices.append(
                {
                    "Date": dates[i],
                    "Open": price - 0.01,
                    "High": price + 0.02,
                    "Low": price - 0.02,
                    "Close": price,
                    "Volume": 1000 + i * 2,
                }
            )

        # 大陽線引け坊主（ヒゲが少なく、実体が大きい）
        prices.append(
            {
                "Date": dates[199],
                "Open": 150.400,
                "High": 150.4006,  # 上ヒゲが小さい
                "Low": 150.4001,  # 下ヒゲが小さい
                "Close": 150.4005,  # 陽線
                "Volume": 1000 + 199 * 2,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 75,
                "values": [50 + (i % 15 - 7) * 0.3 for i in range(200)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(200)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(200)]),
                "histogram": [0.05 + i * 0.002 for i in range(200)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.3 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.3 for p in prices]),
                "std": [0.3] * 200,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self, test_case_index: int = 0) -> Dict:
        """M5データ作成（大陰線引け坊主）"""
        # 価格データ（引け坊主パターン）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")

        # 価格データを作成
        prices = []
        for i in range(499):  # 最初の499期間は通常の価格
            price = 150.0 + (i % 20 - 10) * 0.001
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

        # 複数の大陰線引け坊主パターンを試す
        test_cases = [
            # ケース1: 標準的な引け坊主
            {
                "Open": 150.010,
                "High": 150.0101,
                "Low": 150.0099,
                "Close": 150.0098,
            },
            # ケース2: より小さなヒゲ
            {
                "Open": 150.010,
                "High": 150.01005,
                "Low": 150.00995,
                "Close": 150.0099,
            },
            # ケース3: 最小ヒゲ
            {
                "Open": 150.010,
                "High": 150.01001,
                "Low": 150.00999,
                "Close": 150.00995,
            },
            # ケース4: 完全引け坊主
            {
                "Open": 150.010,
                "High": 150.010,
                "Low": 150.0099,
                "Close": 150.0099,
            },
        ]

        # 指定されたテストケースを使用
        test_case = test_cases[test_case_index]
        prices.append(
            {
                "Date": dates[499],
                "Open": test_case["Open"],
                "High": test_case["High"],
                "Low": test_case["Low"],
                "Close": test_case["Close"],
                "Volume": 1000 + 499,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 25,
                "values": [50 + (i % 25 - 12) * 0.2 for i in range(500)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(500)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(500)]),
                "histogram": [0.05 + i * 0.002 for i in range(500)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p["Close"] + 0.3 for p in prices]),
                "middle": pd.Series([p["Close"] for p in prices]),
                "lower": pd.Series([p["Close"] - 0.3 for p in prices]),
                "std": [0.3] * 500,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _analyze_conditions(self, test_data: Dict) -> Dict:
        """条件の詳細分析"""
        analysis = {}

        for timeframe, data in test_data.items():
            price_data = data.get("price_data", pd.DataFrame())

            timeframe_analysis = {}

            # 引け坊主パターン分析
            if not price_data.empty:
                latest_candle = price_data.iloc[-1]

                # 陽線/陰線チェック
                is_bullish = latest_candle["Close"] > latest_candle["Open"]
                is_bearish = latest_candle["Close"] < latest_candle["Open"]

                # ヒゲの計算
                open_price = latest_candle["Open"]
                close_price = latest_candle["Close"]
                high = latest_candle["High"]
                low = latest_candle["Low"]

                upper_wick = high - max(open_price, close_price)
                lower_wick = min(open_price, close_price) - low
                total_range = high - low

                if total_range > 0:
                    upper_wick_ratio = upper_wick / total_range
                    lower_wick_ratio = lower_wick / total_range

                    # 実体比率計算
                    body_size = abs(close_price - open_price)
                    body_ratio = body_size / total_range

                    # ヒゲの欠如チェック
                    wick_absence = (
                        (upper_wick_ratio <= 0.2 and lower_wick_ratio <= 0.2)
                        or (upper_wick_ratio <= 0.05 and lower_wick_ratio <= 0.3)
                        or (lower_wick_ratio <= 0.05 and upper_wick_ratio <= 0.3)
                    )

                    # 条件チェック
                    body_ratio_condition = body_ratio >= 0.6
                    wick_condition = wick_absence

                    timeframe_analysis["marubozu_pattern"] = {
                        "is_bullish": is_bullish,
                        "is_bearish": is_bearish,
                        "body_ratio": body_ratio,
                        "upper_wick_ratio": upper_wick_ratio,
                        "lower_wick_ratio": lower_wick_ratio,
                        "body_ratio_condition": body_ratio_condition,
                        "wick_condition": wick_condition,
                        "all_conditions_met": body_ratio_condition and wick_condition,
                    }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern9DetailedTester()
    results = await tester.test_pattern9_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン9が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン9は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
