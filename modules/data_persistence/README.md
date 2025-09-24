# データ永続化モジュール (Data Persistence Module)

## 使っている技術スタック

- **Python 3.8+**
- **PostgreSQL**: メインデータベース
- **TimescaleDB**: 時系列データ最適化拡張
- **asyncpg**: PostgreSQL非同期接続ライブラリ
- **psycopg2**: PostgreSQL同期接続ライブラリ
- **asyncio**: 非同期処理
- **dataclasses**: データ構造定義
- **enum**: 列挙型管理
- **logging**: ログ管理

## 機能の概要

金融データ（価格データ、分析結果、ログ等）をPostgreSQLデータベースに永続化し、TimescaleDBの時系列データ最適化機能を活用した高性能なデータ管理システムです。データベース接続管理、スキーマ管理、データ操作、マイグレーション機能を提供し、大容量の時系列データを効率的に処理します。

## 背景・目的

### 背景
- 為替分析アプリケーションの大量時系列データの永続化
- 複数の時間軸（1分〜日足）でのデータ管理
- LLM分析結果の構造化保存
- データ収集ログとパフォーマンス監視
- 高可用性とスケーラビリティの要求

### 目的
- 高性能な時系列データの保存と取得
- データ整合性の保証とトランザクション管理
- 自動的なスキーマ管理とマイグレーション
- データ圧縮とストレージ最適化
- 包括的なデータ監視とログ管理

## コンポーネント設計

### 1. データベース接続管理 (`DatabaseConnectionManager`)
```python
# 接続プール管理
- 非同期接続プール
- トランザクション処理
- ヘルスチェック機能
- TimescaleDB拡張管理
```

### 2. データベース初期化 (`DatabaseInitializer`)
```python
# データベースセットアップ
- テーブル作成
- インデックス最適化
- ハイパーテーブル設定
- 圧縮・保持ポリシー
```

### 3. 価格データリポジトリ (`PriceDataRepository`)
```python
# データ操作
- CRUD操作
- UPSERT機能
- データギャップ検出
- 統計情報取得
```

### 4. マイグレーション管理 (`MigrationManager`)
```python
# スキーマ管理
- バージョン管理
- マイグレーション実行
- ロールバック機能
- 履歴追跡
```

### 5. データモデル群
```python
# データ構造定義
- PriceDataModel: 価格データ
- LLMAnalysisResultsModel: AI分析結果
- DataCollectionLogModel: 収集ログ
- DataQualityMetricsModel: 品質メトリクス
```

### 6. 設定管理 (`DataPersistenceSettings`)
```python
# 設定管理
- データベース接続設定
- TimescaleDB設定
- 圧縮・保持設定
- 環境変数管理
```

## できること・制限事項

### できること
- **高性能な時系列データ保存**: TimescaleDBによる最適化
- **自動データ圧縮**: 時間軸別の圧縮ポリシー
- **データギャップ検出**: 欠損データの自動検出
- **スキーマ管理**: バージョン管理されたマイグレーション
- **トランザクション処理**: ACID特性の保証
- **接続プール管理**: 効率的な接続リソース管理
- **データ品質監視**: 品質スコアとメトリクス
- **LLM分析結果保存**: 構造化されたAI分析データ
- **ログ管理**: 包括的なシステムログ
- **統計情報提供**: データ範囲とパフォーマンス統計

### 制限事項
- **PostgreSQL依存**: PostgreSQL/TimescaleDBの制限に依存
- **メモリ使用量**: 大量データ処理時のメモリ制限
- **接続数制限**: データベース接続プールの制限
- **ストレージ容量**: ディスク容量の制限
- **ネットワーク依存**: データベース接続の安定性依存

## コンポーネント使用時のオプション

### データベース接続設定
```python
# 接続プール設定
database_config = DatabaseConfig(
    host="localhost",
    port=5432,
    database="trading_system",
    min_connections=5,
    max_connections=20,
    connection_timeout=60
)
```

### TimescaleDB設定
```python
# TimescaleDB機能設定
settings = DataPersistenceSettings(
    enable_timescaledb=True,
    enable_compression=True,
    compression_interval="7 days",
    retention_period="1 year"
)
```

