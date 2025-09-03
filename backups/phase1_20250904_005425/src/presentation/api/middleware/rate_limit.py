"""
Rate Limit Middleware
レート制限 ミドルウェア

設計書参照:
- プレゼンテーション層設計_20250809.md

API のレート制限とスロットリング機能
"""

import asyncio
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()


class RateLimitStore:
    """
    レート制限データストア

    責任:
    - リクエスト履歴の管理
    - 期限切れエントリのクリーンアップ
    - スレッドセーフな操作
    """

    def __init__(self, cleanup_interval: int = 60):
        """
        初期化

        Args:
            cleanup_interval: クリーンアップ間隔（秒）
        """
        self._requests: Dict[str, list] = defaultdict(list)
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

    async def add_request(self, key: str, timestamp: float) -> None:
        """
        リクエストを記録

        Args:
            key: クライアントキー
            timestamp: リクエストタイムスタンプ
        """
        async with self._locks[key]:
            self._requests[key].append(timestamp)

            # 定期的なクリーンアップ
            current_time = time.time()
            if current_time - self._last_cleanup > self._cleanup_interval:
                await self._cleanup_expired_requests()
                self._last_cleanup = current_time

    async def get_request_count(self, key: str, window_seconds: int) -> int:
        """
        指定期間内のリクエスト数を取得

        Args:
            key: クライアントキー
            window_seconds: タイムウィンドウ（秒）

        Returns:
            int: リクエスト数
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        async with self._locks[key]:
            # 期限切れリクエストを除去
            self._requests[key] = [ts for ts in self._requests[key] if ts > cutoff_time]

            return len(self._requests[key])

    async def get_oldest_request(self, key: str) -> Optional[float]:
        """
        最古のリクエストタイムスタンプを取得

        Args:
            key: クライアントキー

        Returns:
            Optional[float]: 最古のタイムスタンプ
        """
        async with self._locks[key]:
            requests = self._requests.get(key, [])
            return min(requests) if requests else None

    async def _cleanup_expired_requests(self) -> None:
        """期限切れリクエストをクリーンアップ"""
        current_time = time.time()
        cutoff_time = current_time - 3600  # 1時間前より古いものを削除

        keys_to_remove = []

        for key, requests in self._requests.items():
            # 期限切れリクエストを除去
            self._requests[key] = [ts for ts in requests if ts > cutoff_time]

            # 空になったキーを削除対象に追加
            if not self._requests[key]:
                keys_to_remove.append(key)

        # 空のキーを削除
        for key in keys_to_remove:
            del self._requests[key]
            if key in self._locks:
                del self._locks[key]

        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired rate limit entries")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    レート制限ミドルウェア

    責任:
    - クライアントごとのリクエスト制限
    - エンドポイント別制限
    - 制限超過時のレスポンス処理
    """

    def __init__(
        self,
        app,
        default_calls: int = 100,
        default_period: int = 60,
        burst_calls: int = 20,
        burst_period: int = 1,
        **kwargs,
    ):
        """
        初期化

        Args:
            app: ASGIアプリケーション
            default_calls: デフォルト呼び出し制限数
            default_period: デフォルト期間（秒）
            burst_calls: バースト制限数
            burst_period: バースト期間（秒）
            **kwargs: その他の設定
        """
        super().__init__(app, **kwargs)

        self.default_calls = default_calls
        self.default_period = default_period
        self.burst_calls = burst_calls
        self.burst_period = burst_period

        # レート制限ストア
        self.store = RateLimitStore()

        # エンドポイント固有の制限設定
        self.endpoint_limits = {
            # 認証関連 - より厳しい制限
            "/api/v1/auth": {"calls": 10, "period": 60},
            # AI分析 - リソース消費が大きいため制限
            "/api/v1/ai-reports": {"calls": 20, "period": 60},
            "/api/v1/analysis": {"calls": 50, "period": 60},
            # データ取得 - 比較的緩い制限
            "/api/v1/rates": {"calls": 200, "period": 60},
            "/api/v1/health": {"calls": 500, "period": 60},
            # 管理機能 - 中程度の制限
            "/api/v1/alerts": {"calls": 30, "period": 60},
            "/api/v1/plugins": {"calls": 30, "period": 60},
        }

        logger.info(
            f"Rate limit middleware initialized: {default_calls}/{default_period}s"
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        リクエスト処理とレート制限チェック

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラー

        Returns:
            Response: HTTPレスポンス
        """
        # クライアント識別子を取得
        client_key = self._get_client_key(request)

        # レート制限チェック
        is_allowed, limit_info = await self._check_rate_limit(request, client_key)

        if not is_allowed:
            # レート制限に引っかかった場合
            return await self._create_rate_limit_response(limit_info)

        # リクエストを記録
        current_time = time.time()
        await self.store.add_request(client_key, current_time)

        # 通常のリクエスト処理
        response = await call_next(request)

        # レスポンスヘッダーに制限情報を追加
        self._add_rate_limit_headers(response, limit_info)

        return response

    def _get_client_key(self, request: Request) -> str:
        """
        クライアント識別子を取得

        Args:
            request: HTTPリクエスト

        Returns:
            str: クライアントキー
        """
        # 認証済みユーザーの場合はユーザーIDを使用
        if hasattr(request.state, "user_id") and request.state.user_id:
            return f"user:{request.state.user_id}"

        # APIキーがある場合
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key[:8]}..."  # セキュリティのため一部のみ

        # IPアドレスベース
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """
        クライアントIPアドレスを取得

        Args:
            request: HTTPリクエスト

        Returns:
            str: IPアドレス
        """
        # プロキシ経由の場合を考慮
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 直接接続の場合
        if request.client:
            return request.client.host

        return "unknown"

    async def _check_rate_limit(
        self, request: Request, client_key: str
    ) -> Tuple[bool, Dict[str, any]]:
        """
        レート制限をチェック

        Args:
            request: HTTPリクエスト
            client_key: クライアントキー

        Returns:
            Tuple[bool, Dict]: (許可フラグ, 制限情報)
        """
        path = request.url.path

        # エンドポイント固有の制限を取得
        endpoint_limit = self._get_endpoint_limit(path)
        calls_limit = endpoint_limit.get("calls", self.default_calls)
        period = endpoint_limit.get("period", self.default_period)

        # 現在のリクエスト数を取得
        current_requests = await self.store.get_request_count(client_key, period)

        # バースト制限もチェック
        burst_requests = await self.store.get_request_count(
            client_key, self.burst_period
        )

        # 制限情報
        limit_info = {
            "limit": calls_limit,
            "period": period,
            "current": current_requests,
            "remaining": max(0, calls_limit - current_requests),
            "reset_time": None,
            "burst_limit": self.burst_calls,
            "burst_current": burst_requests,
            "burst_remaining": max(0, self.burst_calls - burst_requests),
        }

        # リセット時間を計算
        oldest_request = await self.store.get_oldest_request(client_key)
        if oldest_request:
            limit_info["reset_time"] = oldest_request + period

        # 制限チェック
        if burst_requests >= self.burst_calls:
            logger.warning(
                f"Burst rate limit exceeded for {client_key}: {burst_requests}/{self.burst_calls}"
            )
            return False, limit_info

        if current_requests >= calls_limit:
            logger.warning(
                f"Rate limit exceeded for {client_key}: {current_requests}/{calls_limit}"
            )
            return False, limit_info

        return True, limit_info

    def _get_endpoint_limit(self, path: str) -> Dict[str, int]:
        """
        エンドポイント固有の制限を取得

        Args:
            path: リクエストパス

        Returns:
            Dict[str, int]: 制限設定
        """
        # 完全一致をチェック
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]

        # プレフィックス一致をチェック
        for endpoint_path, limits in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return limits

        # デフォルト制限
        return {"calls": self.default_calls, "period": self.default_period}

    async def _create_rate_limit_response(
        self, limit_info: Dict[str, any]
    ) -> JSONResponse:
        """
        レート制限レスポンスを作成

        Args:
            limit_info: 制限情報

        Returns:
            JSONResponse: エラーレスポンス
        """
        reset_time = limit_info.get("reset_time")
        retry_after = (
            int(reset_time - time.time()) if reset_time else limit_info["period"]
        )

        content = {
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "レート制限に達しました。しばらく待ってから再試行してください。",
                "type": "rate_limit_error",
            },
            "rate_limit": {
                "limit": limit_info["limit"],
                "remaining": limit_info["remaining"],
                "reset": reset_time,
                "retry_after": retry_after,
            },
            "timestamp": time.time(),
        }

        headers = {
            "X-RateLimit-Limit": str(limit_info["limit"]),
            "X-RateLimit-Remaining": str(limit_info["remaining"]),
            "X-RateLimit-Reset": str(int(reset_time)) if reset_time else "",
            "Retry-After": str(retry_after),
        }

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=content,
            headers=headers,
        )

    def _add_rate_limit_headers(
        self, response: Response, limit_info: Dict[str, any]
    ) -> None:
        """
        レスポンスにレート制限ヘッダーを追加

        Args:
            response: HTTPレスポンス
            limit_info: 制限情報
        """
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])

        if limit_info.get("reset_time"):
            response.headers["X-RateLimit-Reset"] = str(int(limit_info["reset_time"]))

        # バースト制限情報も追加
        response.headers["X-RateLimit-Burst-Limit"] = str(limit_info["burst_limit"])
        response.headers["X-RateLimit-Burst-Remaining"] = str(
            limit_info["burst_remaining"]
        )
