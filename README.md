# 🚀 Exchange Analytics System

**通貨分析システム - ChatGPT 統合・Discord 通知対応**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 概要

Exchange Analytics System は、現代的なアーキテクチャで構築された**エンタープライズグレード**の通貨分析システムです。

### ✨ 主な特徴

- 🏗️ **クリーンアーキテクチャ**: Domain/Application/Infrastructure/Presentation の 4 層設計
- 🌐 **REST API**: FastAPI による高パフォーマンス API (25 エンドポイント)
- 🤖 **AI 統合**: ChatGPT による市場分析レポート自動生成
- 💬 **Discord 通知**: リアルタイム市場アラート・レポート配信
- 🖥️ **美しい CLI**: Typer + Rich による直感的コマンドラインツール
- 📊 **リアルタイム監視**: ヘルスチェック・メトリクス・アラートシステム
- 🔌 **拡張可能**: プラグインシステム対応
- 📈 **テクニカル分析**: SMA, RSI, MACD 等の指標計算
- 🗄️ **データ管理**: PostgreSQL + Redis による高速キャッシュ
- ⚙️ **動的設定**: データベースベース設定管理・ホットリロード

## 🏛️ アーキテクチャ

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │ REST API    │ │ CLI Interface       │ │
│  │ (FastAPI)   │ │ (Typer + Rich)      │ │
│  └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│           Application Layer             │
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │ Use Cases   │ │ Services            │ │
│  │ (Workflows) │ │ (Business Logic)    │ │
│  └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│         Infrastructure Layer            │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────────────┐ │
│  │ DB  │ │Cache│ │APIs │ │ Messaging   │ │
│  │(PG) │ │(RDS)│ │(AV) │ │ (Discord)   │ │
│  └─────┘ └─────┘ └─────┘ └─────────────┘ │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│              Domain Layer               │
│  ┌─────────────┐ ┌─────────────────────┐ │
│  │ Entities    │ │ Value Objects       │ │
│  │ (Models)    │ │ (Business Rules)    │ │
│  └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────┘
```

## 🚀 クイックスタート

### 1. 環境要件

- **Python 3.11+**
- **PostgreSQL 12+**
- **Redis 6+**

### 2. インストール

```bash
# リポジトリをクローン
git clone https://github.com/your-org/exchange-analytics.git
cd exchange-analytics

# 依存関係をインストール
pip install -r requirements/base.txt

# 実行権限を付与
chmod +x exchange-analytics
```

### 3. 環境設定

```bash
# 環境変数を設定
export DATABASE_URL="postgresql://user:pass@localhost:5432/exchange_analytics"
export REDIS_URL="redis://localhost:6379/0"
export ALPHA_VANTAGE_API_KEY="your_api_key"
export OPENAI_API_KEY="your_openai_key"
export DISCORD_WEBHOOK_URL="your_discord_webhook"
```

### 4. システム起動

```bash
# データベース初期化
./exchange-analytics data init

# API サーバー起動
./exchange-analytics api start

# 別ターミナルで状態確認
./exchange-analytics status
```

## 📖 使用方法

### 🌐 REST API

```bash
# API サーバー起動
./exchange-analytics api start --port 8000

# Swagger UI でドキュメント確認
# http://localhost:8000/docs
```

**主要エンドポイント:**

- `GET /api/v1/health` - ヘルスチェック
- `GET /api/v1/rates/latest` - 最新為替レート
- `GET /api/v1/analysis/technical/{pair}` - テクニカル分析
- `POST /api/v1/ai-reports/generate` - AI 分析レポート生成

### 🖥️ CLI コマンド

```bash
# システム状態確認
./exchange-analytics status

# データ取得
./exchange-analytics data fetch --pairs "USD/JPY,EUR/USD"

# 設定管理
./exchange-analytics config show
./exchange-analytics config set api.alpha_vantage.rate_limit 1000

# 監視・ヘルスチェック
./exchange-analytics monitor health --detailed
./exchange-analytics monitor metrics --live

# API サーバー管理
./exchange-analytics api start --background
./exchange-analytics api status
```

### 📊 監視・運用

```bash
# リアルタイム監視
./exchange-analytics monitor health --continuous --interval 5
./exchange-analytics monitor metrics --live
./exchange-analytics monitor logs --follow --level ERROR

# データ管理
./exchange-analytics data backup --compress
./exchange-analytics data clean --days 30
./exchange-analytics data export exchange_rates --format json
```

## 🛠️ 開発

### プロジェクト構造

```
exchange-analytics/
├── src/
│   ├── domain/              # ドメイン層
│   │   ├── entities/        # エンティティ
│   │   └── value_objects/   # 値オブジェクト
│   ├── application/         # アプリケーション層
│   │   ├── use_cases/       # ユースケース
│   │   └── services/        # アプリケーションサービス
│   ├── infrastructure/      # インフラストラクチャ層
│   │   ├── database/        # データベース
│   │   ├── cache/           # キャッシュ
│   │   ├── external_apis/   # 外部API
│   │   └── messaging/       # メッセージング
│   └── presentation/        # プレゼンテーション層
│       ├── api/             # REST API
│       └── cli/             # CLI
├── tests/                   # テスト
├── config/                  # 設定ファイル
├── logs/                    # ログファイル
└── requirements/            # 依存関係
```

### 🧪 テスト実行

```bash
# 全テスト実行
pytest

