# LLM分析モジュール (LLM Analysis Module)

## 使っている技術スタック

- **Python 3.8+**
- **OpenAI GPT-4**: メインLLMプロバイダー
- **Anthropic Claude**: 代替LLMプロバイダー
- **asyncio**: 非同期処理
- **aiohttp**: 非同期HTTP通信
- **PostgreSQL/TimescaleDB**: データベース
- **Discord Webhook**: 通知システム
- **YAML**: 設定ファイル管理
- **dataclasses**: データ構造定義
- **enum**: 列挙型管理
- **logging**: ログ管理
- **TA-Lib**: テクニカル指標計算
- **yfinance**: Yahoo Finance API
- **Fibonacci Retracement**: フィボナッチ分析

## 機能の概要

LLM（Large Language Model）を使用した包括的な市場分析システムです。データベースに蓄積された価格データを基に、AI技術を活用して市場センチメント、価格パターン、リスク評価、トレンド分析を実行し、売買シナリオを生成・Discord配信する高度な分析プラットフォームです。

**現在のシステム状況**:
- ✅ **イベント駆動アーキテクチャ**: データ収集完了時に自動でテクニカル分析を実行
- ✅ **階層的テクニカル分析**: D1/H4（トレンド）、H1（ゾーン）、M5（タイミング）の3段階分析
- ✅ **ルールベース売買システム**: 5つのアクティブルールによる自動シグナル生成
- ✅ **リアルタイム監視**: 継続的監視ツールによるシステム状況の可視化
- ✅ **Discord通知**: シナリオ作成、エントリー/エグジットシグナルの自動通知

## 背景・目的

### 背景
- 為替分析アプリケーションに必要な高度な市場分析
- 大量の市場データの効率的な解釈と分析
- 人間の判断を補完するAI技術の活用
- リアルタイムでの市場状況の把握と通知
- ルールベース売買システムとの連携

### 目的
- AI技術を活用した高精度な市場分析
- 複数の分析タイプの統合と最適化
- 分析結果の品質管理と信頼性向上
- リアルタイム通知とレポート配信
- 継続的な分析パフォーマンスの改善

## コンポーネント設計

### 1. LLM分析サービス (`LLMAnalysisService`)
```python
# 統合分析サービス
- 複数分析タイプの管理
- データベース連携
- 品質管理統合
- ヘルスチェック機能
```

### 2. 分析エンジン (`AnalysisEngine`)
```python
# 分析実行エンジン
- 包括的分析
- センチメント分析
- パターン分析
- リスク分析
```

### 3. LLMクライアント (`LLMClient`)
```python
# LLM API通信
- 複数プロバイダー対応
- 非同期通信
- レート制限管理
- エラーハンドリング
```

### 4. データ準備器 (`LLMDataPreparator`)
```python
# 分析データ準備
- 価格データ統合
- テクニカル指標計算
- データ検証
- 品質チェック
- 階層的分析データ準備
```

### 5. 品質管理コントローラー (`QualityController`)
```python
# 品質管理
- 分析結果評価
- 信頼度スコア計算
- 品質レポート生成
- 改善提案
```

### 6. Discord通知システム (`DiscordNotifier`)
```python
# 通知配信
- シナリオ通知
- シグナル通知
- レポート配信
- エラーアラート
```

### 7. テクニカル分析サービス (`TechnicalAnalysisService`)
```python
# テクニカル分析サービス
- イベント駆動分析
- ルールエンジン連携
- シナリオ管理
- Discord通知
```

### 8. ルールエンジン (`RuleBasedEngine`)
```python
# ルールベース売買エンジン
- エントリー条件評価
- エグジット条件評価
- 5つのアクティブルール
- 信頼度スコア計算
```

### 9. シナリオ管理 (`ScenarioManager`)
```python
# シナリオ管理システム
- シナリオライフサイクル管理
- エントリー/エグジット実行
- ステータス追跡
- 有効期限管理
```

### 10. 設定管理 (`LLMAnalysisSettings`)
```python
# 設定管理
- LLM設定
- 分析設定
- データ準備設定
- 品質管理設定
```

## できること・制限事項

