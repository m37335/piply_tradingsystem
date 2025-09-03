"""
実データパターン分析スクリプト

実際のデータの特徴を分析して、タッチポイント検出の問題を調査する
"""

import asyncio
import logging
from typing import Dict, List

import pandas as pd
from sqlalchemy import text

from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RealDataPatternAnalyzer:
    """実データパターン分析器"""

    async def analyze_real_data_patterns(self) -> Dict:
        """実データのパターンを分析"""
        logger.info("=== 実データパターン分析開始 ===")

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

            # データ分析実行
            analysis = self._analyze_data_patterns(data)

            # データベース接続終了
            await db_manager.close()

            return analysis

        except Exception as e:
            logger.error(f"分析エラー: {e}")
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

    def _analyze_data_patterns(self, data: pd.DataFrame) -> Dict:
        """データパターンの分析"""
        analysis = {
            "basic_stats": {},
            "high_patterns": {},
            "low_patterns": {},
            "price_movements": {},
            "recommendations": [],
        }

        # 基本統計
        analysis["basic_stats"] = {
            "total_points": len(data),
            "price_range": f"{data['Close'].min():.4f} - {data['Close'].max():.4f}",
            "avg_price": data["Close"].mean(),
            "price_volatility": data["Close"].std(),
            "high_range": f"{data['High'].min():.4f} - {data['High'].max():.4f}",
            "low_range": f"{data['Low'].min():.4f} - {data['Low'].max():.4f}",
        }

        # 高値パターン分析
        analysis["high_patterns"] = self._analyze_high_patterns(data)

        # 安値パターン分析
        analysis["low_patterns"] = self._analyze_low_patterns(data)

        # 価格変動分析
        analysis["price_movements"] = self._analyze_price_movements(data)

        # 推奨事項生成
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    def _analyze_high_patterns(self, data: pd.DataFrame) -> Dict:
        """高値パターンの分析"""
        patterns = {
            "strict_peaks": [],
            "relaxed_peaks": [],
            "consecutive_highs": [],
            "high_frequency": 0,
        }

        # 厳格なピーク検出（元の条件）
        for i in range(2, len(data) - 2):
            if (
                data.iloc[i]["High"] > data.iloc[i - 1]["High"]
                and data.iloc[i]["High"] > data.iloc[i - 2]["High"]
                and data.iloc[i]["High"] > data.iloc[i + 1]["High"]
                and data.iloc[i]["High"] > data.iloc[i + 2]["High"]
            ):
                patterns["strict_peaks"].append(i)

        # 緩和されたピーク検出（現在の条件）
        for i in range(1, len(data) - 1):
            if (
                data.iloc[i]["High"] > data.iloc[i - 1]["High"]
                and data.iloc[i]["High"] > data.iloc[i + 1]["High"]
            ):
                patterns["relaxed_peaks"].append(i)

        # 連続高値の分析
        consecutive_count = 0
        for i in range(1, len(data)):
            if data.iloc[i]["High"] > data.iloc[i - 1]["High"]:
                consecutive_count += 1
            else:
                if consecutive_count > 0:
                    patterns["consecutive_highs"].append(consecutive_count)
                consecutive_count = 0

        patterns["high_frequency"] = len(patterns["relaxed_peaks"]) / len(data)

        return patterns

    def _analyze_low_patterns(self, data: pd.DataFrame) -> Dict:
        """安値パターンの分析"""
        patterns = {
            "strict_bottoms": [],
            "relaxed_bottoms": [],
            "consecutive_lows": [],
            "low_frequency": 0,
        }

        # 厳格なボトム検出（元の条件）
        for i in range(2, len(data) - 2):
            if (
                data.iloc[i]["Low"] < data.iloc[i - 1]["Low"]
                and data.iloc[i]["Low"] < data.iloc[i - 2]["Low"]
                and data.iloc[i]["Low"] < data.iloc[i + 1]["Low"]
                and data.iloc[i]["Low"] < data.iloc[i + 2]["Low"]
            ):
                patterns["strict_bottoms"].append(i)

        # 緩和されたボトム検出（現在の条件）
        for i in range(1, len(data) - 1):
            if (
                data.iloc[i]["Low"] < data.iloc[i - 1]["Low"]
                and data.iloc[i]["Low"] < data.iloc[i + 1]["Low"]
            ):
                patterns["relaxed_bottoms"].append(i)

        # 連続安値の分析
        consecutive_count = 0
        for i in range(1, len(data)):
            if data.iloc[i]["Low"] < data.iloc[i - 1]["Low"]:
                consecutive_count += 1
            else:
                if consecutive_count > 0:
                    patterns["consecutive_lows"].append(consecutive_count)
                consecutive_count = 0

        patterns["low_frequency"] = len(patterns["relaxed_bottoms"]) / len(data)

        return patterns

    def _analyze_price_movements(self, data: pd.DataFrame) -> Dict:
        """価格変動の分析"""
        movements = {
            "price_changes": [],
            "high_low_spreads": [],
            "volatility_patterns": [],
        }

        # 価格変化の分析
        for i in range(1, len(data)):
            change = data.iloc[i]["Close"] - data.iloc[i - 1]["Close"]
            movements["price_changes"].append(change)

        # 高値-安値スプレッドの分析
        for i in range(len(data)):
            spread = data.iloc[i]["High"] - data.iloc[i]["Low"]
            movements["high_low_spreads"].append(spread)

        # ボラティリティパターンの分析
        for i in range(1, len(data)):
            volatility = (
                abs(data.iloc[i]["Close"] - data.iloc[i - 1]["Close"])
                / data.iloc[i - 1]["Close"]
            )
            movements["volatility_patterns"].append(volatility)

        return movements

    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """推奨事項の生成"""
        recommendations = []

        high_patterns = analysis["high_patterns"]
        low_patterns = analysis["low_patterns"]

        # 厳格なピーク/ボトムの検出数
        strict_highs = len(high_patterns["strict_peaks"])
        strict_lows = len(low_patterns["strict_bottoms"])
        relaxed_highs = len(high_patterns["relaxed_peaks"])
        relaxed_lows = len(low_patterns["relaxed_bottoms"])

        if strict_highs == 0 and strict_lows == 0:
            recommendations.append("厳格な条件ではピーク/ボトムが検出されません。条件の緩和が必要です。")

        if relaxed_highs == 0 and relaxed_lows == 0:
            recommendations.append("緩和された条件でもピーク/ボトムが検出されません。さらに条件を緩和する必要があります。")

        if relaxed_highs > 0 or relaxed_lows > 0:
            recommendations.append(
                f"緩和された条件で高値ピーク{relaxed_highs}件、安値ボトム{relaxed_lows}件が検出されました。"
            )

        # 高値/安値の頻度分析
        high_freq = high_patterns["high_frequency"]
        low_freq = low_patterns["low_frequency"]

        if high_freq < 0.1:
            recommendations.append("高値ピークの頻度が低すぎます。検出条件をさらに緩和してください。")

        if low_freq < 0.1:
            recommendations.append("安値ボトムの頻度が低すぎます。検出条件をさらに緩和してください。")

        return recommendations


