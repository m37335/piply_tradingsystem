# 🗄️ データベース実装・5 分おきデータ取得システム設計書

## 📋 プロジェクト概要

### 🎯 **目的**

- **USD/JPY 特化**の 5 分おきデータ取得システム
- **API 呼び出し最小化**によるコスト削減
- **既存通知システム**との完全統合
- **テクニカル指標**の自動計算・保存

### 📊 **設計方針**

- **通貨ペア**: USD/JPY のみ（API 呼び出し削減）
- **取得間隔**: 5 分間隔（288 回/日）
- **データ保存**: リアルタイム DB 保存
- **通知連携**: 既存 6 パターン検出システムと統合

## 🏗️ システムアーキテクチャ

### 📈 **データフロー**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Yahoo Finance │───►│   Data Fetcher  │───►│   Database      │
│   API (USD/JPY) │    │   (5分間隔)     │    │   (SQLite/PostgreSQL) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │ Technical       │
                       │ Indicators      │
                       │ Calculator      │
                       └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │ Pattern         │───►│ Discord         │
                       │ Detector        │    │ Notification    │
                       │ (6パターン)     │    │ System          │
                       └─────────────────┘    └─────────────────┘
```

### 🔄 **実行サイクル**

```
1. 5分間隔データ取得
   ↓
2. データベース保存
   ↓
3. テクニカル指標計算
   ↓
4. パターン検出実行
   ↓
5. 通知判定・送信
   ↓
6. 履歴管理
```

## 🗄️ データベース設計

### 📊 **テーブル構成**

#### 1. **価格データテーブル** (`price_data`)

```sql
CREATE TABLE price_data (
    id BIGSERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL DEFAULT 'USD/JPY',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open_price DECIMAL(10,5) NOT NULL,
    high_price DECIMAL(10,5) NOT NULL,
    low_price DECIMAL(10,5) NOT NULL,
    close_price DECIMAL(10,5) NOT NULL,
    volume BIGINT,
    data_source VARCHAR(50) DEFAULT 'Yahoo Finance',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- インデックス
    CONSTRAINT idx_price_data_currency_timestamp UNIQUE (currency_pair, timestamp),
    INDEX idx_price_data_timestamp (timestamp),
    INDEX idx_price_data_currency (currency_pair)
);

