# 🏗️ Exchange Analytics System プロジェクト構造

**最新更新**: 2025 年 8 月 10 日  
**バージョン**: v4.1  
**アーキテクチャ**: Clean Architecture + Domain-Driven Design

## 📁 プロジェクト構造概要

```
exchangeApp/
├── 📄 README.md                    # メインドキュメント（最新版）
├── 📄 PROJECT_STRUCTURE.md         # このファイル
├── 📄 app.py                       # メインアプリケーション
├── 🔗 scheduler.py                 # スケジューラー（シンボリックリンク）
├── 📄 current_crontab.txt          # 現在のcrontab設定
├── 📄 notification_config.json     # 通知設定
├── 📄 notification_history.json    # 通知履歴
├── 📄 performance_cache.json       # パフォーマンスキャッシュ
├── 📄 requirements_backup.txt      # 依存関係バックアップ
├── 📄 test_indicators.py           # テクニカル指標テスト
├── 📄 timezone_fix.py              # タイムゾーン修正
├── 📄 .pre-commit-config.yaml      # Pre-commit設定
├── 📄 docker-compose.yml           # Docker Compose設定
├── 📄 docker-compose.prod.yml      # 本番用Docker Compose
│
├── 📁 src/                         # ソースコード（Clean Architecture）
│   ├── 📁 domain/                  # ドメイン層
│   │   ├── 📁 entities/            # エンティティ
│   │   ├── 📁 value_objects/       # 値オブジェクト
│   │   ├── 📁 repositories/        # リポジトリインターフェース
│   │   └── 📁 services/            # ドメインサービス
│   ├── 📁 application/             # アプリケーション層
│   │   ├── 📁 commands/            # コマンド
│   │   ├── 📁 queries/             # クエリ
│   │   ├── 📁 handlers/            # ハンドラー
│   │   ├── 📁 interfaces/          # インターフェース
│   │   ├── 📁 dto/                 # データ転送オブジェクト
│   │   └── 📁 exceptions/          # 例外
│   ├── 📁 infrastructure/          # インフラストラクチャ層
│   │   ├── 📁 database/            # データベース関連
│   │   │   ├── 📁 models/          # データベースモデル
│   │   │   ├── 📁 repositories/    # リポジトリ実装
│   │   │   └── 📁 services/        # データベースサービス
│   │   ├── 📁 external_apis/       # 外部API
│   │   ├── 📁 messaging/           # メッセージング
│   │   ├── 📁 cache/               # キャッシュ
│   │   ├── 📁 monitoring/          # 監視
│   │   ├── 📁 scheduling/          # スケジューリング
│   │   ├── 📁 config/              # 設定管理
│   │   ├── 📁 error_handling/      # エラーハンドリング
│   │   └── 📁 performance/         # パフォーマンス監視
│   ├── 📁 presentation/            # プレゼンテーション層
│   │   ├── 📁 api/                 # API
│   │   ├── 📁 web/                 # Web UI
│   │   └── 📁 cli/                 # CLI
│   └── 📁 utils/                   # ユーティリティ
│
├── 📁 tests/                       # テストファイル
│   ├── 📁 unit/                    # ユニットテスト
│   │   ├── 📄 test_technical_indicators.py
│   │   └── 📄 test_indicators_extended.py
│   ├── 📁 integration/             # 統合テスト
│   │   ├── 📄 test_notification_integration.py
│   │   ├── 📄 test_pattern5_completion.py
│   │   ├── 📄 test_discord_notification.py
│   │   ├── 📄 test_phase4_integration.py
│   │   ├── 📄 test_new_templates.py
│   │   ├── 📄 test_new_pattern_detectors.py
│   │   ├── 📄 test_notification_patterns.py
│   │   ├── 📄 test_cache_system.py
│   │   ├── 📄 test_notification_manager.py
│   │   ├── 📄 test_discord_simple.py
│   │   ├── 📄 multi_currency_trading_test.py
│   │   └── 📄 test_env_loading.py
│   ├── 📁 database/                # データベーステスト
│   │   ├── 📄 test_models.py
│   │   ├── 📄 test_database_connection.py
│   │   └── 📄 test_data_generator_service.py
│   ├── 📁 api/                     # APIテスト
│   │   ├── 📄 test_openai.py
│   │   ├── 📄 test_alphavantage.py
│   │   └── 📄 test_yahoo_finance.py
│   ├── 📁 e2e/                     # エンドツーエンドテスト
│   ├── 📄 test_app.py              # アプリケーションテスト
│   └── 📄 README.md                # テスト説明書
│
├── 📁 docs/                        # ドキュメント
│   ├── 📁 setup/                   # セットアップ関連ドキュメント
│   │   ├── 📄 DEVELOPMENT_SETUP.md         # 開発環境セットアップガイド
│   │   ├── 📄 GITHUB_ACTIONS_SETUP.md      # GitHub Actions 24時間稼働設定
│   │   ├── 📄 GITHUB_ACTIONS_DETAILED_SETUP.md  # GitHub Actions 詳細設定
│   │   └── 📄 ENVIRONMENT_SECRETS_SETUP.md # 環境変数・Secrets設定ガイド
│   ├── 📁 testing/                 # テスト関連ドキュメント
│   │   └── 📄 SYSTEM_INTEGRATION_TEST.md   # システム統合テストガイド
│   ├── 📁 architecture/            # アーキテクチャ設計書
│   │   └── 📄 DESIGN.md                    # 為替分析アプリ設計書
│   ├── 📁 api/                     # API仕様書（将来）
│   ├── 📁 deployment/              # デプロイメントガイド（将来）
│   ├── 📄 PRODUCTION_DEPLOYMENT.md # 本番デプロイメントガイド
│   └── 📄 README.md                # ドキュメント説明書
│
├── 📁 scripts/                     # スクリプト
│   ├── 📁 cron/                    # Cronスクリプト
│   │   └── 📄 data_scheduler.py    # データ取得スケジューラー
│   ├── 📁 deployment/              # デプロイメントスクリプト
│   │   ├── 📄 production_setup.py  # 本番環境セットアップ
│   │   ├── 📄 deploy_production.py # 本番デプロイ
│   │   └── 📄 data_migration.py    # データマイグレーション
│   ├── 📁 migration/               # マイグレーションスクリプト
│   ├── 📁 monitoring/              # 監視スクリプト
│   ├── 📁 setup/                   # セットアップスクリプト
│   └── 📁 test/                    # テストスクリプト
│       ├── 📄 test_performance_report_discord.py
│       ├── 📄 test_performance_optimization.py
│       ├── 📄 test_error_recovery_system.py
│       ├── 📄 test_discord_monitoring.py
│       ├── 📄 test_webhook_debug.py
│       ├── 📄 test_webhook_verification.py
│       ├── 📄 test_webhook_config.py
│       ├── 📄 test_monitoring_system.py
│       ├── 📄 test_production_deployment.py
│       ├── 📄 test_system_config_manager.py
│       ├── 📄 test_integrated_scheduler.py
│       ├── 📄 test_pattern_detection_complete.py
│       ├── 📄 test_simple_pattern_detection.py
│       ├── 📄 test_pattern_detection_debug.py
│       ├── 📄 test_pattern_detection_with_discord.py
│       ├── 📄 test_pattern_detection_with_test_data.py
│       ├── 📄 test_efficient_pattern_detection.py
│       ├── 📄 test_multi_timeframe_technical_indicators.py
│       ├── 📄 simple_pattern_detector.py
│       ├── 📄 test_timeframe_data_service.py
│       ├── 📄 test_multi_timeframe_fetcher.py
│       ├── 📄 test_timeframe_accuracy.py
│       ├── 📄 test_simple_detector.py
│       ├── 📄 clear_test_data.py
│       ├── 📄 setup_pattern_test_data.py
│       ├── 📄 test_pattern_detection.py
│       ├── 📄 check_data.py
│       ├── 📄 check_table.py
│       ├── 📄 simple_test.py
│       ├── 📄 setup_test_database.py
│       └── 📄 production_test.py
│
├── 📁 config/                      # 設定ファイル
│   ├── 📁 crontab/                 # Cron設定
│   │   ├── 📁 example/             # 例
│   │   ├── 📁 docs/                # ドキュメント
│   │   ├── 📁 production/          # 本番環境
│   │   └── 📁 backup/              # バックアップ
│   ├── 📁 environments/            # 環境設定
│   └── 📁 plugins/                 # プラグイン設定
│
├── 📁 plugins/                     # プラグインシステム
│   ├── 📁 analysis/                # 分析プラグイン
│   ├── 📁 interfaces/              # インターフェース
│   ├── 📁 reports/                 # レポートプラグイン
│   └── 📁 technical_indicators/    # テクニカル指標プラグイン
│
├── 📁 requirements/                # 依存関係管理
│   ├── 📄 base.txt                 # 基本依存関係
│   ├── 📄 development.txt          # 開発用依存関係
│   └── 📄 production.txt           # 本番用依存関係
│
├── 📁 data/                        # データファイル
│   ├── 📄 test_app.db              # テスト用データベース
│   └── 📄 discord_test.json        # Discord設定
│
├── 📁 logs/                        # ログファイル
│   └── 📁 archive/                 # ログアーカイブ
│
├── 📁 migrations/                  # データベースマイグレーション
│   └── 📁 versions/                # マイグレーションバージョン
│
├── 📁 note/                        # 設計・計画ノート
│   ├── 📄 implementation_todo_2025.yaml      # 実装TODO
│   ├── 📄 system_implementation_completion_report_2025.md  # 完了レポート
│   ├── 📄 database_implementation_plan_2025.yaml  # データベース実装計画
│   ├── 📄 api_optimization_implementation_plan_2025.yaml  # API最適化計画
│   ├── 📄 trade_chart_settings_complete_2025.md  # チャート設定
│   ├── 📄 database_implementation_design_2025.md  # データベース設計
│   ├── 📄 api_optimization_design_2025.md  # API最適化設計
│   ├── 📄 基本設計書_20250809.md  # 基本設計書
│   └── 📄 PROJECT_STRUCTURE.md     # プロジェクト構造
│
├── 📁 prompts/                     # AIプロンプト
│
├── 📁 cache/                       # キャッシュ
│
├── 📁 .github/                     # GitHub設定
│   └── 📁 workflows/               # GitHub Actions
│
├── 📁 .devcontainer/               # Dev Container設定
│
├── 📁 .vscode/                     # VS Code設定
│
├── 📄 .env                         # 環境変数（本番）
├── 📄 .env.example                 # 環境変数テンプレート
├── 📄 .gitignore                   # Git除外設定
├── 📄 pytest.ini                   # pytest設定
└── 📄 Dockerfile                   # Docker設定
```

