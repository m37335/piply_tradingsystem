# investpy 経済カレンダーシステム 実装仕様書

## 1. システム概要

### 1.1 目的

- investpy ライブラリを使用して経済カレンダーデータを定期的に取得
- 重要な経済イベントを Discord に自動配信
- データの差分検出とアラート機能の提供
- **重要経済指標に対する ChatGPT によるドル円予測レポートの自動生成**

### 1.2 システム構成

```
investpy-economic-calendar/
├── src/
│   ├── domain/
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── economic_event/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── economic_event.py          # 経済イベントエンティティ（~200行）
│   │   │   │   ├── economic_event_validator.py # バリデーション（~150行）
│   │   │   │   └── economic_event_factory.py   # ファクトリ（~100行）
│   │   │   ├── calendar_data/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── calendar_data.py           # カレンダーデータエンティティ（~150行）
│   │   │   │   └── calendar_data_validator.py # バリデーション（~100行）
│   │   │   └── ai_report/
│   │   │       ├── __init__.py
│   │   │       ├── ai_report.py               # AIレポートエンティティ（~200行）
│   │   │       ├── usd_jpy_prediction.py      # ドル円予測データ（~150行）
│   │   │       └── ai_report_validator.py     # バリデーション（~100行）
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── economic_calendar/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── economic_calendar_repository.py      # インターフェース（~100行）
│   │   │   │   └── economic_calendar_repository_impl.py # 実装（~200行）
│   │   │   ├── notification/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── discord_notification_repository.py   # Discord通知（~150行）
│   │   │   │   └── notification_log_repository.py      # 通知ログ（~100行）
│   │   │   └── ai_report/
│   │   │       ├── __init__.py
│   │   │       ├── ai_report_repository.py              # AIレポート（~150行）
│   │   │       └── ai_report_repository_impl.py         # 実装（~200行）
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── investpy/
│   │       │   ├── __init__.py
│   │       │   ├── investpy_service.py                  # メインサービス（~200行）
│   │       │   ├── investpy_data_processor.py           # データ処理（~150行）
│   │       │   ├── investpy_timezone_handler.py         # タイムゾーン処理（~100行）
│   │       │   └── investpy_validator.py                # データ検証（~100行）
│   │       ├── notification/
│   │       │   ├── __init__.py
│   │       │   ├── notification_service.py              # メイン通知サービス（~200行）
│   │       │   ├── discord_message_builder.py           # Discordメッセージ作成（~150行）
│   │       │   ├── notification_rule_engine.py          # 通知ルールエンジン（~150行）
│   │       │   └── notification_cooldown_manager.py     # クールダウン管理（~100行）
│   │       ├── data_analysis/
│   │       │   ├── __init__.py
│   │       │   ├── data_analysis_service.py             # メイン分析サービス（~200行）
│   │       │   ├── forecast_change_detector.py          # 予測値変更検出（~150行）
│   │       │   ├── surprise_calculator.py               # サプライズ計算（~100行）
│   │       │   └── event_filter.py                      # イベントフィルタ（~100行）
│   │       └── ai_analysis/
│   │           ├── __init__.py
│   │           ├── ai_analysis_service.py               # メインAI分析サービス（~200行）
│   │           ├── openai_prompt_builder.py             # プロンプト作成（~150行）
│   │           ├── usd_jpy_prediction_parser.py         # 予測データ解析（~150行）
│   │           ├── confidence_score_calculator.py       # 信頼度計算（~100行）
│   │           └── ai_report_generator.py               # レポート生成（~150行）
│   ├── application/
│   │   ├── use_cases/
│   │   │   ├── __init__.py
│   │   │   ├── fetch/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── fetch_economic_calendar.py           # メイン取得ユースケース（~200行）
│   │   │   │   ├── fetch_today_events.py                # 当日取得（~150行）
│   │   │   │   └── fetch_weekly_events.py               # 週間取得（~150行）
│   │   │   ├── analysis/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detect_changes.py                    # 変更検出（~200行）
│   │   │   │   ├── analyze_forecast_changes.py          # 予測値変更分析（~150行）
│   │   │   │   └── calculate_surprises.py               # サプライズ計算（~150行）
│   │   │   ├── notification/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── send_notifications.py                # 通知送信（~200行）
│   │   │   │   ├── send_event_notifications.py          # イベント通知（~150行）
│   │   │   │   └── send_ai_report_notifications.py      # AIレポート通知（~150行）
│   │   │   └── ai_report/
│   │   │       ├── __init__.py
│   │   │       ├── generate_ai_report.py                # AIレポート生成（~200行）
│   │   │       ├── generate_pre_event_report.py         # 事前レポート（~150行）
│   │   │       ├── generate_post_event_report.py        # 事後レポート（~150行）
│   │   │       └── manage_ai_reports.py                 # レポート管理（~150行）
│   │   └── interfaces/
│   │       ├── __init__.py
│   │       └── schedulers/
│   │           ├── __init__.py
│   │           ├── base/
│   │           │   ├── __init__.py
│   │           │   ├── base_scheduler.py                # 基底スケジューラー（~150行）
│   │           │   └── scheduler_config.py              # スケジューラー設定（~100行）
│   │           ├── weekly/
│   │           │   ├── __init__.py
│   │           │   ├── weekly_scheduler.py              # 週次スケジューラー（~150行）
│   │           │   └── weekly_scheduler_config.py       # 週次設定（~100行）
│   │           ├── daily/
│   │           │   ├── __init__.py
│   │           │   ├── daily_scheduler.py               # 日次スケジューラー（~150行）
│   │           │   └── daily_scheduler_config.py        # 日次設定（~100行）
│   │           └── realtime/
│   │               ├── __init__.py
│   │               ├── realtime_scheduler.py            # リアルタイムスケジューラー（~150行）
│   │               └── realtime_scheduler_config.py     # リアルタイム設定（~100行）
│   ├── infrastructure/
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── models/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── economic_event/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── economic_event_model.py         # 経済イベントモデル（~200行）
│   │   │   │   │   └── economic_event_mapper.py        # マッパー（~100行）
│   │   │   │   ├── calendar_data/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── calendar_data_model.py          # カレンダーデータモデル（~150行）
│   │   │   │   │   └── calendar_data_mapper.py         # マッパー（~100行）
│   │   │   │   └── ai_report/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── ai_report_model.py              # AIレポートモデル（~200行）
│   │   │   │       └── ai_report_mapper.py             # マッパー（~100行）
│   │   │   ├── repositories/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── sql/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── sql_economic_calendar_repository.py    # SQL実装（~300行）
│   │   │   │   │   ├── sql_notification_log_repository.py     # 通知ログSQL（~200行）
│   │   │   │   │   └── sql_ai_report_repository.py            # AIレポートSQL（~250行）
│   │   │   │   └── cache/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── redis_cache_manager.py                 # Redisキャッシュ（~200行）
│   │   │   │       └── memory_cache_manager.py                # メモリキャッシュ（~150行）
│   │   │   └── migrations/
│   │   │       └── versions/
│   │   ├── external/
│   │   │   ├── __init__.py
│   │   │   ├── investpy/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── investpy_client.py                        # investpyクライアント（~200行）
│   │   │   │   ├── investpy_error_handler.py                 # エラーハンドラー（~150行）
│   │   │   │   └── investpy_rate_limiter.py                  # レート制限（~100行）
│   │   │   ├── discord/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── discord_client.py                         # Discordクライアント（~200行）
│   │   │   │   ├── discord_embed_builder.py                  # 埋め込み作成（~150行）
│   │   │   │   └── discord_error_handler.py                  # エラーハンドラー（~100行）
│   │   │   └── openai/
│   │   │       ├── __init__.py
│   │   │       ├── openai_client.py                          # OpenAIクライアント（~200行）
│   │   │       ├── openai_prompt_manager.py                  # プロンプト管理（~150行）
│   │   │       └── openai_error_handler.py                   # エラーハンドラー（~100行）
│   │   └── config/
│   │       ├── __init__.py
│   │       ├── database/
│   │       │   ├── __init__.py
│   │       │   ├── database_config.py                        # データベース設定（~150行）
│   │       │   └── connection_manager.py                     # 接続管理（~100行）
│   │       ├── investpy/
│   │       │   ├── __init__.py
│   │       │   ├── investpy_config.py                        # investpy設定（~150行）
│   │       │   └── timezone_config.py                        # タイムゾーン設定（~100行）
│   │       ├── notification/
│   │       │   ├── __init__.py
│   │       │   ├── notification_config.py                    # 通知設定（~150行）
│   │       │   └── discord_config.py                         # Discord設定（~100行）
│   │       └── ai_analysis/
│   │           ├── __init__.py
│   │           ├── ai_analysis_config.py                     # AI分析設定（~150行）
│   │           └── openai_config.py                          # OpenAI設定（~100行）
│   └── utils/
│       ├── __init__.py
│       ├── timezone/
│       │   ├── __init__.py
│       │   ├── timezone_utils.py                             # タイムゾーン処理（~150行）
│       │   └── timezone_converter.py                         # 変換処理（~100行）
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── data_validator.py                             # データ検証（~200行）
│       │   ├── schema_validator.py                           # スキーマ検証（~150行）
│       │   └── business_rule_validator.py                    # ビジネスルール検証（~150行）
│       ├── logging/
│       │   ├── __init__.py
│       │   ├── logging_utils.py                              # ログ処理（~200行）
│       │   ├── log_formatter.py                              # ログフォーマッター（~100行）
│       │   └── log_rotator.py                                # ログローテーション（~100行）
│       └── common/
│           ├── __init__.py
│           ├── constants.py                                  # 定数定義（~100行）
│           ├── exceptions.py                                 # 例外定義（~150行）
│           └── decorators.py                                 # デコレーター（~100行）
├── config/
│   ├── investpy_calendar.yaml         # investpy設定
│   ├── notification_rules.yaml        # 通知ルール設定
│   └── crontab/
│       └── production/
│           ├── weekly_schedule.cron
│           ├── daily_schedule.cron
│           └── realtime_schedule.cron
├── data/
│   ├── economic_calendar/             # 取得データ保存
│   │   ├── raw/
│   │   ├── processed/
│   │   └── archive/
│   ├── ai_reports/                    # AI分析レポート保存
│   │   ├── generated/
│   │   ├── templates/
│   │   └── archive/
│   └── logs/
│       ├── fetch_logs/
│       ├── notification_logs/
│       └── error_logs/
├── scripts/
│   ├── setup_database.py
│   ├── test_investpy_connection.py
│   └── deploy_crontab.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/
│   ├── api_documentation.md
│   ├── deployment_guide.md
│   └── troubleshooting.md
└── requirements/
    ├── base.txt
    ├── investpy_calendar.txt          # 新規追加
    └── production.txt
```

