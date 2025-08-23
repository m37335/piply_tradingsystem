# System Directory

## 概要

システムの設定ファイルや IDE 設定を管理するディレクトリです。開発環境の設定やツール固有のファイルが保存されています。

## 保存されているファイル

### システムファイル

- `.DS_Store` - macOS システムファイル
- `.cursorignore` - Cursor IDE 除外設定
- `.dockerignore` - Docker 除外設定

## よく編集するファイル

- `.cursorignore` - 新しい除外パターンの追加時
- `.dockerignore` - Docker ビルド対象の変更時

## 注意事項

- `.DS_Store`は自動生成されるため手動編集不要
- 除外設定の変更は開発効率に影響
- 設定変更時はチーム内で共有
- 不要なファイルは定期的に削除

## 関連フォルダ

- `config/` - アプリケーション設定
- `backups/` - 設定バックアップ
