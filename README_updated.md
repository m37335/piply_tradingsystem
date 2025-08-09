# Exchange Analytics App

為替分析と自動レポート生成を行う Web アプリケーションです。

## 🚀 セットアップ状況

✅ **開発環境準備完了**

- プロジェクト構造作成済み
- 依存関係完全化済み
- 設定ファイル整備済み
- 開発ツール設定済み
- データベース準備済み
- Docker 環境整備済み

## 主な機能

### GitHub 自動更新機能

- GitHub webhook による自動デプロイ
- プッシュ時の自動更新
- リポジトリ情報の取得

### 為替分析機能

#### 主要機能

- リアルタイム為替レート取得
- 履歴データの分析
- テクニカル指標の計算
- カスタマイズ可能なアラート

#### 分析機能

- 移動平均線（SMA, EMA）
- RSI（相対力指数）
- MACD
- ボリンジャーバンド
- サポート・レジスタンスレベル

#### AI 分析レポート

- ChatGPT API を利用した市場分析
- 定期的な自動レポート生成
- Discord 通知機能
- カスタマイズ可能なレポート形式

### プラグインシステム

- モジュール化された拡張可能なアーキテクチャ
- カスタムテクニカル指標の追加
- 分析アルゴリズムの動的ロード
- プラグイン管理 API

## セットアップ

### 前提条件

- Python 3.11+
- Docker & Docker Compose

### インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd exchange-analytics

# 環境変数を設定
cp env.example .env
# .envファイルを編集してAPIキーを設定

# 依存関係をインストール（開発環境）
pip install -r requirements/development.txt

# 本番環境の場合
pip install -r requirements/production.txt
```

### Docker 使用時

```bash
# 開発モード
docker-compose up -d

# 本番モード
docker-compose -f docker-compose.prod.yml up -d
```

## 設定

### 環境変数

- `SECRET_KEY`: Flask シークレットキー
- `DATABASE_URL`: データベース接続 URL
- `REDIS_URL`: Redis 接続 URL
- `ALPHA_VANTAGE_API_KEY`: Alpha Vantage API キー
- `OPENAI_API_KEY`: OpenAI API キー
- `DISCORD_WEBHOOK_URL`: Discord webhook URL
- `GITHUB_TOKEN`: GitHub アクセストークン

### 設定ファイル

- `config/development.py` - 開発環境設定
- `config/production.py` - 本番環境設定
- `config/testing.py` - テスト環境設定

### API エンドポイント

- `/api/rates/latest` - 最新の為替レート
- `/api/analysis/technical` - テクニカル分析
- `/api/reports/ai` - AI 分析レポート
- `/api/github/update` - 手動更新トリガー
- `/api/plugins/` - プラグイン管理

## 開発

### プロジェクト構造

```
/app
├── src/                    # アプリケーションソース
│   ├── domain/            # ドメイン層
│   ├── application/       # アプリケーション層
│   ├── infrastructure/    # インフラ層
│   └── presentation/      # プレゼンテーション層
├── tests/                 # テストファイル
│   ├── unit/             # ユニットテスト
│   ├── integration/      # 統合テスト
│   └── e2e/              # E2Eテスト
├── config/               # 設定ファイル
├── plugins/              # プラグインディレクトリ
├── requirements/         # 依存関係ファイル
│   ├── base.txt         # 基本パッケージ
│   ├── development.txt  # 開発環境用
│   └── production.txt   # 本番環境用
├── migrations/           # データベースマイグレーション
├── docs/                 # ドキュメント
└── scripts/              # セットアップ・デプロイスクリプト
```

### 開発環境セットアップ

```bash
# 開発用依存関係をインストール
pip install -r requirements/development.txt

# pre-commitフックを設定
pre-commit install

# データベースマイグレーション
alembic upgrade head

# テストを実行
pytest

# コード品質チェック
black src/ tests/
flake8 src/ tests/
mypy src/
```

### 開発ワークフロー

1. 各フェーズの実装前に設計書を確認
2. 命名規則に従った実装
3. テスト作成
4. コード品質チェック
5. Git commit & push

## 次のステップ

実装を開始するには：

1. **[TODO.yaml](TODO.yaml)** で実装計画を確認
2. **設計書ディレクトリ** で詳細仕様を確認：
   - `note/基本設計書_20250809.md`
   - `note/詳細内部設計_20250809.md`
   - `note/アプリケーション層設計_20250809.md`
   - `note/インフラ・プラグイン設計_20250809.md`
   - `note/プレゼンテーション層設計_20250809.md`

## 詳細ドキュメント

- [開発環境セットアップガイド](DEVELOPMENT_SETUP.md) - 開発準備の詳細
- [設計書](DESIGN.md) - システム設計の詳細
- [プロジェクト構造](PROJECT_STRUCTURE.md) - コード構成の説明
- [TODO リスト](TODO.yaml) - 実装計画とタスク管理

## ライセンス

MIT License
