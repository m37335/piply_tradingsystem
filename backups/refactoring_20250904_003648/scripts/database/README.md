# Database Scripts Directory

## 概要

データベース関連のスクリプトを管理するディレクトリです。PostgreSQL 接続テスト、スキーマ管理、テーブル作成などのスクリプトが保存されています。

## 保存されているファイル

### 接続・テストスクリプト（1 ファイル）

- `postgresql_connection.py` - PostgreSQL 接続テスト

### スキーマ・初期化ファイル（3 ファイル）

- `postgresql_init.sql` - PostgreSQL 初期化 SQL
- `postgresql_schema.sql` - PostgreSQL スキーマ定義
- `create_notification_history_table.sql` - 通知履歴テーブル作成

## よく編集するファイル

- `postgresql_schema.sql` - スキーマ変更時
- `postgresql_connection.py` - 接続設定変更時
- `create_*.sql` - 新しいテーブル作成時

## 注意事項

- スキーマ変更は本番環境に影響するため慎重に実行
- 変更前にバックアップを必ず取得
- マイグレーション手順を事前に確認
- テスト環境での検証を必ず実施

## 関連フォルダ

- `migrations/` - データベースマイグレーション
- `backups/` - データベースバックアップ
- `config/` - データベース設定
