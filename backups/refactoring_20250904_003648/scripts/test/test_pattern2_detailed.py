#!/usr/bin/env python3
"""
パターン2詳細テストスクリプト
パターン2（プルバック検出）専用の詳細テスト

パターン2の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.pullback_detector import (
    PullbackDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern2DetailedTester:
    """パターン2詳細テストクラス"""

    def __init__(self):
        self.detector = PullbackDetector()

    async def test_pattern2_detailed(self) -> Dict:
        """パターン2詳細テスト実行"""
        logger.info("=== パターン2詳細テスト開始 ===")

        try:
            # パターン2の条件を満たすテストデータを作成
            test_data = self._create_pattern2_test_data()

            # 検出テスト
            result = self.detector.detect(test_data)

            # 結果分析
            if result is not None:
                logger.info("✅ パターン2検出成功！")
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
                logger.info("❌ パターン2は検出されませんでした")

                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)

                return {
                    "success": True,
                    "detected": False,
                    "condition_analysis": condition_analysis,
                }

        except Exception as e:
            logger.error(f"パターン2詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern2_test_data(self) -> Dict:
        """パターン2の条件を満たすテストデータ作成"""
        logger.info("パターン2用テストデータ作成中...")

        # パターン2の条件:
        # D1: RSI 25-55 + MACD上昇
        # H4: RSI 25-45 + BB -1.5σ近接
        # H1: RSI 25-40 + BB -1.5σ近接
        # M5: RSI ≤ 35 + 価格反発サイン

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
        """D1データ作成（RSI 25-55 + MACD上昇）"""
        # 価格データ（下降トレンドから反発）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        prices = []

        for i in range(50):
            if i < 30:
                # 下降トレンド
                price = 150.0 - i * 0.3
            else:
                # 反発開始
                price = 141.0 + (i - 30) * 0.2
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.1 for p in prices],
                "High": [p + 0.2 for p in prices],
                "Low": [p - 0.2 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 10 for i in range(50)],
            }
        )

        # RSI計算（25-55の範囲）
        rsi_values = []
        for i in range(50):
            if i < 30:
                rsi_values.append(45 - i * 0.5)  # 徐々に下降
            else:
                rsi_values.append(30 + (i - 30) * 0.8)  # 徐々に上昇

        # MACDデータ（上昇傾向）
        macd_values = []
        signal_values = []
        for i in range(50):
            if i < 30:
                macd_values.append(0.5 - i * 0.02)
                signal_values.append(0.3 - i * 0.015)
            else:
                # 上昇傾向
                macd_values.append(-0.1 + (i - 30) * 0.03)
                signal_values.append(-0.15 + (i - 30) * 0.025)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": macd_values,
                "signal": signal_values,
                "histogram": [m - s for m, s in zip(macd_values, signal_values)],
            },
            "bollinger_bands": {
                "upper": [p + 0.5 for p in prices],
                "middle": prices,
                "lower": [p - 0.5 for p in prices],
                "std": [0.5] * 50,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h4_data(self) -> Dict:
        """H4データ作成（RSI 25-45 + BB -1.5σ近接）"""
        # 価格データ（ボリンジャーバンド下限に近接）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")
        prices = []

        for i in range(100):
            if i < 60:
                # 下降トレンド
                price = 150.0 - i * 0.15
            else:
                # ボリンジャーバンド下限の5%以内
                base_price = 141.0
                price = base_price + (i - 60) * 0.02
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.05 for p in prices],
                "High": [p + 0.1 for p in prices],
                "Low": [p - 0.1 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 5 for i in range(100)],
            }
        )

        # RSI計算（25-45の範囲）
        rsi_values = [35 + i * 0.1 for i in range(100)]

        # ボリンジャーバンド計算（価格が下限の5%以内になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            if i >= 60:
                # 価格が下限の5%以内になるように調整
                lower = price - 0.01  # 価格の1%下
                middle = price
                upper = price + 0.5
            else:
                lower = price - 0.5
                middle = price
                upper = price + 0.5

            bb_upper.append(upper)
            bb_middle.append(middle)
            bb_lower.append(lower)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": [0.1 + i * 0.01 for i in range(100)],
                "signal": [0.05 + i * 0.008 for i in range(100)],
                "histogram": [0.05 + i * 0.002 for i in range(100)],
            },
            "bollinger_bands": {
                "upper": bb_upper,
                "middle": bb_middle,
                "lower": bb_lower,
                "std": [0.5] * 100,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self) -> Dict:
        """H1データ作成（RSI 25-40 + BB -1.5σ近接）"""
        # H4と同様のデータ構造
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")
        prices = []

        for i in range(200):
            if i < 120:
                # 下降トレンド
                price = 150.0 - i * 0.08
            else:
                # ボリンジャーバンド下限の5%以内
                base_price = 141.0
                price = base_price + (i - 120) * 0.01
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.03 for p in prices],
                "High": [p + 0.05 for p in prices],
                "Low": [p - 0.05 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 2 for i in range(200)],
            }
        )

        # RSI計算（25-40の範囲）
        rsi_values = [30 + i * 0.05 for i in range(200)]

        # ボリンジャーバンド計算（価格が下限の5%以内になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            if i >= 120:
                # 価格が下限の5%以内になるように調整
                lower = price - 0.005  # 価格の0.5%下
                middle = price
                upper = price + 0.3
            else:
                lower = price - 0.3
                middle = price
                upper = price + 0.3

            bb_upper.append(upper)
            bb_middle.append(middle)
            bb_lower.append(lower)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": [0.1 + i * 0.01 for i in range(200)],
                "signal": [0.05 + i * 0.008 for i in range(200)],
                "histogram": [0.05 + i * 0.002 for i in range(200)],
            },
            "bollinger_bands": {
                "upper": bb_upper,
                "middle": bb_middle,
                "lower": bb_lower,
                "std": [0.3] * 200,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self) -> Dict:
        """M5データ作成（RSI ≤ 35 + 価格反発サイン）"""
        # 価格データ（反発サイン）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")
        prices = []

        for i in range(500):
            if i < 400:
                # 下降トレンド
                price = 150.0 - i * 0.02
            else:
                # 反発サイン（連続上昇）
                base_price = 142.0
                price = base_price + (i - 400) * 0.01
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.01 for p in prices],
                "High": [p + 0.02 for p in prices],
                "Low": [p - 0.02 for p in prices],
                "Close": prices,
                "Volume": [1000 + i for i in range(500)],
            }
        )

        # RSI計算（≤ 35）
        rsi_values = [30 + i * 0.01 for i in range(500)]

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": [0.1 + i * 0.01 for i in range(500)],
                "signal": [0.05 + i * 0.008 for i in range(500)],
                "histogram": [0.05 + i * 0.002 for i in range(500)],
            },
            "bollinger_bands": {
                "upper": [p + 0.3 for p in prices],
                "middle": prices,
                "lower": [p - 0.3 for p in prices],
                "std": [0.3] * 500,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _analyze_conditions(self, test_data: Dict) -> Dict:
        """条件の詳細分析"""
        analysis = {}

        for timeframe, data in test_data.items():
            indicators = data.get("indicators", {})
            price_data = data.get("price_data", pd.DataFrame())

            timeframe_analysis = {}

            # RSI分析
            if "rsi" in indicators:
                rsi_value = indicators["rsi"].get("current_value", 0)
                if timeframe == "D1":
                    condition_met = 25 <= rsi_value <= 55
                elif timeframe == "H4":
                    condition_met = 25 <= rsi_value <= 45
                elif timeframe == "H1":
                    condition_met = 25 <= rsi_value <= 40
                elif timeframe == "M5":
                    condition_met = rsi_value <= 35

                timeframe_analysis["rsi"] = {
                    "value": rsi_value,
                    "condition_met": condition_met,
                }

            # MACD分析（D1のみ）
            if timeframe == "D1" and "macd" in indicators:
                macd_data = indicators["macd"]
                if "macd" in macd_data:
                    macd_values = macd_data["macd"]
                    if len(macd_values) >= 3:
                        recent_macd = macd_values[-3:]
                        macd_rising = (
                            recent_macd[-1] > recent_macd[-2] > recent_macd[-3]
                        )

                        timeframe_analysis["macd"] = {
                            "recent_values": recent_macd,
                            "rising_condition": macd_rising,
                        }

            # ボリンジャーバンド分析（H4, H1のみ）
            if timeframe in ["H4", "H1"] and "bollinger_bands" in indicators:
                bb_data = indicators["bollinger_bands"]
                if "lower" in bb_data and not price_data.empty:
                    current_price = price_data["Close"].iloc[-1]
                    bb_lower = bb_data["lower"][-1]

                    # -1.5σ近接チェック
                    price_diff = abs(current_price - bb_lower)
                    bb_near = price_diff <= bb_lower * 0.05

                    timeframe_analysis["bollinger_bands"] = {
                        "current_price": current_price,
                        "bb_lower": bb_lower,
                        "near_condition": bb_near,
                    }

            # 価格反発分析（M5のみ）
            if timeframe == "M5" and not price_data.empty:
                if len(price_data) >= 3:
                    recent_prices = price_data["Close"].iloc[-3:]
                    bounce_condition = (
                        recent_prices.iloc[-1] > recent_prices.iloc[-2]
                        and recent_prices.iloc[-2] > recent_prices.iloc[-3]
                    )

                    timeframe_analysis["price_bounce"] = {
                        "recent_prices": recent_prices.tolist(),
                        "bounce_condition": bounce_condition,
                    }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern2DetailedTester()
    results = await tester.test_pattern2_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン2が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン2は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
