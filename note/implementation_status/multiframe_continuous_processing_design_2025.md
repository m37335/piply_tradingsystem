# 🔄 マルチタイムフレーム継続処理システム設計書

**作成日**: 2025 年 8 月 10 日
**プロジェクト**: Exchange Analytics System
**設計対象**: 5 分足データ取得後の自動集計とテクニカル指標計算の継続処理システム

## 🎯 設計目的

### 問題解決

- **初回データ取得の制約**: 5 分足だけではテクニカル指標が計算できない問題の解決
- **API 制限対応**: 複数時間軸の同時取得ができない制約の回避
- **継続的フロー実現**: 5 分足データのみで継続的テクニカル指標計算フローの確立
- **パターン検出統合**: テクニカル指標を活用したパターン検出システムの統合

### システム概要

**初回データ取得**: 全時間軸（5 分足、1 時間足、4 時間足、日足）の履歴データを一括取得し、テクニカル指標を計算
**継続処理**: 5 分足データを取得後、自動的に 1 時間足・4 時間足に集計し、各時間軸でテクニカル指標を計算してパターン検出を行う統合システム

## 🏗️ システムアーキテクチャ

### 初回データ取得フロー

```
初回実行 → 全時間軸データ取得 → テクニカル指標計算 → パターン検出 → システム準備完了
    ↓              ↓              ↓              ↓
 5分足取得    → 1時間足取得   → RSI/MACD/BB   → 6パターン検出 → 継続処理開始
    ↓              ↓              ↓              ↓
 4時間足取得   → 日足取得      → 指標保存      → 検出結果保存   → 監視開始
```

### 継続処理データフロー

```
5分足データ取得 → 自動集計 → テクニカル指標計算 → パターン検出 → 通知
     ↓              ↓              ↓              ↓
  5分足保存    → 1時間足集計   → RSI/MACD/BB   → 6パターン検出 → Discord
     ↓              ↓              ↓              ↓
  データベース   → 4時間足集計   → 指標保存      → 検出結果保存   → 通知送信
```

### コンポーネント構成

```
┌─────────────────────────────────────────────────────────────┐
│                Continuous Processing Pipeline                │
├─────────────────────────────────────────────────────────────┤
│  DataFetcherService    │  TimeframeAggregatorService        │
│  (5分足データ取得)      │  (自動集計処理)                    │
├─────────────────────────────────────────────────────────────┤
│  TechnicalIndicatorService  │  PatternDetectionService      │
│  (テクニカル指標計算)        │  (パターン検出)                │
├─────────────────────────────────────────────────────────────┤
│  NotificationService   │  MonitoringService                 │
│  (通知処理)            │  (監視・ログ)                      │
└─────────────────────────────────────────────────────────────┘
```

## 📋 依存関係と既存コンポーネント

### 既存コンポーネント（再利用）

#### 1. データ取得関連

```python
# 既存クラス: 5分足データ取得
src/infrastructure/database/services/multi_timeframe_data_fetcher_service.py
├── MultiTimeframeDataFetcherService
│   ├── fetch_timeframe_data(timeframe: str) -> Optional[PriceDataModel]
│   └── fetch_all_timeframes() -> Dict[str, Optional[PriceDataModel]]

# 既存クラス: 外部API
src/infrastructure/external_apis/yahoo_finance_client.py
├── YahooFinanceClient
│   ├── get_current_rate(currency_pair: str) -> Optional[Dict]
│   └── get_historical_data(currency_pair, period, interval) -> Optional[pd.DataFrame]
```

#### 2. データベース関連

```python
# 既存モデル: 価格データ
src/infrastructure/database/models/price_data_model.py
├── PriceDataModel
│   ├── currency_pair: str
│   ├── timestamp: datetime
│   ├── open_price, high_price, low_price, close_price: Decimal
│   └── volume: BigInteger

# 既存モデル: テクニカル指標
src/infrastructure/database/models/technical_indicator_model.py
├── TechnicalIndicatorModel
│   ├── indicator_type: str (RSI, MACD, BB)
│   ├── timeframe: str (5m, 1h, 4h, 1d)
│   ├── value: Decimal
│   └── additional_data: JSON

# 既存モデル: パターン検出
src/infrastructure/database/models/pattern_detection_model.py
├── PatternDetectionModel
│   ├── pattern_type: str
│   ├── confidence_score: Decimal
│   ├── direction: str (BUY/SELL)
│   └── detection_data: JSON
```

