# 📚 ドキュメントディレクトリ

## 📁 ディレクトリ構造

```
docs/
├── setup/                           # セットアップ関連ドキュメント
│   ├── DEVELOPMENT_SETUP.md         # 開発環境セットアップガイド
│   ├── GITHUB_ACTIONS_SETUP.md      # GitHub Actions 24時間稼働設定
│   ├── GITHUB_ACTIONS_DETAILED_SETUP.md  # GitHub Actions 詳細設定
│   └── ENVIRONMENT_SECRETS_SETUP.md # 環境変数・Secrets設定ガイド
├── testing/                         # テスト関連ドキュメント
│   └── SYSTEM_INTEGRATION_TEST.md   # システム統合テストガイド
├── architecture/                    # アーキテクチャ設計書
│   └── DESIGN.md                    # 為替分析アプリ設計書
├── api/                             # API仕様書（将来）
├── deployment/                      # デプロイメントガイド（将来）
└── README.md                        # このファイル
```

## 🎯 ドキュメント分類

### セットアップドキュメント (`setup/`)

#### 開発環境セットアップ

- **ファイル**: `DEVELOPMENT_SETUP.md`
- **目的**: 開発環境の構築手順
- **対象**: 開発者、新規参加者
- **内容**:
  - プロジェクト構造の準備
  - 依存関係の完全化
  - 開発環境の初期化

#### GitHub Actions 設定

- **ファイル**: `GITHUB_ACTIONS_SETUP.md`
- **目的**: 24 時間自動実行システムの設定
- **対象**: DevOps、システム管理者
- **内容**:
  - 自動実行スケジュール設定
  - GitHub Repository Secrets 設定
  - ワークフロー有効化手順

#### 詳細設定ガイド

- **ファイル**: `GITHUB_ACTIONS_DETAILED_SETUP.md`
- **目的**: GitHub Actions の詳細な設定手順
- **対象**: システム管理者
- **内容**:
  - 段階的な設定手順
  - トラブルシューティング
  - 監視・確認方法

#### 環境変数・Secrets 設定

- **ファイル**: `ENVIRONMENT_SECRETS_SETUP.md`
- **目的**: セキュアな環境変数管理
- **対象**: システム管理者、セキュリティ担当者
- **内容**:
  - Environment Secrets 設定
  - セキュリティ向上策
  - 環境分離管理

### テストドキュメント (`testing/`)

#### システム統合テスト

- **ファイル**: `SYSTEM_INTEGRATION_TEST.md`
- **目的**: システム全体の統合テストガイド
- **対象**: 開発者、QA、システム管理者
- **内容**:
  - API Layer テスト
  - CLI 機能テスト
  - 非機能要件テスト
  - 運用機能テスト
  - 包括的チェックリスト

### アーキテクチャ設計書 (`architecture/`)

#### 為替分析アプリ設計書

- **ファイル**: `DESIGN.md`
- **目的**: システム全体の基本設計書
- **対象**: 開発者、アーキテクト、プロジェクトマネージャー
- **内容**:
  - プロジェクト概要・目的
  - システム構成・技術スタック
  - 機能詳細設計
  - API 設計・データ構造
  - プラグインシステム
  - 将来拡張ロードマップ

## 🚀 使用方法

### 新規開発者向け

1. `docs/setup/DEVELOPMENT_SETUP.md` を参照
2. 開発環境を構築
3. 基本的な動作確認

### システム管理者向け

1. `docs/setup/GITHUB_ACTIONS_SETUP.md` を参照
2. `docs/setup/ENVIRONMENT_SECRETS_SETUP.md` でセキュリティ設定
3. 24 時間稼働システムの構築

### トラブルシューティング

1. `docs/setup/GITHUB_ACTIONS_DETAILED_SETUP.md` のトラブルシューティングセクション
2. 各ドキュメントの注意事項・制限事項を確認

## 📋 ドキュメント更新方針

### 更新タイミング

- 新機能追加時
- 設定変更時
- トラブル発生時
- 定期的な見直し（月 1 回）

### 更新内容

- 手順の詳細化
- スクリーンショットの追加
- トラブルシューティングの充実
- ベストプラクティスの追加

## 🔗 関連リンク

### プロジェクト内リンク

- **テスト**: `tests/README.md`
- **実装計画**: `note/implementation_todo_2025.yaml`
- **完了レポート**: `note/system_implementation_completion_report_2025.md`

### 外部リンク

- **GitHub Actions**: https://docs.github.com/en/actions
- **Discord Webhook**: https://discord.com/developers/docs/resources/webhook
- **OpenAI API**: https://platform.openai.com/docs

## 📊 ドキュメント品質

### 成功基準

- ✅ 手順が明確で再現可能
- ✅ スクリーンショット・コード例が充実
- ✅ トラブルシューティングが網羅的
- ✅ 定期的に更新されている

### 改善点

- 動画チュートリアルの追加
- インタラクティブなガイドの作成
- 多言語対応（英語版の追加）
- 検索機能の強化
