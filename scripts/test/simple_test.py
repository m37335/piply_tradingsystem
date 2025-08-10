#!/usr/bin/env python3
"""
シンプルなテストスクリプト
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.infrastructure.database.connection import get_async_session
from src.infrastructure.database.services.pattern_detection_service import (
    PatternDetectionService,
)
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


async def test_pattern_detection():
    """パターン検出をテスト"""
    try:
        # データベースセッションを取得
        session = await get_async_session()

        # パターン検出サービスを初期化
        pattern_service = PatternDetectionService(session)

        print("Testing pattern detection...")

        # パターン検出を実行
        patterns = await pattern_service.detect_all_patterns()

        print(f"Pattern detection completed. Found {len(patterns)} pattern types")

        for pattern_type, pattern_list in patterns.items():
            print(f"Pattern type {pattern_type}: {len(pattern_list)} patterns")

        await session.close()

    except Exception as e:
        logger.error(f"Pattern detection test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 環境変数を設定
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_app.db"

    asyncio.run(test_pattern_detection())
