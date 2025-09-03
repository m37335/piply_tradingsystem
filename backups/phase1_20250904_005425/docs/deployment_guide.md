# investpy Economic Calendar System - デプロイメントガイド

## 概要

このドキュメントは、investpy Economic Calendar System の本番環境へのデプロイメント手順を説明します。

## 前提条件

### システム要件

- **OS**: Linux (Ubuntu 20.04+ / CentOS 8+)
- **Python**: 3.11+
- **PostgreSQL**: 13+
- **Redis**: 6+
- **メモリ**: 4GB 以上
- **ディスク**: 20GB 以上の空き容量

### 必要なソフトウェア

```bash
# システムパッケージのインストール
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-pip \
    python3.11-venv \
    postgresql-13 \
    redis-server \
    cron \
    curl \
    wget \
    git \
    build-essential
```

## 環境変数の設定

### 必須環境変数

`.env`ファイルを作成し、以下の環境変数を設定してください：

```env
# データベース設定
DATABASE_URL=postgresql://economic_user:secure_password@localhost:5432/economic_calendar

# Redis設定
REDIS_URL=redis://localhost:6379/0

# Discord設定
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
DISCORD_ECONOMICINDICATORS_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ECONOMIC_WEBHOOK_URL

# OpenAI設定
OPENAI_API_KEY=your_openai_api_key_here

# アプリケーション設定
ENVIRONMENT=production
LOG_LEVEL=INFO
```

### オプション環境変数

```env
# 通知設定
NOTIFICATION_COOLDOWN=3600
NOTIFICATION_IMPORTANCE_THRESHOLD=medium

# AI分析設定
AI_REPORT_ENABLED=true
AI_CONFIDENCE_THRESHOLD=0.7

# セキュリティ設定
SECRET_KEY=your_secret_key_here_make_it_long_and_random
ENCRYPTION_KEY=your_encryption_key_here
```

## デプロイメント手順

### 1. プロジェクトのクローン

```bash
# プロジェクトディレクトリの作成
sudo mkdir -p /app
sudo chown $USER:$USER /app
cd /app

# プロジェクトのクローン
git clone https://github.com/your-repo/investpy-economic-calendar.git .
```

### 2. 依存関係のインストール

```bash
# Python仮想環境の作成
python3.11 -m venv venv
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements/production.txt
pip install -r requirements/investpy_calendar.txt
```

### 3. データベースのセットアップ

```bash
# PostgreSQLユーザーの作成
sudo -u postgres createuser economic_user
sudo -u postgres createdb economic_calendar
sudo -u postgres psql -c "ALTER USER economic_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE economic_calendar TO economic_user;"

# データベースマイグレーション
python scripts/setup_database.py
```

### 4. Redis の設定

```bash
# Redisの設定
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Redisの動作確認
redis-cli ping
```

### 5. 本番環境のセットアップ

```bash
# 本番環境セットアップスクリプトの実行
python scripts/setup_production.py

# または、ヘルスチェックをスキップする場合
python scripts/setup_production.py --skip-health-checks
```

### 6. crontab の設定

```bash
# crontabデプロイスクリプトの実行
python scripts/deploy_crontab.py --schedule-type all

# 設定の確認
python scripts/deploy_crontab.py --list
```

### 7. デプロイメントの実行

```bash
# フルデプロイメント
./scripts/deploy.sh full production

# または、更新のみ
./scripts/deploy.sh update production
```

## デプロイメント後の確認

### 1. サービスの動作確認

```bash
# サービス監視の実行
python scripts/monitor_service.py

# 継続的な監視
python scripts/monitor_service.py --continuous --interval 300
```

### 2. ログの確認

```bash
# アプリケーションログ
tail -f /app/data/logs/app.log

# スケジューラーログ
tail -f /app/data/logs/scheduler/weekly.log
tail -f /app/data/logs/scheduler/daily.log
tail -f /app/data/logs/scheduler/realtime.log

# エラーログ
tail -f /app/data/logs/error.log
```

### 3. crontab の確認

```bash
# 現在のcrontab設定を確認
crontab -l

# cronサービスの状態確認
sudo systemctl status cron
```

## 運用コマンド

### デプロイメント関連

```bash
# フルデプロイメント
./scripts/deploy.sh full production

# 更新デプロイメント
./scripts/deploy.sh update production

# ロールバック
./scripts/rollback.sh latest
./scripts/rollback.sh 20231201_143000

# ヘルプ表示
./scripts/deploy.sh --help
./scripts/rollback.sh --help
```

### 監視関連

```bash
# サービス監視
python scripts/monitor_service.py

# 継続的監視
python scripts/monitor_service.py --continuous --interval 300

# ヘルスチェック
python scripts/health_check.py
```

### バックアップ関連

```bash
# データベースバックアップ
python scripts/backup_database.py

# データベース復元
python scripts/restore_database.py backup_file.sql

# ログローテーション
python scripts/rotate_logs.py
```

### crontab 関連

```bash
# crontabデプロイ
python scripts/deploy_crontab.py --schedule-type all

# スケジュール一覧表示
python scripts/deploy_crontab.py --list

# 設定検証
python scripts/deploy_crontab.py --validate
```

## トラブルシューティング

### よくある問題と解決方法

#### 1. データベース接続エラー