# カバレッジ付き
pytest --cov=src --cov-report=html

# 特定レイヤーのテスト
pytest tests/unit/domain/
pytest tests/integration/infrastructure/
```

### 🔧 開発ツール

```bash
# コード品質チェック
black src/
flake8 src/
mypy src/

# Git hooks (pre-commit)
pre-commit install
pre-commit run --all-files
```

## 🔌 API リファレンス

### 為替レート API

```http
GET /api/v1/rates/latest?currency_pairs=USD/JPY,EUR/USD
GET /api/v1/rates/{currency_pair}?interval=1min&limit=100
POST /api/v1/rates/fetch
```

### 分析 API

```http
GET /api/v1/analysis/technical/{currency_pair}?indicators=sma,rsi,macd
GET /api/v1/analysis/trend/{currency_pair}?timeframe=1d
POST /api/v1/analysis/custom
```

### AI レポート API

```http
POST /api/v1/ai-reports/generate
GET /api/v1/ai-reports?limit=10
```

### アラート API

```http
GET /api/v1/alerts?active_only=true
POST /api/v1/alerts
```

## ⚙️ 設定

### 環境変数

| 変数名                  | 説明                   | デフォルト    |
| ----------------------- | ---------------------- | ------------- |
| `DATABASE_URL`          | PostgreSQL 接続 URL    | -             |
| `REDIS_URL`             | Redis 接続 URL         | -             |
| `ALPHA_VANTAGE_API_KEY` | Alpha Vantage API キー | -             |
| `OPENAI_API_KEY`        | OpenAI API キー        | -             |
| `DISCORD_WEBHOOK_URL`   | Discord Webhook URL    | -             |
| `JWT_SECRET`            | JWT 署名シークレット   | -             |
| `LOG_LEVEL`             | ログレベル             | `INFO`        |
| `ENVIRONMENT`           | 実行環境               | `development` |

### 動的設定

```bash
# 設定の確認
./exchange-analytics config show

# 設定の更新
./exchange-analytics config set api.alpha_vantage.rate_limit 1000
./exchange-analytics config set database.pool_size 20

# 設定の検証
./exchange-analytics config validate
```

## 📊 監視・運用

### ヘルスチェック

```bash
# 基本ヘルスチェック
curl http://localhost:8000/api/v1/health

# 詳細ヘルスチェック
curl http://localhost:8000/api/v1/health/detailed

# Kubernetes プローブ
curl http://localhost:8000/api/v1/health/readiness
curl http://localhost:8000/api/v1/health/liveness
```

### メトリクス

```bash
# システムメトリクス
curl http://localhost:8000/api/v1/health/metrics

# CLI でリアルタイム監視
./exchange-analytics monitor metrics --live
```

### ログ

```bash
# ログ確認
./exchange-analytics monitor logs --lines 100
./exchange-analytics monitor logs --follow --level ERROR
./exchange-analytics monitor logs --component api
```

## 🔐 セキュリティ

- **認証**: API キー + JWT 認証
- **認可**: ロールベースアクセス制御
- **レート制限**: エンドポイント別・クライアント別制限
- **セキュリティヘッダー**: CORS, CSP, セキュリティヘッダー
- **入力検証**: Pydantic バリデーション
- **ログ**: セキュリティイベント記録

## 🚀 デプロイメント

### Docker

```bash
# イメージビルド
docker build -t exchange-analytics .

# コンテナ実行
docker run -p 8000:8000 exchange-analytics
```

### Kubernetes

```bash
# マニフェスト適用
kubectl apply -f k8s/

# ヘルスチェック
kubectl get pods -l app=exchange-analytics
```

## 📈 パフォーマンス

- **API レスポンス**: 平均 < 100ms
- **データ取得**: 並列処理対応
- **キャッシュ**: Redis による高速化
- **データベース**: 接続プール・インデックス最適化
- **監視**: リアルタイムメトリクス

## 🤝 コントリビューション

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 開発ガイドライン

- **コミット**: Conventional Commits 準拠
- **コード品質**: Black + flake8 + mypy
- **テスト**: 新機能には必ずテストを追加
- **ドキュメント**: API 変更時はドキュメント更新

## 📝 ライセンス

このプロジェクトは [MIT License](LICENSE) の下で公開されています。

## 👥 Authors

- **Exchange Analytics Team** - _Initial work_

## 🙏 謝辞

- [FastAPI](https://fastapi.tiangolo.com/) - 高速 Web API フレームワーク
- [Typer](https://typer.tiangolo.com/) - 美しい CLI フレームワーク
- [Rich](https://rich.readthedocs.io/) - リッチテキスト表示
- [Alpha Vantage](https://www.alphavantage.co/) - 金融データ API
- [OpenAI](https://openai.com/) - AI 分析エンジン

---

**📊 Exchange Analytics System** - _Production-Ready Currency Analysis Platform_
