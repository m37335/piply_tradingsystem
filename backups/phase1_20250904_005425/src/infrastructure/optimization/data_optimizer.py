"""
Data Optimizer System
データ取得最適化システム

設計書参照:
- api_optimization_design_2025.md

データ取得の最適化と効率化
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

import pandas as pd

from ...infrastructure.cache.cache_manager import CacheManager
from ...infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient
from ...utils.logging_config import get_infrastructure_logger
from ...utils.optimization_utils import measure_performance
from .api_rate_limiter import ApiRateLimiter
from .batch_processor import BatchProcessor

logger = get_infrastructure_logger()


class DataOptimizer:
    """
    データ取得最適化システム

    責任:
    - 一括データ取得
    - キャッシュ統合
    - 効率的な履歴データ取得
    - API制限対応
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        api_rate_limiter: ApiRateLimiter,
        batch_processor: BatchProcessor,
        yahoo_finance_client: YahooFinanceClient,
        default_cache_ttl_minutes: int = 60,
        max_historical_days: int = 30,
        enable_smart_caching: bool = True,
    ):
        """
        初期化

        Args:
            cache_manager: キャッシュ管理システム
            api_rate_limiter: API制限管理システム
            batch_processor: バッチ処理システム
            yahoo_finance_client: Yahoo Financeクライアント
            default_cache_ttl_minutes: デフォルトキャッシュTTL（分）
            max_historical_days: 最大履歴日数
            enable_smart_caching: スマートキャッシュを有効にするか
        """
        self.cache_manager = cache_manager
        self.api_rate_limiter = api_rate_limiter
        self.batch_processor = batch_processor
        self.yahoo_finance_client = yahoo_finance_client
        self.default_cache_ttl_minutes = default_cache_ttl_minutes
        self.max_historical_days = max_historical_days
        self.enable_smart_caching = enable_smart_caching

        # 統計情報
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.total_optimization_time = 0.0

        logger.info(
            f"DataOptimizer initialized: "
            f"cache_ttl={default_cache_ttl_minutes}min, "
            f"max_historical_days={max_historical_days}, "
            f"smart_caching={enable_smart_caching}"
        )

    def _generate_cache_key(
        self,
        data_type: str,
        currency_pair: str,
        timeframe: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        キャッシュキーを生成

        Args:
            data_type: データタイプ
            currency_pair: 通貨ペア
            timeframe: 時間軸
            **kwargs: その他のパラメータ

        Returns:
            str: キャッシュキー
        """
        components = {
            "data_type": data_type,
            "currency_pair": currency_pair,
            "timeframe": timeframe,
            **kwargs,
        }
        return f"data_{hash(str(sorted(components.items())))}"

    async def get_exchange_rate_data(
        self,
        currency_pair: str,
        use_cache: bool = True,
        cache_ttl_minutes: Optional[int] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        為替レートデータを取得（最適化版）

        Args:
            currency_pair: 通貨ペア
            use_cache: キャッシュを使用するか
            cache_ttl_minutes: キャッシュTTL（分）

        Returns:
            Optional[Dict[str, Any]]: 為替レートデータ
        """
        start_time, _ = measure_performance()

        try:
            # キャッシュから取得を試行
            if use_cache:
                cache_key = self._generate_cache_key("exchange_rate", currency_pair)
                cached_data = await self.cache_manager.get(
                    "data", {"cache_key": cache_key}
                )
                if cached_data:
                    self.cache_hits += 1
                    logger.debug(f"Cache hit for exchange rate: {currency_pair}")
                    return cached_data

            # APIから取得
            self.cache_misses += 1
            self.api_calls += 1

            data = await self.api_rate_limiter.execute_with_retry(
                "yahoo_finance",
                self.yahoo_finance_client.get_exchange_rate,
                currency_pair,
            )

            # キャッシュに保存
            if use_cache and data:
                ttl_seconds = (
                    cache_ttl_minutes * 60
                    if cache_ttl_minutes
                    else self.default_cache_ttl_minutes * 60
                )
                await self.cache_manager.set(
                    "data",
                    {"cache_key": cache_key},
                    data,
                    ttl_seconds=ttl_seconds,
                )

            return data

        except Exception as e:
            logger.error(
                f"Failed to get exchange rate data for {currency_pair}: {str(e)}"
            )
            return None

        finally:
            execution_time, _ = measure_performance()
            self.total_optimization_time += execution_time

    async def get_historical_data(
        self,
        currency_pair: str,
        days: int = 30,
        use_cache: bool = True,
        cache_ttl_minutes: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        履歴データを取得（最適化版）

        Args:
            currency_pair: 通貨ペア
            days: 取得日数
            use_cache: キャッシュを使用するか
            cache_ttl_minutes: キャッシュTTL（分）

        Returns:
            Optional[List[Dict[str, Any]]]: 履歴データ
        """
        start_time = time.time()

        try:
            # 日数制限を適用
            days = min(days, self.max_historical_days)

            # キャッシュから取得を試行
            if use_cache:
                cache_key = self._generate_cache_key(
                    "historical", currency_pair, days=days
                )
                cached_data = await self.cache_manager.get(
                    "data", {"cache_key": cache_key}
                )
                if cached_data:
                    self.cache_hits += 1
                    logger.debug(
                        f"Cache hit for historical data: {currency_pair} ({days} days)"
                    )
                    return cached_data

            # APIから取得
            self.cache_misses += 1
            self.api_calls += 1

            data = await self.api_rate_limiter.execute_with_retry(
                "yahoo_finance",
                self.yahoo_finance_client.get_historical_data,
                currency_pair,
                days,
            )

            # キャッシュに保存
            if use_cache and data:
                ttl_seconds = (
                    cache_ttl_minutes * 60
                    if cache_ttl_minutes
                    else self.default_cache_ttl_minutes * 60
                )
                await self.cache_manager.set(
                    "data",
                    {"cache_key": cache_key},
                    data,
                    ttl_seconds=ttl_seconds,
                )

            return data

        except Exception as e:
            logger.error(f"Failed to get historical data for {currency_pair}: {str(e)}")
            return None

        finally:
            execution_time = time.time() - start_time
            self.total_optimization_time += execution_time

    async def get_historical_dataframe(
        self,
        currency_pair: str,
        period: str = "1mo",
        interval: str = "1d",
        use_cache: bool = True,
        cache_ttl_minutes: Optional[int] = None,
    ) -> Optional[pd.DataFrame]:
        """
        履歴データをpandas DataFrameで取得（テクニカル指標用）

        Args:
            currency_pair: 通貨ペア
            period: 期間（1mo, 3mo, 1wk等）
            interval: 間隔（1d, 1h等）
            use_cache: キャッシュを使用するか
            cache_ttl_minutes: キャッシュTTL（分）

        Returns:
            Optional[pd.DataFrame]: 履歴データのDataFrame
        """
        start_time = time.time()

        try:
            # キャッシュから取得を試行
            if use_cache:
                cache_key = self._generate_cache_key(
                    "historical_dataframe",
                    currency_pair,
                    timeframe=f"{period}_{interval}",
                )
                cached_data = await self.cache_manager.get(
                    "data", {"cache_key": cache_key}
                )
                if cached_data:
                    self.cache_hits += 1
                    logger.debug(
                        f"Cache hit for historical dataframe: {currency_pair} ({period}, {interval})"
                    )
                    return pd.DataFrame(cached_data)

            # APIから取得
            self.cache_misses += 1
            self.api_calls += 1

            data = await self.api_rate_limiter.execute_with_retry(
                "yahoo_finance",
                self.yahoo_finance_client.get_historical_data,
                currency_pair,
                period,
                interval,
            )

            # キャッシュに保存
            if use_cache and data is not None and not data.empty:
                ttl_seconds = (
                    cache_ttl_minutes * 60
                    if cache_ttl_minutes
                    else self.default_cache_ttl_minutes * 60
                )
                await self.cache_manager.set(
                    "data",
                    {"cache_key": cache_key},
                    data.to_dict("records"),
                    ttl_seconds=ttl_seconds,
                )

            return data

        except Exception as e:
            logger.error(
                f"Failed to get historical dataframe for {currency_pair}: {str(e)}"
            )
            return None

        finally:
            execution_time = time.time() - start_time
            self.total_optimization_time += execution_time

    async def get_multiple_currency_data(
        self,
        currency_pairs: List[str],
        data_type: str = "exchange_rate",
        use_cache: bool = True,
        use_batch_processing: bool = True,
    ) -> Dict[str, Any]:
        """
        複数通貨ペアのデータを一括取得

        Args:
            currency_pairs: 通貨ペアリスト
            data_type: データタイプ（exchange_rate, historical）
            use_cache: キャッシュを使用するか
            use_batch_processing: バッチ処理を使用するか

        Returns:
            Dict[str, Any]: 通貨ペアごとのデータ
        """
        start_time, _ = measure_performance()

        try:
            results = {}

            if use_batch_processing and len(currency_pairs) > 1:
                # バッチ処理を使用
                results = await self._get_data_with_batch_processing(
                    currency_pairs, data_type, use_cache
                )
            else:
                # 個別処理
                for currency_pair in currency_pairs:
                    if data_type == "exchange_rate":
                        data = await self.get_exchange_rate_data(
                            currency_pair, use_cache
                        )
                    else:
                        data = await self.get_historical_data(
                            currency_pair, use_cache=use_cache
                        )
                    results[currency_pair] = data

            return results

        except Exception as e:
            logger.error(f"Failed to get multiple currency data: {str(e)}")
            return {}

        finally:
            execution_time, _ = measure_performance()
            self.total_optimization_time += execution_time

    async def _get_data_with_batch_processing(
        self,
        currency_pairs: List[str],
        data_type: str,
        use_cache: bool,
    ) -> Dict[str, Any]:
        """
        バッチ処理を使用してデータを取得

        Args:
            currency_pairs: 通貨ペアリスト
            data_type: データタイプ
            use_cache: キャッシュを使用するか

        Returns:
            Dict[str, Any]: 通貨ペアごとのデータ
        """
        # まずキャッシュから取得可能なデータを確認
        cached_results = {}
        uncached_pairs = []

        if use_cache:
            for currency_pair in currency_pairs:
                cache_key = self._generate_cache_key(data_type, currency_pair)
                cached_data = await self.cache_manager.get(
                    "data", {"cache_key": cache_key}
                )
                if cached_data:
                    cached_results[currency_pair] = cached_data
                    self.cache_hits += 1
                else:
                    uncached_pairs.append(currency_pair)
        else:
            uncached_pairs = currency_pairs

        # キャッシュにないデータをバッチ処理で取得
        if uncached_pairs:
            batch_requests = []
            for currency_pair in uncached_pairs:
                if data_type == "exchange_rate":
                    func = self.yahoo_finance_client.get_exchange_rate
                    args = (currency_pair,)
                else:
                    func = self.yahoo_finance_client.get_historical_data
                    args = (currency_pair, 30)  # デフォルト30日

                batch_requests.append((func, args, {}))

            # バッチ処理を実行
            batch_result = await self.batch_processor.process_batch(
                batch_requests, "yahoo_finance"
            )

            # 結果を処理
            successful_results = batch_result.get_successful_results()
            for request_id, result in successful_results:
                # リクエストIDから通貨ペアを特定
                request_index = int(request_id.split("_")[-1])
                if request_index < len(uncached_pairs):
                    currency_pair = uncached_pairs[request_index]
                    cached_results[currency_pair] = result

                    # キャッシュに保存
                    if use_cache:
                        cache_key = self._generate_cache_key(data_type, currency_pair)
                        ttl_seconds = self.default_cache_ttl_minutes * 60
                        await self.cache_manager.set(
                            "data",
                            {"cache_key": cache_key},
                            result,
                            ttl_seconds=ttl_seconds,
                        )

            self.api_calls += len(uncached_pairs)
            self.cache_misses += len(uncached_pairs)

        return cached_results

    async def optimize_data_retrieval(
        self,
        currency_pairs: List[str],
        data_types: List[str],
        use_cache: bool = True,
        use_batch_processing: bool = True,
    ) -> Dict[str, Dict[str, Any]]:
        """
        データ取得を最適化

        Args:
            currency_pairs: 通貨ペアリスト
            data_types: データタイプリスト
            use_cache: キャッシュを使用するか
            use_batch_processing: バッチ処理を使用するか

        Returns:
            Dict[str, Dict[str, Any]]: 最適化されたデータ
        """
        start_time, _ = measure_performance()

        try:
            optimized_data = {}

            # 各データタイプに対して最適化された取得を実行
            for data_type in data_types:
                if data_type == "exchange_rate":
                    data = await self.get_multiple_currency_data(
                        currency_pairs, "exchange_rate", use_cache, use_batch_processing
                    )
                elif data_type == "historical":
                    data = await self.get_multiple_currency_data(
                        currency_pairs, "historical", use_cache, use_batch_processing
                    )
                else:
                    logger.warning(f"Unknown data type: {data_type}")
                    continue

                optimized_data[data_type] = data

            return optimized_data

        except Exception as e:
            logger.error(f"Failed to optimize data retrieval: {str(e)}")
            return {}

        finally:
            execution_time, _ = measure_performance()
            self.total_optimization_time += execution_time

    async def preload_cache(
        self,
        currency_pairs: List[str],
        data_types: List[str],
        background: bool = True,
    ) -> None:
        """
        キャッシュを事前読み込み

        Args:
            currency_pairs: 通貨ペアリスト
            data_types: データタイプリスト
            background: バックグラウンドで実行するか

        Returns:
            None
        """

        async def _preload():
            try:
                logger.info(
                    f"Starting cache preload for {len(currency_pairs)} pairs, "
                    f"{len(data_types)} data types"
                )

                await self.optimize_data_retrieval(
                    currency_pairs,
                    data_types,
                    use_cache=True,
                    use_batch_processing=True,
                )

                logger.info("Cache preload completed")

            except Exception as e:
                logger.error(f"Cache preload failed: {str(e)}")

        if background:
            # バックグラウンドで実行
            asyncio.create_task(_preload())
        else:
            # 同期的に実行
            await _preload()

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """
        最適化統計を取得

        Returns:
            Dict[str, Any]: 最適化統計
        """
        total_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        )

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": cache_hit_rate,
            "api_calls": self.api_calls,
            "total_optimization_time": self.total_optimization_time,
            "avg_optimization_time": (
                self.total_optimization_time / total_requests
                if total_requests > 0
                else 0
            ),
            "default_cache_ttl_minutes": self.default_cache_ttl_minutes,
            "max_historical_days": self.max_historical_days,
            "smart_caching_enabled": self.enable_smart_caching,
        }

    async def clear_optimization_cache(
        self, currency_pairs: Optional[List[str]] = None
    ) -> int:
        """
        最適化キャッシュをクリア

        Args:
            currency_pairs: 通貨ペアリスト（Noneの場合は全て）

        Returns:
            int: 削除されたキャッシュ数
        """
        try:
            if currency_pairs:
                # 特定の通貨ペアのキャッシュを削除
                deleted_count = 0
                for currency_pair in currency_pairs:
                    cache_key = self._generate_cache_key("data", currency_pair)
                    if await self.cache_manager.delete(
                        "data", {"cache_key": cache_key}
                    ):
                        deleted_count += 1
                return deleted_count
            else:
                # 全キャッシュを削除
                result = await self.cache_manager.clear_all()
                return result.get("total", 0)

        except Exception as e:
            logger.error(f"Failed to clear optimization cache: {str(e)}")
            return 0

    def reset_statistics(self) -> None:
        """
        統計情報をリセット

        Returns:
            None
        """
        self.cache_hits = 0
        self.cache_misses = 0
        self.api_calls = 0
        self.total_optimization_time = 0.0
        logger.info("DataOptimizer statistics reset")