### 時間軸設定
```python
# 利用可能な時間軸
timeframes = [
    TimeFrame.M1,   # 1分足
    TimeFrame.M5,   # 5分足
    TimeFrame.M15,  # 15分足
    TimeFrame.M30,  # 30分足
    TimeFrame.H1,   # 1時間足
    TimeFrame.H4,   # 4時間足
    TimeFrame.D1    # 日足
]
```

### 分析タイプ設定
```python
# LLM分析タイプ
analysis_types = [
    AnalysisType.MARKET_SENTIMENT,      # 市場センチメント
    AnalysisType.PATTERN_INTERPRETATION, # パターン解釈
    AnalysisType.RISK_SCENARIO,         # リスクシナリオ
    AnalysisType.TECHNICAL_ANALYSIS,    # テクニカル分析
    AnalysisType.FUNDAMENTAL_ANALYSIS   # ファンダメンタル分析
]
```

### マイグレーション設定
```python
# マイグレーション管理
migration_manager = MigrationManager(connection_manager)
migration_manager.add_migration(Migration001InitialSchema())
await migration_manager.run_migrations()
```

## 関連ファイル・ディレクトリ構造

```
/app/modules/data_persistence/
├── config/
│   └── settings.py                    # 設定管理
├── core/
│   ├── database/                      # データベース管理
│   │   ├── connection_manager.py      # 接続管理
│   │   └── database_initializer.py    # 初期化
│   └── repositories/                  # データアクセス層
│       └── price_data_repository.py   # 価格データリポジトリ
├── models/                            # データモデル
│   ├── price_data.py                  # 価格データモデル
│   ├── llm_analysis_results.py        # LLM分析結果モデル
│   ├── data_collection_log.py         # データ収集ログモデル
│   ├── data_quality_metrics.py        # データ品質メトリクスモデル
│   ├── economic_calendar.py           # 経済カレンダーモデル
│   └── economic_indicators.py         # 経済指標モデル
├── migrations/                        # マイグレーション
│   ├── migration_manager.py           # マイグレーション管理
│   └── migration_001_initial_schema.py # 初期スキーマ
└── tests/                             # テストファイル
    └── test_database_connection.py    # 接続テスト
```

## 注意点

### 運用時の注意点
1. **接続プール管理**: 適切な接続数の設定と監視
2. **TimescaleDB設定**: 圧縮ポリシーと保持期間の最適化
3. **データベース容量**: ディスク容量の監視とアラート
4. **パフォーマンス監視**: クエリパフォーマンスの定期的な確認
5. **バックアップ**: 定期的なデータベースバックアップの実行

### 開発時の注意点
1. **非同期処理**: asyncpgの適切な使用とリソース管理
2. **トランザクション**: 適切なトランザクション境界の設定
3. **マイグレーション**: スキーマ変更時の適切なマイグレーション作成
4. **データ型**: PostgreSQLのデータ型とPython型の適切なマッピング
5. **インデックス**: クエリパフォーマンスに応じたインデックス設計

### セキュリティ考慮事項
1. **接続認証**: データベース認証情報の適切な管理
2. **SQLインジェクション**: パラメータ化クエリの使用
3. **アクセス制御**: データベースユーザーの権限管理
4. **暗号化**: 接続の暗号化とデータの暗号化
5. **監査ログ**: データベースアクセスの監査

### パフォーマンス考慮事項
1. **接続プール**: 適切なプールサイズの設定
2. **インデックス**: クエリパターンに応じたインデックス最適化
3. **圧縮**: TimescaleDBの圧縮機能の活用
4. **パーティショニング**: 時系列データの適切なパーティショニング
5. **クエリ最適化**: 効率的なクエリの作成と実行計画の確認

### TimescaleDB特有の注意点
1. **ハイパーテーブル**: 適切なチャンク間隔の設定
2. **圧縮ポリシー**: データアクセスパターンに応じた圧縮設定
3. **保持ポリシー**: データ保持期間の適切な設定
4. **集約**: 時系列データの効率的な集約処理
5. **拡張機能**: TimescaleDB拡張の適切な管理

---

**作成日**: 2025年９月18日
**バージョン**: 1.0  
**対象モジュール**: `/app/modules/data_persistence`