#### 3. リポジトリ関連

```python
# 既存リポジトリ: 価格データ
src/infrastructure/database/repositories/price_data_repository_impl.py
├── PriceDataRepositoryImpl
│   ├── save(price_data: PriceDataModel) -> PriceDataModel
│   ├── find_by_date_range(start, end, currency_pair) -> List[PriceDataModel]
│   └── find_latest(currency_pair, limit) -> List[PriceDataModel]

# 既存リポジトリ: テクニカル指標
src/infrastructure/database/repositories/technical_indicator_repository_impl.py
├── TechnicalIndicatorRepositoryImpl
│   ├── save(indicator: TechnicalIndicatorModel) -> TechnicalIndicatorModel
│   ├── find_latest_by_type(indicator_type, timeframe) -> List[TechnicalIndicatorModel]
│   └── find_by_date_range(start, end, indicator_type, timeframe) -> List[TechnicalIndicatorModel]

# 既存リポジトリ: パターン検出
src/infrastructure/database/repositories/pattern_detection_repository_impl.py
├── PatternDetectionRepositoryImpl
│   ├── save(pattern: PatternDetectionModel) -> PatternDetectionModel
│   ├── find_unnotified_patterns() -> List[PatternDetectionModel]
│   └── mark_notification_sent(pattern_id: int) -> bool
```

#### 4. 分析関連

```python
# 既存クラス: テクニカル指標計算
src/infrastructure/analysis/technical_indicators.py
├── TechnicalIndicatorsAnalyzer
│   ├── calculate_rsi(data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
│   ├── calculate_macd(data: pd.DataFrame, timeframe: str) -> Dict[str, Any]
│   └── calculate_bollinger_bands(data: pd.DataFrame, timeframe: str) -> Dict[str, Any]

# 既存クラス: パターン検出器
src/infrastructure/analysis/pattern_detectors/
├── breakout_detector.py
├── trend_reversal_detector.py
├── rsi_battle_detector.py
├── pullback_detector.py
├── divergence_detector.py
└── composite_signal_detector.py
```

#### 5. 通知関連

```python
# 既存クラス: Discord通知
src/infrastructure/messaging/discord_client.py
├── DiscordClient
│   └── send_message(message: str) -> bool

# 既存クラス: 通知管理
src/infrastructure/messaging/notification_manager.py
├── NotificationManager
│   ├── send_pattern_notification(pattern: PatternDetectionModel) -> bool
│   └── send_system_notification(message: str) -> bool
```

## 🆕 新規作成コンポーネント

### 1. 初回データ取得サービス

#### ファイル: `src/infrastructure/database/services/initial_data_loader_service.py`

