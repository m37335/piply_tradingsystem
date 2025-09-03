"""
パフォーマンス最適化

キャッシュ機能と並列処理によるパフォーマンス最適化
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import pandas as pd

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.notification_pattern_analyzer import (
    NotificationPatternAnalyzer,
)
from src.utils.pattern_utils import PatternUtils


class PerformanceOptimizer:
    """パフォーマンス最適化クラス"""

    def __init__(self):
        self.analyzer = NotificationPatternAnalyzer()
        self.utils = PatternUtils()

        # キャッシュ設定
        self.cache_file = "performance_cache.json"
        self.cache_duration = 300  # 5分間キャッシュ
        self.max_cache_size = 1000  # 最大キャッシュサイズ

        # キャッシュデータ
        self.data_cache = {}
        self.analysis_cache = {}

        # パフォーマンス統計
        self.performance_stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "average_response_time": 0.0,
        }

        # ログ設定
        self.setup_logging()

        # キャッシュを読み込み
        self.load_cache()

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def load_cache(self):
        """キャッシュを読み込み"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    self.data_cache = cache_data.get("data_cache", {})
                    self.analysis_cache = cache_data.get("analysis_cache", {})
                    self.performance_stats = cache_data.get(
                        "performance_stats", self.performance_stats
                    )
            except Exception as e:
                self.logger.error(f"キャッシュ読み込みエラー: {e}")

    def save_cache(self):
        """キャッシュを保存"""
        try:
            cache_data = {
                "data_cache": self.data_cache,
                "analysis_cache": self.analysis_cache,
                "performance_stats": self.performance_stats,
                "last_saved": datetime.now().isoformat(),
            }
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"キャッシュ保存エラー: {e}")

    def get_cache_key(self, currency_pair: str, timeframe: str) -> str:
        """キャッシュキーを生成"""
        return f"{currency_pair}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M')}"

    def is_cache_valid(self, cache_key: str) -> bool:
        """キャッシュが有効かチェック"""
        if cache_key not in self.data_cache:
            return False

        cache_time = self.data_cache[cache_key].get("timestamp")
        if not cache_time:
            return False

        cache_datetime = datetime.fromisoformat(cache_time)
        time_diff = (datetime.now() - cache_datetime).total_seconds()

        return time_diff < self.cache_duration

    def get_cached_data(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """キャッシュされたデータを取得"""
        if self.is_cache_valid(cache_key):
            self.performance_stats["cache_hits"] += 1
            return self.data_cache[cache_key].get("data")
        else:
            self.performance_stats["cache_misses"] += 1
            return None

    def set_cached_data(self, cache_key: str, data: Dict[str, Any]):
        """データをキャッシュに保存"""
        self.data_cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
        }

        # キャッシュサイズを制限
        if len(self.data_cache) > self.max_cache_size:
            self.cleanup_cache()

    def cleanup_cache(self):
        """古いキャッシュを削除"""
        current_time = datetime.now()
        keys_to_remove = []

        for key, cache_data in self.data_cache.items():
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            if (current_time - cache_time).total_seconds() > self.cache_duration:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.data_cache[key]

        self.logger.info(f"キャッシュクリーンアップ: {len(keys_to_remove)}件削除")

    async def get_optimized_data(
        self, currency_pair: str, timeframe: str
    ) -> Dict[str, Any]:
        """
        最適化されたデータ取得

        Args:
            currency_pair: 通貨ペア
            timeframe: 時間軸

        Returns:
            最適化されたデータ
        """
        start_time = time.time()
        self.performance_stats["total_requests"] += 1

        cache_key = self.get_cache_key(currency_pair, timeframe)
        cached_data = self.get_cached_data(cache_key)

        if cached_data:
            self.logger.info(f"キャッシュヒット: {cache_key}")
            return cached_data

        # データを取得
        data = await self.fetch_data(currency_pair, timeframe)

        # キャッシュに保存
        self.set_cached_data(cache_key, data)

        # レスポンス時間を記録
        response_time = time.time() - start_time
        self.update_average_response_time(response_time)

        return data

    async def fetch_data(self, currency_pair: str, timeframe: str) -> Dict[str, Any]:
        """
        データを取得

        Args:
            currency_pair: 通貨ペア
            timeframe: 時間軸

        Returns:
            取得したデータ
        """
        # 実際の実装では、ここでリアルタイムデータを取得
        # 現在はモックデータを使用
        return self.create_mock_data(currency_pair, timeframe)

    def create_mock_data(self, currency_pair: str, timeframe: str) -> Dict[str, Any]:
        """モックデータを作成"""
        dates = pd.date_range(start="2025-01-01", periods=50, freq="1H")
        prices = pd.Series(
            [100 + i * 0.1 + (i % 10) * 0.05 for i in range(50)], index=dates
        )

        rsi = self.utils.calculate_rsi(prices)
        macd = self.utils.calculate_macd(prices)
        bb = self.utils.calculate_bollinger_bands(prices)

        return {
            "price_data": pd.DataFrame(
                {
                    "Open": prices * 0.999,
                    "High": prices * 1.002,
                    "Low": prices * 0.998,
                    "Close": prices,
                    "Volume": [1000000] * 50,
                },
                index=dates,
            ),
            "indicators": {
                "rsi": {"current_value": rsi.iloc[-1], "series": rsi},
                "macd": macd,
                "bollinger_bands": bb,
            },
            "metadata": {
                "currency_pair": currency_pair,
                "timeframe": timeframe,
                "fetched_at": datetime.now().isoformat(),
            },
        }

    def update_average_response_time(self, response_time: float):
        """平均レスポンス時間を更新"""
        total_requests = self.performance_stats["total_requests"]
        current_avg = self.performance_stats["average_response_time"]

        if total_requests == 1:
            self.performance_stats["average_response_time"] = response_time
        else:
            new_avg = (
                current_avg * (total_requests - 1) + response_time
            ) / total_requests
            self.performance_stats["average_response_time"] = new_avg

    async def analyze_multiple_currency_pairs(
        self, currency_pairs: list, timeframes: list
    ) -> Dict[str, Any]:
        """
        複数の通貨ペアを並列分析

        Args:
            currency_pairs: 通貨ペアのリスト
            timeframes: 時間軸のリスト

        Returns:
            分析結果
        """
        start_time = time.time()

        # 並列タスクを作成
        tasks = []
        for currency_pair in currency_pairs:
            for timeframe in timeframes:
                task = self.analyze_single_pair_timeframe(currency_pair, timeframe)
                tasks.append(task)

        # 並列実行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 結果を整理
        analysis_results = {}
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"分析エラー: {result}")
                continue

            currency_pair = currency_pairs[i // len(timeframes)]
            timeframe = timeframes[i % len(timeframes)]

            if currency_pair not in analysis_results:
                analysis_results[currency_pair] = {}

            analysis_results[currency_pair][timeframe] = result

        total_time = time.time() - start_time
        self.logger.info(
            f"並列分析完了: {len(currency_pairs)}通貨ペア x {len(timeframes)}時間軸 = {total_time:.2f}秒"
        )

        return analysis_results

    async def analyze_single_pair_timeframe(
        self, currency_pair: str, timeframe: str
    ) -> Dict[str, Any]:
        """
        単一の通貨ペア・時間軸を分析

        Args:
            currency_pair: 通貨ペア
            timeframe: 時間軸

        Returns:
            分析結果
        """
        try:
            # 最適化されたデータ取得
            data = await self.get_optimized_data(currency_pair, timeframe)

            # 分析実行
            analysis_result = self.analyzer.analyze_multi_timeframe_data(
                {timeframe: data}, currency_pair
            )

            return {
                "currency_pair": currency_pair,
                "timeframe": timeframe,
                "analysis_result": analysis_result,
                "data_timestamp": data["metadata"]["fetched_at"],
            }

        except Exception as e:
            self.logger.error(f"分析エラー {currency_pair} {timeframe}: {e}")
            return {"error": str(e)}

    def get_performance_stats(self) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        cache_hit_rate = 0.0
        if self.performance_stats["total_requests"] > 0:
            cache_hit_rate = (
                self.performance_stats["cache_hits"]
                / self.performance_stats["total_requests"]
                * 100
            )

        return {
            **self.performance_stats,
            "cache_hit_rate_percent": cache_hit_rate,
            "cache_size": len(self.data_cache),
            "analysis_cache_size": len(self.analysis_cache),
            "last_updated": datetime.now().isoformat(),
        }

    def optimize_memory_usage(self):
        """メモリ使用量を最適化"""
        # キャッシュクリーンアップ
        self.cleanup_cache()

        # 分析キャッシュもクリーンアップ
        current_time = datetime.now()
        keys_to_remove = []

        for key, cache_data in self.analysis_cache.items():
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            if (current_time - cache_time).total_seconds() > self.cache_duration:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.analysis_cache[key]

        self.logger.info(f"メモリ最適化完了: {len(keys_to_remove)}件削除")

    def __del__(self):
        """デストラクタ: キャッシュを保存"""
        self.save_cache()


# パフォーマンステスト用の関数
async def test_performance():
    """パフォーマンステスト"""
    optimizer = PerformanceOptimizer()

    # 単一データ取得テスト
    print("=== 単一データ取得テスト ===")
    data = await optimizer.get_optimized_data("USD/JPY", "D1")
    print(f"データ取得: {len(data)}個のフィールド")

    # 並列分析テスト
    print("\n=== 並列分析テスト ===")
    currency_pairs = ["USD/JPY", "EUR/USD", "GBP/USD"]
    timeframes = ["D1", "H4", "H1"]

    results = await optimizer.analyze_multiple_currency_pairs(
        currency_pairs, timeframes
    )
    print(f"並列分析結果: {len(results)}通貨ペア")

    # パフォーマンス統計
    print("\n=== パフォーマンス統計 ===")
    stats = optimizer.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # メモリ最適化
    print("\n=== メモリ最適化 ===")
    optimizer.optimize_memory_usage()


if __name__ == "__main__":
    asyncio.run(test_performance())
