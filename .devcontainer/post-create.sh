#!/bin/bash

# 開発環境セットアップスクリプト
echo "🚀 開発環境のセットアップを開始します..."

# システムパッケージの更新とインストール
echo "📦 システムパッケージをインストール中..."
apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    git \
    curl \
    wget \
    vim \
    nano \
    htop \
    tree \
    jq \
    unzip \
    postgresql-client \
    redis-tools \
    ca-certificates \
    gnupg \
    lsb-release

# Dockerクライアントのインストール（オプション）
echo "🐳 Dockerクライアントをインストール中..."
curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update && apt-get install -y docker-ce-cli docker-compose-plugin

echo "ℹ️ Dockerコマンドはホストシステムで実行してください"

# Pythonパッケージの確認とインストール
echo "📦 Pythonパッケージをインストール中..."
pip install --upgrade pip
pip install -r requirements.txt

# 開発用追加パッケージのインストール
echo "🔧 開発用パッケージをインストール中..."
pip install --no-cache-dir \
    jupyter \
    ipykernel \
    notebook \
    ipywidgets \
    matplotlib \
    seaborn \
    plotly \
    streamlit \
    fastapi \
    uvicorn

# Jupyterカーネルの設定
echo "📓 Jupyterカーネルを設定中..."
python -m ipykernel install --user --name=exchange-analytics --display-name="Exchange Analytics"

# 便利なエイリアスを追加
echo "⚡ 便利なエイリアスを設定中..."
cat >> ~/.bashrc << 'EOF'

# Exchange Analytics 開発用エイリアス
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'

# プロジェクト用エイリアス
alias test-db='python /workspace/test_db_connection.py'
alias test-redis='python /workspace/test_redis_connection.py'
alias run-tests='python -m pytest tests/ -v'
alias format-code='black . && flake8 .'
alias lint-code='mypy .'

# データベース関連
alias db-shell='psql -h localhost -U postgres -d trading_system'
alias redis-shell='redis-cli -h localhost -p 6379'

# サービス関連（ホストで実行）
alias start-services='echo "ホストで実行: cd /Volumes/OWC\ Express\ 1M2/Documents/exchangingApp && docker compose -f docker/docker-compose.dev.yml up -d postgres redis"'
alias stop-services='echo "ホストで実行: cd /Volumes/OWC\ Express\ 1M2/Documents/exchangingApp && docker compose -f docker/docker-compose.dev.yml down"'
alias logs-postgres='echo "ホストで実行: docker logs trading_postgres_dev"'
alias logs-redis='echo "ホストで実行: docker logs trading_redis_dev"'
alias docker-status='echo "ホストで実行: docker ps -a"'
alias docker-logs='echo "ホストで実行: docker compose -f docker/docker-compose.dev.yml logs -f"'

EOF

# データベース接続テスト用のスクリプト作成
echo "🗄️ データベース接続テストスクリプトを作成中..."
cat > /workspace/test_db_connection.py << 'EOF'
#!/usr/bin/env python3
"""
データベース接続テストスクリプト
"""
import asyncio
import asyncpg
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database=os.getenv('DB_NAME', 'trading_system')
        )
        print("✅ データベース接続成功!")
        await conn.close()
    except Exception as e:
        print(f"❌ データベース接続エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
EOF

chmod +x /workspace/test_db_connection.py

# Redis接続テスト用のスクリプト作成
echo "🔴 Redis接続テストスクリプトを作成中..."
cat > /workspace/test_redis_connection.py << 'EOF'
#!/usr/bin/env python3
"""
Redis接続テストスクリプト
"""
import asyncio
import aioredis
import os

async def test_redis():
    try:
        redis = aioredis.from_url(
            f"redis://{os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', 6379)}"
        )
        await redis.ping()
        print("✅ Redis接続成功!")
        await redis.close()
    except Exception as e:
        print(f"❌ Redis接続エラー: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis())
EOF

chmod +x /workspace/test_redis_connection.py

# 環境変数ファイルの確認
echo "📝 環境変数ファイルを確認中..."
if [ ! -f /workspace/.env ]; then
    if [ -f /workspace/env.example ]; then
        echo "📋 .envファイルが見つかりません。env.exampleからコピーしてください:"
        echo "cp env.example .env"
    else
        echo "⚠️ 環境変数ファイルが見つかりません。必要な環境変数を設定してください。"
    fi
fi

# プロジェクト構造の表示
echo "📁 プロジェクト構造:"
tree -L 2 -I '__pycache__|*.pyc|.git' /workspace

echo ""
echo "🎉 開発環境のセットアップが完了しました!"
echo ""
echo "📚 利用可能なコマンド:"
echo "  test-db        - データベース接続テスト"
echo "  test-redis     - Redis接続テスト"
echo "  run-tests      - テスト実行"
echo "  format-code    - コードフォーマット"
echo "  lint-code      - コードリント"
echo "  db-shell       - PostgreSQLシェル"
echo "  redis-shell    - Redisシェル"
echo "  start-services - サービス開始"
echo "  stop-services  - サービス停止"
echo "  docker-status  - Dockerコンテナ状態確認"
echo "  docker-logs    - Dockerログ表示"
echo ""
echo "🗄️ 外部サービス（PostgreSQL、Redis）を起動してください:"
echo "ホストのターミナルで実行:"
echo "cd '/Volumes/OWC Express 1M2/Documents/exchangingApp'"
echo "docker compose -f docker/docker-compose.dev.yml up -d postgres redis"
echo ""
echo "🔍 Dockerデーモンの状態確認:"
echo "ホストのターミナルで実行: docker ps -a"
echo ""
echo "🚀 開発を開始してください!"