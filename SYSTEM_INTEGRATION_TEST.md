# 🧪 システム統合テスト

**Exchange Analytics System - 統合テスト・動作確認ガイド**

## 📋 概要

このドキュメントは、Exchange Analytics System の全機能を統合テストし、システム全体の動作を確認するためのガイドです。

## ✅ 事前準備

### 1. 依存関係の確認

```bash
# Python バージョン確認
python --version  # 3.11+ 必要

# 依存パッケージ確認
pip list | grep -E "(fastapi|typer|rich|sqlalchemy|redis)"
```

### 2. システム起動確認

```bash
# CLI 動作確認
./exchange-analytics --version
./exchange-analytics --help

# システム状態確認
./exchange-analytics status
```

## 🌐 API Layer テスト

### 1. API サーバー起動テスト

```bash
# バックグラウンドでAPI起動
./exchange-analytics api start --background

# 起動確認
./exchange-analytics api status

# 基本ヘルスチェック
curl http://localhost:8000/api/v1/health

# 詳細ヘルスチェック
curl http://localhost:8000/api/v1/health/detailed
```

**期待結果:**

- HTTP 200 OK
- `"status": "healthy"` または `"status": "degraded"`
- 各コンポーネントの状態情報

### 2. Swagger UI テスト

```bash
# ブラウザで確認
# http://localhost:8000/docs

# ReDoc確認
# http://localhost:8000/redoc

# OpenAPI スキーマ取得
curl http://localhost:8000/openapi.json
```

**期待結果:**

- Swagger UI が正常に表示
- 25 個の API エンドポイントが表示
- インタラクティブなテストが可能

### 3. 為替レート API テスト

```bash
# 最新レート取得
curl "http://localhost:8000/api/v1/rates/latest"

# 特定通貨ペア取得
curl "http://localhost:8000/api/v1/rates/USD/JPY?limit=10"

# レート取得トリガー
curl -X POST "http://localhost:8000/api/v1/rates/fetch" \
  -H "Content-Type: application/json" \
  -d '["USD/JPY", "EUR/USD"]'
```

**期待結果:**

- JSON 形式のレスポンス
- `"success": true`
- 適切な為替レートデータ

### 4. 分析 API テスト

```bash
# テクニカル分析
curl "http://localhost:8000/api/v1/analysis/technical/USD/JPY?indicators=sma,rsi,macd"

# トレンド分析
curl "http://localhost:8000/api/v1/analysis/trend/USD/JPY?timeframe=1d"

# ボラティリティ分析
curl "http://localhost:8000/api/v1/analysis/volatility/USD/JPY?period=30"

# カスタム分析
curl -X POST "http://localhost:8000/api/v1/analysis/custom" \
  -H "Content-Type: application/json" \
  -d '{"currency_pair": "USD/JPY", "analysis_type": "momentum"}'
```

**期待結果:**

- 各種テクニカル指標データ
- トレンド・ボラティリティ分析結果
- 信頼度スコア付きの分析結果

### 5. AI レポート API テスト

```bash
# AIレポート生成
curl -X POST "http://localhost:8000/api/v1/ai-reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"currency_pair": "USD/JPY", "analysis_period": "1d"}'

# レポート一覧取得
curl "http://localhost:8000/api/v1/ai-reports?limit=5"
```

**期待結果:**

- AI 分析レポートの生成結果
- 信頼度スコア・生成時刻
- レポート一覧の取得

### 6. アラート API テスト

```bash
# アラート一覧取得
curl "http://localhost:8000/api/v1/alerts?active_only=true"

# アラート作成
curl -X POST "http://localhost:8000/api/v1/alerts" \
  -H "Content-Type: application/json" \
  -d '{
    "currency_pair": "USD/JPY",
    "condition": "rate_above",
    "threshold": 151.0,
    "notification_method": "discord"
  }'
```

**期待結果:**

- アラート一覧の取得
- 新規アラート作成の確認

### 7. プラグイン API テスト

```bash
# プラグイン一覧取得
curl "http://localhost:8000/api/v1/plugins"

# 特定プラグイン情報
curl "http://localhost:8000/api/v1/plugins/sma_indicator"
```