```python
"""
初回データ取得サービス

責任:
- 全時間軸（5分足、1時間足、4時間足、日足）の履歴データ一括取得
- 初回テクニカル指標計算
- 初回パターン検出実行
- システム初期化の完了確認

特徴:
- API制限を考慮した段階的データ取得
- 重複データの防止
- 包括的エラーハンドリング
- 初期化進捗の監視
"""

class InitialDataLoaderService:
    """
    初回データ取得サービス

    責任:
    - 全時間軸（5分足、1時間足、4時間足、日足）の履歴データ一括取得
    - 初回テクニカル指標計算
    - 初回パターン検出実行
    - システム初期化の完了確認
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.yahoo_client = YahooFinanceClient()
        self.price_repo = PriceDataRepositoryImpl(session)
        self.indicator_service = MultiTimeframeTechnicalIndicatorService(session)
        self.pattern_service = EfficientPatternDetectionService(session)

        # 初回取得設定
        self.initial_load_config = {
            "5m": {"period": "7d", "interval": "5m", "description": "5分足"},
            "1h": {"period": "30d", "interval": "1h", "description": "1時間足"},
            "4h": {"period": "60d", "interval": "4h", "description": "4時間足"},
            "1d": {"period": "365d", "interval": "1d", "description": "日足"}
        }

        self.currency_pair = "USD/JPY"
        self.max_retries = 3
        self.retry_delay = 5  # 秒

    async def load_all_initial_data(self) -> Dict[str, Any]:
        """
        全時間軸の初回データを取得

        Returns:
            Dict[str, Any]: 各時間軸の取得結果
        """
        # 実装詳細...

    async def load_timeframe_data(self, timeframe: str) -> int:
        """
        特定時間軸の初回データを取得

        Args:
            timeframe: 時間軸（5m, 1h, 4h, 1d）

        Returns:
            int: 取得したデータ件数
        """
        # 実装詳細...

    async def calculate_initial_indicators(self) -> Dict[str, int]:
        """
        初回テクニカル指標を計算

        Returns:
            Dict[str, int]: 各時間軸の指標計算件数
        """
        # 実装詳細...

    async def detect_initial_patterns(self) -> Dict[str, int]:
        """
        初回パターン検出を実行

        Returns:
            Dict[str, int]: 検出されたパターン数
        """
        # 実装詳細...

    async def verify_initialization(self) -> bool:
        """
        初期化の完了を確認

        Returns:
            bool: 初期化完了フラグ
        """
        # 実装詳細...
```

### 2. 継続処理統合サービス

#### ファイル: `src/infrastructure/database/services/continuous_processing_service.py`

```python
"""
継続処理統合サービス

責任:
- 5分足データ取得後の自動集計処理
- マルチタイムフレームテクニカル指標計算
- パターン検出の統合実行
- エラーハンドリングとリトライ機能

特徴:
- 完全自動化された継続処理パイプライン
- 各ステップの依存関係管理
- 包括的エラーハンドリング
- パフォーマンス監視
"""

class ContinuousProcessingService:
    """
    継続処理統合サービス

    責任:
    - 5分足データ取得後の自動集計処理
    - マルチタイムフレームテクニカル指標計算
    - パターン検出の統合実行
    - エラーハンドリングとリトライ機能
    """

    def __init__(self, session: AsyncSession):
        # 依存サービス初期化
        self.timeframe_aggregator = TimeframeAggregatorService(session)
        self.technical_indicator_service = MultiTimeframeTechnicalIndicatorService(session)
        self.pattern_detection_service = EfficientPatternDetectionService(session)
        self.notification_service = NotificationManager()

        # 設定
        self.currency_pair = "USD/JPY"
        self.timeframes = ["5m", "1h", "4h"]
        self.retry_attempts = 3
        self.retry_delay = 30  # 秒

    async def process_5m_data(self, price_data: PriceDataModel) -> Dict[str, Any]:
        """
        5分足データの継続処理を実行

        Args:
            price_data: 取得された5分足データ

        Returns:
            Dict[str, Any]: 処理結果の統計情報
        """
        # 実装詳細...

    async def aggregate_timeframes(self) -> Dict[str, int]:
        """
        時間軸の自動集計を実行

        Returns:
            Dict[str, int]: 各時間軸の集計件数
        """
        # 実装詳細...

    async def calculate_all_indicators(self) -> Dict[str, int]:
        """
        全時間軸のテクニカル指標を計算

        Returns:
            Dict[str, int]: 各時間軸の指標計算件数
        """
        # 実装詳細...

    async def detect_patterns(self) -> Dict[str, int]:
        """
        パターン検出を実行

        Returns:
            Dict[str, int]: 検出されたパターン数
        """
        # 実装詳細...
```

### 2. 時間軸自動集計サービス

#### ファイル: `src/infrastructure/database/services/timeframe_aggregator_service.py`

