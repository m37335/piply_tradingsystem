#!/bin/bash

# 開発環境セットアップスクリプト

set -e

echo "🚀 開発環境をセットアップしています..."

# 環境変数ファイルの作成
if [ ! -f .env ]; then
    echo "📝 環境変数ファイルを作成しています..."
    cp env.example .env
    echo "✅ .env ファイルが作成されました。必要に応じて設定を編集してください。"
fi

# 必要なディレクトリの作成
echo "📁 必要なディレクトリを作成しています..."
mkdir -p notebooks
mkdir -p logs
mkdir -p data

# Docker環境の構築
echo "🐳 Docker環境を構築しています..."
docker-compose -f docker-compose.dev.yml build

# データベースの初期化
echo "🗄️ データベースを初期化しています..."
docker-compose -f docker-compose.dev.yml up -d postgres redis
sleep 10

# データベースの初期化スクリプトを実行
echo "📊 データベーススキーマを作成しています..."
docker-compose -f docker-compose.dev.yml exec postgres python /docker-entrypoint-initdb.d/init_database.py

# 全サービスの起動
echo "🚀 全サービスを起動しています..."
docker-compose -f docker-compose.dev.yml up -d

# ヘルスチェック
echo "🔍 サービスヘルスチェックを実行しています..."
sleep 30

# 各サービスのヘルスチェック
echo "📊 データ収集サービス:"
docker-compose -f docker-compose.dev.yml exec data_collection_dev python -c "import asyncio; from modules.data_collection.main import health_check; asyncio.run(health_check())"

echo "⏰ スケジューラーサービス:"
docker-compose -f docker-compose.dev.yml exec scheduler_dev python -c "import asyncio; from modules.scheduler.main import health_check; asyncio.run(health_check())"

echo "🤖 LLM分析サービス:"
docker-compose -f docker-compose.dev.yml exec llm_analysis_dev python -c "import asyncio; from modules.llm_analysis.main import health_check; asyncio.run(health_check())"

echo "✅ 開発環境のセットアップが完了しました！"
echo ""
echo "🌐 アクセス可能なサービス:"
echo "  - Grafana: http://localhost:3000 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Jupyter: http://localhost:8888 (token: trading123)"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📝 ログの確認:"
echo "  docker-compose -f docker-compose.dev.yml logs -f [service_name]"
echo ""
echo "🛑 サービスの停止:"
echo "  docker-compose -f docker-compose.dev.yml down"
