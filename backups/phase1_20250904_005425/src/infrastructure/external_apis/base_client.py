"""
Base External API Client
基底外部APIクライアント

設計書参照:
- インフラ・プラグイン設計_20250809.md

外部APIクライアントの基底クラス
"""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import aiohttp
from aiohttp import ClientSession, ClientTimeout

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class APIError(Exception):
    """API関連のエラー"""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(message)


class RateLimitError(APIError):
    """レート制限エラー"""

    def __init__(self, message: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message)


class BaseAPIClient(ABC):
    """
    外部APIクライアントの基底クラス

    責任:
    - HTTP通信の管理
    - エラーハンドリング
    - レート制限の管理
    - リトライ機能
    - ログ記録
    """

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_calls: int = 100,
        rate_limit_period: int = 60,
    ):
        """
        初期化

        Args:
            base_url: APIのベースURL
            api_key: APIキー
            timeout: リクエストタイムアウト（秒）
            max_retries: 最大リトライ回数
            retry_delay: リトライ遅延時間（秒）
            rate_limit_calls: レート制限：呼び出し回数
            rate_limit_period: レート制限：期間（秒）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # レート制限管理
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period
        self._call_times: List[datetime] = []

        # セッション管理
        self._session: Optional[ClientSession] = None

        logger.debug(f"Initialized {self.__class__.__name__} for {base_url}")

    async def __aenter__(self):
        """非同期コンテキストマネージャー開始"""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """非同期コンテキストマネージャー終了"""
        await self.close()

    async def _ensure_session(self) -> None:
        """セッションの確保"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self.timeout)
            logger.debug(f"Created new session for {self.__class__.__name__}")

    async def close(self) -> None:
        """セッションを閉じる"""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug(f"Closed session for {self.__class__.__name__}")

    async def _check_rate_limit(self) -> None:
        """レート制限をチェック"""
        now = datetime.utcnow()

        # 期間外の古い呼び出し記録を削除
        cutoff_time = now - timedelta(seconds=self.rate_limit_period)
        self._call_times = [
            call_time for call_time in self._call_times if call_time > cutoff_time
        ]

        # レート制限に達している場合は待機
        if len(self._call_times) >= self.rate_limit_calls:
            wait_time = (
                self.rate_limit_period - (now - self._call_times[0]).total_seconds()
            )
            if wait_time > 0:
                logger.warning(f"Rate limit reached, waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
                # 再帰的にチェック
                await self._check_rate_limit()

    def _record_api_call(self) -> None:
        """API呼び出しを記録"""
        self._call_times.append(datetime.utcnow())

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        HTTP リクエストを実行

        Args:
            method: HTTPメソッド
            endpoint: エンドポイント
            params: クエリパラメータ
            data: リクエストボディ
            headers: ヘッダー

        Returns:
            Dict[str, Any]: レスポンスデータ

        Raises:
            APIError: API関連のエラー
            RateLimitError: レート制限エラー
        """
        await self._ensure_session()
        await self._check_rate_limit()

        url = f"{self.base_url}/{endpoint.lstrip('/')}"

        # デフォルトヘッダーを設定
        request_headers = self._get_default_headers()
        if headers:
            request_headers.update(headers)

        # APIキーを含める
        if self.api_key:
            params = params or {}
            params.update(self._get_auth_params())

        retry_count = 0
        last_exception = None

        while retry_count <= self.max_retries:
            try:
                logger.debug(
                    f"Making {method} request to {url} (attempt {retry_count + 1})"
                )

                async with self._session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=data,
                    headers=request_headers,
                ) as response:
                    self._record_api_call()

                    # レスポンスの処理
                    response_data = await self._handle_response(response)

                    logger.debug(f"Request successful: {method} {url}")
                    return response_data

            except RateLimitError as e:
                logger.warning(
                    f"Rate limit error on attempt {retry_count + 1}: {e.message}"
                )
                if e.retry_after:
                    await asyncio.sleep(e.retry_after)
                else:
                    await asyncio.sleep(
                        self.retry_delay * (2**retry_count)
                    )  # Exponential backoff
                last_exception = e

            except APIError as e:
                # APIエラーは通常リトライしない
                logger.error(f"API error: {e.message}")
                raise

            except Exception as e:
                logger.warning(f"Request failed on attempt {retry_count + 1}: {str(e)}")
                last_exception = e
                if retry_count < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2**retry_count))

            retry_count += 1

        # 全てのリトライが失敗した場合
        error_msg = f"Request failed after {self.max_retries + 1} attempts"
        if last_exception:
            error_msg += f": {str(last_exception)}"

        logger.error(error_msg)
        raise APIError(error_msg)

    async def _handle_response(
        self, response: aiohttp.ClientResponse
    ) -> Dict[str, Any]:
        """
        レスポンスを処理

        Args:
            response: HTTPレスポンス

        Returns:
            Dict[str, Any]: パースされたレスポンスデータ

        Raises:
            APIError: レスポンス処理エラー
            RateLimitError: レート制限エラー
        """
        # レート制限チェック
        if response.status == 429:
            retry_after = response.headers.get("Retry-After")
            retry_after_int = int(retry_after) if retry_after else None
            raise RateLimitError(
                f"Rate limit exceeded: {response.status}", retry_after=retry_after_int
            )

        # エラーステータスチェック
        if response.status >= 400:
            try:
                error_data = await response.json()
            except:
                error_data = {"error": await response.text()}

            raise APIError(
                f"HTTP {response.status}: {error_data}",
                status_code=response.status,
                response_data=error_data,
            )

        # 成功レスポンスをパース
        try:
            return await response.json()
        except Exception as e:
            logger.error(f"Failed to parse response JSON: {str(e)}")
            raise APIError(f"Invalid JSON response: {str(e)}")

    def _get_default_headers(self) -> Dict[str, str]:
        """
        デフォルトヘッダーを取得

        Returns:
            Dict[str, str]: ヘッダー辞書
        """
        return {
            "User-Agent": f"ExchangeAnalytics/{self.__class__.__name__}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @abstractmethod
    def _get_auth_params(self) -> Dict[str, str]:
        """
        認証パラメータを取得

        Returns:
            Dict[str, str]: 認証パラメータ
        """
        pass

    # 便利メソッド

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """GETリクエスト"""
        return await self._make_request("GET", endpoint, params=params, headers=headers)

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """POSTリクエスト"""
        return await self._make_request(
            "POST", endpoint, params=params, data=data, headers=headers
        )

    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """PUTリクエスト"""
        return await self._make_request(
            "PUT", endpoint, params=params, data=data, headers=headers
        )

    async def delete(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """DELETEリクエスト"""
        return await self._make_request(
            "DELETE", endpoint, params=params, headers=headers
        )

    # 統計情報

    def get_rate_limit_status(self) -> Dict[str, Union[int, float]]:
        """
        レート制限の状況を取得

        Returns:
            Dict[str, Union[int, float]]: レート制限状況
        """
        now = datetime.utcnow()
        cutoff_time = now - timedelta(seconds=self.rate_limit_period)

        recent_calls = [
            call_time for call_time in self._call_times if call_time > cutoff_time
        ]

        remaining_calls = max(0, self.rate_limit_calls - len(recent_calls))

        if recent_calls:
            reset_time = recent_calls[0] + timedelta(seconds=self.rate_limit_period)
            reset_in_seconds = (reset_time - now).total_seconds()
        else:
            reset_in_seconds = 0

        return {
            "calls_made": len(recent_calls),
            "calls_remaining": remaining_calls,
            "reset_in_seconds": max(0, reset_in_seconds),
            "limit": self.rate_limit_calls,
            "period": self.rate_limit_period,
        }

    def __repr__(self) -> str:
        """文字列表現"""
        return f"{self.__class__.__name__}(base_url={self.base_url})"