```python
"""
時間軸自動集計サービス

責任:
- 5分足データから1時間足・4時間足への自動集計
- 集計データのデータベース保存
- 重複データの防止
- 集計品質の監視

特徴:
- リアルタイム集計処理
- 効率的なメモリ使用
- データ整合性保証
- 自動クリーンアップ
"""

class TimeframeAggregatorService:
    """
    時間軸自動集計サービス

    責任:
    - 5分足データから1時間足・4時間足への自動集計
    - 集計データのデータベース保存
    - 重複データの防止
    - 集計品質の監視
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.price_repo = PriceDataRepositoryImpl(session)
        self.currency_pair = "USD/JPY"

        # 集計設定
        self.aggregation_rules = {
            "1h": {"minutes": 60, "description": "1時間足"},
            "4h": {"minutes": 240, "description": "4時間足"}
        }

    async def aggregate_1h_data(self) -> List[PriceDataModel]:
        """
        5分足から1時間足データを集計

        Returns:
            List[PriceDataModel]: 集計された1時間足データ
        """
        # 実装詳細...

    async def aggregate_4h_data(self) -> List[PriceDataModel]:
        """
        5分足から4時間足データを集計

        Returns:
            List[PriceDataModel]: 集計された4時間足データ
        """
        # 実装詳細...

    async def aggregate_all_timeframes(self) -> Dict[str, int]:
        """
        全時間軸の集計を実行

        Returns:
            Dict[str, int]: 各時間軸の集計件数
        """
        # 実装詳細...

    def _aggregate_timeframe_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        指定時間軸にデータを集計

        Args:
            df: 5分足データのDataFrame
            timeframe: 集計時間軸（1h, 4h）

        Returns:
            pd.DataFrame: 集計されたデータ
        """
        # 実装詳細...
```

### 3. システム初期化マネージャー

#### ファイル: `src/infrastructure/database/services/system_initialization_manager.py`

```python
"""
システム初期化マネージャー

責任:
- 初回データ取得と継続処理の統合管理
- 初期化状態の管理
- 初回実行と継続実行の切り替え
- システム状態の監視

特徴:
- 初回実行の自動検出
- 段階的初期化プロセス
- 初期化失敗時の自動復旧
- 継続処理への自動移行
"""

class SystemInitializationManager:
    """
    システム初期化マネージャー

    責任:
    - 初回データ取得と継続処理の統合管理
    - 初期化状態の管理
    - 初回実行と継続実行の切り替え
    - システム状態の監視
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.initial_loader = InitialDataLoaderService(session)
        self.continuous_service = ContinuousProcessingService(session)
        self.monitor = ContinuousProcessingMonitor()

        # 初期化状態
        self.initialization_status = {
            "is_initialized": False,
            "initialization_date": None,
            "data_counts": {},
            "indicator_counts": {},
            "pattern_counts": {}
        }

    async def check_initialization_status(self) -> bool:
        """
        初期化状態をチェック

        Returns:
            bool: 初期化済みフラグ
        """
        # 実装詳細...

    async def perform_initial_initialization(self) -> Dict[str, Any]:
        """
        初回初期化を実行

        Returns:
            Dict[str, Any]: 初期化結果
        """
        # 実装詳細...

    async def start_continuous_processing(self) -> bool:
        """
        継続処理を開始

        Returns:
            bool: 開始成功フラグ
        """
        # 実装詳細...

    async def run_system_cycle(self) -> Dict[str, Any]:
        """
        システムサイクルを実行（初期化チェック + 継続処理）

        Returns:
            Dict[str, Any]: 実行結果
        """
        # 実装詳細...
```

### 4. 継続処理スケジューラー

#### ファイル: `src/infrastructure/schedulers/continuous_processing_scheduler.py`

