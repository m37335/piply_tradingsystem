"""
Health Check API Routes
ヘルスチェック API ルーター

設計書参照:
- プレゼンテーション層設計_20250809.md

システムヘルスチェックとモニタリング API
"""

import asyncio
import time
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    基本ヘルスチェック

    Returns:
        Dict[str, Any]: ヘルスチェック結果
    """
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "service": "exchange-analytics-api",
    }


@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """
    詳細ヘルスチェック

    Returns:
        Dict[str, Any]: 詳細ヘルスチェック結果
    """
    start_time = time.time()

    # 各コンポーネントのヘルスチェック
    checks = {
        "database": await _check_database_health(),
        "redis": await _check_redis_health(),
        "external_apis": await _check_external_apis_health(),
        "disk_space": await _check_disk_space(),
        "memory": await _check_memory_usage(),
    }

    # 全体のステータス判定
    overall_status = "healthy"
    if any(check["status"] == "unhealthy" for check in checks.values()):
        overall_status = "unhealthy"
    elif any(check["status"] == "degraded" for check in checks.values()):
        overall_status = "degraded"

    response_time = time.time() - start_time

    result = {
        "status": overall_status,
        "timestamp": time.time(),
        "response_time_ms": round(response_time * 1000, 2),
        "version": "1.0.0",
        "service": "exchange-analytics-api",
        "checks": checks,
    }

    # 異常時は適切なHTTPステータスコードを返す
    if overall_status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=result
        )
    elif overall_status == "degraded":
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=result,
            headers={"X-Health-Warning": "Service degraded"},
        )

    return result


@router.get("/health/readiness")
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness プローブ（Kubernetes用）

    Returns:
        Dict[str, Any]: Readiness チェック結果
    """
    # 必須サービスの準備状況をチェック
    checks = {
        "database": await _check_database_connection(),
        "required_configs": await _check_required_configs(),
        "dependencies": await _check_critical_dependencies(),
    }

    ready = all(check["ready"] for check in checks.values())

    result = {"ready": ready, "timestamp": time.time(), "checks": checks}

    if not ready:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=result
        )

    return result


