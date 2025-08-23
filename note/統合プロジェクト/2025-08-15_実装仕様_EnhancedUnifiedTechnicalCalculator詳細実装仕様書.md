# EnhancedUnifiedTechnicalCalculator 詳細実装仕様書

**作成日**: 2025 年 8 月 15 日  
**旧ファイル名**: 新規作成  
**目的**: 統合テクニカル指標計算システムの詳細実装仕様

## 📋 概要

### 統合の目的

現在のシステムには 3 つのテクニカル指標計算システムが存在し、それぞれ異なる特徴と利点を持っています。これらを統合して、より効率的で機能的なシステムを構築することを目的としています。

### 統合対象システム

1. **UnifiedTechnicalCalculator**: 継続処理・データ永続化
2. **TALibTechnicalIndicators**: 高度分析機能
3. **TechnicalIndicatorsAnalyzer**: 多期間設定・実戦的分析

## 🏗️ アーキテクチャ設計

### 統合システムの全体構造

```
EnhancedUnifiedTechnicalCalculator
├── 基盤機能（UnifiedTechnicalCalculator継承）
│   ├── データ永続化
│   ├── マルチタイムフレーム対応
│   ├── 継続処理統合
│   └── システム互換性
├── 分析機能（TALibTechnicalIndicators統合）
│   ├── 状態判定
│   ├── 傾き分析
│   ├── シグナル生成
│   └── 高度分析
├── 設定最適化（TechnicalIndicatorsAnalyzer統合）
│   ├── 多期間RSI（30, 50, 70）
│   ├── 3期間移動平均
│   ├── 統合データ保存
│   └── 実戦的設定
└── プログレスバー機能（tqdm統一）
    ├── 時間足別進捗表示
    ├── 指標別進捗表示
    ├── データ保存進捗表示
    └── 統合進捗表示
```

### クラス階層設計

```python
class EnhancedUnifiedTechnicalCalculator:
    """
    統合テクニカル指標計算システム

    継承関係:
    - UnifiedTechnicalCalculator: 基盤機能
    - TALibTechnicalIndicators: 分析機能
    - TechnicalIndicatorsAnalyzer: 設定最適化
    """

    def __init__(self):
        # 基盤設定（UnifiedTechnicalCalculator）
        self.timeframes = {...}
        self.session = None
        self.indicator_repo = None

        # 分析機能（TALibTechnicalIndicators）
        self.analyzer = TALibTechnicalIndicators()

        # 最適化設定（TechnicalIndicatorsAnalyzer）
        self.indicators_config = {...}

        # プログレスバー設定（tqdm統一）
        self.progress_config = {
            "enable_progress": True,
            "show_detailed": True,
            "tqdm_config": {
                "ncols": 80,
                "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
                "unit": "指標"
            }
        }
```

## 📊 詳細クラス設計

### 1. EnhancedUnifiedTechnicalCalculator クラス

#### 基本情報

- **ファイル**: `scripts/cron/enhanced_unified_technical_calculator.py`
- **責任**: 統合テクニカル指標計算システム
- **継承**: UnifiedTechnicalCalculator の基盤機能
- **統合**: TALibTechnicalIndicators、TechnicalIndicatorsAnalyzer

#### 主要メソッド