**期待結果:**

- 利用可能プラグインの一覧
- プラグインの詳細情報

## 🖥️ CLI Layer テスト

### 1. システム管理コマンド

```bash
# システム情報表示
./exchange-analytics info

# システム状態確認
./exchange-analytics status

# バージョン情報
./exchange-analytics --version
```

**期待結果:**

- システム情報の詳細表示
- 各コンポーネントの状態確認
- バージョン・コンポーネント情報

### 2. API 管理コマンド

```bash
# API ヘルスチェック
./exchange-analytics api health

# 詳細ヘルスチェック
./exchange-analytics api health --detailed

# メトリクス取得
./exchange-analytics api metrics

# API サーバー停止・再起動
./exchange-analytics api stop
./exchange-analytics api restart
```

**期待結果:**

- ヘルスチェック結果の表示
- システムメトリクスの表示
- サーバー管理操作の成功

### 3. データ管理コマンド

```bash
# データベース状態確認
./exchange-analytics data status

# データ取得シミュレーション
./exchange-analytics data fetch --pairs "USD/JPY,EUR/USD" --days 7

# データベース初期化 (テスト環境のみ)
# ./exchange-analytics data init --force
```

**期待結果:**

- データベーステーブル状態の表示
- プログレスバー付きデータ取得
- データベース操作の成功

### 4. 設定管理コマンド

```bash
# 設定表示
./exchange-analytics config show

# 設定をツリー表示
./exchange-analytics config tree

# 環境変数確認
./exchange-analytics config env

# 設定検証
./exchange-analytics config validate
```

**期待結果:**

- 設定の階層表示
- 環境変数の状態確認
- 設定検証結果の表示

### 5. 監視コマンド

```bash
# ヘルスチェック
./exchange-analytics monitor health

# 詳細ヘルスチェック
./exchange-analytics monitor health --detailed

# システムメトリクス
./exchange-analytics monitor metrics

# ログ表示
./exchange-analytics monitor logs --lines 20

# アラート確認
./exchange-analytics monitor alerts
```

**期待結果:**

- ヘルスチェック結果の詳細表示
- システムメトリクスの表示
- ログエントリの表示
- アクティブアラートの表示

## 🔄 統合シナリオテスト

### シナリオ 1: 通常運用フロー

```bash
# 1. システム起動
./exchange-analytics api start --background

# 2. 状態確認
./exchange-analytics status

# 3. データ取得
./exchange-analytics data fetch --pairs "USD/JPY"

# 4. 分析実行 (API経由)
curl "http://localhost:8000/api/v1/analysis/technical/USD/JPY?indicators=sma,rsi"

# 5. AIレポート生成
curl -X POST "http://localhost:8000/api/v1/ai-reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"currency_pair": "USD/JPY"}'

# 6. 監視確認
./exchange-analytics monitor health --detailed
./exchange-analytics monitor metrics
```

### シナリオ 2: 設定・運用管理

```bash
# 1. 環境確認
./exchange-analytics config env

# 2. 設定確認
./exchange-analytics config show

# 3. 設定検証
./exchange-analytics config validate

# 4. データベース状態確認
./exchange-analytics data status

# 5. システム監視
./exchange-analytics monitor health
./exchange-analytics monitor logs --lines 50
```

### シナリオ 3: エラー・復旧テスト

```bash
# 1. API停止
./exchange-analytics api stop

# 2. 状態確認 (エラー状態)
./exchange-analytics api status

# 3. 再起動
./exchange-analytics api restart

# 4. 復旧確認
./exchange-analytics api health
./exchange-analytics status
```

## 📊 パフォーマンステスト

### 1. API レスポンス時間

```bash
# ヘルスチェック レスポンス時間
time curl -s http://localhost:8000/api/v1/health

# 複数リクエストの平均時間
for i in {1..10}; do
  time curl -s http://localhost:8000/api/v1/rates/latest > /dev/null
done
```

**期待結果:**

- ヘルスチェック: < 50ms
- データ取得: < 200ms

### 2. 並行処理テスト