## 🏛️ アーキテクチャ概要

### Clean Architecture 構造

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │     API     │  │    Web UI   │  │     CLI     │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Application Layer                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Commands   │  │   Queries   │  │  Handlers   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Domain Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Entities   │  │Value Objects│  │  Services   │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │  Database   │  │External APIs│  │  Messaging  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 🎯 主要コンポーネント

### 1. データ取得・分析システム

- **マルチタイムフレームデータ取得**: 5 分足、1 時間足、4 時間足、日足
- **テクニカル指標計算**: RSI、MACD、ボリンジャーバンド
- **パターン検出**: 6 種類のパターン検出アルゴリズム
- **AI 分析**: GPT-4 による統合分析

### 2. 通知システム

- **Discord 通知**: リアルタイム配信
- **チャンネル分離**: #一般、#システム監視・ログ管理システム
- **通知テンプレート**: カスタマイズ可能な通知形式

### 3. スケジューリングシステム

- **統合スケジューラー**: データ取得、指標計算、パターン検出の統合管理
- **24 時間稼働**: グローバル市場対応
- **エラーハンドリング**: 自動復旧・リトライ機能

### 4. 監視・ログシステム

- **システム監視**: CPU、メモリ、ディスク使用量
- **パフォーマンス監視**: レスポンス時間、エラー率
- **ログ管理**: 構造化ログ、ローテーション

