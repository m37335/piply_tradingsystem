# Exchanging App

Python Flask を使用した Web アプリケーションの Docker 開発環境

## 開発環境のセットアップ

### 必要なツール

- Docker
- Docker Compose

### 環境構築手順

1. **環境変数ファイルの作成**

   ```bash
   cp env.example .env
   ```

2. **Docker コンテナの構築と起動**

   ```bash
   docker-compose up --build
   ```

3. **アプリケーションの確認**
   - http://localhost:8000 でアプリケーションにアクセス
   - http://localhost:8000/api/health でヘルスチェック
   - http://localhost:8000/api/github/info で GitHub 連携状況確認

### 開発用コマンド

```bash
# コンテナの起動
docker-compose up

# バックグラウンドで起動
docker-compose up -d

# コンテナの停止
docker-compose down

# コンテナ内でコマンド実行
docker-compose exec app bash

# Pythonシェルの起動
docker-compose exec app python

# テストの実行
docker-compose exec app pytest

# コードフォーマット
docker-compose exec app black .
docker-compose exec app isort .

# Linting
docker-compose exec app flake8 .
```

### プロジェクト構造

```
exchangingApp/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
├── env.example
├── app.py                # メインアプリケーション
└── README.md
```

### 為替分析機能

このアプリケーションは高機能な為替分析システムです：

#### 🔥 主要機能

- **リアルタイム為替データ取得・分析**
- **AI 市場分析レポート** (ChatGPT-4 API 使用)
- **テクニカル指標計算** (SMA, RSI, MACD 等)
- **Discord 自動通知** (毎朝 8 時 + イベント駆動)
- **プラグインシステム** (指標・分析アルゴリズムを拡張可能)

#### 📊 分析機能

- **テクニカル分析**: 移動平均、RSI、MACD、ボリンジャーバンド等
- **AI 分析**: ChatGPT-4 による総合的な市場分析とレポート生成
- **自動シグナル**: 売買タイミングの自動検出
- **カスタム分析**: プラグインによる独自分析手法の追加

#### 🤖 AI 分析レポート

- **毎朝 8 時の定期レポート**: 市場概況・テクニカル・推奨戦略
- **Discord 配信**: 美しい Embed 形式でのレポート自動送信
- **カスタムテンプレート**: レポート形式の柔軟なカスタマイズ

### GitHub 自動更新機能

開発効率化のための GitHub 連携：

- **自動デプロイ**: GitHub プッシュ時の自動更新
- **手動更新**: `/api/github/update` エンドポイント
- **連携状況確認**: `/api/github/info` で状況確認

### プラグインシステム

将来の機能拡張に対応：

- **テクニカル指標**: 新しい指標を簡単に追加
- **分析アルゴリズム**: カスタム分析ロジックの実装
- **レポートテンプレート**: 独自のレポート形式作成
- **動的設定**: 運用中の設定変更・プラグイン追加

詳細な設計は [DESIGN.md](DESIGN.md) および [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) を参照してください。

### 開発のヒント

- ソースコードの変更は自動で反映されます（ホットリロード）
- データベースや Redis が必要な場合は、docker-compose.yml 内のコメントアウト部分を有効化してください
- 本番環境用の設定は別途作成することをお勧めします
