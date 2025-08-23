#!/usr/bin/env python3
"""
SQLite to PostgreSQL Migration Script
SQLiteからPostgreSQLへのデータ移行スクリプト

使用方法:
    python scripts/migration/sqlite_to_postgresql_migration.py
"""

import asyncio
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.connection import DatabaseManager
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class SQLiteToPostgreSQLMigration:
    """SQLiteからPostgreSQLへのデータ移行クラス"""

    def __init__(self, sqlite_path: str, postgresql_url: str):
        self.sqlite_path = sqlite_path
        self.postgresql_url = postgresql_url
        self.sqlite_conn = None
        self.postgresql_pool = None

    async def initialize(self):
        """初期化"""
        # SQLite接続
        self.sqlite_conn = sqlite3.connect(self.sqlite_path)
        self.sqlite_conn.row_factory = sqlite3.Row

        # PostgreSQL接続プール
        self.postgresql_pool = await asyncpg.create_pool(
            host="localhost",
            port=5432,
            database="exchange_analytics_production_db",
            user="exchange_analytics_user",
            password="exchange_password",
        )

        logger.info("データベース接続を初期化しました")

    async def close(self):
        """接続を閉じる"""
        if self.sqlite_conn:
            self.sqlite_conn.close()
        if self.postgresql_pool:
            await self.postgresql_pool.close()

    def get_sqlite_tables(self) -> List[str]:
        """SQLiteのテーブル一覧を取得"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables

    async def get_postgresql_tables(self) -> List[str]:
        """PostgreSQLのテーブル一覧を取得"""
        async with self.postgresql_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
            return [row['table_name'] for row in rows]

    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """テーブルのスキーマ情報を取得"""
        cursor = self.sqlite_conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = []
        for row in cursor.fetchall():
            columns.append({
                'name': row[1],
                'type': row[2],
                'notnull': bool(row[3]),
                'default': row[4],
                'pk': bool(row[5])
            })
        cursor.close()
        return columns

    def get_table_data(self, table_name: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """テーブルのデータを取得"""
        cursor = self.sqlite_conn.cursor()
        
        if limit:
            cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
        else:
            cursor.execute(f"SELECT * FROM {table_name}")
        
        rows = cursor.fetchall()
        data = []
        for row in rows:
            row_dict = {}
            for i, column in enumerate(row.keys()):
                value = row[i]
                # JSON文字列の場合はパース
                if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                # 日時文字列の場合はdatetimeオブジェクトに変換
                elif isinstance(value, str) and ' ' in value and ':' in value:
                    try:
                        from datetime import datetime
                        # SQLiteの日時形式を解析
                        if '.' in value:  # マイクロ秒付き
                            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
                        else:  # マイクロ秒なし
                            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        pass  # 変換できない場合はそのまま
                row_dict[column] = value
            data.append(row_dict)
        
        cursor.close()
        return data

    async def migrate_table(self, table_name: str, batch_size: int = 1000) -> int:
        """テーブルを移行"""
        logger.info(f"テーブル {table_name} の移行を開始...")

        # データを取得
        data = self.get_table_data(table_name)
        total_rows = len(data)
        
        if total_rows == 0:
            logger.info(f"テーブル {table_name} は空です")
            return 0

        # バッチ処理で挿入
        migrated_count = 0
        for i in range(0, total_rows, batch_size):
            batch = data[i:i + batch_size]
            
            try:
                await self._insert_batch(table_name, batch)
                migrated_count += len(batch)
                logger.info(f"テーブル {table_name}: {migrated_count}/{total_rows} 件移行完了")
            except Exception as e:
                logger.error(f"テーブル {table_name} のバッチ挿入エラー: {e}")
                raise

        logger.info(f"テーブル {table_name} の移行完了: {migrated_count} 件")
        return migrated_count

    async def _insert_batch(self, table_name: str, batch: List[Dict[str, Any]]):
        """バッチデータを挿入"""
        if not batch:
            return

        # カラム名を取得
        columns = list(batch[0].keys())
        placeholders = [f"${i+1}" for i in range(len(columns))]
        
        # INSERT文を作成
        query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON CONFLICT DO NOTHING
        """

        async with self.postgresql_pool.acquire() as conn:
            # バッチデータを準備
            values = []
            for row in batch:
                row_values = []
                for column in columns:
                    value = row.get(column)
                    # JSONデータの場合は文字列化
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value)
                    row_values.append(value)
                values.append(row_values)

            # バッチ挿入実行
            await conn.executemany(query, values)

    async def migrate_all_tables(self) -> Dict[str, int]:
        """全テーブルを移行"""
        logger.info("データ移行を開始します...")

        # テーブル一覧を取得
        sqlite_tables = self.get_sqlite_tables()
        postgresql_tables = await self.get_postgresql_tables()

        logger.info(f"SQLiteテーブル: {sqlite_tables}")
        logger.info(f"PostgreSQLテーブル: {postgresql_tables}")

        # 共通のテーブルを移行
        common_tables = set(sqlite_tables) & set(postgresql_tables)
        migration_results = {}

        for table_name in sorted(common_tables):
            try:
                count = await self.migrate_table(table_name)
                migration_results[table_name] = count
            except Exception as e:
                logger.error(f"テーブル {table_name} の移行に失敗: {e}")
                migration_results[table_name] = 0

        return migration_results

    async def verify_migration(self) -> Dict[str, Dict[str, int]]:
        """移行結果を検証"""
        logger.info("移行結果を検証します...")

        sqlite_tables = self.get_sqlite_tables()
        postgresql_tables = await self.get_postgresql_tables()
        common_tables = set(sqlite_tables) & set(postgresql_tables)

        verification_results = {}

        for table_name in sorted(common_tables):
            # SQLiteの行数を取得
            cursor = self.sqlite_conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            sqlite_count = cursor.fetchone()[0]
            cursor.close()

            # PostgreSQLの行数を取得
            async with self.postgresql_pool.acquire() as conn:
                postgresql_count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")

            verification_results[table_name] = {
                'sqlite_count': sqlite_count,
                'postgresql_count': postgresql_count,
                'match': sqlite_count == postgresql_count
            }

            logger.info(f"テーブル {table_name}: SQLite={sqlite_count}, PostgreSQL={postgresql_count}, 一致={sqlite_count == postgresql_count}")

        return verification_results


