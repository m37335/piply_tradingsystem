"""
パターン発生頻度分析スクリプト
実際の市場データで各パターンの発生頻度を統計的に分析
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import text

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

# データベース関連のインポート
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class PatternFrequencyAnalyzer:
    """パターン発生頻度分析クラス"""

    def __init__(self):
        self.detectors = {
            1: ("トレンド転換", TrendReversalDetector()),
            2: ("プルバック", PullbackDetector()),
            3: ("ダイバージェンス", DivergenceDetector()),
            4: ("ブレイクアウト", BreakoutDetector()),
            5: ("RSI戦い", RSIBattleDetector()),
            6: ("複合シグナル", CompositeSignalDetector()),
            7: ("つつみ足", EngulfingPatternDetector()),
            8: ("赤三兵", RedThreeSoldiersDetector()),
            9: ("大陽線/大陰線", MarubozuDetector()),
            10: ("ダブルトップ/ボトム", DoubleTopBottomDetector()),
            11: ("トリプルトップ/ボトム", TripleTopBottomDetector()),
            12: ("フラッグパターン", FlagPatternDetector()),
            13: ("三尊天井/逆三尊", ThreeBuddhasDetector()),
            14: ("ウェッジパターン", WedgePatternDetector()),
            15: ("レジスタンス/サポート", SupportResistanceDetector()),
            16: ("ロールリバーサル", RollReversalDetector()),
        }

    async def analyze_pattern_frequency(self):
        """パターン発生頻度の分析実行"""
        logger.info("=== パターン発生頻度分析開始 ===")

        try:
            # データベース接続
            logger.info("データベースに接続中...")
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )

            # データ取得（より長期間）
            logger.info("USD/JPYの長期データを取得中...")
            market_data = await self._fetch_extended_market_data()

            if market_data is None or market_data.empty:
                logger.error("❌ データ取得に失敗しました")
                return

            logger.info(f"✅ データ取得完了: {len(market_data)}件")
            logger.info(
                f"期間: {market_data['Date'].min()} 〜 {market_data['Date'].max()}"
            )

            # 期間分割分析
            logger.info("期間分割での頻度分析を実行中...")
            frequency_results = await self._analyze_frequency_by_period(market_data)

            # 結果表示
            self._display_frequency_results(frequency_results)

        except Exception as e:
            logger.error(f"分析実行エラー: {e}")
        finally:
            await db_manager.close()

    async def _fetch_extended_market_data(self) -> pd.DataFrame:
        """より長期間の市場データを取得"""
        try:
            # 過去1年分のデータを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)

            query = """
                SELECT
                    timestamp as Date,
                    open_price as Open,
                    high_price as High,
                    low_price as Low,
                    close_price as Close,
                    volume as Volume
                FROM price_data
                WHERE currency_pair = 'USD/JPY'
                AND timestamp BETWEEN :start_date AND :end_date
                ORDER BY timestamp ASC
            """

            async with db_manager.get_session() as session:
                result = await session.execute(
                    text(query), {"start_date": start_date, "end_date": end_date}
                )
                result = result.fetchall()

            if not result:
                logger.error("データベースにUSD/JPYデータが見つかりません")
                return None

            # データフレームに変換
            df = pd.DataFrame(result)
            df["Date"] = pd.to_datetime(df["Date"])

            return df

        except Exception as e:
            logger.error(f"データベース取得エラー: {e}")
            return None

    async def _analyze_frequency_by_period(
        self, market_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """期間分割での頻度分析"""
        results = {}

        # 期間を分割（月単位）
        market_data["year_month"] = market_data["Date"].dt.to_period("M")
        periods = market_data["year_month"].unique()

        logger.info(f"分析期間数: {len(periods)}ヶ月")

        for pattern_num, (pattern_name, detector) in self.detectors.items():
            logger.info(f"パターン{pattern_num} ({pattern_name}) の頻度分析中...")

            pattern_results = {
                "pattern_name": pattern_name,
                "total_detections": 0,
                "monthly_frequency": [],
                "detection_dates": [],
                "avg_interval_days": None,
                "max_interval_days": None,
                "min_interval_days": None,
            }

            # 月別検出回数を計算
            for period in periods:
                period_data = market_data[market_data["year_month"] == period]
                if len(period_data) < 10:  # データが少ない月はスキップ
                    continue

                try:
                    result = detector.detect(period_data)
                    if result:
                        pattern_results["total_detections"] += 1
                        pattern_results["monthly_frequency"].append(
                            {
                                "period": str(period),
                                "detections": 1,
                                "data_points": len(period_data),
                            }
                        )
                        # 検出日を記録
                        if "timestamp" in result:
                            pattern_results["detection_dates"].append(
                                result["timestamp"]
                            )
                        else:
                            pattern_results["detection_dates"].append(
                                period_data["Date"].iloc[-1]
                            )
                except Exception as e:
                    logger.debug(f"パターン{pattern_num} 期間{period}でエラー: {e}")

            # 検出間隔を計算
            if len(pattern_results["detection_dates"]) > 1:
                detection_dates = sorted(pattern_results["detection_dates"])
                intervals = []
                for i in range(1, len(detection_dates)):
                    interval = (detection_dates[i] - detection_dates[i - 1]).days
                    intervals.append(interval)

                if intervals:
                    pattern_results["avg_interval_days"] = np.mean(intervals)
                    pattern_results["max_interval_days"] = np.max(intervals)
                    pattern_results["min_interval_days"] = np.min(intervals)

            results[pattern_num] = pattern_results

        return results

    def _display_frequency_results(self, frequency_results: Dict[str, Any]):
        """頻度分析結果の表示"""
        print("\n" + "=" * 80)
        print("📊 パターン発生頻度分析結果")
        print("=" * 80)

        # 検出回数でソート
        sorted_patterns = sorted(
            frequency_results.items(),
            key=lambda x: x[1]["total_detections"],
            reverse=True,
        )

        print(f"\n🎯 パターン別検出頻度（降順）:")
        print(
            f"{'順位':<4} {'パターン':<6} {'パターン名':<20} {'検出回数':<8} {'月平均':<8} {'平均間隔':<10}"
        )
        print("-" * 80)

        for rank, (pattern_num, result) in enumerate(sorted_patterns, 1):
            total_detections = result["total_detections"]
            pattern_name = result["pattern_name"]

            # 月平均検出回数
            monthly_avg = total_detections / 12 if total_detections > 0 else 0

            # 平均間隔
            avg_interval = result["avg_interval_days"]
            interval_str = f"{avg_interval:.1f}日" if avg_interval else "N/A"

            print(
                f"{rank:<4} {pattern_num:<6} {pattern_name:<20} {total_detections:<8} {monthly_avg:<8.2f} {interval_str:<10}"
            )

        print("\n" + "=" * 80)

        # 詳細分析
        print(f"\n📈 詳細分析:")

        # 高頻度パターン（月1回以上）
        high_freq_patterns = [
            (num, result)
            for num, result in sorted_patterns
            if result["total_detections"] >= 12
        ]

        if high_freq_patterns:
            print(f"\n🔥 高頻度パターン（月1回以上）:")
            for pattern_num, result in high_freq_patterns:
                print(
                    f"   パターン{pattern_num}: {result['pattern_name']} - {result['total_detections']}回"
                )

        # 中頻度パターン（月0.5回以上）
        medium_freq_patterns = [
            (num, result)
            for num, result in sorted_patterns
            if 6 <= result["total_detections"] < 12
        ]

        if medium_freq_patterns:
            print(f"\n⚡ 中頻度パターン（月0.5回以上）:")
            for pattern_num, result in medium_freq_patterns:
                print(
                    f"   パターン{pattern_num}: {result['pattern_name']} - {result['total_detections']}回"
                )

        # 低頻度パターン（月0.5回未満）
        low_freq_patterns = [
            (num, result)
            for num, result in sorted_patterns
            if result["total_detections"] < 6
        ]

        if low_freq_patterns:
            print(f"\n🐌 低頻度パターン（月0.5回未満）:")
            for pattern_num, result in low_freq_patterns:
                print(
                    f"   パターン{pattern_num}: {result['pattern_name']} - {result['total_detections']}回"
                )

        print("\n" + "=" * 80)

        # 推奨事項
        print(f"\n💡 基準調整の推奨事項:")

        if high_freq_patterns:
            print(f"   ✅ 高頻度パターン: 現在の基準で十分検出可能")

        if medium_freq_patterns:
            print(f"   ⚠️ 中頻度パターン: 基準を少し緩和して検出率向上")

        if low_freq_patterns:
            print(f"   🔧 低頻度パターン: 基準を大幅に緩和するか、市場状況に応じた調整が必要")

        print(f"\n📋 次のステップ:")
        print(f"   1. 低頻度パターンの基準緩和")
        print(f"   2. 市場状況別の基準調整")
        print(f"   3. 複数時間足での頻度分析")


async def main():
    """メイン関数"""
    analyzer = PatternFrequencyAnalyzer()
    await analyzer.analyze_pattern_frequency()


if __name__ == "__main__":
    asyncio.run(main())
