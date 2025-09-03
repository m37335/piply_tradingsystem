#!/usr/bin/env python3
"""
パターン8詳細テストスクリプト
パターン8（赤三兵検出）専用の詳細テスト

パターン8の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.red_three_soldiers_detector import (
    RedThreeSoldiersDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern8DetailedTester:
    """パターン8詳細テストクラス"""

    def __init__(self):
        self.detector = RedThreeSoldiersDetector()

    async def test_pattern8_detailed(self) -> Dict:
        """パターン8詳細テスト実行"""
        logger.info("=== パターン8詳細テスト開始 ===")

        try:
            # パターン8の条件を満たすテストデータを作成
            test_data = self._create_pattern8_test_data()

            # 検出テスト
            result = self.detector.detect(test_data)

            # 結果分析
            if result is not None:
                logger.info("✅ パターン8検出成功！")
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
                logger.info("❌ パターン8は検出されませんでした")

                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)

                return {
                    "success": True,
                    "detected": False,
                    "condition_analysis": condition_analysis,
                }

        except Exception as e:
            logger.error(f"パターン8詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern8_test_data(self) -> Dict:
        """パターン8の条件を満たすテストデータ作成"""
        logger.info("パターン8用テストデータ作成中...")

        # パターン8の条件:
        # 実体比率: 30%以上
        # 終値上昇: 0.05%以上
        # 実体サイズ一貫性: 70%以内
        # 3本連続陽線

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
        """D1データ作成（赤三兵パターン）"""
        # 価格データ（赤三兵パターン）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")

        # 価格データを作成
        prices = []
        for i in range(47):  # 最初の47日は通常の価格
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

        # 赤三兵パターン（3本連続陽線）
        # 1本目
        prices.append(
            {
                "Date": dates[47],
                "Open": 150.47,
                "High": 150.55,
                "Low": 150.45,
                "Close": 150.52,  # 陽線
                "Volume": 1000 + 47 * 10,
            }
        )

        # 2本目
        prices.append(
            {
                "Date": dates[48],
                "Open": 150.52,
                "High": 150.60,
                "Low": 150.50,
                "Close": 150.58,  # 陽線、前日より上昇
                "Volume": 1000 + 48 * 10,
            }
        )

        # 3本目
        prices.append(
            {
                "Date": dates[49],
                "Open": 150.58,
                "High": 150.65,
                "Low": 150.56,
                "Close": 150.63,  # 陽線、前日より上昇
                "Volume": 1000 + 49 * 10,
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

    def _create_h4_data(self) -> Dict:
        """H4データ作成（赤三兵パターン）"""
        # 価格データ（赤三兵パターン）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")

        # 価格データを作成
        prices = []
        for i in range(97):  # 最初の97期間は通常の価格
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

        # 赤三兵パターン（3本連続陽線）
        # 1本目
        prices.append(
            {
                "Date": dates[97],
                "Open": 150.485,
                "High": 150.52,
                "Low": 150.48,
                "Close": 150.51,  # 陽線
                "Volume": 1000 + 97 * 5,
            }
        )

        # 2本目
        prices.append(
            {
                "Date": dates[98],
                "Open": 150.51,
                "High": 150.54,
                "Low": 150.50,
                "Close": 150.53,  # 陽線、前日より上昇
                "Volume": 1000 + 98 * 5,
            }
        )

        # 3本目
        prices.append(
            {
                "Date": dates[99],
                "Open": 150.53,
                "High": 150.56,
                "Low": 150.52,
                "Close": 150.55,  # 陽線、前日より上昇
                "Volume": 1000 + 99 * 5,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 60,
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
        """H1データ作成（赤三兵パターン）"""
        # 価格データ（赤三兵パターン）
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")

        # 価格データを作成
        prices = []
        for i in range(197):  # 最初の197期間は通常の価格
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

        # 赤三兵パターン（3本連続陽線）
        # 1本目
        prices.append(
            {
                "Date": dates[197],
                "Open": 150.39,
                "High": 150.42,
                "Low": 150.38,
                "Close": 150.41,  # 陽線
                "Volume": 1000 + 197 * 2,
            }
        )

        # 2本目
        prices.append(
            {
                "Date": dates[198],
                "Open": 150.41,
                "High": 150.44,
                "Low": 150.40,
                "Close": 150.43,  # 陽線、前日より上昇
                "Volume": 1000 + 198 * 2,
            }
        )

        # 3本目
        prices.append(
            {
                "Date": dates[199],
                "Open": 150.43,
                "High": 150.46,
                "Low": 150.42,
                "Close": 150.45,  # 陽線、前日より上昇
                "Volume": 1000 + 199 * 2,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 70,
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
        """M5データ作成（赤三兵パターン）"""
        # 価格データ（赤三兵パターン）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")

        # 価格データを作成
        prices = []
        for i in range(497):  # 最初の497期間は通常の価格
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

        # 赤三兵パターン（3本連続陽線）
        # 1本目
        prices.append(
            {
                "Date": dates[497],
                "Open": 150.005,
                "High": 150.012,
                "Low": 150.003,
                "Close": 150.010,  # 陽線
                "Volume": 1000 + 497,
            }
        )

        # 2本目
        prices.append(
            {
                "Date": dates[498],
                "Open": 150.010,
                "High": 150.015,
                "Low": 150.008,
                "Close": 150.013,  # 陽線、前日より上昇
                "Volume": 1000 + 498,
            }
        )

        # 3本目
        prices.append(
            {
                "Date": dates[499],
                "Open": 150.013,
                "High": 150.018,
                "Low": 150.011,
                "Close": 150.016,  # 陽線、前日より上昇
                "Volume": 1000 + 499,
            }
        )

        price_data = pd.DataFrame(prices)

        # 指標データ
        indicators = {
            "rsi": {
                "current_value": 75,
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

            # 赤三兵パターン分析
            if not price_data.empty and len(price_data) >= 3:
                candles = price_data.tail(3)

                # 3本連続陽線チェック
                three_bullish = True
                for _, candle in candles.iterrows():
                    if candle["Close"] <= candle["Open"]:
                        three_bullish = False
                        break

                # 終値上昇チェック
                higher_closes = True
                closes = candles["Close"].values
                for i in range(1, len(closes)):
                    if closes[i] <= closes[i - 1]:
                        higher_closes = False
                        break

                # 実体サイズ一貫性チェック
                body_sizes = []
                for _, candle in candles.iterrows():
                    body_size = abs(candle["Close"] - candle["Open"])
                    total_range = candle["High"] - candle["Low"]
                    body_ratio = body_size / total_range if total_range > 0 else 0
                    body_sizes.append(body_ratio)

                body_consistency = True
                if body_sizes:
                    # 実体比率30%以上チェック
                    for ratio in body_sizes:
                        if ratio < 0.3:
                            body_consistency = False
                            break

                    # 実体サイズ一貫性70%以内チェック
                    if max(body_sizes) - min(body_sizes) > 0.7:
                        body_consistency = False

                timeframe_analysis["red_three_soldiers"] = {
                    "three_bullish_candles": three_bullish,
                    "higher_closes": higher_closes,
                    "body_consistency": body_consistency,
                    "body_sizes": body_sizes,
                    "all_conditions_met": three_bullish
                    and higher_closes
                    and body_consistency,
                }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern8DetailedTester()
    results = await tester.test_pattern8_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン8が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン8は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
