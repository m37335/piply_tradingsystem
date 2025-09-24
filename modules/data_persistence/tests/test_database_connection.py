#!/usr/bin/env python3
"""
データベース接続テスト

データベース接続の動作確認を行います。
"""

import asyncio
import logging
try:
    import pytest
except ImportError:
    pytest = None
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_persistence.config.settings import DatabaseConfig
from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager

# ログ設定
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class TestDatabaseConnection:
    """データベース接続テストクラス"""
    
    @pytest.fixture
    async def connection_manager(self):
        """接続管理のフィクスチャ"""
        config = DatabaseConfig.from_env()
        manager = DatabaseConnectionManager(
            connection_string=config.connection_string,
            min_connections=1,
            max_connections=1
        )
        await manager.initialize()
        yield manager
        await manager.close()
    
    @pytest.mark.asyncio
    async def test_database_connection(self, connection_manager):
        """データベース接続テスト"""
        # 接続プールが初期化されていることを確認
        assert connection_manager.pool is not None
        logger.info("✅ Database connection pool initialized successfully")
    
    @pytest.mark.asyncio
    async def test_health_check(self, connection_manager):
        """ヘルスチェックテスト"""
        health = await connection_manager.health_check()
        assert health is not None
        logger.info(f"✅ Database health check: {health}")
    
    @pytest.mark.asyncio
    async def test_simple_query(self, connection_manager):
        """簡単なクエリテスト"""
        async with connection_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT version()")
            assert result is not None
            logger.info(f"✅ PostgreSQL version: {result}")
    
    @pytest.mark.asyncio
    async def test_timescaledb_extension(self, connection_manager):
        """TimescaleDB拡張の確認"""
        async with connection_manager.get_connection() as conn:
            timescale_version = await conn.fetchval(
                "SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'"
            )
            if timescale_version:
                logger.info(f"✅ TimescaleDB version: {timescale_version}")
            else:
                logger.warning("⚠️ TimescaleDB extension not found")
    
    @pytest.mark.asyncio
    async def test_database_config(self):
        """データベース設定テスト"""
        config = DatabaseConfig.from_env()
        
        # 設定値の確認
        assert config.host is not None
        assert config.port > 0
        assert config.database is not None
        assert config.username is not None
        assert config.password is not None
        
        # 接続文字列の確認
        connection_string = config.connection_string
        assert "postgresql://" in connection_string
        assert config.host in connection_string
        assert str(config.port) in connection_string
        assert config.database in connection_string
        
        logger.info(f"✅ Database config: {config.host}:{config.port}/{config.database}")


async def main():
    """メイン関数（直接実行用）"""
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
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
