#!/usr/bin/env python3
"""
データベース初期化スクリプト

データベースの初期セットアップを実行します。
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_persistence.config.settings import DataPersistenceSettings
from modules.data_persistence.core.database.connection_manager import (
    DatabaseConnectionManager,
)
from modules.data_persistence.core.database.database_initializer import (
    DatabaseInitializer,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """メイン関数"""
    try:
        # 設定を読み込み
        settings = DataPersistenceSettings.from_env()
        logger.info(f"Initializing database: {settings.database.database}")

        # 接続管理を初期化
        connection_manager = DatabaseConnectionManager(
            connection_string=settings.database.connection_string,
            min_connections=settings.database.min_connections,
            max_connections=settings.database.max_connections,
        )

        # データベース初期化
        initializer = DatabaseInitializer(connection_manager)
        await initializer.initialize_database(settings.database.database)

        # ヘルスチェック
        health = await connection_manager.health_check()
        logger.info(f"Database health check: {health}")

        logger.info("Database initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)

    finally:
        # 接続を閉じる
        if "connection_manager" in locals():
            await connection_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
