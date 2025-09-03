#!/usr/bin/env python3
"""
パターン1詳細テストスクリプト
パターン1（トレンド転換検出）専用の詳細テスト

パターン1の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import numpy as np
import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.trend_reversal_detector import (
    TrendReversalDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern1DetailedTester:
    """パターン1詳細テストクラス"""

    def __init__(self):
        self.detector = TrendReversalDetector()

    async def test_pattern1_detailed(self) -> Dict:
        """パターン1詳細テスト実行"""
        logger.info("=== パターン1詳細テスト開始 ===")

        try:
            # パターン1の条件を満たすテストデータを作成
            test_data = self._create_pattern1_test_data()

            # 検出テスト
            result = self.detector.detect(test_data)

            # 結果分析
            if result is not None:
                logger.info("✅ パターン1検出成功！")
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
                logger.info("❌ パターン1は検出されませんでした")

                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)

                return {
                    "success": True,
                    "detected": False,
                    "condition_analysis": condition_analysis,
                }

        except Exception as e:
            logger.error(f"パターン1詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern1_test_data(self) -> Dict:
        """パターン1の条件を満たすテストデータ作成"""
        logger.info("パターン1用テストデータ作成中...")

        # パターン1の条件:
        # D1: RSI > 65 + MACDデッドクロス
        # H4: RSI > 65 + BB +1.5σタッチ
        # H1: RSI > 65 + BB +1.5σタッチ
        # M5: RSI > 65 + ヒゲ形成

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
        """D1データ作成（RSI > 65 + MACD下降）"""
        # 価格データ（上昇トレンドから下降転換）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        prices = []

        for i in range(50):
            if i < 30:
                # 上昇トレンド
                price = 150.0 + i * 0.5
            else:
                # 下降転換
                price = 165.0 - (i - 30) * 0.8
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.2 for p in prices],
                "High": [p + 0.3 for p in prices],
                "Low": [p - 0.3 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 10 for i in range(50)],
            }
        )

        # RSI計算（> 65になるように調整）
        rsi_values = []
        for i in range(50):
            if i < 30:
                rsi_values.append(60 + i * 0.5)  # 徐々に上昇
            else:
                rsi_values.append(75 - (i - 30) * 0.3)  # 徐々に下降

        # MACDデータ（確実に下降するように調整）
        macd_values = []
        signal_values = []
        for i in range(50):
            if i < 30:
                macd_values.append(0.5 + i * 0.1)
                signal_values.append(0.3 + i * 0.08)
            else:
                # 確実に下降
                macd_values.append(3.5 - (i - 30) * 0.2)  # より急激な下降
                signal_values.append(2.7 - (i - 30) * 0.15)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},  # 最新値
            "macd": {
                "macd": macd_values,
                "signal": signal_values,
                "histogram": [m - s for m, s in zip(macd_values, signal_values)],
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h4_data(self) -> Dict:
        """H4データ作成（RSI > 65 + BB +1.5σ近接）"""
        # 価格データ（ボリンジャーバンド上限に近接）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")
        prices = []

        for i in range(100):
            if i < 60:
                # 上昇トレンド
                price = 150.0 + i * 0.2
            else:
                # ボリンジャーバンド上限の5%以内
                base_price = 162.0
                price = base_price + (i - 60) * 0.02
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.1 for p in prices],
                "High": [p + 0.2 for p in prices],
                "Low": [p - 0.2 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 5 for i in range(100)],
            }
        )

        # RSI計算（> 65）
        rsi_values = [65 + i * 0.1 for i in range(100)]

        # ボリンジャーバンド計算（価格が上限の5%以内になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            if i >= 60:
                # 価格が上限の5%以内になるように調整
                upper = price + 0.02  # 価格の2%上
                middle = price
                lower = price - 0.5
            else:
                upper = price + 0.5
                middle = price
                lower = price - 0.5

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
        """H1データ作成（RSI > 65 + BB +1.5σ近接）"""
        # H4と同様のデータ構造
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")
        prices = []

        for i in range(200):
            if i < 120:
                # 上昇トレンド
                price = 150.0 + i * 0.1
            else:
                # ボリンジャーバンド上限の5%以内
                base_price = 162.0
                price = base_price + (i - 120) * 0.01
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.05 for p in prices],
                "High": [p + 0.1 for p in prices],
                "Low": [p - 0.1 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 2 for i in range(200)],
            }
        )

        # RSI計算（> 65）
        rsi_values = [65 + i * 0.05 for i in range(200)]

        # ボリンジャーバンド計算（価格が上限の5%以内になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            if i >= 120:
                # 価格が上限の5%以内になるように調整
                upper = price + 0.01  # 価格の1%上
                middle = price
                lower = price - 0.3
            else:
                upper = price + 0.3
                middle = price
                lower = price - 0.3

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
        """M5データ作成（RSI > 65 + ヒゲ形成）"""
        # 価格データ（ヒゲ形成）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")
        prices = []

        for i in range(500):
            if i < 300:
                # 上昇トレンド
                price = 150.0 + i * 0.02
            else:
                # ヒゲ形成
                price = 156.0 + (i - 300) * 0.01
            prices.append(price)

        # ヒゲ形成のための価格調整（確実にヒゲが形成されるように）
        highs = []
        lows = []
        opens = []

        for i, price in enumerate(prices):
            if i >= 450:  # 最後の50期間で確実にヒゲ形成
                open_price = price - 0.02
                high = price + 0.15  # 上ヒゲ（0.15）
                low = price - 0.08  # 下ヒゲ（0.08）
                close = price
            else:
                open_price = price - 0.02
                high = price + 0.05
                low = price - 0.05
                close = price

            opens.append(open_price)
            highs.append(high)
            lows.append(low)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": opens,
                "High": highs,
                "Low": lows,
                "Close": prices,
                "Volume": [1000 + i for i in range(500)],
            }
        )

        # RSI計算（> 65）
        rsi_values = [65 + i * 0.02 for i in range(500)]

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": [0.1 + i * 0.01 for i in range(500)],
                "signal": [0.05 + i * 0.008 for i in range(500)],
                "histogram": [0.05 + i * 0.002 for i in range(500)],
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
                timeframe_analysis["rsi"] = {
                    "value": rsi_value,
                    "condition_met": rsi_value > 65,
                }

            # MACD分析（D1のみ）
            if timeframe == "D1" and "macd" in indicators:
                macd_data = indicators["macd"]
                if "macd" in macd_data and "signal" in macd_data:
                    macd_values = macd_data["macd"]
                    signal_values = macd_data["signal"]

                    # デッドクロスチェック
                    if len(macd_values) >= 2 and len(signal_values) >= 2:
                        current_macd = macd_values[-1]
                        current_signal = signal_values[-1]
                        prev_macd = macd_values[-2]
                        prev_signal = signal_values[-2]

                        dead_cross = (
                            prev_macd > prev_signal and current_macd < current_signal
                        )

                        timeframe_analysis["macd"] = {
                            "current_macd": current_macd,
                            "current_signal": current_signal,
                            "dead_cross": dead_cross,
                        }

            # ボリンジャーバンド分析（H4, H1のみ）
            if timeframe in ["H4", "H1"] and "bollinger_bands" in indicators:
                bb_data = indicators["bollinger_bands"]
                if "upper" in bb_data and not price_data.empty:
                    current_price = price_data["Close"].iloc[-1]
                    bb_upper = bb_data["upper"][-1]

                    # +1.5σタッチチェック
                    bb_touch = abs(current_price - bb_upper) < 0.1

                    timeframe_analysis["bollinger_bands"] = {
                        "current_price": current_price,
                        "bb_upper": bb_upper,
                        "touch_condition": bb_touch,
                    }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern1DetailedTester()
    results = await tester.test_pattern1_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン1が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン1は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
