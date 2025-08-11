# 🔄 継続処理システム運用マニュアル

**作成日**: 2025 年 1 月  
**対象システム**: Exchange Analytics System - Multi-Timeframe Continuous Processing  
**バージョン**: 1.0.0

## 📋 目次

1. [システム概要](#システム概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [設定とデプロイ](#設定とデプロイ)
4. [監視とログ](#監視とログ)
5. [運用手順](#運用手順)
6. [トラブルシューティング](#トラブルシューティング)
7. [パフォーマンス最適化](#パフォーマンス最適化)
8. [セキュリティ](#セキュリティ)

## 🎯 システム概要

### 目的

- 5 分足データ取得後の自動集計とテクニカル指標計算の継続処理
- システム初期化状態の自動検出と適切な処理の実行
- 包括的な監視とアラート機能

### 主要機能

- **自動初期化**: 初回実行時の全時間軸データ取得
- **継続処理**: 5 分足からの自動時間軸集計
- **テクニカル指標計算**: RSI、MACD、ボリンジャーバンドの自動計算
- **パターン検出**: 6 種類のパターンの自動検出
- **監視・アラート**: システム健全性の監視とアラート

## 🏗️ アーキテクチャ

### コンポーネント構成

```
┌─────────────────────────────────────────────────────────────┐
│                Continuous Processing Pipeline                │
├─────────────────────────────────────────────────────────────┤
│  SystemInitializationManager  │  ContinuousProcessingService │
│  (初期化状態管理)              │  (継続処理統合)              │
├─────────────────────────────────────────────────────────────┤
│  TimeframeAggregatorService   │  ContinuousProcessingScheduler│
│  (時間軸集計)                  │  (スケジューラー)            │
├─────────────────────────────────────────────────────────────┤
│  ContinuousProcessingMonitor  │  NotificationManager         │
│  (監視・アラート)              │  (通知管理)                  │
└─────────────────────────────────────────────────────────────┘
```

### データフロー

1. **初期化チェック**: システム初期化状態を確認
2. **初回データ取得**: 未初期化の場合、全時間軸データを取得
3. **継続処理**: 初期化済みの場合、5 分足データを処理
4. **時間軸集計**: 5 分足から 1 時間足・4 時間足に集計
5. **テクニカル指標計算**: 各時間軸で指標を計算
6. **パターン検出**: 検出されたパターンを分析
7. **通知送信**: 重要なパターンを Discord に通知

## ⚙️ 設定とデプロイ

### 環境変数設定

```bash
# データベース設定
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/exchange_analytics

# Discord設定
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
DISCORD_BOT_TOKEN=your_bot_token

# 監視設定
MAX_PROCESSING_TIME=300  # 5分
MIN_SUCCESS_RATE=0.95    # 95%
MAX_ERROR_COUNT=5        # 5回

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=/app/logs/continuous_processing_cron.log
```

### デプロイ手順

1. **依存関係のインストール**

   ```bash
   pip install -r requirements.txt
   ```

2. **データベースマイグレーション**

   ```bash
   alembic upgrade head
   ```

3. **crontab の設定**

   ```bash
   # 現在のcrontabをバックアップ
   crontab -l > crontab_backup.txt

   # 新しいcrontabを設定
   crontab updated_crontab.txt
   ```

4. **ログディレクトリの作成**

   ```bash
   mkdir -p /app/logs
   chmod 755 /app/logs
   ```

5. **権限設定**
   ```bash
   chmod +x scripts/cron/continuous_processing_cron.py
   ```

## 📊 監視とログ

### ログファイル

| ファイル                                   | 説明               | ローテーション  |
| ------------------------------------------ | ------------------ | --------------- |
| `/app/logs/continuous_processing_cron.log` | メインログ         | 10MB 以上で圧縮 |
| `/app/logs/health_check_cron.log`          | 健全性チェックログ | 10MB 以上で圧縮 |
| `/app/logs/error_alert.log`                | エラーアラートログ | 7 日で削除      |

### 監視指標

#### パフォーマンス指標

- **処理時間**: 平均 5 分以内
- **成功率**: 95%以上
- **エラー率**: 5%以下
- **データ量**: 1 サイクルあたり 1-10 件

#### システム健全性

- **データベース接続**: 正常
- **API 接続**: 正常
- **ディスク使用量**: 80%以下
- **メモリ使用量**: 2GB 以下

### アラート設定

| アラートタイプ | 条件             | アクション                |
| -------------- | ---------------- | ------------------------- |
| **CRITICAL**   | 処理時間 > 10 分 | Discord 通知 + 管理者連絡 |
| **WARNING**    | 成功率 < 90%     | Discord 通知              |
| **INFO**       | 新規パターン検出 | Discord 通知              |

## 🔧 運用手順

### 日常運用

#### 1. システム起動

```bash
# 手動でシステムサイクルを実行
python scripts/cron/continuous_processing_cron.py --mode system_cycle

# 健全性チェックのみ実行
python scripts/cron/continuous_processing_cron.py --health-check-only
```

#### 2. ログ確認

```bash
# 最新のログを確認
tail -f /app/logs/continuous_processing_cron.log

# エラーログを確認
grep -i "error\|failed" /app/logs/continuous_processing_cron.log

# 健全性チェックログを確認
tail -20 /app/logs/health_check_cron.log
```

#### 3. 統計情報確認

```bash
# データベース統計を確認
python scripts/monitoring/database_stats.py

# パフォーマンス統計を確認
python scripts/monitoring/performance_stats.py
```

### 定期メンテナンス

#### 週次メンテナンス

1. **ログローテーション確認**

   ```bash
   ls -la /app/logs/*.gz
   ```

2. **ディスク使用量確認**

   ```bash
   df -h /app
   ```

3. **データベース最適化**
   ```bash
   python scripts/maintenance/database_optimization.py
   ```

#### 月次メンテナンス

1. **パフォーマンス分析**

   ```bash
   python scripts/analysis/performance_analysis.py
   ```

2. **設定見直し**
   - アラート閾値の調整
   - 処理間隔の最適化
   - リソース使用量の確認

## 🚨 トラブルシューティング

### よくある問題と対処法

#### 1. データベース接続エラー

**症状**: `DATABASE_URL環境変数が設定されていません`

**対処法**:

```bash
# 環境変数を確認
echo $DATABASE_URL

# .envファイルを確認
cat .env | grep DATABASE_URL

# データベース接続をテスト
python scripts/test/database_connection_test.py
```

#### 2. 処理時間超過

**症状**: `処理時間が閾値を超過`

**対処法**:

```bash
# 処理時間の詳細を確認
grep "processing_time" /app/logs/continuous_processing_cron.log

# データベースパフォーマンスを確認
python scripts/monitoring/database_performance.py

# システムリソースを確認
top -p $(pgrep -f continuous_processing_cron)
```

#### 3. 成功率低下

**症状**: `成功率が閾値を下回る`

**対処法**:

```bash
# エラーの詳細を確認
grep -A 5 -B 5 "error\|failed" /app/logs/continuous_processing_cron.log

# 外部API接続を確認
python scripts/test/api_connection_test.py

# システム健全性を確認
python scripts/cron/continuous_processing_cron.py --health-check-only
```

#### 4. メモリ不足

**症状**: `MemoryError` または `Killed`

**対処法**:

```bash
# メモリ使用量を確認
free -h

# プロセスを確認
ps aux | grep continuous_processing

# 設定を調整
# MAX_PROCESSING_TIMEを短縮
# バッチサイズを削減
```

### 緊急時対応

#### システム停止

```bash
# cronジョブを停止
crontab -r

# 実行中のプロセスを停止
pkill -f continuous_processing_cron
```

#### システム再起動

```bash
# データベース接続を確認
python scripts/test/database_connection_test.py

# 健全性チェックを実行
python scripts/cron/continuous_processing_cron.py --health-check-only

# cronジョブを再開
crontab updated_crontab.txt
```

## ⚡ パフォーマンス最適化

### データベース最適化

#### インデックス最適化

```sql
-- 価格データのインデックス
CREATE INDEX idx_price_data_timestamp ON price_data(timestamp);
CREATE INDEX idx_price_data_currency_pair ON price_data(currency_pair);
CREATE INDEX idx_price_data_timeframe ON price_data(timeframe);

-- テクニカル指標のインデックス
CREATE INDEX idx_technical_indicator_type ON technical_indicators(indicator_type);
CREATE INDEX idx_technical_indicator_timeframe ON technical_indicators(timeframe);
```

#### クエリ最適化

- バッチ処理の活用
- 不要なデータの削除
- 定期的な VACUUM 実行

### システム最適化

#### 設定パラメータ

```python
# 処理間隔の調整
INTERVAL_MINUTES = 5

# バッチサイズの調整
BATCH_SIZE = 100

# リトライ回数の調整
MAX_RETRIES = 3
```

#### リソース使用量

- メモリ使用量の監視
- CPU 使用率の最適化
- ディスク I/O の最適化

## 🔒 セキュリティ

### アクセス制御

#### ファイル権限

```bash
# スクリプトファイルの権限
chmod 755 scripts/cron/continuous_processing_cron.py

# 設定ファイルの権限
chmod 600 .env

# ログファイルの権限
chmod 644 /app/logs/*.log
```

#### データベースセキュリティ

- 強力なパスワードの使用
- SSL 接続の有効化
- アクセス制限の設定

### 監査ログ

#### ログ監視

```bash
# アクセスログの監視
tail -f /var/log/auth.log | grep continuous_processing

# エラーログの監視
tail -f /app/logs/error_alert.log
```

#### セキュリティスキャン

```bash
# 依存関係の脆弱性チェック
safety check

# コードのセキュリティチェック
bandit -r src/
```

## 📞 サポート

### 連絡先

- **技術サポート**: tech-support@example.com
- **緊急時連絡**: emergency@example.com
- **ドキュメント**: https://docs.example.com

### エスカレーション手順

1. **レベル 1**: 運用チームによる初期対応
2. **レベル 2**: 開発チームによる技術対応
3. **レベル 3**: アーキテクトによる設計見直し

---

**🔄 Exchange Analytics System** - _Continuous Processing Operations Manual v1.0.0_
