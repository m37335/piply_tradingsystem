#!/usr/bin/env python3
"""
データベース接続テストスクリプト
"""

import asyncio
import logging
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent))

from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager

# ログ設定
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_database_connection():
    """データベース接続テスト"""
    try:
        # 設定を読み込み
        config = DatabaseConfig.from_env()
        logger.info(f"Testing connection to: {config.host}:{config.port}/{config.database}")
        logger.info(f"Connection string: {config.connection_string}")
        
        # 接続管理を初期化
        connection_manager = DatabaseConnectionManager(
            connection_string=config.connection_string,
            min_connections=1,
            max_connections=1
        )
        
        # 接続プールを初期化
        await connection_manager.initialize()
        logger.info("✅ Database connection pool initialized successfully")
        
        # ヘルスチェック
        health = await connection_manager.health_check()
        logger.info(f"✅ Database health check: {health}")
        
        # 簡単なクエリテスト
        async with connection_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT version()")
            logger.info(f"✅ PostgreSQL version: {result}")
            
            # TimescaleDB拡張の確認
            timescale_version = await conn.fetchval(
                "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
            )
            if timescale_version:
                logger.info(f"✅ TimescaleDB version: {timescale_version}")
            else:
                logger.warning("⚠️ TimescaleDB extension not found")
        
        logger.info("🎉 Database connection test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False
        
    finally:
        # 接続を閉じる
        if "connection_manager" in locals():
            await connection_manager.close()


if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    sys.exit(0 if success else 1)
