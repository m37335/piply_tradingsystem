"""
Base Handler Classes
基底ハンドラークラス

設計書参照:
- アプリケーション層設計_20250809.md

CQRSパターンのHandlerを実装
Commands/Queriesを処理するビジネスロジック層
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from ...utils.logging_config import get_application_logger
from ..commands.base import BaseCommand
from ..queries.base import BaseQuery

logger = get_application_logger()

# Type variables
TCommand = TypeVar("TCommand", bound=BaseCommand)
TQuery = TypeVar("TQuery", bound=BaseQuery)
TResult = TypeVar("TResult")


class BaseCommandHandler(ABC, Generic[TCommand, TResult]):
    """
    コマンドハンドラーの基底クラス

    責任:
    - コマンドの実行処理
    - エラーハンドリング
    - ログ記録
    - パフォーマンス監視
    """

    def __init__(self):
        self._execution_metrics: Dict[str, Any] = {}

    async def handle(self, command: TCommand) -> TResult:
        """
        コマンドを処理

        Args:
            command: 処理するコマンド

        Returns:
            TResult: 処理結果

        Raises:
            Exception: 処理エラー
        """
        start_time = datetime.utcnow()
        command_type = command.__class__.__name__

        logger.info(f"Handling command: {command_type} ({command.command_id})")

        try:
            # 前処理
            await self._before_handle(command)

            # バリデーション
            command.validate()

            # メイン処理
            result = await self._handle_command(command)

            # 後処理
            await self._after_handle(command, result)

            # メトリクス記録
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._record_metrics(command, execution_time, success=True)

            logger.info(
                f"Command handled successfully: {command_type} "
                f"({command.command_id}) in {execution_time:.3f}s"
            )

            return result

        except Exception as e:
            # エラーメトリクス記録
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            self._record_metrics(command, execution_time, success=False, error=str(e))

            logger.error(
                f"Command handling failed: {command_type} "
                f"({command.command_id}) after {execution_time:.3f}s - {str(e)}"
            )

            # エラー後処理
            await self._on_error(command, e)

            raise

    @abstractmethod
    async def _handle_command(self, command: TCommand) -> TResult:
        """
        コマンドの具体的な処理
        サブクラスで実装

        Args:
            command: 処理するコマンド

        Returns:
            TResult: 処理結果
        """
        pass

    async def _before_handle(self, command: TCommand) -> None:
        """
        コマンド処理前の処理

        Args:
            command: 処理するコマンド
        """
        # デフォルトでは何もしない
        pass

    async def _after_handle(self, command: TCommand, result: TResult) -> None:
        """
        コマンド処理後の処理

        Args:
            command: 処理したコマンド
            result: 処理結果
        """
        # デフォルトでは何もしない
        pass

    async def _on_error(self, command: TCommand, error: Exception) -> None:
        """
        エラー時の処理

        Args:
            command: 処理中だったコマンド
            error: 発生したエラー
        """
        # デフォルトでは何もしない
        pass

    def _record_metrics(
        self,
        command: TCommand,
        execution_time: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        実行メトリクスを記録

        Args:
            command: 実行されたコマンド
            execution_time: 実行時間（秒）
            success: 成功フラグ
            error: エラーメッセージ（エラー時のみ）
        """
        command_type = command.__class__.__name__

        if command_type not in self._execution_metrics:
            self._execution_metrics[command_type] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "last_execution": None,
                "errors": [],
            }

        metrics = self._execution_metrics[command_type]
        metrics["total_executions"] += 1
        metrics["total_execution_time"] += execution_time
        metrics["average_execution_time"] = (
            metrics["total_execution_time"] / metrics["total_executions"]
        )
        metrics["last_execution"] = datetime.utcnow().isoformat()

        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
            if error:
                metrics["errors"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "command_id": command.command_id,
                        "error": error,
                    }
                )
                # 直近10件のエラーのみ保持
                if len(metrics["errors"]) > 10:
                    metrics["errors"] = metrics["errors"][-10:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        実行メトリクスを取得

        Returns:
            Dict[str, Any]: 実行メトリクス
        """
        return self._execution_metrics.copy()


class BaseQueryHandler(ABC, Generic[TQuery, TResult]):
    """
    クエリハンドラーの基底クラス

    責任:
    - クエリの実行処理
    - キャッシュ管理
    - パフォーマンス最適化
    - ログ記録
    """

    def __init__(self):
        self._execution_metrics: Dict[str, Any] = {}
        self._cache_enabled: bool = True
        self._cache_ttl: int = 300  # 5分

    async def handle(self, query: TQuery) -> TResult:
        """
        クエリを処理

        Args:
            query: 処理するクエリ

        Returns:
            TResult: 処理結果
        """
        query.start_execution()
        query_type = query.__class__.__name__

        logger.debug(f"Handling query: {query_type} ({query.query_id})")

        try:
            # 前処理
            await self._before_handle(query)

            # バリデーション
            query.validate()

            # キャッシュチェック
            if self._cache_enabled:
                cached_result = await self._get_cached_result(query)
                if cached_result is not None:
                    query.end_execution()
                    logger.debug(
                        f"Cache hit for query: {query_type} ({query.query_id})"
                    )
                    return cached_result

            # メイン処理
            result = await self._handle_query(query)

            # キャッシュ保存
            if self._cache_enabled:
                await self._cache_result(query, result)

            # 後処理
            await self._after_handle(query, result)

            query.end_execution()
            execution_time = query.get_execution_duration_ms()

            # メトリクス記録
            self._record_metrics(query, execution_time or 0, success=True)

            logger.debug(
                f"Query handled successfully: {query_type} "
                f"({query.query_id}) in {execution_time:.2f}ms"
            )

            return result

        except Exception as e:
            query.end_execution()
            execution_time = query.get_execution_duration_ms()

            # エラーメトリクス記録
            self._record_metrics(
                query, execution_time or 0, success=False, error=str(e)
            )

            logger.error(
                f"Query handling failed: {query_type} "
                f"({query.query_id}) after {execution_time:.2f}ms - {str(e)}"
            )

            # エラー後処理
            await self._on_error(query, e)

            raise

    @abstractmethod
    async def _handle_query(self, query: TQuery) -> TResult:
        """
        クエリの具体的な処理
        サブクラスで実装

        Args:
            query: 処理するクエリ

        Returns:
            TResult: 処理結果
        """
        pass

    async def _before_handle(self, query: TQuery) -> None:
        """
        クエリ処理前の処理

        Args:
            query: 処理するクエリ
        """
        # デフォルトでは何もしない
        pass

    async def _after_handle(self, query: TQuery, result: TResult) -> None:
        """
        クエリ処理後の処理

        Args:
            query: 処理したクエリ
            result: 処理結果
        """
        # デフォルトでは何もしない
        pass

    async def _on_error(self, query: TQuery, error: Exception) -> None:
        """
        エラー時の処理

        Args:
            query: 処理中だったクエリ
            error: 発生したエラー
        """
        # デフォルトでは何もしない
        pass

    async def _get_cached_result(self, query: TQuery) -> Optional[TResult]:
        """
        キャッシュから結果を取得

        Args:
            query: クエリ

        Returns:
            Optional[TResult]: キャッシュされた結果（存在しない場合None）
        """
        # デフォルト実装では何もしない（キャッシュなし）
        return None

    async def _cache_result(self, query: TQuery, result: TResult) -> None:
        """
        結果をキャッシュに保存

        Args:
            query: クエリ
            result: 結果
        """
        # デフォルト実装では何もしない（キャッシュなし）
        pass

    def _generate_cache_key(self, query: TQuery) -> str:
        """
        キャッシュキーを生成

        Args:
            query: クエリ

        Returns:
            str: キャッシュキー
        """
        query_dict = query.to_dict()
        # 実行時固有の情報を除外
        cache_data = {
            k: v
            for k, v in query_dict.items()
            if k not in ["query_id", "timestamp", "execution_start", "execution_end"]
        }

        import hashlib
        import json

        cache_string = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def _record_metrics(
        self,
        query: TQuery,
        execution_time: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        実行メトリクスを記録

        Args:
            query: 実行されたクエリ
            execution_time: 実行時間（ミリ秒）
            success: 成功フラグ
            error: エラーメッセージ（エラー時のみ）
        """
        query_type = query.__class__.__name__

        if query_type not in self._execution_metrics:
            self._execution_metrics[query_type] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "last_execution": None,
                "errors": [],
            }

        metrics = self._execution_metrics[query_type]
        metrics["total_executions"] += 1
        metrics["total_execution_time"] += execution_time
        metrics["average_execution_time"] = (
            metrics["total_execution_time"] / metrics["total_executions"]
        )
        metrics["last_execution"] = datetime.utcnow().isoformat()

        if success:
            metrics["successful_executions"] += 1
        else:
            metrics["failed_executions"] += 1
            if error:
                metrics["errors"].append(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "query_id": query.query_id,
                        "error": error,
                    }
                )
                # 直近10件のエラーのみ保持
                if len(metrics["errors"]) > 10:
                    metrics["errors"] = metrics["errors"][-10:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        実行メトリクスを取得

        Returns:
            Dict[str, Any]: 実行メトリクス
        """
        return self._execution_metrics.copy()

    def set_cache_config(self, enabled: bool = True, ttl: int = 300) -> None:
        """
        キャッシュ設定を変更

        Args:
            enabled: キャッシュ有効フラグ
            ttl: キャッシュ有効期間（秒）
        """
        self._cache_enabled = enabled
        self._cache_ttl = ttl