```python
"""
継続処理スケジューラー

責任:
- 5分足データ取得の定期実行
- 継続処理パイプラインの統合管理
- エラー処理とリトライ機能
- システム監視とログ記録

特徴:
- 5分間隔での自動実行
- 包括的エラーハンドリング
- パフォーマンス監視
- 自動復旧機能
"""

class ContinuousProcessingScheduler:
    """
    継続処理スケジューラー

    責任:
    - 5分足データ取得の定期実行
    - 継続処理パイプラインの統合管理
    - エラー処理とリトライ機能
    - システム監視とログ記録
    """

    def __init__(self):
        self.running = False
        self.session = None
        self.continuous_service = None

        # スケジューラー設定
        self.interval_minutes = 5
        self.max_retries = 3
        self.retry_delay = 30  # 秒

        # 統計情報
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_error": None,
            "processing_times": []
        }

    async def start(self):
        """
        スケジューラーを開始
        """
        # 実装詳細...

    async def stop(self):
        """
        スケジューラーを停止
        """
        # 実装詳細...

    async def run_single_cycle(self):
        """
        単一サイクルの実行
        """
        # 実装詳細...

    async def _fetch_and_process_data(self):
        """
        データ取得と処理を実行
        """
        # 実装詳細...
```

### 5. 継続処理監視サービス

#### ファイル: `src/infrastructure/monitoring/continuous_processing_monitor.py`

```python
"""
継続処理監視サービス

責任:
- 継続処理パイプラインの監視
- パフォーマンス指標の収集
- エラー検出とアラート
- システム健全性の監視

特徴:
- リアルタイム監視
- 自動アラート機能
- パフォーマンス分析
- 障害検知
"""

class ContinuousProcessingMonitor:
    """
    継続処理監視サービス

    責任:
    - 継続処理パイプラインの監視
    - パフォーマンス指標の収集
    - エラー検出とアラート
    - システム健全性の監視
    """

    def __init__(self):
        self.metrics = {
            "processing_times": [],
            "error_counts": {},
            "success_rates": {},
            "data_volumes": {}
        }

        # 監視設定
        self.alert_thresholds = {
            "max_processing_time": 300,  # 5分
            "min_success_rate": 0.95,    # 95%
            "max_error_count": 5         # 5回
        }

    async def monitor_processing_cycle(self, cycle_data: Dict[str, Any]):
        """
        処理サイクルの監視

        Args:
            cycle_data: サイクル実行データ
        """
        # 実装詳細...

    async def check_system_health(self) -> Dict[str, Any]:
        """
        システム健全性チェック

        Returns:
            Dict[str, Any]: 健全性情報
        """
        # 実装詳細...

    async def send_alert(self, alert_type: str, message: str):
        """
        アラート送信

        Args:
            alert_type: アラートタイプ
            message: アラートメッセージ
        """
        # 実装詳細...
```

## 🔧 実装詳細

### 1. 初回データ取得の実装

#### 初回データ取得フロー

```python
async def load_all_initial_data(self) -> Dict[str, Any]:
    """
    全時間軸の初回データを取得
    """
    start_time = time.time()
    results = {
        "data_counts": {},
        "indicator_counts": {},
        "pattern_counts": {},
        "processing_time": 0
    }

    try:
        logger.info("=== 初回データ取得開始 ===")

        # 1. 各時間軸のデータを順次取得（API制限対応）
        for timeframe, config in self.initial_load_config.items():
            logger.info(f"📊 {config['description']}データ取得中...")

            data_count = await self.load_timeframe_data(timeframe)
            results["data_counts"][timeframe] = data_count

            logger.info(f"✅ {config['description']}完了: {data_count}件")

            # API制限を考慮した待機
            if timeframe != "1d":  # 最後の時間軸以外で待機
                await asyncio.sleep(self.retry_delay)

        # 2. 初回テクニカル指標計算
        logger.info("📈 初回テクニカル指標計算中...")
        indicator_results = await self.calculate_initial_indicators()
        results["indicator_counts"] = indicator_results

        # 3. 初回パターン検出
        logger.info("🔍 初回パターン検出中...")
        pattern_results = await self.detect_initial_patterns()
        results["pattern_counts"] = pattern_results

        # 4. 初期化完了確認
        is_initialized = await self.verify_initialization()

        results["processing_time"] = time.time() - start_time
        results["is_initialized"] = is_initialized

        logger.info("🎉 初回データ取得完了")
        return results

    except Exception as e:
        logger.error(f"初回データ取得エラー: {e}")
        raise
```