| メソッド名                       | 種類           | 目的                   | 戻り値            | 依存関係     |
| -------------------------------- | -------------- | ---------------------- | ----------------- | ------------ |
| `__init__`                       | コンストラクタ | 初期化・設定           | -                 | 全システム   |
| `initialize`                     | 公開           | 初期化処理             | `bool`            | データベース |
| `cleanup`                        | 公開           | リソースクリーンアップ | `None`            | セッション   |
| `calculate_all_indicators`       | 公開           | 全時間足の指標計算     | `Dict[str, int]`  | 全指標       |
| `calculate_timeframe_indicators` | 公開           | 特定時間足の指標計算   | `int`             | 単一時間足   |
| `calculate_enhanced_rsi`         | 公開           | 多期間 RSI 計算        | `Dict[str, Any]`  | RSI 分析     |
| `calculate_enhanced_macd`        | 公開           | 統合 MACD 計算         | `Dict[str, Any]`  | MACD 分析    |
| `calculate_enhanced_bb`          | 公開           | 統合 BB 計算           | `Dict[str, Any]`  | BB 分析      |
| `calculate_enhanced_ma`          | 公開           | 多期間移動平均計算     | `Dict[str, Any]`  | MA 分析      |
| `calculate_enhanced_stoch`       | 公開           | 統合 STOCH 計算        | `Dict[str, Any]`  | STOCH 分析   |
| `calculate_enhanced_atr`         | 公開           | 統合 ATR 計算          | `Dict[str, Any]`  | ATR 分析     |
| `save_unified_indicator`         | プライベート   | 統合データ保存         | `bool`            | データベース |
| `analyze_indicator_state`        | プライベート   | 指標状態分析           | `Dict[str, Any]`  | 分析機能     |
| `generate_trading_signals`       | 公開           | トレードシグナル生成   | `Dict[str, Any]`  | 全分析       |
| `_create_progress_manager`       | プライベート   | プログレス管理作成     | `ProgressManager` | プログレス   |
| `_update_progress`               | プライベート   | プログレス更新         | `None`            | プログレス   |

#### 内部メソッド（プライベート）

| メソッド名                    | 目的                 | 戻り値             | 依存関係     |
| ----------------------------- | -------------------- | ------------------ | ------------ |
| `_get_price_data`             | 価格データ取得       | `pd.DataFrame`     | データベース |
| `_calculate_multi_period_rsi` | 多期間 RSI 計算      | `Dict[str, float]` | RSI 設定     |
| `_calculate_unified_macd`     | 統合 MACD 計算       | `Dict[str, float]` | MACD 設定    |
| `_calculate_unified_bb`       | 統合 BB 計算         | `Dict[str, float]` | BB 設定      |
| `_calculate_multi_period_ma`  | 多期間 MA 計算       | `Dict[str, float]` | MA 設定      |
| `_calculate_unified_stoch`    | 統合 STOCH 計算      | `Dict[str, float]` | STOCH 設定   |
| `_calculate_unified_atr`      | 統合 ATR 計算        | `float`            | ATR 設定     |
| `_analyze_trend_strength`     | トレンド強度分析     | `Dict[str, Any]`   | 分析機能     |
| `_detect_divergence`          | ダイバージェンス検出 | `Dict[str, Any]`   | 分析機能     |
| `_validate_data_quality`      | データ品質検証       | `bool`             | データ検証   |

### 2. プログレスバー管理クラス（tqdm 統一）

#### ProgressManager クラス

```python
class ProgressManager:
    """
    プログレスバー管理クラス（tqdm統一）

    責任:
    - 複数レベルのプログレスバー管理
    - 時間足別・指標別の進捗表示
    - 詳細進捗とサマリー進捗の切り替え
    """

    def __init__(self, enable_progress: bool = True, tqdm_config: dict = None):
        self.enable_progress = enable_progress
        self.tqdm_config = tqdm_config or {
            "ncols": 80,
            "bar_format": "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]",
            "unit": "指標"
        }
        self.progress_bars = {}

    def start_timeframe_progress(self, timeframe: str, total_indicators: int):
        """時間足別プログレス開始"""
        if not self.enable_progress:
            return None

        from tqdm import tqdm
        pbar = tqdm(
            total=total_indicators,
            desc=f"📊 {timeframe} 指標計算中...",
            unit="指標",
            **self.tqdm_config
        )
        self.progress_bars[f"timeframe_{timeframe}"] = pbar
        return pbar

    def start_indicator_progress(self, indicator: str, total_steps: int):
        """指標別プログレス開始"""
        if not self.enable_progress:
            return None

        from tqdm import tqdm
        pbar = tqdm(
            total=total_steps,
            desc=f"🔍 {indicator} 計算中...",
            unit="ステップ",
            **self.tqdm_config
        )
        self.progress_bars[f"indicator_{indicator}"] = pbar
        return pbar

    def update_progress(self, progress_id, advance: int = 1, description: str = None):
        """プログレス更新"""
        if not self.enable_progress or progress_id is None:
            return

        if description:
            progress_id.set_description(description)
        progress_id.update(advance)

    def close_progress(self, progress_id):
        """プログレス終了"""
        if not self.enable_progress or progress_id is None:
            return

        progress_id.close()

    def __enter__(self):
        """コンテキストマネージャー開始"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャー終了"""
        # 残っているプログレスバーを全て閉じる
        for pbar in self.progress_bars.values():
            if not pbar.closed:
                pbar.close()
```