## 2. 技術仕様

### 2.1 依存関係

#### 2.1.1 新規追加ライブラリ

```txt
# requirements/investpy_calendar.txt
investpy==1.0.8
pytz==2023.3
python-dateutil==2.8.2
schedule==1.2.0

# Linting & Code Quality
flake8==6.1.0
black==23.11.0
isort==5.12.0
mypy==1.7.1
pylint==3.0.3

# Type Checking
types-pytz==2023.3.1
types-requests==2.31.0.10
```

#### 2.1.2 既存ライブラリ（確認済み）

- pandas==2.1.4
- discord-webhook==1.3.0
- APScheduler==3.10.4
- SQLAlchemy==2.0.23
- python-dotenv==1.0.0

### 2.2 データベース設計

#### 2.2.1 economic_events テーブル

```sql
CREATE TABLE economic_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,  -- investpy固有ID
    date_utc TIMESTAMP NOT NULL,
    time_utc TIME,
    country VARCHAR(100) NOT NULL,
    zone VARCHAR(100),
    event_name TEXT NOT NULL,
    importance VARCHAR(20) NOT NULL,  -- 'low', 'medium', 'high'
    actual_value DECIMAL(15,6),
    forecast_value DECIMAL(15,6),
    previous_value DECIMAL(15,6),
    currency VARCHAR(10),
    unit VARCHAR(50),
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_date_country (date_utc, country),
    INDEX idx_importance (importance),
    INDEX idx_event_id (event_id)
);
```

