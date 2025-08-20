# Exchange Analytics System - crontab 設定・運用ガイド

## 📋 目次

1. [概要](#概要)
2. [crontab 設定ファイル](#crontab設定ファイル)
3. [実行スクリプト一覧](#実行スクリプト一覧)
4. [ログ管理システム](#ログ管理システム)
5. [監視・アラートシステム](#監視アラートシステム)
6. [運用・メンテナンス](#運用メンテナンス)
7. [トラブルシューティング](#トラブルシューティング)
8. [今後の拡張計画](#今後の拡張計画)

---

## 概要

### 🎯 目的

Exchange Analytics System の crontab 設定は、為替データの自動取得、テクニカル指標計算、AI 分析、システム監視を 24 時間 365 日自動化するためのスケジューリングシステムです。

### 🔧 主要機能

- **データ取得**: 5 分間隔での為替データ自動取得
- **テクニカル分析**: 時間足別の集計・指標計算
- **AI 分析**: 統合 AI 分析の定期実行
- **システム監視**: ヘルスチェック・アラート機能
- **ログ管理**: 自動ローテーション・容量管理
- **API 管理**: 自動起動・復旧機能

### 📊 システム構成図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   crontab       │    │   実行スクリプト │    │   ログ管理      │
│   スケジューラー │───▶│   システム      │───▶│   システム      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   監視・アラート │    │   APIサーバー   │    │   データベース  │
│   システム      │    │   管理          │    │   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## crontab 設定ファイル

### 📁 ファイル構成

#### メイン設定ファイル

- **ファイル**: `current_crontab.txt`
- **場所**: `/app/current_crontab.txt`
- **更新方法**: `crontab current_crontab.txt`

### 🔧 基本設定

```bash
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/app
```

### 📅 実行スケジュール詳細

#### 1. 🔄 継続処理システム（平日 24 時間稼働）

```bash
*/5 * * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 300 python scripts/cron/simple_data_fetcher.py >> /app/logs/simple_data_fetcher.log 2>&1
```

**実行内容**:

- **頻度**: 5 分間隔（平日のみ）
- **スクリプト**: `simple_data_fetcher.py`
- **タイムアウト**: 300 秒（5 分）
- **目的**: 為替データの継続取得

#### 2. 📈 日次レポート

```bash
0 6 * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 120 python scripts/cron/daily_report.py >> /app/logs/daily_cron.log 2>&1
```

**実行内容**:

- **頻度**: 毎日 6:00 JST
- **スクリプト**: `daily_report.py`
- **タイムアウト**: 120 秒（2 分）
- **目的**: 日次分析レポート生成

#### 3. 📊 週次統計・レポート

```bash
0 6 * * 6 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 180 python scripts/cron/weekly_report.py >> /app/logs/weekly_cron.log 2>&1
```

**実行内容**:

- **頻度**: 毎週土曜日 6:00 JST
- **スクリプト**: `weekly_report.py`
- **タイムアウト**: 180 秒（3 分）
- **目的**: 週次統計レポート生成

#### 4. 🔍 システムヘルスチェック

```bash
*/30 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 10 python scripts/monitoring/realtime_monitor.py --interval 1 --no-alerts >> /app/logs/health_cron.log 2>&1
```

**実行内容**:

- **頻度**: 30 分間隔
- **スクリプト**: `realtime_monitor.py`
- **タイムアウト**: 10 秒
- **目的**: API サーバー・システム監視

#### 5. 🗑️ ログローテーション

```bash
0 2 * * * cd /app/logs && find . -name "*.log" -size +10M -exec gzip {} \; && find . -name "*.gz" -mtime +7 -delete >> /app/logs/cleanup.log 2>&1
```

**実行内容**:

- **頻度**: 毎日 2:00 JST
- **処理**: 10MB 以上のログを圧縮、7 日以上古い.gz ファイルを削除
- **目的**: ログファイルの容量管理

#### 6. 🔍 エラーログ監視

```bash
*/10 * * * * [ -f /app/logs/continuous_processing_cron.log ] && tail -10 /app/logs/continuous_processing_cron.log | grep -i "error\|failed" && echo "$(date): Continuous processing errors detected" >> /app/logs/error_alert.log
```

**実行内容**:

- **頻度**: 10 分間隔
- **処理**: エラーログの監視・検知
- **目的**: 継続処理エラーの早期発見

#### 7. 🧪 環境変数テスト

```bash
0 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 30 python tests/integration/test_env_loading.py >> /app/logs/env_test_cron.log 2>&1
```

**実行内容**:

- **頻度**: 1 時間間隔
- **スクリプト**: `test_env_loading.py`
- **タイムアウト**: 30 秒
- **目的**: 環境変数の正常性確認

#### 8. 🤖 統合 AI 分析（平日）

```bash
0 8,9,10,12,14,16,18,19,20,21,22,23,0,2 * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 180 python scripts/cron/integrated_ai_discord.py >> /app/logs/integrated_ai_cron.log 2>&1
```

**実行内容**:

- **頻度**: 2 時間間隔（8:00-2:00）
- **スクリプト**: `integrated_ai_discord.py`
- **タイムアウト**: 180 秒（3 分）
- **目的**: AI 分析・Discord 通知

#### 9. 🤖 統合 AI 分析（土曜日）

```bash
0 8,9,10,12,14,16,18,19,20,21,22,23,0,2,4,6 * * 6 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 180 python scripts/cron/integrated_ai_discord.py >> /app/logs/integrated_ai_cron.log 2>&1
```

**実行内容**:

- **頻度**: 2 時間間隔（8:00-6:00）
- **スクリプト**: `integrated_ai_discord.py`
- **タイムアウト**: 180 秒（3 分）
- **目的**: AI 分析・Discord 通知（土曜日限定）

#### 10. 🔍 継続処理システム健全性チェック

```bash
0 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 60 python scripts/cron/continuous_processing_cron.py --health-check-only >> /app/logs/health_check_cron.log 2>&1
```

**実行内容**:

- **頻度**: 1 時間間隔
- **スクリプト**: `continuous_processing_cron.py`
- **タイムアウト**: 60 秒
- **目的**: 継続処理システムの健全性確認

#### 11. 🚀 API サーバー自動起動

```bash
*/5 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 30 ./exchange-analytics api status > /dev/null 2>&1 || (timeout 60 ./exchange-analytics api start --background >> /app/logs/api_auto_start.log 2>&1)
```

**実行内容**:

- **頻度**: 5 分間隔
- **処理**: API サーバー状態確認・自動起動
- **タイムアウト**: 30 秒（確認）+ 60 秒（起動）
- **目的**: API サーバーの常時稼働保証

#### 12. 📊 時間足集計システム

##### 1 時間足集計

```bash
5 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 60 python scripts/cron/hourly_aggregator.py >> /app/logs/hourly_aggregator.log 2>&1
```

##### 4 時間足集計

```bash
10 0,4,8,12,16,20 * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 90 python scripts/cron/four_hour_aggregator.py >> /app/logs/four_hour_aggregator.log 2>&1
```

##### 日足集計

```bash
15 0 * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 120 python scripts/cron/daily_aggregator.py >> /app/logs/daily_aggregator.log 2>&1
```

---

## 実行スクリプト一覧

### 📁 スクリプトディレクトリ構成

```
scripts/
├── cron/                          # 定期実行スクリプト
│   ├── simple_data_fetcher.py     # 5分間隔データ取得
│   ├── daily_report.py            # 日次レポート
│   ├── weekly_report.py           # 週次レポート
│   ├── integrated_ai_discord.py   # 統合AI分析
│   ├── continuous_processing_cron.py # 継続処理健全性チェック
│   ├── hourly_aggregator.py       # 1時間足集計
│   ├── four_hour_aggregator.py    # 4時間足集計
│   ├── daily_aggregator.py        # 日足集計
│   └── base_aggregator.py         # 集計基底クラス
├── monitoring/                    # 監視スクリプト
│   └── realtime_monitor.py        # リアルタイム監視
└── tests/                         # テストスクリプト
    └── integration/
        └── test_env_loading.py    # 環境変数テスト
```

### 🔧 主要スクリプト詳細

#### 1. `simple_data_fetcher.py`

**目的**: 為替データの継続取得
**機能**:

- Yahoo Finance API からのデータ取得
- PostgreSQL データベースへの保存
- API 制限対応
- エラーハンドリング

#### 2. `integrated_ai_discord.py`

**目的**: AI 分析と Discord 通知
**機能**:

- テクニカル指標分析
- パターン検出
- Discord Webhook 通知
- 分析結果のデータベース保存

#### 3. `realtime_monitor.py`

**目的**: システム監視・アラート
**機能**:

- API サーバーヘルスチェック
- システムリソース監視
- Discord アラート通知
- アラートデータベース保存

#### 4. `hourly_aggregator.py`

**目的**: 1 時間足データ集計
**機能**:

- 5 分足データから 1 時間足を集計
- OHLCV 計算
- 重複チェック
- PostgreSQL 保存

#### 5. `four_hour_aggregator.py`

**目的**: 4 時間足データ集計
**機能**:

- 5 分足データから 4 時間足を集計
- 4 時間単位での期間計算
- データベース保存

#### 6. `daily_aggregator.py`

**目的**: 日足データ集計
**機能**:

- 5 分足データから日足を集計
- 前日のデータを対象
- 日次 OHLCV 計算

---

## ログ管理システム

### 📁 ログディレクトリ構成

```
/app/logs/
├── simple_data_fetcher.log        # データ取得ログ
├── integrated_ai_cron.log         # AI分析ログ
├── health_cron.log                # ヘルスチェックログ
├── health_check_cron.log          # 健全性チェックログ
├── hourly_aggregator.log          # 1時間足集計ログ
├── four_hour_aggregator.log       # 4時間足集計ログ
├── daily_aggregator.log           # 日足集計ログ
├── api_auto_start.log             # API自動起動ログ
├── error_alert.log                # エラーアラートログ
├── env_test_cron.log              # 環境変数テストログ
├── cleanup.log                    # ログローテーションログ
└── archive/                       # 圧縮ログ保存
```

### 🔄 ログローテーション仕組み

#### 自動ローテーション設定

```bash
# 毎日2:00 JSTに実行
0 2 * * * cd /app/logs && find . -name "*.log" -size +10M -exec gzip {} \; && find . -name "*.gz" -mtime +7 -delete >> /app/logs/cleanup.log 2>&1
```

#### ローテーション条件

- **サイズ制限**: 10MB 以上のログファイルを圧縮
- **圧縮形式**: gzip 形式（.gz）
- **保持期間**: 7 日間後に自動削除
- **実行時刻**: 毎日 2:00 JST

### 📊 ログ監視機能

#### エラーログ監視

```bash
# 10分間隔でエラーログを監視
*/10 * * * * [ -f /app/logs/continuous_processing_cron.log ] && tail -10 /app/logs/continuous_processing_cron.log | grep -i "error\|failed" && echo "$(date): Continuous processing errors detected" >> /app/logs/error_alert.log
```

#### 監視対象

- **ファイル**: `continuous_processing_cron.log`
- **検索キーワード**: "error", "failed"
- **通知先**: `error_alert.log`
- **間隔**: 10 分間隔

---

## 監視・アラートシステム

### 🔍 監視対象

#### 1. API サーバー監視

- **対象**: `http://localhost:8000`
- **エンドポイント**: `/api/v1/health`
- **間隔**: 30 分間隔
- **アラート**: 接続失敗時に Discord 通知

#### 2. システムリソース監視

- **CPU 使用率**: 警告 70%、危険 90%
- **メモリ使用率**: 警告 80%、危険 95%
- **ディスク使用率**: 警告 85%、危険 95%

#### 3. データ取得監視

- **継続処理**: 5 分間隔データ取得の監視
- **エラー検知**: 連続失敗時のアラート
- **健全性チェック**: 1 時間間隔

### 🚨 アラートシステム

#### Discord 通知設定

```yaml
alert_type_webhooks:
  system_resource: "${DISCORD_MONITORING_WEBHOOK_URL}"
  api_error: "${DISCORD_MONITORING_WEBHOOK_URL}"
  data_fetch_error: "${DISCORD_MONITORING_WEBHOOK_URL}"
  rate_threshold: "${DISCORD_WEBHOOK_URL}"
  pattern_detection: "${DISCORD_WEBHOOK_URL}"
```

#### アラートタイプ

- **system_resource**: システムリソース監視
- **api_error**: API 接続エラー
- **data_fetch_error**: データ取得エラー
- **rate_threshold**: 為替レート閾値
- **pattern_detection**: パターン検出

---

## 運用・メンテナンス

### 🔧 日常運用

#### 1. crontab 管理

```bash
# crontab確認
crontab -l

# crontab更新
crontab current_crontab.txt

# crontab編集
crontab -e
```

#### 2. ログ確認

```bash
# 特定ログの確認
tail -f /app/logs/health_cron.log

# エラーログの確認
tail -f /app/logs/error_alert.log

# ログサイズ確認
du -sh /app/logs/
```

#### 3. システム状態確認

```bash
# APIサーバー状態
./exchange-analytics api status

# アラート確認
./exchange-analytics monitor alerts

# データベース状態
./exchange-analytics data show status
```

### 🛠️ メンテナンス作業

#### 1. 定期メンテナンス

- **ログローテーション**: 毎日 2:00 自動実行
- **データベース最適化**: 必要に応じて手動実行
- **ディスク容量確認**: 週次確認

#### 2. 緊急対応

- **API サーバー停止**: 自動起動機能で復旧
- **データ取得エラー**: エラーログ監視で早期発見
- **システムリソース不足**: アラートで即座に通知

---

## トラブルシューティング

### 🚨 よくある問題と解決方法

#### 1. crontab が実行されない

**原因**: 環境変数が設定されていない
**解決方法**:

```bash
# 環境変数確認
source .env
echo $DATABASE_URL

# crontab再設定
crontab current_crontab.txt
```

#### 2. ログファイルが大きくなりすぎる

**原因**: ログローテーションが正常に動作していない
**解決方法**:

```bash
# 手動ログローテーション
cd /app/logs && find . -name "*.log" -size +10M -exec gzip {} \;

# ログローテーション設定確認
crontab -l | grep "ログローテーション"
```

#### 3. API サーバーが起動しない

**原因**: ポート競合、設定エラー
**解決方法**:

```bash
# プロセス確認
ps aux | grep uvicorn

# ポート確認
netstat -tlnp | grep 8000

# 手動起動
./exchange-analytics api start
```

#### 4. データベース接続エラー

**原因**: PostgreSQL が停止、認証エラー
**解決方法**:

```bash
# PostgreSQL状態確認
systemctl status postgresql

# 接続テスト
psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db
```

### 📊 監視・診断コマンド

#### システム状態確認

```bash
# 全体的な状態確認
./exchange-analytics monitor health

# アラート確認
./exchange-analytics monitor alerts

# パフォーマンス確認
./exchange-analytics monitor performance
```

#### ログ分析

```bash
# エラー検索
grep -i "error" /app/logs/*.log

# 最新ログ確認
tail -100 /app/logs/health_cron.log

# ログ統計
wc -l /app/logs/*.log
```

---

## 今後の拡張計画

### 🚀 短期計画（1-3 ヶ月）

#### 1. 監視機能強化

- **メトリクス収集**: Prometheus 連携
- **ダッシュボード**: Grafana 統合
- **アラート拡張**: Slack 連携追加

#### 2. ログ管理改善

- **構造化ログ**: JSON 形式ログ
- **ログ分析**: ELK Stack 統合
- **ログ検索**: 全文検索機能

#### 3. 自動化強化

- **自動復旧**: より高度な復旧ロジック
- **スケーリング**: 負荷に応じた自動スケーリング
- **バックアップ**: 自動バックアップ機能

### 🌟 中期計画（3-6 ヶ月）

#### 1. 分散化対応

- **マルチサーバー**: 複数サーバーでの分散実行
- **負荷分散**: ロードバランサー導入
- **高可用性**: 冗長化システム

#### 2. セキュリティ強化

- **認証・認可**: より強固な認証システム
- **暗号化**: データ暗号化
- **監査ログ**: セキュリティ監査機能

#### 3. パフォーマンス最適化

- **キャッシュ**: Redis 連携
- **非同期処理**: Celery 導入
- **データベース最適化**: クエリ最適化

### 🎯 長期計画（6 ヶ月以上）

#### 1. AI/ML 統合

- **予測モデル**: 機械学習モデル統合
- **自動最適化**: パラメータ自動調整
- **異常検知**: 高度な異常検知システム

#### 2. クラウド移行

- **コンテナ化**: Docker/Kubernetes
- **クラウドネイティブ**: クラウド最適化
- **マイクロサービス**: サービス分割

#### 3. 国際化対応

- **多通貨対応**: 複数通貨ペア対応
- **多言語対応**: 多言語インターフェース
- **グローバル展開**: 世界各地での運用

---

## 📚 関連ドキュメント

- [CLI 機能説明書](./2025-08-15_CLI機能_ExchangeAnalyticsSystem_CLI機能説明書.md)
- [アラートシステム設計書](./2025-08-16_アラートシステム_ExchangeAnalyticsSystem_アラートシステム設計・実装ガイド.md)
- [システム設計書](../note/アーキテクチャ設計/2025-08-09_基本設計_基本設計書.md)
- [データベース設計書](../note/データベース/PostgreSQL_MIGRATION_README.md)

---

**作成日**: 2025 年 8 月 16 日  
**更新日**: 2025 年 8 月 16 日  
**バージョン**: 1.0.0  
**対象システム**: Exchange Analytics System crontab 設定・運用
