"""
パターン15実データ検証スクリプト

実際のデータベースデータを使用してレジスタンス/サポートライン検出の検証を行い、
複数の検証パターンで検出件数を測定して基準の妥当性を評価する
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple

import pandas as pd
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector import (
    SupportResistanceDetector,
)
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15RealDataValidator:
    """パターン15実データ検証器"""

    def __init__(self):
        self.detector = SupportResistanceDetector()
        self.validation_results = {}

    async def validate_pattern15_with_real_data(self) -> Dict:
        """実際のデータでパターン15を検証"""
        logger.info("=== パターン15実データ検証開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 複数の検証パターンを実行
            validation_patterns = [
                {"name": "直近1ヶ月", "days": 30, "expected_min": 5, "expected_max": 50},
                {"name": "直近3ヶ月", "days": 90, "expected_min": 15, "expected_max": 150},
                {"name": "直近6ヶ月", "days": 180, "expected_min": 30, "expected_max": 300},
                {"name": "直近1年", "days": 365, "expected_min": 60, "expected_max": 600},
            ]

            for pattern in validation_patterns:
                logger.info(f"検証パターン: {pattern['name']} を実行中...")
                result = await self._validate_single_pattern(pattern)
                self.validation_results[pattern["name"]] = result

            # 結果の分析と評価
            analysis = self._analyze_validation_results()

            # データベース接続終了
            await db_manager.close()

            return analysis

        except Exception as e:
            logger.error(f"実データ検証エラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _validate_single_pattern(self, pattern: Dict) -> Dict:
        """単一パターンの検証"""
        try:
            # データ取得
            data = await self._fetch_market_data(pattern["days"])
            if data.empty:
                return {"detection_count": 0, "error": "データが取得できませんでした"}

            logger.info(f"   取得データ: {len(data)}件")

            # パターン検出実行
            detections = []
            detection_count = 0

            # スライディングウィンドウで検出
            window_size = 120  # 4ヶ月分のデータ
            step_size = 30  # 1ヶ月ずつ移動

            for start_idx in range(0, len(data) - window_size, step_size):
                end_idx = start_idx + window_size
                window_data = data.iloc[start_idx:end_idx].copy()

                # インデックスをリセット
                window_data = window_data.reset_index(drop=True)

                # パターン検出
                result = self.detector.detect(window_data)

                if result:
                    detection_count += 1
                    detections.append(
                        {
                            "start_date": window_data.iloc[0]["Date"],
                            "end_date": window_data.iloc[-1]["Date"],
                            "pattern_type": result.get("pattern_type", "unknown"),
                            "direction": result.get("direction", "unknown"),
                            "confidence": result.get("confidence", 0.0),
                        }
                    )

            # 結果の評価
            expected_min = pattern["expected_min"]
            expected_max = pattern["expected_max"]

            if detection_count < expected_min:
                evaluation = "検出件数が少なすぎる（基準が厳しすぎる可能性）"
            elif detection_count > expected_max:
                evaluation = "検出件数が多すぎる（基準が緩すぎる可能性）"
            else:
                evaluation = "適切な検出件数"

            return {
                "detection_count": detection_count,
                "expected_min": expected_min,
                "expected_max": expected_max,
                "evaluation": evaluation,
                "detections": detections,
                "data_points": len(data),
            }

        except Exception as e:
            logger.error(f"単一パターン検証エラー: {e}")
            return {"detection_count": 0, "error": str(e)}

    async def _fetch_market_data(self, days: int) -> pd.DataFrame:
        """市場データ取得"""
        try:
            async with db_manager.get_session() as session:
                # 指定日数分のUSD/JPYデータを取得
                query = text(
                    """
                    SELECT
                        timestamp as Date,
                        open_price as Open,
                        high_price as High,
                        low_price as Low,
                        close_price as Close,
                        volume as Volume
                    FROM price_data
                    WHERE currency_pair = 'USD/JPY'
                    ORDER BY timestamp DESC
                    LIMIT :days
                """
                )

                result = await session.execute(query, {"days": days})
                rows = result.fetchall()

                if not rows:
                    return pd.DataFrame()

                # DataFrameに変換
                data = pd.DataFrame(
                    rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
                )

                # 日付順にソート（古い順）
                data = data.sort_values("Date").reset_index(drop=True)

                return data

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return pd.DataFrame()

    def _analyze_validation_results(self) -> Dict:
        """検証結果の分析"""
        try:
            analysis = {
                "summary": {},
                "detailed_results": self.validation_results,
                "recommendations": [],
            }

            # 各パターンの結果を分析
            for pattern_name, result in self.validation_results.items():
                if "error" in result:
                    continue

                detection_count = result["detection_count"]
                expected_min = result["expected_min"]
                expected_max = result["expected_max"]

                # 検出率の計算
                if result["data_points"] > 0:
                    detection_rate = detection_count / (
                        result["data_points"] / 120
                    )  # 4ヶ月単位での検出率
                else:
                    detection_rate = 0

                analysis["summary"][pattern_name] = {
                    "detection_count": detection_count,
                    "detection_rate": detection_rate,
                    "evaluation": result["evaluation"],
                }

            # 推奨事項の生成
            recommendations = self._generate_recommendations(analysis["summary"])
            analysis["recommendations"] = recommendations

            return analysis

        except Exception as e:
            logger.error(f"結果分析エラー: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, summary: Dict) -> List[str]:
        """推奨事項の生成"""
        recommendations = []

        # 検出件数の傾向を分析
        detection_counts = [data["detection_count"] for data in summary.values()]
        avg_detection_count = (
            sum(detection_counts) / len(detection_counts) if detection_counts else 0
        )

        if avg_detection_count < 10:
            recommendations.append("検出件数が少なすぎます。基準をさらに緩和することを推奨します。")
        elif avg_detection_count > 100:
            recommendations.append("検出件数が多すぎます。基準を厳しくすることを推奨します。")
        else:
            recommendations.append("検出件数は適切な範囲内です。")

        # 各パターンの評価
        for pattern_name, data in summary.items():
            if "少なすぎる" in data["evaluation"]:
                recommendations.append(f"{pattern_name}: 基準の緩和を検討してください。")
            elif "多すぎる" in data["evaluation"]:
                recommendations.append(f"{pattern_name}: 基準の厳格化を検討してください。")

        return recommendations


async def main():
    """メイン関数"""
    validator = Pattern15RealDataValidator()
    results = await validator.validate_pattern15_with_real_data()

    if "error" in results:
        print(f"\n❌ 検証エラー: {results['error']}")
        return

    print("\n=== パターン15実データ検証結果 ===")

    # サマリー表示
    print("\n📊 検証サマリー:")
    for pattern_name, data in results["summary"].items():
        print(f"  {pattern_name}:")
        print(f"    検出件数: {data['detection_count']}件")
        print(f"    検出率: {data['detection_rate']:.2f}")
        print(f"    評価: {data['evaluation']}")

    # 推奨事項表示
    print("\n💡 推奨事項:")
    for recommendation in results["recommendations"]:
        print(f"  • {recommendation}")

    # 詳細結果表示
    print("\n📋 詳細結果:")
    for pattern_name, result in results["detailed_results"].items():
        print(f"\n  {pattern_name}:")
        if "error" in result:
            print(f"    エラー: {result['error']}")
        else:
            print(f"    検出件数: {result['detection_count']}件")
            print(f"    期待範囲: {result['expected_min']}-{result['expected_max']}件")
            print(f"    評価: {result['evaluation']}")

            # 検出されたパターンの詳細
            if result["detections"]:
                print(f"    検出パターン例:")
                for i, detection in enumerate(result["detections"][:3]):  # 最初の3件のみ表示
                    print(
                        f"      {i+1}. {detection['start_date']} - {detection['end_date']}"
                    )
                    print(f"         タイプ: {detection['pattern_type']}")
                    print(f"         方向: {detection['direction']}")
                    print(f"         信頼度: {detection['confidence']:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
