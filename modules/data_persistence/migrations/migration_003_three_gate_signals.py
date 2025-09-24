#!/usr/bin/env python3
"""
三層ゲートシグナルテーブル作成マイグレーション
"""

import sys
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from modules.data_persistence.core.database.connection_manager import DatabaseConnectionManager
from modules.data_persistence.config.settings import DatabaseConfig


class Migration003ThreeGateSignals:
    """三層ゲートシグナルテーブル作成マイグレーション"""
    
    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager

    async def up(self):
        """三層ゲートシグナルテーブルを作成"""
        async with self.connection_manager.get_connection() as conn:
            # 三層ゲートシグナルテーブルの作成
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS three_gate_signals (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    signal_type VARCHAR(10) NOT NULL,
                    overall_confidence DECIMAL(5,4) NOT NULL,
                    entry_price DECIMAL(20,8) NOT NULL,
                    stop_loss DECIMAL(20,8) NOT NULL,
                    take_profit JSONB NOT NULL,
                    gate1_pattern VARCHAR(100) NOT NULL,
                    gate1_confidence DECIMAL(5,4) NOT NULL,
                    gate2_pattern VARCHAR(100) NOT NULL,
                    gate2_confidence DECIMAL(5,4) NOT NULL,
                    gate3_pattern VARCHAR(100) NOT NULL,
                    gate3_confidence DECIMAL(5,4) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # インデックスの作成
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_three_gate_signals_symbol_created 
                ON three_gate_signals (symbol, created_at DESC);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_three_gate_signals_signal_type 
                ON three_gate_signals (signal_type);
            """)
            
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_three_gate_signals_confidence 
                ON three_gate_signals (overall_confidence DESC);
            """)
            
            print("✅ 三層ゲートシグナルテーブルとインデックスを作成しました")

    async def down(self):
        """三層ゲートシグナルテーブルを削除"""
        async with self.connection_manager.get_connection() as conn:
            await conn.execute("DROP TABLE IF EXISTS three_gate_signals CASCADE")
            print("✅ 三層ゲートシグナルテーブルを削除しました")


async def main():
    """テスト用のメイン関数"""
    db_config = DatabaseConfig()
    connection_string = f"postgresql://{db_config.username}:{db_config.password}@{db_config.host}:{db_config.port}/{db_config.database}"
    connection_manager = DatabaseConnectionManager(connection_string=connection_string)
    await connection_manager.initialize()
    
    migration = Migration003ThreeGateSignals(connection_manager)
    await migration.up()
    # await migration.down() # 必要に応じてダウンもテスト
    
    await connection_manager.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
