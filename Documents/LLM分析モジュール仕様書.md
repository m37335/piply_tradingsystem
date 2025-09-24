# LLM分析モジュール仕様書

**作成日**: 2025年1月4日  
**バージョン**: v1.0  
**対象モジュール**: LLM分析モジュール  
**目的**: データベース連携型LLM分析システムの完全仕様

---

## 📋 目次

1. [モジュール概要](#1-モジュール概要)
2. [アーキテクチャ設計](#2-アーキテクチャ設計)
3. [機能仕様](#3-機能仕様)
4. [データフロー](#4-データフロー)
5. [API仕様](#5-api仕様)
6. [設定仕様](#6-設定仕様)
7. [実装計画](#7-実装計画)
8. [品質要件](#8-品質要件)

---

## 1. モジュール概要

### 1.1 目的
データベースに蓄積されたUSD/JPY価格データを基に、LLM（Large Language Model）を使用して市場分析を行い、売買シナリオを生成・Discord配信するシステム。

### 1.2 主要機能
- **データベース連携**: TimescaleDBから複数時間足データを取得
- **階層的テクニカル分析**: 大局（D1・H4）→戦術（H1）→執行（M5）の3段階分析
- **トレンド補強システム**: 全指標をトレンド判断補強に特化
- **LLM分析**: OpenAI GPT-4、Anthropic Claudeによる市場解釈
- **シナリオ生成**: ENTRY PROPOSAL / OBSERVE判定とシナリオ構築
- **Discord配信**: 構造化されたメッセージでの通知

### 1.3 運用方針
1. **大局（D1・H4）で方向性を判断** - 主要トレンドの方向性を確定
2. **戦術（H1）でゾーンを決定** - エントリーゾーンの特定
3. **執行（M5）でタイミングを計る** - エントリータイミングの最適化
4. **すべての指標は「トレンド判断を補強する目的」で使う** - トレンドの強度・継続性の確認
5. **逆張りは必ず上位足の反転サインと一致する場面のみに限定** - 逆張りの安全性確保

### 1.4 対象市場
- **通貨ペア**: USD/JPY
- **時間足**: 5m, 15m, 1h, 4h, 1d
- **分析頻度**: 5分間隔（M5足ベース）

---

## 2. アーキテクチャ設計

### 2.1 モジュール構造
```
modules/llm_analysis/
├── core/                          # コア機能
│   ├── data_preparator.py         # データ準備器
│   ├── technical_calculator.py    # テクニカル指標計算器
│   ├── llm_analyzer.py           # LLM分析エンジン
│   └── scenario_generator.py     # シナリオ生成器
├── providers/                     # LLMプロバイダー
│   ├── openai_client.py          # OpenAI API
│   ├── anthropic_client.py       # Anthropic API
│   └── base_llm_provider.py      # 共通インターフェース
├── notification/                  # 通知システム
│   ├── discord_notifier.py       # Discord配信
│   └── message_formatter.py      # メッセージフォーマット
├── config/                        # 設定管理
│   ├── analysis_config.yaml      # 分析設定
│   └── prompt_templates.json     # プロンプトテンプレート
├── orchestration/                 # オーケストレーション
│   └── analysis_pipeline.py      # 分析パイプライン
└── tests/                         # テスト
    ├── test_data_preparator.py
    ├── test_technical_calculator.py
    ├── test_llm_analyzer.py
    └── test_scenario_generator.py
```

### 2.2 主要コンポーネント

#### 2.2.1 データ準備器 (DataPreparator)
```python
class LLMDataPreparator:
    """LLM分析用データ準備器"""
    
    async def prepare_analysis_data(
        self, 
        analysis_type: str,
        symbol: str = 'USDJPY=X',
        timeframes: List[str] = ['5m', '15m', '1h', '4h', '1d']
    ) -> Dict:
        """分析用データの準備"""
```

#### 2.2.2 テクニカル指標計算器 (TechnicalCalculator)
```python
class TechnicalIndicatorCalculator:
    """テクニカル指標計算器"""
    
    def calculate_indicators(self, data: pd.DataFrame) -> Dict:
        """主要テクニカル指標を計算"""
```

#### 2.2.3 LLM分析エンジン (LLMAnalyzer)
```python
class LLMAnalyzer:
    """LLM分析エンジン"""
    
    async def analyze_market_sentiment(self, data: Dict) -> Dict:
        """市場センチメント分析"""
    
    async def generate_trading_scenario(self, analysis: Dict) -> Dict:
        """売買シナリオ生成"""
```

#### 2.2.4 Discord通知システム (DiscordNotifier)
```python
class DiscordNotifier:
    """Discord通知システム"""
    
    async def send_trading_proposal(self, scenario: Dict) -> None:
        """ENTRY PROPOSAL配信"""
    
    async def send_observation(self, analysis: Dict) -> None:
        """OBSERVE配信"""
```

---

## 3. 機能仕様

### 3.1 Stage 1: データベースからデータ取得

#### 3.1.1 機能概要
- TimescaleDBから複数時間足の価格データを取得
- 分析タイプに応じたデータ範囲の最適化
- データ品質チェックと前処理

#### 3.1.2 取得データ仕様
```python
# 取得データ構造
{
    "symbol": "USDJPY=X",
    "timeframes": {
        "5m": {
            "data": pd.DataFrame,  # OHLCV + テクニカル指標
            "count": int,          # データ件数
            "latest": datetime,    # 最新時刻
            "range": (start, end)  # データ範囲
        },
        "15m": {...},
        "1h": {...},
        "4h": {...},
        "1d": {...}
    },
    "metadata": {
        "analysis_type": str,      # 分析タイプ
        "lookback_hours": int,     # 遡及時間
        "data_quality": float      # データ品質スコア
    }
}
```

#### 3.1.3 分析タイプ別設定
```yaml
analysis_types:
  market_sentiment:
    timeframes: ['5m', '15m', '1h']
    lookback_hours: 24
    max_data_points: 1000
    
  pattern_interpretation:
    timeframes: ['15m', '1h', '4h']
    lookback_hours: 72
    max_data_points: 500
    
  risk_scenario:
    timeframes: ['1h', '4h', '1d']
    lookback_hours: 168
    max_data_points: 200
```

### 3.2 Stage 2: 階層的テクニカル指標計算

#### 3.2.1 運用方針に基づく指標設計

##### 3.2.1.1 大局判断指標（D1・H4）
```python
TREND_DIRECTION_INDICATORS = {
    "D1": {
        "EMA_21": 21,        # 短期トレンド
        "EMA_55": 55,        # 中期トレンド
        "EMA_200": 200,      # 長期トレンド
        "MACD": (12, 26, 9), # トレンド転換
        "ATR_14": 14,        # ボラティリティ
        "RSI_14": 14         # オーバーボート/オーバーソール
    },
    "H4": {
        "EMA_21": 21,        # 短期トレンド
        "EMA_55": 55,        # 中期トレンド
        "MACD": (12, 26, 9), # トレンド転換
        "ATR_14": 14,        # ボラティリティ
        "RSI_14": 14,        # オーバーボート/オーバーソール
        "Bollinger": (20, 2.0) # 価格帯
    }
}
```

##### 3.2.1.2 戦術判断指標（H1）
```python
ZONE_DECISION_INDICATORS = {
    "H1": {
        "EMA_21": 21,        # 短期トレンド
        "EMA_55": 55,        # 中期トレンド
        "MACD": (12, 26, 9), # トレンド転換
        "ATR_14": 14,        # ボラティリティ
        "RSI_14": 14,        # オーバーボート/オーバーソール
        "Bollinger": (20, 2.0), # 価格帯
        "Stochastic": (14, 3, 3), # モメンタム
        "Williams_R": 14     # 追加モメンタム
    }
}
```

##### 3.2.1.3 執行判断指標（M5）
```python
TIMING_EXECUTION_INDICATORS = {
    "M5": {
        "EMA_21": 21,        # 短期トレンド
        "RSI_14": 14,        # オーバーボート/オーバーソール
        "RSI_7": 7,          # 短期RSI（敏感）
        "Stochastic": (14, 3, 3), # モメンタム
        "Williams_R": 14,    # 追加モメンタム
        "ATR_14": 14,        # ボラティリティ
        "Volume_SMA_20": 20  # ボリューム確認
    }
}
```

#### 3.2.2 トレンド判断補強システム

##### 3.2.2.1 トレンド強度判定
```python
TREND_STRENGTH_ANALYSIS = {
    "trend_alignment": {
        "D1_EMA_21": "D1のEMA21の傾き",
        "H4_EMA_21": "H4のEMA21の傾き",
        "H1_EMA_21": "H1のEMA21の傾き",
        "M5_EMA_21": "M5のEMA21の傾き"
    },
    "trend_consistency": {
        "all_bullish": "全時間足で上昇トレンド",
        "all_bearish": "全時間足で下降トレンド",
        "mixed": "時間足間でトレンドが混在"
    },
    "trend_strength": {
        "strong": "全時間足で一致",
        "medium": "上位3時間足で一致",
        "weak": "上位2時間足で一致"
    }
}
```

##### 3.2.2.2 逆張り条件判定
```python
COUNTER_TREND_CONDITIONS = {
    "upper_timeframe_reversal": {
        "D1": "D1で反転サイン",
        "H4": "H4で反転サイン",
        "H1": "H1で反転サイン"
    },
    "lower_timeframe_confirmation": {
        "M5": "M5でエントリータイミング",
        "M15": "M15でエントリータイミング"
    },
    "risk_management": {
        "stop_loss": "上位足の反転サイン無効化",
        "position_size": "上位足の信頼度に応じたサイズ調整"
    }
}
```

#### 3.2.3 エントリー条件の階層化
```python
ENTRY_CONDITION_HIERARCHY = {
    "level_1": {
        "timeframe": "D1",
        "condition": "主要トレンド方向の確定",
        "weight": 40
    },
    "level_2": {
        "timeframe": "H4",
        "condition": "中期トレンドの確認",
        "weight": 30
    },
    "level_3": {
        "timeframe": "H1",
        "condition": "エントリーゾーンの特定",
        "weight": 20
    },
    "level_4": {
        "timeframe": "M5",
        "condition": "エントリータイミング",
        "weight": 10
    }
}
```

### 3.3 Stage 3: LLM分析・シナリオ作成

#### 3.3.1 分析タイプ

##### 3.3.1.1 市場センチメント分析
```python
async def analyze_market_sentiment(self, data: Dict) -> Dict:
    """市場センチメント分析"""
    return {
        "sentiment_score": float,      # -100 to +100
        "confidence": float,           # 0 to 100
        "key_observations": List[str], # 主要観察事項
        "risk_factors": List[str],     # リスク要因
        "recommendation": str          # 推奨アクション
    }
```

##### 3.3.1.2 パターン解釈分析
```python
async def interpret_patterns(self, data: Dict) -> Dict:
    """パターン解釈分析"""
    return {
        "pattern_type": str,           # パターンタイプ
        "pattern_strength": float,     # パターン強度
        "breakout_probability": float, # ブレイクアウト確率
        "target_levels": List[float],  # 目標レベル
        "stop_levels": List[float]     # ストップロスレベル
    }
```

##### 3.3.1.3 リスクシナリオ分析
```python
async def analyze_risk_scenarios(self, data: Dict) -> Dict:
    """リスクシナリオ分析"""
    return {
        "risk_level": str,             # LOW/MEDIUM/HIGH
        "scenarios": List[Dict],       # リスクシナリオ
        "mitigation_strategies": List[str], # 軽減戦略
        "position_sizing": Dict        # ポジションサイジング
    }
```

#### 3.3.2 シナリオ生成
```python
async def generate_trading_scenario(self, analysis: Dict) -> Dict:
    """売買シナリオ生成"""
    return {
        "action": str,                 # ENTRY/OBSERVE/SKIP
        "direction": str,              # BUY/SELL
        "entry_price": float,          # エントリー価格
        "stop_loss": float,            # ストップロス
        "take_profit": List[float],    # 利確レベル
        "probability": float,          # 成功確率
        "risk_reward": float,          # リスクリワード比
        "reasoning": str,              # 判断根拠
        "time_horizon": int            # 時間軸（分）
    }
```

### 3.4 Stage 4: Discord配信

#### 3.4.1 メッセージタイプ

##### 3.4.1.1 ENTRY PROPOSAL
```python
ENTRY_PROPOSAL_FORMAT = """
🟢 **ENTRY PROPOSAL** 🟢
📊 **USD/JPY** | {timeframe}
⏰ **時刻**: {timestamp}

🎯 **エントリー**: {direction} @ {entry_price}
🛑 **SL**: {stop_loss} ({sl_pips} pips)
💰 **TP1**: {tp1} ({tp1_pips} pips)
💰 **TP2**: {tp2} ({tp2_pips} pips)
💰 **TP3**: {tp3} ({tp3_pips} pips)

📈 **確率**: {probability}% | **RR**: {risk_reward}
⏱️ **時間軸**: {time_horizon}分

💡 **根拠**: {reasoning}

🔍 **テクニカル**: {technical_summary}
⚠️ **リスク**: {risk_factors}
"""
```

##### 3.4.1.2 OBSERVE
```python
OBSERVE_FORMAT = """
🟡 **OBSERVE** 🟡
📊 **USD/JPY** | {timeframe}
⏰ **時刻**: {timestamp}

👀 **観察ポイント**: {observation_points}
📈 **次のシグナル**: {next_signal_conditions}
⏱️ **観察期間**: {observation_duration}

💡 **分析**: {analysis_summary}
⚠️ **注意事項**: {risk_factors}
"""
```

#### 3.4.2 配信ルール
- **ENTRY PROPOSAL**: 確率 ≥ 58% かつ RR ≥ 1.30
- **OBSERVE**: 確率 45-57% または 不確実性が高い場合
- **SKIP**: 確率 < 45% または リスクが高い場合

---

## 4. データフロー

### 4.1 階層的分析パイプライン
```
データベース → データ準備 → 階層的テクニカル指標 → LLM分析 → シナリオ生成 → Discord配信
     ↓              ↓              ↓                    ↓           ↓
   USDJPY=X     複数時間足      大局→戦術→執行        市場分析     ENTRY/OBSERVE   通知配信
                                    ↓
                              トレンド補強システム
                                    ↓
                              逆張り条件判定
```

### 4.2 階層的処理フロー
1. **トリガー**: 5分間隔でのスケジューリング
2. **データ取得**: 最新データの取得・品質チェック
3. **階層的指標計算**: 
   - 大局判断（D1・H4）: トレンド方向の確定
   - 戦術判断（H1）: エントリーゾーンの特定
   - 執行判断（M5）: エントリータイミングの最適化
4. **トレンド補強分析**: 時間足間の整合性チェック
5. **逆張り条件判定**: 上位足反転サインの確認
6. **LLM分析**: 複数プロバイダーでの並列分析
7. **シナリオ生成**: 分析結果の統合・判定
8. **配信判定**: 閾値チェック・重複抑制
9. **Discord配信**: 構造化メッセージの送信

### 4.3 エラーハンドリング
- **データ取得エラー**: キャッシュデータの使用
- **LLM APIエラー**: フォールバックプロバイダー
- **配信エラー**: リトライ・アラート通知

---

## 5. API仕様

### 5.1 LLMプロバイダーAPI

#### 5.1.1 OpenAI API
```python
class OpenAIClient:
    async def analyze_market(
        self, 
        prompt: str, 
        data: Dict
    ) -> Dict:
        """OpenAI GPT-4での市場分析"""
```

#### 5.1.2 Anthropic API
```python
class AnthropicClient:
    async def analyze_market(
        self, 
        prompt: str, 
        data: Dict
    ) -> Dict:
        """Anthropic Claudeでの市場分析"""
```

### 5.2 Discord API
```python
class DiscordNotifier:
    async def send_message(
        self, 
        channel_id: str, 
        message: str, 
        embed: Dict = None
    ) -> bool:
        """Discordメッセージ送信"""
```

---

## 6. 設定仕様

### 6.1 分析設定 (analysis_config.yaml)
```yaml
# LLM分析設定
llm:
  openai:
    model: "gpt-4o"
    max_tokens: 2000
    temperature: 0.3
    timeout: 30
    
  anthropic:
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 2000
    temperature: 0.3
    timeout: 30

# 階層的分析設定
analysis_types:
  trend_direction:
    enabled: true
    frequency: "M5"
    provider: "openai"
    timeframes: ['1d', '4h']  # 大局判断
    lookback_hours: 168
    indicators: ['EMA_21', 'EMA_55', 'EMA_200', 'MACD', 'ATR_14', 'RSI_14']
    
  zone_decision:
    enabled: true
    frequency: "M5"
    provider: "anthropic"
    timeframes: ['1h']  # 戦術判断
    lookback_hours: 72
    indicators: ['EMA_21', 'EMA_55', 'MACD', 'ATR_14', 'RSI_14', 'Bollinger', 'Stochastic', 'Williams_R']
    
  timing_execution:
    enabled: true
    frequency: "M5"
    provider: "openai"
    timeframes: ['5m']  # 執行判断
    lookback_hours: 24
    indicators: ['EMA_21', 'RSI_14', 'RSI_7', 'Stochastic', 'Williams_R', 'ATR_14', 'Volume_SMA_20']
    
  trend_reinforcement:
    enabled: true
    frequency: "M5"
    provider: "anthropic"
    timeframes: ['5m', '15m', '1h', '4h', '1d']  # 全時間足
    lookback_hours: 24
    indicators: ['EMA_21', 'MACD', 'ATR_14', 'RSI_14']

# コスト管理
cost_management:
  daily_limit_usd: 50.0
  monthly_limit_usd: 1000.0
  alert_threshold_percent: 80.0

# Discord設定
discord:
  webhook_url: "${DISCORD_WEBHOOK_URL}"
  channel_id: "${DISCORD_CHANNEL_ID}"
  thread_creation: true
  message_formatting: true
```

### 6.2 プロンプトテンプレート (prompt_templates.json)
```json
{
  "trend_direction": {
    "system_prompt": "あなたは経験豊富な為替トレーダーです。USD/JPYの大局的なトレンド方向を分析してください。D1・H4のデータを基に主要トレンドの方向性を確定することが重要です。",
    "user_prompt_template": "以下のUSD/JPY大局データ（D1・H4）を分析してください：\n\n{data_summary}\n\n分析結果を以下の形式で出力してください：\n- 主要トレンド方向（BULLISH/BEARISH/SIDEWAYS）\n- トレンド強度（0から100）\n- 信頼度（0から100）\n- 主要観察事項（3つまで）\n- リスク要因（3つまで）\n- 推奨アクション"
  },
  "zone_decision": {
    "system_prompt": "あなたはテクニカル分析の専門家です。H1データを基にエントリーゾーンを特定してください。大局トレンドに沿ったゾーン決定が重要です。",
    "user_prompt_template": "以下のUSD/JPY戦術データ（H1）を分析してください：\n\n{data_summary}\n\n分析結果を以下の形式で出力してください：\n- エントリーゾーン（BUY_ZONE/SELL_ZONE/WAIT）\n- ゾーン強度（0から100）\n- エントリー確率（0から100）\n- 目標レベル（3つまで）\n- ストップロスレベル\n- ゾーン根拠"
  },
  "timing_execution": {
    "system_prompt": "あなたはエントリータイミングの専門家です。M5データを基に最適なエントリータイミングを特定してください。上位足のトレンドに沿ったタイミングが重要です。",
    "user_prompt_template": "以下のUSD/JPY執行データ（M5）を分析してください：\n\n{data_summary}\n\n分析結果を以下の形式で出力してください：\n- エントリータイミング（NOW/WAIT/SKIP）\n- タイミング強度（0から100）\n- エントリー確率（0から100）\n- エントリー価格\n- ストップロス価格\n- 利確価格（3つまで）\n- タイミング根拠"
  },
  "trend_reinforcement": {
    "system_prompt": "あなたはトレンド分析の専門家です。全時間足のデータを基にトレンドの補強状況を分析してください。時間足間の整合性が重要です。",
    "user_prompt_template": "以下のUSD/JPY全時間足データを分析してください：\n\n{data_summary}\n\n分析結果を以下の形式で出力してください：\n- トレンド整合性（STRONG/MEDIUM/WEAK）\n- 補強強度（0から100）\n- 信頼度（0から100）\n- 整合性観察事項（3つまで）\n- 不整合リスク（3つまで）\n- 推奨アクション"
  }
}
```

---

## 7. 実装計画

### 7.1 Phase 1: 基盤構築（1週間）
- [ ] モジュール構造の作成
- [ ] データ準備器の実装
- [ ] 階層的テクニカル指標計算器の実装
- [ ] トレンド補強システムの実装
- [ ] 基本テストの実装

### 7.2 Phase 2: 階層的分析エンジン（2週間）
- [ ] 大局判断エンジン（D1・H4）
- [ ] 戦術判断エンジン（H1）
- [ ] 執行判断エンジン（M5）
- [ ] トレンド整合性チェック機能
- [ ] 逆張り条件判定機能

### 7.3 Phase 3: LLM分析エンジン（2週間）
- [ ] OpenAI API連携
- [ ] Anthropic API連携
- [ ] 階層的プロンプトエンジンの実装
- [ ] 分析結果の構造化
- [ ] トレンド補強分析の実装

### 7.4 Phase 4: シナリオ生成（1週間）
- [ ] 階層的シナリオ生成ロジック
- [ ] エントリー条件の階層化判定
- [ ] 逆張り条件の実装
- [ ] 品質管理システム

### 7.5 Phase 5: Discord配信（1週間）
- [ ] Discord API連携
- [ ] 階層的分析結果のメッセージフォーマッター
- [ ] 配信ルールの実装
- [ ] トレンド補強情報の配信

### 7.6 Phase 6: 統合・最適化（1週間）
- [ ] 階層的パイプライン統合
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング強化
- [ ] 統合テスト
- [ ] 運用方針の検証

---

## 8. 品質要件

### 8.1 パフォーマンス要件
- **分析時間**: 30秒以内
- **データ取得**: 5秒以内
- **LLM応答**: 20秒以内
- **配信時間**: 5秒以内

### 8.2 可用性要件
- **システム可用性**: 99.5%以上
- **データ可用性**: 99.9%以上
- **API可用性**: 99.0%以上

### 8.3 品質要件
- **分析精度**: 60%以上
- **配信精度**: 95%以上
- **エラー率**: 1%以下

### 8.4 セキュリティ要件
- **API キー管理**: 環境変数での管理
- **データ暗号化**: 通信の暗号化
- **アクセス制御**: 適切な権限管理

---

## 9. 監視・ログ

### 9.1 監視項目
- **分析実行時間**: 各ステージの処理時間
- **LLM API使用量**: トークン数・コスト
- **配信成功率**: Discord配信の成功率
- **エラー率**: 各コンポーネントのエラー率

### 9.2 ログ仕様
```python
# ログレベル
LOGGING_LEVELS = {
    "DEBUG": "詳細なデバッグ情報",
    "INFO": "一般的な情報",
    "WARNING": "警告情報",
    "ERROR": "エラー情報",
    "CRITICAL": "重大なエラー"
}

# ログ出力項目
LOG_FIELDS = [
    "timestamp", "level", "module", "function", 
    "message", "data", "execution_time", "cost"
]
```

---

## 10. テスト戦略

### 10.1 テスト階層
- **単体テスト**: 各コンポーネントの個別テスト
- **統合テスト**: コンポーネント間の連携テスト
- **E2Eテスト**: 全体フローのテスト
- **パフォーマンステスト**: 負荷・応答時間テスト

### 10.2 テストカバレッジ
- **コードカバレッジ**: 80%以上
- **機能カバレッジ**: 100%
- **APIカバレッジ**: 100%

---

**文書管理情報**

- 文書ID: LLM-ANALYSIS-SPEC-001
- バージョン: v1.0
- 作成日: 2025-01-04
- 承認者: [システム設計者]
- 次回レビュー予定: 2025-02-04
