# Configuration フォルダ解説

## 📁 概要

`config/`フォルダは、Exchange Analytics USD/JPY パターン検出システムの設定管理を担当しています。環境別設定、アラート設定、ログ設定、crontab 設定など、システム全体の設定を一元管理します。

## 🗂️ ディレクトリ構造

```
config/
├── base.py                    # 基本設定クラス
├── development.py             # 開発環境設定
├── production.py              # 本番環境設定
├── testing.py                 # テスト環境設定
├── alerts.yaml                # アラート設定
├── logging.yaml               # ログ設定
├── production_config.json     # 本番環境詳細設定
├── crontab/                   # crontab設定管理
│   ├── production/            # 本番稼働設定
│   ├── example/               # テスト・サンプル設定
│   └── docs/                  # ドキュメント
├── environments/              # 環境別設定（将来拡張）
├── plugins/                   # プラグイン設定（将来拡張）
└── README.md                  # このファイル
```

## 🔧 環境別設定ファイル

### base.py - 基本設定クラス

**基本設定クラス（1.0KB, 36 行）**

**主要設定項目**:

- **Flask 設定**: SECRET_KEY, DEBUG, TESTING
- **データベース**: DATABASE_URL, DATABASE_ECHO
- **Redis**: REDIS_URL
- **外部 API**: ALPHA_VANTAGE_API_KEY, OPENAI_API_KEY
- **GitHub**: GITHUB_TOKEN, GITHUB_WEBHOOK_SECRET
- **Discord**: DISCORD_WEBHOOK_URL
- **ログ**: LOG_LEVEL, LOG_FORMAT

**特徴**:

- 環境変数による設定管理
- デフォルト値の提供
- 型安全性の確保

### development.py - 開発環境設定

**開発環境設定（134B, 8 行）**

**設定内容**:

```python
DEBUG = True
DATABASE_ECHO = True
LOG_LEVEL = "DEBUG"
```

**用途**:

- 開発時のデバッグ有効化
- SQL クエリの詳細表示
- 詳細ログ出力

### production.py - 本番環境設定

**本番環境設定（131B, 8 行）**

**設定内容**:

```python
DEBUG = False
TESTING = False
DATABASE_ECHO = False
```

**用途**:

- セキュリティ強化
- パフォーマンス最適化
- 本番稼働に適した設定

### testing.py - テスト環境設定

**テスト環境設定（166B, 8 行）**

**設定内容**:

```python
TESTING = True
DATABASE_URL = "sqlite:///:memory:"
REDIS_URL = "redis://localhost:6379/1"
```

**用途**:

- テスト専用データベース
- 分離された Redis 環境
- テスト実行の最適化

## 🚨 alerts.yaml - アラート設定

**アラート設定ファイル（2.9KB, 106 行）**

### 主要設定項目

#### レート閾値アラート

```yaml
rate_threshold_alerts:
  enabled: true
  currency_pairs:
    USD/JPY:
      upper_threshold: 151.00
      lower_threshold: 140.00
      check_interval_minutes: 5
      severity: "high"
```

#### パターン検出アラート

```yaml
pattern_detection_alerts:
  enabled: true
  confidence_threshold: 0.80
  patterns:
    reversal:
      enabled: true
      severity: "high"
      min_confidence: 0.85
```

#### システムリソースアラート

```yaml
system_resource_alerts:
  enabled: true
  cpu_usage:
    warning_threshold: 70
    critical_threshold: 90
    severity: "medium"
```

#### 通知設定

```yaml
notification_settings:
  discord:
    enabled: true
    webhook_url: "${DISCORD_WEBHOOK_URL}"
    alert_type_webhooks:
      system_resource: "${DISCORD_MONITORING_WEBHOOK_URL}"
      rate_threshold: "${DISCORD_WEBHOOK_URL}"
```

## 📝 logging.yaml - ログ設定

**ログ設定ファイル（3.5KB, 173 行）**

### 主要設定項目

#### フォーマッター

```yaml
formatters:
  standard:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  detailed:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s"
  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
```

#### ハンドラー

```yaml
handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: standard

  file_info:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    filename: logs/app.log
    maxBytes: 10485760 # 10MB
    backupCount: 5
```

#### ロガー設定

```yaml
loggers:
  exchange_analytics:
    level: DEBUG
    handlers: [console, file_info, file_error]
    propagate: false

  exchange_analytics.domain:
    level: INFO
    handlers: [file_info]
    propagate: true
```

## ⚙️ production_config.json - 本番環境詳細設定

**本番環境詳細設定（2.5KB, 104 行）**

### 主要設定項目

#### データベース設定

```json
{
  "database": {
    "url": "postgresql+asyncpg://username:password@localhost:5432/forex_analytics",
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
  }
}
```

#### データ取得設定

```json
{
  "data_fetch": {
    "currency_pair": "USD/JPY",
    "symbol": "USDJPY=X",
    "intervals": {
      "5m": { "seconds": 300, "description": "5分足" },
      "1h": { "seconds": 3600, "description": "1時間足" },
      "4h": { "seconds": 14400, "description": "4時間足" },
      "1d": { "seconds": 86400, "description": "日足" }
    },
    "max_retries": 5,
    "retry_delay": 120,
    "fetch_history_days": 30
  }
}
```