#### 2.2.2 calendar_fetch_logs テーブル

```sql
CREATE TABLE calendar_fetch_logs (
    id SERIAL PRIMARY KEY,
    fetch_type VARCHAR(50) NOT NULL,  -- 'weekly', 'daily', 'realtime'
    fetch_start TIMESTAMP NOT NULL,
    fetch_end TIMESTAMP,
    records_fetched INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_new INTEGER DEFAULT 0,
    status VARCHAR(20) NOT NULL,  -- 'success', 'partial', 'failed'
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.2.3 notification_logs テーブル

#### 2.2.4 ai_reports テーブル

```sql
CREATE TABLE ai_reports (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES economic_events(id),
    report_type VARCHAR(50) NOT NULL,  -- 'pre_event', 'post_event', 'forecast_change'
    report_content TEXT NOT NULL,
    usd_jpy_prediction JSONB,  -- 予測データ（方向性、強度、理由等）
    confidence_score DECIMAL(3,2),  -- 信頼度スコア（0.00-1.00）
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_event_id (event_id),
    INDEX idx_report_type (report_type),
    INDEX idx_generated_at (generated_at)
);
```

```sql
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES economic_events(id),
    notification_type VARCHAR(50) NOT NULL,  -- 'new_event', 'forecast_change', 'actual_announcement'
    discord_message_id VARCHAR(255),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- 'sent', 'failed'
    error_message TEXT
);
```

### 2.3 設定ファイル

#### 2.3.1 config/investpy_calendar.yaml

````yaml
investpy:
  default_timezone: "GMT +9:00"
  time_filter: "time_only"
  default_countries:
    - "japan"
    - "united states"
    - "euro zone"
    - "united kingdom"
    - "australia"
    - "canada"
  default_importances:
    - "high"
    - "medium"
  retry_attempts: 3
  retry_delay: 5

scheduling:
  weekly:
    day: "sunday"
    time: "09:00"
    timezone: "Asia/Tokyo"
  daily:
    time: "07:00"
    timezone: "Asia/Tokyo"
  realtime:
    check_interval: 30 # minutes
    pre_announcement: 60 # minutes before event
    post_announcement: 15 # minutes after event

notification:
  discord:
    webhook_url: "${DISCORD_WEBHOOK_URL}"
    username: "Economic Calendar Bot"
    avatar_url: ""
    cooldown_period: 3600 # seconds
  rules:
    importance_threshold: "medium"
    countries_filter:
      - "japan"
      - "united states"
      - "euro zone"
      - "united kingdom"
      - "australia"
      - "canada"
    categories_filter:
      - "inflation"
      - "employment"
      - "interest_rate"
      - "gdp"
    forecast_change_threshold: 0.1 # 10% change

  ai_analysis:
    openai:
      model: "gpt-4"
      max_tokens: 2000
      temperature: 0.3
      api_key: "${OPENAI_API_KEY}"
    report_generation:
      pre_event_hours: 24  # イベント前24時間
      post_event_hours: 2   # イベント後2時間
      importance_threshold: "high"  # 高重要度のみ
      target_events:
        - "Consumer Price Index (CPI)"
        - "Gross Domestic Product (GDP)"
        - "Employment Report"
        - "Interest Rate Decision"
        - "Bank of Japan Policy Rate"
        - "Federal Reserve Interest Rate Decision"
        - "ECB Interest Rate Decision"
        - "Bank of England Interest Rate Decision"
        - "Non-Farm Payrolls"
        - "Eurozone CPI"
        - "UK CPI"
  usd_jpy_analysis:
    timeframe: "1-4 hours"  # 予測時間枠
    confidence_threshold: 0.7  # 信頼度閾値
    include_technical_analysis: true
    include_fundamental_analysis: true

#### 2.3.2 config/notification_rules.yaml

```yaml
notification_patterns:
  new_high_importance_event:
    enabled: true
          conditions:
        importance: "high"
        countries: ["japan", "united states", "euro zone"]
            message_template: "🚨 重要経済指標: {country} - {event_name} ({date} {time})"

  forecast_change:
    enabled: true
    conditions:
      change_threshold: 0.1
      importance: ["high", "medium"]
    message_template: "📊 予測値変更: {country} - {event_name} 予測: {old_forecast} → {new_forecast}"

  actual_announcement:
    enabled: true
    conditions:
      importance: ["high", "medium"]
    message_template: "📈 発表: {country} - {event_name} 実際: {actual} (予測: {forecast})"

  surprise_alert:
    enabled: true
    conditions:
      surprise_threshold: 0.2
      importance: "high"
    message_template: "⚠️ サプライズ: {country} - {event_name} 予測差: {surprise_percentage}%"

  ai_report_alert:
    enabled: true
    conditions:
      importance: "high"
      event_types: ["CPI", "GDP", "Employment", "Interest Rate"]
    message_template: "🤖 AI分析: {country} - {event_name} ドル円予測レポート生成完了"
    include_report_summary: true

