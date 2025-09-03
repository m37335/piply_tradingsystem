#!/usr/bin/env python3
"""
パターン5詳細テストスクリプト
パターン5（RSI戦い検出）専用の詳細テスト

パターン5の条件を満たすテストデータを生成して検出テストを行う
"""

import asyncio
import logging
import sys
from typing import Dict

import pandas as pd

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.pattern_detectors.rsi_battle_detector import (
    RSIBattleDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Pattern5DetailedTester:
    """パターン5詳細テストクラス"""

    def __init__(self):
        self.detector = RSIBattleDetector()

    async def test_pattern5_detailed(self) -> Dict:
        """パターン5詳細テスト実行"""
        logger.info("=== パターン5詳細テスト開始 ===")

        try:
            # パターン5の条件を満たすテストデータを作成
            test_data = self._create_pattern5_test_data()

            # 検出テスト
            result = self.detector.detect(test_data)

            # 結果分析
            if result is not None:
                logger.info("✅ パターン5検出成功！")
                logger.info(f"  信頼度: {result.get('confidence_score', 'N/A')}")
                logger.info(f"  条件: {result.get('conditions_met', {})}")

                return {
                    "success": True,
                    "detected": True,
                    "confidence_score": result.get("confidence_score"),
                    "pattern_info": result,
                }
            else:
                logger.info("❌ パターン5は検出されませんでした")

                # 条件の詳細分析
                condition_analysis = self._analyze_conditions(test_data)

                return {
                    "success": True,
                    "detected": False,
                    "condition_analysis": condition_analysis,
                }

        except Exception as e:
            logger.error(f"パターン5詳細テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_pattern5_test_data(self) -> Dict:
        """パターン5の条件を満たすテストデータ作成"""
        logger.info("パターン5用テストデータ作成中...")

        # パターン5の条件:
        # D1: RSI 40-60 + MACDゼロライン付近（±0.2）
        # H4: RSI 40-60 + ボリンジャーバンドミドル付近（±0.5%）
        # H1: RSI 40-60 + 価格変動増加（0.1%以上）
        # M5: RSI 50ライン攻防（40-60範囲で50を跨ぐ）

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
        """D1データ作成（RSI 40-60 + MACDゼロライン付近）"""
        # 価格データ（横ばい）
        dates = pd.date_range(start="2024-01-01", periods=50, freq="D")
        prices = []

        for i in range(50):
            # 横ばいトレンド（RSI戦いの状況）
            price = 150.0 + (i % 3 - 1) * 0.1  # -0.1, 0, +0.1の繰り返し
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.05 for p in prices],
                "High": [p + 0.1 for p in prices],
                "Low": [p - 0.1 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 10 for i in range(50)],
            }
        )

        # RSIデータ（40-60の範囲）
        rsi_values = [50 + (i % 5 - 2) * 2 for i in range(50)]  # 46-54の範囲

        # MACDデータ（ゼロライン付近）
        macd_values = []
        signal_values = []
        for i in range(50):
            # MACDがゼロライン付近（±0.2以内）
            macd_values.append(0.1 + (i % 3 - 1) * 0.05)
            signal_values.append(0.05 + (i % 3 - 1) * 0.03)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": pd.Series(macd_values),
                "signal": pd.Series(signal_values),
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
        """H4データ作成（RSI 40-60 + ボリンジャーバンドミドル付近）"""
        # 価格データ（ボリンジャーバンドミドル付近）
        dates = pd.date_range(start="2024-01-01", periods=100, freq="4H")
        prices = []

        for i in range(100):
            # ボリンジャーバンドミドル付近（±0.5%以内）
            base_price = 150.0
            price = base_price + (i % 3 - 1) * 0.02  # 小さな変動
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.02 for p in prices],
                "High": [p + 0.05 for p in prices],
                "Low": [p - 0.05 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 5 for i in range(100)],
            }
        )

        # RSIデータ（40-60の範囲）
        rsi_values = [50 + (i % 7 - 3) * 1.5 for i in range(100)]  # 45.5-54.5の範囲

        # ボリンジャーバンド計算（価格がミドル付近になるように）
        bb_upper = []
        bb_middle = []
        bb_lower = []

        for i, price in enumerate(prices):
            # 価格がミドル付近になるように調整
            middle = price
            upper = price + 0.3
            lower = price - 0.3

            bb_upper.append(upper)
            bb_middle.append(middle)
            bb_lower.append(lower)

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(100)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(100)]),
                "histogram": [0.05 + i * 0.002 for i in range(100)],
            },
            "bollinger_bands": {
                "upper": pd.Series(bb_upper),
                "middle": pd.Series(bb_middle),
                "lower": pd.Series(bb_lower),
                "std": [0.3] * 100,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_h1_data(self) -> Dict:
        """H1データ作成（RSI 40-60 + 価格変動増加）"""
        # 価格データ（変動増加）
        dates = pd.date_range(start="2024-01-01", periods=200, freq="H")
        prices = []

        for i in range(200):
            # 価格変動を増加させる（0.1%以上の変動）
            base_price = 150.0
            if i < 197:
                price = base_price + (i % 3 - 1) * 0.05
            else:
                # 直近3期間で変動を増加
                price = base_price + (i - 197) * 0.2  # 0.2%の変動
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.01 for p in prices],
                "High": [p + 0.02 for p in prices],
                "Low": [p - 0.02 for p in prices],
                "Close": prices,
                "Volume": [1000 + i * 2 for i in range(200)],
            }
        )

        # RSIデータ（40-60の範囲）
        rsi_values = [50 + (i % 5 - 2) * 1 for i in range(200)]  # 48-52の範囲

        indicators = {
            "rsi": {"current_value": rsi_values[-1], "values": rsi_values},
            "macd": {
                "macd": pd.Series([0.1 + i * 0.01 for i in range(200)]),
                "signal": pd.Series([0.05 + i * 0.008 for i in range(200)]),
                "histogram": [0.05 + i * 0.002 for i in range(200)],
            },
            "bollinger_bands": {
                "upper": pd.Series([p + 0.3 for p in prices]),
                "middle": pd.Series(prices),
                "lower": pd.Series([p - 0.3 for p in prices]),
                "std": [0.3] * 200,
            },
        }

        return {"price_data": price_data, "indicators": indicators}

    def _create_m5_data(self) -> Dict:
        """M5データ作成（RSI 50ライン攻防）"""
        # 価格データ（横ばい）
        dates = pd.date_range(start="2024-01-01", periods=500, freq="5min")
        prices = []

        for i in range(500):
            # 横ばいトレンド
            price = 150.0 + (i % 5 - 2) * 0.01
            prices.append(price)

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.005 for p in prices],
                "High": [p + 0.01 for p in prices],
                "Low": [p - 0.01 for p in prices],
                "Close": prices,
                "Volume": [1000 + i for i in range(500)],
            }
        )

        # RSIデータ（50ライン攻防）
        rsi_values = []
        for i in range(500):
            if i < 495:
                # 50の±10の範囲で変動
                rsi_values.append(50 + (i % 7 - 3) * 2)
            else:
                # 直近5期間で50を跨ぐ
                if i == 495:
                    rsi_values.append(45)  # 50未満
                elif i == 496:
                    rsi_values.append(48)
                elif i == 497:
                    rsi_values.append(52)  # 50超過
                elif i == 498:
                    rsi_values.append(55)
                else:
                    rsi_values.append(50)  # 50付近

        indicators = {
            "rsi": {
                "current_value": rsi_values[-1],
                "values": rsi_values,
                "series": pd.Series(rsi_values),
            },
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

            # RSI分析
            if "rsi" in indicators:
                rsi_value = indicators["rsi"].get("current_value", 0)
                rsi_condition = 40 <= rsi_value <= 60

                timeframe_analysis["rsi"] = {
                    "value": rsi_value,
                    "condition_met": rsi_condition,
                }

            # MACD分析（D1のみ）
            if timeframe == "D1" and "macd" in indicators:
                macd_data = indicators["macd"]
                if "macd" in macd_data and "signal" in macd_data:
                    macd_series = macd_data["macd"]
                    signal_series = macd_data["signal"]

                    if hasattr(macd_series, "iloc"):
                        current_macd = macd_series.iloc[-1]
                        current_signal = signal_series.iloc[-1]
                    else:
                        current_macd = macd_series[-1]
                        current_signal = signal_series[-1]

                    macd_condition = (
                        abs(current_macd) <= 0.2 and abs(current_signal) <= 0.2
                    )

                    timeframe_analysis["macd"] = {
                        "current_macd": current_macd,
                        "current_signal": current_signal,
                        "condition_met": macd_condition,
                    }

            # ボリンジャーバンド分析（H4のみ）
            if timeframe == "H4" and "bollinger_bands" in indicators:
                bb_data = indicators["bollinger_bands"]
                if "middle" in bb_data and not price_data.empty:
                    current_price = price_data["Close"].iloc[-1]
                    bb_middle = bb_data["middle"]

                    if hasattr(bb_middle, "iloc"):
                        current_bb_middle = bb_middle.iloc[-1]
                    else:
                        current_bb_middle = bb_middle[-1]

                    bb_condition = (
                        abs(current_price - current_bb_middle) / current_bb_middle
                        <= 0.005
                    )

                    timeframe_analysis["bollinger_bands"] = {
                        "current_price": current_price,
                        "bb_middle": current_bb_middle,
                        "condition_met": bb_condition,
                    }

            # 価格変動分析（H1のみ）
            if timeframe == "H1" and not price_data.empty:
                if len(price_data) >= 3:
                    recent_prices = price_data["Close"].iloc[-3:]
                    price_list = recent_prices.tolist()

                    price_changes = []
                    for i in range(1, len(price_list)):
                        if price_list[i - 1] > 0:
                            change = (
                                abs(price_list[i] - price_list[i - 1])
                                / price_list[i - 1]
                            )
                            price_changes.append(change)

                    volatility_condition = (
                        sum(price_changes) / len(price_changes) >= 0.001
                        if len(price_changes) > 0
                        else False
                    )

                    timeframe_analysis["volatility"] = {
                        "recent_prices": price_list,
                        "avg_change": sum(price_changes) / len(price_changes)
                        if len(price_changes) > 0
                        else 0.0,
                        "condition_met": volatility_condition,
                    }

            # RSI攻防分析（M5のみ）
            if (
                timeframe == "M5"
                and "rsi" in indicators
                and "series" in indicators["rsi"]
            ):
                rsi_series = indicators["rsi"]["series"]
                if hasattr(rsi_series, "iloc"):
                    recent_rsi = rsi_series.iloc[-5:]
                else:
                    recent_rsi = rsi_series[-5:]

                rsi_values = (
                    recent_rsi.tolist()
                    if hasattr(recent_rsi, "tolist")
                    else list(recent_rsi)
                )

                rsi_near_50 = all(40 <= rsi <= 60 for rsi in rsi_values)
                first_half = rsi_values[:3]
                second_half = rsi_values[-3:]
                rsi_crosses_50 = any(rsi < 50 for rsi in first_half) and any(
                    rsi > 50 for rsi in second_half
                )

                timeframe_analysis["rsi_battle"] = {
                    "recent_rsi": rsi_values,
                    "near_50": rsi_near_50,
                    "crosses_50": rsi_crosses_50,
                    "condition_met": rsi_near_50 and rsi_crosses_50,
                }

            analysis[timeframe] = timeframe_analysis

        return analysis


async def main():
    """メイン関数"""
    # テスト実行
    tester = Pattern5DetailedTester()
    results = await tester.test_pattern5_detailed()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン5が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン5は検出されませんでした")
            logger.info("条件分析:")
            for timeframe, analysis in results.get("condition_analysis", {}).items():
                logger.info(f"  {timeframe}: {analysis}")
            sys.exit(1)
    else:
        logger.error(f"❌ テストでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