### 3. 最適化された設定

#### 指標設定

```python
self.indicators_config = {
    "RSI": {
        "short": {
            "period": 30,   # TechnicalIndicatorsAnalyzer から採用
            "overbought": 70,
            "oversold": 30,
            "description": "短期の過熱・過冷感を測定"
        },
        "medium": {
            "period": 50,   # TechnicalIndicatorsAnalyzer から採用
            "overbought": 65,
            "oversold": 35,
            "description": "中期トレンドの強弱を測定"
        },
        "long": {
            "period": 70,   # TechnicalIndicatorsAnalyzer から採用
            "overbought": 60,
            "oversold": 40,
            "description": "長期トレンドの方向性を測定"
        }
    },
    "MACD": {
        "fast_period": 12,  # 全システム共通
        "slow_period": 26,  # 全システム共通
        "signal_period": 9, # 全システム共通
        "analysis_features": [
            "cross_signal",      # TechnicalIndicatorsAnalyzer から
            "zero_line_position" # TechnicalIndicatorsAnalyzer から
        ],
        "unified_save": True
    },
    "BB": {
        "period": 20,       # 全システム共通
        "std_dev": 2.0,     # 全システム共通
        "analysis_features": [
            "band_position",     # TechnicalIndicatorsAnalyzer から
            "band_walk",         # TechnicalIndicatorsAnalyzer から
            "band_width"         # TechnicalIndicatorsAnalyzer から
        ],
        "unified_save": True
    },
    "SMA": {
        "short": 20,        # TechnicalIndicatorsAnalyzer から採用
        "medium": 50,       # TechnicalIndicatorsAnalyzer から採用
        "long": 200,        # TechnicalIndicatorsAnalyzer から採用
        "description": "短期・中期・長期の3期間で市場トレンドを把握"
    },
    "EMA": {
        "short": 12,        # UnifiedTechnicalCalculator から採用
        "medium": 26,       # UnifiedTechnicalCalculator から採用
        "long": 50,         # TechnicalIndicatorsAnalyzer から採用
        "description": "MACDと連携する短期・中期、長期トレンド用"
    },
    "STOCH": {
        "fastk_period": 14, # UnifiedTechnicalCalculator から採用
        "slowk_period": 3,  # UnifiedTechnicalCalculator から採用
        "slowd_period": 3,  # UnifiedTechnicalCalculator から採用
        "analysis_features": [
            "state_analysis"     # TALibTechnicalIndicators から
        ],
        "unified_save": True
    },
    "ATR": {
        "period": 14,       # UnifiedTechnicalCalculator から採用
        "analysis_features": [
            "volatility_analysis" # TALibTechnicalIndicators から
        ]
    }
}
```

## 💾 データ構造設計

### 1. 統合データ保存方式

#### 現在の問題

```python
# 現在の問題: 別々のレコード
current_macd_records = [
    {"indicator_type": "MACD", "value": 0.1234, "additional_data": {}},
    {"indicator_type": "MACD", "value": 0.0987, "additional_data": {}},
    {"indicator_type": "MACD", "value": 0.0247, "additional_data": {}}
]
```

#### 統合後の設計