message_formatting:
  embed_color:
    high_importance: 0xFF0000
    medium_importance: 0xFFA500
    low_importance: 0x00FF00
  timezone_display: "Asia/Tokyo"
  date_format: "%Y-%m-%d %H:%M"
````

## 3. 実装仕様

### 3.1 コアサービス

#### 3.1.1 InvestpyService（メインサービス）

```python
class InvestpyService:
    def __init__(
        self,
        config: InvestpyConfig,
        data_processor: InvestpyDataProcessor,
        timezone_handler: InvestpyTimezoneHandler,
        validator: InvestpyValidator
    ):
        self.config = config
        self.data_processor = data_processor
        self.timezone_handler = timezone_handler
        self.validator = validator

    async def fetch_economic_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        countries: Optional[List[str]] = None,
        importances: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """経済カレンダーデータを取得（~50行）"""

    async def fetch_today_events(self) -> pd.DataFrame:
        """当日のイベントを取得（~30行）"""

    async def fetch_weekly_events(self, start_date: str) -> pd.DataFrame:
        """週間イベントを取得（~40行）"""
```

#### 3.1.2 InvestpyDataProcessor（データ処理）

```python
class InvestpyDataProcessor:
    def __init__(self, config: InvestpyConfig):
        self.config = config

    def process_raw_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """生データの処理（~80行）"""

    def filter_by_criteria(
        self,
        df: pd.DataFrame,
        countries: List[str],
        importances: List[str]
    ) -> pd.DataFrame:
        """条件によるフィルタリング（~60行）"""

    def enrich_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """データの拡張（~70行）"""
```

