"""
Authentication Middleware
認証ミドルウェア

設計書参照:
- プレゼンテーション層設計_20250809.md

API認証とセキュリティ管理
"""

import hashlib
import hmac
import time
from typing import Any, Dict, List, Optional, Set

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    認証ミドルウェア

    責任:
    - API キー認証
    - JWT トークン認証
    - パブリックエンドポイントの管理
    - セキュリティヘッダーの追加
    """

    def __init__(
        self,
        app,
        api_keys: Optional[Dict[str, Dict[str, Any]]] = None,
        jwt_secret: Optional[str] = None,
        **kwargs,
    ):
        """
        初期化

        Args:
            app: ASGIアプリケーション
            api_keys: APIキー設定辞書
            jwt_secret: JWT署名シークレット
            **kwargs: その他の設定
        """
        super().__init__(app, **kwargs)

        # APIキー設定（通常は環境変数やデータベースから取得）
        self.api_keys = api_keys or self._get_default_api_keys()

        # JWT設定
        self.jwt_secret = jwt_secret or self._get_jwt_secret()

        # 認証不要のパブリックエンドポイント
        self.public_paths: Set[str] = {
            "/",
            "/api",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v1/health/",
            "/favicon.ico",
        }

        # 管理者権限が必要なエンドポイント
        self.admin_paths: Set[str] = {"/api/v1/plugins", "/api/v1/admin"}

        logger.info("Authentication middleware initialized")

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        リクエスト処理と認証チェック

        Args:
            request: HTTPリクエスト
            call_next: 次のミドルウェア/ハンドラー

        Returns:
            Response: HTTPレスポンス
        """
        # パブリックパスの場合は認証をスキップ
        if self._is_public_path(request.url.path):
            response = await call_next(request)
            self._add_security_headers(response)
            return response

        # 認証チェック
        auth_result = await self._authenticate_request(request)

        if not auth_result["success"]:
            return self._create_auth_error_response(auth_result)

        # リクエスト状態に認証情報を設定
        self._set_request_state(request, auth_result)

        # 権限チェック
        if not self._check_permissions(request, auth_result):
            return self._create_permission_error_response()

        # 通常のリクエスト処理
        response = await call_next(request)

        # セキュリティヘッダーを追加
        self._add_security_headers(response)

        return response

    def _is_public_path(self, path: str) -> bool:
        """
        パブリックパスかどうかをチェック

        Args:
            path: リクエストパス

        Returns:
            bool: パブリックパスの場合True
        """
        # 完全一致チェック
        if path in self.public_paths:
            return True

        # プレフィックス一致チェック（静的ファイルなど）
        public_prefixes = ["/static/", "/assets/"]
        return any(path.startswith(prefix) for prefix in public_prefixes)

    async def _authenticate_request(self, request: Request) -> Dict[str, Any]:
        """
        リクエストを認証

        Args:
            request: HTTPリクエスト

        Returns:
            Dict[str, Any]: 認証結果
        """
        # APIキー認証を試行
        api_key_result = self._authenticate_api_key(request)
        if api_key_result["success"]:
            return api_key_result

        # JWT認証を試行
        jwt_result = self._authenticate_jwt(request)
        if jwt_result["success"]:
            return jwt_result

        # 認証失敗
        return {
            "success": False,
            "error": "認証が必要です",
            "error_code": "AUTHENTICATION_REQUIRED",
        }

    def _authenticate_api_key(self, request: Request) -> Dict[str, Any]:
        """
        API キー認証

        Args:
            request: HTTPリクエスト

        Returns:
            Dict[str, Any]: 認証結果
        """
        # ヘッダーからAPIキーを取得
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return {"success": False, "error": "APIキーが必要です"}

        # APIキーの検証
        key_info = self.api_keys.get(api_key)

        if not key_info:
            logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
            return {"success": False, "error": "無効なAPIキーです"}

        # キーの有効期限チェック
        if key_info.get("expires") and time.time() > key_info["expires"]:
            return {"success": False, "error": "APIキーの有効期限が切れています"}

        # キーのアクティブ状態チェック
        if not key_info.get("active", True):
            return {"success": False, "error": "APIキーが無効化されています"}

        logger.debug(
            f"API key authentication successful: {key_info.get('name', 'Unknown')}"
        )

        return {
            "success": True,
            "auth_type": "api_key",
            "user_id": key_info.get("user_id"),
            "user_name": key_info.get("name"),
            "permissions": key_info.get("permissions", []),
            "is_admin": key_info.get("is_admin", False),
        }

    def _authenticate_jwt(self, request: Request) -> Dict[str, Any]:
        """
        JWT 認証

        Args:
            request: HTTPリクエスト

        Returns:
            Dict[str, Any]: 認証結果
        """
        # Authorization ヘッダーからトークンを取得
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return {"success": False, "error": "Bearerトークンが必要です"}

        token = auth_header[7:]  # "Bearer " を除去

        try:
            # JWTトークンをデコード（実装では python-jose などを使用）
            payload = self._decode_jwt_token(token)

            if not payload:
                return {"success": False, "error": "無効なトークンです"}

            # トークンの有効期限チェック
            if payload.get("exp", 0) < time.time():
                return {"success": False, "error": "トークンの有効期限が切れています"}

            logger.debug(
                f"JWT authentication successful: {payload.get('sub', 'Unknown')}"
            )

            return {
                "success": True,
                "auth_type": "jwt",
                "user_id": payload.get("sub"),
                "user_name": payload.get("name"),
                "permissions": payload.get("permissions", []),
                "is_admin": payload.get("is_admin", False),
                "token_payload": payload,
            }

        except Exception as e:
            logger.warning(f"JWT authentication failed: {str(e)}")
            return {"success": False, "error": "トークンの処理に失敗しました"}

    def _decode_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        JWT トークンをデコード

        Args:
            token: JWTトークン

        Returns:
            Optional[Dict[str, Any]]: デコードされたペイロード
        """
        # 簡易実装（実際はpython-joseなどを使用）
        # ここでは開発用のダミー実装

        if not self.jwt_secret:
            return None

        try:
            # 実際の実装では jwt.decode() を使用
            # import jwt
            # return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])

            # ダミー実装（開発用）
            if token == "dev_token":
                return {
                    "sub": "dev_user",
                    "name": "Development User",
                    "permissions": ["read", "write"],
                    "is_admin": True,
                    "exp": time.time() + 3600,  # 1時間後に期限切れ
                }

            return None

        except Exception:
            return None

    def _check_permissions(self, request: Request, auth_result: Dict[str, Any]) -> bool:
        """
        権限をチェック

        Args:
            request: HTTPリクエスト
            auth_result: 認証結果

        Returns:
            bool: 権限がある場合True
        """
        path = request.url.path

        # 管理者権限が必要なパスのチェック
        if any(path.startswith(admin_path) for admin_path in self.admin_paths):
            return auth_result.get("is_admin", False)

        # メソッドベースの権限チェック
        method = request.method.upper()
        permissions = auth_result.get("permissions", [])

        # 読み取り権限チェック
        if method in ["GET", "HEAD", "OPTIONS"]:
            return "read" in permissions or "admin" in permissions

        # 書き込み権限チェック
        if method in ["POST", "PUT", "PATCH", "DELETE"]:
            return "write" in permissions or "admin" in permissions

        # その他のメソッドは管理者のみ
        return "admin" in permissions

    def _set_request_state(self, request: Request, auth_result: Dict[str, Any]) -> None:
        """
        リクエスト状態に認証情報を設定

        Args:
            request: HTTPリクエスト
            auth_result: 認証結果
        """
        request.state.user_id = auth_result.get("user_id")
        request.state.user_name = auth_result.get("user_name")
        request.state.auth_type = auth_result.get("auth_type")
        request.state.permissions = auth_result.get("permissions", [])
        request.state.is_admin = auth_result.get("is_admin", False)
        request.state.authenticated = True

    def _create_auth_error_response(self, auth_result: Dict[str, Any]) -> JSONResponse:
        """
        認証エラーレスポンスを作成

        Args:
            auth_result: 認証結果

        Returns:
            JSONResponse: エラーレスポンス
        """
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "success": False,
                "error": {
                    "code": auth_result.get("error_code", "AUTHENTICATION_FAILED"),
                    "message": auth_result.get("error", "認証に失敗しました"),
                    "type": "authentication_error",
                },
                "timestamp": time.time(),
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    def _create_permission_error_response(self) -> JSONResponse:
        """
        権限エラーレスポンスを作成

        Returns:
            JSONResponse: エラーレスポンス
        """
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "success": False,
                "error": {
                    "code": "INSUFFICIENT_PERMISSIONS",
                    "message": "このリソースにアクセスする権限がありません",
                    "type": "permission_error",
                },
                "timestamp": time.time(),
            },
        )

    def _add_security_headers(self, response: Response) -> None:
        """
        セキュリティヘッダーを追加

        Args:
            response: HTTPレスポンス
        """
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

    def _get_default_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """
        デフォルトAPIキー設定を取得

        Returns:
            Dict[str, Dict[str, Any]]: APIキー設定
        """
        # 実際の実装では環境変数やデータベースから取得
        import os

        default_api_key = os.getenv("DEFAULT_API_KEY", "dev_api_key_12345")

        return {
            default_api_key: {
                "name": "Development API Key",
                "user_id": "dev_user",
                "permissions": ["read", "write", "admin"],
                "is_admin": True,
                "active": True,
                "created_at": time.time(),
                "expires": None,  # 無期限
            }
        }

    def _get_jwt_secret(self) -> str:
        """
        JWT シークレットを取得

        Returns:
            str: JWT シークレット
        """
        import os

        return os.getenv("JWT_SECRET", "development_secret_key_change_in_production")


# 認証ユーティリティ関数


def generate_api_key(length: int = 32) -> str:
    """
    APIキーを生成

    Args:
        length: キー長

    Returns:
        str: 生成されたAPIキー
    """
    import secrets
    import string

    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_api_key(api_key: str, salt: str) -> str:
    """
    APIキーをハッシュ化

    Args:
        api_key: APIキー
        salt: ソルト

    Returns:
        str: ハッシュ化されたキー
    """
    return hashlib.pbkdf2_hex(api_key.encode(), salt.encode(), 100000)


def verify_signature(payload: str, signature: str, secret: str) -> bool:
    """
    HMAC署名を検証

    Args:
        payload: ペイロード
        signature: 署名
        secret: シークレット

    Returns:
        bool: 署名が正しい場合True
    """
    expected_signature = hmac.new(
        secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected_signature)