```python
# 統合後の設計: 1つのレコードに統合
unified_macd_record = {
    "indicator_type": "MACD",
    "value": 0.1234,  # MACD線
    "additional_data": {
        "signal_line": 0.0987,
        "histogram": 0.0247,
        "state": "bullish",
        "analysis": {
            "trend": "rising",
            "strength": "strong",
            "divergence": "none",
            "cross_signal": "bullish_cross",
            "zero_line_position": "above"
        }
    }
}

# 統合後の設計: 多期間RSI
unified_rsi_record = {
    "indicator_type": "RSI",
    "value": 65.2,  # 中期RSI値をメイン値として使用
    "additional_data": {
        "short_term": {
            "period": 30,
            "value": 75.5,
            "state": "overbought",
            "trend": "rising"
        },
        "medium_term": {
            "period": 50,
            "value": 65.2,
            "state": "neutral",
            "trend": "flat"
        },
        "long_term": {
            "period": 70,
            "value": 58.8,
            "state": "neutral",
            "trend": "falling"
        },
        "analysis": {
            "overall_trend": "mixed",
            "short_term_signal": "sell",
            "medium_term_signal": "hold",
            "long_term_signal": "buy",
            "confidence": "medium"
        }
    }
}
```

### 2. データベーススキーマ

#### 現在のスキーマ

```sql
CREATE TABLE technical_indicators (
    id INTEGER PRIMARY KEY,
    currency_pair VARCHAR(10),
    timestamp DATETIME,
    indicator_type VARCHAR(20),
    timeframe VARCHAR(10),
    value DECIMAL(15,8),
    additional_data JSON,    -- 現在は空の辞書
    parameters JSON,
    created_at DATETIME
);
```

#### 統合後のスキーマ（変更なし、使用方法変更）

```sql
-- スキーマは変更せず、additional_dataの活用方法を変更
CREATE TABLE technical_indicators (
    id INTEGER PRIMARY KEY,
    currency_pair VARCHAR(10),
    timestamp DATETIME,
    indicator_type VARCHAR(20),
    timeframe VARCHAR(10),
    value DECIMAL(15,8),
    additional_data JSON,    -- 統合データを保存
    parameters JSON,
    created_at DATETIME
);
```

## 🔄 依存関係とワークフロー

### 1. ファイル依存関係

#### 直接依存

```
enhanced_unified_technical_calculator.py
├── src/infrastructure/database/connection.py
├── src/infrastructure/database/models/technical_indicator_model.py
├── src/infrastructure/database/repositories/technical_indicator_repository_impl.py
├── src/infrastructure/analysis/talib_technical_indicators.py
├── src/infrastructure/analysis/technical_indicators.py
├── scripts/cron/unified_technical_calculator.py
└── src/utils/progress_manager.py  # 新規作成（tqdm統一）
```

#### 間接依存

```
enhanced_unified_technical_calculator.py
├── src/infrastructure/database/services/
│   ├── unified_technical_indicator_service.py
│   ├── continuous_processing_service.py
│   └── system_initialization_manager.py
├── src/infrastructure/schedulers/
│   └── continuous_processing_scheduler.py
└── src/presentation/cli/commands/
    └── data_commands.py
```

### 2. ワークフロー統合

#### 継続処理ワークフロー

```
5分足データ取得
    ↓
ContinuousProcessingService.process_5m_data()
    ↓
EnhancedUnifiedTechnicalCalculator.calculate_timeframe_indicators("M5")
    ↓
tqdmプログレスバー表示開始
    ↓
統合データ保存（1レコードに統合）
    ↓
プログレスバー更新
    ↓
パターン検出・通知
    ↓
プログレスバー完了
```

#### 初期化ワークフロー

```
データベース初期化
    ↓
マルチタイムフレームデータ取得
    ↓
EnhancedUnifiedTechnicalCalculator.calculate_all_indicators()
    ↓
時間足別tqdmプログレスバー開始
    ↓
統合データ保存
    ↓
指標別プログレスバー更新
    ↓
初期化完了確認
    ↓
プログレスバー完了
```

#### CLI ワークフロー