-- パーティション化（月別）
CREATE TABLE price_data_2025_01 PARTITION OF price_data
FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE price_data_2025_02 PARTITION OF price_data
FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');
```

#### 2. **テクニカル指標テーブル** (`technical_indicators`)

```sql
CREATE TABLE technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL DEFAULT 'USD/JPY',
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,  -- RSI, MACD, BB, SMA, EMA
    timeframe VARCHAR(10) NOT NULL,       -- M5, M15, H1, H4, D1
    value DECIMAL(15,8) NOT NULL,
    additional_data JSONB,                -- MACD histogram, BB bands等
    parameters JSONB,                     -- 計算パラメータ（期間等）
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- インデックス
    CONSTRAINT idx_tech_indicators_unique UNIQUE (currency_pair, timestamp, indicator_type, timeframe),
    INDEX idx_tech_indicators_timestamp (timestamp),
    INDEX idx_tech_indicators_type (indicator_type),
    INDEX idx_tech_indicators_timeframe (timeframe)
);
```

#### 3. **パターン検出結果テーブル** (`pattern_detections`)

```sql
CREATE TABLE pattern_detections (
    id BIGSERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL DEFAULT 'USD/JPY',
    pattern_number INTEGER NOT NULL,      -- 1-6
    pattern_name VARCHAR(100) NOT NULL,
    priority INTEGER NOT NULL,            -- 10-100
    confidence_score DECIMAL(3,2) NOT NULL, -- 0.00-1.00
    detection_time TIMESTAMP WITH TIME ZONE NOT NULL,
    notification_title VARCHAR(200),
    notification_color VARCHAR(10),
    strategy TEXT,
    entry_condition TEXT,
    take_profit VARCHAR(50),
    stop_loss VARCHAR(50),
    description TEXT,
    conditions_met JSONB,                 -- 各時間軸の条件達成状況
    technical_data JSONB,                 -- 検出時のテクニカルデータ
    notification_sent BOOLEAN DEFAULT FALSE,
    discord_message_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- インデックス
    INDEX idx_pattern_detections_time (detection_time),
    INDEX idx_pattern_detections_pattern (pattern_number),
    INDEX idx_pattern_detections_priority (priority),
    INDEX idx_pattern_detections_notification (notification_sent)
);
```

#### 4. **データ取得履歴テーブル** (`data_fetch_history`)

```sql
CREATE TABLE data_fetch_history (
    id BIGSERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL DEFAULT 'USD/JPY',
    fetch_time TIMESTAMP WITH TIME ZONE NOT NULL,
    data_source VARCHAR(50) NOT NULL,
    success BOOLEAN NOT NULL,
    response_time_ms INTEGER,
    data_count INTEGER,                   -- 取得データ数
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- インデックス
    INDEX idx_fetch_history_time (fetch_time),
    INDEX idx_fetch_history_success (success),
    INDEX idx_fetch_history_source (data_source)
);
```

#### 5. **システム設定テーブル** (`system_config`)

```sql
CREATE TABLE system_config (
    id BIGSERIAL PRIMARY KEY,
    config_key VARCHAR(100) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) NOT NULL,     -- string, integer, float, boolean, json
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 初期設定データ
INSERT INTO system_config (config_key, config_value, config_type, description) VALUES
('data_fetch_interval_minutes', '5', 'integer', 'データ取得間隔（分）'),
('currency_pairs', '["USD/JPY"]', 'json', '取得対象通貨ペア'),
('yahoo_finance_retry_count', '3', 'integer', 'Yahoo Finance API リトライ回数'),
('yahoo_finance_retry_delay', '2.0', 'float', 'リトライ間隔（秒）'),
('technical_indicators_enabled', 'true', 'boolean', 'テクニカル指標計算有効化'),
('pattern_detection_enabled', 'true', 'boolean', 'パターン検出有効化'),
('notification_enabled', 'true', 'boolean', '通知機能有効化'),
('data_retention_days', '90', 'integer', 'データ保持期間（日）');
```

### 🔧 **データベース管理**

#### パーティション戦略

```sql
-- 月別パーティション作成スクリプト
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name TEXT, year_month TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('
        CREATE TABLE IF NOT EXISTS %I_%s PARTITION OF %I
        FOR VALUES FROM (%L) TO (%L)
    ',
    table_name, year_month, table_name,
    year_month || '-01',
    (year_month || '-01')::date + INTERVAL '1 month'
    );
END;
$$ LANGUAGE plpgsql;

-- 自動パーティション作成（月次実行）
SELECT create_monthly_partition('price_data', '2025_01');
SELECT create_monthly_partition('price_data', '2025_02');
```

#### データクリーンアップ

```sql
-- 古いデータ削除（90日以上前）
DELETE FROM price_data
WHERE timestamp < NOW() - INTERVAL '90 days';

DELETE FROM technical_indicators
WHERE timestamp < NOW() - INTERVAL '90 days';

DELETE FROM pattern_detections
WHERE detection_time < NOW() - INTERVAL '90 days';

DELETE FROM data_fetch_history
WHERE fetch_time < NOW() - INTERVAL '30 days';
```

## 🔄 データ取得システム

### 📡 **Yahoo Finance データ取得**

#### データ取得クラス

```python
class USDJPYDataFetcher:
    """USD/JPY特化データ取得クラス"""

    def __init__(self):
        self.currency_pair = "USD/JPY"
        self.yahoo_symbol = "USDJPY=X"
        self.fetch_interval = 300  # 5分間隔
        self.retry_count = 3
        self.retry_delay = 2.0

    async def fetch_current_data(self) -> Optional[Dict[str, Any]]:
        """現在のUSD/JPYデータを取得"""
        try:
            ticker = yf.Ticker(self.yahoo_symbol)
            info = ticker.info

            if not info or "regularMarketPrice" not in info:
                return None

            return {
                "currency_pair": self.currency_pair,
                "timestamp": datetime.now(timezone.utc),
                "open_price": info.get("open", 0),
                "high_price": info.get("dayHigh", 0),
                "low_price": info.get("dayLow", 0),
                "close_price": info.get("regularMarketPrice", 0),
                "volume": info.get("volume", 0),
                "data_source": "Yahoo Finance"
            }

        except Exception as e:
            logger.error(f"USD/JPYデータ取得エラー: {e}")
            return None
