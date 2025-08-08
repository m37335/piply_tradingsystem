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

### GitHub 自動更新機能

このアプリケーションには GitHub 自動更新機能が含まれています：

- **自動更新**: GitHub にプッシュすると自動でアプリケーションが更新
- **手動更新**: `/api/github/update` エンドポイントで手動更新
- **リポジトリ情報**: `/api/github/info` で GitHub 連携状況を確認

詳細な設定方法は [GITHUB_SETUP.md](GITHUB_SETUP.md) を参照してください。

### 開発のヒント

- ソースコードの変更は自動で反映されます（ホットリロード）
- データベースや Redis が必要な場合は、docker-compose.yml 内のコメントアウト部分を有効化してください
- 本番環境用の設定は別途作成することをお勧めします