```
CLIコマンド実行
    ↓
EnhancedUnifiedTechnicalCalculator.initialize()
    ↓
EnhancedUnifiedTechnicalCalculator.calculate_all_indicators()
    ↓
tqdmプログレスバー表示
    ↓
結果表示・保存
    ↓
プログレスバー完了
```

### 3. サービス統合

#### EnhancedUnifiedTechnicalIndicatorService

```python
class EnhancedUnifiedTechnicalIndicatorService:
    """
    EnhancedUnifiedTechnicalCalculator のサービス層ラッパー
    """

    def __init__(self, session: AsyncSession, currency_pair: str = "USD/JPY"):
        self.session = session
        self.currency_pair = currency_pair
        self.calculator: Optional[EnhancedUnifiedTechnicalCalculator] = None
        self.indicator_repo = TechnicalIndicatorRepositoryImpl(session)

        # 初期化状態
        self.is_initialized = False
        self.initialization_error = None

    async def initialize(self) -> bool:
        """サービスを初期化"""
        try:
            self.calculator = EnhancedUnifiedTechnicalCalculator(self.currency_pair)
            await self.calculator.initialize()
            self.is_initialized = True
            return True
        except Exception as e:
            self.initialization_error = str(e)
            return False

    async def calculate_and_save_all_indicators(self, timeframe: str) -> Dict[str, int]:
        """全テクニカル指標を計算して保存"""
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.calculate_timeframe_indicators(timeframe)
        except Exception as e:
            return {"error": str(e)}

    async def generate_trading_signals(self, timeframe: str) -> Dict[str, Any]:
        """トレードシグナルを生成"""
        if not self.is_initialized:
            await self.initialize()

        try:
            return await self.calculator.generate_trading_signals(timeframe)
        except Exception as e:
            return {"error": str(e)}
```

## 🔧 実装詳細

### 1. メソッド実装仕様

#### calculate_all_indicators（tqdm プログレスバー付き）

```python
async def calculate_all_indicators(self) -> Dict[str, int]:
    """
    全テクニカル指標を計算（tqdmプログレスバー付き）

    Returns:
        Dict[str, int]: 各時間足の計算件数
    """
    results = {}

    # プログレス管理開始
    with ProgressManager(
        enable_progress=self.progress_config["enable_progress"],
        tqdm_config=self.progress_config["tqdm_config"]
    ) as progress_manager:

        # 時間足別の処理
        timeframes = ["M5", "H1", "H4", "D1"]
        total_timeframes = len(timeframes)

        for i, timeframe in enumerate(timeframes):
            # 時間足別プログレス開始
            timeframe_progress = progress_manager.start_timeframe_progress(
                timeframe,
                total_indicators=6  # RSI, MACD, BB, SMA, EMA, STOCH, ATR
            )

            print(f"📊 {timeframe}時間足のテクニカル指標計算を開始...")

            try:
                count = await self.calculate_timeframe_indicators(timeframe, progress_manager)
                results[timeframe] = count

                # プログレス更新
                progress_manager.update_progress(
                    timeframe_progress,
                    advance=6,  # 全指標完了
                    description=f"✅ {timeframe} 完了: {count}件"
                )

                print(f"✅ {timeframe}時間足指標計算完了: {count}件")

            except Exception as e:
                progress_manager.update_progress(
                    timeframe_progress,
                    advance=6,
                    description=f"❌ {timeframe} エラー: {str(e)}"
                )
                print(f"❌ {timeframe}時間足指標計算エラー: {e}")
                results[timeframe] = 0

            # プログレス終了
            progress_manager.close_progress(timeframe_progress)

    return results
```

#### calculate_timeframe_indicators（tqdm プログレスバー付き）

