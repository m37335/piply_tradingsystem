"""
データベースの実際の市場データを使用したパターン検出テスト
運用中のデータベースからUSD/JPYの過去データを取得してテスト実行
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

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


class DatabaseMarketDataTester:
    """データベースの市場データを使用したテストクラス"""

    def __init__(self):
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

    async def test_database_market_data(self):
        """データベースの市場データでのテスト実行"""
        logger.info("=== データベース市場データテスト開始 ===")

        try:
            # データベース接続
            logger.info("データベースに接続中...")
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )

            # データ取得
            logger.info("USD/JPYの過去データを取得中...")
            market_data = await self._fetch_market_data_from_db()

            if market_data is None or market_data.empty:
                logger.error("❌ データ取得に失敗しました")
                return

            logger.info(f"✅ データ取得完了: {len(market_data)}件")
            logger.info(
                f"期間: {market_data['Date'].min()} 〜 {market_data['Date'].max()}"
            )

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
        finally:
            # データベース接続を閉じる
            await db_manager.close()

    async def _fetch_market_data_from_db(self) -> Optional[pd.DataFrame]:
        """データベースからUSD/JPYの過去データを取得"""
        try:
            # 過去3ヶ月分のデータを取得
            end_date = datetime.now()
            start_date = end_date - timedelta(days=90)

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
                logger.warning("データが見つかりませんでした。期間を拡張します。")
                # 期間を1年に拡張
                start_date = end_date - timedelta(days=365)
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

            # データの基本情報をログ出力
            logger.info(f"取得データ統計:")
            logger.info(f"  期間: {df['Date'].min()} 〜 {df['Date'].max()}")
            logger.info(f"  件数: {len(df)}")
            logger.info(f"  価格範囲: {df['Low'].min():.2f} 〜 {df['High'].max():.2f}")

            return df

        except Exception as e:
            logger.error(f"データベース取得エラー: {e}")
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
        print("🎯 データベース市場データテスト結果")
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
            print("✅ データベーステスト成功！検出率が良好です。")
        elif analysis_results["detection_rate"] >= 30:
            print("⚠️ 検出率が中程度。さらなる調整が必要です。")
        else:
            print("❌ 検出率が低い。基準の大幅な調整が必要です。")


async def main():
    """メイン関数"""
    tester = DatabaseMarketDataTester()
    await tester.test_database_market_data()


if __name__ == "__main__":
    asyncio.run(main())