#### 3.1.3 InvestpyTimezoneHandler（タイムゾーン処理）

```python
class InvestpyTimezoneHandler:
    def __init__(self, config: InvestpyConfig):
        self.config = config

    def convert_to_utc(self, df: pd.DataFrame) -> pd.DataFrame:
        """UTC変換（~50行）"""

    def convert_to_jst(self, df: pd.DataFrame) -> pd.DataFrame:
        """JST変換（~50行）"""

    def handle_dst(self, df: pd.DataFrame) -> pd.DataFrame:
        """夏時間処理（~40行）"""
```

#### 3.1.2 NotificationService

```python
class NotificationService:
    def __init__(self, discord_client: DiscordClient, rules: NotificationRules):
        self.discord_client = discord_client
        self.rules = rules

    async def send_event_notification(self, event: EconomicEvent) -> bool:
        """イベント通知を送信"""

    async def send_forecast_change_notification(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent
    ) -> bool:
        """予測値変更通知を送信"""

    async def send_actual_announcement_notification(self, event: EconomicEvent) -> bool:
        """実際値発表通知を送信"""

    def _create_discord_embed(self, event: EconomicEvent) -> discord.Embed:
        """Discord埋め込みメッセージ作成"""

    def _should_send_notification(self, event: EconomicEvent) -> bool:
        """通知判定ロジック"""
```

