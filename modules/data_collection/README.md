# データ収集モジュール (Data Collection Module)

## 使っている技術スタック

- **Python 3.8+**
- **asyncio**: 非同期処理
- **asyncpg**: PostgreSQL非同期接続
- **aiohttp**: 非同期HTTP通信
- **yfinance**: Yahoo Finance API
- **PostgreSQL**: データベース
- **logging**: ログ管理
- **dataclasses**: データ構造定義
- **enum**: 列挙型管理

## 機能の概要

金融データ（為替レート、株価等）をYahoo Finance APIから収集し、PostgreSQLデータベースに保存する包括的なデータ収集システムです。継続的データ収集、バックフィル、手動収集の3つのモードをサポートし、レート制限対応、エラーハンドリング、データ品質管理機能を提供します。

## 背景・目的

### 背景
- 為替分析アプリケーションに必要な高品質な金融データの収集
- 複数の時間軸（5分、15分、1時間、4時間、日足）でのデータ管理
- リアルタイムデータ更新と履歴データの補完
- API制限への対応と安定したデータ収集

### 目的
- 信頼性の高い金融データの継続的収集
- データ品質の自動検証と管理
- システム障害時の自動復旧機能
- 効率的なデータベース保存と管理

## コンポーネント設計

### 1. データ収集サービス (`DataCollectionService`)
```python
# メインサービスクラス
- 継続的収集モード
- バックフィルモード  
- 手動収集モード
- ヘルスチェック機能
```

### 2. Yahoo Finance プロバイダー (`YahooFinanceProvider`)
```python
# データ取得プロバイダー
- 履歴データ取得
- 最新データ取得
- レート制限対応
- データ品質スコア計算
```

### 3. インテリジェントデータコレクター (`IntelligentDataCollector`)
```python
# 高度なデータ収集機能
- 優先度ベース収集
- バッチ処理
- フォールバック機能
- 統計情報管理
```

### 4. データベース保存機能 (`DatabaseSaver`)
```python
# データベース操作
- UPSERT機能
- バッチ処理
- データ検証
- 品質メトリクス
```

### 5. レート制限管理 (`RateLimitManager`)
```python
# API制限対応
- トークンバケット
- スライディングウィンドウ
- サーキットブレーカー
- 適応的制限
```

### 6. 設定管理 (`DataCollectionSettings`)
```python
# 設定管理
- 環境変数読み込み
- Yahoo Finance設定
- データベース設定
- 収集設定
```

## できること・制限事項

### できること
- **複数時間軸での同時データ収集**: 5分、15分、1時間、4時間、日足
- **継続的データ更新**: リアルタイムでの最新データ収集
- **履歴データバックフィル**: 過去データの一括取得
- **データ品質管理**: 自動検証と品質スコア計算
- **エラー回復**: プロバイダー障害時の自動フォールバック
- **レート制限対応**: API制限への適応的対応
- **バッチ処理**: 効率的なデータベース保存
- **監視機能**: システムヘルスチェックとログ管理

### 制限事項
- **Yahoo Finance API依存**: 外部APIの制限に依存
- **データ遅延**: リアルタイムデータに15-20分の遅延
- **API制限**: 1秒間に10リクエストの制限
- **データ範囲**: 過去1年程度の履歴データ
- **シンボル制限**: Yahoo Financeで利用可能なシンボルのみ

## コンポーネント使用時のオプション

### データ収集モード
```python
# 継続的収集モード
settings.collection.mode = DataCollectionMode.CONTINUOUS

# バックフィルモード
settings.collection.mode = DataCollectionMode.BACKFILL

# 手動モード
settings.collection.mode = DataCollectionMode.MANUAL
```

### 時間軸設定
```python
# 利用可能な時間軸
timeframes = [
    TimeFrame.M5,   # 5分足
    TimeFrame.M15,  # 15分足
    TimeFrame.H1,   # 1時間足
    TimeFrame.H4,   # 4時間足
    TimeFrame.D1    # 日足
]
```

### シンボル設定
```python
# 通貨ペア
symbols = [
    "USDJPY=X",  # 米ドル/円
    "EURJPY=X",  # ユーロ/円
    "GBPJPY=X",  # 英ポンド/円
    "AUDJPY=X"   # 豪ドル/円
]
```

### レート制限設定
```python
# Yahoo Finance設定
yahoo_config = YahooFinanceConfig(
    rate_limit_per_second=10.0,
    burst_capacity=50,
    timeout_seconds=30,
    retry_attempts=3
)
```

## 関連ファイル・ディレクトリ構造

```
/app/modules/data_collection/
├── main.py                          # メインスクリプト
├── config/
│   └── settings.py                  # 設定管理
├── core/
│   ├── data_collection_service.py   # メインサービス
│   ├── intelligent_collector/       # インテリジェント収集
│   │   ├── intelligent_collector.py
│   │   ├── priority_manager.py
│   │   └── batch_processor.py
│   ├── database_saver/              # データベース保存
│   │   ├── database_saver.py
│   │   ├── data_validator.py
│   │   └── quality_metrics.py
│   └── rate_limiter/                # レート制限
│       ├── rate_limit_manager.py
│       ├── token_bucket.py
│       ├── sliding_window.py
│       └── circuit_breaker.py
├── providers/
│   ├── base_provider.py             # ベースプロバイダー
│   └── yahoo_finance.py             # Yahoo Finance実装
├── daemon/
│   └── data_collection_daemon.py    # デーモンプロセス
├── tools/                           # ユーティリティツール
│   ├── collect_and_save_data.py
│   ├── data_gap_checker.py
│   ├── emergency_data_fix.py
│   └── realtime_monitor.py
├── utils/
│   └── timezone_utils.py            # タイムゾーン処理
└── tests/                           # テストファイル
    ├── test_data_collection_service.py
    ├── test_yahoo_finance_provider.py
    └── test_database_save.py
```

## 注意点

### 運用時の注意点
1. **API制限**: Yahoo Finance APIの制限を超えないよう注意
2. **データベース接続**: 接続プールの適切な管理が必要
3. **エラーハンドリング**: ネットワーク障害時の適切な処理
4. **ログ管理**: 大量のログ出力によるディスク容量の監視
5. **タイムゾーン**: JST時刻での統一的な処理

### 開発時の注意点
1. **非同期処理**: asyncioの適切な使用
2. **リソース管理**: データベース接続とHTTPセッションの適切な解放
3. **設定管理**: 環境変数の適切な設定
4. **テスト**: モックを使用したAPI制限のテスト
5. **エラー処理**: 例外の適切なキャッチとログ出力

### セキュリティ考慮事項
1. **認証情報**: データベース認証情報の適切な管理
2. **API制限**: 過度なリクエストによるIP制限の回避
3. **データ検証**: 入力データの適切な検証
4. **ログ情報**: 機密情報のログ出力回避

### パフォーマンス考慮事項
1. **バッチ処理**: 大量データの効率的な処理
2. **接続プール**: データベース接続の最適化
3. **メモリ使用量**: 大量データ処理時のメモリ管理
4. **並列処理**: 複数シンボルの並列収集

---

**作成日**: 2025年９月18日  
**バージョン**: 1.0  
**対象モジュール**: `/app/modules/data_collection`