```

#### 履歴データ取得

```python
async def fetch_historical_data(
    self,
    period: str = "5d",
    interval: str = "5m"
) -> Optional[pd.DataFrame]:
    """履歴データ取得（テクニカル指標計算用）"""
    try:
        ticker = yf.Ticker(self.yahoo_symbol)
        hist = ticker.history(period=period, interval=interval)

        if hist.empty:
            return None

        # データ正規化
        hist = hist.reset_index()
        hist['currency_pair'] = self.currency_pair
        hist['data_source'] = "Yahoo Finance"

        return hist

    except Exception as e:
        logger.error(f"履歴データ取得エラー: {e}")
        return None
```

### 🧮 **テクニカル指標計算**

#### 指標計算クラス

```python
class TechnicalIndicatorCalculator:
    """テクニカル指標計算クラス"""

    def __init__(self):
        self.indicators = {
            'RSI': self.calculate_rsi,
            'MACD': self.calculate_macd,
            'BB': self.calculate_bollinger_bands,
            'SMA': self.calculate_sma,
            'EMA': self.calculate_ema
        }

    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """RSI計算"""
        if len(prices) < period + 1:
            return None

        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def calculate_macd(
        self,
        prices: List[float],
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Dict[str, float]:
        """MACD計算"""
        if len(prices) < slow + signal:
            return None

        ema_fast = self.calculate_ema(prices, fast)
        ema_slow = self.calculate_ema(prices, slow)

        macd_line = ema_fast - ema_slow
        signal_line = self.calculate_ema([macd_line], signal)
        histogram = macd_line - signal_line

        return {
            "macd_line": round(macd_line, 6),
            "signal_line": round(signal_line, 6),
            "histogram": round(histogram, 6)
        }

    def calculate_bollinger_bands(
        self,
        prices: List[float],
        period: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, float]:
        """ボリンジャーバンド計算"""
        if len(prices) < period:
            return None

        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])

        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)

        return {
            "upper_band": round(upper_band, 5),
            "middle_band": round(sma, 5),
            "lower_band": round(lower_band, 5)
        }
```

### 🔄 **データ取得スケジューラー**

#### メインスケジューラー

```python
class USDJPYDataScheduler:
    """USD/JPYデータ取得スケジューラー"""

    def __init__(self):
        self.fetcher = USDJPYDataFetcher()
        self.calculator = TechnicalIndicatorCalculator()
        self.db_manager = DatabaseManager()
        self.pattern_analyzer = NotificationPatternAnalyzer()

        # 設定
        self.fetch_interval = 300  # 5分間隔
        self.currency_pair = "USD/JPY"

    async def start_scheduler(self):
        """スケジューラー開始"""
        logger.info("USD/JPYデータ取得スケジューラー開始")

        while True:
            try:
                await self.fetch_and_process_data()
                await asyncio.sleep(self.fetch_interval)

            except KeyboardInterrupt:
                logger.info("スケジューラー停止")
                break
            except Exception as e:
                logger.error(f"スケジューラーエラー: {e}")
                await asyncio.sleep(60)  # エラー時は1分待機

    async def fetch_and_process_data(self):
        """データ取得・処理・保存"""
        start_time = time.time()

        try:
            # 1. データ取得
            price_data = await self.fetcher.fetch_current_data()
            if not price_data:
                logger.warning("データ取得失敗")
                return

            # 2. データベース保存
            await self.db_manager.save_price_data(price_data)

            # 3. テクニカル指標計算
            indicators = await self.calculate_indicators()
            if indicators:
                await self.db_manager.save_technical_indicators(indicators)

            # 4. パターン検出
            patterns = await self.detect_patterns()
            if patterns:
                await self.db_manager.save_pattern_detections(patterns)
                await self.send_notifications(patterns)

            # 5. 履歴記録
            processing_time = (time.time() - start_time) * 1000
            await self.db_manager.save_fetch_history(
                success=True,
                response_time_ms=int(processing_time),
                data_count=1
            )

            logger.info(f"データ処理完了: {processing_time:.2f}ms")

        except Exception as e:
            logger.error(f"データ処理エラー: {e}")
            await self.db_manager.save_fetch_history(
                success=False,
                error_message=str(e)
            )