### 5. エラーハンドリング・リカバリー

- **自動エラー検出**: エラー分類・統計
- **リトライ機能**: 指数バックオフ
- **サーキットブレーカー**: 障害の伝播防止
- **タイムアウト処理**: 長時間処理の制御

## 📊 実装完了状況

### ✅ Phase 1: データ基盤の整備 (100% 完了)

- マルチタイムフレームデータ取得システム
- テクニカル指標計算システム
- データベース設計・実装

### ✅ Phase 2: パターン検出・通知システム (100% 完了)

- 効率的パターン検出サービス
- Discord 通知統合
- 統合スケジューラー

### ✅ Phase 3: システム運用・保守 (100% 完了)

- システム設定管理
- 本番環境デプロイメント
- 監視・ログシステム
- エラーハンドリング・リカバリー

### ✅ Phase 4: パフォーマンス最適化 (100% 完了)

- パフォーマンス監視
- データベース最適化
- システム最適化

## 🔧 開発・運用ツール

### 開発環境

- **Python 3.11+**: メイン言語
- **SQLAlchemy**: ORM
- **PostgreSQL/SQLite**: データベース
- **Docker**: コンテナ化
- **pytest**: テストフレームワーク

### 外部サービス

- **Yahoo Finance API**: 為替データ取得
- **OpenAI GPT-4**: AI 分析
- **Discord Webhook**: 通知配信
- **GitHub Actions**: CI/CD

### 監視・ログ

- **psutil**: システム監視
- **logging**: ログ管理
- **カスタム監視**: パフォーマンス監視

## 🚀 デプロイメント

### 本番環境

- **Docker Compose**: コンテナオーケストレーション
- **systemd**: サービス管理
- **cron**: スケジューリング
- **環境変数**: 設定管理

### CI/CD

- **GitHub Actions**: 自動テスト・デプロイ
- **環境分離**: production/staging/development
- **セキュリティ**: Environment Secrets

## 📈 パフォーマンス指標

### システム性能

- **レスポンス時間**: 平均 1 秒以下
- **データ取得頻度**: 5 分間隔
- **通知配信成功率**: 100%
- **システム稼働率**: 24 時間/日

### 最適化結果

- **API 呼び出し削減**: 82.5%削減
- **エラー率削減**: 90%削減
- **レスポンス時間短縮**: 50%短縮

## 🔮 将来拡張計画

### 追加パターン検出（別途計画）

1. **高度なテクニカルパターン**

   - フィボナッチリトレースメント
   - エリオット波動
   - サポート・レジスタンスライン

2. **マルチタイムフレーム分析**

   - 時間軸間の相関分析
   - トレンドの強度測定

3. **機械学習によるパターン検出**
   - 異常検出
   - クラスタリング分析

### システム拡張

1. **追加通貨ペア対応**
2. **Web UI ダッシュボード**
3. **モバイルアプリ対応**
4. **API エンドポイント提供**

---

**📊 Exchange Analytics System v4.1** - _Production-Ready Architecture_
