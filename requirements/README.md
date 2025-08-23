# Requirements フォルダ解説

## 📁 概要

`requirements/`フォルダは、Exchange Analytics USD/JPY パターン検出システムの依存関係管理を担当しています。環境別に適切なパッケージを管理し、開発・本番環境での一貫性を保証します。

## 🗂️ ファイル構成

```
requirements/
├── base.txt          # 基本依存関係（全環境共通）
├── development.txt   # 開発環境用依存関係
├── production.txt    # 本番環境用依存関係
└── README.md         # このファイル
```

## 📋 各ファイルの詳細

### 🔧 base.txt - 基本依存関係

**用途**: 全環境（開発・本番）で共通して必要なパッケージ

#### Web Framework

- **FastAPI 0.104.1**: モダンな Python Web フレームワーク
- **Uvicorn 0.24.0**: ASGI サーバー（標準機能付き）
- **python-multipart 0.0.6**: マルチパートデータ処理

#### Database

- **SQLAlchemy 2.0.23**: ORM（Object-Relational Mapping）
- **Alembic 1.12.1**: データベースマイグレーション
- **asyncpg 0.29.0**: PostgreSQL 非同期ドライバー

#### Dependency Injection

- **dependency-injector 4.41.0**: 依存性注入コンテナ

#### Data & Analysis

- **pandas 2.1.4**: データ分析・操作ライブラリ
- **numpy 1.25.2**: 数値計算ライブラリ
- **ta 0.10.2**: テクニカル分析ライブラリ

#### External APIs

- **aiohttp 3.9.1**: 非同期 HTTP クライアント
- **httpx 0.25.2**: モダンな HTTP クライアント
- **requests 2.31.0**: HTTP ライブラリ
- **PyGithub 1.59.1**: GitHub API クライアント
- **openai 1.3.8**: OpenAI API クライアント
- **alpha-vantage 2.3.1**: Alpha Vantage API（株価データ）
- **yfinance 0.2.28**: Yahoo Finance API

#### Async Support

- **asyncio-mqtt 0.16.1**: MQTT 非同期クライアント

#### Caching

- **redis 5.0.1**: Redis キャッシュクライアント

#### Monitoring

- **psutil 5.9.6**: システム・プロセス監視
- **prometheus-client 0.19.0**: Prometheus 監視クライアント

#### Validation

- **marshmallow 3.20.1**: データシリアライゼーション・検証
- **pydantic 2.5.0**: データ検証ライブラリ

#### Environment

- **python-dotenv 1.0.0**: 環境変数管理

#### Discord Integration

- **discord-webhook 1.3.0**: Discord Webhook 統合

#### Job Scheduling

- **APScheduler 3.10.4**: タスクスケジューラー

#### Cryptography

- **cryptography 41.0.7**: 暗号化ライブラリ

#### CLI Framework

- **click 8.1.7**: CLI アプリケーション構築
- **rich 13.6.0**: リッチなターミナル出力
- **typer 0.9.0**: モダンな CLI フレームワーク

### 🛠️ development.txt - 開発環境用

**用途**: 開発・テスト環境でのみ必要なパッケージ

#### Testing

- **pytest 7.4.3**: テストフレームワーク
- **pytest-cov 4.1.0**: カバレッジ測定
- **pytest-asyncio 0.21.1**: 非同期テスト対応
- **pytest-mock 3.12.0**: モック機能
- **factory-boy 3.3.0**: テストデータファクトリ

#### Code Quality

- **black 23.11.0**: コードフォーマッター
- **flake8 6.1.0**: リンター
- **isort 5.12.0**: import 文整理
- **mypy 1.7.1**: 型チェッカー
- **bandit 1.7.5**: セキュリティチェッカー

#### Documentation

- **sphinx 7.2.6**: ドキュメント生成
- **sphinx-rtd-theme 1.3.0**: Read the Docs テーマ

#### Development Tools

- **pre-commit 3.5.0**: Git pre-commit フック
- **ipython 8.17.2**: 対話的 Python シェル
- **jupyter 1.0.0**: Jupyter Notebook

#### Database Tools

- **psycopg2-binary 2.9.9**: PostgreSQL バイナリドライバー

### 🚀 production.txt - 本番環境用

**用途**: 本番環境でのみ必要なパッケージ

#### Production WSGI Server

- **gunicorn 21.2.0**: WSGI サーバー

#### Production Database

- **psycopg2 2.9.9**: PostgreSQL ドライバー（バイナリ版）

#### Monitoring

- **sentry-sdk 1.38.0**: エラー監視・トラッキング

## 🔄 依存関係の継承構造

```
production.txt
├── base.txt (継承)
└── 本番環境固有パッケージ

development.txt
├── base.txt (継承)
└── 開発環境固有パッケージ
```

## 📦 インストール方法

### 開発環境

```bash
pip install -r requirements/development.txt
```

### 本番環境

```bash
pip install -r requirements/production.txt
```

### 基本のみ

```bash
pip install -r requirements/base.txt
```

## 🎯 設計思想

### 1. 環境分離

- **開発環境**: テスト・デバッグ・コード品質ツールを含む
- **本番環境**: 最小限の必要パッケージのみ
- **基本パッケージ**: 全環境で共通するコア機能

### 2. バージョン固定

- すべてのパッケージでバージョンを明示的に指定
- 環境間での一貫性を保証
- 予期しない破壊的変更を防止

### 3. 機能別グループ化

- コメントで機能別にグループ化
- 依存関係の目的を明確化
- メンテナンス性の向上

## 🔧 メンテナンス

### パッケージ更新

```bash
# 依存関係の更新確認
pip list --outdated

# 特定パッケージの更新
pip install --upgrade package_name

# requirements.txtの更新
pip freeze > requirements/base.txt
```

### セキュリティ監査

```bash
# セキュリティ脆弱性のチェック
safety check -r requirements/base.txt
```

## 📊 システム要件

- **Python**: 3.11+
- **OS**: Linux（推奨）、Windows、macOS
- **メモリ**: 最小 2GB、推奨 4GB 以上
- **ストレージ**: 最小 1GB の空き容量

## 🚨 注意事項

1. **バージョン互換性**: パッケージ更新時は互換性を確認
2. **セキュリティ**: 定期的なセキュリティ監査を実施
3. **パフォーマンス**: 本番環境では不要なパッケージを除外
4. **ライセンス**: 商用利用時のライセンス確認を推奨
