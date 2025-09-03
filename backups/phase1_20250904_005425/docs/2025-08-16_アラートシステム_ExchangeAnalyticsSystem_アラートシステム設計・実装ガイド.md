# Exchange Analytics System - アラートシステム設計・実装ガイド

## 📋 目次

1. [概要](#概要)
2. [システムアーキテクチャ](#システムアーキテクチャ)
3. [データベース設計](#データベース設計)
4. [設定管理](#設定管理)
5. [CLI機能](#cli機能)
6. [実装詳細](#実装詳細)
7. [拡張・カスタマイズ](#拡張カスタマイズ)
8. [運用・監視](#運用監視)
9. [トラブルシューティング](#トラブルシューティング)
10. [今後の拡張計画](#今後の拡張計画)

---

## 概要

### 🎯 目的
Exchange Analytics Systemのアラートシステムは、以下の機能を提供します：

- **リアルタイム監視**: システムリソース、API エラー、データ取得状況の監視
- **為替レート監視**: 設定された閾値を超えた場合のアラート
- **パターン検出**: テクニカル分析によるパターン検出時のアラート
- **通知機能**: Discordチャンネル分離による適切な通知配信
- **管理機能**: アラートの確認・解決・履歴管理

### 🔧 主要機能
- アラートタイプ別のDiscordチャンネル分離
- 重要度レベル管理（low, medium, high, critical）
- アラート状態管理（active, acknowledged, resolved）
- 設定ファイルによる柔軟なカスタマイズ
- CLI による管理・監視機能

---

## システムアーキテクチャ

### 📊 全体構成図

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   監視対象      │    │   アラート      │    │   通知システム  │
│                 │    │   システム      │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • システム      │───▶│ • アラート検出  │───▶│ • Discord       │
│   リソース      │    │ • 重要度判定    │    │ • チャンネル分離│
│ • API エラー    │    │ • 状態管理      │    │ • Webhook送信   │
│ • データ取得    │    │ • 履歴管理      │    │                 │
│ • 為替レート    │    │                 │    │                 │
│ • パターン検出  │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   設定管理      │    │   データベース  │    │   CLI管理       │
│                 │    │                 │    │                 │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • YAML設定      │    │ • PostgreSQL    │    │ • アラート表示  │
│ • 環境変数      │    │ • アラートテーブル│   │ • 設定管理      │
│ • 動的更新      │    │ • 履歴管理      │    │ • 状態変更      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 🏗️ コンポーネント構成

#### 1. データ層
- **AlertModel**: アラートデータの永続化
- **AlertRepositoryImpl**: データベース操作
- **BaseModel**: 共通フィールド管理

#### 2. ビジネスロジック層
- **AlertConfigManager**: 設定管理
- **DiffDetectionService**: 差分検出
- **TechnicalIndicatorDiffCalculator**: テクニカル指標差分計算

#### 3. プレゼンテーション層
- **CLI Commands**: コマンドライン操作
- **Monitor Commands**: 監視・表示機能
- **Alert Config Commands**: 設定管理

#### 4. 外部連携層
- **Discord Webhook**: 通知配信
- **Environment Variables**: 設定値管理

---

## データベース設計

### 📊 テーブル構造

#### alerts テーブル

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    uuid VARCHAR(36) UNIQUE NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    currency_pair VARCHAR(10),
    message TEXT NOT NULL,
    details JSONB,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    acknowledged_by VARCHAR(100),
    resolved_by VARCHAR(100),
    related_data_id INTEGER,
    related_data_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);
```

### 🔍 インデックス設計

```sql
-- アラートタイプでの検索
CREATE INDEX idx_alert_type ON alerts(alert_type);

-- 重要度での検索
CREATE INDEX idx_alert_severity ON alerts(severity);

-- ステータスでの検索
CREATE INDEX idx_alert_status ON alerts(status);

-- 作成時刻での検索
CREATE INDEX idx_alert_created_at ON alerts(created_at);

-- 通貨ペアでの検索
CREATE INDEX idx_alert_currency_pair ON alerts(currency_pair);

-- アクティブアラートの検索
CREATE INDEX idx_alert_active ON alerts(status, created_at);
```

### 📝 フィールド詳細

| フィールド名 | 型 | 説明 | 例 |
|-------------|----|------|----|
| `id` | SERIAL | 主キー | 1, 2, 3... |
| `uuid` | VARCHAR(36) | 一意識別子 | "550e8400-e29b-41d4-a716-446655440000" |
| `alert_type` | VARCHAR(50) | アラートタイプ | "system_resource", "rate_threshold" |
| `severity` | VARCHAR(20) | 重要度 | "low", "medium", "high", "critical" |
| `status` | VARCHAR(20) | ステータス | "active", "acknowledged", "resolved" |
| `currency_pair` | VARCHAR(10) | 通貨ペア | "USD/JPY", "EUR/USD" |
| `message` | TEXT | アラートメッセージ | "Memory usage exceeded threshold" |
| `details` | JSONB | 詳細データ | `{"resource": "memory", "usage": 85.2}` |
| `acknowledged_at` | TIMESTAMP | 確認時刻 | 2025-08-16 17:30:00+09 |
| `resolved_at` | TIMESTAMP | 解決時刻 | 2025-08-16 18:00:00+09 |
| `acknowledged_by` | VARCHAR(100) | 確認者 | "admin" |
| `resolved_by` | VARCHAR(100) | 解決者 | "admin" |
| `related_data_id` | INTEGER | 関連データID | 123 |
| `related_data_type` | VARCHAR(50) | 関連データタイプ | "price_data" |
| `created_at` | TIMESTAMP | 作成時刻 | 2025-08-16 17:25:00+09 |
| `updated_at` | TIMESTAMP | 更新時刻 | 2025-08-16 17:25:00+09 |
| `version` | INTEGER | バージョン | 1 |

---

## 設定管理

### 📁 設定ファイル構造

#### config/alerts.yaml

```yaml
# レート閾値アラート設定
rate_threshold_alerts:
  enabled: true
  currency_pairs:
    USD/JPY:
      upper_threshold: 151.00
      lower_threshold: 140.00
      check_interval_minutes: 5
      severity: "high"
    EUR/USD:
      upper_threshold: 1.1500
      lower_threshold: 1.0500
      check_interval_minutes: 5
      severity: "medium"

# パターン検出アラート設定
pattern_detection_alerts:
  enabled: true
  confidence_threshold: 0.80
  patterns:
    reversal:
      enabled: true
      severity: "high"
      min_confidence: 0.85
    continuation:
      enabled: true
      severity: "medium"
      min_confidence: 0.80
    divergence:
      enabled: true
      severity: "high"
      min_confidence: 0.90

# システムリソースアラート設定
system_resource_alerts:
  enabled: true
  cpu_usage:
    warning_threshold: 70
    critical_threshold: 90
    severity: "medium"
  memory_usage:
    warning_threshold: 80
    critical_threshold: 95
    severity: "high"
  disk_usage:
    warning_threshold: 85
    critical_threshold: 95
    severity: "medium"

# API エラーアラート設定
api_error_alerts:
  enabled: true
  rate_limit_threshold: 5
  timeout_threshold: 3
  severity: "medium"

# データ取得エラーアラート設定
data_fetch_alerts:
  enabled: true
  consecutive_failures: 3
  severity: "high"
  timeframes:
    - "5m"
    - "1h"
    - "4h"
    - "1d"

# 通知設定
notification_settings:
  email:
    enabled: false
    recipients: []
  discord:
    enabled: true
    webhook_url: "${DISCORD_WEBHOOK_URL}"
    channel_id: "${DISCORD_CHANNEL_ID}"
    # アラートタイプ別のWebhook URL設定
    alert_type_webhooks:
      # システム系アラート（リソース監視、API エラー等）
      system_resource: "${DISCORD_MONITORING_WEBHOOK_URL}"
      api_error: "${DISCORD_MONITORING_WEBHOOK_URL}"
      data_fetch_error: "${DISCORD_MONITORING_WEBHOOK_URL}"
      # 為替系アラート（レート閾値、パターン検出等）
      rate_threshold: "${DISCORD_WEBHOOK_URL}"
      pattern_detection: "${DISCORD_WEBHOOK_URL}"
      # デフォルト（設定されていないアラートタイプ用）
      default: "${DISCORD_WEBHOOK_URL}"
  slack:
    enabled: false
    webhook_url: ""

# アラート管理設定
alert_management:
  auto_resolve:
    enabled: true
    resolve_after_hours: 24
  escalation:
    enabled: true
    escalation_after_hours: 2
  retention:
    keep_resolved_days: 30
```

### 🔧 環境変数設定

#### .env ファイル

```bash
# === 通知設定 ===
DISCORD_WEBHOOK_URL=https://canary.discord.com/api/webhooks/1403643478361116672/nf6aIMHvPjNVX4x10i_ARpbTa9V5_XAtGUenrbkauV1ibdDZbT9l5U7EoTreZ5LiwwKZ

DISCORD_MONITORING_WEBHOOK_URL=https://canary.discord.com/api/webhooks/1404124259520876595/NV4t96suXeoQN6fvOnpKRNpDdBVBESRvChWLp3cZ3TMWuWwJvYX9VfmDWEBzbI9DoX_d

# オプショナル
DISCORD_CHANNEL_ID=your_channel_id
```

### 🎛️ 設定管理クラス

#### AlertConfigManager

```python
class AlertConfigManager:
    """アラート設定管理クラス"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "config/alerts.yaml"
        self._config: Optional[AlertConfig] = None

        # .envファイルを読み込み
        self._load_env_file()
        self._load_config()

    def get_discord_webhook_url(self, alert_type: str) -> Optional[str]:
        """アラートタイプ別のDiscord Webhook URLを取得"""

    def get_discord_channel_id(self) -> Optional[str]:
        """DiscordチャンネルIDを取得"""

    def is_alert_enabled(self, alert_type: str) -> bool:
        """アラートタイプが有効かどうかを判定"""

    def get_threshold_config(self, alert_type: str, currency_pair: str = None) -> Dict:
        """閾値設定を取得"""
```

---

## CLI機能

### 🖥️ コマンド一覧

#### 1. アラート設定管理

```bash
# 設定表示
exchange-analytics alert-config show

# 設定検証
exchange-analytics alert-config validate

# 設定編集（プレースホルダー）
exchange-analytics alert-config edit

# 設定再読み込み
exchange-analytics alert-config reload
```

#### 2. アラート監視・管理

```bash
# アラート一覧表示
exchange-analytics monitor alerts

# フィルタリングオプション
exchange-analytics monitor alerts --limit 10
exchange-analytics monitor alerts --severity high
exchange-analytics monitor alerts --alert-type system_resource
exchange-analytics monitor alerts --active-only

# アラート確認
exchange-analytics monitor alerts acknowledge <alert_id> --by <user>

# アラート解決
exchange-analytics monitor alerts resolve <alert_id> --by <user>
```

### 📊 CLI出力例

#### アラート設定表示

```
🚨 アラート設定
                💰 レート閾値アラート設定
┏━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ 通貨ペア ┃ 上限閾値 ┃ 下限閾値 ┃ チェック間隔 ┃ 重要度 ┃
┡━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━╇━━━━━━━━┩
│ USD/JPY  │ 151.0    │ 140.0    │ 5分          │ HIGH   │
│ EUR/USD  │ 1.15     │ 1.05     │ 5分          │ MEDIUM │
└──────────┴──────────┴──────────┴──────────────┴────────┘
```

#### アラート一覧表示

```
🚨 アクティブアラート確認中...
                                                   🚨 Active Alerts
┏━━━━┳━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ ID ┃ Type              ┃ Severity ┃ Message                                          ┃ Created             ┃ Status ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ 6  │ system_resource   │ MEDIUM   │ CPU usage exceeded warning threshold (75%)       │ 2025-08-16 17:51:01 │ ACTIVE │
│ 5  │ data_fetch_error  │ MEDIUM   │ Failed to fetch 5-minute data from Yahoo Finance │ 2025-08-16 17:00:24 │ ACTIVE │
│ 4  │ pattern_detection │ HIGH     │ Strong reversal pattern detected on USD/JPY      │ 2025-08-16 17:00:24 │ ACTIVE │
│ 1  │ rate_threshold    │ HIGH     │ USD/JPY rate exceeded threshold (151.00)         │ 2025-08-16 17:00:24 │ ACTIVE │
└────┴───────────────────┴──────────┴──────────────────────────────────────────────────┴─────────────────────┴────────┘
╭─ 📊 Alert Summary ──╮
│ 🚨 Active Alerts: 4 │
│ ⚠️ High Severity: 2  │
╰─────────────────────╯
```
---

## 実装詳細

### 📁 ファイル構成

```
src/
├── infrastructure/
│   ├── database/
│   │   ├── models/
│   │   │   ├── alert_model.py          # アラートデータモデル
│   │   │   └── base.py                 # 基本モデル（タイムスタンプ管理）
│   │   └── repositories/
│   │       └── alert_repository_impl.py # アラートリポジトリ実装
│   └── config/
│       └── alert_config_manager.py     # アラート設定管理
├── presentation/
│   └── cli/
│       └── commands/
│           ├── alert_config_commands.py # アラート設定CLI
│           └── monitor_commands.py      # 監視・表示CLI
└── utils/
    └── logging_config.py               # ログ設定

config/
└── alerts.yaml                         # アラート設定ファイル

.env                                    # 環境変数設定
```

### 🔧 主要クラス・メソッド

#### AlertModel

```python
class AlertModel(BaseModel):
    """アラートデータモデル"""

    __tablename__ = "alerts"

    # フィールド定義
    uuid = Column(String(36), unique=True, nullable=False)
    alert_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="active")
    # ... その他のフィールド

    def __init__(self, **kwargs):
        """初期化時にUUIDを自動生成"""
        if "uuid" not in kwargs:
            kwargs["uuid"] = str(uuid.uuid4())
        super().__init__(**kwargs)

    def acknowledge(self, acknowledged_by: str) -> None:
        """アラートを確認済みにする"""

    def resolve(self, resolved_by: str) -> None:
        """アラートを解決済みにする"""

    def is_active(self) -> bool:
        """アラートがアクティブかどうかを判定"""

    def is_high_severity(self) -> bool:
        """高重要度かどうかを判定"""
```

#### AlertRepositoryImpl

```python
class AlertRepositoryImpl(BaseRepositoryImpl):
    """アラートリポジトリ実装"""

    async def find_active_alerts(
        self,
        limit: Optional[int] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
    ) -> List[AlertModel]:
        """アクティブなアラートを取得"""

    async def find_by_severity(
        self, severity: str, limit: Optional[int] = None
    ) -> List[AlertModel]:
        """重要度でアラートを検索"""

    async def find_by_type(
        self, alert_type: str, limit: Optional[int] = None
    ) -> List[AlertModel]:
        """アラートタイプで検索"""

    async def find_recent_alerts(
        self, hours: int = 24, limit: Optional[int] = None
    ) -> List[AlertModel]:
        """最近のアラートを取得"""

    async def get_alert_statistics(self) -> Dict[str, Any]:
        """アラート統計情報を取得"""

    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """アラートを確認済みにする"""

    async def resolve_alert(self, alert_id: int, resolved_by: str) -> bool:
        """アラートを解決済みにする"""

    async def create_alert(
        self,
        alert_type: str,
        severity: str,
        message: str,
        currency_pair: Optional[str] = None,
        details: Optional[Dict] = None,
        related_data_id: Optional[int] = None,
        related_data_type: Optional[str] = None,
    ) -> Optional[AlertModel]:
        """新しいアラートを作成"""
```

### ⏰ タイムスタンプ管理

#### 日本時間設定

```python
def get_jst_now() -> datetime:
    """日本時間の現在時刻を取得"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).replace(tzinfo=None)

class BaseModel(Base):
    """全モデルの基底クラス"""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=get_jst_now,
        comment="作成日時"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=get_jst_now,
        onupdate=get_jst_now,
        comment="更新日時",
    )
```

#### CLI表示での日本時間変換

```python
# タイムスタンプをJSTに変換
created_time = alert.created_at
if created_time:
    # タイムゾーン情報がない場合はJSTとして扱う
    if created_time.tzinfo is None:
        jst = pytz.timezone('Asia/Tokyo')
        created_time = jst.localize(created_time)

    # JSTに変換して表示
    jst = pytz.timezone('Asia/Tokyo')
    jst_time = created_time.astimezone(jst)
    created_str = jst_time.strftime("%Y-%m-%d %H:%M:%S")
else:
    created_str = "N/A"
```

---

## 拡張・カスタマイズ

### 🔧 新しいアラートタイプの追加

#### 1. 設定ファイルに追加

```yaml
# config/alerts.yaml
new_alert_type_alerts:
  enabled: true
  threshold: 100
  severity: "medium"
  check_interval_minutes: 10
```

#### 2. 環境変数に追加

```bash
# .env
DISCORD_NEW_ALERT_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

#### 3. 設定ファイルにWebhook設定を追加

```yaml
notification_settings:
  discord:
    alert_type_webhooks:
      new_alert_type: "${DISCORD_NEW_ALERT_WEBHOOK_URL}"
```

#### 4. アラート作成コード

```python
# アラート作成例
alert = await alert_repo.create_alert(
    alert_type='new_alert_type',
    severity='medium',
    message='New alert triggered',
    details={'threshold': 100, 'current_value': 105}
)
```

### 🎨 新しい通知チャンネルの追加

#### 1. 設定ファイルに追加

```yaml
notification_settings:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    alert_type_webhooks:
      system_resource: "${SLACK_MONITORING_WEBHOOK_URL}"
      rate_threshold: "${SLACK_TRADING_WEBHOOK_URL}"
```

#### 2. 通知クラスの実装

```python
class SlackNotifier:
    """Slack通知クラス"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_alert(self, alert: AlertModel) -> bool:
        """アラートをSlackに送信"""
        # 実装
        pass
```

### 📊 新しい統計情報の追加

#### 1. AlertRepositoryImplにメソッド追加

```python
async def get_custom_statistics(self) -> Dict[str, Any]:
    """カスタム統計情報を取得"""
    try:
        # カスタムクエリの実装
        query = select(
            AlertModel.alert_type,
            func.count(AlertModel.id)
        ).group_by(AlertModel.alert_type)

        result = await self.session.execute(query)
        return {"custom_stats": dict(result)}

    except Exception as e:
        logger.error(f"Error getting custom statistics: {e}")
        return {}
```

#### 2. CLIコマンドに追加

```python
@app.command()
def custom_stats():
    """カスタム統計情報を表示"""
    # 実装
    pass
```

---

## 運用・監視

### 🔍 日常的な監視項目

#### 1. アラート状況確認

```bash
# アクティブアラート確認
exchange-analytics monitor alerts --active-only

# 高重要度アラート確認
exchange-analytics monitor alerts --severity high

# 統計情報確認
exchange-analytics monitor alerts --stats
```

#### 2. 設定確認

```bash
# 設定検証
exchange-analytics alert-config validate

# 設定表示
exchange-analytics alert-config show
```

#### 3. データベース監視

```sql
-- アラート統計
SELECT
    alert_type,
    severity,
    status,
    COUNT(*) as count
FROM alerts
GROUP BY alert_type, severity, status
ORDER BY alert_type, severity;

-- 最近のアラート
SELECT
    id,
    alert_type,
    severity,
    message,
    created_at
FROM alerts
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;
```

### 📈 パフォーマンス監視

#### 1. インデックス使用状況

```sql
-- インデックス使用状況確認
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE tablename = 'alerts';
```

#### 2. テーブルサイズ監視

```sql
-- テーブルサイズ確認
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE tablename = 'alerts';
```

### 🔄 定期メンテナンス

#### 1. 古いアラートの削除

```sql
-- 解決済みアラートの削除（30日以上前）
DELETE FROM alerts
WHERE status = 'resolved'
AND resolved_at < NOW() - INTERVAL '30 days';
```

#### 2. 統計情報の更新

```sql
-- 統計情報の更新
ANALYZE alerts;
```

---

## トラブルシューティング

### 🚨 よくある問題と解決方法

#### 1. 環境変数が読み込まれない

**症状**: `環境変数 XXX が見つかりません` エラー

**原因**: `.env`ファイルが読み込まれていない

**解決方法**:
```bash
# .envファイルの存在確認
ls -la .env

# 環境変数の確認
echo $DISCORD_WEBHOOK_URL

# python-dotenvのインストール確認
pip list | grep dotenv
```

#### 2. タイムスタンプがUTCで表示される

**症状**: CLIでタイムスタンプがUTC時間で表示される

**原因**: タイムゾーン変換が正しく行われていない

**解決方法**:
```python
# タイムゾーン情報の確認
print(f"Timezone info: {datetime_obj.tzinfo}")

# 手動でJSTに変換
import pytz
jst = pytz.timezone('Asia/Tokyo')
jst_time = datetime_obj.astimezone(jst)
```

#### 3. Discord通知が送信されない

**症状**: アラートは作成されるがDiscordに通知が届かない

**原因**: Webhook URLが無効または権限不足

**解決方法**:
```bash
# Webhook URLの確認
echo $DISCORD_WEBHOOK_URL

# 手動でWebhookテスト
curl -X POST -H "Content-Type: application/json" \
  -d '{"content":"Test message"}' \
  $DISCORD_WEBHOOK_URL
```

#### 4. データベース接続エラー

**症状**: `connection failed` エラー

**原因**: PostgreSQL接続設定の問題

**解決方法**:
```bash
# データベース接続確認
PGPASSWORD=exchange_password psql -h localhost -U exchange_analytics_user -d exchange_analytics_production_db

# テーブル存在確認
\dt alerts
```

### 🔧 デバッグ方法

#### 1. ログレベルの変更

```python
# ログレベルをDEBUGに変更
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

#### 2. 設定値の確認

```python
# 設定値の確認
from src.infrastructure.config.alert_config_manager import AlertConfigManager

config_manager = AlertConfigManager()
print(config_manager.get_discord_webhook_url('system_resource'))
```

#### 3. データベース直接確認

```sql
-- 最新のアラート確認
SELECT * FROM alerts ORDER BY created_at DESC LIMIT 5;

-- アラートタイプ別統計
SELECT alert_type, COUNT(*) FROM alerts GROUP BY alert_type;
```

---

## 今後の拡張計画

### 🚀 短期計画（1-2ヶ月）

#### 1. アラートエスカレーション機能
- 一定時間経過後の自動エスカレーション
- 重要度に応じた通知頻度の調整
- 管理者への自動通知

#### 2. アラート履歴・分析機能
- アラート発生パターンの分析
- 統計レポートの自動生成
- アラート効率性の測定

#### 3. Web UI の追加
- アラートダッシュボード
- リアルタイム監視画面
- 設定管理インターフェース

### 🌟 中期計画（3-6ヶ月）

#### 1. 機械学習による異常検出
- 異常パターンの自動学習
- 予測的アラート機能
- 誤報の自動フィルタリング

#### 2. マルチチャンネル通知
- Slack統合
- メール通知
- SMS通知
- プッシュ通知

#### 3. アラートルールエンジン
- 複雑な条件設定
- 動的ルール生成
- ルールの自動最適化

### 🎯 長期計画（6ヶ月以上）

#### 1. AI アシスタント機能
- 自然言語でのアラート設定
- 自動トラブルシューティング
- インテリジェントな推奨事項

#### 2. エンタープライズ機能
- マルチテナント対応
- SSO統合
- 監査ログ機能

#### 3. 外部システム統合
- Prometheus統合
- Grafana統合
- PagerDuty統合

---

## 📚 参考資料

### 🔗 関連ドキュメント
- [CLI機能説明書](./2025-08-15_CLI機能_ExchangeAnalyticsSystem_CLI機能説明書.md)
- [テクニカル指標統合設計書](./2025-08-13_テクニカル指標統合_TA-Libテクニカル指標統合設計書.md)
- [高度分析システム](./2025-08-15_分析システム_高度分析システム.md)

### 📖 技術スタック
- **データベース**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0
- **CLI**: Typer
- **設定管理**: Pydantic + YAML
- **通知**: Discord Webhook
- **タイムゾーン**: pytz

### 🛠️ 開発環境
- **Python**: 3.11+
- **依存関係管理**: pip
- **環境変数**: python-dotenv
- **ログ**: logging

---

## 📝 更新履歴

| 日付 | バージョン | 変更内容 | 担当者 |
|------|-----------|----------|--------|
| 2025-08-16 | 1.0.0 | 初版作成 | System |
| 2025-08-16 | 1.1.0 | タイムスタンプ修正 | System |
| 2025-08-16 | 1.2.0 | Discordチャンネル分離機能追加 | System |

---

**📧 お問い合わせ**: システム管理者
**📅 最終更新**: 2025-08-16
**🔄 バージョン**: 1.2.0