#### 3.1.3 DataAnalysisService

```python
class DataAnalysisService:
    def __init__(self):
        pass

    def detect_forecast_changes(
        self,
        old_data: pd.DataFrame,
        new_data: pd.DataFrame
    ) -> List[ForecastChange]:
        """予測値変更を検出"""

    def calculate_surprise(
        self,
        actual: float,
        forecast: float
    ) -> float:
        """サプライズ計算"""

    def filter_important_events(
        self,
        data: pd.DataFrame,
        rules: NotificationRules
    ) -> pd.DataFrame:
        """重要イベントフィルタリング"""
```

#### 3.1.4 AIAnalysisService（メイン AI 分析サービス）

```python
class AIAnalysisService:
    def __init__(
        self,
        openai_client: OpenAIClient,
        config: AIAnalysisConfig,
        prompt_builder: OpenAIPromptBuilder,
        prediction_parser: USDJPYPredictionParser,
        confidence_calculator: ConfidenceScoreCalculator,
        report_generator: AIReportGenerator
    ):
        self.openai_client = openai_client
        self.config = config
        self.prompt_builder = prompt_builder
        self.prediction_parser = prediction_parser
        self.confidence_calculator = confidence_calculator
        self.report_generator = report_generator

    async def generate_pre_event_report(self, event: EconomicEvent) -> AIReport:
        """イベント前のドル円予測レポート生成（~60行）"""

    async def generate_post_event_report(self, event: EconomicEvent) -> AIReport:
        """イベント後のドル円分析レポート生成（~70行）"""

    async def generate_forecast_change_report(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent
    ) -> AIReport:
        """予測値変更時のドル円影響分析レポート生成（~80行）"""
```

#### 3.1.5 OpenAIPromptBuilder（プロンプト作成）

```python
class OpenAIPromptBuilder:
    def __init__(self, config: AIAnalysisConfig):
        self.config = config

    def build_pre_event_prompt(self, event: EconomicEvent) -> str:
        """事前レポート用プロンプト作成（~80行）"""

    def build_post_event_prompt(self, event: EconomicEvent) -> str:
        """事後レポート用プロンプト作成（~90行）"""

    def build_forecast_change_prompt(
        self,
        old_event: EconomicEvent,
        new_event: EconomicEvent
    ) -> str:
        """予測値変更用プロンプト作成（~100行）"""
```

#### 3.1.6 USDJPYPredictionParser（予測データ解析）

```python
class USDJPYPredictionParser:
    def __init__(self):
        pass

    def parse_prediction_data(self, ai_response: str) -> Dict[str, Any]:
        """AI応答からドル円予測データを解析（~120行）"""

    def extract_direction(self, text: str) -> str:
        """方向性の抽出（~40行）"""

    def extract_strength(self, text: str) -> float:
        """強度の抽出（~50行）"""

    def extract_reasons(self, text: str) -> List[str]:
        """理由の抽出（~60行）"""
```

### 3.2 スケジューラー

#### 3.2.1 BaseScheduler（基底スケジューラー）

```python
class BaseScheduler:
    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self) -> bool:
        """スケジューラー実行（~50行）"""

    def _handle_error(self, error: Exception) -> None:
        """エラーハンドリング（~40行）"""

    def _log_execution(self, success: bool, duration: float) -> None:
        """実行ログ記録（~30行）"""
```

#### 3.2.2 WeeklyScheduler（週次スケジューラー）

```python
class WeeklyScheduler(BaseScheduler):
    def __init__(
        self,
        config: WeeklySchedulerConfig,
        use_case: FetchEconomicCalendarUseCase
    ):
        super().__init__(config)
        self.use_case = use_case

    async def execute_weekly_fetch(self) -> bool:
        """週次データ取得実行（~60行）"""

    def _get_next_week_start(self) -> str:
        """翌週開始日取得（~30行）"""

    def _get_next_week_end(self) -> str:
        """翌週終了日取得（~30行）"""
```

#### 3.2.2 DailyScheduler

