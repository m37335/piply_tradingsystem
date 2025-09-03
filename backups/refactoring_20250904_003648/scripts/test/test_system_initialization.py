#!/usr/bin/env python3
"""
システム初期化テストスクリプト
Phase 1: データ準備とシステム確認

分析エンジンの初期化確認と全16個のパターン検出器の動作確認
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
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SystemInitializationTester:
    """システム初期化テストクラス"""

    def __init__(self):
        self.test_results = {}

    async def test_system_initialization(self) -> Dict:
        """システム初期化テスト実行"""
        logger.info("=== システム初期化テスト開始 ===")

        try:
            # 1. 分析エンジン初期化テスト
            analyzer_test = await self._test_analyzer_initialization()
            self.test_results["analyzer_initialization"] = analyzer_test

            # 2. パターン検出器初期化テスト
            detector_test = await self._test_detector_initialization()
            self.test_results["detector_initialization"] = detector_test

            # 3. パターン定義テスト
            pattern_test = await self._test_pattern_definitions()
            self.test_results["pattern_definitions"] = pattern_test

            # 4. 統合テスト
            integration_test = await self._test_integration()
            self.test_results["integration_test"] = integration_test

            # 5. 結果サマリー
            self._generate_summary()

            return self.test_results

        except Exception as e:
            logger.error(f"システム初期化テストでエラーが発生しました: {e}")
            self.test_results["error"] = str(e)
            return self.test_results

    async def _test_analyzer_initialization(self) -> Dict:
        """分析エンジン初期化テスト"""
        logger.info("分析エンジン初期化テスト開始...")

        try:
            # 分析エンジンの初期化
            analyzer = NotificationPatternAnalyzer()

            # 基本属性の確認
            if not hasattr(analyzer, "detectors"):
                return {"success": False, "error": "detectors属性が存在しません"}

            if not hasattr(analyzer, "patterns"):
                return {"success": False, "error": "patterns属性が存在しません"}

            if not hasattr(analyzer, "utils"):
                return {"success": False, "error": "utils属性が存在しません"}

            # 検出器数の確認
            detector_count = len(analyzer.detectors)
            pattern_count = len(analyzer.patterns)

            logger.info(f"✅ 分析エンジン初期化テスト成功")
            logger.info(f"  検出器数: {detector_count}")
            logger.info(f"  パターン数: {pattern_count}")

            return {
                "success": True,
                "detector_count": detector_count,
                "pattern_count": pattern_count,
                "message": "分析エンジンが正常に初期化されました",
            }

        except Exception as e:
            logger.error(f"分析エンジン初期化テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_detector_initialization(self) -> Dict:
        """パターン検出器初期化テスト"""
        logger.info("パターン検出器初期化テスト開始...")

        try:
            # 全検出器の初期化テスト
            detectors = {
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

            # 各検出器の基本属性確認
            detector_results = {}
            for pattern_num, detector in detectors.items():
                try:
                    # 基本属性の確認
                    if not hasattr(detector, "pattern"):
                        detector_results[pattern_num] = {
                            "success": False,
                            "error": "pattern属性が存在しません",
                        }
                        continue

                    if not hasattr(detector, "utils"):
                        detector_results[pattern_num] = {
                            "success": False,
                            "error": "utils属性が存在しません",
                        }
                        continue

                    if not hasattr(detector, "detect"):
                        detector_results[pattern_num] = {
                            "success": False,
                            "error": "detectメソッドが存在しません",
                        }
                        continue

                    # パターン番号の確認
                    if detector.pattern.pattern_number != pattern_num:
                        detector_results[pattern_num] = {
                            "success": False,
                            "error": f"パターン番号が一致しません: 期待値={pattern_num}, 実際={detector.pattern.pattern_number}",
                        }
                        continue

                    detector_results[pattern_num] = {
                        "success": True,
                        "name": detector.pattern.name,
                        "priority": str(detector.pattern.priority),
                    }

                except Exception as e:
                    detector_results[pattern_num] = {"success": False, "error": str(e)}

            # 成功数の計算
            success_count = sum(
                1
                for result in detector_results.values()
                if result.get("success", False)
            )
            total_count = len(detector_results)

            logger.info(f"✅ パターン検出器初期化テスト完了")
            logger.info(f"  成功: {success_count}/{total_count}")

            return {
                "success": success_count == total_count,
                "total_detectors": total_count,
                "successful_detectors": success_count,
                "detector_results": detector_results,
            }

        except Exception as e:
            logger.error(f"パターン検出器初期化テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_pattern_definitions(self) -> Dict:
        """パターン定義テスト"""
        logger.info("パターン定義テスト開始...")

        try:
            analyzer = NotificationPatternAnalyzer()
            patterns = analyzer.patterns

            pattern_results = {}
            for pattern_num, pattern in patterns.items():
                try:
                    # 必須属性の確認
                    required_attrs = [
                        "pattern_number",
                        "name",
                        "description",
                        "priority",
                        "conditions",
                        "notification_title",
                        "notification_color",
                        "take_profit",
                        "stop_loss",
                        "confidence",
                    ]

                    missing_attrs = []
                    for attr in required_attrs:
                        if not hasattr(pattern, attr):
                            missing_attrs.append(attr)

                    if missing_attrs:
                        pattern_results[pattern_num] = {
                            "success": False,
                            "error": f"必須属性が不足: {missing_attrs}",
                        }
                        continue

                    # 条件の確認
                    if not pattern.conditions:
                        pattern_results[pattern_num] = {
                            "success": False,
                            "error": "conditionsが空です",
                        }
                        continue

                    # 時間足の確認
                    required_timeframes = ["D1", "H4", "H1", "M5"]
                    missing_timeframes = [
                        tf for tf in required_timeframes if tf not in pattern.conditions
                    ]

                    if missing_timeframes:
                        pattern_results[pattern_num] = {
                            "success": False,
                            "error": f"必須時間足が不足: {missing_timeframes}",
                        }
                        continue

                    pattern_results[pattern_num] = {
                        "success": True,
                        "name": pattern.name,
                        "priority": str(pattern.priority),
                        "timeframes": list(pattern.conditions.keys()),
                    }

                except Exception as e:
                    pattern_results[pattern_num] = {"success": False, "error": str(e)}

            # 成功数の計算
            success_count = sum(
                1 for result in pattern_results.values() if result.get("success", False)
            )
            total_count = len(pattern_results)

            logger.info(f"✅ パターン定義テスト完了")
            logger.info(f"  成功: {success_count}/{total_count}")

            return {
                "success": success_count == total_count,
                "total_patterns": total_count,
                "successful_patterns": success_count,
                "pattern_results": pattern_results,
            }

        except Exception as e:
            logger.error(f"パターン定義テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    async def _test_integration(self) -> Dict:
        """統合テスト"""
        logger.info("統合テスト開始...")

        try:
            analyzer = NotificationPatternAnalyzer()

            # サンプルデータの作成
            sample_data = self._create_sample_data()

            # 各検出器での検出テスト
            detection_results = {}
            for pattern_num, detector in analyzer.detectors.items():
                try:
                    # 検出メソッドの実行
                    result = detector.detect(sample_data)

                    # 結果の確認（Noneでも正常）
                    detection_results[pattern_num] = {
                        "success": True,
                        "detected": result is not None,
                        "result_type": type(result).__name__ if result else "None",
                    }

                except Exception as e:
                    detection_results[pattern_num] = {"success": False, "error": str(e)}

            # 成功数の計算
            success_count = sum(
                1
                for result in detection_results.values()
                if result.get("success", False)
            )
            total_count = len(detection_results)

            logger.info(f"✅ 統合テスト完了")
            logger.info(f"  成功: {success_count}/{total_count}")

            return {
                "success": success_count == total_count,
                "total_tests": total_count,
                "successful_tests": success_count,
                "detection_results": detection_results,
            }

        except Exception as e:
            logger.error(f"統合テストでエラー: {e}")
            return {"success": False, "error": str(e)}

    def _create_sample_data(self) -> pd.DataFrame:
        """サンプルデータ作成"""
        # テスト用のサンプルデータを作成
        dates = pd.date_range(start="2024-01-01", periods=50, freq="H")
        data = []

        for i in range(50):
            # 基本的な価格データ
            base_price = 150.0 + i * 0.01
            high = base_price + 0.1
            low = base_price - 0.1
            close = base_price + 0.05

            data.append(
                {
                    "timestamp": dates[i],
                    "open": base_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + i * 10,
                }
            )

        return pd.DataFrame(data)

    def _generate_summary(self):
        """テスト結果サマリー生成"""
        logger.info("=== システム初期化テスト結果サマリー ===")

        total_tests = len(self.test_results)
        passed_tests = sum(
            1
            for result in self.test_results.values()
            if isinstance(result, dict) and result.get("success", False)
        )

        logger.info(f"総テスト数: {total_tests}")
        logger.info(f"成功: {passed_tests}")
        logger.info(f"失敗: {total_tests - passed_tests}")

        # 各テストの詳細結果
        for test_name, result in self.test_results.items():
            if isinstance(result, dict):
                status = "✅ 成功" if result.get("success", False) else "❌ 失敗"
                logger.info(f"{test_name}: {status}")

                if not result.get("success", False) and "error" in result:
                    logger.error(f"  エラー: {result['error']}")


async def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="システム初期化テストスクリプト")
    parser.add_argument("--output", help="結果出力ファイル")

    args = parser.parse_args()

    # テスト実行
    tester = SystemInitializationTester()
    results = await tester.test_system_initialization()

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