```bash
# 並行リクエスト (バックグラウンド実行)
for i in {1..5}; do
  curl -s "http://localhost:8000/api/v1/rates/USD/JPY" &
done
wait

# CLI並行実行
./exchange-analytics monitor metrics &
./exchange-analytics monitor health &
wait
```

**期待結果:**

- 並行リクエストの正常処理
- レスポンス時間の大幅な劣化なし

### 3. メモリ・CPU 使用量

```bash
# システムメトリクス監視
./exchange-analytics monitor metrics --live

# プロセス監視 (別ターミナル)
top -p $(pgrep -f uvicorn)
htop
```

**期待結果:**

- CPU 使用率: < 50% (通常時)
- メモリ使用量: < 500MB
- リークのない安定した使用量

## 🔐 セキュリティテスト

### 1. 認証テスト

```bash
# 認証なしアクセス (パブリックエンドポイント)
curl http://localhost:8000/api/v1/health

# 認証なしアクセス (保護されたエンドポイント)
curl http://localhost:8000/api/v1/plugins
```

**期待結果:**

- パブリックエンドポイント: HTTP 200
- 保護されたエンドポイント: HTTP 401 (実装に依存)

### 2. レート制限テスト

```bash
# 大量リクエスト送信
for i in {1..100}; do
  curl -s http://localhost:8000/api/v1/health
  sleep 0.1
done
```

**期待結果:**

- 制限到達後: HTTP 429 Too Many Requests
- 適切なリトライ情報の提供

### 3. 入力検証テスト

```bash
# 無効な通貨ペア
curl "http://localhost:8000/api/v1/rates/INVALID"

# 無効なJSON
curl -X POST "http://localhost:8000/api/v1/ai-reports/generate" \
  -H "Content-Type: application/json" \
  -d '{"invalid": json}'

# SQLインジェクション試行
curl "http://localhost:8000/api/v1/rates/USD'; DROP TABLE users; --"
```

**期待結果:**

- HTTP 400 Bad Request または 422 Unprocessable Entity
- 適切なエラーメッセージ
- システムの安全性維持

## ✅ 統合テスト チェックリスト

### 基本機能

- [ ] CLI ヘルプ・バージョン表示
- [ ] システム状態確認
- [ ] API サーバー起動・停止・再起動
- [ ] ヘルスチェック (基本・詳細)
- [ ] Swagger UI アクセス

### API 機能

- [ ] 為替レート取得 (最新・履歴)
- [ ] テクニカル分析 (SMA, RSI, MACD)
- [ ] トレンド・ボラティリティ分析
- [ ] AI レポート生成・取得
- [ ] アラート管理
- [ ] プラグイン情報取得

### CLI 機能

- [ ] データ管理コマンド
- [ ] 設定管理コマンド
- [ ] 監視コマンド
- [ ] ログ表示・フィルタリング
- [ ] リアルタイム監視

### 非機能要件

- [ ] レスポンス時間 (< 200ms)
- [ ] 並行処理対応
- [ ] メモリ・CPU 使用量
- [ ] エラーハンドリング
- [ ] 入力検証
- [ ] セキュリティヘッダー

### 運用機能

- [ ] ログローテーション
- [ ] メトリクス収集
- [ ] アラート通知
- [ ] 設定のホットリロード
- [ ] グレースフルシャットダウン

## 🎯 合格基準

### 機能テスト

- **全 API エンドポイント**: HTTP 200/201/400/401/422 の適切なレスポンス
- **全 CLI コマンド**: 正常終了・適切な出力
- **エラー処理**: 適切なエラーメッセージ・HTTP ステータス

### パフォーマンス

- **API レスポンス**: 平均 < 200ms
- **CPU 使用率**: 通常時 < 50%
- **メモリ使用量**: < 500MB
- **並行処理**: 50 並行リクエスト処理可能

### セキュリティ

- **認証・認可**: 適切なアクセス制御
- **入力検証**: 無効入力の適切な処理
- **レート制限**: 制限超過時の適切な制御

### 運用性

- **監視**: ヘルスチェック・メトリクス取得
- **ログ**: 適切なログレベル・構造化ログ
- **設定**: 動的設定変更・検証

---

**📊 Exchange Analytics System** - _Production-Ready Integration Testing_
