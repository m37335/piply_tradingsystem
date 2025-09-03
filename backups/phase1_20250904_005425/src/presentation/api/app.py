"""
FastAPI Application
FastAPI アプリケーション

設計書参照:
- プレゼンテーション層設計_20250809.md

Exchange Analytics REST API のメインアプリケーション
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from ...container import Container
from ...utils.logging_config import get_presentation_logger, setup_logging_directories
from .middleware.auth import AuthMiddleware
from .middleware.error_handler import ErrorHandlerMiddleware
from .middleware.rate_limit import RateLimitMiddleware
from .routes import ai_reports, alerts, analysis, health, plugins, rates

logger = get_presentation_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    アプリケーション起動・終了時の処理

    Args:
        app: FastAPIアプリケーション
    """
    # 起動時処理
    logger.info("🚀 Starting Exchange Analytics API...")

    try:
        # ログディレクトリの作成
        setup_logging_directories()

        # DIコンテナの初期化
        container = Container()
        container.wire(packages=["src.presentation.api"])
        app.container = container

        # Infrastructure Layer サービスの初期化
        # database_manager = container.database_manager()
        # await database_manager.initialize()

        logger.info("✅ Exchange Analytics API started successfully")

        yield

    except Exception as e:
        logger.error(f"❌ Failed to start API: {str(e)}")
        raise
    finally:
        # 終了時処理
        logger.info("🛑 Shutting down Exchange Analytics API...")

        # Infrastructure サービスのクリーンアップ
        try:
            if hasattr(app, "container"):
                # await app.container.database_manager().close()
                pass
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")

        logger.info("✅ Exchange Analytics API shutdown complete")


def create_app() -> FastAPI:
    """
    FastAPI アプリケーションを作成

    Returns:
        FastAPI: 設定済みのFastAPIアプリケーション
    """
    app = FastAPI(
        title="Exchange Analytics API",
        description="通貨分析システム - ChatGPT統合・Discord通知対応",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        # 本番環境では docs_url=None にしてSwagger UIを無効化
    )

    # ミドルウェアの設定
    setup_middleware(app)

    # ルーターの登録
    setup_routes(app)

    return app


def setup_middleware(app: FastAPI) -> None:
    """
    ミドルウェアを設定

    Args:
        app: FastAPIアプリケーション
    """
    # トラステッドホストミドルウェア（本番環境用）
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])  # 本番環境では具体的なホストを指定

    # CORS ミドルウェア
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 本番環境では具体的なオリジンを指定
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # カスタムミドルウェア
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)

    # リクエスト/レスポンス ログミドルウェア
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        """リクエスト/レスポンス ログミドルウェア"""
        start_time = time.time()

        # リクエスト情報をログ
        logger.info(
            f"📨 {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # リクエスト処理
        try:
            response = await call_next(request)

            # 処理時間計算
            process_time = time.time() - start_time

            # レスポンス情報をログ
            logger.info(
                f"📤 {request.method} {request.url.path} - "
                f"Status: {response.status_code} - "
                f"Time: {process_time:.3f}s"
            )

            # レスポンスヘッダーに処理時間を追加
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"❌ {request.method} {request.url.path} - "
                f"Error: {str(e)} - Time: {process_time:.3f}s"
            )
            raise


def setup_routes(app: FastAPI) -> None:
    """
    API ルーターを設定

    Args:
        app: FastAPIアプリケーション
    """
    # メインルーターを登録
    app.include_router(health.router, prefix="/api/v1", tags=["health"])

    app.include_router(rates.router, prefix="/api/v1", tags=["rates"])

    app.include_router(analysis.router, prefix="/api/v1", tags=["analysis"])

    app.include_router(ai_reports.router, prefix="/api/v1", tags=["ai_reports"])

    app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])

    app.include_router(plugins.router, prefix="/api/v1", tags=["plugins"])

    # ルートエンドポイント
    @app.get("/", response_class=JSONResponse)
    async def root() -> Dict[str, Any]:
        """
        API ルートエンドポイント

        Returns:
            Dict[str, Any]: API情報
        """
        return {
            "name": "Exchange Analytics API",
            "version": "1.0.0",
            "description": "通貨分析システム - ChatGPT統合・Discord通知対応",
            "docs_url": "/docs",
            "redoc_url": "/redoc",
            "openapi_url": "/openapi.json",
            "status": "running",
            "timestamp": time.time(),
        }

    # API情報エンドポイント
    @app.get("/api", response_class=JSONResponse)
    async def api_info() -> Dict[str, Any]:
        """
        API 情報エンドポイント

        Returns:
            Dict[str, Any]: 詳細API情報
        """
        return {
            "api_version": "v1",
            "endpoints": {
                "health": "/api/v1/health",
                "rates": "/api/v1/rates",
                "analysis": "/api/v1/analysis",
                "ai_reports": "/api/v1/ai-reports",
                "alerts": "/api/v1/alerts",
                "plugins": "/api/v1/plugins",
            },
            "features": [
                "Exchange rate data fetching",
                "AI-powered market analysis",
                "Discord notifications",
                "Technical indicators",
                "Alert management",
                "Plugin system",
            ],
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_schema": "/openapi.json",
            },
        }


# アプリケーションインスタンスを作成
app = create_app()


# 開発サーバー用エントリーポイント
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting development server...")

    uvicorn.run(
        "src.presentation.api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
    )