@router.get("/health/liveness")
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness プローブ（Kubernetes用）

    Returns:
        Dict[str, Any]: Liveness チェック結果
    """
    # アプリケーションが生きているかの基本チェック
    try:
        # 簡単な処理を実行してアプリが応答できることを確認
        test_start = time.time()
        await asyncio.sleep(0.001)  # 1ms待機
        test_duration = time.time() - test_start

        result = {
            "alive": True,
            "timestamp": time.time(),
            "response_time_ms": round(test_duration * 1000, 2),
        }

        return result

    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"alive": False, "timestamp": time.time(), "error": str(e)},
        )


@router.get("/health/metrics")
async def health_metrics() -> Dict[str, Any]:
    """
    ヘルスメトリクス取得

    Returns:
        Dict[str, Any]: システムメトリクス
    """
    import os

    import psutil

    # システムメトリクス
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    # プロセスメトリクス
    process = psutil.Process(os.getpid())
    process_memory = process.memory_info()

    return {
        "timestamp": time.time(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used,
                "free": memory.free,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100,
            },
        },
        "process": {
            "pid": os.getpid(),
            "memory": {"rss": process_memory.rss, "vms": process_memory.vms},
            "cpu_percent": process.cpu_percent(),
            "num_threads": process.num_threads(),
            "create_time": process.create_time(),
        },
    }


# 内部ヘルパー関数


async def _check_database_health() -> Dict[str, Any]:
    """データベースヘルスチェック"""
    try:
        # TODO: 実際のデータベース接続テスト
        # from ....infrastructure.database.connection import db_manager
        # health = await db_manager.health_check()

        # ダミー実装
        await asyncio.sleep(0.01)  # DB接続をシミュレート

        return {
            "status": "healthy",
            "response_time_ms": 10,
            "connection_pool": {"active": 5, "idle": 10, "total": 15},
        }

    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_redis_health() -> Dict[str, Any]:
    """Redisヘルスチェック"""
    try:
        # TODO: 実際のRedis接続テスト
        # from ....infrastructure.cache.redis_client import redis_client
        # health = await redis_client.ping()

        # ダミー実装
        await asyncio.sleep(0.005)  # Redis接続をシミュレート

        return {"status": "healthy", "response_time_ms": 5, "connected": True}

    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {"status": "degraded", "error": str(e)}


async def _check_external_apis_health() -> Dict[str, Any]:
    """外部APIヘルスチェック"""
    try:
        # TODO: 実際の外部API接続テスト
        # Alpha Vantage, OpenAI などの接続確認

        # ダミー実装
        await asyncio.sleep(0.02)  # 外部API接続をシミュレート

        return {
            "status": "healthy",
            "apis": {
                "alpha_vantage": {"status": "healthy", "response_time_ms": 150},
                "openai": {"status": "healthy", "response_time_ms": 200},
                "discord": {"status": "healthy", "response_time_ms": 100},
            },
        }

    except Exception as e:
        logger.error(f"External APIs health check failed: {str(e)}")
        return {"status": "degraded", "error": str(e)}


async def _check_disk_space() -> Dict[str, Any]:
    """ディスク容量チェック"""
    try:
        import psutil

        disk = psutil.disk_usage("/")
        usage_percent = (disk.used / disk.total) * 100

        status = "healthy"
        if usage_percent > 90:
            status = "unhealthy"
        elif usage_percent > 80:
            status = "degraded"

        return {
            "status": status,
            "usage_percent": round(usage_percent, 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "total_gb": round(disk.total / (1024**3), 2),
        }

    except Exception as e:
        logger.error(f"Disk space check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_memory_usage() -> Dict[str, Any]:
    """メモリ使用量チェック"""
    try:
        import psutil

        memory = psutil.virtual_memory()
        usage_percent = memory.percent

        status = "healthy"
        if usage_percent > 90:
            status = "unhealthy"
        elif usage_percent > 80:
            status = "degraded"

        return {
            "status": status,
            "usage_percent": usage_percent,
            "available_gb": round(memory.available / (1024**3), 2),
            "total_gb": round(memory.total / (1024**3), 2),
        }

    except Exception as e:
        logger.error(f"Memory usage check failed: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}


async def _check_database_connection() -> Dict[str, Any]:
    """データベース接続チェック"""
    try:
        # TODO: 実際のデータベース接続確認
        await asyncio.sleep(0.01)

        return {"ready": True, "response_time_ms": 10}

    except Exception as e:
        return {"ready": False, "error": str(e)}


async def _check_required_configs() -> Dict[str, Any]:
    """必須設定チェック"""
    try:
        import os

        # 必須環境変数のチェック
        required_configs = [
            "DATABASE_URL",
            "REDIS_URL",
            # "ALPHA_VANTAGE_API_KEY",
            # "OPENAI_API_KEY"
        ]

        missing_configs = []
        for config in required_configs:
            if not os.getenv(config):
                missing_configs.append(config)

        ready = len(missing_configs) == 0

        result = {
            "ready": ready,
            "checked_configs": len(required_configs),
            "missing_configs": missing_configs,
        }

        if not ready:
            result[
                "error"
            ] = f"Missing required configurations: {', '.join(missing_configs)}"

        return result

    except Exception as e:
        return {"ready": False, "error": str(e)}


async def _check_critical_dependencies() -> Dict[str, Any]:
    """重要な依存関係チェック"""
    try:
        # 重要なPythonパッケージの存在確認
        critical_packages = ["fastapi", "sqlalchemy", "redis", "httpx"]

        missing_packages = []
        for package in critical_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)

        ready = len(missing_packages) == 0

        result = {
            "ready": ready,
            "checked_packages": len(critical_packages),
            "missing_packages": missing_packages,
        }

        if not ready:
            result[
                "error"
            ] = f"Missing critical packages: {', '.join(missing_packages)}"

        return result

    except Exception as e:
        return {"ready": False, "error": str(e)}
