# DevContainer 開発環境

このディレクトリには、VS Code DevContainerを使用した開発環境の設定が含まれています。

## ファイル構成

- `devcontainer.json` - DevContainerのメイン設定ファイル
- `post-create.sh` - コンテナ作成後のセットアップスクリプト

## 使用方法

### 1. 前提条件

- Docker Desktop がインストールされていること
- VS Code がインストールされていること
- Dev Containers 拡張機能がインストールされていること

### 2. DevContainerで開く

1. VS Codeでプロジェクトフォルダを開く
2. コマンドパレット（Cmd+Shift+P）を開く
3. "Dev Containers: Reopen in Container" を選択
4. 初回はコンテナのビルドに時間がかかります

### 3. 外部サービスの起動

DevContainer起動後、以下のコマンドでサービスを起動できます：

```bash
start-services
```

または手動で：

```bash
docker compose -f docker/docker-compose.dev.yml up -d postgres redis
```

利用可能なサービス：
- **PostgreSQL** (port 5432) - メインデータベース
- **Redis** (port 6379) - キャッシュ・セッション管理

**機能**: 
- DevContainer内からDockerコマンドが実行可能
- Dockerソケットが安全にマウントされています
- ホストのDockerデーモンにアクセス可能

### 4. 便利なエイリアス

コンテナ内では以下のエイリアスが利用可能です：

```bash
test-db        # データベース接続テスト
test-redis     # Redis接続テスト
run-tests      # テスト実行
format-code    # コードフォーマット
lint-code      # コードリント
db-shell       # PostgreSQLシェル
redis-shell    # Redisシェル
start-services # サービス開始
stop-services  # サービス停止
docker-status  # Dockerコンテナ状態確認
docker-logs    # Dockerログ表示
```

### 5. 開発ワークフロー

1. **サービス起動**: `start-services`コマンドで起動
2. **コード編集**: VS Codeで直接編集
3. **テスト実行**: `run-tests` でテスト実行
4. **コード品質**: `format-code` と `lint-code` で品質チェック
5. **データベース確認**: `db-shell` でデータベースアクセス
6. **分析作業**: Jupyter Notebook (http://localhost:8888) でデータ分析

### 6. トラブルシューティング

#### コンテナが起動しない場合
```bash
# Dockerサービスの状態確認
docker ps -a

# ログ確認
docker logs trading_dev_container
```

#### データベース接続エラーの場合
```bash
# データベース接続テスト
test-db

# PostgreSQLサービスの確認
docker logs trading_postgres_dev
```

#### ポートが使用中の場合
```bash
# ポート使用状況確認
lsof -i :5432
lsof -i :6379
lsof -i :8888
```

### 7. 環境変数

開発環境では以下の環境変数が設定されています：

- `PYTHONPATH=/workspace`
- `PYTHONUNBUFFERED=1`
- `ENVIRONMENT=development`
- `LOG_LEVEL=DEBUG`

追加の環境変数が必要な場合は、`.env` ファイルを作成してください。

### 8. データ永続化

以下のデータは永続化されています：

- PostgreSQLデータ: `postgres_data_dev` ボリューム
- Redisデータ: `redis_data_dev` ボリューム
- プロジェクトファイル: ホストマシンと同期

### 9. セキュリティ

- 開発環境用の設定のため、本番環境では使用しないでください
- デフォルトパスワードが使用されています（開発環境のみ）
- 本番環境では適切な認証設定を行ってください
