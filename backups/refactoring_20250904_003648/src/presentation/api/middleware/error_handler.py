"""
Error Handler Middleware
エラーハンドリング ミドルウェア

設計書参照:
- プレゼンテーション層設計_20250809.md

アプリケーション全体のエラーハンドリングとレスポンス統一
"""

import traceback
from typing import Any, Dict, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    エラーハンドリング ミドルウェア

    責任:
    - 未処理例外のキャッチ
    - エラーレスポンスの統一
    - ログ記録
    - 本番環境でのセキュリティ考慮
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        リクエスト処理とエラーハンドリング

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラー

        Returns:
            Response: HTTPレスポンス
        """
        try:
            # 通常のリクエスト処理
            response = await call_next(request)
            return response

        except Exception as e:
            # エラーハンドリング
            return await self._handle_exception(request, e)

    async def _handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """
        例外を処理してJSONレスポンスを返す

        Args:
            request: HTTPリクエスト
            exc: 発生した例外

        Returns:
            JSONResponse: エラーレスポンス
        """
        # エラーの種類に応じて処理を分岐
        error_info = self._categorize_error(exc)

        # ログ記録
        self._log_error(request, exc, error_info)

        # エラーレスポンスを作成
        return self._create_error_response(error_info, request)

    def _categorize_error(self, exc: Exception) -> Dict[str, Any]:
        """
        エラーを分類し、適切なレスポンス情報を返す

        Args:
            exc: 発生した例外

        Returns:
            Dict[str, Any]: エラー情報
        """
        # HTTPExceptionの処理
        if hasattr(exc, "status_code"):
            return {
                "status_code": exc.status_code,
                "error_code": f"HTTP_{exc.status_code}",
                "message": getattr(exc, "detail", str(exc)),
                "error_type": "http_error",
                "internal": False,
            }

        # バリデーションエラー
        if "ValidationError" in exc.__class__.__name__:
            return {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_code": "VALIDATION_ERROR",
                "message": "リクエストデータが無効です",
                "error_type": "validation_error",
                "internal": False,
                "details": self._extract_validation_details(exc),
            }

        # データベースエラー
        if any(
            db_error in exc.__class__.__name__.lower()
            for db_error in ["sqlalchemy", "database", "connection", "operational"]
        ):
            return {
                "status_code": status.HTTP_503_SERVICE_UNAVAILABLE,
                "error_code": "DATABASE_ERROR",
                "message": "データベースエラーが発生しました",
                "error_type": "database_error",
                "internal": True,
            }

        # 外部API エラー
        if (
            "api" in exc.__class__.__name__.lower()
            or "client" in exc.__class__.__name__.lower()
        ):
            return {
                "status_code": status.HTTP_502_BAD_GATEWAY,
                "error_code": "EXTERNAL_API_ERROR",
                "message": "外部サービスとの通信でエラーが発生しました",
                "error_type": "external_api_error",
                "internal": True,
            }

        # タイムアウトエラー
        if "timeout" in exc.__class__.__name__.lower():
            return {
                "status_code": status.HTTP_408_REQUEST_TIMEOUT,
                "error_code": "TIMEOUT_ERROR",
                "message": "リクエストがタイムアウトしました",
                "error_type": "timeout_error",
                "internal": False,
            }

        # 認証・認可エラー
        if any(
            auth_error in exc.__class__.__name__.lower()
            for auth_error in ["auth", "permission", "forbidden", "unauthorized"]
        ):
            return {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "error_code": "AUTHENTICATION_ERROR",
                "message": "認証が必要です",
                "error_type": "auth_error",
                "internal": False,
            }

        # レート制限エラー
        if (
            "rate" in exc.__class__.__name__.lower()
            and "limit" in exc.__class__.__name__.lower()
        ):
            return {
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "error_code": "RATE_LIMIT_ERROR",
                "message": "リクエスト制限に達しました。しばらく待ってから再試行してください",
                "error_type": "rate_limit_error",
                "internal": False,
            }

        # その他の内部エラー
        return {
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "内部サーバーエラーが発生しました",
            "error_type": "internal_error",
            "internal": True,
        }

    def _extract_validation_details(self, exc: Exception) -> Optional[Dict[str, Any]]:
        """
        バリデーションエラーの詳細を抽出

        Args:
            exc: バリデーション例外

        Returns:
            Optional[Dict[str, Any]]: バリデーション詳細
        """
        try:
            if hasattr(exc, "errors"):
                errors = exc.errors()
                formatted_errors = []

                for error in errors:
                    formatted_errors.append(
                        {
                            "field": ".".join(str(x) for x in error.get("loc", [])),
                            "message": error.get("msg", ""),
                            "type": error.get("type", ""),
                            "input": error.get("input", ""),
                        }
                    )

                return {"validation_errors": formatted_errors}

        except Exception as e:
            logger.warning(f"Failed to extract validation details: {str(e)}")

        return None

    def _log_error(
        self, request: Request, exc: Exception, error_info: Dict[str, Any]
    ) -> None:
        """
        エラーをログに記録

        Args:
            request: HTTPリクエスト
            exc: 発生した例外
            error_info: エラー情報
        """
        # リクエスト情報
        request_info = {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "content_type": request.headers.get("content-type", "unknown"),
        }

        # エラーレベルに応じてログレベルを決定
        if error_info.get("internal", False):
            # 内部エラーはERRORレベル
            logger.error(
                f"❌ Internal Error: {exc.__class__.__name__}: {str(exc)}\n"
                f"Request: {request_info}\n"
                f"Error Info: {error_info}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
        else:
            # 外部起因のエラーはWARNINGレベル
            logger.warning(
                f"⚠️ Client Error: {exc.__class__.__name__}: {str(exc)}\n"
                f"Request: {request_info}\n"
                f"Error Info: {error_info}"
            )

    def _create_error_response(
        self, error_info: Dict[str, Any], request: Request
    ) -> JSONResponse:
        """
        エラーレスポンスを作成

        Args:
            error_info: エラー情報
            request: HTTPリクエスト

        Returns:
            JSONResponse: エラーレスポンス
        """
        # 基本レスポンス構造
        response_data = {
            "success": False,
            "error": {
                "code": error_info["error_code"],
                "message": error_info["message"],
                "type": error_info["error_type"],
            },
            "request_id": getattr(request.state, "request_id", None),
            "timestamp": self._get_current_timestamp(),
        }

        # 詳細情報があれば追加（開発環境のみ）
        if error_info.get("details") and self._is_development_mode():
            response_data["error"]["details"] = error_info["details"]

        # トレースID（分散トレーシング用）
        if hasattr(request.state, "trace_id"):
            response_data["trace_id"] = request.state.trace_id

        return JSONResponse(
            status_code=error_info["status_code"],
            content=response_data,
            headers={
                "X-Error-Code": error_info["error_code"],
                "X-Error-Type": error_info["error_type"],
            },
        )

    def _get_current_timestamp(self) -> str:
        """
        現在のタイムスタンプを取得

        Returns:
            str: ISO形式のタイムスタンプ
        """
        from datetime import datetime

        return datetime.utcnow().isoformat() + "Z"

    def _is_development_mode(self) -> bool:
        """
        開発モードかどうかを判定

        Returns:
            bool: 開発モードの場合True
        """
        import os

        return os.getenv("ENVIRONMENT", "development").lower() in [
            "development",
            "dev",
            "local",
        ]


# グローバルエラーハンドラー関数（FastAPIのexception_handlerデコレータ用）


def create_global_exception_handlers():
    """
    グローバル例外ハンドラーを作成

    Returns:
        Dict: 例外ハンドラーの辞書
    """
    from fastapi import HTTPException
    from pydantic import ValidationError

    async def http_exception_handler(
        request: Request, exc: HTTPException
    ) -> JSONResponse:
        """HTTPException ハンドラー"""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "type": "http_error",
                },
                "timestamp": ErrorHandlerMiddleware()._get_current_timestamp(),
            },
        )

    async def validation_exception_handler(
        request: Request, exc: ValidationError
    ) -> JSONResponse:
        """ValidationError ハンドラー"""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "リクエストデータが無効です",
                    "type": "validation_error",
                    "details": [
                        {
                            "field": ".".join(str(x) for x in error["loc"]),
                            "message": error["msg"],
                            "type": error["type"],
                        }
                        for error in exc.errors()
                    ],
                },
                "timestamp": ErrorHandlerMiddleware()._get_current_timestamp(),
            },
        )

    return {
        HTTPException: http_exception_handler,
        ValidationError: validation_exception_handler,
    }
