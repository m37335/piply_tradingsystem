"""
ライン方程式計算デバッグスクリプト

なぜレジスタンスラインのライン方程式計算が失敗するかを詳細に分析する
"""

import asyncio
import logging
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


class LineEquationDebugger:
    """ライン方程式計算デバッガー"""

    def __init__(self):
        self.detector = SupportResistanceDetector()

    async def debug_line_equation(self) -> Dict:
        """ライン方程式計算の詳細デバッグ"""
        logger.info("=== ライン方程式計算デバッグ開始 ===")

        try:
            # データベース接続
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )
            logger.info("✅ データベース接続完了")

            # 直近1ヶ月のデータでテスト
            data = await self._fetch_market_data(30)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"取得データ: {len(data)}件")

            # レジスタンスラインの詳細分析
            resistance_analysis = self._debug_resistance_line_equation(data)

            # サポートラインの詳細分析
            support_analysis = self._debug_support_line_equation(data)

            # データベース接続終了
            await db_manager.close()

            return {
                "resistance_analysis": resistance_analysis,
                "support_analysis": support_analysis,
            }

        except Exception as e:
            logger.error(f"ライン方程式デバッグエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    def _debug_resistance_line_equation(self, data: pd.DataFrame) -> Dict:
        """レジスタンスライン方程式計算の詳細デバッグ"""
        try:
            analysis = {}

            # タッチポイント検出
            touch_points = self.detector._find_touch_points(data, "resistance")
            analysis["touch_points"] = {
                "count": len(touch_points),
                "indices": touch_points[:10],  # 最初の10個のみ表示
            }

            if len(touch_points) >= 1:
                # タッチポイントの価格を取得
                touch_prices = [data.iloc[point]["High"] for point in touch_points]
                analysis["touch_prices"] = {
                    "prices": touch_prices[:10],  # 最初の10個のみ表示
                    "unique_count": len(set(touch_prices)),
                    "min_price": min(touch_prices),
                    "max_price": max(touch_prices),
                    "price_range": max(touch_prices) - min(touch_prices),
                }

                # ライン方程式計算の詳細
                line_data = self.detector._calculate_line_equation(
                    touch_points, data, "High"
                )
                analysis["line_equation"] = {
                    "success": line_data is not None,
                    "slope": line_data.get("slope") if line_data else None,
                    "intercept": line_data.get("intercept") if line_data else None,
                }

                if not line_data:
                    # 失敗理由の詳細分析
                    failure_reason = self._analyze_line_equation_failure(
                        touch_points, data, "High"
                    )
                    analysis["failure_reason"] = failure_reason

            return analysis

        except Exception as e:
            logger.error(f"レジスタンスライン方程式デバッグエラー: {e}")
            return {"error": str(e)}

    def _debug_support_line_equation(self, data: pd.DataFrame) -> Dict:
        """サポートライン方程式計算の詳細デバッグ"""
        try:
            analysis = {}

            # タッチポイント検出
            touch_points = self.detector._find_touch_points(data, "support")
            analysis["touch_points"] = {
                "count": len(touch_points),
                "indices": touch_points[:10],  # 最初の10個のみ表示
            }

            if len(touch_points) >= 1:
                # タッチポイントの価格を取得
                touch_prices = [data.iloc[point]["Low"] for point in touch_points]
                analysis["touch_prices"] = {
                    "prices": touch_prices[:10],  # 最初の10個のみ表示
                    "unique_count": len(set(touch_prices)),
                    "min_price": min(touch_prices),
                    "max_price": max(touch_prices),
                    "price_range": max(touch_prices) - min(touch_prices),
                }

                # ライン方程式計算の詳細
                line_data = self.detector._calculate_line_equation(
                    touch_points, data, "Low"
                )
                analysis["line_equation"] = {
                    "success": line_data is not None,
                    "slope": line_data.get("slope") if line_data else None,
                    "intercept": line_data.get("intercept") if line_data else None,
                }

                if not line_data:
                    # 失敗理由の詳細分析
                    failure_reason = self._analyze_line_equation_failure(
                        touch_points, data, "Low"
                    )
                    analysis["failure_reason"] = failure_reason

            return analysis

        except Exception as e:
            logger.error(f"サポートライン方程式デバッグエラー: {e}")
            return {"error": str(e)}

    def _analyze_line_equation_failure(
        self, touch_points: List[int], data: pd.DataFrame, column: str
    ) -> Dict:
        """ライン方程式計算失敗の詳細分析"""
        try:
            analysis = {}

            # タッチポイントの価格を取得
            x = [point for point in touch_points]
            y = [data.iloc[point][column] for point in touch_points]

            analysis["data_points"] = {
                "x_values": x[:10],  # 最初の10個のみ表示
                "y_values": y[:10],  # 最初の10個のみ表示
                "x_unique": len(set(x)),
                "y_unique": len(set(y)),
            }

            # 価格の一意性チェック
            if len(set(y)) < 2:
                analysis["failure_cause"] = "価格の一意性不足"
                analysis["details"] = f"一意な価格数: {len(set(y))} (最低2個必要)"
            else:
                analysis["failure_cause"] = "その他の理由"
                analysis["details"] = "価格は一意だが計算で失敗"

            return analysis

        except Exception as e:
            logger.error(f"失敗理由分析エラー: {e}")
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


async def main():
    """メイン関数"""
    debugger = LineEquationDebugger()
    results = await debugger.debug_line_equation()

    if "error" in results:
        print(f"\n❌ デバッグエラー: {results['error']}")
        return

    print("\n=== ライン方程式計算デバッグ結果 ===")

    # レジスタンスライン分析
    print(f"\n📈 レジスタンスライン分析:")
    resistance = results.get("resistance_analysis", {})

    if "touch_points" in resistance:
        tp = resistance["touch_points"]
        print(f"  タッチポイント: {tp['count']}件")
        print(f"  インデックス例: {tp['indices']}")

    if "touch_prices" in resistance:
        prices = resistance["touch_prices"]
        print(f"  価格情報:")
        print(f"    一意な価格数: {prices['unique_count']}個")
        print(f"    価格範囲: {prices['min_price']:.5f} - {prices['max_price']:.5f}")
        print(f"    価格差: {prices['price_range']:.5f}")
        print(f"    価格例: {prices['prices'][:5]}")

    if "line_equation" in resistance:
        le = resistance["line_equation"]
        print(f"  ライン方程式: {'成功' if le['success'] else '失敗'}")
        if le["success"]:
            print(f"    傾き: {le['slope']:.6f}")
            print(f"    切片: {le['intercept']:.5f}")

    if "failure_reason" in resistance:
        fr = resistance["failure_reason"]
        print(f"  失敗理由: {fr.get('failure_cause', '不明')}")
        print(f"  詳細: {fr.get('details', 'なし')}")

    # サポートライン分析
    print(f"\n📉 サポートライン分析:")
    support = results.get("support_analysis", {})

    if "touch_points" in support:
        tp = support["touch_points"]
        print(f"  タッチポイント: {tp['count']}件")
        print(f"  インデックス例: {tp['indices']}")

    if "touch_prices" in support:
        prices = support["touch_prices"]
        print(f"  価格情報:")
        print(f"    一意な価格数: {prices['unique_count']}個")
        print(f"    価格範囲: {prices['min_price']:.5f} - {prices['max_price']:.5f}")
        print(f"    価格差: {prices['price_range']:.5f}")
        print(f"    価格例: {prices['prices'][:5]}")

    if "line_equation" in support:
        le = support["line_equation"]
        print(f"  ライン方程式: {'成功' if le['success'] else '失敗'}")
        if le["success"]:
            print(f"    傾き: {le['slope']:.6f}")
            print(f"    切片: {le['intercept']:.5f}")

    if "failure_reason" in support:
        fr = support["failure_reason"]
        print(f"  失敗理由: {fr.get('failure_cause', '不明')}")
        print(f"  詳細: {fr.get('details', 'なし')}")


if __name__ == "__main__":
    asyncio.run(main())
