#!/usr/bin/env python3
"""
パターン4詳細テストスクリプト
パターン4（ブレイクアウト検出）専用の詳細テスト

パターン4の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.breakout_detector import (
    BreakoutDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern4DetailedTester:
    """パターン4詳細テストクラス"""

    def __init__(self):
        self.detector = BreakoutDetector()

    async def test_pattern4_detailed(self) -> Dict:
        """パターン4詳細テスト実行"""
        logger.info("=== パターン4詳細テスト開始 ===")

        try:
            # パターン4の条件を満たすテストデータを作成
            test_data = self._create_pattern4_test_data()

            # 検出テスト
            result = self.detector.detect(test_data)

            # 結果分析
            if result is not None:
                logger.info("✅ パターン4検出成功！")
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
                logger.info("❌ パターン4は検出されませんでした")

                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)

                return {
                    "success": True,
                    "detected": False,
                    "condition_analysis": condition_analysis,
                }

        except Exception as e:
            logger.error(f"パターン4詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern4_test_data(self) -> Dict:
        """パターン4の条件を満たすテストデータ作成"""
        logger.info("パターン4用テストデータ作成中...")

        # パターン4の条件:
        # D1: RSI 45-75 + MACD上昇トレンド（3期間連続）
        # H4: ボリンジャーバンド +1.5σ近接（5%以内）
        # H1: ボリンジャーバンド +1.5σ近接（5%以内）
        # M5: 上昇モメンタム（3期間連続上昇）

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
        """D1データ作成（RSI 45-75 + MACD上昇トレンド）"""
        # 価格データ（上昇トレンド）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        prices = []

        for i in range(50):
            # 上昇トレンド
            price = 150.0 + i * 0.3
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

        # RSIデータ（45-75の範囲）
        rsi_values = [60 + i * 0.3 for i in range(50)]

        # MACDデータ（3期間連続上昇）
        macd_values = []
        signal_values = []
        for i in range(50):
            if i < 47:
                macd_values.append(0.1 + i * 0.02)
                signal_values.append(0.05 + i * 0.015)
            else:
                # 直近3期間で連続上昇
                base_macd = 1.04
                base_signal = 0.755
                macd_values.append(base_macd + (i - 47) * 0.05)
                signal_values.append(base_signal + (i - 47) * 0.03)

        # pandas Seriesに変換
        macd_series = pd.Series(macd_values)
        signal_series = pd.Series(signal_values)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": macd_series,
                "signal": signal_series,
                "histogram": [m - s for m, s in zip(macd_values, signal_values)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p + 0.5 for p in prices]),
                "middle": pd.Series(prices),
                "lower": pd.Series([p - 0.5 for p in prices]),
                "std": [0.5] * 50,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h4_data(self) -> Dict:
        """H4データ作成（ボリンジャーバンド +1.5σ近接）"""
        # 価格データ（ボリンジャーバンド上限に近接）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")
        prices = []

        for i in range(100):
            if i < 95:
                price = 150.0 + i * 0.1
            else:
                # ボリンジャーバンド上限の5%以内
                base_price = 159.5
                price = base_price + (i - 95) * 0.02
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

        # ボリンジャーバンド計算（価格が上限の5%以内になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            if i >= 95:
                # 価格が上限の5%以内になるように調整
                upper = price + 0.01  # 価格の1%上
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
            "rsi": {"current_value": 65, "values": [60 + i * 0.05 for i in range(100)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(100)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(100)]),
                "histogram": [0.05 + i * 0.002 for i in range(100)],
            },
            "bollinger_bands": {
                "upper": pd.Series(bb_upper),
                "middle": pd.Series(bb_middle),
                "lower": pd.Series(bb_lower),
                "std": [0.5] * 100,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self) -> Dict:
        """H1データ作成（ボリンジャーバンド +1.5σ近接）"""
        # H4と同様のデータ構造
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")
        prices = []

        for i in range(200):
            if i < 195:
                price = 150.0 + i * 0.05
            else:
                # ボリンジャーバンド上限の5%以内
                base_price = 159.75
                price = base_price + (i - 195) * 0.01
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

        # ボリンジャーバンド計算（価格が上限の5%以内になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            if i >= 195:
                # 価格が上限の5%以内になるように調整
                upper = price + 0.005  # 価格の0.5%上
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
            "rsi": {
                "current_value": 65,
                "values": [60 + i * 0.025 for i in range(200)],
            },
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(200)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(200)]),
                "histogram": [0.05 + i * 0.002 for i in range(200)],
            },
            "bollinger_bands": {
                "upper": pd.Series(bb_upper),
                "middle": pd.Series(bb_middle),
                "lower": pd.Series(bb_lower),
                "std": [0.3] * 200,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self) -> Dict:
        """M5データ作成（上昇モメンタム）"""
        # 価格データ（3期間連続上昇）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")
        prices = []

        for i in range(500):
            if i < 497:
                price = 150.0 + i * 0.02
            else:
                # 直近3期間で連続上昇
                base_price = 159.94
                price = base_price + (i - 497) * 0.03
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

        indicators = {
            "rsi": {"current_value": 65, "values": [60 + i * 0.01 for i in range(500)]},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(500)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(500)]),
                "histogram": [0.05 + i * 0.002 for i in range(500)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p + 0.3 for p in prices]),
                "middle": pd.Series(prices),
                "lower": pd.Series([p - 0.3 for p in prices]),
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

            # RSI分析（D1のみ）
            if timeframe == "D1" and "rsi" in indicators:
                rsi_value = indicators["rsi"].get("current_value", 0)
                rsi_condition = 45 <= rsi_value <= 75

                timeframe_analysis["rsi"] = {
                    "value": rsi_value,
                    "condition_met": rsi_condition,
                }

            # MACD分析（D1のみ）
            if timeframe == "D1" and "macd" in indicators:
                macd_data = indicators["macd"]
                if "macd" in macd_data:
                    macd_values = macd_data["macd"]
                    if len(macd_values) >= 3:
                        recent_macd = macd_values[-3:]
                        macd_trend = recent_macd[-1] > recent_macd[-2] > recent_macd[-3]

                        timeframe_analysis["macd"] = {
                            "recent_values": recent_macd,
                            "trend_condition": macd_trend,
                        }

            # ボリンジャーバンド分析（H4, H1のみ）
            if timeframe in ["H4", "H1"] and "bollinger_bands" in indicators:
                bb_data = indicators["bollinger_bands"]
                if "upper" in bb_data and not price_data.empty:
                    current_price = price_data["Close"].iloc[-1]
                    upper_band = bb_data["upper"][-1]

                    # +1.5σ近接チェック
                    price_diff = abs(current_price - upper_band)
                    bb_near = price_diff <= upper_band * 0.05

                    timeframe_analysis["bollinger_bands"] = {
                        "current_price": current_price,
                        "upper_band": upper_band,
                        "near_condition": bb_near,
                    }

            # モメンタム分析（M5のみ）
            if timeframe == "M5" and not price_data.empty:
                if len(price_data) >= 5:
                    recent_prices = price_data["Close"].iloc[-3:]
                    if len(recent_prices) >= 3:
                        momentum_condition = (
                            recent_prices.iloc[-1]
                            > recent_prices.iloc[-2]
                            > recent_prices.iloc[-3]
                        )

                        timeframe_analysis["momentum"] = {
                            "recent_prices": recent_prices.tolist(),
                            "momentum_condition": momentum_condition,
                        }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern4DetailedTester()
    results = await tester.test_pattern4_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン4が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン4は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