#### 時間軸別データ取得

```python
async def load_timeframe_data(self, timeframe: str) -> int:
    """
    特定時間軸の初回データを取得
    """
    try:
        config = self.initial_load_config[timeframe]

        # 既存データチェック
        existing_count = await self.price_repo.count_by_date_range(
            datetime.now() - timedelta(days=7),
            datetime.now(),
            self.currency_pair
        )

        if existing_count > 100:  # 十分なデータが既に存在
            logger.info(f"  ⚠️ {config['description']}データは既に存在: {existing_count}件")
            return existing_count

        # Yahoo Financeから履歴データ取得
        hist_data = await self.yahoo_client.get_historical_data(
            self.currency_pair,
            config["period"],
            config["interval"]
        )

        if hist_data is None or hist_data.empty:
            logger.warning(f"  ❌ {config['description']}データ取得失敗")
            return 0

        # データベースに保存
        saved_count = 0
        for timestamp, row in hist_data.iterrows():
            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                open_price=float(row["Open"]),
                high_price=float(row["High"]),
                low_price=float(row["Low"]),
                close_price=float(row["Close"]),
                volume=int(row["Volume"]) if "Volume" in row else 1000000,
                data_source="Yahoo Finance Initial Load"
            )

            # 重複チェック
            existing = await self.price_repo.find_by_timestamp(
                timestamp, self.currency_pair
            )
            if not existing:
                await self.price_repo.save(price_data)
                saved_count += 1

        logger.info(f"  ✅ {config['description']}保存完了: {saved_count}件")
        return saved_count

    except Exception as e:
        logger.error(f"  ❌ {timeframe}データ取得エラー: {e}")
        return 0
```

### 2. システム初期化マネージャーの実装

#### 初期化状態チェック

```python
async def check_initialization_status(self) -> bool:
    """
    初期化状態をチェック
    """
    try:
        # 各時間軸のデータ存在確認
        timeframes = ["5m", "1h", "4h", "1d"]
        min_data_counts = {"5m": 100, "1h": 50, "4h": 30, "1d": 30}

        for timeframe in timeframes:
            data_count = await self.price_repo.count_by_date_range(
                datetime.now() - timedelta(days=7),
                datetime.now(),
                self.currency_pair
            )

            if data_count < min_data_counts[timeframe]:
                logger.info(f"初期化未完了: {timeframe}データ不足 ({data_count}/{min_data_counts[timeframe]})")
                return False

        # テクニカル指標の存在確認
        indicator_count = await self.indicator_service.count_latest_indicators()
        if indicator_count < 50:
            logger.info(f"初期化未完了: テクニカル指標不足 ({indicator_count}/50)")
            return False

        logger.info("初期化完了確認済み")
        return True

    except Exception as e:
        logger.error(f"初期化状態チェックエラー: {e}")
        return False
```

#### システムサイクル実行

```python
async def run_system_cycle(self) -> Dict[str, Any]:
    """
    システムサイクルを実行（初期化チェック + 継続処理）
    """
    try:
        # 1. 初期化状態をチェック
        is_initialized = await self.check_initialization_status()

        if not is_initialized:
            logger.info("=== 初回初期化を実行 ===")
            return await self.perform_initial_initialization()
        else:
            logger.info("=== 継続処理を実行 ===")
            return await self.continuous_service.process_latest_data()

    except Exception as e:
        logger.error(f"システムサイクルエラー: {e}")
        raise
```

### 3. 継続処理パイプラインの実装

#### メインフロー

