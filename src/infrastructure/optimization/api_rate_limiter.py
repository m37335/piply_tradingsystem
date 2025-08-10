"""
API Rate Limiter System
API制限管理システム

設計書参照:
- api_optimization_design_2025.md

API制限の管理と回避戦略
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from ...utils.logging_config import get_infrastructure_logger
from ...utils.optimization_utils import calculate_backoff_delay

logger = get_infrastructure_logger()


class RateLimitInfo:
    """
    レート制限情報

    責任:
    - API制限の詳細情報を管理
    - 制限状態の追跡
    """

    def __init__(
        self,
        calls_per_minute: int = 100,
        calls_per_hour: int = 1000,
        calls_per_day: int = 10000,
        backoff_multiplier: float = 2.0,
        max_retries: int = 5,
    ):
        """
        初期化

        Args:
            calls_per_minute: 1分あたりの最大呼び出し数
            calls_per_hour: 1時間あたりの最大呼び出し数
            calls_per_day: 1日あたりの最大呼び出し数
            backoff_multiplier: バックオフ倍率
            max_retries: 最大リトライ回数
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_hour = calls_per_hour
        self.calls_per_day = calls_per_day
        self.backoff_multiplier = backoff_multiplier
        self.max_retries = max_retries

        # 呼び出し履歴
        self.call_history: List[datetime] = []
        self.retry_count = 0
        self.last_rate_limit_error: Optional[datetime] = None
        self.current_backoff_seconds = 0

    def add_call(self) -> None:
        """
        呼び出しを記録

        Returns:
            None
        """
        now = datetime.utcnow()
        self.call_history.append(now)

        # 古い履歴を削除（24時間前より古いもの）
        cutoff_time = now - timedelta(hours=24)
        self.call_history = [
            call_time for call_time in self.call_history if call_time > cutoff_time
        ]

    def get_calls_in_period(self, period_minutes: int) -> int:
        """
        指定期間内の呼び出し数を取得

        Args:
            period_minutes: 期間（分）

        Returns:
            int: 呼び出し数
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=period_minutes)
        return len(
            [call_time for call_time in self.call_history if call_time > cutoff_time]
        )

    def is_rate_limited(self) -> bool:
        """
        レート制限されているかどうかを判定

        Returns:
            bool: レート制限されている場合True
        """
        now = datetime.utcnow()

        # 1分間の制限チェック
        calls_last_minute = self.get_calls_in_period(1)
        if calls_last_minute >= self.calls_per_minute:
            return True

        # 1時間の制限チェック
        calls_last_hour = self.get_calls_in_period(60)
        if calls_last_hour >= self.calls_per_hour:
            return True

        # 1日の制限チェック
        calls_last_day = self.get_calls_in_period(24 * 60)
        if calls_last_day >= self.calls_per_day:
            return True

        # バックオフ期間チェック
        if self.last_rate_limit_error and self.current_backoff_seconds > 0:
            backoff_until = self.last_rate_limit_error + timedelta(
                seconds=self.current_backoff_seconds
            )
            if now < backoff_until:
                return True

        return False

    def record_rate_limit_error(self) -> None:
        """
        レート制限エラーを記録

        Returns:
            None
        """
        self.last_rate_limit_error = datetime.utcnow()
        self.retry_count += 1

        # 指数バックオフを計算
        self.current_backoff_seconds = calculate_backoff_delay(
            self.retry_count,
            self.backoff_multiplier,
            max_delay_seconds=300,  # 最大5分
        )

        logger.warning(
            f"Rate limit error recorded: retry_count={self.retry_count}, "
            f"backoff_seconds={self.current_backoff_seconds}"
        )

    def reset_backoff(self) -> None:
        """
        バックオフをリセット

        Returns:
            None
        """
        self.retry_count = 0
        self.current_backoff_seconds = 0
        self.last_rate_limit_error = None

    def get_wait_time_seconds(self) -> float:
        """
        待機時間を取得（秒）

        Returns:
            float: 待機時間（秒）
        """
        if not self.is_rate_limited():
            return 0.0

        # バックオフ期間の残り時間
        if self.last_rate_limit_error and self.current_backoff_seconds > 0:
            backoff_until = self.last_rate_limit_error + timedelta(
                seconds=self.current_backoff_seconds
            )
            remaining = (backoff_until - datetime.utcnow()).total_seconds()
            if remaining > 0:
                return remaining

        # 制限の解除を待つ時間
        now = datetime.utcnow()

        # 1分間の制限
        calls_last_minute = self.get_calls_in_period(1)
        if calls_last_minute >= self.calls_per_minute:
            # 最も古い呼び出しから1分後まで待機
            oldest_call = min(self.call_history)
            wait_until = oldest_call + timedelta(minutes=1)
            return max(0, (wait_until - now).total_seconds())

        # 1時間の制限
        calls_last_hour = self.get_calls_in_period(60)
        if calls_last_hour >= self.calls_per_hour:
            # 最も古い呼び出しから1時間後まで待機
            oldest_call = min(self.call_history)
            wait_until = oldest_call + timedelta(hours=1)
            return max(0, (wait_until - now).total_seconds())

        return 0.0

    def get_statistics(self) -> Dict[str, any]:
        """
        統計情報を取得

        Returns:
            Dict[str, any]: 統計情報
        """
        return {
            "calls_per_minute": self.calls_per_minute,
            "calls_per_hour": self.calls_per_hour,
            "calls_per_day": self.calls_per_day,
            "calls_last_minute": self.get_calls_in_period(1),
            "calls_last_hour": self.get_calls_in_period(60),
            "calls_last_day": self.get_calls_in_period(24 * 60),
            "retry_count": self.retry_count,
            "current_backoff_seconds": self.current_backoff_seconds,
            "is_rate_limited": self.is_rate_limited(),
            "wait_time_seconds": self.get_wait_time_seconds(),
            "last_rate_limit_error": (
                self.last_rate_limit_error.isoformat()
                if self.last_rate_limit_error
                else None
            ),
        }


class ApiRateLimiter:
    """
    API制限管理システム

    責任:
    - 指数バックオフ
    - レート制限監視
    - 自動リトライ
    - 制限回避戦略
    """

    def __init__(self):
        """
        初期化
        """
        self.rate_limits: Dict[str, RateLimitInfo] = {}
        self.default_config = {
            "calls_per_minute": 100,
            "calls_per_hour": 1000,
            "calls_per_day": 10000,
            "backoff_multiplier": 2.0,
            "max_retries": 5,
        }

        logger.info("ApiRateLimiter initialized")

    def register_api(
        self,
        api_name: str,
        calls_per_minute: Optional[int] = None,
        calls_per_hour: Optional[int] = None,
        calls_per_day: Optional[int] = None,
        backoff_multiplier: Optional[float] = None,
        max_retries: Optional[int] = None,
    ) -> None:
        """
        APIを登録

        Args:
            api_name: API名
            calls_per_minute: 1分あたりの最大呼び出し数
            calls_per_hour: 1時間あたりの最大呼び出し数
            calls_per_day: 1日あたりの最大呼び出し数
            backoff_multiplier: バックオフ倍率
            max_retries: 最大リトライ回数

        Returns:
            None
        """
        config = self.default_config.copy()

        if calls_per_minute is not None:
            config["calls_per_minute"] = calls_per_minute
        if calls_per_hour is not None:
            config["calls_per_hour"] = calls_per_hour
        if calls_per_day is not None:
            config["calls_per_day"] = calls_per_day
        if backoff_multiplier is not None:
            config["backoff_multiplier"] = backoff_multiplier
        if max_retries is not None:
            config["max_retries"] = max_retries

        self.rate_limits[api_name] = RateLimitInfo(**config)

        logger.info(
            f"Registered API: {api_name}, "
            f"limits: {calls_per_minute}/{calls_per_hour}/{calls_per_day}"
        )

    def is_rate_limited(self, api_name: str) -> bool:
        """
        APIがレート制限されているかどうかを判定

        Args:
            api_name: API名

        Returns:
            bool: レート制限されている場合True
        """
        if api_name not in self.rate_limits:
            return False

        return self.rate_limits[api_name].is_rate_limited()

    def record_call(self, api_name: str) -> None:
        """
        API呼び出しを記録

        Args:
            api_name: API名

        Returns:
            None
        """
        if api_name not in self.rate_limits:
            # デフォルト設定で登録
            self.register_api(api_name)

        self.rate_limits[api_name].add_call()

    def record_rate_limit_error(self, api_name: str) -> None:
        """
        レート制限エラーを記録

        Args:
            api_name: API名

        Returns:
            None
        """
        if api_name not in self.rate_limits:
            # デフォルト設定で登録
            self.register_api(api_name)

        self.rate_limits[api_name].record_rate_limit_error()

    def get_wait_time(self, api_name: str) -> float:
        """
        待機時間を取得（秒）

        Args:
            api_name: API名

        Returns:
            float: 待機時間（秒）
        """
        if api_name not in self.rate_limits:
            return 0.0

        return self.rate_limits[api_name].get_wait_time_seconds()

    async def wait_if_needed(self, api_name: str) -> None:
        """
        必要に応じて待機

        Args:
            api_name: API名

        Returns:
            None
        """
        wait_time = self.get_wait_time(api_name)
        if wait_time > 0:
            logger.info(f"Waiting {wait_time:.2f}s for API {api_name}")
            await asyncio.sleep(wait_time)

    async def execute_with_retry(
        self,
        api_name: str,
        func,
        *args,
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> any:
        """
        リトライ付きで関数を実行

        Args:
            api_name: API名
            func: 実行する関数
            *args: 関数の引数
            max_retries: 最大リトライ回数
            **kwargs: 関数のキーワード引数

        Returns:
            any: 関数の戻り値
        """
        if api_name not in self.rate_limits:
            self.register_api(api_name)

        rate_limit_info = self.rate_limits[api_name]
        retry_count = 0
        max_retry_attempts = max_retries or rate_limit_info.max_retries

        while retry_count <= max_retry_attempts:
            try:
                # レート制限チェック
                if rate_limit_info.is_rate_limited():
                    wait_time = rate_limit_info.get_wait_time_seconds()
                    if wait_time > 0:
                        logger.info(
                            f"Rate limited for {api_name}, " f"waiting {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)

                # 呼び出しを記録
                rate_limit_info.add_call()

                # 関数を実行
                result = await func(*args, **kwargs)

                # 成功したらバックオフをリセット
                rate_limit_info.reset_backoff()
                return result

            except Exception as e:
                retry_count += 1
                error_message = str(e).lower()

                # レート制限エラーの場合
                if any(
                    keyword in error_message
                    for keyword in [
                        "rate limit",
                        "429",
                        "too many requests",
                        "quota exceeded",
                    ]
                ):
                    rate_limit_info.record_rate_limit_error()

                    if retry_count <= max_retry_attempts:
                        wait_time = rate_limit_info.get_wait_time_seconds()
                        logger.warning(
                            f"Rate limit error for {api_name}, "
                            f"retry {retry_count}/{max_retry_attempts}, "
                            f"waiting {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for {api_name}: {str(e)}")
                        raise

                # その他のエラーの場合
                else:
                    if retry_count <= max_retry_attempts:
                        # 指数バックオフで待機
                        backoff_delay = calculate_backoff_delay(
                            retry_count,
                            rate_limit_info.backoff_multiplier,
                            max_delay_seconds=60,
                        )
                        logger.warning(
                            f"Error for {api_name}, "
                            f"retry {retry_count}/{max_retry_attempts}, "
                            f"waiting {backoff_delay:.2f}s: {str(e)}"
                        )
                        await asyncio.sleep(backoff_delay)
                        continue
                    else:
                        logger.error(f"Max retries exceeded for {api_name}: {str(e)}")
                        raise

    def get_api_statistics(self, api_name: str) -> Optional[Dict[str, any]]:
        """
        API統計を取得

        Args:
            api_name: API名

        Returns:
            Optional[Dict[str, any]]: API統計
        """
        if api_name not in self.rate_limits:
            return None

        return self.rate_limits[api_name].get_statistics()

    def get_all_statistics(self) -> Dict[str, Dict[str, any]]:
        """
        全API統計を取得

        Returns:
            Dict[str, Dict[str, any]]: 全API統計
        """
        return {
            api_name: rate_limit.get_statistics()
            for api_name, rate_limit in self.rate_limits.items()
        }

    def reset_api(self, api_name: str) -> None:
        """
        APIの状態をリセット

        Args:
            api_name: API名

        Returns:
            None
        """
        if api_name in self.rate_limits:
            self.rate_limits[api_name].reset_backoff()
            logger.info(f"Reset API state: {api_name}")

    def reset_all(self) -> None:
        """
        全APIの状態をリセット

        Returns:
            None
        """
        for api_name in self.rate_limits:
            self.rate_limits[api_name].reset_backoff()
        logger.info("Reset all API states")