async def main():
    """メイン関数"""
    # 設定
    sqlite_path = "/app/data/exchange_analytics.db"
    postgresql_url = "postgresql+asyncpg://exchange_analytics_user:exchange_password@localhost:5432/exchange_analytics_production_db"

    # 移行クラスのインスタンスを作成
    migration = SQLiteToPostgreSQLMigration(sqlite_path, postgresql_url)

    try:
        # 初期化
        await migration.initialize()

        # 移行実行
        results = await migration.migrate_all_tables()

        # 結果表示
        logger.info("=== 移行結果 ===")
        total_migrated = 0
        for table_name, count in results.items():
            logger.info(f"{table_name}: {count} 件")
            total_migrated += count

        logger.info(f"総移行件数: {total_migrated} 件")

        # 検証
        verification = await migration.verify_migration()
        
        logger.info("=== 検証結果 ===")
        all_match = True
        for table_name, result in verification.items():
            status = "✅" if result['match'] else "❌"
            logger.info(f"{status} {table_name}: SQLite={result['sqlite_count']}, PostgreSQL={result['postgresql_count']}")
            if not result['match']:
                all_match = False

        if all_match:
            logger.info("🎉 全てのテーブルで移行が成功しました！")
        else:
            logger.warning("⚠️ 一部のテーブルで移行に問題があります")

    except Exception as e:
        logger.error(f"移行中にエラーが発生しました: {e}")
        raise
    finally:
        await migration.close()


if __name__ == "__main__":
    asyncio.run(main())
