"""
レンジ相場検出デバッグスクリプト

レンジ相場（行き来する現象）の検出がなぜ動作しないかを詳細に分析する
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List

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


class RangePatternDebugger:
    """レンジ相場検出デバッガー"""

    def __init__(self):
        self.detector = SupportResistanceDetector()

    async def debug_range_pattern(self) -> Dict:
        """レンジ相場検出の詳細デバッグ"""
        logger.info("=== レンジ相場検出デバッグ開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 複数の期間でテスト
            test_periods = [
                ("直近1週間", 7),
                ("直近2週間", 14),
                ("直近1ヶ月", 30),
                ("直近3ヶ月", 90),
            ]

            results = {}
            for period_name, days in test_periods:
                logger.info(f"検証期間: {period_name}")
                result = await self._debug_single_period(period_name, days)
                results[period_name] = result

            # データベース接続終了
            await db_manager.close()

            return results

        except Exception as e:
            logger.error(f"レンジ相場デバッグエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    async def _debug_single_period(self, period_name: str, days: int) -> Dict:
        """単一期間のデバッグ"""
        try:
            # データ取得
            data = await self._fetch_market_data(days)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"  取得データ: {len(data)}件")

            # レンジ相場検出の詳細分析
            debug_info = self._analyze_range_detection(data)

            return {"data_points": len(data), "debug_info": debug_info}

        except Exception as e:
            logger.error(f"期間デバッグエラー: {e}")
            return {"error": str(e)}

    def _analyze_range_detection(self, data: pd.DataFrame) -> Dict:
        """レンジ相場検出の詳細分析"""
        try:
            debug_info = {
                "resistance_line_analysis": {},
                "support_line_analysis": {},
                "range_pattern_analysis": {},
                "recommendations": [],
            }

            # 1. レジスタンスライン検出の詳細分析
            resistance_analysis = self._debug_resistance_line(data)
            debug_info["resistance_line_analysis"] = resistance_analysis

            # 2. サポートライン検出の詳細分析
            support_analysis = self._debug_support_line(data)
            debug_info["support_line_analysis"] = support_analysis

            # 3. レンジ相場検出の詳細分析
            range_analysis = self._debug_range_pattern_logic(data)
            debug_info["range_pattern_analysis"] = range_analysis

            # 4. 推奨事項の生成
            recommendations = self._generate_debug_recommendations(debug_info)
            debug_info["recommendations"] = recommendations

            return debug_info

        except Exception as e:
            logger.error(f"レンジ検出分析エラー: {e}")
            return {"error": str(e)}

    def _debug_resistance_line(self, data: pd.DataFrame) -> Dict:
        """レジスタンスライン検出の詳細デバッグ"""
        try:
            analysis = {}

            # タッチポイント検出
            touch_points = self.detector._find_touch_points(data, "resistance")
            analysis["touch_points"] = {
                "count": len(touch_points),
                "indices": touch_points[:10],  # 最初の10個のみ表示
                "min_required": self.detector.min_touch_points,
            }

            if len(touch_points) >= self.detector.min_touch_points:
                # ライン方程式計算
                line_data = self.detector._calculate_line_equation(
                    touch_points, data, "High"
                )
                analysis["line_equation"] = {
                    "success": line_data is not None,
                    "slope": line_data.get("slope") if line_data else None,
                    "intercept": line_data.get("intercept") if line_data else None,
                }

                if line_data:
                    # ライン強度検証
                    strength = self.detector._validate_line_strength(
                        touch_points, line_data
                    )
                    analysis["line_strength"] = {
                        "strength": strength,
                        "min_required": 0.01,
                        "passed": strength >= 0.01,
                    }

                    # ブレイクアウト検出
                    breakout = self.detector._detect_breakout(
                        data, line_data, "resistance"
                    )
                    analysis["breakout"] = {
                        "detected": breakout is not None,
                        "type": breakout.get("type") if breakout else None,
                        "strength": breakout.get("strength") if breakout else None,
                    }

            return analysis

        except Exception as e:
            logger.error(f"レジスタンスラインデバッグエラー: {e}")
            return {"error": str(e)}

    def _debug_support_line(self, data: pd.DataFrame) -> Dict:
        """サポートライン検出の詳細デバッグ"""
        try:
            analysis = {}

            # タッチポイント検出
            touch_points = self.detector._find_touch_points(data, "support")
            analysis["touch_points"] = {
                "count": len(touch_points),
                "indices": touch_points[:10],  # 最初の10個のみ表示
                "min_required": self.detector.min_touch_points,
            }

            if len(touch_points) >= self.detector.min_touch_points:
                # ライン方程式計算
                line_data = self.detector._calculate_line_equation(
                    touch_points, data, "Low"
                )
                analysis["line_equation"] = {
                    "success": line_data is not None,
                    "slope": line_data.get("slope") if line_data else None,
                    "intercept": line_data.get("intercept") if line_data else None,
                }

                if line_data:
                    # ライン強度検証
                    strength = self.detector._validate_line_strength(
                        touch_points, line_data
                    )
                    analysis["line_strength"] = {
                        "strength": strength,
                        "min_required": 0.01,
                        "passed": strength >= 0.01,
                    }

                    # ブレイクアウト検出
                    breakout = self.detector._detect_breakout(
                        data, line_data, "support"
                    )
                    analysis["breakout"] = {
                        "detected": breakout is not None,
                        "type": breakout.get("type") if breakout else None,
                        "strength": breakout.get("strength") if breakout else None,
                    }

            return analysis

        except Exception as e:
            logger.error(f"サポートラインデバッグエラー: {e}")
            return {"error": str(e)}

    def _debug_range_pattern_logic(self, data: pd.DataFrame) -> Dict:
        """レンジ相場検出ロジックの詳細デバッグ"""
        try:
            analysis = {}

            # レンジ相場用の緩和版で検出
            resistance_line = self.detector._detect_resistance_line_for_range(data)
            support_line = self.detector._detect_support_line_for_range(data)

            analysis["both_lines_detected"] = (
                resistance_line is not None and support_line is not None
            )
            analysis["resistance_detected"] = resistance_line is not None
            analysis["support_detected"] = support_line is not None

            # レジスタンスラインの詳細分析
            if resistance_line:
                analysis["resistance_details"] = {
                    "strength": resistance_line.get("strength", 0.0),
                    "touch_points_count": len(resistance_line.get("touch_points", [])),
                    "breakout_type": resistance_line.get("breakout", {}).get(
                        "type", "unknown"
                    ),
                }
            else:
                # なぜレジスタンスラインが検出されないかの分析
                resistance_analysis = self._analyze_why_line_not_detected(
                    data, "resistance"
                )
                analysis["resistance_failure_reason"] = resistance_analysis

            # サポートラインの詳細分析
            if support_line:
                analysis["support_details"] = {
                    "strength": support_line.get("strength", 0.0),
                    "touch_points_count": len(support_line.get("touch_points", [])),
                    "breakout_type": support_line.get("breakout", {}).get(
                        "type", "unknown"
                    ),
                }
            else:
                # なぜサポートラインが検出されないかの分析
                support_analysis = self._analyze_why_line_not_detected(data, "support")
                analysis["support_failure_reason"] = support_analysis

            if resistance_line and support_line:
                # レンジ幅の計算
                resistance_price = resistance_line["line_data"]["intercept"]
                support_price = support_line["line_data"]["intercept"]
                range_width = abs(resistance_price - support_price) / support_price

                analysis["range_width"] = {
                    "resistance_price": resistance_price,
                    "support_price": support_price,
                    "range_width": range_width,
                    "min_required": 0.03,
                    "max_allowed": 0.25,
                    "passed": 0.03 <= range_width <= 0.25,
                }

                if 0.03 <= range_width <= 0.25:
                    # 価格の行き来現象をチェック
                    oscillations = self.detector._check_price_oscillations(
                        data, resistance_price, support_price
                    )

                    analysis["oscillations"] = {
                        "resistance_touches": oscillations.get("resistance_touches", 0),
                        "support_touches": oscillations.get("support_touches", 0),
                        "crossings": oscillations.get("crossings", 0),
                        "is_valid": oscillations.get("is_valid", False),
                        "min_touches_required": 3,
                        "min_crossings_required": 2,
                    }

                    if oscillations.get("is_valid", False):
                        # レンジ相場の強度計算
                        range_strength = self.detector._calculate_range_strength(
                            data, resistance_line, support_line, oscillations
                        )

                        analysis["range_strength"] = {
                            "strength": range_strength,
                            "resistance_strength": resistance_line.get("strength", 0.0),
                            "support_strength": support_line.get("strength", 0.0),
                        }

            return analysis

        except Exception as e:
            logger.error(f"レンジパターンロジックデバッグエラー: {e}")
            return {"error": str(e)}

    def _analyze_why_line_not_detected(
        self, data: pd.DataFrame, line_type: str
    ) -> Dict:
        """ラインが検出されない理由を分析"""
        try:
            analysis = {}

            # タッチポイント検出
            touch_points = self.detector._find_touch_points(data, line_type)
            analysis["touch_points"] = {"count": len(touch_points), "min_required": 1}

            if len(touch_points) >= 1:
                # ライン方程式計算
                column = "High" if line_type == "resistance" else "Low"
                line_data = self.detector._calculate_line_equation(
                    touch_points, data, column
                )
                analysis["line_equation"] = {"success": line_data is not None}

                if line_data:
                    # ライン強度検証
                    strength = self.detector._validate_line_strength(
                        touch_points, line_data
                    )
                    analysis["line_strength"] = {
                        "strength": strength,
                        "min_required": 0.005,
                        "passed": strength >= 0.005,
                    }

                    if strength >= 0.005:
                        # ブレイクアウト検出
                        breakout = self.detector._detect_breakout_for_range(
                            data, line_data, line_type
                        )
                        analysis["breakout"] = {
                            "detected": breakout is not None,
                            "type": breakout.get("type") if breakout else None,
                        }

            return analysis

        except Exception as e:
            logger.error(f"ライン検出失敗分析エラー: {e}")
            return {"error": str(e)}

    def _generate_debug_recommendations(self, debug_info: Dict) -> List[str]:
        """デバッグ結果に基づく推奨事項生成"""
        recommendations = []

        # レジスタンスライン分析
        resistance_analysis = debug_info.get("resistance_line_analysis", {})
        if "touch_points" in resistance_analysis:
            touch_count = resistance_analysis["touch_points"]["count"]
            if touch_count < self.detector.min_touch_points:
                recommendations.append(
                    f"レジスタンスライン: タッチポイント数が不足 ({touch_count}/{self.detector.min_touch_points})"
                )

        # サポートライン分析
        support_analysis = debug_info.get("support_line_analysis", {})
        if "touch_points" in support_analysis:
            touch_count = support_analysis["touch_points"]["count"]
            if touch_count < self.detector.min_touch_points:
                recommendations.append(
                    f"サポートライン: タッチポイント数が不足 ({touch_count}/{self.detector.min_touch_points})"
                )

        # レンジ相場分析
        range_analysis = debug_info.get("range_pattern_analysis", {})
        if not range_analysis.get("both_lines_detected", False):
            recommendations.append("レンジ相場: レジスタンスラインとサポートラインの両方が検出されていません")

        if "range_width" in range_analysis:
            range_width_info = range_analysis["range_width"]
            if not range_width_info.get("passed", False):
                range_width = range_width_info.get("range_width", 0)
                recommendations.append(
                    f"レンジ相場: レンジ幅が不適切 ({range_width:.3f}, 期待値: 0.05-0.20)"
                )

        if "oscillations" in range_analysis:
            oscillations = range_analysis["oscillations"]
            if not oscillations.get("is_valid", False):
                recommendations.append(
                    f"レンジ相場: 行き来現象が不十分 (タッチ: {oscillations.get('resistance_touches', 0)}+{oscillations.get('support_touches', 0)}, クロス: {oscillations.get('crossings', 0)})"
                )

        if not recommendations:
            recommendations.append("すべての条件が満たされています。レンジ相場が検出されるはずです。")

        return recommendations

    async def _fetch_market_data(self, days: int) -> pd.DataFrame:
        """市場データ取得"""
        try:
            async with db_manager.get_session() as session:
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

                data = pd.DataFrame(
                    rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"]
                )

                data = data.sort_values("Date").reset_index(drop=True)
                return data

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return pd.DataFrame()


async def main():
    """メイン関数"""
    debugger = RangePatternDebugger()
    results = await debugger.debug_range_pattern()

    if "error" in results:
        print(f"\n❌ デバッグエラー: {results['error']}")
        return

    print("\n=== レンジ相場検出デバッグ結果 ===")

    for period_name, result in results.items():
        if "error" in result:
            print(f"\n❌ {period_name}: {result['error']}")
            continue

        print(f"\n📊 {period_name} ({result['data_points']}件):")

        debug_info = result.get("debug_info", {})

        # レジスタンスライン分析
        resistance = debug_info.get("resistance_line_analysis", {})
        print(f"  レジスタンスライン:")
        if "touch_points" in resistance:
            tp = resistance["touch_points"]
            print(f"    タッチポイント: {tp['count']}件 (必要: {tp['min_required']}件)")

        # サポートライン分析
        support = debug_info.get("support_line_analysis", {})
        print(f"  サポートライン:")
        if "touch_points" in support:
            tp = support["touch_points"]
            print(f"    タッチポイント: {tp['count']}件 (必要: {tp['min_required']}件)")

        # レンジ相場分析
        range_analysis = debug_info.get("range_pattern_analysis", {})
        print(f"  レンジ相場:")
        print(f"    両ライン検出: {range_analysis.get('both_lines_detected', False)}")
        print(f"    レジスタンス検出: {range_analysis.get('resistance_detected', False)}")
        print(f"    サポート検出: {range_analysis.get('support_detected', False)}")

        # レジスタンスライン詳細
        if "resistance_details" in range_analysis:
            rd = range_analysis["resistance_details"]
            print(
                f"    レジスタンス詳細: 強度{rd.get('strength', 0):.3f}, タッチ{rd.get('touch_points_count', 0)}件"
            )
        elif "resistance_failure_reason" in range_analysis:
            rfr = range_analysis["resistance_failure_reason"]
            print(f"    レジスタンス失敗理由: {rfr}")

        # サポートライン詳細
        if "support_details" in range_analysis:
            sd = range_analysis["support_details"]
            print(
                f"    サポート詳細: 強度{sd.get('strength', 0):.3f}, タッチ{sd.get('touch_points_count', 0)}件"
            )
        elif "support_failure_reason" in range_analysis:
            sfr = range_analysis["support_failure_reason"]
            print(f"    サポート失敗理由: {sfr}")

        if "range_width" in range_analysis:
            rw = range_analysis["range_width"]
            print(
                f"    レンジ幅: {rw.get('range_width', 0):.3f} (適正: {rw.get('min_required', 0)}-{rw.get('max_allowed', 0)})"
            )

        if "oscillations" in range_analysis:
            osc = range_analysis["oscillations"]
            print(
                f"    行き来現象: レジスタンス{osc.get('resistance_touches', 0)}回, サポート{osc.get('support_touches', 0)}回, クロス{osc.get('crossings', 0)}回"
            )

        # 推奨事項
        recommendations = debug_info.get("recommendations", [])
        if recommendations:
            print(f"  💡 推奨事項:")
            for rec in recommendations:
                print(f"    • {rec}")


if __name__ == "__main__":
    asyncio.run(main())
