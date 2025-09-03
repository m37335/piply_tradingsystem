# システム復旧手続きガイド

## PC 再起動後の復旧手順

### 📋 **目次**

1. [Docker 環境の復旧](#docker環境の復旧)
2. [PostgreSQL データベースの復旧](#postgresqlデータベースの復旧)
3. [Crontab サービスの復旧](#crontabサービスの復旧)
4. [システム状態の確認](#システム状態の確認)
5. [トラブルシューティング](#トラブルシューティング)

---

## 🐳 **Docker 環境の復旧**

### 0. 現在のコンテナ情報

```bash
# 現在のコンテナID確認
hostname
# 出力例: df2031f4ec3f

# 完全なコンテナID確認（ホスト側で実行）
docker ps | grep df2031f4ec3f
# 出力例: df2031f4ec3f7f8bf960e248894559bbfd00ba6197ecd20f332c0e29398c2215
```

### 1. Docker サービスの起動

```bash
# Dockerサービスの状態確認
sudo systemctl status docker

# Dockerサービスが停止している場合、起動
sudo systemctl start docker

# Dockerサービスの自動起動設定
sudo systemctl enable docker
```

### 2. Docker コンテナの起動

```bash
# 既存コンテナの確認
docker ps -a

# 停止中のコンテナを起動（コンテナIDまたはコンテナ名を指定）
docker start df2031f4ec3f
# または
docker start df2031f4ec3f7f8bf960e248894559bbfd00ba6197ecd20f332c0e29398c2215

# または、全ての停止中コンテナを起動
docker start $(docker ps -aq)
```

### 3. Docker Compose 環境の復旧

```bash
# プロジェクトディレクトリに移動
cd /app

# Docker Composeでサービスを起動
docker-compose up -d

# または、バックグラウンドで起動
docker-compose up -d --build
```

---

## 🗄️ **PostgreSQL データベースの復旧**

### 1. PostgreSQL サービスの起動

```bash
# PostgreSQLサービスの状態確認
sudo systemctl status postgresql

# PostgreSQLサービスが停止している場合、起動
sudo systemctl start postgresql

# PostgreSQLサービスの自動起動設定
sudo systemctl enable postgresql
```

### 2. データベース接続確認

```bash
# データベース接続テスト
cd /app
python3 postgresql_connection.py

# または、直接psqlで接続確認
PGPASSWORD=exchange_password psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db -c "SELECT version();"
```

### 3. データベーステーブル確認

```bash
# テーブル一覧確認
PGPASSWORD=exchange_password psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db -c "\dt"

# 主要テーブルのデータ件数確認
PGPASSWORD=exchange_password psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db -c "
SELECT
    'technical_indicators' as table_name, count(*) as count FROM technical_indicators
UNION ALL
SELECT
    'price_data' as table_name, count(*) as count FROM price_data
UNION ALL
SELECT
    'analysis_cache' as table_name, count(*) as count FROM analysis_cache
UNION ALL
SELECT
    'notification_history' as table_name, count(*) as count FROM notification_history;"
```

---

## ⏰ **Crontab サービスの復旧**

### 1. Crontab サービスの起動

```bash
# Crontabサービスの状態確認
sudo systemctl status cron

# Crontabサービスが停止している場合、起動
sudo systemctl start cron

# Crontabサービスの自動起動設定
sudo systemctl enable cron
```

### 2. Crontab 設定の確認

```bash
# 現在のCrontab設定を確認
crontab -l

# Crontab設定が存在しない場合、再設定
crontab /etc/crontab
```

### 3. 環境変数の確認

```bash
# 環境変数ファイルの存在確認
ls -la /app/.env

# 環境変数の読み込みテスト
cd /app
export $(cat .env | grep -v '^#' | xargs)
echo $DATABASE_URL
```

---

## 🔍 **システム状態の確認**

### 1. 基本サービス状態確認

```bash
# 主要サービスの状態確認
sudo systemctl status docker
sudo systemctl status postgresql
sudo systemctl status cron

# プロセス確認
ps aux | grep python
ps aux | grep postgres
```

### 2. ログファイルの確認

```bash
# 最新のログを確認
tail -20 /app/logs/integrated_ai_cron.log
tail -20 /app/logs/continuous_processing_cron.log
tail -20 /app/logs/error_alert.log

# エラーログの確認
grep -i "error\|failed" /app/logs/*.log | tail -10
```

### 3. システムヘルスチェック

```bash
# システムヘルスチェック実行
cd /app
python scripts/monitoring/realtime_monitor.py --interval 1 --no-alerts

# 手動で統合AI分析をテスト
python scripts/cron/integrated_ai_discord.py --test
```

### 4. データベースヘルスチェック

```bash
# データベース接続テスト
cd /app
python3 postgresql_connection.py

# システム初期化状態確認
PGPASSWORD=exchange_password psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db -c "
SELECT
    'system_health' as table_name, count(*) as count FROM system_health
UNION ALL
SELECT
    'system_config' as table_name, count(*) as count FROM system_config;"
```

---

## 🛠️ **トラブルシューティング**

### 1. Docker 関連の問題

```bash
# Dockerデーモンの再起動
sudo systemctl restart docker

# Dockerコンテナの強制再起動
docker restart df2031f4ec3f
# または
docker restart df2031f4ec3f7f8bf960e248894559bbfd00ba6197ecd20f332c0e29398c2215

# Dockerボリュームの確認
docker volume ls
```

### 2. PostgreSQL 関連の問題

```bash
# PostgreSQLサービスの再起動
sudo systemctl restart postgresql

# PostgreSQLログの確認
sudo tail -50 /var/log/postgresql/postgresql-15-main.log

# データベース接続数の確認
PGPASSWORD=exchange_password psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db -c "
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';"
```

### 3. Crontab 関連の問題

```bash
# Crontabサービスの再起動
sudo systemctl restart cron

# Crontabログの確認（利用可能な場合）
sudo tail -50 /var/log/cron.log

# 手動でCrontabジョブをテスト
cd /app
export $(cat .env | grep -v '^#' | xargs)
timeout 180 python scripts/cron/integrated_ai_discord.py
```

### 4. 権限関連の問題

```bash
# ファイル権限の確認
ls -la /app/.env
ls -la /app/logs/

# 権限の修正
chmod 644 /app/.env
chmod 755 /app/logs/
```

---

## 📝 **復旧チェックリスト**

### 起動後確認項目

- [ ] Docker サービスが起動している
- [ ] PostgreSQL サービスが起動している
- [ ] Crontab サービスが起動している
- [ ] データベースに接続できる
- [ ] 環境変数が正しく読み込まれている
- [ ] ログファイルが正常に作成されている
- [ ] 手動実行でシステムが動作する

### 定期確認項目

- [ ] 12:00 の自動配信が実行されている
- [ ] エラーログに異常がない
- [ ] データベースのデータが正常に蓄積されている
- [ ] システムリソース（CPU、メモリ、ディスク）に余裕がある

---

## 🚨 **緊急時の対応**

### システムが完全に停止した場合

```bash
# 1. 全サービスの停止
sudo systemctl stop cron
sudo systemctl stop postgresql
sudo systemctl stop docker

# 2. システムリソースの確認
df -h
free -h
top

# 3. サービスを順次起動
sudo systemctl start docker
sudo systemctl start postgresql
sudo systemctl start cron

# 4. Dockerコンテナの起動
docker start df2031f4ec3f
# または
docker start df2031f4ec3f7f8bf960e248894559bbfd00ba6197ecd20f332c0e29398c2215

# 5. システムテスト
cd /app
python scripts/cron/integrated_ai_discord.py --test
```

### データベースが破損した場合

```bash
# 1. PostgreSQLサービスの停止
sudo systemctl stop postgresql

# 2. データベースの整合性チェック
sudo -u postgres pg_ctl -D /var/lib/postgresql/15/main start -o "--single --user=postgres"

# 3. 必要に応じてバックアップからの復旧
# （バックアップ手順は別途準備）
```

---

## 📞 **サポート情報**

### ログファイルの場所

- アプリケーションログ: `/app/logs/`
- PostgreSQL ログ: `/var/log/postgresql/`
- システムログ: `/var/log/syslog`

### 重要な設定ファイル

- 環境変数: `/app/.env`
- Crontab 設定: `/etc/crontab`
- PostgreSQL 設定: `/etc/postgresql/15/main/postgresql.conf`

### コンテナ情報

- コンテナ ID（短縮）: `df2031f4ec3f`
- コンテナ ID（完全）: `df2031f4ec3f7f8bf960e248894559bbfd00ba6197ecd20f332c0e29398c2215`
- ホスト名: `df2031f4ec3f`

### 緊急連絡先

- システム管理者: [連絡先情報]
- データベース管理者: [連絡先情報]

---

**最終更新**: 2025-08-20
**バージョン**: 1.0
**作成者**: AI Assistant