### できること
- **包括的市場分析**: センチメント、パターン、リスク、トレンドの統合分析
- **複数LLMプロバイダー対応**: OpenAI、Anthropic、Google等の柔軟な選択
- **イベント駆動分析**: データ収集完了時の自動テクニカル分析実行
- **階層的テクニカル分析**: D1/H4（トレンド）、H1（ゾーン）、M5（タイミング）の3段階分析
- **ルールベース売買**: 5つのアクティブルールによる自動シグナル生成
- **シナリオ管理**: エントリーからエグジットまでの完全なライフサイクル管理
- **品質管理**: 分析結果の自動品質評価と改善提案
- **Discord通知**: リッチな埋め込みメッセージでの通知配信
- **リアルタイム監視**: 継続的監視ツールによるシステム状況の可視化
- **履歴分析**: 過去データに基づく分析とトレンド予測
- **バッチ処理**: 複数シンボル・時間軸の並行分析
- **オンデマンド分析**: 必要に応じた即座の分析実行
- **パフォーマンス監視**: 分析品質とシステム状態の監視

### 制限事項
- **LLM API依存**: 外部APIの制限とコストに依存
- **データ品質依存**: 入力データの品質が分析結果に影響
- **処理時間**: 複雑な分析には時間がかかる場合がある
- **API制限**: LLMプロバイダーのレート制限
- **コスト制限**: API使用料金の制限
- **言語制限**: 主に英語での分析に最適化

## コンポーネント使用時のオプション

### LLMプロバイダー設定
```python
# OpenAI設定
llm_config = LLMConfig(
    provider=LLMProvider.OPENAI,
    model_name="gpt-4",
    max_tokens=4000,
    temperature=0.1
)

# Anthropic設定
llm_config = LLMConfig(
    provider=LLMProvider.ANTHROPIC,
    model_name="claude-3-sonnet",
    max_tokens=4000,
    temperature=0.1
)
```

### 分析タイプ設定
```python
# 分析タイプ
analysis_types = [
    AnalysisType.MARKET_SENTIMENT,    # 市場センチメント
    AnalysisType.PRICE_PATTERN,       # 価格パターン
    AnalysisType.RISK_ASSESSMENT,     # リスク評価
    AnalysisType.TREND_ANALYSIS       # トレンド分析
]
```

### 分析頻度設定
```python
# 分析頻度
frequencies = [
    AnalysisFrequency.REAL_TIME,      # リアルタイム
    AnalysisFrequency.HOURLY,         # 時間別
    AnalysisFrequency.DAILY,          # 日別
    AnalysisFrequency.WEEKLY,         # 週別
    AnalysisFrequency.ON_DEMAND       # オンデマンド
]
```

### データ準備設定
```python
# データ準備設定
data_config = DataPreparationConfig(
    enable_data_aggregation=True,
    aggregation_window_minutes=60,
    enable_outlier_detection=True,
    outlier_threshold=3.0,
    enable_missing_data_interpolation=True,
    interpolation_method="linear"
)
```

### 品質管理設定
```python
# 品質管理設定
quality_config = QualityControlConfig(
    enable_quality_scoring=True,
    quality_threshold=0.8,
    enable_consistency_check=True,
    consistency_threshold=0.9
)
```

### Discord通知設定
```python
# Discord通知設定
notification_settings = {
    "scenario_created": True,
    "rule_evaluation": True,
    "entry_signals": True,
    "exit_signals": True,
    "daily_reports": True,
    "weekly_reports": True,
    "error_alerts": True
}
```

## 関連ファイル・ディレクトリ構造

```
/app/modules/llm_analysis/
├── main.py                          # メインスクリプト
├── config/
│   ├── settings.py                  # 設定管理
│   └── rules.yaml                   # ルールベース設定
├── core/
│   ├── llm_analysis_service.py      # メインサービス
│   ├── technical_analysis_service.py # テクニカル分析サービス
│   ├── analysis_engine/             # 分析エンジン
│   │   ├── analysis_engine.py
│   │   ├── market_analyzer.py
│   │   ├── pattern_analyzer.py
│   │   ├── risk_analyzer.py
│   │   └── sentiment_analyzer.py
│   ├── llm_client/                  # LLMクライアント
│   │   ├── llm_client.py
│   │   ├── openai_client.py
│   │   └── anthropic_client.py
│   ├── data_preparation/            # データ準備
│   │   ├── data_preparator.py
│   │   ├── data_validator.py
│   │   └── feature_engineer.py
│   ├── quality_control/             # 品質管理
│   │   ├── quality_controller.py
│   │   ├── quality_metrics.py
│   │   └── quality_validator.py
│   ├── rule_engine.py               # ルールエンジン
│   ├── scenario_manager.py          # シナリオ管理
│   ├── technical_calculator.py      # テクニカル指標計算
│   ├── snapshot_manager.py          # スナップショット管理
│   └── trading_pipeline.py          # 取引パイプライン
├── notification/                    # 通知システム
│   ├── discord_notifier.py
│   └── message_formatter.py
├── evaluation/                      # 評価システム
│   └── daily_evaluator.py
├── llm/                            # LLM処理
│   ├── llm_analyzer.py
│   ├── language_processor.py
│   ├── journal_generator.py
│   └── improvement_advisor.py
├── providers/                      # データプロバイダー
│   ├── base_provider.py
│   ├── oanda_stream_client.py
│   └── yahoo_finance_stream_client.py
├── services/                       # サービス層
│   └── analysis_service.py         # 分析サービス
├── orchestration/                  # オーケストレーション
│   └── trading_pipeline.py         # 取引パイプライン統合
├── tests/                          # テストファイル
│   ├── test_llm_analyzer.py
│   ├── test_analysis_engine.py
│   ├── test_discord_notifier.py
│   ├── test_rule_engine.py
│   ├── test_technical_calculator.py
│   └── test_technical_values.py
├── LLM分析モジュール仕様書.md        # 詳細仕様書
└── ルールベース売買システム仕様書.md  # ルール仕様書
```

