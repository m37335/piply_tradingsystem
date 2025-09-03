"""
現実的なパターン発生頻度分析スクリプト
実際の市場データから、現実的な基準でのパターン発生頻度を統計的に分析
"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
from sqlalchemy import text

# データベース関連のインポート
from src.infrastructure.database.connection import db_manager

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RealisticPatternFrequencyAnalyzer:
    """現実的なパターン発生頻度分析クラス"""

    def __init__(self):
        self.pattern_definitions = {
            1: "トレンド転換",
            2: "プルバック",
            3: "ダイバージェンス",
            4: "ブレイクアウト",
            5: "RSI戦い",
            6: "複合シグナル",
            7: "つつみ足",
            8: "赤三兵",
            9: "大陽線/大陰線",
            10: "ダブルトップ/ボトム",
            11: "トリプルトップ/ボトム",
            12: "フラッグパターン",
            13: "三尊天井/逆三尊",
            14: "ウェッジパターン",
            15: "レジスタンス/サポート",
            16: "ロールリバーサル",
        }

    async def analyze_realistic_frequency(self):
        """現実的なパターン発生頻度の分析実行"""
        logger.info("=== 現実的パターン発生頻度分析開始 ===")

        try:
            # データベース接続
            logger.info("データベースに接続中...")
            await db_manager.initialize(
                "sqlite+aiosqlite:///./data/exchange_analytics.db"
            )

            # データ取得
            logger.info("USD/JPYの長期データを取得中...")
            market_data = await self._fetch_market_data()

            if market_data is None or market_data.empty:
                logger.error("❌ データ取得に失敗しました")
                return

            logger.info(f"✅ データ取得完了: {len(market_data)}件")
            logger.info(
                f"期間: {market_data['Date'].min()} 〜 {market_data['Date'].max()}"
            )

            # 現実的なパターン分析
            logger.info("現実的なパターン分析を実行中...")
            frequency_results = await self._analyze_realistic_patterns(market_data)

            # 結果表示
            self._display_realistic_results(frequency_results, market_data)

        except Exception as e:
            logger.error(f"分析実行エラー: {e}")
        finally:
            await db_manager.close()

    async def _fetch_market_data(self) -> pd.DataFrame:
        """市場データを取得"""
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

    async def _analyze_realistic_patterns(
        self, market_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """現実的なパターン分析"""
        results = {}

        # 基本統計
        total_days = (market_data["Date"].max() - market_data["Date"].min()).days
        total_candles = len(market_data)

        logger.info(f"分析期間: {total_days}日, ローソク足数: {total_candles}")

        # 1. トレンド転換パターン（現実的な基準）
        results[1] = self._analyze_trend_reversals(market_data, total_days)

        # 2. プルバックパターン
        results[2] = self._analyze_pullbacks(market_data, total_days)

        # 3. ダイバージェンスパターン
        results[3] = self._analyze_divergences(market_data, total_days)

        # 4. ブレイクアウトパターン
        results[4] = self._analyze_breakouts(market_data, total_days)

        # 5. RSI戦いパターン
        results[5] = self._analyze_rsi_battles(market_data, total_days)

        # 6. 複合シグナルパターン
        results[6] = self._analyze_composite_signals(market_data, total_days)

        # 7. つつみ足パターン
        results[7] = self._analyze_engulfing_patterns(market_data, total_days)

        # 8. 赤三兵パターン
        results[8] = self._analyze_red_three_soldiers(market_data, total_days)

        # 9. 大陽線/大陰線パターン
        results[9] = self._analyze_marubozu_patterns(market_data, total_days)

        # 10. ダブルトップ/ボトムパターン
        results[10] = self._analyze_double_patterns(market_data, total_days)

        # 11. トリプルトップ/ボトムパターン
        results[11] = self._analyze_triple_patterns(market_data, total_days)

        # 12. フラッグパターン
        results[12] = self._analyze_flag_patterns(market_data, total_days)

        # 13. 三尊天井/逆三尊パターン
        results[13] = self._analyze_three_buddhas(market_data, total_days)

        # 14. ウェッジパターン
        results[14] = self._analyze_wedge_patterns(market_data, total_days)

        # 15. レジスタンス/サポートパターン
        results[15] = self._analyze_support_resistance(market_data, total_days)

        # 16. ロールリバーサルパターン
        results[16] = self._analyze_roll_reversals(market_data, total_days)

        return results

    def _analyze_trend_reversals(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """トレンド転換パターンの現実的分析"""
        # 移動平均を使用したトレンド転換検出
        data = data.copy()
        data["SMA20"] = data["Close"].rolling(window=20).mean()
        data["SMA50"] = data["Close"].rolling(window=50).mean()

        trend_changes = 0
        for i in range(50, len(data)):
            # 上昇トレンドから下降トレンドへの転換
            if (
                data["SMA20"].iloc[i - 1] > data["SMA50"].iloc[i - 1]
                and data["SMA20"].iloc[i] < data["SMA50"].iloc[i]
            ):
                trend_changes += 1
            # 下降トレンドから上昇トレンドへの転換
            elif (
                data["SMA20"].iloc[i - 1] < data["SMA50"].iloc[i - 1]
                and data["SMA20"].iloc[i] > data["SMA50"].iloc[i]
            ):
                trend_changes += 1

        return {
            "pattern_name": "トレンド転換",
            "realistic_count": trend_changes,
            "monthly_frequency": (trend_changes / (total_days / 30)),
            "description": "移動平均クロスによるトレンド転換",
        }

    def _analyze_pullbacks(self, data: pd.DataFrame, total_days: int) -> Dict[str, Any]:
        """プルバックパターンの現実的分析"""
        # 高値からの一定割合の下落をプルバックとして検出
        data = data.copy()
        data["High_20"] = data["High"].rolling(window=20).max()

        pullbacks = 0
        for i in range(20, len(data)):
            high_20 = data["High_20"].iloc[i]
            current_low = data["Low"].iloc[i]
            pullback_ratio = (high_20 - current_low) / high_20

            # 5-15%のプルバックを検出
            if 0.05 <= pullback_ratio <= 0.15:
                pullbacks += 1

        return {
            "pattern_name": "プルバック",
            "realistic_count": pullbacks,
            "monthly_frequency": (pullbacks / (total_days / 30)),
            "description": "高値からの5-15%下落",
        }

    def _analyze_divergences(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """ダイバージェンスパターンの現実的分析"""
        # RSIダイバージェンスの簡易検出
        data = data.copy()
        data["RSI"] = self._calculate_rsi(data["Close"], 14)

        divergences = 0
        for i in range(20, len(data)):
            # 価格が上昇しているがRSIが下降している（ベアリッシュダイバージェンス）
            if (
                data["Close"].iloc[i] > data["Close"].iloc[i - 5]
                and data["RSI"].iloc[i] < data["RSI"].iloc[i - 5]
            ):
                divergences += 1
            # 価格が下降しているがRSIが上昇している（ブルリッシュダイバージェンス）
            elif (
                data["Close"].iloc[i] < data["Close"].iloc[i - 5]
                and data["RSI"].iloc[i] > data["RSI"].iloc[i - 5]
            ):
                divergences += 1

        return {
            "pattern_name": "ダイバージェンス",
            "realistic_count": divergences,
            "monthly_frequency": (divergences / (total_days / 30)),
            "description": "価格とRSIの乖離",
        }

    def _analyze_breakouts(self, data: pd.DataFrame, total_days: int) -> Dict[str, Any]:
        """ブレイクアウトパターンの現実的分析"""
        # レンジブレイクアウトの検出
        data = data.copy()
        data["High_20"] = data["High"].rolling(window=20).max()
        data["Low_20"] = data["Low"].rolling(window=20).min()

        breakouts = 0
        for i in range(20, len(data)):
            # 上向きブレイクアウト
            if data["Close"].iloc[i] > data["High_20"].iloc[i - 1]:
                breakouts += 1
            # 下向きブレイクアウト
            elif data["Close"].iloc[i] < data["Low_20"].iloc[i - 1]:
                breakouts += 1

        return {
            "pattern_name": "ブレイクアウト",
            "realistic_count": breakouts,
            "monthly_frequency": (breakouts / (total_days / 30)),
            "description": "20日レンジからのブレイクアウト",
        }

    def _analyze_rsi_battles(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """RSI戦いパターンの現実的分析"""
        # RSIが30-70の範囲で停滞している期間を検出
        data = data.copy()
        data["RSI"] = self._calculate_rsi(data["Close"], 14)

        rsi_battles = 0
        for i in range(10, len(data)):
            rsi_values = data["RSI"].iloc[i - 10 : i + 1]
            # RSIが30-70の範囲で10日以上停滞
            if all(30 <= rsi <= 70 for rsi in rsi_values if not pd.isna(rsi)):
                rsi_battles += 1

        return {
            "pattern_name": "RSI戦い",
            "realistic_count": rsi_battles,
            "monthly_frequency": (rsi_battles / (total_days / 30)),
            "description": "RSI 30-70範囲での停滞",
        }

    def _analyze_composite_signals(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """複合シグナルパターンの現実的分析"""
        # 複数の指標が同時にシグナルを出す状況を検出
        data = data.copy()
        data["RSI"] = self._calculate_rsi(data["Close"], 14)
        data["SMA20"] = data["Close"].rolling(window=20).mean()

        composite_signals = 0
        for i in range(20, len(data)):
            # RSIオーバーブought + 価格が移動平均を下回る
            if (
                data["RSI"].iloc[i] > 70
                and data["Close"].iloc[i] < data["SMA20"].iloc[i]
            ):
                composite_signals += 1
            # RSIオーバーソールド + 価格が移動平均を上回る
            elif (
                data["RSI"].iloc[i] < 30
                and data["Close"].iloc[i] > data["SMA20"].iloc[i]
            ):
                composite_signals += 1

        return {
            "pattern_name": "複合シグナル",
            "realistic_count": composite_signals,
            "monthly_frequency": (composite_signals / (total_days / 30)),
            "description": "RSI + 移動平均の複合シグナル",
        }

    def _analyze_engulfing_patterns(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """つつみ足パターンの現実的分析"""
        engulfing_patterns = 0
        for i in range(1, len(data)):
            prev_open = data["Open"].iloc[i - 1]
            prev_close = data["Close"].iloc[i - 1]
            curr_open = data["Open"].iloc[i]
            curr_close = data["Close"].iloc[i]

            # 陽線が陰線を包む
            if (
                curr_close > curr_open
                and prev_close < prev_open  # 陽線
                and curr_open < prev_close  # 前日陰線
                and curr_close > prev_open  # 今日の始値 < 前日の終値
            ):  # 今日の終値 > 前日の始値
                engulfing_patterns += 1
            # 陰線が陽線を包む
            elif (
                curr_close < curr_open
                and prev_close > prev_open  # 陰線
                and curr_open > prev_close  # 前日陽線
                and curr_close < prev_open  # 今日の始値 > 前日の終値
            ):  # 今日の終値 < 前日の始値
                engulfing_patterns += 1

        return {
            "pattern_name": "つつみ足",
            "realistic_count": engulfing_patterns,
            "monthly_frequency": (engulfing_patterns / (total_days / 30)),
            "description": "前日ローソク足を包むパターン",
        }

    def _analyze_red_three_soldiers(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """赤三兵パターンの現実的分析"""
        red_three_soldiers = 0
        for i in range(3, len(data)):
            # 連続3日間の陽線
            if all(
                data["Close"].iloc[j] > data["Open"].iloc[j]
                for j in range(i - 2, i + 1)
            ):
                red_three_soldiers += 1

        return {
            "pattern_name": "赤三兵",
            "realistic_count": red_three_soldiers,
            "monthly_frequency": (red_three_soldiers / (total_days / 30)),
            "description": "連続3日間の陽線",
        }

    def _analyze_marubozu_patterns(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """大陽線/大陰線パターンの現実的分析"""
        marubozu_patterns = 0
        for i in range(len(data)):
            open_price = data["Open"].iloc[i]
            close_price = data["Close"].iloc[i]
            high_price = data["High"].iloc[i]
            low_price = data["Low"].iloc[i]

            body_size = abs(close_price - open_price)
            total_range = high_price - low_price

            # 実体が全体の80%以上
            if body_size / total_range > 0.8:
                marubozu_patterns += 1

        return {
            "pattern_name": "大陽線/大陰線",
            "realistic_count": marubozu_patterns,
            "monthly_frequency": (marubozu_patterns / (total_days / 30)),
            "description": "実体が全体の80%以上のローソク足",
        }

    def _analyze_double_patterns(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """ダブルトップ/ボトムパターンの現実的分析"""
        # 簡易的なダブルトップ/ボトム検出
        data = data.copy()
        data["High_10"] = data["High"].rolling(window=10).max()
        data["Low_10"] = data["Low"].rolling(window=10).min()

        double_patterns = 0
        for i in range(20, len(data)):
            # ダブルトップ
            if (
                data["High"].iloc[i] > data["High"].iloc[i - 1]
                and data["High"].iloc[i] > data["High"].iloc[i - 2]
                and abs(data["High"].iloc[i] - data["High"].iloc[i - 10]) < 0.5
            ):
                double_patterns += 1
            # ダブルボトム
            elif (
                data["Low"].iloc[i] < data["Low"].iloc[i - 1]
                and data["Low"].iloc[i] < data["Low"].iloc[i - 2]
                and abs(data["Low"].iloc[i] - data["Low"].iloc[i - 10]) < 0.5
            ):
                double_patterns += 1

        return {
            "pattern_name": "ダブルトップ/ボトム",
            "realistic_count": double_patterns,
            "monthly_frequency": (double_patterns / (total_days / 30)),
            "description": "類似高値/安値の形成",
        }

    def _analyze_triple_patterns(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """トリプルトップ/ボトムパターンの現実的分析"""
        # 簡易的なトリプルパターン検出
        triple_patterns = 0
        for i in range(30, len(data)):
            # 30日間で3つの類似高値/安値
            high_values = data["High"].iloc[i - 30 : i + 1]
            low_values = data["Low"].iloc[i - 30 : i + 1]

            # 高値の類似性チェック
            high_peaks = self._find_peaks(high_values)
            if len(high_peaks) >= 3:
                triple_patterns += 1

        return {
            "pattern_name": "トリプルトップ/ボトム",
            "realistic_count": triple_patterns,
            "monthly_frequency": (triple_patterns / (total_days / 30)),
            "description": "30日間で3つの類似高値/安値",
        }

    def _analyze_flag_patterns(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """フラッグパターンの現実的分析"""
        # 簡易的なフラッグパターン検出
        flag_patterns = 0
        for i in range(15, len(data)):
            # 上昇後の横ばい期間
            if (
                data["Close"].iloc[i] > data["Close"].iloc[i - 15]
                and abs(data["Close"].iloc[i] - data["Close"].iloc[i - 5]) < 1.0
            ):
                flag_patterns += 1

        return {
            "pattern_name": "フラッグパターン",
            "realistic_count": flag_patterns,
            "monthly_frequency": (flag_patterns / (total_days / 30)),
            "description": "上昇後の横ばい期間",
        }

    def _analyze_three_buddhas(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """三尊天井/逆三尊パターンの現実的分析"""
        # 簡易的な三尊パターン検出
        three_buddhas = 0
        for i in range(40, len(data)):
            # 40日間で3つの高値
            high_values = data["High"].iloc[i - 40 : i + 1]
            peaks = self._find_peaks(high_values)
            if len(peaks) >= 3:
                three_buddhas += 1

        return {
            "pattern_name": "三尊天井/逆三尊",
            "realistic_count": three_buddhas,
            "monthly_frequency": (three_buddhas / (total_days / 30)),
            "description": "40日間で3つの高値形成",
        }

    def _analyze_wedge_patterns(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """ウェッジパターンの現実的分析"""
        # 簡易的なウェッジパターン検出
        wedge_patterns = 0
        for i in range(20, len(data)):
            # 20日間の収束パターン
            high_values = data["High"].iloc[i - 20 : i + 1]
            low_values = data["Low"].iloc[i - 20 : i + 1]

            # 高値と安値の収束チェック
            if (
                max(high_values) - min(high_values) < 2.0
                and max(low_values) - min(low_values) < 2.0
            ):
                wedge_patterns += 1

        return {
            "pattern_name": "ウェッジパターン",
            "realistic_count": wedge_patterns,
            "monthly_frequency": (wedge_patterns / (total_days / 30)),
            "description": "20日間の収束パターン",
        }

    def _analyze_support_resistance(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """レジスタンス/サポートパターンの現実的分析"""
        # 簡易的なサポート/レジスタンス検出
        support_resistance = 0
        for i in range(30, len(data)):
            # 30日間で同じ価格レベルでの反発
            price_level = data["Close"].iloc[i]
            recent_highs = data["High"].iloc[i - 30 : i + 1]
            recent_lows = data["Low"].iloc[i - 30 : i + 1]

            # 価格レベルのタッチ回数
            touches = sum(1 for high in recent_highs if abs(high - price_level) < 0.5)
            touches += sum(1 for low in recent_lows if abs(low - price_level) < 0.5)

            if touches >= 3:
                support_resistance += 1

        return {
            "pattern_name": "レジスタンス/サポート",
            "realistic_count": support_resistance,
            "monthly_frequency": (support_resistance / (total_days / 30)),
            "description": "30日間で3回以上の価格レベルタッチ",
        }

    def _analyze_roll_reversals(
        self, data: pd.DataFrame, total_days: int
    ) -> Dict[str, Any]:
        """ロールリバーサルパターンの現実的分析"""
        # 簡易的なロールリバーサル検出
        roll_reversals = 0
        for i in range(10, len(data)):
            # 10日間の方向転換
            recent_trend = data["Close"].iloc[i] - data["Close"].iloc[i - 10]
            short_trend = data["Close"].iloc[i] - data["Close"].iloc[i - 5]

            # 長期トレンドと短期トレンドの逆転
            if (recent_trend > 0 and short_trend < 0) or (
                recent_trend < 0 and short_trend > 0
            ):
                roll_reversals += 1

        return {
            "pattern_name": "ロールリバーサル",
            "realistic_count": roll_reversals,
            "monthly_frequency": (roll_reversals / (total_days / 30)),
            "description": "10日間の方向転換",
        }

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """RSI計算"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _find_peaks(self, values: pd.Series) -> List[int]:
        """ピーク検出"""
        peaks = []
        for i in range(1, len(values) - 1):
            if (
                values.iloc[i] > values.iloc[i - 1]
                and values.iloc[i] > values.iloc[i + 1]
            ):
                peaks.append(i)
        return peaks

    def _display_realistic_results(
        self, frequency_results: Dict[str, Any], market_data: pd.DataFrame
    ):
        """現実的な分析結果の表示"""
        print("\n" + "=" * 80)
        print("📊 現実的パターン発生頻度分析結果")
        print("=" * 80)

        total_days = (market_data["Date"].max() - market_data["Date"].min()).days

        # 検出回数でソート
        sorted_patterns = sorted(
            frequency_results.items(),
            key=lambda x: x[1]["realistic_count"],
            reverse=True,
        )

        print(f"\n🎯 パターン別現実的発生頻度（降順）:")
        print(f"{'順位':<4} {'パターン':<6} {'パターン名':<20} {'発生回数':<8} {'月平均':<8} {'説明':<30}")
        print("-" * 80)

        for rank, (pattern_num, result) in enumerate(sorted_patterns, 1):
            realistic_count = result["realistic_count"]
            pattern_name = result["pattern_name"]
            monthly_freq = result["monthly_frequency"]
            description = result["description"]

            print(
                f"{rank:<4} {pattern_num:<6} {pattern_name:<20} {realistic_count:<8} {monthly_freq:<8.2f} {description:<30}"
            )

        print("\n" + "=" * 80)

        # 頻度分類
        high_freq = [
            (num, result)
            for num, result in sorted_patterns
            if result["monthly_frequency"] >= 5
        ]
        medium_freq = [
            (num, result)
            for num, result in sorted_patterns
            if 1 <= result["monthly_frequency"] < 5
        ]
        low_freq = [
            (num, result)
            for num, result in sorted_patterns
            if result["monthly_frequency"] < 1
        ]

        print(f"\n📈 頻度分類:")

        if high_freq:
            print(f"\n🔥 高頻度パターン（月5回以上）:")
            for pattern_num, result in high_freq:
                print(
                    f"   パターン{pattern_num}: {result['pattern_name']} - {result['monthly_frequency']:.1f}回/月"
                )

        if medium_freq:
            print(f"\n⚡ 中頻度パターン（月1-5回）:")
            for pattern_num, result in medium_freq:
                print(
                    f"   パターン{pattern_num}: {result['pattern_name']} - {result['monthly_frequency']:.1f}回/月"
                )

        if low_freq:
            print(f"\n🐌 低頻度パターン（月1回未満）:")
            for pattern_num, result in low_freq:
                print(
                    f"   パターン{pattern_num}: {result['pattern_name']} - {result['monthly_frequency']:.1f}回/月"
                )

        print("\n" + "=" * 80)

        # 基準調整の推奨事項
        print(f"\n💡 基準調整の推奨事項:")
        print(f"   📊 分析期間: {total_days}日間")
        print(f"   📈 総ローソク足数: {len(market_data)}件")

        if high_freq:
            print(f"   ✅ 高頻度パターン: 現在の基準を維持または厳格化")

        if medium_freq:
            print(f"   ⚠️ 中頻度パターン: 基準を適度に調整")

        if low_freq:
            print(f"   🔧 低頻度パターン: 基準を大幅に緩和")

        print(f"\n📋 次のステップ:")
        print(f"   1. 低頻度パターンの基準大幅緩和")
        print(f"   2. 中頻度パターンの基準微調整")
        print(f"   3. 高頻度パターンの精度向上")


async def main():
    """メイン関数"""
    analyzer = RealisticPatternFrequencyAnalyzer()
    await analyzer.analyze_realistic_frequency()


if __name__ == "__main__":
    asyncio.run(main())