```python
async def calculate_timeframe_indicators(
    self,
    timeframe: str,
    progress_manager: Optional[ProgressManager] = None
) -> int:
    """
    特定時間足の指標を計算（tqdmプログレスバー付き）

    Args:
        timeframe: 時間足
        progress_manager: プログレス管理オブジェクト

    Returns:
        int: 計算件数
    """
    try:
        # 価格データを取得
        df = await self._get_price_data(timeframe)

        if df.empty:
            print(f"⚠️ {timeframe}の価格データがありません")
            return 0

        print(f"📈 {timeframe}データ取得: {len(df)}件")

        # 各指標を計算
        total_indicators = 0
        indicators = [
            ("RSI", self._calculate_enhanced_rsi),
            ("MACD", self._calculate_enhanced_macd),
            ("BB", self._calculate_enhanced_bb),
            ("MA", self._calculate_enhanced_ma),
            ("STOCH", self._calculate_enhanced_stoch),
            ("ATR", self._calculate_enhanced_atr)
        ]

        for indicator_name, calculate_func in indicators:
            # 指標別プログレス開始
            indicator_progress = None
            if progress_manager:
                indicator_progress = progress_manager.start_indicator_progress(
                    indicator_name,
                    total_steps=3  # 計算、分析、保存
                )

            try:
                # 指標計算
                if progress_manager:
                    progress_manager.update_progress(
                        indicator_progress,
                        advance=1,
                        description=f"🔍 {indicator_name} 計算中..."
                    )

                result = await calculate_func(df, timeframe)

                if progress_manager:
                    progress_manager.update_progress(
                        indicator_progress,
                        advance=1,
                        description=f"💾 {indicator_name} 保存中..."
                    )

                # 結果カウント
                if isinstance(result, dict) and "count" in result:
                    count = result["count"]
                else:
                    count = 1 if result else 0

                total_indicators += count

                if progress_manager:
                    progress_manager.update_progress(
                        indicator_progress,
                        advance=1,
                        description=f"✅ {indicator_name} 完了: {count}件"
                    )

            except Exception as e:
                if progress_manager:
                    progress_manager.update_progress(
                        indicator_progress,
                        advance=3,
                        description=f"❌ {indicator_name} エラー: {str(e)}"
                    )
                print(f"❌ {indicator_name}計算エラー: {e}")

            finally:
                if progress_manager and indicator_progress:
                    progress_manager.close_progress(indicator_progress)

        return total_indicators

    except Exception as e:
        print(f"❌ {timeframe}指標計算エラー: {e}")
        return 0
```

#### calculate_enhanced_rsi

```python
async def calculate_enhanced_rsi(self, df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
    """
    多期間RSI計算

    Args:
        df: 価格データ
        timeframe: 時間足

    Returns:
        Dict[str, Any]: 多期間RSI計算結果
    """
    try:
        results = {}

        # 各期間のRSIを計算
        for period_type, config in self.indicators_config["RSI"].items():
            rsi_values = talib.RSI(df["Close"].values, timeperiod=config["period"])
            current_rsi = rsi_values[-1] if not np.isnan(rsi_values[-1]) else None

            if current_rsi is not None:
                # 状態判定
                state = self._analyze_rsi_state(current_rsi, config)

                # 傾き分析
                trend = self._analyze_rsi_trend(rsi_values, periods=5)

                results[period_type] = {
                    "period": config["period"],
                    "value": round(current_rsi, 2),
                    "state": state,
                    "trend": trend
                }

        # 統合分析
        analysis = self._analyze_multi_period_rsi(results)

        # 統合データ保存
        main_value = results.get("medium", {}).get("value", 0)
        await self._save_unified_indicator(
            "RSI", timeframe, main_value, results, analysis
        )

        return {
            "indicator": "RSI",
            "timeframe": timeframe,
            "values": results,
            "analysis": analysis,
            "count": len(results)
        }

    except Exception as e:
        logger.error(f"多期間RSI計算エラー: {e}")
        return {"error": str(e), "count": 0}
```

#### calculate_enhanced_macd

