"""
Discordエラーハンドラー
Discord通知のエラー処理を担当
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional


class DiscordErrorHandler:
    """Discordエラーハンドラー"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.error_counts = {}
        self.last_error_time = {}
        self.max_errors_per_hour = 10

    def handle_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        エラーを処理

        Args:
            error: 発生したエラー
            context: エラーコンテキスト

        Returns:
            Dict[str, Any]: エラー情報
        """
        error_type = type(error).__name__
        current_time = datetime.utcnow()

        # エラーカウントを更新
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
            self.last_error_time[error_type] = current_time

        # 1時間経過したらカウントをリセット
        if current_time - self.last_error_time[error_type] > timedelta(hours=1):
            self.error_counts[error_type] = 0
            self.last_error_time[error_type] = current_time

        self.error_counts[error_type] += 1

        # エラー情報を構築
        error_info = {
            "error_type": error_type,
            "error_message": str(error),
            "timestamp": current_time.isoformat(),
            "error_count": self.error_counts[error_type],
            "context": context or {},
        }

        # ログ出力
        self._log_error(error_info)

        # エラー率が高すぎる場合は警告
        if self.error_counts[error_type] >= self.max_errors_per_hour:
            self.logger.warning(
                f"High error rate for {error_type}: "
                f"{self.error_counts[error_type]} errors in the last hour"
            )

        return error_info

    def _log_error(self, error_info: Dict[str, Any]) -> None:
        """エラーをログに出力"""
        error_type = error_info["error_type"]
        error_message = error_info["error_message"]
        error_count = error_info["error_count"]

        if error_count == 1:
            # 初回エラー
            self.logger.error(f"Discord error ({error_type}): {error_message}")
        else:
            # 繰り返しエラー
            self.logger.warning(
                f"Discord error repeated ({error_type}): "
                f"{error_message} (count: {error_count})"
            )

    def should_retry(self, error: Exception) -> bool:
        """
        リトライすべきかどうかを判定

        Args:
            error: 発生したエラー

        Returns:
            bool: リトライすべき場合True
        """
        error_type = type(error).__name__

        # エラー率が高すぎる場合はリトライしない
        if self.error_counts.get(error_type, 0) >= self.max_errors_per_hour:
            return False

        # リトライ可能なエラータイプ
        retryable_errors = [
            "ConnectionError",
            "TimeoutError",
            "ClientError",
            "ServerError",
        ]

        return error_type in retryable_errors

    def get_error_summary(self) -> Dict[str, Any]:
        """
        エラーサマリーを取得

        Returns:
            Dict[str, Any]: エラーサマリー
        """
        current_time = datetime.utcnow()

        # 1時間以内のエラーのみをカウント
        recent_errors = {}
        for error_type, count in self.error_counts.items():
            if current_time - self.last_error_time[error_type] <= timedelta(hours=1):
                recent_errors[error_type] = count

        return {
            "total_errors": sum(recent_errors.values()),
            "error_types": recent_errors,
            "high_error_rate": any(
                count >= self.max_errors_per_hour for count in recent_errors.values()
            ),
        }

    def reset_error_counts(self) -> None:
        """エラーカウントをリセット"""
        self.error_counts.clear()
        self.last_error_time.clear()
        self.logger.info("Discord error counts reset")

    def is_healthy(self) -> bool:
        """
        システムが健全かどうかを判定

        Returns:
            bool: 健全な場合True
        """
        summary = self.get_error_summary()
        return not summary["high_error_rate"]