#### スケジューラー設定

```json
{
  "scheduler": {
    "data_fetch_interval": 300,
    "d1_fetch_interval": 86400,
    "pattern_detection_interval": 300,
    "notification_interval": 60,
    "max_concurrent_tasks": 10,
    "task_timeout": 600
  }
}
```

#### テクニカル指標設定

```json
{
  "technical_indicators": {
    "rsi": {
      "period": 14,
      "overbought_threshold": 70,
      "oversold_threshold": 30
    },
    "macd": {
      "fast_period": 12,
      "slow_period": 26,
      "signal_period": 9
    },
    "bollinger_bands": {
      "period": 20,
      "std_dev": 2
    }
  }
}
```

#### 通知設定

```json
{
  "notifications": {
    "discord": {
      "webhook_url": "",
      "enabled": true,
      "notification_types": ["pattern_detection"],
      "rate_limit_per_minute": 20
    },
    "discord_monitoring": {
      "webhook_url": "",
      "enabled": true,
      "notification_types": [
        "system_status",
        "error_alert",
        "performance_report",
        "log_summary"
      ],
      "rate_limit_per_minute": 10
    }
  }
}
```

## ⏰ crontab/ - crontab 設定管理

**定期実行タスクの設定管理**

### 📁 production/ - 本番稼働設定

**本番環境での定期実行設定**

- **`current_crontab.txt`**: 現在の本番稼働設定（2.5KB, 53 行）
- **`current_crontab_backup_*.txt`**: 設定バックアップ

**主要タスク**:

- USD/JPY データ取得（5 分間隔）
- 日次レポート（毎日 6:00）
- 週次統計（毎週土曜 6:00）

### 📁 example/ - テスト・サンプル設定

**テスト・開発用設定**

- **`example_crontab.txt`**: 基本テスト設定（2.1KB, 56 行）
- **`test_crontab.txt`**: 機能テスト設定（767B, 17 行）
- **`crontab-example.txt`**: サンプル設定（2.4KB, 59 行）

### 📁 docs/ - ドキュメント

**設定ガイド・ドキュメント**

- **`crontab_guide.md`**: crontab 設定の詳細ガイド（7.1KB, 274 行）

## 🎯 設定管理の設計思想

### 1. 環境分離

- **開発環境**: デバッグ有効・詳細ログ
- **本番環境**: セキュリティ重視・パフォーマンス最適化
- **テスト環境**: 分離されたデータベース・独立した設定

### 2. 階層化設定

- **基本設定**: 全環境共通の設定
- **環境別設定**: 環境固有の設定
- **詳細設定**: 機能別の詳細設定

### 3. 外部化設定

- **環境変数**: 機密情報の外部化
- **設定ファイル**: 構造化された設定管理
- **動的設定**: ランタイムでの設定変更

### 4. バックアップ・バージョン管理

- **設定バックアップ**: 変更履歴の保持
- **バージョン管理**: 設定の履歴追跡
- **ロールバック**: 設定変更の復旧

## 📊 統計情報

- **総設定ファイル数**: 15+ ファイル
- **設定項目数**: 100+ 項目
- **環境数**: 3 環境（development, production, testing）
- **アラートタイプ**: 6 種類
- **ログレベル**: 5 レベル
- **crontab タスク**: 10+ タスク

## 🚀 使用方法

### 環境設定の読み込み

```python
from config.base import BaseConfig
from config.development import DevelopmentConfig
from config.production import ProductionConfig

# 環境に応じた設定の選択
config = DevelopmentConfig() if DEBUG else ProductionConfig()
```

### アラート設定の読み込み

```python
import yaml

with open('config/alerts.yaml', 'r') as f:
    alert_config = yaml.safe_load(f)
```

### ログ設定の適用

```python
import logging.config

with open('config/logging.yaml', 'r') as f:
    logging_config = yaml.safe_load(f)
    logging.config.dictConfig(logging_config)
```

### crontab 設定の適用

```bash
# 本番設定の適用
crontab config/crontab/production/current_crontab.txt

# 設定確認
crontab -l
```

## 🔧 メンテナンス

### 設定更新

1. **バックアップ**: 現在の設定をバックアップ
2. **テスト**: 開発環境で設定をテスト
3. **段階的適用**: 本番環境に段階的に適用
4. **監視**: 設定変更後の動作監視

### 設定検証

```bash
# 設定ファイルの構文チェック
python -c "import yaml; yaml.safe_load(open('config/alerts.yaml'))"

# JSON設定の検証
python -c "import json; json.load(open('config/production_config.json'))"
```

## 🚨 注意事項

1. **機密情報**: API キーなどの機密情報は環境変数で管理
2. **バックアップ**: 設定変更前は必ずバックアップを取得
3. **テスト**: 本番環境での適用前にテスト環境で検証
4. **監視**: 設定変更後のシステム動作を監視
5. **ドキュメント**: 設定変更時はドキュメントを更新