```python
async def process_5m_data(self, price_data: PriceDataModel) -> Dict[str, Any]:
    """
    5分足データの継続処理を実行
    """
    start_time = time.time()
    results = {
        "aggregation": {},
        "indicators": {},
        "patterns": {},
        "notifications": {},
        "processing_time": 0
    }

    try:
        # 1. 5分足データを保存
        saved_data = await self.price_repo.save(price_data)

        # 2. 時間軸集計を実行
        aggregation_results = await self.aggregate_timeframes()
        results["aggregation"] = aggregation_results

        # 3. テクニカル指標を計算
        indicator_results = await self.calculate_all_indicators()
        results["indicators"] = indicator_results

        # 4. パターン検出を実行
        pattern_results = await self.detect_patterns()
        results["patterns"] = pattern_results

        # 5. 通知処理
        notification_results = await self.process_notifications()
        results["notifications"] = notification_results

        # 処理時間を記録
        results["processing_time"] = time.time() - start_time

        return results

    except Exception as e:
        logger.error(f"継続処理エラー: {e}")
        raise
```

#### 時間軸集計の実装

```python
async def aggregate_1h_data(self) -> List[PriceDataModel]:
    """
    5分足から1時間足データを集計
    """
    try:
        # 過去1時間の5分足データを取得
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=1)

        m5_data = await self.price_repo.find_by_date_range_and_timeframe(
            start_date, end_date, self.currency_pair, "5m", 1000
        )

        if len(m5_data) < 12:  # 1時間 = 12個の5分足
            logger.warning("1時間足集計に必要な5分足データが不足")
            return []

        # DataFrameに変換
        df = self._convert_to_dataframe(m5_data)

        # 1時間足に集計
        h1_df = self._aggregate_timeframe_data(df, "1H")

        # データベースに保存
        saved_data = []
        for timestamp, row in h1_df.iterrows():
            price_data = PriceDataModel(
                currency_pair=self.currency_pair,
                timestamp=timestamp,
                open_price=float(row["Open"]),
                high_price=float(row["High"]),
                low_price=float(row["Low"]),
                close_price=float(row["Close"]),
                volume=int(row["Volume"]),
                data_source="Aggregated from 5m"
            )

            # 重複チェック
            existing = await self.price_repo.find_by_timestamp(
                timestamp, self.currency_pair
            )
            if not existing:
                saved_data.append(await self.price_repo.save(price_data))

        logger.info(f"1時間足集計完了: {len(saved_data)}件")
        return saved_data

    except Exception as e:
        logger.error(f"1時間足集計エラー: {e}")
        return []
```

### 2. スケジューラーの実装

#### 定期実行フロー

```python
async def run_single_cycle(self):
    """
    単一サイクルの実行
    """
    start_time = time.time()
    self.stats["total_runs"] += 1

    try:
        logger.info(f"継続処理サイクル #{self.stats['total_runs']} 開始")

        # 1. 5分足データを取得
        price_data = await self._fetch_5m_data()
        if not price_data:
            raise Exception("5分足データ取得失敗")

        # 2. 継続処理を実行
        results = await self.continuous_service.process_5m_data(price_data)

        # 3. 統計情報を更新
        processing_time = time.time() - start_time
        self.stats["processing_times"].append(processing_time)
        self.stats["successful_runs"] += 1
        self.stats["last_run"] = datetime.now()

        logger.info(f"継続処理サイクル完了: {processing_time:.2f}秒")
        logger.info(f"結果: 集計={results['aggregation']}, 指標={results['indicators']}, パターン={results['patterns']}")

    except Exception as e:
        self.stats["failed_runs"] += 1
        self.stats["last_error"] = str(e)
        logger.error(f"継続処理サイクルエラー: {e}")

        # リトライ処理
        await self._handle_error(e)
```

### 3. 監視システムの実装

#### パフォーマンス監視

