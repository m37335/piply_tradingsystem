"""
Plugins API Routes
プラグイン API ルーター

設計書参照:
- プレゼンテーション層設計_20250809.md

プラグイン管理・設定 API
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter

from ....utils.logging_config import get_presentation_logger

logger = get_presentation_logger()

router = APIRouter()


@router.get("/plugins")
async def get_plugins() -> Dict[str, Any]:
    """
    プラグイン一覧取得

    Returns:
        Dict[str, Any]: プラグイン一覧
    """
    logger.info("Getting plugins list")

    # ダミーデータ
    plugins = [
        {
            "plugin_id": "sma_indicator",
            "name": "Simple Moving Average",
            "type": "technical_indicator",
            "status": "active",
            "version": "1.0.0",
        },
        {
            "plugin_id": "rsi_indicator",
            "name": "RSI Indicator",
            "type": "technical_indicator",
            "status": "active",
            "version": "1.0.0",
        },
    ]

    return {
        "success": True,
        "data": {"plugins": plugins, "total": len(plugins)},
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/plugins/{plugin_id}")
async def get_plugin_info(plugin_id: str) -> Dict[str, Any]:
    """
    プラグイン詳細情報取得

    Args:
        plugin_id: プラグインID

    Returns:
        Dict[str, Any]: プラグイン詳細
    """
    logger.info(f"Getting plugin info: {plugin_id}")

    return {
        "success": True,
        "data": {
            "plugin_id": plugin_id,
            "name": "Sample Plugin",
            "description": "サンプルプラグインです",
            "status": "active",
            "config": {},
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
