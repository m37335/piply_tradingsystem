# Backups Directory

## 概要

バックアップファイルとテンプレートファイルを管理するディレクトリです。

## 保存されているファイル

### バックアップファイル

- `.env.backup` - 環境変数のバックアップファイル
- `backup_exchange_analytics_minimum_20250815.gz` - 最小限のデータベースバックアップ
- `backup_exchange_analytics_postgresql_complete_20250815.gz` - PostgreSQL 完全バックアップ
- `requirements_backup.txt` - 依存関係のバックアップ

### テンプレートファイル

- `env.example` - 環境変数のテンプレートファイル

## よく編集するファイル

- `env.example` - 新しい環境設定時のテンプレート更新

## 注意事項

- バックアップファイルは定期的に更新が必要
- 本番環境のバックアップは自動化を検討
- 機密情報を含むファイルは適切に管理

## 関連フォルダ

- `config/` - 現在の設定ファイル
- `legacy/` - 旧データベースファイル