```

## 🔗 既存システム統合

### 📊 **通知システム統合**

#### パターン検出統合

```python
class DatabasePatternDetector:
    """データベースベースのパターン検出器"""

    def __init__(self):
        self.analyzer = NotificationPatternAnalyzer()
        self.db_manager = DatabaseManager()

    async def detect_patterns_from_db(self) -> List[Dict[str, Any]]:
        """データベースから最新データを取得してパターン検出"""
        try:
            # 最新の価格データ取得
            price_data = await self.db_manager.get_latest_price_data(
                currency_pair="USD/JPY",
                limit=100  # 十分なデータ量
            )

            # 最新のテクニカル指標取得
            indicators = await self.db_manager.get_latest_indicators(
                currency_pair="USD/JPY",
                timeframe="M5"  # 5分足
            )

            # パターン検出実行
            patterns = await self.analyzer.detect_all_patterns(
                price_data=price_data,
                indicators=indicators
            )

            return patterns

        except Exception as e:
            logger.error(f"パターン検出エラー: {e}")
            return []
```

#### 通知送信統合

```python
class DatabaseNotificationManager:
    """データベースベースの通知管理"""

    def __init__(self):
        self.discord_client = DiscordClient()
        self.db_manager = DatabaseManager()

    async def send_pattern_notifications(self, patterns: List[Dict[str, Any]]):
        """検出されたパターンの通知送信"""
        for pattern in patterns:
            try:
                # 重複チェック
                if await self.is_duplicate_notification(pattern):
                    continue

                # 通知テンプレート選択
                template = self.get_notification_template(pattern['pattern_number'])

                # Discord通知作成
                embed = template.create_embed(pattern)

                # 通知送信
                message_id = await self.discord_client.send_embed(embed)

                # 通知履歴保存
                await self.db_manager.update_pattern_notification(
                    pattern_id=pattern['id'],
                    notification_sent=True,
                    discord_message_id=message_id
                )

                logger.info(f"パターン{pattern['pattern_number']}通知送信完了")

            except Exception as e:
                logger.error(f"通知送信エラー: {e}")

    async def is_duplicate_notification(self, pattern: Dict[str, Any]) -> bool:
        """重複通知チェック"""
        # 過去1時間内の同じパターン通知をチェック
        recent_patterns = await self.db_manager.get_recent_patterns(
            pattern_number=pattern['pattern_number'],
            hours=1
        )

        return len(recent_patterns) > 0
