#!/bin/bash

# 本番環境デプロイスクリプト

set -e

echo "🚀 本番環境をデプロイしています..."

# 環境変数の確認
if [ -z "$LLM_API_KEY" ]; then
    echo "❌ LLM_API_KEY が設定されていません。"
    echo "export LLM_API_KEY=your_api_key_here"
    exit 1
fi

# 環境変数ファイルの確認
if [ ! -f .env ]; then
    echo "❌ .env ファイルが見つかりません。"
    echo "env.example をコピーして .env を作成し、本番環境用に設定を編集してください。"
    exit 1
fi

# 必要なディレクトリの作成
echo "📁 必要なディレクトリを作成しています..."
mkdir -p logs
mkdir -p data

# Docker環境の構築
echo "🐳 Docker環境を構築しています..."
docker-compose -f docker-compose.prod.yml build

# 既存のサービスの停止
echo "🛑 既存のサービスを停止しています..."
docker-compose -f docker-compose.prod.yml down

# データベースの起動
echo "🗄️ データベースを起動しています..."
docker-compose -f docker-compose.prod.yml up -d postgres redis
sleep 15

# データベースの初期化
echo "📊 データベーススキーマを作成しています..."
docker-compose -f docker-compose.prod.yml exec postgres python /docker-entrypoint-initdb.d/init_database.py

# 全サービスの起動
echo "🚀 全サービスを起動しています..."
docker-compose -f docker-compose.prod.yml up -d

# ヘルスチェック
echo "🔍 サービスヘルスチェックを実行しています..."
sleep 30

# 各サービスのヘルスチェック
echo "📊 データ収集サービス:"
docker-compose -f docker-compose.prod.yml exec data_collection python -c "import asyncio; from modules.data_collection.main import health_check; asyncio.run(health_check())"

echo "⏰ スケジューラーサービス:"
docker-compose -f docker-compose.prod.yml exec scheduler python -c "import asyncio; from modules.scheduler.main import health_check; asyncio.run(health_check())"

echo "🤖 LLM分析サービス:"
docker-compose -f docker-compose.prod.yml exec llm_analysis python -c "import asyncio; from modules.llm_analysis.main import health_check; asyncio.run(health_check())"

echo "✅ 本番環境のデプロイが完了しました！"
echo ""
echo "🌐 アクセス可能なサービス:"
echo "  - Grafana: http://localhost:3000 (admin/${GRAFANA_PASSWORD:-admin})"
echo "  - Prometheus: http://localhost:9090"
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo ""
echo "📝 ログの確認:"
echo "  docker-compose -f docker-compose.prod.yml logs -f [service_name]"
echo ""
echo "🛑 サービスの停止:"
echo "  docker-compose -f docker-compose.prod.yml down"
echo ""
echo "🔄 サービスの再起動:"
echo "  docker-compose -f docker-compose.prod.yml restart [service_name]"
