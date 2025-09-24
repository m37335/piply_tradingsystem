"""
マイグレーション管理

データベースマイグレーションの実行と管理を提供します。
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from abc import ABC, abstractmethod

from ..core.database.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


@dataclass
class MigrationResult:
    """マイグレーション結果"""
    migration_id: str
    success: bool
    executed_at: datetime
    error_message: Optional[str] = None
    execution_time_seconds: Optional[float] = None


class BaseMigration(ABC):
    """マイグレーションの基底クラス"""
    
    def __init__(self):
        self.migration_id = self.get_migration_id()
        self.description = self.get_description()
    
    @abstractmethod
    def get_migration_id(self) -> str:
        """マイグレーションIDを取得"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """マイグレーションの説明を取得"""
        pass
    
    @abstractmethod
    async def up(self, connection_manager: ConnectionManager) -> None:
        """マイグレーションを実行"""
        pass
    
    @abstractmethod
    async def down(self, connection_manager: ConnectionManager) -> None:
        """マイグレーションをロールバック"""
        pass


class MigrationManager:
    """マイグレーション管理クラス"""
    
    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.migrations: List[BaseMigration] = []
    
    def add_migration(self, migration: BaseMigration) -> None:
        """マイグレーションを追加"""
        self.migrations.append(migration)
        # マイグレーションIDでソート
        self.migrations.sort(key=lambda m: m.migration_id)
    
    async def initialize_migration_table(self) -> None:
        """マイグレーション管理テーブルを作成"""
        query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id SERIAL PRIMARY KEY,
            migration_id VARCHAR(100) NOT NULL UNIQUE,
            description TEXT,
            executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            execution_time_seconds DECIMAL(10, 3),
            success BOOLEAN NOT NULL DEFAULT TRUE,
            error_message TEXT
        );
        
        CREATE INDEX IF NOT EXISTS idx_migrations_migration_id 
        ON migrations (migration_id);
        
        CREATE INDEX IF NOT EXISTS idx_migrations_executed_at 
        ON migrations (executed_at);
        """
        
        await self.connection_manager.execute(query)
        logger.info("Migration table initialized")
    
    async def get_executed_migrations(self) -> List[str]:
        """実行済みマイグレーションのIDリストを取得"""
        query = """
        SELECT migration_id 
        FROM migrations 
        WHERE success = TRUE 
        ORDER BY migration_id
        """
        
        results = await self.connection_manager.fetch(query)
        return [row['migration_id'] for row in results]
    
    async def record_migration(
        self,
        migration: BaseMigration,
        success: bool,
        execution_time: float,
        error_message: Optional[str] = None
    ) -> None:
        """マイグレーション実行結果を記録"""
        query = """
        INSERT INTO migrations (
            migration_id, description, executed_at, execution_time_seconds,
            success, error_message
        ) VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT (migration_id) 
        DO UPDATE SET
            executed_at = EXCLUDED.executed_at,
            execution_time_seconds = EXCLUDED.execution_time_seconds,
            success = EXCLUDED.success,
            error_message = EXCLUDED.error_message
        """
        
        await self.connection_manager.execute(
            query,
            migration.migration_id,
            migration.description,
            datetime.now(),
            execution_time,
            success,
            error_message
        )
    
    async def run_migrations(self, target_migration_id: Optional[str] = None) -> List[MigrationResult]:
        """マイグレーションを実行"""
        logger.info("Starting migration process...")
        
        # マイグレーションテーブルを初期化
        await self.initialize_migration_table()
        
        # 実行済みマイグレーションを取得
        executed_migrations = await self.get_executed_migrations()
        
        results = []
        
        for migration in self.migrations:
            # ターゲットマイグレーションが指定されている場合、それ以降は実行しない
            if target_migration_id and migration.migration_id > target_migration_id:
                break
            
            # 既に実行済みの場合はスキップ
            if migration.migration_id in executed_migrations:
                logger.info(f"Migration {migration.migration_id} already executed, skipping")
                continue
            
            logger.info(f"Running migration: {migration.migration_id} - {migration.description}")
            
            start_time = datetime.now()
            success = True
            error_message = None
            
            try:
                await migration.up(self.connection_manager)
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Migration {migration.migration_id} completed successfully in {execution_time:.3f}s")
                
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                success = False
                error_message = str(e)
                logger.error(f"Migration {migration.migration_id} failed: {e}")
            
            # 結果を記録
            await self.record_migration(migration, success, execution_time, error_message)
            
            # 結果を保存
            result = MigrationResult(
                migration_id=migration.migration_id,
                success=success,
                executed_at=datetime.now(),
                error_message=error_message,
                execution_time_seconds=execution_time
            )
            results.append(result)
            
            # 失敗した場合は停止
            if not success:
                logger.error(f"Migration failed, stopping migration process")
                break
        
        logger.info(f"Migration process completed. {len(results)} migrations processed.")
        return results
    
    async def rollback_migration(self, migration_id: str) -> MigrationResult:
        """マイグレーションをロールバック"""
        logger.info(f"Rolling back migration: {migration_id}")
        
        # マイグレーションを検索
        migration = next((m for m in self.migrations if m.migration_id == migration_id), None)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")
        
        start_time = datetime.now()
        success = True
        error_message = None
        
        try:
            await migration.down(self.connection_manager)
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.info(f"Migration {migration_id} rolled back successfully in {execution_time:.3f}s")
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            success = False
            error_message = str(e)
            logger.error(f"Rollback of migration {migration_id} failed: {e}")
        
        # 結果を記録
        await self.record_migration(migration, success, execution_time, error_message)
        
        return MigrationResult(
            migration_id=migration_id,
            success=success,
            executed_at=datetime.now(),
            error_message=error_message,
            execution_time_seconds=execution_time
        )
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """マイグレーションの状態を取得"""
        query = """
        SELECT 
            migration_id,
            description,
            executed_at,
            execution_time_seconds,
            success,
            error_message
        FROM migrations
        ORDER BY migration_id
        """
        
        results = await self.connection_manager.fetch(query)
        
        return {
            "total_migrations": len(self.migrations),
            "executed_migrations": len(results),
            "pending_migrations": len(self.migrations) - len(results),
            "migration_details": [
                {
                    "migration_id": row['migration_id'],
                    "description": row['description'],
                    "executed_at": row['executed_at'],
                    "execution_time_seconds": row['execution_time_seconds'],
                    "success": row['success'],
                    "error_message": row['error_message']
                }
                for row in results
            ]
        }
