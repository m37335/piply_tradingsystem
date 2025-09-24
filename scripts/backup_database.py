#!/usr/bin/env python3
"""
データベースバックアップスクリプト
PostgreSQL/TimescaleDBのバックアップを作成
"""

import asyncio
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from modules.data_persistence.config.settings import DatabaseConfig

class DatabaseBackup:
    """データベースバックアップクラス"""
    
    def __init__(self):
        self.db_config = DatabaseConfig.from_env()
        self.backup_dir = Path("/app/backups/database")
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def create_backup_filename(self, backup_type="manual"):
        """バックアップファイル名を生成"""
        return f"trading_system_{backup_type}_{self.timestamp}.sql"
    
    def get_backup_path(self, backup_type="manual"):
        """バックアップファイルのパスを取得"""
        filename = self.create_backup_filename(backup_type)
        backup_subdir = self.backup_dir / backup_type
        backup_subdir.mkdir(parents=True, exist_ok=True)
        return backup_subdir / filename
    
    def create_pg_dump_command(self, output_path):
        """pg_dumpコマンドを生成"""
        # 環境変数でパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config.password
        
        # pg_dumpコマンド
        cmd = [
            'pg_dump',
            '-h', self.db_config.host,
            '-p', str(self.db_config.port),
            '-U', self.db_config.username,
            '-d', self.db_config.database,
            '--verbose',
            '--clean',
            '--create',
            '--if-exists',
            '--format=custom',
            '--compress=9',
            '--file', str(output_path)
        ]
        
        return cmd, env
    
    def create_sql_dump_command(self, output_path):
        """SQLダンプコマンドを生成"""
        # 環境変数でパスワードを設定
        env = os.environ.copy()
        env['PGPASSWORD'] = self.db_config.password
        
        # pg_dumpコマンド（SQL形式）
        cmd = [
            'pg_dump',
            '-h', self.db_config.host,
            '-p', str(self.db_config.port),
            '-U', self.db_config.username,
            '-d', self.db_config.database,
            '--verbose',
            '--clean',
            '--create',
            '--if-exists',
            '--format=plain',
            '--file', str(output_path)
        ]
        
        return cmd, env
    
    def run_backup(self, backup_type="manual", format_type="custom"):
        """バックアップを実行"""
        print(f"🚀 データベースバックアップ開始 ({backup_type})")
        print(f"📅 タイムスタンプ: {self.timestamp}")
        print("=" * 80)
        
        # バックアップファイルパスを生成
        if format_type == "custom":
            output_path = self.get_backup_path(backup_type).with_suffix('.dump')
            cmd, env = self.create_pg_dump_command(output_path)
        else:
            output_path = self.get_backup_path(backup_type).with_suffix('.sql')
            cmd, env = self.create_sql_dump_command(output_path)
        
        print(f"📁 バックアップ先: {output_path}")
        print(f"🔧 コマンド: {' '.join(cmd[:-2])}")  # ファイルパスを除く
        
        try:
            # バックアップ実行
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            # ファイルサイズを確認
            file_size = output_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"✅ バックアップ完了!")
            print(f"📊 ファイルサイズ: {file_size_mb:.2f} MB")
            print(f"📁 保存先: {output_path}")
            
            # バックアップ情報をログに記録
            self.log_backup_info(output_path, file_size_mb, backup_type)
            
            return {
                'success': True,
                'file_path': str(output_path),
                'file_size_mb': file_size_mb,
                'backup_type': backup_type,
                'timestamp': self.timestamp
            }
            
        except subprocess.CalledProcessError as e:
            print(f"❌ バックアップエラー: {e}")
            print(f"📝 エラー出力: {e.stderr}")
            return {
                'success': False,
                'error': str(e),
                'stderr': e.stderr
            }
    
    def log_backup_info(self, file_path, file_size_mb, backup_type):
        """バックアップ情報をログに記録"""
        log_file = self.backup_dir / "backup_log.txt"
        
        log_entry = f"{self.timestamp} | {backup_type} | {file_path} | {file_size_mb:.2f}MB\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
    
    def list_backups(self, backup_type=None):
        """バックアップファイル一覧を表示"""
        print("📋 バックアップファイル一覧")
        print("=" * 80)
        
        if backup_type:
            backup_dirs = [self.backup_dir / backup_type]
        else:
            backup_dirs = [
                self.backup_dir / "manual",
                self.backup_dir / "daily",
                self.backup_dir / "weekly",
                self.backup_dir / "monthly"
            ]
        
        total_files = 0
        total_size = 0
        
        for backup_dir in backup_dirs:
            if not backup_dir.exists():
                continue
                
            print(f"\n📁 {backup_dir.name}/")
            
            files = list(backup_dir.glob("*"))
            if not files:
                print("  (ファイルなし)")
                continue
            
            for file_path in sorted(files):
                if file_path.is_file():
                    file_size = file_path.stat().st_size
                    file_size_mb = file_size / (1024 * 1024)
                    modified_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    
                    print(f"  📄 {file_path.name}")
                    print(f"     サイズ: {file_size_mb:.2f}MB")
                    print(f"     更新日時: {modified_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    total_files += 1
                    total_size += file_size
        
        print(f"\n📊 合計: {total_files}ファイル, {total_size / (1024 * 1024):.2f}MB")
    
    def cleanup_old_backups(self, backup_type, keep_days=30):
        """古いバックアップファイルを削除"""
        print(f"🧹 古いバックアップファイルのクリーンアップ ({backup_type})")
        print(f"📅 保持期間: {keep_days}日")
        print("=" * 80)
        
        backup_dir = self.backup_dir / backup_type
        if not backup_dir.exists():
            print("📁 バックアップディレクトリが存在しません")
            return
        
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        deleted_count = 0
        deleted_size = 0
        
        for file_path in backup_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_size = file_path.stat().st_size
                print(f"🗑️ 削除: {file_path.name}")
                file_path.unlink()
                deleted_count += 1
                deleted_size += file_size
        
        print(f"✅ クリーンアップ完了: {deleted_count}ファイル削除, {deleted_size / (1024 * 1024):.2f}MB解放")

def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="データベースバックアップツール")
    parser.add_argument("--type", choices=["manual", "daily", "weekly", "monthly"], 
                       default="manual", help="バックアップタイプ")
    parser.add_argument("--format", choices=["custom", "sql"], 
                       default="custom", help="バックアップ形式")
    parser.add_argument("--list", action="store_true", help="バックアップ一覧表示")
    parser.add_argument("--cleanup", action="store_true", help="古いバックアップを削除")
    parser.add_argument("--keep-days", type=int, default=30, help="保持日数")
    
    args = parser.parse_args()
    
    backup = DatabaseBackup()
    
    if args.list:
        backup.list_backups()
    elif args.cleanup:
        backup.cleanup_old_backups(args.type, args.keep_days)
    else:
        result = backup.run_backup(args.type, args.format)
        if result['success']:
            print(f"\n🎉 バックアップが正常に完了しました!")
            print(f"📁 ファイル: {result['file_path']}")
            print(f"📊 サイズ: {result['file_size_mb']:.2f}MB")
        else:
            print(f"\n❌ バックアップに失敗しました: {result['error']}")
            sys.exit(1)

if __name__ == "__main__":
    main()
