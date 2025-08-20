# プロトレーダー向け為替アラートシステム 運用ドキュメント

## 📋 目次

1. [システム概要](#システム概要)
2. [デプロイメント](#デプロイメント)
3. [監視・ログ](#監視ログ)
4. [バックアップ・復旧](#バックアップ復旧)
5. [トラブルシューティング](#トラブルシューティング)
6. [パフォーマンス最適化](#パフォーマンス最適化)
7. [セキュリティ](#セキュリティ)
8. [運用コマンド](#運用コマンド)

## 🏗️ システム概要

### アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │───►│  API Service    │───►│  PostgreSQL DB  │
│   (Port 80/443) │    │  (Port 8000)    │    │  (Port 5432)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Grafana       │    │   Worker        │    │   Redis Cache   │
│   (Port 3000)   │    │   Service       │    │   (Port 6379)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Prometheus    │    │   Scheduler     │
│   (Port 9090)   │    │   Service       │
└─────────────────┘    └─────────────────┘
```

### サービス構成

| サービス   | ポート | 説明                 |
| ---------- | ------ | -------------------- |
| API        | 8000   | メイン API サービス  |
| Worker     | -      | バックグラウンド処理 |
| Scheduler  | -      | 定期タスク実行       |
| PostgreSQL | 5432   | データベース         |
| Redis      | 6379   | キャッシュ・キュー   |
| Nginx      | 80/443 | リバースプロキシ     |
| Grafana    | 3000   | 監視ダッシュボード   |
| Prometheus | 9090   | メトリクス収集       |

## 🚀 デプロイメント

### 前提条件

- Docker & Docker Compose
- 4GB 以上の RAM
- 20GB 以上のディスク容量
- インターネット接続

### 初回デプロイメント

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd forex-alert-system

# 2. 環境変数ファイルの設定
cp .env.production.example .env.production
# .env.productionファイルを編集して必要な値を設定

# 3. デプロイメントスクリプトの実行
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

### 更新デプロイメント

```bash
# 1. コードの更新
git pull origin main

# 2. 再デプロイメント
./scripts/deploy.sh production
```

### 環境別デプロイメント

```bash
# 開発環境
./scripts/deploy.sh development

# ステージング環境
./scripts/deploy.sh staging

# 本番環境
./scripts/deploy.sh production
```

## 📊 監視・ログ

### Grafana ダッシュボード

**アクセス方法:**

- URL: http://localhost:3000
- ユーザー: admin
- パスワード: 環境変数`GRAFANA_PASSWORD`で設定

**主要ダッシュボード:**

- システム概要
- アラート統計
- パフォーマンス分析
- データベース監視

### Prometheus メトリクス

**アクセス方法:**

- URL: http://localhost:9090

**主要メトリクス:**

- API 応答時間
- データベース接続数
- メモリ使用量
- CPU 使用率
- アラート生成数

### ログ管理

**ログファイルの場所:**

```
logs/
├── app/           # アプリケーションログ
├── nginx/         # Nginxログ
└── system/        # システムログ
```

**ログローテーション:**

- サイズ: 100MB
- 保持期間: 30 日
- 圧縮: 有効

**ログレベル:**

- DEBUG: 開発環境
- INFO: 本番環境
- WARNING: 警告
- ERROR: エラー

## 💾 バックアップ・復旧

### データベースバックアップ

**自動バックアップ:**

```bash
# バックアップ実行
docker exec forex_alert_postgres pg_dump -U forex_user forex_alert_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 圧縮
gzip backup_*.sql
```

**スケジュールバックアップ:**

```bash
# crontabに追加
0 2 * * * /path/to/backup_script.sh
```

### 復旧手順

```bash
# 1. サービス停止
docker-compose -f docker-compose.prod.yml down

# 2. データベース復旧
docker exec -i forex_alert_postgres psql -U forex_user forex_alert_db < backup_file.sql

# 3. サービス再起動
docker-compose -f docker-compose.prod.yml up -d
```

### 設定ファイルバックアップ

```bash
# 重要な設定ファイルのバックアップ
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
    .env.production \
    config/ \
    nginx/ \
    monitoring/
```

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. サービスが起動しない

**症状:** コンテナが起動直後に停止する

**確認項目:**

```bash
# ログの確認
docker-compose -f docker-compose.prod.yml logs [service_name]

# 環境変数の確認
docker-compose -f docker-compose.prod.yml config

# リソース使用量の確認
docker stats
```

**解決方法:**

- 環境変数の設定を確認
- ポートの競合を確認
- ディスク容量を確認

#### 2. データベース接続エラー

**症状:** アプリケーションがデータベースに接続できない

**確認項目:**

```bash
# データベースの状態確認
docker exec forex_alert_postgres pg_isready -U forex_user

# 接続テスト
docker exec forex_alert_postgres psql -U forex_user -d forex_alert_db -c "SELECT 1;"
```

**解決方法:**

- データベースサービスの再起動
- 接続文字列の確認
- ファイアウォール設定の確認

#### 3. メモリ不足

**症状:** システムが遅い、エラーが頻発する

**確認項目:**

```bash
# メモリ使用量の確認
free -h
docker stats

# プロセス確認
ps aux --sort=-%mem | head -10
```

**解決方法:**

- 不要なコンテナの停止
- メモリ制限の調整
- システムリソースの増強

#### 4. ディスク容量不足

**症状:** ログ書き込みエラー、バックアップ失敗

**確認項目:**

```bash
# ディスク使用量の確認
df -h
du -sh logs/*

# Docker使用量の確認
docker system df
```

**解決方法:**

- 古いログファイルの削除
- Docker イメージ・コンテナのクリーンアップ
- ディスク容量の増強

### 緊急時の対応

#### システムダウン時の復旧手順

1. **状況確認**

   ```bash
   docker-compose -f docker-compose.prod.yml ps
   docker-compose -f docker-compose.prod.yml logs
   ```

2. **緊急停止**

   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

3. **データベース保護**

   ```bash
   docker exec forex_alert_postgres pg_dump -U forex_user forex_alert_db > emergency_backup.sql
   ```

4. **段階的復旧**

   ```bash
   # データベースのみ起動
   docker-compose -f docker-compose.prod.yml up -d postgres redis

   # 確認後、全サービス起動
   docker-compose -f docker-compose.prod.yml up -d
   ```

## ⚡ パフォーマンス最適化

### データベース最適化

**インデックス最適化:**

```sql
-- 使用頻度の低いインデックスを削除
DROP INDEX IF EXISTS unused_index_name;

-- 新しいインデックスを作成
CREATE INDEX CONCURRENTLY idx_currency_timestamp
ON technical_indicators(currency_pair, timestamp);
```

**クエリ最適化:**

```sql
-- スロークエリの特定
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### アプリケーション最適化

**キャッシュ戦略:**

- Redis キャッシュの活用
- クエリ結果のキャッシュ
- 静的ファイルのキャッシュ

**非同期処理:**

- 重い処理のバックグラウンド実行
- キューシステムの活用
- ワーカープロセスの調整

### システム最適化

**リソース制限:**

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "1.0"
        reservations:
          memory: 1G
          cpus: "0.5"
```

**ログ最適化:**

- ログレベルの調整
- ログローテーションの設定
- 不要なログの削減

## 🔒 セキュリティ

### 基本的なセキュリティ対策

**ファイアウォール設定:**

```bash
# UFWの設定
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

**SSL/TLS 設定:**

```nginx
# nginx/nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
}
```

**環境変数の管理:**

- 機密情報は環境変数で管理
- .env ファイルは Git にコミットしない
- 定期的なパスワード変更

### 監査とログ

**セキュリティログの監視:**

```bash
# 認証ログの確認
docker-compose -f docker-compose.prod.yml logs api | grep "authentication"

# アクセスログの確認
tail -f logs/nginx/access.log | grep "error\|warning"
```

**定期的なセキュリティチェック:**

- 依存関係の脆弱性チェック
- セキュリティアップデートの適用
- アクセス権限の確認

## 🛠️ 運用コマンド

### 日常的な運用コマンド

**サービスの管理:**

```bash
# 全サービスの状態確認
docker-compose -f docker-compose.prod.yml ps

# 特定サービスの再起動
docker-compose -f docker-compose.prod.yml restart [service_name]

# サービスの停止
docker-compose -f docker-compose.prod.yml stop [service_name]

# サービスの開始
docker-compose -f docker-compose.prod.yml start [service_name]
```

**ログの確認:**

```bash
# 全サービスのログ確認
docker-compose -f docker-compose.prod.yml logs

# 特定サービスのログ確認
docker-compose -f docker-compose.prod.yml logs [service_name]

# リアルタイムログ確認
docker-compose -f docker-compose.prod.yml logs -f [service_name]
```

**データベース操作:**

```bash
# データベース接続
docker exec -it forex_alert_postgres psql -U forex_user -d forex_alert_db

# バックアップ作成
docker exec forex_alert_postgres pg_dump -U forex_user forex_alert_db > backup.sql

# バックアップ復元
docker exec -i forex_alert_postgres psql -U forex_user forex_alert_db < backup.sql
```

**システムメンテナンス:**

```bash
# 不要なDockerリソースの削除
docker system prune -a

# ディスク使用量の確認
docker system df

# コンテナのリソース使用量確認
docker stats
```

### 緊急時コマンド

**システムの緊急停止:**

```bash
# 全サービスの即座停止
docker-compose -f docker-compose.prod.yml down --timeout 0

# 特定サービスの強制停止
docker kill [container_name]
```

**データベースの緊急操作:**

```bash
# データベースの強制再起動
docker restart forex_alert_postgres

# 接続の強制切断
docker exec forex_alert_postgres pkill -f postgres
```

**ログの緊急確認:**

```bash
# 最新のエラーログ確認
docker-compose -f docker-compose.prod.yml logs --tail=100 | grep -i error

# 特定時間のログ確認
docker-compose -f docker-compose.prod.yml logs --since="2024-01-01T00:00:00"
```

## 📞 サポート

### 連絡先

- **技術サポート:** tech-support@company.com
- **緊急時:** emergency@company.com
- **ドキュメント:** https://docs.company.com

### エスカレーション手順

1. **レベル 1:** 基本的なトラブルシューティング
2. **レベル 2:** システム管理者による対応
3. **レベル 3:** 開発チームによる対応
4. **レベル 4:** ベンダーサポート

### 定期メンテナンス

- **日次:** ログ確認、バックアップ確認
- **週次:** パフォーマンス分析、セキュリティチェック
- **月次:** システム更新、容量計画
- **四半期:** 完全なシステム監査