```python
async def monitor_processing_cycle(self, cycle_data: Dict[str, Any]):
    """
    処理サイクルの監視
    """
    try:
        # 処理時間を記録
        processing_time = cycle_data.get("processing_time", 0)
        self.metrics["processing_times"].append(processing_time)

        # 処理時間の閾値チェック
        if processing_time > self.alert_thresholds["max_processing_time"]:
            await self.send_alert(
                "PERFORMANCE",
                f"処理時間が閾値を超過: {processing_time:.2f}秒"
            )

        # 成功率を計算
        total_runs = cycle_data.get("total_runs", 0)
        successful_runs = cycle_data.get("successful_runs", 0)

        if total_runs > 0:
            success_rate = successful_runs / total_runs
            self.metrics["success_rates"]["overall"] = success_rate

            if success_rate < self.alert_thresholds["min_success_rate"]:
                await self.send_alert(
                    "RELIABILITY",
                    f"成功率が閾値を下回る: {success_rate:.2%}"
                )

        # データ量を記録
        data_volume = cycle_data.get("data_volume", 0)
        self.metrics["data_volumes"].append(data_volume)

    except Exception as e:
        logger.error(f"監視処理エラー: {e}")
```

## 📊 設定とパラメータ

### 1. 時間軸設定

```python
TIMEFRAME_CONFIG = {
    "5m": {
        "interval": "5m",
        "minutes": 5,
        "description": "5分足",
        "aggregation_source": None
    },
    "1h": {
        "interval": "1h",
        "minutes": 60,
        "description": "1時間足",
        "aggregation_source": "5m",
        "aggregation_rule": "12_5m_periods"
    },
    "4h": {
        "interval": "4h",
        "minutes": 240,
        "description": "4時間足",
        "aggregation_source": "5m",
        "aggregation_rule": "48_5m_periods"
    }
}
```

### 2. テクニカル指標設定

```python
TECHNICAL_INDICATOR_CONFIG = {
    "rsi": {
        "period": 14,
        "overbought": 70,
        "oversold": 30
    },
    "macd": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9
    },
    "bollinger_bands": {
        "period": 20,
        "std_dev": 2.0
    }
}
```

### 3. パターン検出設定

```python
PATTERN_DETECTION_CONFIG = {
    "breakout": {
        "min_confidence": 70.0,
        "volume_threshold": 1.5
    },
    "trend_reversal": {
        "min_confidence": 75.0,
        "confirmation_periods": 3
    },
    "rsi_battle": {
        "min_confidence": 80.0,
        "battle_threshold": 50.0
    }
}
```

## 🚀 実装計画

### Phase 1: 初回データ取得システム（1 週間）

1. **InitialDataLoaderService**の実装
2. **SystemInitializationManager**の実装
3. 初回データ取得のテスト

### Phase 2: 継続処理基盤（1 週間）

1. **TimeframeAggregatorService**の実装
2. **ContinuousProcessingService**の実装
3. 基本的な統合テスト

### Phase 3: スケジューラー実装（1 週間）

1. **ContinuousProcessingScheduler**の実装
2. エラーハンドリングとリトライ機能
3. 基本的な監視機能

### Phase 4: 監視・最適化（1 週間）

1. **ContinuousProcessingMonitor**の実装
2. パフォーマンス最適化
3. 包括的テスト

### Phase 5: 本番統合（1 週間）

1. 既存システムとの統合
2. 本番環境でのテスト
3. 運用ドキュメント作成

## 📈 期待される効果

### 1. システム信頼性の向上

- **初回データ取得の確実性**: API 制限を考慮した段階的データ取得
- **継続的なテクニカル指標計算**: 5 分足データのみでの継続処理
- **安定したパターン検出**: 十分なデータ量での高精度検出
- **自動エラー復旧**: 初期化失敗時の自動再試行

### 2. パフォーマンスの改善

- **効率的なデータ集計**: 5 分足からの自動時間軸集計
- **最適化された処理フロー**: 初回実行と継続実行の最適化
- **リソース使用量の削減**: API 呼び出し回数の最小化
- **高速な初期化**: 並列処理による初期化時間短縮

### 3. 運用効率の向上

- **自動化された継続処理**: 人手介入不要の完全自動化
- **包括的監視システム**: 初期化から継続処理までの統合監視
- **迅速な問題検知**: リアルタイムアラート機能
- **柔軟な設定管理**: 時間軸やパラメータの動的調整

---

**🔄 Exchange Analytics System** - _Multi-Timeframe Continuous Processing Design_