```bash
# 接続確認
psql "$DATABASE_URL" -c "SELECT 1;"

# サービス状態確認
sudo systemctl status postgresql

# ログ確認
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### 2. Redis 接続エラー

```bash
# 接続確認
redis-cli ping

# サービス状態確認
sudo systemctl status redis-server

# ログ確認
sudo tail -f /var/log/redis/redis-server.log
```

#### 3. crontab が動作しない

```bash
# cronサービスの確認
sudo systemctl status cron

# crontab設定の確認
crontab -l

# cronログの確認
sudo tail -f /var/log/cron
```

#### 4. 権限エラー

```bash
# ディレクトリ権限の確認
ls -la /app/data/

# 権限の修正
sudo chown -R $USER:$USER /app/data/
chmod -R 755 /app/data/
```

#### 5. メモリ不足

```bash
# メモリ使用量の確認
free -h

# プロセス確認
ps aux | grep python

# ログファイルサイズの確認
du -sh /app/data/logs/
```

## セキュリティ設定

### 1. ファイアウォール設定

```bash
# UFWの有効化
sudo ufw enable

# 必要なポートの開放
sudo ufw allow ssh
sudo ufw allow 5432  # PostgreSQL
sudo ufw allow 6379  # Redis

# 状態確認
sudo ufw status
```

### 2. SSL 証明書の設定

```bash
# Let's Encrypt証明書の取得
sudo apt-get install certbot
sudo certbot certonly --standalone -d yourdomain.com

# 証明書の自動更新
sudo crontab -e
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### 3. ファイル権限の設定

```bash
# 設定ファイルの権限設定
chmod 600 /app/.env
chmod 600 /app/config/production_config.json

# ログファイルの権限設定
chmod 644 /app/data/logs/*.log
```

## パフォーマンス最適化

### 1. データベース最適化

```bash
# データベース最適化スクリプトの実行
python scripts/optimize_database.py

# 定期的な最適化（crontabに追加）
0 2 * * 0 python /app/scripts/optimize_database.py
```

### 2. ログローテーション

```bash
# ログローテーションの設定
python scripts/rotate_logs.py

# 定期的なローテーション（crontabに追加）
0 0 * * * python /app/scripts/rotate_logs.py
```

### 3. キャッシュ最適化

```bash
# Redisキャッシュの確認
redis-cli info memory

# キャッシュのクリア
redis-cli flushall
```

## 監視とアラート

### 1. 監視設定

```bash
# 監視スクリプトの実行
python scripts/monitor_service.py --continuous --interval 300

# システム監視の設定
sudo apt-get install htop iotop
```

### 2. アラート設定

Discord Webhook を使用したアラート設定：

```python
# 監視設定ファイル: config/monitoring.yaml
monitoring:
  alerts:
    discord_webhook: "https://discord.com/api/webhooks/YOUR_ALERT_WEBHOOK_URL"
    email: "alerts@yourdomain.com"
```

### 3. ログ監視

```bash
# エラーログの監視
tail -f /app/data/logs/error.log | grep ERROR

# リアルタイムログ監視
tail -f /app/data/logs/app.log
```

## バックアップ戦略

### 1. 自動バックアップ

```bash
# バックアップスクリプトの実行
python scripts/backup_database.py

# 定期的なバックアップ（crontabに追加）
0 1 * * * python /app/scripts/backup_database.py
```

### 2. バックアップの検証

```bash
# バックアップファイルの確認
ls -la /app/data/backups/

# バックアップの復元テスト
python scripts/restore_database.py test_backup.sql
```

### 3. オフサイトバックアップ

```bash
# 外部ストレージへのバックアップ
rsync -avz /app/data/backups/ user@backup-server:/backups/

# クラウドストレージへのバックアップ
aws s3 sync /app/data/backups/ s3://your-bucket/backups/
```

## 更新とメンテナンス

### 1. 定期的な更新

```bash
# コードの更新
git pull origin main

# 依存関係の更新
pip install -r requirements/production.txt --upgrade

# データベースマイグレーション
python scripts/setup_database.py
```

### 2. メンテナンスモード

```bash
# メンテナンスモードの有効化
echo "maintenance" > /app/data/maintenance.flag

# メンテナンスモードの無効化
rm /app/data/maintenance.flag
```

### 3. パフォーマンス監視

```bash
# パフォーマンス監視の実行
python scripts/performance_monitor.py

# リソース使用量の確認
htop
iotop
df -h
```

## サポートとトラブルシューティング

### ログファイルの場所

- **アプリケーションログ**: `/app/data/logs/app.log`
- **エラーログ**: `/app/data/logs/error.log`
- **スケジューラーログ**: `/app/data/logs/scheduler/`
- **監視ログ**: `/app/data/logs/monitoring/`
- **デプロイメントログ**: `/app/data/logs/deployment/`

### 重要なファイル

- **設定ファイル**: `/app/config/production_config.json`
- **環境変数**: `/app/.env`
- **crontab 設定**: `crontab -l`
- **バックアップ**: `/app/data/backups/`

### 緊急時の連絡先

- **システム管理者**: admin@yourdomain.com
- **開発チーム**: dev@yourdomain.com
- **Discord**: #system-alerts

## 更新履歴

- **v1.0.0** (2023-12-01): 初回リリース
- **v1.1.0** (2023-12-15): 監視機能の追加
- **v1.2.0** (2024-01-01): バックアップ機能の強化
