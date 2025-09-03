"""
パターン15実データデバッグスクリプト

実際のデータでパターン15の検出プロセスを詳細にデバッグし、
どの段階で失敗しているかを特定する
"""

import asyncio
import logging
from typing import Dict

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


class Pattern15RealDataDebugger:
    """パターン15実データデバッガー"""

    def __init__(self):
        self.detector = SupportResistanceDetector()

    async def debug_pattern15_with_real_data(self) -> Dict:
        """実際のデータでパターン15をデバッグ"""
        logger.info("=== パターン15実データデバッグ開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 直近3ヶ月のデータを取得
            data = await self._fetch_market_data(90)
            if data.empty:
                logger.error("データが取得できませんでした")
                return {"error": "データが取得できませんでした"}

            logger.info(f"取得データ: {len(data)}件")
            logger.info(f"データ期間: {data.iloc[0]['Date']} - {data.iloc[-1]['Date']}")

            # 詳細デバッグ実行
            debug_results = self._detailed_debug(data)

            # データベース接続終了
            await db_manager.close()

            return debug_results

        except Exception as e:
            logger.error(f"デバッグエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

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

    def _detailed_debug(self, data: pd.DataFrame) -> Dict:
        """詳細デバッグ"""
        debug_info = {
            "data_info": {},
            "resistance_debug": {},
            "support_debug": {},
            "overall_result": {},
        }

        # データ情報
        debug_info["data_info"] = {
            "total_points": len(data),
            "date_range": f"{data.iloc[0]['Date']} - {data.iloc[-1]['Date']}",
            "price_range": f"{data['Close'].min():.2f} - {data['Close'].max():.2f}",
            "avg_price": data["Close"].mean(),
        }

        # レジスタンスライン詳細デバッグ
        logger.info("=== レジスタンスライン詳細デバッグ ===")
        resistance_debug = self._debug_resistance_line(data)
        debug_info["resistance_debug"] = resistance_debug

        # サポートライン詳細デバッグ
        logger.info("=== サポートライン詳細デバッグ ===")
        support_debug = self._debug_support_line(data)
        debug_info["support_debug"] = support_debug

        # 全体結果
        overall_result = self.detector.detect(data)
        debug_info["overall_result"] = {
            "detected": overall_result is not None,
            "result": overall_result,
        }

        return debug_info

    def _debug_resistance_line(self, data: pd.DataFrame) -> Dict:
        """レジスタンスライン詳細デバッグ"""
        debug = {}

        try:
            # 1. タッチポイント検出
            logger.info("1. レジスタンスタッチポイント検出...")
            touch_points = self.detector._find_touch_points(data, "resistance")
            debug["touch_points"] = {
                "count": len(touch_points),
                "sufficient": len(touch_points) >= self.detector.min_touch_points,
                "points": touch_points[:5] if touch_points else [],  # 最初の5件のみ表示
            }
            logger.info(f"   タッチポイント数: {len(touch_points)}")

            if not debug["touch_points"]["sufficient"]:
                logger.info("   ❌ タッチポイントが不足")
                return debug

            # 2. ライン方程式計算
            logger.info("2. レジスタンスライン方程式計算...")
            line_data = self.detector._calculate_line_equation(
                touch_points, data, "High"
            )
            debug["line_equation"] = {
                "calculated": line_data is not None,
                "data": line_data,
            }
            logger.info(f"   ライン方程式計算: {'成功' if line_data else '失敗'}")

            if not line_data:
                logger.info("   ❌ ライン方程式計算失敗")
                return debug

            # 3. ライン強度検証
            logger.info("3. レジスタンスライン強度検証...")
            strength = self.detector._validate_line_strength(touch_points, line_data)
            debug["line_strength"] = {
                "strength": strength,
                "sufficient": strength >= 0.1,
                "threshold": 0.1,
            }
            logger.info(f"   ライン強度: {strength:.4f} (閾値: 0.1)")

            if not debug["line_strength"]["sufficient"]:
                logger.info("   ❌ ライン強度不足")
                return debug

            # 4. ブレイクアウト検出
            logger.info("4. レジスタンスブレイクアウト検出...")
            breakout = self.detector._detect_breakout(data, line_data, "resistance")
            debug["breakout"] = {"detected": breakout is not None, "data": breakout}
            logger.info(f"   ブレイクアウト検出: {'成功' if breakout else '失敗'}")

            if not breakout:
                # ブレイクアウト検出の詳細分析
                debug["breakout_analysis"] = self._analyze_breakout_failure(
                    data, line_data, "resistance"
                )

        except Exception as e:
            logger.error(f"レジスタンスラインデバッグエラー: {e}")
            debug["error"] = str(e)

        return debug

    def _debug_support_line(self, data: pd.DataFrame) -> Dict:
        """サポートライン詳細デバッグ"""
        debug = {}

        try:
            # 1. タッチポイント検出
            logger.info("1. サポートタッチポイント検出...")
            touch_points = self.detector._find_touch_points(data, "support")
            debug["touch_points"] = {
                "count": len(touch_points),
                "sufficient": len(touch_points) >= self.detector.min_touch_points,
                "points": touch_points[:5] if touch_points else [],
            }
            logger.info(f"   タッチポイント数: {len(touch_points)}")

            if not debug["touch_points"]["sufficient"]:
                logger.info("   ❌ タッチポイントが不足")
                return debug

            # 2. ライン方程式計算
            logger.info("2. サポートライン方程式計算...")
            line_data = self.detector._calculate_line_equation(
                touch_points, data, "Low"
            )
            debug["line_equation"] = {
                "calculated": line_data is not None,
                "data": line_data,
            }
            logger.info(f"   ライン方程式計算: {'成功' if line_data else '失敗'}")

            if not line_data:
                logger.info("   ❌ ライン方程式計算失敗")
                return debug

            # 3. ライン強度検証
            logger.info("3. サポートライン強度検証...")
            strength = self.detector._validate_line_strength(touch_points, line_data)
            debug["line_strength"] = {
                "strength": strength,
                "sufficient": strength >= 0.1,
                "threshold": 0.1,
            }
            logger.info(f"   ライン強度: {strength:.4f} (閾値: 0.1)")

            if not debug["line_strength"]["sufficient"]:
                logger.info("   ❌ ライン強度不足")
                return debug

            # 4. ブレイクアウト検出
            logger.info("4. サポートブレイクアウト検出...")
            breakout = self.detector._detect_breakout(data, line_data, "support")
            debug["breakout"] = {"detected": breakout is not None, "data": breakout}
            logger.info(f"   ブレイクアウト検出: {'成功' if breakout else '失敗'}")

            if not breakout:
                # ブレイクアウト検出の詳細分析
                debug["breakout_analysis"] = self._analyze_breakout_failure(
                    data, line_data, "support"
                )

        except Exception as e:
            logger.error(f"サポートラインデバッグエラー: {e}")
            debug["error"] = str(e)

        return debug

    def _analyze_breakout_failure(
        self, data: pd.DataFrame, line_data: Dict, line_type: str
    ) -> Dict:
        """ブレイクアウト失敗の詳細分析"""
        analysis = {}

        try:
            slope = line_data["slope"]
            intercept = line_data["intercept"]
            current_index = len(data) - 1
            current_price = data.iloc[-1]["Close"]
            line_price = slope * current_index + intercept

            analysis["current_price"] = current_price
            analysis["line_price"] = line_price
            analysis["price_difference"] = current_price - line_price
            analysis["price_difference_percent"] = (
                current_price - line_price
            ) / line_price

            if line_type == "resistance":
                analysis["breakout_condition"] = current_price > line_price
                analysis["breakout_strength"] = (
                    (current_price - line_price) / line_price
                    if current_price > line_price
                    else 0
                )
            else:
                analysis["breakout_condition"] = current_price < line_price
                analysis["breakout_strength"] = (
                    (line_price - current_price) / line_price
                    if current_price < line_price
                    else 0
                )

            analysis["threshold"] = self.detector.breakout_threshold
            analysis["strength_sufficient"] = (
                analysis["breakout_strength"] > self.detector.breakout_threshold
            )

            logger.info(f"   現在価格: {current_price:.4f}")
            logger.info(f"   ライン価格: {line_price:.4f}")
            logger.info(f"   価格差: {analysis['price_difference']:.4f}")
            logger.info(f"   価格差%: {analysis['price_difference_percent']:.4f}")
            logger.info(f"   ブレイクアウト条件: {analysis['breakout_condition']}")
            logger.info(f"   ブレイクアウト強度: {analysis['breakout_strength']:.4f}")
            logger.info(f"   閾値: {self.detector.breakout_threshold}")
            logger.info(f"   強度十分: {analysis['strength_sufficient']}")

        except Exception as e:
            analysis["error"] = str(e)

        return analysis


async def main():
    """メイン関数"""
    debugger = Pattern15RealDataDebugger()
    results = await debugger.debug_pattern15_with_real_data()

    if "error" in results:
        print(f"\n❌ デバッグエラー: {results['error']}")
        return

    print("\n=== パターン15実データデバッグ結果 ===")

    # データ情報
    print(f"\n📊 データ情報:")
    data_info = results["data_info"]
    print(f"  総データポイント: {data_info['total_points']}")
    print(f"  期間: {data_info['date_range']}")
    print(f"  価格範囲: {data_info['price_range']}")
    print(f"  平均価格: {data_info['avg_price']:.2f}")

    # レジスタンスライン結果
    print(f"\n🔴 レジスタンスライン:")
    resistance = results["resistance_debug"]
    if "error" in resistance:
        print(f"  エラー: {resistance['error']}")
    else:
        print(
            f"  タッチポイント: {resistance['touch_points']['count']}件 (十分: {resistance['touch_points']['sufficient']})"
        )
        print(
            f"  ライン方程式: {'成功' if resistance['line_equation']['calculated'] else '失敗'}"
        )
        if "line_strength" in resistance:
            print(
                f"  ライン強度: {resistance['line_strength']['strength']:.4f} (十分: {resistance['line_strength']['sufficient']})"
            )
        print(f"  ブレイクアウト: {'検出' if resistance['breakout']['detected'] else '未検出'}")

        if not resistance["breakout"]["detected"] and "breakout_analysis" in resistance:
            analysis = resistance["breakout_analysis"]
            print(f"    現在価格: {analysis['current_price']:.4f}")
            print(f"    ライン価格: {analysis['line_price']:.4f}")
            print(f"    ブレイクアウト強度: {analysis['breakout_strength']:.4f}")
            print(f"    閾値: {analysis['threshold']}")

    # サポートライン結果
    print(f"\n🟢 サポートライン:")
    support = results["support_debug"]
    if "error" in support:
        print(f"  エラー: {support['error']}")
    else:
        print(
            f"  タッチポイント: {support['touch_points']['count']}件 (十分: {support['touch_points']['sufficient']})"
        )
        print(f"  ライン方程式: {'成功' if support['line_equation']['calculated'] else '失敗'}")
        if "line_strength" in support:
            print(
                f"  ライン強度: {support['line_strength']['strength']:.4f} (十分: {support['line_strength']['sufficient']})"
            )
        print(f"  ブレイクアウト: {'検出' if support['breakout']['detected'] else '未検出'}")

        if not support["breakout"]["detected"] and "breakout_analysis" in support:
            analysis = support["breakout_analysis"]
            print(f"    現在価格: {analysis['current_price']:.4f}")
            print(f"    ライン価格: {analysis['line_price']:.4f}")
            print(f"    ブレイクアウト強度: {analysis['breakout_strength']:.4f}")
            print(f"    閾値: {analysis['threshold']}")

    # 全体結果
    print(f"\n🎯 全体結果:")
    overall = results["overall_result"]
    print(f"  検出: {'成功' if overall['detected'] else '失敗'}")


if __name__ == "__main__":
    asyncio.run(main())