```python
async def calculate_enhanced_macd(self, df: pd.DataFrame, timeframe: str) -> Dict[str, Any]:
    """
    統合MACD計算

    Args:
        df: 価格データ
        timeframe: 時間足

    Returns:
        Dict[str, Any]: 統合MACD計算結果
    """
    try:
        config = self.indicators_config["MACD"]

        # TA-LibでMACD計算
        macd, signal, hist = talib.MACD(
            df["Close"].values,
            fastperiod=config["fast_period"],
            slowperiod=config["slow_period"],
            signalperiod=config["signal_period"]
        )

        # 最新値を取得
        current_macd = macd[-1] if not np.isnan(macd[-1]) else None
        current_signal = signal[-1] if not np.isnan(signal[-1]) else None
        current_hist = hist[-1] if not np.isnan(hist[-1]) else None

        if current_macd is not None:
            # 状態判定
            state = self._analyze_macd_state(current_macd, current_signal, current_hist)

            # クロス分析
            cross_signal = self._analyze_macd_cross(macd, signal)

            # ゼロライン位置
            zero_line_position = self._analyze_zero_line_position(current_macd)

            # 統合データ
            additional_data = {
                "signal_line": round(current_signal, 4) if current_signal else None,
                "histogram": round(current_hist, 4) if current_hist else None,
                "state": state,
                "analysis": {
                    "cross_signal": cross_signal,
                    "zero_line_position": zero_line_position
                }
            }

            # 統合データ保存
            await self._save_unified_indicator(
                "MACD", timeframe, current_macd, additional_data
            )

            return {
                "indicator": "MACD",
                "timeframe": timeframe,
                "value": round(current_macd, 4),
                "additional_data": additional_data,
                "count": 1
            }

        return {"error": "MACD計算失敗", "count": 0}

    except Exception as e:
        logger.error(f"統合MACD計算エラー: {e}")
        return {"error": str(e), "count": 0}
```

### 2. データ保存メソッド

#### \_save_unified_indicator

```python
async def _save_unified_indicator(
    self,
    indicator_type: str,
    timeframe: str,
    value: float,
    additional_data: Dict[str, Any],
    analysis: Optional[Dict[str, Any]] = None
) -> bool:
    """
    統合データ保存

    Args:
        indicator_type: 指標タイプ
        timeframe: 時間足
        value: 主要な値
        additional_data: 追加データ
        analysis: 分析結果

    Returns:
        bool: 保存成功時True
    """
    try:
        # 分析結果を追加データに統合
        if analysis:
            additional_data["analysis"] = analysis

        # 技術指標モデルを作成
        indicator = TechnicalIndicatorModel(
            currency_pair=self.currency_pair,
            timestamp=datetime.now(),
            indicator_type=indicator_type,
            timeframe=timeframe,
            value=value,
            additional_data=additional_data,
            parameters=self.indicators_config.get(indicator_type, {})
        )

        # データベースに保存
        await self.indicator_repo.save(indicator)

        return True

    except Exception as e:
        logger.error(f"統合データ保存エラー: {e}")
        return False
```

## 🧪 テスト設計

### 1. 単体テスト

#### テスト対象メソッド

- `calculate_enhanced_rsi`
- `calculate_enhanced_macd`
- `calculate_enhanced_bb`
- `calculate_enhanced_ma`
- `calculate_enhanced_stoch`
- `calculate_enhanced_atr`
- `_save_unified_indicator`
- `_analyze_indicator_state`
- `ProgressManager` クラス（tqdm 統一）

#### テストケース

```python
class TestEnhancedUnifiedTechnicalCalculator:
    """EnhancedUnifiedTechnicalCalculator テストクラス"""

    async def test_calculate_enhanced_rsi(self):
        """多期間RSI計算テスト"""
        # テストデータ準備
        # 計算実行
        # 結果検証

    async def test_calculate_enhanced_macd(self):
        """統合MACD計算テスト"""
        # テストデータ準備
        # 計算実行
        # 結果検証

    async def test_unified_data_save(self):
        """統合データ保存テスト"""
        # テストデータ準備
        # 保存実行
        # データベース検証

    async def test_progress_manager(self):
        """プログレス管理テスト（tqdm統一）"""
        # プログレス管理作成
        # 進捗更新
        # 完了処理
```

