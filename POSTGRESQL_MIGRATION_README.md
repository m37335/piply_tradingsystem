# PostgreSQL Migration Guide

## 概要

SQLiteからPostgreSQLへの移行ガイドです。現在のSQLiteデータベースの制約（ロック問題、パフォーマンス問題）を解決するため、PostgreSQLへの移行を推奨します。

## ファイル構成

```
├── postgresql_schema.sql          # PostgreSQLスキーマ定義
├── postgresql_init.sql            # 初期化スクリプト
├── docker-compose.postgresql.yml  # Docker Compose設定
├── postgresql_connection.py       # 接続テストスクリプト
└── POSTGRESQL_MIGRATION_README.md # このファイル
```

## セットアップ手順

### 1. PostgreSQL環境の起動

```bash
# PostgreSQLコンテナを起動
docker-compose -f docker-compose.postgresql.yml up -d

# ログを確認
docker-compose -f docker-compose.postgresql.yml logs -f postgresql
```

### 2. 接続テスト

```bash
# 接続テストを実行
python postgresql_connection.py
```

### 3. データベース情報の確認

```bash
# PostgreSQLに直接接続
docker exec -it exchange_analytics_postgresql psql -U exchange_user -d exchange_analytics

# テーブル一覧を確認
\dt

# データベース情報を確認
SELECT * FROM get_database_info();

# テーブル統計を確認
SELECT * FROM get_table_stats();
```

## 環境変数設定

### .env ファイルに追加

```bash
# PostgreSQL設定
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=exchange_analytics
POSTGRES_USER=exchange_user
POSTGRES_PASSWORD=exchange_password

# 接続プール設定
POSTGRES_MIN_SIZE=5
POSTGRES_MAX_SIZE=20
POSTGRES_COMMAND_TIMEOUT=60
POSTGRES_STATEMENT_TIMEOUT=300

# データベースURL（アプリケーション用）
DATABASE_URL=postgresql+asyncpg://exchange_user:exchange_password@localhost:5432/exchange_analytics
```

## アプリケーション設定の変更

### 1. requirements.txt に追加

```
asyncpg>=0.28.0
psycopg2-binary>=2.9.5
```

### 2. データベース接続設定の更新

`src/infrastructure/database/connection.py` を更新：

```python
# PostgreSQL用の接続設定
async def get_async_session():
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://exchange_user:exchange_password@localhost:5432/exchange_analytics"
    )
    
    engine = create_async_engine(
        database_url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    
    return engine
```

## データ移行

### 1. SQLiteデータのエクスポート

```bash
# SQLiteデータをCSVにエクスポート
sqlite3 data/exchange_analytics.db ".mode csv" ".headers on" "SELECT * FROM price_data;" > price_data.csv
sqlite3 data/exchange_analytics.db ".mode csv" ".headers on" "SELECT * FROM technical_indicators;" > technical_indicators.csv
```

### 2. PostgreSQLへのデータインポート

```bash
# PostgreSQLにCSVデータをインポート
docker exec -i exchange_analytics_postgresql psql -U exchange_user -d exchange_analytics -c "\COPY price_data FROM STDIN WITH CSV HEADER" < price_data.csv
docker exec -i exchange_analytics_postgresql psql -U exchange_user -d exchange_analytics -c "\COPY technical_indicators FROM STDIN WITH CSV HEADER" < technical_indicators.csv
```

## パフォーマンス最適化

### 1. PostgreSQL設定の調整

`docker-compose.postgresql.yml` の設定：

```yaml
command: >
  postgres
  -c shared_buffers=256MB
  -c effective_cache_size=1GB
  -c maintenance_work_mem=64MB
  -c checkpoint_completion_target=0.9
  -c wal_buffers=16MB
  -c default_statistics_target=100
  -c random_page_cost=1.1
  -c effective_io_concurrency=200
  -c work_mem=4MB
  -c max_worker_processes=8
  -c max_parallel_workers_per_gather=4
```

### 2. インデックスの最適化

```sql
-- パーティショニング（大規模データ用）
CREATE TABLE price_data_partitioned (
    LIKE price_data INCLUDING ALL
) PARTITION BY RANGE (timestamp);

-- パーティション作成
CREATE TABLE price_data_2024_01 PARTITION OF price_data_partitioned
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

## 監視とメンテナンス

### 1. データベース監視

```sql
-- 接続数確認
SELECT count(*) FROM pg_stat_activity WHERE state = 'active';

-- テーブルサイズ確認
SELECT * FROM get_table_stats();

-- データベースサイズ確認
SELECT * FROM get_database_size();
```

### 2. 定期メンテナンス

```sql
-- 古いデータの削除（30日以上前）
SELECT * FROM cleanup_old_data(30);

-- 統計情報の更新
ANALYZE;

-- テーブルの最適化
VACUUM ANALYZE;
```

## トラブルシューティング

### 1. 接続エラー

```bash
# コンテナの状態確認
docker-compose -f docker-compose.postgresql.yml ps

# ログ確認
docker-compose -f docker-compose.postgresql.yml logs postgresql

# ポート確認
netstat -tlnp | grep 5432
```

### 2. パフォーマンス問題

```sql
-- スロークエリの確認
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- ロックの確認
SELECT * FROM pg_locks WHERE NOT granted;
```

### 3. ディスク容量問題

```sql
-- テーブルサイズの詳細確認
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 移行チェックリスト

- [ ] PostgreSQLコンテナの起動
- [ ] 接続テストの実行
- [ ] スキーマの作成確認
- [ ] 環境変数の設定
- [ ] アプリケーション設定の更新
- [ ] データの移行
- [ ] パフォーマンステスト
- [ ] アプリケーションの動作確認
- [ ] 監視設定の確認
- [ ] バックアップ設定の確認

## 注意事項

1. **データバックアップ**: 移行前に必ずSQLiteデータをバックアップしてください
2. **段階的移行**: 本番環境では段階的に移行することを推奨します
3. **パフォーマンス監視**: 移行後はパフォーマンスを継続的に監視してください
4. **ロールバック計画**: 問題が発生した場合のロールバック計画を準備してください

## サポート

問題が発生した場合は、以下を確認してください：

1. Docker Composeログ
2. PostgreSQLログ
3. アプリケーションログ
4. ネットワーク接続
5. ディスク容量
