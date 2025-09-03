#!/usr/bin/env python3
"""
パターン1デバッグテストスクリプト
パターン1の内部動作を詳細に確認するデバッグスクリプト
"""

import asyncio
import logging
import sys
from typing import Dict

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


class Pattern1DebugTester:
    """パターン1デバッグテストクラス"""

    def __init__(self):
        self.detector = TrendReversalDetector()

    async def debug_pattern1(self) -> Dict:
        """パターン1デバッグ実行"""
        logger.info("=== パターン1デバッグ開始 ===")

        try:
            # シンプルなテストデータを作成
            test_data = self._create_simple_test_data()

            # データ妥当性チェック
            logger.info("データ妥当性チェック...")
            is_valid = self.detector._validate_data(test_data)
            logger.info(f"データ妥当性: {is_valid}")

            if not is_valid:
                logger.error("データが妥当ではありません")
                return {"success": False, "error": "データ妥当性エラー"}

            # 各時間足の条件を個別にチェック
            logger.info("各時間足の条件チェック...")

            # D1条件チェック
            d1_result = self.detector._check_d1_conditions(test_data.get("D1", {}))
            logger.info(f"D1条件: {d1_result}")

            # H4条件チェック
            h4_result = self.detector._check_h4_conditions(test_data.get("H4", {}))
            logger.info(f"H4条件: {h4_result}")

            # H1条件チェック
            h1_result = self.detector._check_h1_conditions(test_data.get("H1", {}))
            logger.info(f"H1条件: {h1_result}")

            # M5条件チェック
            m5_result = self.detector._check_m5_conditions(test_data.get("M5", {}))
            logger.info(f"M5条件: {m5_result}")

            # 全条件の結果
            conditions_met = {
                "D1": d1_result,
                "H4": h4_result,
                "H1": h1_result,
                "M5": m5_result,
            }

            logger.info(f"全条件結果: {conditions_met}")

            # 全条件が満たされているかチェック
            all_conditions_met = all(conditions_met.values())
            logger.info(f"全条件満足: {all_conditions_met}")

            # 検出テスト
            result = self.detector.detect(test_data)
            logger.info(f"検出結果: {result is not None}")

            if result:
                logger.info("✅ パターン1検出成功！")
                logger.info(f"  信頼度: {result.get('confidence_score', 'N/A')}")
                return {
                    "success": True,
                    "detected": True,
                    "conditions_met": conditions_met,
                    "result": result,
                }
            else:
                logger.info("❌ パターン1は検出されませんでした")
                return {
                    "success": True,
                    "detected": False,
                    "conditions_met": conditions_met,
                }

        except Exception as e:
            logger.error(f"パターン1デバッグでエラー: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}

    def _create_simple_test_data(self) -> Dict:
        """シンプルなテストデータ作成"""
        logger.info("シンプルなテストデータ作成中...")

        # 基本的な価格データ
        dates = pd.date_range(start="2024-01-01", periods=50, freq="H")
        prices = [150.0 + i * 0.1 for i in range(50)]

        price_data = pd.DataFrame(
            {
                "Date": dates,
                "Open": [p - 0.05 for p in prices],
                "High": [p + 0.1 for p in prices],
                "Low": [p - 0.1 for p in prices],
                "Close": prices,
                "Volume": [1000 + i for i in range(50)],
            }
        )

        # 基本的な指標データ
        indicators = {
            "rsi": {"current_value": 70.0, "values": [70.0] * 50},  # RSI > 65
            "macd": {
                "macd": [0.1 + i * 0.01 for i in range(50)],
                "signal": [0.05 + i * 0.008 for i in range(50)],
                "histogram": [0.05 + i * 0.002 for i in range(50)],
            },
            "bollinger_bands": {
                "upper": [p + 0.5 for p in prices],
                "middle": prices,
                "lower": [p - 0.5 for p in prices],
                "std": [0.5] * 50,
            },
        }

        # 各時間足のデータ
        test_data = {
            "D1": {"price_data": price_data, "indicators": indicators},
            "H4": {"price_data": price_data, "indicators": indicators},
            "H1": {"price_data": price_data, "indicators": indicators},
            "M5": {"price_data": price_data, "indicators": indicators},
        }

        logger.info("✅ シンプルなテストデータ作成完了")
        return test_data


async def main():
    """メイン関数"""
    # デバッグ実行
    tester = Pattern1DebugTester()
    results = await tester.debug_pattern1()

    # 結果表示
    if results.get("success", False):
        if results.get("detected", False):
            logger.info("🎉 パターン1が正常に検出されました！")
            sys.exit(0)
        else:
            logger.info("❌ パターン1は検出されませんでした")
            logger.info("条件詳細:")
            for timeframe, condition in results.get("conditions_met", {}).items():
                logger.info(f"  {timeframe}: {condition}")
            sys.exit(1)
    else:
        logger.error(f"❌ デバッグでエラーが発生しました: {results.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
