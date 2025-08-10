"""
Optimization Utilities
最適化ユーティリティ

設計書参照:
- api_optimization_design_2025.md

最適化システム用のユーティリティ関数
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, TypeVar

from .logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()

T = TypeVar("T")


async def batch_process_requests(
    requests: List[Dict[str, Any]],
    processor_func: Callable[[Dict[str, Any]], Any],
    max_concurrent: int = 5,
    delay_ms: int = 100,
) -> List[Any]:
    """
    リクエストをバッチ処理

    Args:
        requests: 処理するリクエストのリスト
        processor_func: 各リクエストを処理する関数
        max_concurrent: 最大同時実行数
        delay_ms: リクエスト間の遅延（ミリ秒）

    Returns:
        List[Any]: 処理結果のリスト
    """
    try:
        semaphore = asyncio.Semaphore(max_concurrent)
        results = []

        async def process_single_request(request: Dict[str, Any]) -> Any:
            async with semaphore:
                try:
                    result = await processor_func(request)
                    await asyncio.sleep(delay_ms / 1000)  # ミリ秒を秒に変換
                    return result
                except Exception as e:
                    logger.error(f"Failed to process request: {str(e)}")
                    return None

        # 並列処理
        tasks = [process_single_request(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # エラーを除外
        valid_results = [
            r for r in results if r is not None and not isinstance(r, Exception)
        ]

        logger.debug(
            f"Batch processing completed: {len(valid_results)}/{len(requests)} "
            f"successful"
        )
        return valid_results

    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        return []


def calculate_rate_limit(
    calls_per_minute: int,
    calls_per_hour: int,
    current_calls_minute: int,
    current_calls_hour: int,
) -> Dict[str, Any]:
    """
    レート制限を計算

    Args:
        calls_per_minute: 1分あたりの制限
        calls_per_hour: 1時間あたりの制限
        current_calls_minute: 現在の1分間の呼び出し数
        current_calls_hour: 現在の1時間の呼び出し数

    Returns:
        Dict[str, Any]: レート制限情報
    """
    try:
        minute_remaining = max(0, calls_per_minute - current_calls_minute)
        hour_remaining = max(0, calls_per_hour - current_calls_hour)

        minute_usage_rate = (current_calls_minute / calls_per_minute) * 100
        hour_usage_rate = (current_calls_hour / calls_per_hour) * 100

        # 制限に近づいているかどうか
        is_near_limit = minute_usage_rate > 80 or hour_usage_rate > 80
        is_at_limit = minute_usage_rate >= 100 or hour_usage_rate >= 100

        rate_limit_info = {
            "minute_remaining": minute_remaining,
            "hour_remaining": hour_remaining,
            "minute_usage_rate": minute_usage_rate,
            "hour_usage_rate": hour_usage_rate,
            "is_near_limit": is_near_limit,
            "is_at_limit": is_at_limit,
            "can_make_request": not is_at_limit,
        }

        logger.debug(f"Rate limit calculation: {rate_limit_info}")
        return rate_limit_info

    except Exception as e:
        logger.error(f"Failed to calculate rate limit: {str(e)}")
        return {
            "minute_remaining": 0,
            "hour_remaining": 0,
            "minute_usage_rate": 100,
            "hour_usage_rate": 100,
            "is_near_limit": True,
            "is_at_limit": True,
            "can_make_request": False,
        }


def measure_performance(
    func: Callable[..., T],
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    関数のパフォーマンスを測定

    Args:
        func: 測定する関数
        *args: 関数の引数
        **kwargs: 関数のキーワード引数

    Returns:
        Dict[str, Any]: パフォーマンス測定結果
    """
    try:
        start_time = time.time()
        start_memory = get_memory_usage()

        # 関数実行
        func(*args, **kwargs)

        end_time = time.time()
        end_memory = get_memory_usage()

        execution_time = end_time - start_time
        memory_used = end_memory - start_memory

        performance_data = {
            "execution_time_ms": execution_time * 1000,
            "memory_used_mb": memory_used,
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

        logger.debug(f"Performance measurement: {performance_data}")
        return performance_data

    except Exception as e:
        logger.error(f"Performance measurement failed: {str(e)}")
        return {
            "execution_time_ms": 0,
            "memory_used_mb": 0,
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


def get_memory_usage() -> float:
    """
    メモリ使用量を取得（MB）

    Returns:
        float: メモリ使用量（MB）
    """
    try:
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()
        return memory_info.rss / 1024 / 1024  # バイトをMBに変換
    except ImportError:
        logger.warning("psutil not available, using fallback memory measurement")
        return 0.0
    except Exception as e:
        logger.error(f"Failed to get memory usage: {str(e)}")
        return 0.0


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0,
) -> float:
    """
    指数バックオフの遅延時間を計算

    Args:
        attempt: 試行回数
        base_delay: 基本遅延時間（秒）
        max_delay: 最大遅延時間（秒）
        multiplier: 乗数

    Returns:
        float: 遅延時間（秒）
    """
    try:
        delay = base_delay * (multiplier ** (attempt - 1))
        delay = min(delay, max_delay)

        logger.debug(f"Calculated backoff delay: {delay}s (attempt: {attempt})")
        return delay

    except Exception as e:
        logger.error(f"Failed to calculate backoff delay: {str(e)}")
        return base_delay


def optimize_batch_size(
    total_items: int,
    max_concurrent: int = 5,
    target_duration_seconds: int = 30,
) -> int:
    """
    最適なバッチサイズを計算

    Args:
        total_items: 総アイテム数
        max_concurrent: 最大同時実行数
        target_duration_seconds: 目標実行時間（秒）

    Returns:
        int: 最適なバッチサイズ
    """
    try:
        # 基本的な計算
        estimated_time_per_item = 1.0  # 秒（推定値）
        total_estimated_time = total_items * estimated_time_per_item
        optimal_batch_size = max(1, total_items // max_concurrent)

        # 目標時間に基づく調整
        if total_estimated_time > target_duration_seconds:
            optimal_batch_size = max(
                1, int(total_items * target_duration_seconds / total_estimated_time)
            )

        logger.debug(
            f"Optimized batch size: {optimal_batch_size} "
            f"(total: {total_items}, concurrent: {max_concurrent})"
        )
        return optimal_batch_size

    except Exception as e:
        logger.error(f"Failed to optimize batch size: {str(e)}")
        return max(1, total_items // max_concurrent)


def get_optimal_retry_count(
    error_type: str,
    base_retries: int = 3,
) -> int:
    """
    最適なリトライ回数を取得

    Args:
        error_type: エラータイプ
        base_retries: 基本リトライ回数

    Returns:
        int: 最適なリトライ回数
    """
    try:
        # エラータイプに基づく調整
        retry_multipliers = {
            "rate_limit": 2,  # レート制限は多めにリトライ
            "timeout": 1,  # タイムアウトは標準
            "network": 3,  # ネットワークエラーは多めにリトライ
            "server_error": 2,  # サーバーエラーは多めにリトライ
            "default": 1,
        }

        multiplier = retry_multipliers.get(error_type, retry_multipliers["default"])
        optimal_retries = base_retries * multiplier

        logger.debug(
            f"Optimal retry count: {optimal_retries} "
            f"(error_type: {error_type}, base: {base_retries})"
        )
        return optimal_retries

    except Exception as e:
        logger.error(f"Failed to get optimal retry count: {str(e)}")
        return base_retries


def validate_optimization_config(config: Dict[str, Any]) -> bool:
    """
    最適化設定の妥当性を検証

    Args:
        config: 検証する設定

    Returns:
        bool: 設定が妥当な場合True
    """
    try:
        required_fields = [
            "max_concurrent_requests",
            "request_delay_ms",
            "batch_size",
            "retry_count",
        ]

        for field in required_fields:
            if field not in config:
                logger.warning(f"Optimization config missing required field: {field}")
                return False

        # 値の範囲チェック
        if config["max_concurrent_requests"] <= 0:
            logger.warning("max_concurrent_requests must be positive")
            return False

        if config["request_delay_ms"] < 0:
            logger.warning("request_delay_ms must be non-negative")
            return False

        if config["batch_size"] <= 0:
            logger.warning("batch_size must be positive")
            return False

        if config["retry_count"] < 0:
            logger.warning("retry_count must be non-negative")
            return False

        logger.debug("Optimization config validation passed")
        return True

    except Exception as e:
        logger.error(f"Optimization config validation failed: {str(e)}")
        return False
