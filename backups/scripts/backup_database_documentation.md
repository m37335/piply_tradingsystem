# データベースバックアップシステム

## 使っている技術スタック

- **Python 3.11+**: メインスクリプト言語
- **PostgreSQL**: データベースエンジン
- **TimescaleDB**: 時系列データ拡張
- **pg_dump**: PostgreSQL標準バックアップツール
- **pg_restore**: PostgreSQL復元ツール
- **asyncio**: 非同期処理（将来の拡張用）
- **pathlib**: ファイルパス管理
- **subprocess**: 外部コマンド実行

## 機能の概要

データベースバックアップシステムは、PostgreSQL/TimescaleDBデータベースの完全なバックアップを作成・管理するためのツールです。手動バックアップ、定期バックアップ、古いバックアップの自動クリーンアップ機能を提供します。

### 主要機能
- カスタム形式・SQL形式でのバックアップ作成
- 圧縮による効率的なストレージ使用
- バックアップタイプ別の管理（手動・日次・週次・月次）
- バックアップファイルの一覧表示・管理
- 古いバックアップの自動削除
- バックアップログの自動記録

## 背景・目的

### 背景
- 為替分析アプリケーションの重要なデータ（価格データ、分析結果等）を保護
- システム障害やデータ破損時の迅速な復旧
- 開発・テスト環境でのデータ復元
- 規制要件への対応（データ保持期間）

### 目的
- データの完全性と可用性の確保
- 災害復旧計画の実装
- 開発効率の向上（テストデータの再利用）
- コンプライアンス要件の満足

## コンポーネント設計

### クラス設計

```python
class DatabaseBackup:
    """データベースバックアップクラス"""
    
    def __init__(self):
        # データベース設定の読み込み
        # バックアップディレクトリの設定
        # タイムスタンプの生成
    
    def create_backup_filename(self, backup_type):
        """バックアップファイル名を生成"""
    
    def get_backup_path(self, backup_type):
        """バックアップファイルのパスを取得"""
    
    def create_pg_dump_command(self, output_path):
        """pg_dumpコマンドを生成（カスタム形式）"""
    
    def create_sql_dump_command(self, output_path):
        """pg_dumpコマンドを生成（SQL形式）"""
    
    def run_backup(self, backup_type, format_type):
        """バックアップを実行"""
    
    def log_backup_info(self, file_path, file_size_mb, backup_type):
        """バックアップ情報をログに記録"""
    
    def list_backups(self, backup_type):
        """バックアップファイル一覧を表示"""
    
    def cleanup_old_backups(self, backup_type, keep_days):
        """古いバックアップファイルを削除"""
```

### ディレクトリ構造

```
/app/backups/
├── database/
│   ├── manual/          # 手動バックアップ
│   ├── daily/           # 日次バックアップ
│   ├── weekly/          # 週次バックアップ
│   ├── monthly/         # 月次バックアップ
│   └── backup_log.txt   # バックアップログ
└── scripts/
    └── backup_database.py  # バックアップスクリプト
```

## できること・制限事項

### できること

**1. バックアップ作成**
- カスタム形式（圧縮・高速）
- SQL形式（可読性・互換性）
- 完全バックアップ（スキーマ+データ+インデックス）

**2. バックアップ管理**
- タイプ別分類（手動・日次・週次・月次）
- ファイル一覧表示
- サイズ・日時情報の表示

**3. 自動化機能**
- 古いバックアップの自動削除
- バックアップログの自動記録
- コマンドライン引数による柔軟な設定

**4. 復元対応**
- pg_restoreによる完全復元
- 異なるデータベース名での復元
- 部分復元（テーブル単位）

### 制限事項

**1. 技術的制限**
- PostgreSQL/TimescaleDB専用
- 単一データベースのバックアップのみ
- リアルタイムバックアップは非対応

**2. 運用制限**
- バックアップ中のデータベースアクセス制限
- 大容量データベースでの長時間実行
- ネットワーク障害時の中断リスク

**3. ストレージ制限**
- ローカルストレージのみ対応
- クラウドストレージ連携は未実装
- 暗号化機能は未実装

## コンポーネント使用時のオプション

### コマンドライン引数

```bash
# 基本オプション
--type {manual,daily,weekly,monthly}  # バックアップタイプ
--format {custom,sql}                 # バックアップ形式
--list                               # バックアップ一覧表示
--cleanup                           # 古いバックアップ削除
--keep-days 30                      # 保持日数（デフォルト30日）
```

### 使用例

```bash
# 手動バックアップ（カスタム形式）
python scripts/backup_database.py --type manual --format custom

# 手動バックアップ（SQL形式）
python scripts/backup_database.py --type manual --format sql

# 日次バックアップ
python scripts/backup_database.py --type daily

# バックアップ一覧表示
python scripts/backup_database.py --list

# 古いバックアップ削除（60日保持）
python scripts/backup_database.py --cleanup --keep-days 60
```

### 環境変数

```bash
# データベース接続設定（.envファイル）
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trading_system
DB_USER=postgres
DB_PASSWORD=Postgres_Secure_2025!
```

## 関連ファイル・ディレクトリ構造

### 主要ファイル

```
/app/scripts/backup_database.py          # メインスクリプト
/app/backups/database/                   # バックアップ保存ディレクトリ
/app/backups/database/backup_log.txt     # バックアップログ
/app/modules/data_persistence/config/settings.py  # DB設定
```

### 設定ファイル

```
/app/.env                                # 環境変数設定
/app/modules/data_persistence/config/settings.py  # データベース設定
```

### ログファイル

```
/app/backups/database/backup_log.txt     # バックアップログ
/app/logs/                               # システムログ（将来拡張）
```

## 注意点

### セキュリティ

**1. 認証情報の管理**
- データベースパスワードは環境変数で管理
- バックアップファイルのアクセス権限設定
- ログファイルにパスワードが含まれないよう注意

**2. ファイル権限**
```bash
# バックアップファイルの権限設定
chmod 600 /app/backups/database/*/*.dump
chmod 600 /app/backups/database/*/*.sql
```

### 運用上の注意

**1. バックアップ実行時**
- データベースへの書き込み負荷を考慮
- 十分なディスク容量の確保
- バックアップ完了の確認

**2. 復元時の注意**
- 既存データの上書き確認
- 復元先データベースの準備
- アプリケーションの停止

**3. 定期メンテナンス**
- 古いバックアップの定期削除
- ディスク容量の監視
- バックアップファイルの整合性チェック

### トラブルシューティング

**1. よくある問題**
- ディスク容量不足
- データベース接続エラー
- 権限不足

**2. 解決方法**
```bash
# ディスク容量確認
df -h /app/backups/

# データベース接続確認
psql -h localhost -p 5432 -U postgres -d trading_system

# 権限確認
ls -la /app/backups/database/
```

### 将来の拡張予定

**1. 機能拡張**
- クラウドストレージ連携（AWS S3、Google Cloud Storage）
- 暗号化機能の追加
- インクリメンタルバックアップ
- 自動復元機能

**2. 監視機能**
- バックアップ成功/失敗の通知
- バックアップサイズの監視
- 復元時間の測定

**3. スケジューリング**
- cronジョブとの連携
- 自動定期バックアップ
- バックアップスケジュールの管理

---

**作成日**: 2025-09-17  
**バージョン**: 1.0  
**作成者**: システム開発チーム