async def main():
    """メイン関数"""
    analyzer = RealDataPatternAnalyzer()
    results = await analyzer.analyze_real_data_patterns()

    if "error" in results:
        print(f"\n❌ 分析エラー: {results['error']}")
        return

    print("\n=== 実データパターン分析結果 ===")

    # 基本統計
    print(f"\n📊 基本統計:")
    stats = results["basic_stats"]
    print(f"  総データポイント: {stats['total_points']}")
    print(f"  価格範囲: {stats['price_range']}")
    print(f"  平均価格: {stats['avg_price']:.4f}")
    print(f"  価格ボラティリティ: {stats['price_volatility']:.4f}")
    print(f"  高値範囲: {stats['high_range']}")
    print(f"  安値範囲: {stats['low_range']}")

    # 高値パターン
    print(f"\n🔴 高値パターン:")
    high_patterns = results["high_patterns"]
    print(f"  厳格なピーク: {len(high_patterns['strict_peaks'])}件")
    print(f"  緩和されたピーク: {len(high_patterns['relaxed_peaks'])}件")
    print(f"  高値頻度: {high_patterns['high_frequency']:.4f}")
    if high_patterns["consecutive_highs"]:
        print(f"  連続高値パターン: {high_patterns['consecutive_highs'][:5]}")  # 最初の5件のみ

    # 安値パターン
    print(f"\n🟢 安値パターン:")
    low_patterns = results["low_patterns"]
    print(f"  厳格なボトム: {len(low_patterns['strict_bottoms'])}件")
    print(f"  緩和されたボトム: {len(low_patterns['relaxed_bottoms'])}件")
    print(f"  安値頻度: {low_patterns['low_frequency']:.4f}")
    if low_patterns["consecutive_lows"]:
        print(f"  連続安値パターン: {low_patterns['consecutive_lows'][:5]}")  # 最初の5件のみ

    # 価格変動
    print(f"\n📈 価格変動:")
    movements = results["price_movements"]
    price_changes = movements["price_changes"]
    if price_changes:
        print(f"  平均価格変化: {sum(price_changes) / len(price_changes):.4f}")
        print(f"  最大価格変化: {max(price_changes, key=abs):.4f}")

    # 推奨事項
    print(f"\n💡 推奨事項:")
    for recommendation in results["recommendations"]:
        print(f"  • {recommendation}")


if __name__ == "__main__":
    asyncio.run(main())