```python
class DailyScheduler:
    def __init__(self, use_case: FetchEconomicCalendarUseCase):
        self.use_case = use_case

    async def execute_daily_fetch(self):
        """日次データ取得実行"""
        # 毎朝 07:00 JST に当日分を再取得
        today = datetime.now().strftime("%d/%m/%Y")

        await self.use_case.execute(
            from_date=today,
            to_date=today,
            fetch_type="daily"
        )
```

#### 3.2.3 RealtimeScheduler

```python
class RealtimeScheduler:
    def __init__(self, use_case: DetectChangesUseCase):
        self.use_case = use_case

    async def execute_realtime_check(self):
        """リアルタイムチェック実行"""
        # 30分間隔で重要イベントの直前・直後をチェック
        await self.use_case.execute_realtime_monitoring()
```

### 3.3 crontab 設定

#### 3.3.1 config/crontab/production/weekly_schedule.cron

```bash
# 週次データ取得（日曜 09:00 JST）
0 9 * * 0 cd /app && python -m src.application.interfaces.schedulers.weekly_scheduler >> /app/data/logs/fetch_logs/weekly.log 2>&1
```

#### 3.3.2 config/crontab/production/daily_schedule.cron

```bash
# 日次データ取得（毎朝 07:00 JST）
0 7 * * * cd /app && python -m src.application.interfaces.schedulers.daily_scheduler >> /app/data/logs/fetch_logs/daily.log 2>&1
```

#### 3.3.3 config/crontab/production/realtime_schedule.cron

```bash
# リアルタイムチェック（30分間隔）
*/30 * * * * cd /app && python -m src.application.interfaces.schedulers.realtime_scheduler >> /app/data/logs/fetch_logs/realtime.log 2>&1
```

## 4. デプロイメント仕様

### 4.1 Docker 設定

#### 4.1.1 Dockerfile.investpy

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# システム依存関係のインストール
RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係のインストール
COPY requirements/investpy_calendar.txt .
RUN pip install -r investpy_calendar.txt

# アプリケーションコードのコピー
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/

# ログディレクトリの作成
RUN mkdir -p /app/data/logs/fetch_logs \
    /app/data/logs/notification_logs \
    /app/data/logs/error_logs

