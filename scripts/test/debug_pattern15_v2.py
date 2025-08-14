"""
パターン15 V2 詳細デバッグスクリプト

なぜ検出されないのかを詳細に分析する
"""

import asyncio
import logging
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from src.infrastructure.analysis.pattern_detectors.support_resistance_detector_v2 import SupportResistanceDetectorV2
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Pattern15V2Debugger:
    """パターン15 V2 デバッガー"""

    def __init__(self):
        self.detector = SupportResistanceDetectorV2()

    async def debug_pattern15_v2(self) -> Dict:
        """パターン15 V2の詳細デバッグ"""
        logger.info("=== パターン15 V2 詳細デバッグ開始 ===")

        try:
            # データベース接続
            await db_manager.initialize("sqlite+aiosqlite:///./data/exchange_analytics.db")
            logger.info("✅ データベース接続完了")

            # 直近1ヶ月のデータで詳細デバッグ
            data = await self._fetch_market_data(30)
            if data.empty:
                return {"error": "データが取得できませんでした"}

            logger.info(f"取得データ: {len(data)}件")

            # 詳細分析
            debug_info = self._detailed_analysis(data)

            # データベース接続終了
            await db_manager.close()

            return debug_info

        except Exception as e:
            logger.error(f"パターン15 V2デバッグエラー: {e}")
            await db_manager.close()
            return {"error": str(e)}

    def _detailed_analysis(self, data: pd.DataFrame) -> Dict:
        """詳細分析"""
        try:
            analysis = {
                "resistance_analysis": {},
                "support_analysis": {},
                "recommendations": []
            }

            # レジスタンスライン分析
            resistance_analysis = self._debug_resistance_line(data)
            analysis["resistance_analysis"] = resistance_analysis

            # サポートライン分析
            support_analysis = self._debug_support_line(data)
            analysis["support_analysis"] = support_analysis

            # 推奨事項生成
            recommendations = self._generate_recommendations(analysis)
            analysis["recommendations"] = recommendations

            return analysis

        except Exception as e:
            logger.error(f"詳細分析エラー: {e}")
            return {"error": str(e)}

    def _debug_resistance_line(self, data: pd.DataFrame) -> Dict:
        """レジスタンスラインの詳細デバッグ"""
        try:
            analysis = {}

            # 高値の極大値検出
            peaks = self.detector._find_price_peaks(data["High"].values, "max")
            analysis["peaks"] = {
                "count": len(peaks),
                "min_required": self.detector.min_peaks,
                "indices": peaks[:10]  # 最初の10個のみ表示
            }

            if len(peaks) >= self.detector.min_peaks:
                # 最適な1次関数計算
                best_line = self.detector._find_best_line_equation(peaks, data, "High")
                analysis["line_equation"] = {
                    "success": best_line is not None,
                    "slope": best_line.get("slope") if best_line else None,
                    "intercept": best_line.get("intercept") if best_line else None,
                    "angle": best_line.get("angle") if best_line else None,
                    "score": best_line.get("score") if best_line else None
                }

                if best_line:
                    # ライン強度計算
                    strength = self.detector._calculate_line_strength_v2(peaks, best_line, data, "High")
                    analysis["line_strength"] = {
                        "strength": strength,
                        "min_required": self.detector.min_line_strength,
                        "passed": strength >= self.detector.min_line_strength
                    }

                    if strength >= self.detector.min_line_strength:
                        # 現在価格との関係分析
                        current_analysis = self.detector._analyze_current_price_relation(data, best_line, "resistance")
                        analysis["current_relation"] = current_analysis

            return analysis

        except Exception as e:
            logger.error(f"レジスタンスラインデバッグエラー: {e}")
            return {"error": str(e)}

    def _debug_support_line(self, data: pd.DataFrame) -> Dict:
        """サポートラインの詳細デバッグ"""
        try:
            analysis = {}

            # 安値の極小値検出
            troughs = self.detector._find_price_peaks(data["Low"].values, "min")
            analysis["troughs"] = {
                "count": len(troughs),
                "min_required": self.detector.min_peaks,
                "indices": troughs[:10]  # 最初の10個のみ表示
            }

            if len(troughs) >= self.detector.min_peaks:
                # 最適な1次関数計算
                best_line = self.detector._find_best_line_equation(troughs, data, "Low")
                analysis["line_equation"] = {
                    "success": best_line is not None,
                    "slope": best_line.get("slope") if best_line else None,
                    "intercept": best_line.get("intercept") if best_line else None,
                    "angle": best_line.get("angle") if best_line else None,
                    "score": best_line.get("score") if best_line else None
                }

                if best_line:
                    # ライン強度計算
                    strength = self.detector._calculate_line_strength_v2(troughs, best_line, data, "Low")
                    analysis["line_strength"] = {
                        "strength": strength,
                        "min_required": self.detector.min_line_strength,
                        "passed": strength >= self.detector.min_line_strength
                    }

                    if strength >= self.detector.min_line_strength:
                        # 現在価格との関係分析
                        current_analysis = self.detector._analyze_current_price_relation(data, best_line, "support")
                        analysis["current_relation"] = current_analysis

            return analysis

        except Exception as e:
            logger.error(f"サポートラインデバッグエラー: {e}")
            return {"error": str(e)}

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """推奨事項生成"""
        recommendations = []

        # レジスタンスライン分析
        resistance = analysis.get("resistance_analysis", {})
        if "peaks" in resistance:
            peak_count = resistance["peaks"]["count"]
            min_required = resistance["peaks"]["min_required"]
            if peak_count < min_required:
                recommendations.append(f"レジスタンスライン: ピーク数が不足 ({peak_count}/{min_required})")

        if "line_equation" in resistance:
            if not resistance["line_equation"]["success"]:
                recommendations.append("レジスタンスライン: 1次関数計算に失敗")

        if "line_strength" in resistance:
            strength = resistance["line_strength"]["strength"]
            min_required = resistance["line_strength"]["min_required"]
            if strength < min_required:
                recommendations.append(f"レジスタンスライン: ライン強度が不足 ({strength:.3f}/{min_required})")

        # サポートライン分析
        support = analysis.get("support_analysis", {})
        if "troughs" in support:
            trough_count = support["troughs"]["count"]
            min_required = support["troughs"]["min_required"]
            if trough_count < min_required:
                recommendations.append(f"サポートライン: ボトム数が不足 ({trough_count}/{min_required})")

        if "line_equation" in support:
            if not support["line_equation"]["success"]:
                recommendations.append("サポートライン: 1次関数計算に失敗")

        if "line_strength" in support:
            strength = support["line_strength"]["strength"]
            min_required = support["line_strength"]["min_required"]
            if strength < min_required:
                recommendations.append(f"サポートライン: ライン強度が不足 ({strength:.3f}/{min_required})")

        if not recommendations:
            recommendations.append("すべての条件が満たされています。検出されるはずです。")

        return recommendations

    async def _fetch_market_data(self, days: int) -> pd.DataFrame:
        """市場データ取得"""
        try:
            async with db_manager.get_session() as session:
                query = text("""
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
                """)
                
                result = await session.execute(query, {"days": days})
                rows = result.fetchall()
                
                if not rows:
                    return pd.DataFrame()
                
                data = pd.DataFrame(rows, columns=[
                    "Date", "Open", "High", "Low", "Close", "Volume"
                ])
                
                data = data.sort_values("Date").reset_index(drop=True)
                return data

        except Exception as e:
            logger.error(f"データ取得エラー: {e}")
            return pd.DataFrame()


