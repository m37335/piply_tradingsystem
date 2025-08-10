"""
Batch Processor System
バッチ処理システム

設計書参照:
- api_optimization_design_2025.md

一括API呼び出しと並列処理システム
"""

import asyncio
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

from ...utils.logging_config import get_infrastructure_logger
from ...utils.optimization_utils import measure_performance, optimize_batch_size
from .api_rate_limiter import ApiRateLimiter

logger = get_infrastructure_logger()

T = TypeVar("T")
R = TypeVar("R")


class BatchRequest:
    """
    バッチリクエスト

    責任:
    - 個別リクエストの情報を管理
    - リクエスト状態の追跡
    """

    def __init__(
        self,
        request_id: str,
        func: Callable,
        args: Tuple[Any, ...] = (),
        kwargs: Dict[str, Any] = None,
        priority: int = 0,
        retry_count: int = 0,
        max_retries: int = 3,
    ):
        """
        初期化

        Args:
            request_id: リクエストID
            func: 実行する関数
            args: 関数の引数
            kwargs: 関数のキーワード引数
            priority: 優先度（高いほど優先）
            retry_count: 現在のリトライ回数
            max_retries: 最大リトライ回数
        """
        self.request_id = request_id
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries

        # 状態管理
        self.status = "pending"  # pending, running, completed, failed, retrying
        self.result = None
        self.error = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.execution_time: Optional[float] = None

    def start_execution(self) -> None:
        """
        実行開始

        Returns:
            None
        """
        self.status = "running"
        self.start_time = datetime.utcnow()

    def complete_execution(self, result: Any) -> None:
        """
        実行完了

        Args:
            result: 実行結果

        Returns:
            None
        """
        self.status = "completed"
        self.result = result
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()

    def fail_execution(self, error: Exception) -> None:
        """
        実行失敗

        Args:
            error: エラー

        Returns:
            None
        """
        self.status = "failed"
        self.error = error
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.execution_time = (self.end_time - self.start_time).total_seconds()

    def can_retry(self) -> bool:
        """
        リトライ可能かどうかを判定

        Returns:
            bool: リトライ可能な場合True
        """
        return self.retry_count < self.max_retries

    def increment_retry(self) -> None:
        """
        リトライ回数を増加

        Returns:
            None
        """
        self.retry_count += 1
        self.status = "retrying"
        self.error = None
        self.start_time = None
        self.end_time = None
        self.execution_time = None

    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        return {
            "request_id": self.request_id,
            "status": self.status,
            "priority": self.priority,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "execution_time": self.execution_time,
            "start_time": (self.start_time.isoformat() if self.start_time else None),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "has_error": self.error is not None,
            "error_message": str(self.error) if self.error else None,
        }


