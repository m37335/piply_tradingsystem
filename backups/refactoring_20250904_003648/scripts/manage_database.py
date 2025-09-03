#!/usr/bin/env python3
"""
データベース管理スクリプト
Alembicマイグレーションとデータベース操作を管理
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config.database import DatabaseConfig, ConnectionManager


def run_alembic_command(command: str, *args) -> int:
    """Alembicコマンドを実行"""
    alembic_ini = project_root / "src/infrastructure/database/migrations/alembic.ini"
    cmd = ["alembic", "-c", str(alembic_ini), command] + list(args)
    
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=project_root).returncode


def create_migration(message: str) -> int:
    """新しいマイグレーションを作成"""
    return run_alembic_command("revision", "--autogenerate", "-m", message)


def upgrade_database(revision: str = "head") -> int:
    """データベースをアップグレード"""
    return run_alembic_command("upgrade", revision)


def downgrade_database(revision: str) -> int:
    """データベースをダウングレード"""
    return run_alembic_command("downgrade", revision)


def show_current_revision() -> int:
    """現在のリビジョンを表示"""
    return run_alembic_command("current")


def show_history() -> int:
    """マイグレーション履歴を表示"""
    return run_alembic_command("history")


def test_connection() -> bool:
    """データベース接続をテスト"""
    try:
        config = DatabaseConfig()
        manager = ConnectionManager(config)
        
        print("Testing database connection...")
        print(f"Config: {config}")
        
        if manager.test_connection():
            print("✅ Database connection successful!")
            return True
        else:
            print("❌ Database connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def create_database() -> bool:
    """データベースを作成（PostgreSQL管理用）"""
    try:
        config = DatabaseConfig()
        
        # 管理用データベース（postgres）に接続してデータベースを作成
        admin_config = DatabaseConfig()
        admin_config.database = "postgres"
        admin_manager = ConnectionManager(admin_config)
        
        with admin_manager.get_session() as session:
            # データベースの存在確認
            result = session.execute(
                f"SELECT 1 FROM pg_database WHERE datname = '{config.database}'"
            )
            
            if result.fetchone():
                print(f"Database '{config.database}' already exists")
                return True
            
            # データベース作成
            session.execute(f"CREATE DATABASE {config.database}")
            print(f"✅ Database '{config.database}' created successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False


def drop_database() -> bool:
    """データベースを削除（注意：全データが失われます）"""
    try:
        config = DatabaseConfig()
        
        # 確認
        response = input(f"Are you sure you want to drop database '{config.database}'? (yes/no): ")
        if response.lower() != 'yes':
            print("Operation cancelled")
            return False
        
        # 管理用データベース（postgres）に接続してデータベースを削除
        admin_config = DatabaseConfig()
        admin_config.database = "postgres"
        admin_manager = ConnectionManager(admin_config)
        
        with admin_manager.get_session() as session:
            # アクティブな接続を終了
            session.execute(
                f"SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                f"WHERE datname = '{config.database}' AND pid <> pg_backend_pid()"
            )
            
            # データベース削除
            session.execute(f"DROP DATABASE IF EXISTS {config.database}")
            print(f"✅ Database '{config.database}' dropped successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Failed to drop database: {e}")
        return False


def setup_database() -> bool:
    """データベースの初期セットアップ"""
    print("Setting up database...")
    
    # 1. データベース作成
    if not create_database():
        return False
    
    # 2. 接続テスト
    if not test_connection():
        return False
    
    # 3. マイグレーション実行
    print("Running migrations...")
    if upgrade_database() != 0:
        print("❌ Migration failed!")
        return False
    
    print("✅ Database setup completed successfully!")
    return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="Database management script")
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # マイグレーション関連
    migration_parser = subparsers.add_parser("create", help="Create a new migration")
    migration_parser.add_argument("message", help="Migration message")
    
    subparsers.add_parser("upgrade", help="Upgrade database")
    
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument("revision", help="Target revision")
    
    subparsers.add_parser("current", help="Show current revision")
    subparsers.add_parser("history", help="Show migration history")
    
    # データベース管理
    subparsers.add_parser("test", help="Test database connection")
    subparsers.add_parser("create-db", help="Create database")
    subparsers.add_parser("drop-db", help="Drop database")
    subparsers.add_parser("setup", help="Setup database (create + migrate)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # コマンド実行
    try:
        if args.command == "create":
            return create_migration(args.message)
        elif args.command == "upgrade":
            return upgrade_database()
        elif args.command == "downgrade":
            return downgrade_database(args.revision)
        elif args.command == "current":
            return show_current_revision()
        elif args.command == "history":
            return show_history()
        elif args.command == "test":
            return 0 if test_connection() else 1
        elif args.command == "create-db":
            return 0 if create_database() else 1
        elif args.command == "drop-db":
            return 0 if drop_database() else 1
        elif args.command == "setup":
            return 0 if setup_database() else 1
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