async def main():
    """メイン関数"""
    debugger = Pattern15V2Debugger()
    results = await debugger.debug_pattern15_v2()
    
    if "error" in results:
        print(f"\n❌ デバッグエラー: {results['error']}")
        return
    
    print("\n=== パターン15 V2 詳細デバッグ結果 ===")
    
    # レジスタンスライン分析
    print(f"\n📈 レジスタンスライン分析:")
    resistance = results.get("resistance_analysis", {})
    
    if "peaks" in resistance:
        peaks = resistance["peaks"]
        print(f"  ピーク数: {peaks['count']}件 (必要: {peaks['min_required']}件)")
        print(f"  ピークインデックス: {peaks['indices']}")
    
    if "line_equation" in resistance:
        le = resistance["line_equation"]
        print(f"  1次関数: {'成功' if le['success'] else '失敗'}")
        if le['success']:
            print(f"    傾き: {le['slope']:.6f}")
            print(f"    角度: {le['angle']:.2f}度")
            print(f"    切片: {le['intercept']:.5f}")
            print(f"    スコア: {le['score']:.3f}")
    
    if "line_strength" in resistance:
        ls = resistance["line_strength"]
        print(f"  ライン強度: {ls['strength']:.3f} (必要: {ls['min_required']})")
    
    # サポートライン分析
    print(f"\n📉 サポートライン分析:")
    support = results.get("support_analysis", {})
    
    if "troughs" in support:
        troughs = support["troughs"]
        print(f"  ボトム数: {troughs['count']}件 (必要: {troughs['min_required']}件)")
        print(f"  ボトムインデックス: {troughs['indices']}")
    
    if "line_equation" in support:
        le = support["line_equation"]
        print(f"  1次関数: {'成功' if le['success'] else '失敗'}")
        if le['success']:
            print(f"    傾き: {le['slope']:.6f}")
            print(f"    角度: {le['angle']:.2f}度")
            print(f"    切片: {le['intercept']:.5f}")
            print(f"    スコア: {le['score']:.3f}")
    
    if "line_strength" in support:
        ls = support["line_strength"]
        print(f"  ライン強度: {ls['strength']:.3f} (必要: {ls['min_required']})")
    
    # 推奨事項
    recommendations = results.get("recommendations", [])
    if recommendations:
        print(f"\n💡 推奨事項:")
        for rec in recommendations:
            print(f"  • {rec}")


if __name__ == "__main__":
    asyncio.run(main())
