#!/usr/bin/env python3
"""
基本パターンテストスクリプト
Phase 2: 個別パターン検出テスト

基本パターン（1-6）の検出テストを行うスクリプト
"""

import argparse
import asyncio
import logging
import sys
from typing import Dict, List

import pandas as pd
import yaml

# プロジェクトのルートディレクトリをパスに追加
sys.path.append("/app")

from src.infrastructure.analysis.notification_pattern_analyzer import (
    NotificationPatternAnalyzer,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BasicPatternsTester:
    """基本パターンテストクラス"""

    def __init__(self):
        self.analyzer = NotificationPatternAnalyzer()
        self.test_results = {}

    async def test_basic_patterns(self, patterns: List[int]) -> Dict:
        """基本パターンテスト実行"""
        logger.info("=== 基本パターンテスト開始 ===")
        logger.info(f"テスト対象パターン: {patterns}")

        try:
            # テストデータの作成
            test_data = self._create_test_data()

            # 各パターンのテスト
            for pattern_num in patterns:
                if pattern_num in self.analyzer.detectors:
                    pattern_test = await self._test_single_pattern(
                        pattern_num, test_data
                    )
                    self.test_results[f"pattern_{pattern_num}"] = pattern_test
                else:
                    logger.warning(f"パターン{pattern_num}は存在しません")

            # 結果サマリー
            self._generate_summary()

            return self.test_results

        except Exception as e:
            logger.error(f"基本パターンテストでエラーが発生しました: {e}")
            self.test_results["error"] = str(e)
            return self.test_results

    async def _test_single_pattern(
        self, pattern_num: int, test_data: pd.DataFrame
    ) -> Dict:
        """単一パターンのテスト"""
        logger.info(f"パターン{pattern_num}のテスト開始...")

        try:
            detector = self.analyzer.detectors[pattern_num]
            pattern_info = self.analyzer.patterns[pattern_num]

            # 検出実行
            result = detector.detect(test_data)

            # 結果分析
            if result is not None:
                # 検出成功
                detection_analysis = self._analyze_detection_result(result)

                logger.info(f"✅ パターン{pattern_num}検出成功")
                logger.info(f"  信頼度: {result.get('confidence_score', 'N/A')}")
                logger.info(f"  方向: {result.get('strategy', 'N/A')}")

                return {
                    "success": True,
                    "detected": True,
                    "pattern_name": pattern_info.name,
                    "confidence_score": result.get("confidence_score"),
                    "strategy": result.get("strategy"),
                    "detection_analysis": detection_analysis,
                }
            else:
                # 検出なし（正常な結果）
                logger.info(f"ℹ️ パターン{pattern_num}は検出されませんでした（正常）")

                return {
                    "success": True,
                    "detected": False,
                    "pattern_name": pattern_info.name,
                    "message": "パターンが検出されませんでした（正常な動作）",
                }

        except Exception as e:
            logger.error(f"パターン{pattern_num}のテストでエラー: {e}")
            return {"success": False, "detected": False, "error": str(e)}

    def _analyze_detection_result(self, result: Dict) -> Dict:
        """検出結果の分析"""
        analysis = {
            "has_confidence": "confidence_score" in result,
            "has_strategy": "strategy" in result,
            "has_pattern_data": "pattern_data" in result,
            "result_keys": list(result.keys()),
        }

        # 信頼度の評価
        if "confidence_score" in result:
            confidence = result["confidence_score"]
            if confidence >= 0.8:
                analysis["confidence_level"] = "高"
            elif confidence >= 0.6:
                analysis["confidence_level"] = "中"
            else:
                analysis["confidence_level"] = "低"

        return analysis

    def _create_test_data(self) -> pd.DataFrame:
        """テストデータ作成"""
        # 基本パターン検出に適したテストデータを作成

        # パターン1: トレンド転換 - RSI 30以下 + MACD上昇
        # パターン2: プルバック - RSI 30-50 + 価格反発
        # パターン3: ダイバージェンス - 価格新高値 + RSI前回高値未達
        # パターン4: ブレイクアウト - RSI 50-70 + 価格突破
        # パターン5: RSI戦い - RSI 45-55 + 価格横ばい
        # パターン6: 複合シグナル - 複数条件の組み合わせ

        dates = pd.date_range(start="2024-01-01", periods=100, freq="H")
        data = []

        for i in range(100):
            # 基本的な価格トレンド
            if i < 30:
                # 下降トレンド
                base_price = 150.0 - i * 0.02
            elif i < 60:
                # 上昇トレンド
                base_price = 149.4 + (i - 30) * 0.03
            else:
                # 横ばい
                base_price = 150.3 + (i - 60) * 0.001

            # 価格データ
            high = base_price + 0.15 + (i % 3) * 0.01
            low = base_price - 0.15 - (i % 3) * 0.01
            close = base_price + 0.05 * (i % 2 - 0.5)

            data.append(
                {
                    "timestamp": dates[i],
                    "open": base_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + i * 10 + (i % 5) * 100,
                }
            )

        return pd.DataFrame(data)

    def _generate_summary(self):
        """テスト結果サマリー生成"""
        logger.info("=== 基本パターンテスト結果サマリー ===")

        total_tests = len(self.test_results)
        successful_tests = sum(
            1
            for result in self.test_results.values()
            if isinstance(result, dict) and result.get("success", False)
        )
        detected_patterns = sum(
            1
            for result in self.test_results.values()
            if isinstance(result, dict) and result.get("detected", False)
        )

        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {successful_tests}")
        logger.info(f"失敗: {total_tests - successful_tests}")
        logger.info(f"検出されたパターン: {detected_patterns}")

        # 各パターンの詳細結果
        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ 成功" if result.get("success", False) else "❌ 失敗"
                detected = "🔍 検出" if result.get("detected", False) else "❌ 未検出"
                logger.info(f"{test_name}: {status} ({detected})")

                if result.get("detected", False):
                    confidence = result.get("confidence_score", "N/A")
                    strategy = result.get("strategy", "N/A")
                    logger.info(f"  信頼度: {confidence}, 戦略: {strategy}")

                if not result.get("success", False) and "error" in result:
                    logger.error(f"  エラー: {result['error']}")


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="基本パターンテストスクリプト")
    parser.add_argument("--patterns", default="1,2,3,4,5,6", help="テストするパターン番号（カンマ区切り）")
    parser.add_argument("--output", help="結果出力ファイル")

    args = parser.parse_args()

    # パターン番号の解析
    try:
        pattern_numbers = [int(p.strip()) for p in args.patterns.split(",")]
    except ValueError:
        logger.error("パターン番号の形式が正しくありません")
        sys.exit(1)

    # テスト実行
    tester = BasicPatternsTester()
    results = await tester.test_basic_patterns(pattern_numbers)

    # 結果出力
    if args.output:
        with open(args.output, "w") as f:
            yaml.dump(results, f, default_flow_style=False, allow_unicode=True)
        logger.info(f"結果を {args.output} に保存しました")

    # 終了コード
    success_count = sum(
        1
        for result in results.values()
        if isinstance(result, dict) and result.get("success", False)
    )
    total_tests = len([r for r in results.values() if isinstance(r, dict)])

    if success_count == total_tests:
        logger.info("🎉 すべてのテストが成功しました！")
        sys.exit(0)
    else:
        logger.error(f"❌ {total_tests - success_count}個のテストが失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
