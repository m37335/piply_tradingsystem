# Scripts Directory

## 概要

Exchange Analytics USD/JPY パターン検出システムの運用・管理スクリプトを管理するディレクトリです。24 時間自動稼働システムの実行、監視、デプロイメント、テストを担当します。

## 保存されているファイル

### 新規整理されたサブディレクトリ

- `analysis/` - 分析・デバッグスクリプト（18 ファイル）
- `development/` - 開発・実装スクリプト（3 ファイル）
- `database/` - データベース関連スクリプト（4 ファイル）

### 既存のサブディレクトリ

- `cron/` - 定期実行スクリプト（本番稼働）
- `monitoring/` - システム監視・ヘルスチェック
- `deployment/` - デプロイメント・環境構築
- `migration/` - データベース移行
- `test/` - テスト・検証スクリプト
- `data/` - データ処理・分析
- `cleanup/` - データクリーンアップ
- `archive/` - アーカイブスクリプト
- `setup/` - 初期セットアップ

## よく編集するファイル

- `cron/`内の本番稼働スクリプト
- `test/`内のテストスクリプト
- `monitoring/`内の監視スクリプト

## 注意事項

- 本番稼働スクリプトの変更は慎重に行う
- テスト環境での検証を必ず実施
- ログファイルの監視を継続
- バックアップを定期的に取得

## 🗂️ ディレクトリ構造

```
scripts/
├── cron/              # 定期実行スクリプト（本番稼働）
├── monitoring/        # システム監視・ヘルスチェック
├── deployment/        # デプロイメント・環境構築
├── migration/         # データベース移行
├── test/              # テスト・検証スクリプト
├── data/              # データ処理・分析
├── cleanup/           # データクリーンアップ
├── archive/           # アーカイブスクリプト
├── setup/             # 初期セットアップ
├── deploy.sh          # メインデプロイスクリプト
├── run_phase1.py      # Phase 1 実行スクリプト
├── run_phase2.py      # Phase 2 実行スクリプト
├── yahoo_finance_api_test.py  # Yahoo Finance API テスト
├── data_gap_analysis.py       # データギャップ分析
├── fetch_1h_data.py           # 1時間足データ取得
├── fetch_4h_data.py           # 4時間足データ取得
├── test_debug.py              # デバッグテスト
└── README.md                  # このファイル
```

## ⏰ cron/ - 定期実行スクリプト

**用途**: 本番環境での 24 時間自動稼働

### 主要スクリプト

#### データ取得・分析

- **`usdjpy_data_cron.py`**: USD/JPY 5 分足データ取得・分析（メイン稼働）
- **`simple_data_fetch_cron.py`**: シンプルデータ取得
- **`integrated_data_cron.py`**: 統合データ処理
- **`continuous_processing_cron.py`**: 継続的データ処理

#### テクニカル分析

- **`enhanced_unified_technical_calculator.py`**: 統合テクニカル指標計算
- **`unified_technical_calculator.py`**: 基本テクニカル指標計算
- **`technical_analysis_cron.py`**: テクニカル分析定期実行
- **`talib_technical_indicators_calculator.py`**: TA-Lib 指標計算

#### 高度な分析

- **`divergence_detector.py`**: ダイバージェンス検出
- **`support_resistance_analyzer.py`**: サポート・レジスタンス分析
- **`momentum_analyzer.py`**: モメンタム分析
- **`advanced_signal_analyzer.py`**: 高度なシグナル分析

#### AI・通知

- **`integrated_ai_discord.py`**: 統合 AI Discord 通知
- **`real_ai_discord.py`**: リアル AI Discord 通知
- **`yahoo_finance_discord.py`**: Yahoo Finance Discord 通知

#### レポート・集計

- **`daily_report.py`**: 日次レポート
- **`weekly_report.py`**: 週次レポート
- **`hourly_aggregator.py`**: 時間別集計
- **`daily_aggregator.py`**: 日別集計
- **`four_hour_aggregator.py`**: 4 時間別集計

#### データ管理

- **`data_scheduler.py`**: データスケジューラー
- **`database_cleanup.py`**: データベースクリーンアップ
- **`differential_updater.py`**: 差分更新
- **`data_loader.py`**: データローダー

#### 初期化・セットアップ

- **`unified_initialization.py`**: 統合初期化
- **`hybrid_initialization.py`**: ハイブリッド初期化
- **`multi_timeframe_initial_load.py`**: マルチタイムフレーム初期ロード
- **`simple_initial_load.py`**: シンプル初期ロード

## 📊 monitoring/ - システム監視

**用途**: システムの健全性監視・パフォーマンス監視

### スクリプト

- **`realtime_monitor.py`**: リアルタイム監視（25KB, 670 行）

  - CPU・メモリ使用率監視
  - データベース接続状態
  - データ取得成功率
  - パターン検出状況
  - Discord 通知状況

- **`cron_monitor.py`**: cron 実行監視（3.1KB, 97 行）
  - 定期実行スクリプトの監視
  - 実行ログの確認
  - エラー検出

## 🚀 deployment/ - デプロイメント

**用途**: 本番環境へのデプロイ・環境構築

### スクリプト

- **`production_setup.py`**: 本番環境セットアップ（11KB, 380 行）

  - データベース・テーブル作成
  - 環境設定
  - 初期データ投入

- **`production_startup.py`**: 本番環境起動（18KB, 621 行）

  - システム初期化
  - サービス起動
  - ヘルスチェック

- **`deploy_production.py`**: 本番デプロイ（16KB, 497 行）

  - 完全デプロイメント
  - バックアップ・復元
  - ロールバック機能