## 注意点

### 運用時の注意点
1. **API制限**: LLMプロバイダーのレート制限を超えないよう注意
2. **コスト管理**: API使用料金の監視と予算管理
3. **データ品質**: 入力データの品質が分析結果に直接影響
4. **分析頻度**: 過度な分析によるAPI制限の回避
5. **通知設定**: Discord通知の適切な設定とスパム防止

### 開発時の注意点
1. **非同期処理**: asyncioの適切な使用とリソース管理
2. **エラーハンドリング**: LLM APIの不安定性への対応
3. **設定管理**: 環境変数と設定ファイルの適切な管理
4. **テスト**: モックを使用したAPI制限のテスト
5. **ログ管理**: 詳細なログ出力とデバッグ情報

### セキュリティ考慮事項
1. **API認証**: LLM APIキーの適切な管理と保護
2. **データ保護**: 分析データの機密性確保
3. **アクセス制御**: Discord Webhookの適切な設定
4. **ログ情報**: 機密情報のログ出力回避
5. **通信暗号化**: HTTPS通信の確保

### パフォーマンス考慮事項
1. **並列処理**: 複数分析の効率的な並行実行
2. **キャッシュ**: 分析結果の適切なキャッシュ管理
3. **リソース管理**: メモリとCPU使用量の最適化
4. **データベース**: 効率的なクエリとインデックス活用
5. **API最適化**: リクエスト頻度とバッチ処理の最適化

### LLM特有の注意点
1. **プロンプト設計**: 効果的なプロンプトエンジニアリング
2. **コンテキスト管理**: トークン制限内での効率的な情報伝達
3. **出力解析**: LLM出力の構造化と検証
4. **品質評価**: 分析結果の客観的な品質評価
5. **バイアス対策**: LLMの潜在的バイアスへの対応

### ルールベース連携の注意点
1. **ルール整合性**: 分析結果とルールの整合性確保
2. **シグナル品質**: エントリーシグナルの信頼性管理
3. **リスク管理**: 分析結果に基づくリスク評価
4. **パフォーマンス追跡**: 分析精度と取引結果の相関
5. **継続改善**: 分析結果に基づくルールの最適化

## 現在のシステム運用状況

### 起動中のプロセス
1. **データ収集デーモン** (`start_event_driven_system.py`)
   - 5分間隔でデータ収集
   - イベント駆動でテクニカル分析実行
   - シナリオ作成とDiscord通知

2. **継続的監視ツール** (`continuous_monitor.py`)
   - 10秒間隔でシステム状況を監視
   - 日本時間表示でリアルタイム監視
   - データ更新状況の可視化

### アクティブルール
- **pullback_buy**: 押し目買い（RSI ≤ 40, 価格 > EMA200）
- **reversal_sell**: 逆張り売り（RSI ≥ 70, 価格 < EMA200）
- **trend_follow_sell**: 下降トレンドフォロー売り
- **strong_downtrend_sell**: 強い下降トレンド売り（RSI 25-40）

### 監視内容
- 📈 **データ収集状況**: 各時間足の最新データ時刻
- 📢 **イベント処理**: データ収集完了イベントの処理状況
- 🔍 **分析結果**: テクニカル分析の実行結果
- 🎯 **シナリオ状況**: 作成されたシナリオの情報
- 💚 **システムヘルス**: 全体的なシステムの健全性

---

**作成日**: 2025年1月4日  
**最終更新**: 2025年9月18日  
**バージョン**: 2.0  
**対象モジュール**: `/app/modules/llm_analysis`
