"""
実際の市場データを使用したパターン検出テスト
Alpha Vantage APIからUSD/JPYデータを取得してテスト実行
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pandas as pd
import requests

# パターン検出器のインポート
from src.infrastructure.analysis.pattern_detectors import (
    BreakoutDetector,
    CompositeSignalDetector,
    DivergenceDetector,
    DoubleTopBottomDetector,
    EngulfingPatternDetector,
    FlagPatternDetector,
    MarubozuDetector,
    PullbackDetector,
    RedThreeSoldiersDetector,
    RollReversalDetector,
    RSIBattleDetector,
    SupportResistanceDetector,
    ThreeBuddhasDetector,
    TrendReversalDetector,
    TripleTopBottomDetector,
    WedgePatternDetector,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RealMarketDataTester:
    """実際の市場データを使用したテストクラス"""

    def __init__(self):
        self.api_key = "demo"  # デモ用APIキー
        self.base_url = "https://www.alphavantage.co/query"
        self.detectors = {
            1: TrendReversalDetector(),
            2: PullbackDetector(),
            3: DivergenceDetector(),
            4: BreakoutDetector(),
            5: RSIBattleDetector(),
            6: CompositeSignalDetector(),
            7: EngulfingPatternDetector(),
            8: RedThreeSoldiersDetector(),
            9: MarubozuDetector(),
            10: DoubleTopBottomDetector(),
            11: TripleTopBottomDetector(),
            12: FlagPatternDetector(),
            13: ThreeBuddhasDetector(),
            14: WedgePatternDetector(),
            15: SupportResistanceDetector(),
            16: RollReversalDetector(),
        }

    async def test_real_market_data(self):
        """実際の市場データでのテスト実行"""
        logger.info("=== 実際の市場データテスト開始 ===")

        try:
            # データ取得
            logger.info("Alpha Vantage APIからデータ取得中...")
            market_data = await self._fetch_market_data()

            if market_data is None or market_data.empty:
                logger.error("❌ データ取得に失敗しました")
                return

            logger.info(f"✅ データ取得完了: {len(market_data)}件")

            # パターン検出実行
            logger.info("全16個のパターン検出を実行中...")
            detection_results = await self._detect_all_patterns(market_data)

            # 結果分析
            logger.info("検出結果を分析中...")
            analysis_results = self._analyze_detection_results(detection_results)

            # 結果表示
            self._display_results(analysis_results)

        except Exception as e:
            logger.error(f"テスト実行エラー: {e}")

    async def _fetch_market_data(self) -> Optional[pd.DataFrame]:
        """Alpha Vantage APIからUSD/JPYデータを取得"""
        try:
            # デモ用のUSD/JPYデータ取得
            params = {
                "function": "FX_DAILY",
                "from_symbol": "USD",
                "to_symbol": "JPY",
                "apikey": self.api_key,
                "outputsize": "compact",  # 最新100件
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            if "Time Series FX (Daily)" not in data:
                logger.error(f"APIレスポンスエラー: {data}")
                return None

            # データフレームに変換
            time_series = data["Time Series FX (Daily)"]
            records = []

            for date, values in time_series.items():
                records.append(
                    {
                        "Date": pd.to_datetime(date),
                        "Open": float(values["1. open"]),
                        "High": float(values["2. high"]),
                        "Low": float(values["3. low"]),
                        "Close": float(values["4. close"]),
                        "Volume": 1000,  # デフォルト値
                    }
                )

            df = pd.DataFrame(records)
            df = df.sort_values("Date").reset_index(drop=True)

            return df

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return None

    async def _detect_all_patterns(self, market_data: pd.DataFrame) -> Dict[int, Any]:
        """全パターンの検出実行"""
        detection_results = {}

        for pattern_num, detector in self.detectors.items():
            try:
                logger.info(f"パターン{pattern_num}検出中...")

                result = detector.detect(market_data)

                if result:
                    detection_results[pattern_num] = result
                    logger.info(f"✅ パターン{pattern_num}検出成功")
                else:
                    logger.info(f"❌ パターン{pattern_num}は検出されませんでした")

            except Exception as e:
                logger.error(f"パターン{pattern_num}検出エラー: {e}")
                detection_results[pattern_num] = {"error": str(e)}

        return detection_results

    def _analyze_detection_results(
        self, detection_results: Dict[int, Any]
    ) -> Dict[str, Any]:
        """検出結果の分析"""
        total_patterns = len(self.detectors)
        detected_patterns = len(
            [r for r in detection_results.values() if r and "error" not in r]
        )
        error_patterns = len(
            [r for r in detection_results.values() if r and "error" in r]
        )

        detection_rate = (detected_patterns / total_patterns) * 100

        # 信頼度サマリー
        confidence_summary = {"High": 0, "Medium": 0, "Low": 0}
        direction_summary = {"BUY": 0, "SELL": 0, "unknown": 0}
        priority_summary = {}

        pattern_details = []

        for pattern_num, result in detection_results.items():
            if result and "error" not in result:
                confidence = result.get("confidence", "unknown")
                direction = result.get("direction", "unknown")
                priority = result.get("priority", 0)

                if confidence in confidence_summary:
                    confidence_summary[confidence] += 1

                if direction in direction_summary:
                    direction_summary[direction] += 1

                priority_summary[priority] = priority_summary.get(priority, 0) + 1

                pattern_details.append(
                    f"パターン{pattern_num}: ✅ {result.get('pattern_type', 'unknown')} "
                    f"({direction}, 信頼度: {confidence})"
                )

        return {
            "total_patterns": total_patterns,
            "detected_patterns": detected_patterns,
            "error_patterns": error_patterns,
            "detection_rate": detection_rate,
            "confidence_summary": confidence_summary,
            "direction_summary": direction_summary,
            "priority_summary": priority_summary,
            "pattern_details": pattern_details,
        }

    def _display_results(self, analysis_results: Dict[str, Any]):
        """結果の表示"""
        print("\n" + "=" * 60)
        print("🎯 実際の市場データテスト結果")
        print("=" * 60)

        print(f"\n📊 基本統計:")
        print(f"   総パターン数: {analysis_results['total_patterns']}")
        print(f"   検出パターン数: {analysis_results['detected_patterns']}")
        print(f"   エラーパターン数: {analysis_results['error_patterns']}")
        print(f"   検出率: {analysis_results['detection_rate']:.1f}%")

        print(f"\n🎯 信頼度サマリー:")
        for confidence, count in analysis_results["confidence_summary"].items():
            if count > 0:
                print(f"   {confidence}: {count}個")

        print(f"\n📈 方向サマリー:")
        for direction, count in analysis_results["direction_summary"].items():
            if count > 0:
                print(f"   {direction}: {count}個")

        print(f"\n⚡ 優先度サマリー:")
        for priority, count in analysis_results["priority_summary"].items():
            print(f"   {priority}: {count}個")

        if analysis_results["pattern_details"]:
            print(f"\n🔍 パターン詳細:")
            for detail in analysis_results["pattern_details"]:
                print(f"   {detail}")

        print("\n" + "=" * 60)

        if analysis_results["detection_rate"] >= 50:
            print("✅ 実際の市場データテスト成功！検出率が良好です。")
        elif analysis_results["detection_rate"] >= 30:
            print("⚠️ 検出率が中程度。さらなる調整が必要です。")
        else:
            print("❌ 検出率が低い。基準の大幅な調整が必要です。")


async def main():
    """メイン関数"""
    tester = RealMarketDataTester()
    await tester.test_real_market_data()


if __name__ == "__main__":
    asyncio.run(main())
