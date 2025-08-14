#!/usr/bin/env python3
"""
パターン7詳細テストスクリプト
パターン7（つつみ足検出）専用の詳細テスト

パターン7の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.engulfing_pattern_detector import (
    EngulfingPatternDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern7DetailedTester:
    """パターン7詳細テストクラス"""

    def __init__(self):
        self.detector = EngulfingPatternDetector()

    async def test_pattern7_detailed(self) -> Dict:
        """パターン7詳細テスト実行"""
        logger.info("=== パターン7詳細テスト開始 ===")

        try:
            # パターン7の条件を満たすテストデータを作成
            test_data = self._create_pattern7_test_data()

            # 検出テスト
            result = self.detector.detect(test_data)

            # 結果分析
            if result is not None:
                logger.info("✅ パターン7検出成功！")
                logger.info(f"  信頼度: {result.get('confidence_score', 'N/A')}")
                logger.info(f"  条件: {result.get('conditions_met', {})}")

                return {
                    "success": True,
                    "detected": True,
                    "confidence_score": result.get("confidence_score"),
                    "conditions_met": result.get("conditions_met"),
                    "pattern_info": result,
                }
            else:
                logger.info("❌ パターン7は検出されませんでした")

                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)

                return {
                    "success": True,
                    "detected": False,
                    "condition_analysis": condition_analysis,
                }

        except Exception as e:
            logger.error(f"パターン7詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern7_test_data(self) -> Dict:
        """パターン7の条件を満たすテストデータ作成"""
        logger.info("パターン7用テストデータ作成中...")

        # パターン7の条件:
        # 実体比率: 40%以上
        # 包み込み比率: 105%以上
        # 包み込み条件: 完全包み込みまたは部分包み込み（実体の80%以上）

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

        # M5データ作成
        m5_data = self._create_m5_data()
        test_data["M5"] = m5_data

        logger.info("✅ テストデータ作成完了")
        return test_data

    def _create_d1_data(self) -> Dict:
        """D1データ作成（陽のつつみ足）"""
        # 価格データ（つつみ足パターン）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

        # 前日（陰線）
        previous_open = 150.0
        previous_close = 149.5  # 陰線
        previous_high = 150.2
        previous_low = 149.3

        # 当日（陽線で前日を包み込む）
        current_open = 149.4
        current_close = 150.3  # 陽線
        current_high = 150.4
        current_low = 149.2

        # 価格データを作成
        prices = []
        for i in range(48):  # 最初の48日は通常の価格
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

        # 前日（陰線）
        prices.append(
            {
                "Date": dates[48],
                "Open": previous_open,
                "High": previous_high,
                "Low": previous_low,
                "Close": previous_close,
                "Volume": 1000 + 48 * 10,
            }
        )

        # 当日（陽線で包み込む）
        prices.append(
            {
                "Date": dates[49],
                "Open": current_open,
                "High": current_high,
                "Low": current_low,
                "Close": current_close,
                "Volume": 1000 + 49 * 10,
            }
        )

        price_data = pd.DataFrame(prices)
        # カラム名を小文字に統一
        price_data.columns = price_data.columns.str.lower()

        # 指標データ
        indicators = {
            "rsi": {"current_value": 55, "values": [50 + i * 0.1 for i in range(50)]},
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
        """H4データ作成（陰のつつみ足）"""
        # 価格データ（つつみ足パターン）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")

        # 前日（陽線）
        previous_open = 150.0
        previous_close = 150.5  # 陽線
        previous_high = 150.6
        previous_low = 149.9

        # 当日（陰線で前日を包み込む）
        current_open = 150.6
        current_close = 149.8  # 陰線
        current_high = 150.7
        current_low = 149.7

        # 価格データを作成
        prices = []
        for i in range(98):  # 最初の98期間は通常の価格
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

        # 前日（陽線）
        prices.append(
            {
                "Date": dates[98],
                "Open": previous_open,
                "High": previous_high,
                "Low": previous_low,
                "Close": previous_close,
                "Volume": 1000 + 98 * 5,
            }
        )

        # 当日（陰線で包み込む）
        prices.append(
            {
                "Date": dates[99],
                "Open": current_open,
                "High": current_high,
                "Low": current_low,
                "Close": current_close,
                "Volume": 1000 + 99 * 5,
            }
        )

        price_data = pd.DataFrame(prices)
        # カラム名を小文字に統一
        price_data.columns = price_data.columns.str.lower()

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 45,
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
        """H1データ作成（陽のつつみ足）"""
        # H4と同様のデータ構造
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")

        # 前日（陰線）
        previous_open = 150.0
        previous_close = 149.7  # 陰線
        previous_high = 150.1
        previous_low = 149.6

        # 当日（陽線で前日を包み込む）
        current_open = 149.6
        current_close = 150.2  # 陽線
        current_high = 150.3
        current_low = 149.5

        # 価格データを作成
        prices = []
        for i in range(198):  # 最初の198期間は通常の価格
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

        # 前日（陰線）
        prices.append(
            {
                "Date": dates[198],
                "Open": previous_open,
                "High": previous_high,
                "Low": previous_low,
                "Close": previous_close,
                "Volume": 1000 + 198 * 2,
            }
        )

        # 当日（陽線で包み込む）
        prices.append(
            {
                "Date": dates[199],
                "Open": current_open,
                "High": current_high,
                "Low": current_low,
                "Close": current_close,
                "Volume": 1000 + 199 * 2,
            }
        )

        price_data = pd.DataFrame(prices)
        # カラム名を小文字に統一
        price_data.columns = price_data.columns.str.lower()

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 60,
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

    def _create_m5_data(self) -> Dict:
        """M5データ作成（陰のつつみ足）"""
        # 価格データ（つつみ足パターン）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")

        # 前日（陽線）
        previous_open = 150.0
        previous_close = 150.2  # 陽線
        previous_high = 150.25
        previous_low = 149.98

        # 当日（陰線で前日を包み込む）
        current_open = 150.25
        current_close = 149.95  # 陰線
        current_high = 150.26
        current_low = 149.94

        # 価格データを作成
        prices = []
        for i in range(498):  # 最初の498期間は通常の価格
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

        # 前日（陽線）
        prices.append(
            {
                "Date": dates[498],
                "Open": previous_open,
                "High": previous_high,
                "Low": previous_low,
                "Close": previous_close,
                "Volume": 1000 + 498,
            }
        )

        # 当日（陰線で包み込む）
        prices.append(
            {
                "Date": dates[499],
                "Open": current_open,
                "High": current_high,
                "Low": current_low,
                "Close": current_close,
                "Volume": 1000 + 499,
            }
        )

        price_data = pd.DataFrame(prices)
        # カラム名を小文字に統一
        price_data.columns = price_data.columns.str.lower()
        
        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 40,
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

            # つつみ足分析
            if not price_data.empty and len(price_data) >= 2:
                current_candle = price_data.iloc[-1]
                previous_candle = price_data.iloc[-2]

                # 実体比率計算
                current_body_size = abs(
                    current_candle["close"] - current_candle["open"]
                )
                current_total_size = current_candle["high"] - current_candle["low"]
                current_body_ratio = (
                    current_body_size / current_total_size
                    if current_total_size > 0
                    else 0
                )

                previous_body_size = abs(
                    previous_candle["close"] - previous_candle["open"]
                )
                engulfing_ratio = (
                    current_body_size / previous_body_size
                    if previous_body_size > 0
                    else 0
                )

                # 包み込み条件チェック
                current_body_high = max(current_candle["open"], current_candle["close"])
                current_body_low = min(current_candle["open"], current_candle["close"])
                previous_body_high = max(
                    previous_candle["open"], previous_candle["close"]
                )
                previous_body_low = min(
                    previous_candle["open"], previous_candle["close"]
                )

                # 完全包み込み
                complete_engulfing = (
                    current_body_high >= previous_body_high
                    and current_body_low <= previous_body_low
                )

                # 部分包み込み
                partial_engulfing = (
                    current_body_high >= previous_body_high * 0.95
                    and current_body_low <= previous_body_low * 1.05
                    and current_body_size >= previous_body_size * 0.8
                )

                # 条件チェック
                body_ratio_condition = current_body_ratio >= 0.4
                engulfing_ratio_condition = engulfing_ratio >= 1.05
                engulfing_condition = complete_engulfing or partial_engulfing

                timeframe_analysis["engulfing_pattern"] = {
                    "current_body_ratio": current_body_ratio,
                    "engulfing_ratio": engulfing_ratio,
                    "complete_engulfing": complete_engulfing,
                    "partial_engulfing": partial_engulfing,
                    "body_ratio_condition": body_ratio_condition,
                    "engulfing_ratio_condition": engulfing_ratio_condition,
                    "engulfing_condition": engulfing_condition,
                    "all_conditions_met": body_ratio_condition
                    and engulfing_ratio_condition
                    and engulfing_condition,
                }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern7DetailedTester()
    results = await tester.test_pattern7_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン7が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン7は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