```

### 🔧 **設定管理統合**

#### 動的設定管理

```python
class DatabaseConfigManager:
    """データベースベースの設定管理"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.cache = {}
        self.cache_ttl = 300  # 5分キャッシュ

    async def get_config(self, key: str, default=None):
        """設定値取得"""
        # キャッシュチェック
        if key in self.cache:
            cached_value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_value

        # データベースから取得
        config = await self.db_manager.get_system_config(key)
        if config:
            value = self.parse_config_value(config['config_value'], config['config_type'])
            self.cache[key] = (value, time.time())
            return value

        return default

    async def set_config(self, key: str, value: Any, config_type: str = "string"):
        """設定値更新"""
        await self.db_manager.update_system_config(key, value, config_type)

        # キャッシュ更新
        if key in self.cache:
            del self.cache[key]

    def parse_config_value(self, value: str, config_type: str) -> Any:
        """設定値の型変換"""
        if config_type == "integer":
            return int(value)
        elif config_type == "float":
            return float(value)
        elif config_type == "boolean":
            return value.lower() == "true"
        elif config_type == "json":
            return json.loads(value)
        else:
            return value
```

## 📊 パフォーマンス最適化

### ⚡ **API 呼び出し最適化**

#### 呼び出し回数削減

```python
class OptimizedDataFetcher:
    """最適化されたデータ取得クラス"""

    def __init__(self):
        self.fetcher = USDJPYDataFetcher()
        self.cache = {}
        self.cache_ttl = 300  # 5分キャッシュ

    async def get_optimized_data(self) -> Optional[Dict[str, Any]]:
        """最適化されたデータ取得"""
        current_time = time.time()

        # キャッシュチェック
        if 'last_fetch' in self.cache:
            last_fetch_time, last_data = self.cache['last_fetch']
            if current_time - last_fetch_time < self.cache_ttl:
                return last_data

        # 新規データ取得
        data = await self.fetcher.fetch_current_data()
        if data:
            self.cache['last_fetch'] = (current_time, data)

        return data
```

#### バッチ処理

```python
class BatchDataProcessor:
    """バッチデータ処理クラス"""

    def __init__(self):
        self.db_manager = DatabaseManager()
        self.batch_size = 100
        self.batch_timeout = 60  # 60秒でバッチ処理

    async def process_batch(self, data_batch: List[Dict[str, Any]]):
        """バッチデータ処理"""
        if len(data_batch) >= self.batch_size:
            await self.save_batch_data(data_batch)
            return []
        return data_batch

    async def save_batch_data(self, data_batch: List[Dict[str, Any]]):
        """バッチデータ保存"""
        try:
            # 一括挿入
            await self.db_manager.bulk_insert_price_data(data_batch)
            logger.info(f"バッチ保存完了: {len(data_batch)}件")
        except Exception as e:
            logger.error(f"バッチ保存エラー: {e}")
```

### 🗄️ **データベース最適化**

#### インデックス最適化

```sql
-- 複合インデックス作成
CREATE INDEX CONCURRENTLY idx_price_data_currency_timestamp_composite
ON price_data (currency_pair, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_tech_indicators_composite
ON technical_indicators (currency_pair, indicator_type, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_pattern_detections_composite
ON pattern_detections (currency_pair, pattern_number, detection_time DESC);
```

#### クエリ最適化

```python
class OptimizedDatabaseQueries:
    """最適化されたデータベースクエリ"""

    async def get_latest_data_optimized(self, limit: int = 100) -> List[Dict[str, Any]]:
        """最適化された最新データ取得"""
        query = """
        SELECT pd.*, ti.indicator_type, ti.value, ti.additional_data
        FROM price_data pd
        LEFT JOIN technical_indicators ti
            ON pd.currency_pair = ti.currency_pair
            AND pd.timestamp = ti.timestamp
        WHERE pd.currency_pair = 'USD/JPY'
        ORDER BY pd.timestamp DESC
        LIMIT :limit
        """

        return await self.db_manager.execute_query(query, {"limit": limit})

    async def get_pattern_statistics(self, days: int = 7) -> Dict[str, Any]:
        """パターン統計取得"""
        query = """
        SELECT
            pattern_number,
            pattern_name,
            COUNT(*) as detection_count,
            AVG(confidence_score) as avg_confidence,
            MAX(detection_time) as last_detection
        FROM pattern_detections
        WHERE detection_time >= NOW() - INTERVAL ':days days'
        GROUP BY pattern_number, pattern_name
        ORDER BY detection_count DESC
        """

        return await self.db_manager.execute_query(query, {"days": days})
```

## 🔧 実装ファイル構成

### 📁 **新規作成ファイル**

```
src/infrastructure/database/
├── models/
│   ├── price_data_model.py          # 価格データモデル
│   ├── technical_indicator_model.py # テクニカル指標モデル
│   ├── pattern_detection_model.py   # パターン検出モデル
│   ├── data_fetch_history_model.py  # データ取得履歴モデル
│   └── system_config_model.py       # システム設定モデル
├── repositories/
│   ├── price_data_repository.py     # 価格データリポジトリ
│   ├── technical_indicator_repository.py # テクニカル指標リポジトリ
│   ├── pattern_detection_repository.py   # パターン検出リポジトリ
│   └── system_config_repository.py  # システム設定リポジトリ
└── services/
    ├── data_fetcher_service.py      # データ取得サービス
    ├── technical_indicator_service.py # テクニカル指標サービス
    └── pattern_detection_service.py # パターン検出サービス

src/infrastructure/scheduler/
├── usdjpy_data_scheduler.py         # USD/JPYデータ取得スケジューラー
├── technical_indicator_scheduler.py # テクニカル指標計算スケジューラー
└── pattern_detection_scheduler.py   # パターン検出スケジューラー

scripts/cron/
├── usdjpy_data_cron.py              # USD/JPYデータ取得cron
└── technical_analysis_cron.py       # テクニカル分析cron

tests/
├── database/
│   ├── test_price_data_model.py     # 価格データモデルテスト
│   ├── test_technical_indicator_model.py # テクニカル指標モデルテスト
│   └── test_pattern_detection_model.py   # パターン検出モデルテスト
├── services/
│   ├── test_data_fetcher_service.py # データ取得サービステスト
│   └── test_technical_indicator_service.py # テクニカル指標サービステスト
└── integration/
    └── test_database_integration.py # データベース統合テスト
```

### 🔄 **既存ファイル修正**

```
src/infrastructure/
├── analysis/
│   └── notification_pattern_analyzer.py  # データベース統合対応
├── messaging/
│   └── notification_manager.py           # データベース通知対応
└── external_apis/
    └── yahoo_finance_client.py           # USD/JPY特化対応

scripts/cron/
├── integrated_ai_discord.py              # データベース統合対応
└── real_ai_discord_v2.py                 # データベース統合対応
```

## 📅 実装スケジュール

### 🗓️ **Phase 1: データベース基盤（1 週間）**

#### Day 1-2: データベースモデル実装

- [ ] `price_data_model.py` 作成
- [ ] `technical_indicator_model.py` 作成
- [ ] `pattern_detection_model.py` 作成
- [ ] `data_fetch_history_model.py` 作成
- [ ] `system_config_model.py` 作成

#### Day 3-4: リポジトリ実装

- [ ] `price_data_repository.py` 作成
- [ ] `technical_indicator_repository.py` 作成
- [ ] `pattern_detection_repository.py` 作成
- [ ] `system_config_repository.py` 作成

#### Day 5-7: データベーステスト

- [ ] モデル単体テスト
- [ ] リポジトリ単体テスト
- [ ] データベース統合テスト

### 🗓️ **Phase 2: データ取得システム（1 週間）**

#### Day 1-3: データ取得サービス実装

- [ ] `data_fetcher_service.py` 作成
- [ ] `technical_indicator_service.py` 作成
- [ ] Yahoo Finance API 統合
- [ ] エラーハンドリング実装

#### Day 4-5: スケジューラー実装

- [ ] `usdjpy_data_scheduler.py` 作成
- [ ] `technical_indicator_scheduler.py` 作成
- [ ] 5 分間隔実行設定

#### Day 6-7: テスト・最適化

- [ ] データ取得テスト
- [ ] パフォーマンス最適化
- [ ] エラー処理テスト

### 🗓️ **Phase 3: 通知システム統合（1 週間）**

#### Day 1-3: パターン検出統合

- [ ] `pattern_detection_service.py` 作成
- [ ] 既存パターン検出器統合
- [ ] データベースベース検出実装

#### Day 4-5: 通知管理統合

- [ ] データベース通知管理実装
- [ ] 重複通知防止機能
- [ ] 通知履歴管理

#### Day 6-7: 統合テスト

- [ ] エンドツーエンドテスト
- [ ] 通知精度テスト
- [ ] パフォーマンステスト

### 🗓️ **Phase 4: 本番運用準備（1 週間）**

#### Day 1-3: cron 設定・監視

- [ ] `usdjpy_data_cron.py` 作成
- [ ] `technical_analysis_cron.py` 作成
- [ ] 監視システム実装

#### Day 4-5: 設定管理・最適化

- [ ] 動的設定管理実装
- [ ] パフォーマンス最適化
- [ ] データクリーンアップ機能

#### Day 6-7: 本番デプロイ

- [ ] 本番環境設定
- [ ] データ移行
- [ ] 運用開始

## 📊 期待効果

### 🎯 **API 呼び出し削減**

- **現在**: 171 回/日（複数通貨ペア）
- **実装後**: 288 回/日（USD/JPY のみ）
- **削減率**: 0%（通貨ペア削減による効果）

### ⚡ **パフォーマンス向上**

- **データ取得時間**: 3-5 秒 → 1-2 秒
- **分析処理時間**: 10-15 秒 → 5-8 秒
- **通知送信時間**: 3-5 秒 → 1-2 秒

### 📈 **データ品質向上**

- **データ取得成功率**: 85% → 95%
- **エラー率**: 15% → 5%
- **データ完全性**: 90% → 98%

### 🔄 **運用効率向上**

- **自動化率**: 70% → 95%
- **監視精度**: 80% → 95%
- **保守性**: 中 → 高

## 🚀 次のステップ

### 📋 **実装開始前チェックリスト**

- [ ] データベース環境確認
- [ ] Yahoo Finance API 接続テスト
- [ ] 既存通知システム動作確認
- [ ] 開発環境セットアップ

### 🔧 **実装開始**

1. **データベースモデル実装**から開始
2. **段階的統合**によるリスク最小化
3. **継続的テスト**による品質保証
4. **本番運用**への段階的移行

---

**🎯 この設計書に基づいて、USD/JPY 特化の 5 分おきデータ取得システムを実装し、既存の通知システムと完全統合します。**
