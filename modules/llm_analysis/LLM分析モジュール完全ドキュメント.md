# LLM分析モジュール完全ドキュメント

## 目次
1. [モジュール概要](#モジュール概要)
2. [アーキテクチャ](#アーキテクチャ)
3. [三層ゲート式フィルタリングシステム](#三層ゲート式フィルタリングシステム)
4. [テクニカル指標計算](#テクニカル指標計算)
5. [パターン検出ロジック](#パターン検出ロジック)
6. [設定ファイル](#設定ファイル)
7. [データフロー](#データフロー)
8. [運用・監視](#運用監視)
9. [トラブルシューティング](#トラブルシューティング)

---

## モジュール概要

### 目的
金融市場データを分析し、高品質な取引シグナルを生成するための包括的な分析システム。

### 主要機能
- **階層的テクニカル分析**: 複数時間足での指標計算
- **三層ゲート式フィルタリング**: 段階的なパターン検出
- **イベント駆動アーキテクチャ**: リアルタイム分析
- **パフォーマンス監視**: システム最適化

### 技術スタック
- **Python 3.8+**
- **PostgreSQL + TimescaleDB**: 時系列データベース
- **TA-Lib**: テクニカル指標計算
- **Pandas**: データ処理
- **NumPy**: 数値計算
- **Pytz**: タイムゾーン処理

---

## アーキテクチャ

### システム構成図
```
┌─────────────────────────────────────────────────────────────┐
│                    LLM分析モジュール                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │   データ収集    │  │   データ永続化  │  │   LLM分析    │ │
│  │   モジュール    │  │   モジュール    │  │   モジュール  │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────┐
│                三層ゲート式フィルタリング                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  GATE 1     │  │  GATE 2     │  │      GATE 3         │  │
│  │ 環境認識    │  │ シナリオ選定 │  │     トリガー        │  │
│  │ ゲート      │  │ ゲート      │  │     ゲート          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### ディレクトリ構造
```
/app/modules/llm_analysis/
├── core/                           # コアエンジン
│   ├── three_gate_engine.py        # 三層ゲートエンジン
│   ├── technical_calculator.py     # テクニカル指標計算器
│   ├── pattern_loader.py           # パターン設定ローダー
│   └── performance_monitor.py      # パフォーマンス監視
├── services/                       # サービス層
│   ├── three_gate_analysis_service.py  # 三層ゲート分析サービス
│   └── analysis_service.py         # 従来分析サービス
├── config/                         # 設定ファイル
│   ├── gate1_patterns.yaml         # GATE 1 パターン設定
│   ├── gate2_scenario_patterns.yaml # GATE 2 シナリオ設定
│   └── gate3_patterns.yaml         # GATE 3 トリガー設定
└── scripts/                        # 実行スクリプト
    ├── analysis_system_router.py   # 分析システムルーター
    ├── continuous_monitor_v2.py    # 継続監視スクリプト
    └── realtime_monitor.py         # リアルタイム監視
```

---

## 三層ゲート式フィルタリングシステム

### システム概要
市場環境を段階的にフィルタリングし、高品質なシグナルを生成する3段階の評価システム。

### GATE 1: 環境認識ゲート
**目的**: 市場の基本的な環境を認識し、トレンド方向を確定

#### パターン一覧
1. **trending_market (bullish)**: 確度の高いトレンド相場（強気）
   - `price_above_ema200`: 価格がEMA200を上回る
   - `recent_closes_consistent`: 最近の終値が一貫して上昇
   - `strong_trend_adx`: ADX > 25で強いトレンド

2. **trending_market (bearish)**: 確度の高いトレンド相場（弱気）
   - `price_below_ema200`: 価格がEMA200を下回る
   - `recent_closes_consistent`: 最近の終値が一貫して下降
   - `strong_trend_adx`: ADX > 25で強いトレンド

3. **ranging_market**: レンジ相場
   - `weak_trend_adx`: ADX < 25で弱いトレンド
   - `consistently_weak_trend`: 一貫して弱いトレンド

#### 信頼度計算
- **重み付け平均**: 各条件の重みに基づく信頼度計算
- **最小信頼度**: 0.6以上で合格

### GATE 2: シナリオ選定ゲート
**目的**: 環境に適した取引シナリオを選定

#### シナリオ一覧
1. **pullback_buy**: プルバック買い
   - `price_above_ema55`: 価格がEMA55を上回る
   - `price_below_ema21`: 価格がEMA21を下回る
   - `rsi_oversold`: RSI < 40

2. **rally_sell**: ラリー売り
   - `price_below_ema55`: 価格がEMA55を下回る
   - `price_above_ema21`: 価格がEMA21を上回る
   - `rsi_overbought`: RSI > 60

3. **bullish_breakout**: 強気ブレイクアウト
   - `bollinger_compression`: ボリンジャーバンド幅 < 0.015
   - `price_above_sma20`: 価格がSMA20を上回る

4. **bearish_breakout**: 弱気ブレイクアウト
   - `bollinger_compression`: ボリンジャーバンド幅 < 0.015
   - `price_below_sma20`: 価格がSMA20を下回る

#### 信頼度計算
- **重み付け平均**: 各条件の重みに基づく信頼度計算
- **最小信頼度**: 0.6以上で合格

### GATE 3: トリガーゲート
**目的**: 具体的なエントリータイミングを検出

#### トリガーパターン一覧
1. **bullish_reversal**: 強気転換シグナル
   - **必須条件**: `bullish_candle` (close > open)
   - `rsi_oversold_recovery`: RSI > 35
   - `momentum_bullish`: MACD > MACD_Signal
   - **最小信頼度**: 0.7

2. **bearish_reversal**: 弱気転換シグナル
   - **必須条件**: `bearish_candle` (close < open)
   - `rsi_overbought_decline`: RSI < 65
   - `momentum_bearish`: MACD < MACD_Signal
   - **最小信頼度**: 0.7

3. **engulfing_pattern**: 包み足パターン
   - **必須条件**: `strong_candle`, `engulfs_previous`
   - `strong_candle`: ローソク足の実体が平均の1.5倍以上
   - `engulfs_previous`: 前のローソク足を包み込む
   - **最小信頼度**: 0.7

#### 環境制限
- `bullish_reversal`: `trending_market_bullish`環境でのみ有効
- `bearish_reversal`: `trending_market_bearish`環境でのみ有効
- `engulfing_pattern`: 両環境で有効

---

## テクニカル指標計算

### 階層的テクニカル分析
運用方針に基づく3段階のテクニカル分析を実装：

1. **大局判断（D1・H4）**: トレンド方向の確定
2. **戦術判断（H1）**: エントリーゾーンの特定
3. **執行判断（M5）**: エントリータイミングの最適化

### 計算対象時間足
- **1d**: 日足（大局判断）
- **4h**: 4時間足（大局判断）
- **1h**: 1時間足（戦術判断）
- **5m**: 5分足（執行判断）

### 指標カテゴリ別一覧

#### 1. トレンド指標（Trend Indicators）
**1d足（44個の指標）**:
- EMA_5, EMA_10, EMA_20, EMA_50, EMA_100, EMA_200
- SMA_5, SMA_10, SMA_20, SMA_50, SMA_100, SMA_200
- MACD, MACD_Signal, MACD_Histogram
- ADX, ADXR
- Parabolic_SAR
- Ichimoku_Cloud (Tenkan, Kijun, Senkou_A, Senkou_B, Chikou)
- Williams_R
- CCI
- Ultimate_Oscillator
- Aroon_Up, Aroon_Down, Aroon_Oscillator
- Mass_Index
- Vortex_Positive, Vortex_Negative
- Trix
- Plus_DM, Minus_DM
- Plus_DI, Minus_DI
- DX
- Minus_DI_14, Plus_DI_14
- ADX_14, ADXR_14

**4h足（54個の指標）**:
- 上記に加えて追加の期間設定
- より細かいトレンド分析用指標

**1h足（54個の指標）**:
- 4h足と同様の構成
- 中期的なトレンド分析

**5m足（52個の指標）**:
- 短期的なトレンド分析用
- エントリータイミング用指標

#### 2. オシレーター指標（Oscillator Indicators）
- **RSI_14**: 相対力指数（14期間）
- **Stochastic_14**: ストキャスティクス（14期間）
- **Williams_R**: ウィリアムズ%R
- **CCI**: 商品チャンネル指数
- **Ultimate_Oscillator**: アルティメットオシレーター
- **Aroon_Oscillator**: アロンオシレーター
- **Mass_Index**: マスインデックス

#### 3. ボラティリティ指標（Volatility Indicators）
- **Bollinger_Bands_Upper**: ボリンジャーバンド上限
- **Bollinger_Bands_Middle**: ボリンジャーバンド中央
- **Bollinger_Bands_Lower**: ボリンジャーバンド下限
- **bollinger_width**: ボリンジャーバンド幅
- **ATR_14**: 平均真の範囲（14期間）
- **Keltner_Upper**: ケルトナーチャンネル上限
- **Keltner_Middle**: ケルトナーチャンネル中央
- **Keltner_Lower**: ケルトナーチャンネル下限
- **Donchian_Upper**: ドンチャンチャンネル上限
- **Donchian_Middle**: ドンチャンチャンネル中央
- **Donchian_Lower**: ドンチャンチャンネル下限

#### 4. ボリューム指標（Volume Indicators）
**注意**: Yahoo Finance APIではボリュームデータが0.0のため、現在は非活性化
- **Volume_SMA_20**: ボリューム移動平均（20期間）
- **Volume_Ratio**: ボリューム比率
- **OBV**: オン・バランス・ボリューム
- **AD**: アキュムレーション・ディストリビューション
- **Chaikin_MF**: チャイキン・マネーフロー
- **MFI**: マネーフロー・インデックス
- **VWAP**: 出来高加重平均価格

#### 5. フィボナッチ指標（Fibonacci Indicators）
各時間足で計算されるフィボナッチレベル：

**リトレースメントレベル**:
- Fib_0.0, Fib_0.236, Fib_0.382, Fib_0.5, Fib_0.618, Fib_0.786, Fib_1.0

**エクステンションレベル**:
- Fib_1.272, Fib_1.414, Fib_1.618, Fib_2.0

**フィボナッチ位置**:
- `Fibonacci_Position`: RETRACEMENT_ZONE, EXTENSION_ZONE, TREND_ZONE

### 指標計算の詳細仕様

#### データ検証
```python
def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
    """データの検証と前処理"""
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    
    # データ型変換
    for col in required_columns:
        if col in df.columns:
            df[col] = df[col].astype(np.float64)
    
    # 欠損値処理
    df = df.fillna(method='ffill').fillna(method='bfill')
    
    return df
```

#### ボラティリティ指標計算
```python
def _calculate_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
    """ボラティリティ指標の計算"""
    # ボリンジャーバンド
    bb_upper, bb_middle, bb_lower = talib.BBANDS(
        df['close'], timeperiod=20, nbdevup=2, nbdevdn=2
    )
    
    # ボリンジャーバンド幅
    bb_width = (bb_upper - bb_lower) / bb_middle
    
    # ATR
    atr = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    
    return df
```

#### フィボナッチ計算
```python
def _calculate_fibonacci_levels(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """フィボナッチレベルの計算"""
    config = self.fibonacci_config['trend_direction'][timeframe]
    
    # スイングハイ・ロー検出
    swing_high = df['high'].rolling(window=config['swing_periods'][0]).max()
    swing_low = df['low'].rolling(window=config['swing_periods'][0]).min()
    
    # フィボナッチレベル計算
    for level in config['levels']:
        fib_level = swing_low + (swing_high - swing_low) * level
        df[f'Fib_{level}'] = fib_level
    
    return df
```

---

## パターン検出ロジック

### 条件評価システム

#### 比較演算子
- `>`: より大きい
- `<`: より小さい
- `>=`: 以上
- `<=`: 以下
- `==`: 等しい
- `!=`: 等しくない
- `near`: 近い（±2%の範囲内）
- `all_above`: すべて上回る
- `all_below`: すべて下回る
- `engulfs`: 包み込む

#### 論理演算子
- `and`: 論理積
- `or`: 論理和
- `not`: 論理否定

#### 条件評価フロー
```python
async def evaluate_condition(self, data: Dict[str, Any], condition: Dict[str, Any]) -> float:
    """条件評価の実行"""
    indicator_name = condition.get('indicator')
    operator = condition.get('operator')
    reference = condition.get('reference')
    value = condition.get('value')
    timeframe = condition.get('timeframe', '5m')
    
    # 指標値の取得
    indicator_value = self._get_indicator_value(data, indicator_name, timeframe)
    
    # 参照値の取得
    if reference:
        reference_value = self._get_indicator_value(data, reference, timeframe)
    else:
        reference_value = value
    
    # 演算子による評価
    return self._evaluate_comparison(indicator_value, operator, reference_value)
```

### 信頼度計算

#### 重み付け平均方式
```python
def calculate_confidence(self, conditions: List[Dict], scores: List[float]) -> float:
    """重み付け平均による信頼度計算"""
    total_score = 0.0
    total_weight = 0.0
    
    for condition, score in zip(conditions, scores):
        weight = condition.get('weight', 1.0)
        total_score += score * weight
        total_weight += weight
    
    return total_score / total_weight if total_weight > 0 else 0.0
```

#### 必須条件チェック
```python
def check_required_conditions(self, required_conditions: List[str], passed_conditions: List[str]) -> bool:
    """必須条件のチェック"""
    for required in required_conditions:
        if required not in passed_conditions:
            return False
    return True
```

### シグナル生成ロジック

#### エントリー価格計算
```python
def _calculate_entry_price(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult) -> float:
    """フィボナッチを考慮したエントリー価格の計算"""
    # 時間足プレフィックス付きのclose価格を取得
    current_price = 0.0
    for timeframe in ['5m', '1h', '4h', '1d']:
        close_key = f'{timeframe}_close'
        if close_key in data:
            current_price = data[close_key]
            break
    
    # フィボナッチ位置に基づくエントリー価格の調整
    fib_position = data.get('Fibonacci_Position', 'UNKNOWN')
    
    if 'bullish' in gate1.pattern:
        if fib_position == 'RETRACEMENT_ZONE':
            # フィボナッチリトレースメントレベルでエントリー
            fib_618 = data.get('Fib_0.618', None)
            if fib_618 and fib_618 < current_price:
                return fib_618
        return current_price
    elif 'bearish' in gate1.pattern:
        if fib_position == 'RETRACEMENT_ZONE':
            fib_382 = data.get('Fib_0.382', None)
            if fib_382 and fib_382 > current_price:
                return fib_382
        return current_price
    
    return current_price
```

#### ストップロス・テイクプロフィット計算
```python
def _calculate_stop_loss(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult, entry_price: float) -> float:
    """フィボナッチを考慮したストップロス計算"""
    atr = data.get('ATR_14', 0.01)  # デフォルト値
    
    if 'bullish' in gate1.pattern:
        # 買いの場合：エントリー価格より下にストップロス
        fib_786 = data.get('Fib_0.786', None)
        if fib_786 and fib_786 < entry_price:
            return fib_786
        return entry_price - (atr * 1.5)
    else:
        # 売りの場合：エントリー価格より上にストップロス
        fib_236 = data.get('Fib_0.236', None)
        if fib_236 and fib_236 > entry_price:
            return fib_236
        return entry_price + (atr * 1.5)

def _calculate_take_profit(self, data: Dict[str, Any], gate1: GateResult, gate2: GateResult, entry_price: float) -> List[float]:
    """フィボナッチエクステンションを考慮したテイクプロフィット計算"""
    atr = data.get('ATR_14', 0.01)
    take_profits = []
    
    if 'bullish' in gate1.pattern:
        # フィボナッチエクステンションレベル
        for ext in [1.272, 1.414, 1.618]:
            fib_ext = data.get(f'Fib_{ext}', None)
            if fib_ext and fib_ext > entry_price:
                take_profits.append(fib_ext)
        
        # ATRベースのフォールバック
        if not take_profits:
            take_profits = [
                entry_price + (atr * 1.5),
                entry_price + (atr * 2.0),
                entry_price + (atr * 3.0)
            ]
    else:
        # 売りの場合の逆計算
        for ext in [1.272, 1.414, 1.618]:
            fib_ext = data.get(f'Fib_{ext}', None)
            if fib_ext and fib_ext < entry_price:
                take_profits.append(fib_ext)
        
        if not take_profits:
            take_profits = [
                entry_price - (atr * 1.5),
                entry_price - (atr * 2.0),
                entry_price - (atr * 3.0)
            ]
    
    return take_profits[:3]  # 最大3つのテイクプロフィット
```

---

## 設定ファイル

### GATE 1 パターン設定 (`gate1_patterns.yaml`)
```yaml
patterns:
  trending_market:
    name: "確度の高いトレンド相場"
    description: "明確なトレンド方向を持つ市場環境"
    
    variants:
      bullish:
        name: "確度の高いトレンド相場（強気）"
        conditions:
          - name: "price_above_ema200"
            indicator: "close"
            operator: ">"
            reference: "EMA_200"
            timeframe: "1d"
            weight: 0.4
          - name: "recent_closes_consistent"
            indicator: "close"
            operator: "all_above"
            reference: "EMA_200"
            timeframe: "1d"
            weight: 0.4
          - name: "strong_trend_adx"
            indicator: "ADX"
            operator: ">"
            value: 25
            timeframe: "1d"
            weight: 0.2
        
        confidence_calculation:
          method: "weighted_average"
          min_confidence: 0.6
```

### GATE 2 シナリオ設定 (`gate2_scenario_patterns.yaml`)
```yaml
patterns:
  pullback_buy:
    name: "プルバック買い"
    description: "上昇トレンド中の一時的な押し目での買い機会"
    
    conditions:
      - name: "price_above_ema55"
        indicator: "close"
        operator: ">"
        reference: "EMA_55"
        timeframe: "1h"
        weight: 0.4
      - name: "price_below_ema21"
        indicator: "close"
        operator: "<"
        reference: "EMA_21"
        timeframe: "1h"
        weight: 0.3
      - name: "rsi_oversold"
        indicator: "RSI_14"
        operator: "<"
        value: 40
        timeframe: "1h"
        weight: 0.3
    
    confidence_calculation:
      method: "weighted_average"
      min_confidence: 0.6
```

### GATE 3 トリガー設定 (`gate3_patterns.yaml`)
```yaml
patterns:
  bullish_reversal:
    name: "強気転換シグナル"
    description: "上昇トレンドの継続または転換を示すシグナル"
    allowed_environments: ["trending_market_bullish"]
    
    conditions:
      - name: "bullish_candle"
        indicator: "close"
        operator: ">"
        reference: "open"
        timeframe: "5m"
        weight: 0.4
      - name: "rsi_oversold_recovery"
        indicator: "RSI_14"
        operator: ">"
        value: 35
        timeframe: "5m"
        weight: 0.3
      - name: "momentum_bullish"
        indicator: "MACD"
        operator: ">"
        reference: "MACD_Signal"
        timeframe: "5m"
        weight: 0.3
    
    confidence_calculation:
      method: "weighted_average"
      min_confidence: 0.7
    required_conditions: ["bullish_candle"]
```

---

## データフロー

### イベント駆動アーキテクチャ
```
データ収集デーモン → イベント発行 → 分析システムルーター → 三層ゲート分析サービス
```

### 詳細フロー
1. **データ収集**: `standalone_data_collection_daemon.py`
   - 5分間隔でYahoo Finance APIからデータ取得
   - データベースに保存
   - `data_collection_completed`イベントを発行

2. **イベント監視**: `analysis_system_router.py`
   - データベースの`events`テーブルを監視
   - 未処理イベントを検出
   - 適切な分析サービスにルーティング

3. **三層ゲート分析**: `three_gate_analysis_service.py`
   - テクニカル指標計算
   - 三層ゲート評価実行
   - シグナル生成・保存

### データベーススキーマ
```sql
-- イベントテーブル
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    event_data JSONB,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 三層ゲートシグナルテーブル
CREATE TABLE three_gate_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    signal_type VARCHAR(10) NOT NULL,
    confidence DECIMAL(5,2) NOT NULL,
    entry_price DECIMAL(10,5) NOT NULL,
    stop_loss DECIMAL(10,5) NOT NULL,
    take_profit_1 DECIMAL(10,5),
    take_profit_2 DECIMAL(10,5),
    take_profit_3 DECIMAL(10,5),
    gate1_pattern VARCHAR(100),
    gate2_pattern VARCHAR(100),
    gate3_pattern VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 運用・監視

### システム起動
```bash
# データ収集デーモン起動
cd /app
nohup python modules/data_collection/daemon/standalone_data_collection_daemon.py > /tmp/data_collection.log 2>&1 &

# 分析システムルーター起動
nohup python modules/llm_analysis/scripts/analysis_system_router.py --mode three_gate > /tmp/analysis_system.log 2>&1 &

# 監視スクリプト起動
python modules/llm_analysis/scripts/continuous_monitor_v2.py
```

### 監視項目
1. **データ収集状況**
   - 最新データの取得時刻
   - データ品質スコア
   - エラー発生状況

2. **分析システム状況**
   - イベント処理数
   - シグナル生成数
   - 各ゲートの通過率

3. **パフォーマンス指標**
   - 平均処理時間
   - メモリ使用量
   - CPU使用率

### ログ管理
```bash
# ログローテーション
python modules/llm_analysis/scripts/log_manager.py --rotate

# ログ統計
python modules/llm_analysis/scripts/log_manager.py --stats

# ログクリア
python modules/llm_analysis/scripts/log_manager.py --clear
```

---

## トラブルシューティング

### よくある問題と解決方法

#### 1. シグナル生成過多
**症状**: 短時間で大量のシグナルが生成される
**原因**: 
- 信頼度閾値が低すぎる
- 必須条件が設定されていない
- シグナル間隔制限が機能していない

**解決方法**:
```yaml
# gate3_patterns.yaml
confidence_calculation:
  min_confidence: 0.7  # 0.6から0.7に引き上げ

required_conditions: ["bullish_candle"]  # 必須条件を追加
```

#### 2. テクニカル指標がNaN
**症状**: 指標値がNaNで条件評価が失敗
**原因**:
- 十分な履歴データがない
- データ型の不整合

**解決方法**:
```python
# technical_calculator.py
def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
    # データ型変換を確実に実行
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = df[col].astype(np.float64)
    
    # 欠損値処理
    df = df.fillna(method='ffill').fillna(method='bfill')
    return df
```

#### 3. 環境制限が機能しない
**症状**: 環境に合わないパターンが評価される
**原因**:
- 環境名の不一致
- 環境制限の設定ミス

**解決方法**:
```yaml
# gate3_patterns.yaml
allowed_environments: ["trending_market_bullish"]  # アンダースコア形式で統一
```

#### 4. ボリュームデータ警告
**症状**: Volumeデータが利用できませんの警告が大量出力
**原因**: Yahoo Finance APIの制限

**解決方法**:
```python
# technical_calculator.py
# 警告を非表示化（既に実装済み）
# self.logger.warning("⚠️ Volumeデータが利用できません（すべて0.0）")
```

### パフォーマンス最適化

#### 1. データベース接続プール
```python
# 接続プール設定
DATABASE_CONFIG = {
    'min_connections': 3,
    'max_connections': 10,
    'connection_timeout': 30
}
```

#### 2. パターン設定キャッシュ
```python
# pattern_loader.py
class PatternLoader:
    def __init__(self):
        self._cache = {}
        self._cache_ttl = 300  # 5分間キャッシュ
```

#### 3. 指標計算最適化
```python
# バッチ処理による効率化
def calculate_all_indicators(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """全時間足の指標を一括計算"""
    results = {}
    
    for timeframe, df in data_dict.items():
        # 並列処理で指標計算
        results[timeframe] = self._calculate_timeframe_indicators(df, timeframe)
    
    return results
```

---

## 今後の改善計画

### 短期改善（1-2週間）
1. **Discord通知機能の実装**
2. **設定ファイルの命名規則統一**
3. **データ不整合の修正**

### 中期改善（1-2ヶ月）
1. **動的リスク管理の実装**
2. **パターン判定精度の向上**
3. **信頼度計算の改善**

### 長期改善（3-6ヶ月）
1. **機械学習によるパターン最適化**
2. **マルチアセット対応**
3. **バックテスト機能の実装**

---

## まとめ

LLM分析モジュールは、階層的テクニカル分析と三層ゲート式フィルタリングを組み合わせた高度な取引シグナル生成システムです。イベント駆動アーキテクチャにより、リアルタイムでの市場分析とシグナル生成を実現しています。

システムの継続的な改善により、より高精度で実用的な取引シグナルの生成を目指しています。

---

**最終更新**: 2025年9月20日  
**バージョン**: 1.0.0  
**作成者**: AI Assistant