# crontab設定
COPY config/crontab/production/*.cron /etc/cron.d/
RUN chmod 0644 /etc/cron.d/*.cron

# 起動スクリプト
COPY scripts/start_investpy_service.sh /app/
RUN chmod +x /app/start_investpy_service.sh

EXPOSE 8000

CMD ["/app/start_investpy_service.sh"]
```

#### 4.1.2 scripts/start_investpy_service.sh

```bash
#!/bin/bash

# cronサービス開始
service cron start

# データベースマイグレーション
python scripts/setup_database.py

# アプリケーション開始
python -m src.application.main
```

### 4.2 環境変数設定

#### 4.2.1 .env.investpy

```env
# データベース設定
DATABASE_URL=postgresql://user:password@localhost:5432/economic_calendar

# Discord設定
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# OpenAI設定
OPENAI_API_KEY=your_openai_api_key_here

# Investpy設定
INVESTPY_DEFAULT_TIMEZONE=GMT +9:00
INVESTPY_DEFAULT_COUNTRIES=japan,united states,euro zone,united kingdom,australia,canada

# 通知設定
NOTIFICATION_COOLDOWN=3600
NOTIFICATION_IMPORTANCE_THRESHOLD=medium

# AI分析設定
AI_REPORT_ENABLED=true
AI_CONFIDENCE_THRESHOLD=0.7

# ログ設定
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/data/logs
```

## 5. テスト仕様

### 5.1 単体テスト

- **エンティティテスト**

  - EconomicEvent のバリデーション
  - AIReport の生成・検証
  - USDJPYPrediction の解析

- **サービステスト**

  - InvestpyService の各メソッド
  - NotificationService の通知ロジック
  - DataAnalysisService の分析機能
  - AIAnalysisService のレポート生成機能

- **リポジトリテスト**

  - データベースリポジトリの CRUD 操作
  - キャッシュ機能の動作確認

- **ユーティリティテスト**
  - タイムゾーン変換処理
  - データ検証ロジック
  - ログ処理機能

### 5.2 統合テスト

- スケジューラーとユースケースの連携
- Discord 通知の送信テスト
- OpenAI API との連携テスト
- データベースとの連携テスト

### 5.3 E2E テスト

- 週次・日次・リアルタイムスケジュールの実行
- エラー発生時の復旧処理
- 長時間実行時の安定性

## 6. 監視・ログ仕様

### 6.1 ログ出力

- データ取得ログ（成功・失敗・件数）
- 通知送信ログ（送信先・内容・結果）
- AI 分析ログ（レポート生成・API 呼び出し・信頼度スコア）
- エラーログ（詳細なスタックトレース）
- パフォーマンスログ（実行時間・メモリ使用量）

### 6.2 監視項目

- データ取得成功率
- 通知送信成功率
- AI 分析成功率・信頼度スコア
- OpenAI API 使用量・コスト
- システムリソース使用量
- データベース接続状態

### 6.3 アラート設定

- データ取得失敗時の即座通知
- 通知送信失敗時の管理者通知
- AI 分析失敗・低信頼度時の警告
- OpenAI API 制限・エラー時の通知
- システムリソース不足時の警告

## 7. セキュリティ仕様

### 7.1 認証・認可

- Discord Webhook URL の環境変数管理
- OpenAI API キーの安全な管理
- データベース接続情報の暗号化
- API キーの安全な管理

### 7.2 データ保護

- 個人情報の取り扱い制限
- ログファイルの適切な権限設定
- バックアップデータの暗号化

## 8. 運用・保守仕様

### 8.1 定期メンテナンス

- ログファイルのローテーション
- 古いデータのアーカイブ
- データベースの最適化

### 8.2 障害対応

- 自動復旧機能の実装
- 手動復旧手順の整備
- 緊急連絡体制の確立

### 8.3 パフォーマンス最適化

- データベースクエリの最適化
- キャッシュ機能の実装
- 非同期処理の活用

## 9. 開発・デプロイフロー

### 9.1 開発環境

1. **ローカル環境での investpy 接続テスト**
2. **モックデータを使用した通知機能テスト**
3. **データベースマイグレーションの検証**
4. **Linter・フォーマッターの設定確認**

### 9.2 ステージング環境

1. **本番に近い環境での統合テスト**
2. **スケジューラーの動作確認**
3. **Discord 通知の実機テスト**
4. **AI 分析機能の精度検証**

### 9.3 本番環境

1. **段階的な機能リリース**
2. **監視・アラートの設定**
3. **運用ドキュメントの整備**
4. **パフォーマンス監視の設定**

## 12. コード品質管理

### 12.1 Linting・フォーマティング

- **Black**: コードフォーマット統一
- **isort**: import 文の整理
- **flake8**: コードスタイルチェック
- **mypy**: 型チェック
- **pylint**: コード品質分析

### 12.2 ファイルサイズ制約

- **最大行数**: 400 行（推奨 300 行以下）
- **クラス最大行数**: 200 行
- **メソッド最大行数**: 50 行
- **関数最大行数**: 30 行

### 12.3 コードレビュー基準

- **単一責任原則**: 1 つのクラス・メソッドは 1 つの責任のみ
- **依存性注入**: 外部依存はコンストラクタで注入
- **エラーハンドリング**: 適切な例外処理
- **ログ出力**: 重要な処理のログ記録
- **型ヒント**: 全メソッド・関数に型ヒント付与

## 10. 今後の拡張計画

### 10.1 機能拡張

- 他の経済データソースとの統合
- 機械学習による重要度予測
- カスタム通知ルールの設定機能
- **AI 予測精度の向上（過去データ学習）**
- **複数通貨ペアへの拡張（EUR/JPY、GBP/JPY 等）**
- **テクニカル分析との統合**

### 10.2 パフォーマンス向上

- 分散処理による大規模データ処理
- リアルタイムストリーミング対応
- モバイルアプリ連携

### 10.3 運用改善

- ダッシュボード機能の追加
- 自動化された障害検知・復旧
- 多言語対応