class BatchResult:
    """
    バッチ処理結果

    責任:
    - バッチ処理の結果を管理
    - 統計情報の提供
    """

    def __init__(self, batch_id: str):
        """
        初期化

        Args:
            batch_id: バッチID
        """
        self.batch_id = batch_id
        self.requests: List[BatchRequest] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.total_execution_time: Optional[float] = None

    def add_request(self, request: BatchRequest) -> None:
        """
        リクエストを追加

        Args:
            request: バッチリクエスト

        Returns:
            None
        """
        self.requests.append(request)

    def start_batch(self) -> None:
        """
        バッチ処理開始

        Returns:
            None
        """
        self.start_time = datetime.utcnow()

    def complete_batch(self) -> None:
        """
        バッチ処理完了

        Returns:
            None
        """
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.total_execution_time = (
                self.end_time - self.start_time
            ).total_seconds()

    def get_successful_results(self) -> List[Tuple[str, Any]]:
        """
        成功した結果を取得

        Returns:
            List[Tuple[str, Any]]: リクエストIDと結果のリスト
        """
        return [
            (req.request_id, req.result)
            for req in self.requests
            if req.status == "completed"
        ]

    def get_failed_requests(self) -> List[Tuple[str, Exception]]:
        """
        失敗したリクエストを取得

        Returns:
            List[Tuple[str, Exception]]: リクエストIDとエラーのリスト
        """
        return [
            (req.request_id, req.error)
            for req in self.requests
            if req.status == "failed"
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得

        Returns:
            Dict[str, Any]: 統計情報
        """
        total_requests = len(self.requests)
        completed_requests = len([r for r in self.requests if r.status == "completed"])
        failed_requests = len([r for r in self.requests if r.status == "failed"])
        retrying_requests = len([r for r in self.requests if r.status == "retrying"])

        avg_execution_time = None
        if completed_requests > 0:
            execution_times = [
                r.execution_time for r in self.requests if r.execution_time is not None
            ]
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)

        return {
            "batch_id": self.batch_id,
            "total_requests": total_requests,
            "completed_requests": completed_requests,
            "failed_requests": failed_requests,
            "retrying_requests": retrying_requests,
            "success_rate": (
                (completed_requests / total_requests * 100) if total_requests > 0 else 0
            ),
            "total_execution_time": self.total_execution_time,
            "avg_execution_time": avg_execution_time,
            "start_time": (self.start_time.isoformat() if self.start_time else None),
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


class BatchProcessor:
    """
    バッチ処理システム

    責任:
    - 一括API呼び出し
    - 並列処理
    - エラーハンドリング
    - 結果集約
    """

    def __init__(
        self,
        api_rate_limiter: ApiRateLimiter,
        max_concurrent_requests: int = 5,
        request_delay_ms: int = 100,
        max_batch_size: int = 50,
        enable_priority_queue: bool = True,
    ):
        """
        初期化

        Args:
            api_rate_limiter: API制限管理システム
            max_concurrent_requests: 最大並列リクエスト数
            request_delay_ms: リクエスト間の遅延（ミリ秒）
            max_batch_size: 最大バッチサイズ
            enable_priority_queue: 優先度キューを有効にするか
        """
        self.api_rate_limiter = api_rate_limiter
        self.max_concurrent_requests = max_concurrent_requests
        self.request_delay_ms = request_delay_ms
        self.max_batch_size = max_batch_size
        self.enable_priority_queue = enable_priority_queue

        # バッチ処理履歴
        self.batch_history: List[BatchResult] = []
        self.active_batches: Dict[str, BatchResult] = {}

        logger.info(
            f"BatchProcessor initialized: "
            f"max_concurrent={max_concurrent_requests}, "
            f"delay={request_delay_ms}ms, "
            f"max_batch_size={max_batch_size}"
        )

    def _generate_batch_id(self) -> str:
        """
        バッチIDを生成

        Returns:
            str: バッチID
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        return f"batch_{timestamp}"

    def _generate_request_id(self, batch_id: str, index: int) -> str:
        """
        リクエストIDを生成

        Args:
            batch_id: バッチID
            index: インデックス

        Returns:
            str: リクエストID
        """
        return f"{batch_id}_req_{index:04d}"

    async def _execute_single_request(
        self, request: BatchRequest, api_name: str
    ) -> None:
        """
        単一リクエストを実行

        Args:
            request: バッチリクエスト
            api_name: API名

        Returns:
            None
        """
        try:
            request.start_execution()

            # API制限管理システムを使用して実行
            result = await self.api_rate_limiter.execute_with_retry(
                api_name, request.func, *request.args, **request.kwargs
            )

            request.complete_execution(result)

        except Exception as e:
            request.fail_execution(e)
            logger.error(f"Request {request.request_id} failed: {str(e)}")

    async def _process_batch_requests(
        self, requests: List[BatchRequest], api_name: str
    ) -> None:
        """
        バッチリクエストを処理

        Args:
            requests: リクエストリスト
            api_name: API名

        Returns:
            None
        """
        # 優先度でソート（高い優先度が先）
        if self.enable_priority_queue:
            requests.sort(key=lambda r: r.priority, reverse=True)

        # セマフォを使用して並列数を制限
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        async def execute_with_semaphore(request: BatchRequest) -> None:
            async with semaphore:
                await self._execute_single_request(request, api_name)
                # リクエスト間の遅延
                if self.request_delay_ms > 0:
                    await asyncio.sleep(self.request_delay_ms / 1000)

        # 並列実行
        tasks = [execute_with_semaphore(request) for request in requests]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def process_batch(
        self,
        requests: List[Tuple[Callable, Tuple[Any, ...], Dict[str, Any]]],
        api_name: str,
        batch_id: Optional[str] = None,
        priorities: Optional[List[int]] = None,
        max_retries: Optional[List[int]] = None,
    ) -> BatchResult:
        """
        バッチ処理を実行

        Args:
            requests: リクエストリスト（関数、引数、キーワード引数のタプル）
            api_name: API名
            batch_id: バッチID（Noneの場合は自動生成）
            priorities: 優先度リスト（Noneの場合は全て0）
            max_retries: 最大リトライ回数リスト（Noneの場合は全て3）

        Returns:
            BatchResult: バッチ処理結果
        """
        # パフォーマンス測定開始
        start_time, memory_before = measure_performance()

        # バッチIDを生成
        if batch_id is None:
            batch_id = self._generate_batch_id()

        # バッチ結果を作成
        batch_result = BatchResult(batch_id)
        self.active_batches[batch_id] = batch_result

        try:
            # バッチ処理開始
            batch_result.start_batch()

            # リクエストをバッチサイズで分割
            batch_size = optimize_batch_size(len(requests), self.max_batch_size)
            request_batches = [
                requests[i : i + batch_size]
                for i in range(0, len(requests), batch_size)
            ]

            logger.info(
                f"Starting batch {batch_id}: "
                f"{len(requests)} requests in {len(request_batches)} batches"
            )

            # 各バッチを処理
            for batch_index, request_batch in enumerate(request_batches):
                # バッチリクエストを作成
                batch_requests = []
                for req_index, (func, args, kwargs) in enumerate(request_batch):
                    request_id = self._generate_request_id(
                        batch_id, batch_index * batch_size + req_index
                    )

                    req_idx = batch_index * batch_size + req_index
                    priority = (
                        priorities[req_idx]
                        if priorities and req_idx < len(priorities)
                        else 0
                    )

                    retry_count = (
                        max_retries[req_idx]
                        if max_retries and req_idx < len(max_retries)
                        else 3
                    )

                    request = BatchRequest(
                        request_id=request_id,
                        func=func,
                        args=args,
                        kwargs=kwargs,
                        priority=priority,
                        max_retries=retry_count,
                    )
                    batch_requests.append(request)
                    batch_result.add_request(request)

                # バッチを処理
                await self._process_batch_requests(batch_requests, api_name)

                logger.info(
                    f"Completed batch {batch_index + 1}/{len(request_batches)} "
                    f"for {batch_id}"
                )

            # バッチ処理完了
            batch_result.complete_batch()

            # 統計情報を記録
            self.batch_history.append(batch_result)
            del self.active_batches[batch_id]

            # パフォーマンス測定完了
            execution_time, memory_after = measure_performance()
            memory_usage = memory_after - memory_before

            logger.info(
                f"Batch {batch_id} completed: "
                f"time={execution_time:.2f}s, "
                f"memory={memory_usage:.2f}MB, "
                f"success_rate={batch_result.get_statistics()['success_rate']:.1f}%"
            )

            return batch_result

        except Exception as e:
            logger.error(f"Batch {batch_id} failed: {str(e)}")
            batch_result.complete_batch()
            return batch_result

    async def process_requests_with_retry(
        self,
        requests: List[Tuple[Callable, Tuple[Any, ...], Dict[str, Any]]],
        api_name: str,
        max_retry_attempts: int = 3,
        **kwargs,
    ) -> BatchResult:
        """
        リトライ付きでバッチ処理を実行

        Args:
            requests: リクエストリスト
            api_name: API名
            max_retry_attempts: 最大リトライ回数
            **kwargs: その他の引数

        Returns:
            BatchResult: バッチ処理結果
        """
        batch_result = await self.process_batch(requests, api_name, **kwargs)

        # 失敗したリクエストをリトライ
        for attempt in range(max_retry_attempts):
            failed_requests = batch_result.get_failed_requests()
            if not failed_requests:
                break

            logger.info(
                f"Retrying {len(failed_requests)} failed requests "
                f"(attempt {attempt + 1}/{max_retry_attempts})"
            )

            # 失敗したリクエストを再実行
            retry_requests = []
            for request_id, error in failed_requests:
                # 元のリクエストを取得
                original_request = next(
                    (r for r in batch_result.requests if r.request_id == request_id),
                    None,
                )
                if original_request and original_request.can_retry():
                    original_request.increment_retry()
                    retry_requests.append(
                        (
                            original_request.func,
                            original_request.args,
                            original_request.kwargs,
                        )
                    )

            if retry_requests:
                retry_batch_result = await self.process_batch(
                    retry_requests, api_name, **kwargs
                )
                # 結果を統合
                for retry_request in retry_batch_result.requests:
                    original_request = next(
                        (
                            r
                            for r in batch_result.requests
                            if r.request_id == retry_request.request_id
                        ),
                        None,
                    )
                    if original_request:
                        original_request.status = retry_request.status
                        original_request.result = retry_request.result
                        original_request.error = retry_request.error
                        original_request.execution_time = retry_request.execution_time

        return batch_result

    def get_batch_statistics(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        バッチ統計を取得

        Args:
            batch_id: バッチID

        Returns:
            Optional[Dict[str, Any]]: バッチ統計
        """
        # アクティブなバッチから検索
        if batch_id in self.active_batches:
            return self.active_batches[batch_id].get_statistics()

        # 履歴から検索
        for batch_result in self.batch_history:
            if batch_result.batch_id == batch_id:
                return batch_result.get_statistics()

        return None

    def get_all_statistics(self) -> Dict[str, Any]:
        """
        全バッチ統計を取得

        Returns:
            Dict[str, Any]: 全バッチ統計
        """
        total_batches = len(self.batch_history)
        total_requests = sum(len(batch.requests) for batch in self.batch_history)
        total_completed = sum(
            len([r for r in batch.requests if r.status == "completed"])
            for batch in self.batch_history
        )
        total_failed = sum(
            len([r for r in batch.requests if r.status == "failed"])
            for batch in self.batch_history
        )

        avg_execution_time = None
        if total_batches > 0:
            execution_times = [
                batch.total_execution_time
                for batch in self.batch_history
                if batch.total_execution_time is not None
            ]
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)

        return {
            "total_batches": total_batches,
            "total_requests": total_requests,
            "total_completed": total_completed,
            "total_failed": total_failed,
            "overall_success_rate": (
                (total_completed / total_requests * 100) if total_requests > 0 else 0
            ),
            "avg_execution_time": avg_execution_time,
            "active_batches": len(self.active_batches),
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_delay_ms": self.request_delay_ms,
        }

    def clear_history(self) -> int:
        """
        履歴をクリア

        Returns:
            int: 削除されたバッチ数
        """
        count = len(self.batch_history)
        self.batch_history.clear()
        logger.info(f"Cleared {count} batch history entries")
        return count
