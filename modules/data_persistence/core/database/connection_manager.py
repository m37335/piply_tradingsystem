"""
データベース接続管理

PostgreSQLとTimescaleDBの接続管理を提供します。
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

try:
    import asyncpg
    from asyncpg import Pool, Connection
except ImportError:
    asyncpg = None
    Pool = None
    Connection = None

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    psycopg2 = None
    ISOLATION_LEVEL_AUTOCOMMIT = None

logger = logging.getLogger(__name__)


class DatabaseConnectionManager:
    """データベース接続管理"""
    
    def __init__(self, connection_string: str, min_connections: int = 5, max_connections: int = 20):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[Pool] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """接続プールを初期化"""
        async with self._lock:
            if self.pool is not None:
                return
            
            try:
                self.pool = await asyncpg.create_pool(
                    self.connection_string,
                    min_size=self.min_connections,
                    max_size=self.max_connections,
                    command_timeout=60,
                    server_settings={
                        'application_name': 'trading_system',
                        'timezone': 'UTC'
                    }
                )
                logger.info(f"Database connection pool initialized with {self.min_connections}-{self.max_connections} connections")
                
            except Exception as e:
                logger.error(f"Failed to initialize database connection pool: {e}")
                raise
    
    async def close(self) -> None:
        """接続プールを閉じる"""
        async with self._lock:
            if self.pool is not None:
                await self.pool.close()
                self.pool = None
                logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self):
        """データベース接続を取得"""
        if self.pool is None:
            await self.initialize()
        
        connection = await self.pool.acquire()
        try:
            yield connection
        finally:
            await self.pool.release(connection)
    
    async def execute_query(self, query: str, *args) -> Any:
        """クエリを実行"""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_command(self, command: str, *args) -> str:
        """コマンドを実行"""
        async with self.get_connection() as conn:
            return await conn.execute(command, *args)
    
    async def execute_transaction(self, queries: list) -> list:
        """トランザクションでクエリを実行"""
        async with self.get_connection() as conn:
            async with conn.transaction():
                results = []
                for query, args in queries:
                    if query.strip().upper().startswith('SELECT'):
                        result = await conn.fetch(query, *args)
                        results.append(result)
                    else:
                        result = await conn.execute(query, *args)
                        results.append(result)
                return results
    
    async def health_check(self) -> Dict[str, Any]:
        """データベースのヘルスチェック"""
        try:
            async with self.get_connection() as conn:
                # 基本的な接続テスト
                result = await conn.fetchval("SELECT 1")
                
                # 接続プールの状態
                pool_status = {
                    "size": self.pool.get_size(),
                    "min_size": self.pool.get_min_size(),
                    "max_size": self.pool.get_max_size(),
                    "idle_size": self.pool.get_idle_size()
                }
                
                # データベース情報
                db_info = await conn.fetchrow("""
                    SELECT 
                        current_database() as database_name,
                        current_user as user_name,
                        version() as version,
                        now() as current_time
                """)
                
                return {
                    "status": "healthy",
                    "connection_test": result == 1,
                    "pool_status": pool_status,
                    "database_info": dict(db_info)
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def create_database(self, database_name: str) -> None:
        """データベースを作成"""
        # 接続文字列からデータベース名を除いたベース接続文字列を取得
        base_connection_string = self.connection_string.rsplit('/', 1)[0] + '/postgres'
        
        try:
            # 同期接続でデータベース作成
            conn = psycopg2.connect(base_connection_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # データベースが存在するかチェック
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            if not cursor.fetchone():
                cursor.execute(f'CREATE DATABASE "{database_name}"')
                logger.info(f"Database '{database_name}' created successfully")
            else:
                logger.info(f"Database '{database_name}' already exists")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to create database '{database_name}': {e}")
            raise
    
    async def create_timescaledb_extension(self) -> None:
        """TimescaleDB拡張を作成"""
        try:
            await self.execute_command("CREATE EXTENSION IF NOT EXISTS timescaledb")
            logger.info("TimescaleDB extension created successfully")
        except Exception as e:
            logger.error(f"Failed to create TimescaleDB extension: {e}")
            raise
    
    async def create_hypertable(self, table_name: str, time_column: str, partitioning_column: Optional[str] = None) -> None:
        """ハイパーテーブルを作成"""
        try:
            # 既存のハイパーテーブルかチェック
            check_query = """
                SELECT EXISTS (
                    SELECT 1 FROM timescaledb_information.hypertables 
                    WHERE hypertable_name = $1
                )
            """
            async with self.get_connection() as conn:
                is_hypertable = await conn.fetchval(check_query, table_name)
            
            if is_hypertable:
                logger.info(f"Hypertable '{table_name}' already exists, skipping creation")
                return
            
            # ハイパーテーブルを作成
            if partitioning_column:
                query = f"SELECT create_hypertable('{table_name}', '{time_column}', chunk_time_interval => INTERVAL '1 day', partitioning_column => '{partitioning_column}')"
            else:
                query = f"SELECT create_hypertable('{table_name}', '{time_column}', chunk_time_interval => INTERVAL '1 day')"
            
            await self.execute_command(query)
            logger.info(f"Hypertable '{table_name}' created successfully")
        except Exception as e:
            logger.error(f"Failed to create hypertable '{table_name}': {e}")
            raise