### 2. 統合テスト

#### テスト対象

- 継続処理システムとの統合
- 初期化システムとの統合
- CLI システムとの統合
- プログレスバー機能の統合（tqdm 統一）

#### テストケース

```python
class TestEnhancedUnifiedIntegration:
    """統合テストクラス"""

    async def test_continuous_processing_integration(self):
        """継続処理統合テスト"""
        # 継続処理サービスとの統合テスト

    async def test_initialization_integration(self):
        """初期化統合テスト"""
        # 初期化システムとの統合テスト

    async def test_cli_integration(self):
        """CLI統合テスト"""
        # CLIシステムとの統合テスト

    async def test_progress_bar_integration(self):
        """プログレスバー統合テスト（tqdm統一）"""
        # プログレスバー機能の統合テスト
```

## 📊 パフォーマンス設計

### 1. 計算効率

#### 最適化方針

- バッチ処理による効率化
- メモリ使用量の最適化
- 並列処理の活用
- tqdm プログレスバーの軽量化

#### 期待される効果

- 計算時間: 30%短縮
- メモリ使用量: 20%削減
- データベース負荷: 40%削減
- ユーザー体験: 大幅向上

### 2. データベース効率

#### 最適化方針

- レコード数削減（60%削減予定）
- インデックス最適化
- クエリ効率化

#### 期待される効果

- クエリ速度: 50%向上
- ストレージ使用量: 40%削減
- バックアップ時間: 30%短縮

## 🔄 移行計画

### Phase 1: 基盤統合（1 週間）

1. EnhancedUnifiedTechnicalCalculator クラスの作成
2. 基本計算機能の実装
3. tqdm プログレスバー機能の実装
4. 単体テストの実装

### Phase 2: 分析機能統合（1 週間）

1. TALibTechnicalIndicators の分析機能統合
2. TechnicalIndicatorsAnalyzer の設定統合
3. tqdm プログレスバーの詳細化
4. 統合テストの実装

### Phase 3: データ保存統合（1 週間）

1. 統合データ保存ロジックの実装
2. 既存データの移行
3. データ整合性の確認
4. tqdm プログレスバーの最適化

### Phase 4: システム統合（1 週間）

1. 継続処理システムとの統合
2. CLI 機能の更新
3. 本番環境でのテスト
4. tqdm プログレスバーの本番対応

### Phase 5: アーカイブ（1 日）

1. 過去スクリプトのアーカイブ
2. ドキュメントの更新
3. 最終検証

## 📋 実装チェックリスト

### 開発前

- [ ] 詳細設計の完了
- [ ] テスト計画の策定
- [ ] 開発環境の準備
- [ ] tqdm ライブラリの確認

### 開発中

- [ ] 基盤クラスの実装
- [ ] 分析機能の統合
- [ ] データ保存の統合
- [ ] tqdm プログレスバー機能の実装
- [ ] 単体テストの実装

### 統合時

- [ ] 継続処理システムとの統合
- [ ] 初期化システムとの統合
- [ ] CLI システムとの統合
- [ ] tqdm プログレスバーの統合テスト
- [ ] 統合テストの実行

### リリース前

- [ ] パフォーマンステスト
- [ ] データ整合性の確認
- [ ] tqdm プログレスバーの動作確認
- [ ] ドキュメントの更新
- [ ] アーカイブの実行

## 🎯 期待される効果

### 技術的効果

- システムの統合による保守性向上
- データベース効率の向上
- 計算精度の向上
- tqdm プログレスバーによる可視性向上

### 運用効果

- 管理負荷の軽減
- 設定の一元化
- エラー対応の簡素化
- 進捗状況の把握

### ビジネス効果

- 分析精度の向上
- トレード判断の改善
- システム安定性の向上
- ユーザー体験の向上

---

**更新履歴**:

- 2025-08-15: 初版作成、詳細実装仕様完了
- 2025-08-15: プログレスバー機能の実装仕様追加
- 2025-08-15: tqdm 統一によるプログレスバー仕様更新
