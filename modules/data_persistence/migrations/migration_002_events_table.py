#!/usr/bin/env python3
"""
Migration 002: イベントテーブルの作成

イベント駆動アーキテクチャ用のイベントテーブルを作成します。
"""

from datetime import datetime, timezone
from typing import Dict, Any

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager


class Migration002EventsTable:
    """イベントテーブル作成マイグレーション"""
    
    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager
    
    async def up(self):
        """マイグレーション実行"""
        async with self.connection_manager.get_connection() as conn:
            # イベントテーブルの作成
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    event_type VARCHAR(50) NOT NULL,
                    symbol VARCHAR(20) NOT NULL,
                    event_data JSONB NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    processed_at TIMESTAMP WITH TIME ZONE,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0
                )
            """)
            
            # インデックスの作成
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_type_processed 
                ON events (event_type, processed)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_created_at 
                ON events (created_at)
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_symbol 
                ON events (symbol)
            """)
            
            # イベントタイプの列挙型を作成
            await conn.execute("""
                DO $$ BEGIN
                    CREATE TYPE event_type_enum AS ENUM (
                        'data_collection_completed',
                        'technical_analysis_completed',
                        'scenario_created',
                        'scenario_triggered',
                        'scenario_entered',
                        'scenario_exited',
                        'scenario_cancelled',
                        'error_occurred'
                    );
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            """)
            
            print("✅ イベントテーブルとインデックスを作成しました")
    
    async def down(self):
        """マイグレーションロールバック"""
        async with self.connection_manager.get_connection() as conn:
            await conn.execute("DROP TABLE IF EXISTS events CASCADE")
            await conn.execute("DROP TYPE IF EXISTS event_type_enum CASCADE")
            print("✅ イベントテーブルを削除しました")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from modules.data_persistence.config.settings import DatabaseConfig
    
    # データベース接続設定
    db_config = DatabaseConfig()
    connection_string = f"postgresql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
    
    connection_manager = DatabaseConnectionManager(
        connection_string=connection_string,
        min_connections=db_config.min_connections,
        max_connections=db_config.max_connections
    )
    
    try:
        await connection_manager.initialize()
        
        # マイグレーション実行
        migration = Migration002EventsTable(connection_manager)
        await migration.up()
        
        print("✅ マイグレーション完了")
        
    except Exception as e:
        print(f"❌ マイグレーションエラー: {e}")
    finally:
        await connection_manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