- **`data_migration.py`**: データ移行（7.6KB, 230 行）
  - データベース移行
  - スキーマ更新

## 🔄 migration/ - データベース移行

**用途**: データベーススキーマ・データ移行

### スクリプト

- **`sqlite_to_postgresql_migration.py`**: SQLite → PostgreSQL 移行（11KB, 303 行）

  - データベース移行
  - スキーマ変換
  - データ整合性確認

- **`data_migration.py`**: 汎用データ移行（18KB, 598 行）
  - 大規模データ移行
  - バッチ処理
  - エラーハンドリング

## 🧪 test/ - テスト・検証

**用途**: システム機能のテスト・検証・デバッグ

### パターン検出テスト

- **`test_pattern1_detailed.py`** 〜 **`test_pattern16_detailed.py`**: 各パターンの詳細テスト
- **`test_all_patterns_integration.py`**: 全パターン統合テスト
- **`test_pattern_detection_with_discord.py`**: Discord 通知統合テスト

### システムテスト

- **`test_system_initialization.py`**: システム初期化テスト
- **`test_real_market_data.py`**: 実市場データテスト
- **`test_error_handler.py`**: エラーハンドリングテスト
- **`test_monitoring_system.py`**: 監視システムテスト

### パフォーマンステスト

- **`test_performance_optimization.py`**: パフォーマンス最適化テスト
- **`test_memory_optimizer.py`**: メモリ最適化テスト
- **`test_query_optimizer.py`**: クエリ最適化テスト

### データ検証

- **`verify_database_data.py`**: データベースデータ検証
- **`test_real_5m_data.py`**: 5 分足実データテスト
- **`check_database_timeframes.py`**: タイムフレーム確認

## 📊 data/ - データ処理

**用途**: データ処理・分析・検証

### スクリプト

- **`check_aggregated_data.py`**: 集計データ確認（1.8KB, 57 行）
  - データ集計状況確認
  - データ品質チェック

## 🧹 cleanup/ - データクリーンアップ

**用途**: 不要データの削除・クリーンアップ

### スクリプト

- **`cleanup_artificial_data.py`**: 人工データクリーンアップ（3.5KB, 102 行）
  - テストデータ削除
  - 古いデータ削除

## 📦 メインスクリプト

### deploy.sh - デプロイスクリプト

**用途**: 本格的なデプロイメントスクリプト（5.7KB, 174 行）

**機能**:

- 環境別デプロイ（development/production）
- Docker コンテナ管理
- データベースバックアップ・復元
- ヘルスチェック
- ロールバック機能

**使用方法**:

```bash
# 本番環境デプロイ
./scripts/deploy.sh production

# 開発環境デプロイ
./scripts/deploy.sh development
```

### Phase 実行スクリプト

- **`run_phase1.py`**: Phase 1 実行（8.6KB, 294 行）

  - 基本パターン検出システム
  - 初期データ取得・分析

- **`run_phase2.py`**: Phase 2 実行（5.2KB, 177 行）
  - 高度なパターン検出
  - AI 分析統合

### データ取得スクリプト

- **`fetch_1h_data.py`**: 1 時間足データ取得（1.3KB, 49 行）
- **`fetch_4h_data.py`**: 4 時間足データ取得（1.3KB, 49 行）
- **`yahoo_finance_api_test.py`**: Yahoo Finance API テスト（4.2KB, 132 行）

### 分析スクリプト

- **`data_gap_analysis.py`**: データギャップ分析（6.8KB, 222 行）
  - データ欠損分析
  - データ品質評価

## 🔄 本番 crontab 設定

### 現在の稼働設定

```bash
# Exchange Analytics Production Crontab - 24時間稼働版
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/app

# 📊 基本データ取得（5分間隔、平日24時間稼働）
*/5 * * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 300 python scripts/cron/usdjpy_data_cron.py >> /app/logs/data_cron.log 2>&1

# 📈 日次レポート（毎日6:00 JST = 21:00 UTC）
0 21 * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 120 python scripts/cron/daily_report.py >> /app/logs/daily_cron.log 2>&1

# 📊 週次統計・レポート（毎週土曜日 6:00 JST = 21:00 UTC）
0 21 * * 6 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 180 python scripts/cron/weekly_report.py >> /app/logs/weekly_cron.log 2>&1
```

## 🎯 使用方法

### 開発環境での実行

```bash
# 単発実行（テスト用）
cd /app && python scripts/cron/usdjpy_data_cron.py --once

# 特定のテスト実行
cd /app && python scripts/test/test_pattern_detection.py

# 監視システム起動
cd /app && python scripts/monitoring/realtime_monitor.py
```

### 本番環境での実行

```bash
# デプロイ
./scripts/deploy.sh production

# システム起動
python scripts/deployment/production_startup.py

# 監視開始
python scripts/monitoring/realtime_monitor.py
```

## 📊 統計情報

- **総スクリプト数**: 100+ ファイル
- **cron スクリプト**: 40+ ファイル
- **テストスクリプト**: 50+ ファイル
- **監視スクリプト**: 2 ファイル
- **デプロイスクリプト**: 4 ファイル

## 🚨 注意事項

1. **実行権限**: スクリプト実行前に適切な権限を設定
2. **環境変数**: 実行前に環境変数を正しく設定
3. **ログ確認**: 実行後はログファイルを確認
4. **バックアップ**: 本番環境での実行前はバックアップを取得
5. **テスト**: 本番環境での実行前にテスト環境で検証
