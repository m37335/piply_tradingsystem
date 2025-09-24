#!/bin/bash

# 統合テスト実行スクリプト

set -e

echo "🧪 統合テストを実行しています..."

# テスト環境の準備
echo "📋 テスト環境を準備しています..."
export PYTHONPATH=/app
export ENVIRONMENT=test

# 必要なディレクトリの作成
mkdir -p logs
mkdir -p test_results

# 統合テストの実行
echo "🔍 統合テストを実行しています..."
python -m pytest tests/integration/ -v \
    --tb=short \
    --junitxml=test_results/integration_test_results.xml \
    --html=test_results/integration_test_report.html \
    --self-contained-html \
    --cov=modules \
    --cov-report=html:test_results/coverage_html \
    --cov-report=xml:test_results/coverage.xml \
    --cov-report=term-missing

# テスト結果の確認
if [ $? -eq 0 ]; then
    echo "✅ 統合テストが成功しました！"
    echo "📊 テストレポート: test_results/integration_test_report.html"
    echo "📈 カバレッジレポート: test_results/coverage_html/index.html"
else
    echo "❌ 統合テストが失敗しました。"
    echo "📋 詳細なログを確認してください。"
    exit 1
fi

# システムヘルスチェックの実行
echo "🔍 システムヘルスチェックを実行しています..."
python scripts/system_health_check.py

# 結果の確認
if [ $? -eq 0 ]; then
    echo "✅ システムヘルスチェックが成功しました！"
elif [ $? -eq 2 ]; then
    echo "⚠️ システムヘルスチェックで警告が検出されました。"
else
    echo "❌ システムヘルスチェックが失敗しました。"
    exit 1
fi

echo "🎉 統合テストとヘルスチェックが完了しました！"
