# 為替分析アプリ 設計書

## 1. プロジェクト概要

### アプリケーション名

**Exchange Analytics** (exchangeApp)

### 目的

リアルタイムの為替データを取得・分析し、投資判断をサポートする Web アプリケーション

### 主な機能

- リアルタイム為替レート取得・表示
- 過去データの分析とチャート表示
- テクニカル指標の計算・可視化
- 価格アラート機能
- **AI 市場分析レポート生成** (ChatGPT API)
- **自動レポートの Discord 配信**
- Discord 通知機能
- データのエクスポート機能

## 2. システム構成

### 技術スタック

- **Backend**: Python Flask
- **Frontend**: HTML5 + CSS3 + JavaScript (Chart.js)
- **Database**: SQLite (開発) / PostgreSQL (本番)
- **External APIs**:
  - Alpha Vantage API (為替データ)
  - Yahoo Finance API (補助データ)
  - OpenAI ChatGPT API (市場分析レポート生成)
- **通知**: Discord Webhook
- **デプロイ**: Docker + GitHub Actions

### アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │  External APIs  │
│  (Chart.js)     │◄──►│   (Backend)     │◄──►│ (Alpha Vantage) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                       ┌─────────────────┐
                       │   Database      │
                       │  (SQLite/PG)    │
                       └─────────────────┘
                              │
                       ┌─────────────────┐
                       │ Discord Webhook │
                       │   (通知機能)     │
                       └─────────────────┘
```

## 3. 機能詳細設計

### 3.1 データ取得・管理

#### 対象通貨ペア

- **主要ペア**: USD/JPY, EUR/JPY, GBP/JPY, AUD/JPY
- **クロスペア**: EUR/USD, GBP/USD, AUD/USD
- **仮想通貨**: BTC/USD, ETH/USD (オプション)

#### データ取得仕様

- **リアルタイム**: 1 分間隔で最新レート取得
- **履歴データ**: 過去 1 年分の日次・時間足データ
- **データ保存**: ローカル DB に蓄積して API 呼び出し回数を最適化

### 3.2 分析機能

#### テクニカル指標

1. **移動平均**

   - 単純移動平均 (SMA): 5, 20, 50, 200 日
   - 指数移動平均 (EMA): 12, 26 日

2. **モメンタム指標**

   - RSI (14 日)
   - MACD (12, 26, 9)
   - ストキャスティクス (%K, %D)

3. **ボラティリティ指標**

   - ボリンジャーバンド (20 日, 2σ)
   - ATR (14 日)

4. **サポート・レジスタンス**
   - 自動検出アルゴリズム
   - フィボナッチリトレースメント

#### 分析アルゴリズム

- **トレンド分析**: 移動平均の傾きによる判定
- **買い/売りシグナル**: 複数指標の組み合わせ
- **リスク評価**: ボラティリティベースの計算
- **AI 総合分析**: ChatGPT API による複合的な市場分析

### 3.3 アラート・通知機能

#### アラート条件

- **価格ベース**: 指定価格到達時
- **変動率ベース**: X%以上の変動時
- **テクニカル**: シグナル発生時
- **時間ベース**: 定期レポート

#### 通知方式

- **Discord**: Webhook 経由でチャンネルに投稿
- **メール**: SMTP 経由 (オプション)
- **Web**: ブラウザ通知 (オプション)

### 3.3 AI 市場分析レポート機能

#### ChatGPT API 連携仕様

- **API**: OpenAI GPT-4 API
- **分析頻度**: 毎朝 8 時、重要イベント時、ユーザーリクエスト時
- **分析対象**: 主要通貨ペア（USD/JPY, EUR/JPY, GBP/JPY 等）
- **データソース**: 取得した為替データ + テクニカル指標 + 経済カレンダー

#### レポート生成プロセス

```python
def generate_ai_market_report(currency_pairs, analysis_period="24h"):
    """AI市場分析レポートを生成"""

    # 1. 分析データの収集
    market_data = {
        'rates': get_recent_rates(currency_pairs, analysis_period),
        'technical': get_technical_indicators(currency_pairs),
        'volatility': calculate_volatility(currency_pairs),
        'trends': analyze_trends(currency_pairs)
    }

    # 2. ChatGPT用プロンプト作成
    prompt = create_analysis_prompt(market_data)

    # 3. ChatGPT API呼び出し
    analysis = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたは経験豊富な為替アナリストです。"},
            {"role": "user", "content": prompt}
        ]
    )

    # 4. レポートの構造化
    report = structure_report(analysis['choices'][0]['message']['content'])

    return report
```

#### レポート構成

1. **📊 市場概況サマリー**

   - 主要通貨ペアの動向
   - 前日からの変動率と要因分析
   - 今日の注目ポイント

2. **📈 テクニカル分析**

   - トレンド方向の判定
   - 重要なサポート・レジスタンスレベル
   - 各種指標からの売買シグナル

3. **📰 ファンダメンタル要因**

   - 経済指標発表の影響分析
   - 中央銀行政策の考察
   - 地政学的リスクの評価

4. **💡 今日の推奨戦略**
   - 注目すべき価格レベル
   - 推奨エントリーポイント
   - リスク管理のアドバイス

#### Discord 送信フォーマット

```python
discord_report_format = {
    "embeds": [{
        "title": "🔍 AI市場分析レポート",
        "description": f"{datetime.now().strftime('%Y年%m月%d日')} 朝の市場分析",
        "color": 0x3498db,
        "fields": [
            {
                "name": "📊 市場概況",
                "value": report.market_summary,
                "inline": False
            },
            {
                "name": "📈 主要通貨ペア分析",
                "value": report.currency_analysis,
                "inline": False
            },
            {
                "name": "💡 今日の注目ポイント",
                "value": report.key_points,
                "inline": False
            }
        ],
        "footer": {
            "text": "Generated by ChatGPT-4 | Exchange Analytics App"
        },
        "timestamp": datetime.now().isoformat()
    }]
}
```

## 4. データベース設計

### 4.1 テーブル構成

#### exchange_rates

```sql
CREATE TABLE exchange_rates (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,  -- USD/JPY
    timestamp TIMESTAMP NOT NULL,
    open_price DECIMAL(10,5) NOT NULL,
    high_price DECIMAL(10,5) NOT NULL,
    low_price DECIMAL(10,5) NOT NULL,
    close_price DECIMAL(10,5) NOT NULL,
    volume BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### technical_indicators

```sql
CREATE TABLE technical_indicators (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    indicator_type VARCHAR(20) NOT NULL,  -- SMA, RSI, MACD
    indicator_value DECIMAL(10,5),
    additional_data JSON,  -- MACD histogram, BB upper/lower
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### alerts

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    alert_type VARCHAR(20) NOT NULL,  -- price, technical, schedule
    condition_data JSON NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_triggered TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### alert_history

```sql
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    triggered_at TIMESTAMP NOT NULL,
    trigger_price DECIMAL(10,5),
    message TEXT,
    notification_sent BOOLEAN DEFAULT false
);
```

#### ai_market_reports

```sql
CREATE TABLE ai_market_reports (
    id SERIAL PRIMARY KEY,
    report_date DATE NOT NULL,
    report_type VARCHAR(20) NOT NULL,  -- daily, event_driven, custom
    market_summary TEXT NOT NULL,
    technical_analysis TEXT NOT NULL,
    fundamental_analysis TEXT,
    recommendations TEXT,
    currency_pairs_analyzed VARCHAR(200),
    confidence_score DECIMAL(3,2),  -- 0.00-1.00
    generated_at TIMESTAMP DEFAULT NOW(),
    discord_sent BOOLEAN DEFAULT false,
    discord_message_id VARCHAR(50)
);
```

#### report_data_snapshots

```sql
CREATE TABLE report_data_snapshots (
    id SERIAL PRIMARY KEY,
    report_id INTEGER REFERENCES ai_market_reports(id),
    currency_pair VARCHAR(10) NOT NULL,
    snapshot_data JSON NOT NULL,  -- 分析時点のレート・指標データ
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 5. API 設計

### 5.1 REST API エンドポイント

#### データ取得

- `GET /api/rates/{pair}` - 指定通貨ペアの最新レート
- `GET /api/rates/{pair}/history` - 履歴データ (期間指定可能)
- `GET /api/rates/all` - 全通貨ペアの最新レート

#### 分析

- `GET /api/analysis/{pair}/technical` - テクニカル指標
- `GET /api/analysis/{pair}/signals` - 売買シグナル
- `GET /api/analysis/{pair}/support-resistance` - サポート・レジスタンス

#### アラート管理

- `GET /api/alerts` - アラート一覧
- `POST /api/alerts` - アラート作成
- `PUT /api/alerts/{id}` - アラート更新
- `DELETE /api/alerts/{id}` - アラート削除

#### 通知

- `POST /api/notifications/discord/test` - Discord 通知テスト
- `GET /api/notifications/history` - 通知履歴

#### AI 分析レポート

- `POST /api/ai/report/generate` - AI 市場分析レポート生成
- `GET /api/ai/reports` - 過去の AI 分析レポート一覧
- `GET /api/ai/reports/{id}` - 特定レポートの詳細
- `POST /api/ai/report/send-discord` - 手動で Discord に送信
- `GET /api/ai/report/latest` - 最新の AI 分析レポート

### 5.2 WebSocket (リアルタイム)

- `ws://localhost:8000/ws/rates` - リアルタイム価格更新
- `ws://localhost:8000/ws/alerts` - アラート通知

## 6. フロントエンド設計

### 6.1 画面構成

#### ダッシュボード (`/`)

- 主要通貨ペアのリアルタイム価格表示
- 今日の変動率ランキング
- 最新アラート通知

#### チャート画面 (`/chart/{pair}`)

- インタラクティブな価格チャート
- テクニカル指標のオーバーレイ
- 時間足切り替え (1 分, 5 分, 1 時間, 1 日)

#### 分析画面 (`/analysis/{pair}`)

- テクニカル指標一覧
- 売買シグナル
- サポート・レジスタンス表示

#### アラート管理 (`/alerts`)

- アラート設定画面
- アラート履歴
- 通知テスト機能

#### 設定画面 (`/settings`)

- API 設定
- Discord 設定
- 表示設定

### 6.2 UI/UX 設計

#### デザインテーマ

- **カラー**: ダーク/ライトテーマ切り替え対応
- **レスポンシブ**: モバイル対応
- **アクセシビリティ**: WCAG 2.1 準拠

#### チャートライブラリ

- **Chart.js**: 軽量でカスタマイズ性が高い
- **Trading View (将来)**: 高機能チャート (有料オプション)

## 7. 外部サービス連携

### 7.1 Alpha Vantage API

```python
# 設定例
ALPHA_VANTAGE_API_KEY = "your_api_key"
BASE_URL = "https://www.alphavantage.co/query"

# API制限
FREE_TIER_LIMIT = 5  # 1分あたり5回
PREMIUM_TIER_LIMIT = 75  # 1分あたり75回
```

### 7.2 Discord Webhook

```python
# 設定例
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/..."

# 通知フォーマット
{
    "embeds": [{
        "title": "価格アラート: USD/JPY",
        "description": "150.00円を上回りました",
        "color": 0x00ff00,
        "fields": [
            {"name": "現在価格", "value": "150.25円", "inline": true},
            {"name": "変動率", "value": "+0.8%", "inline": true}
        ],
        "timestamp": "2024-01-15T10:30:00Z"
    }]
}
```

## 8. セキュリティ・パフォーマンス

### 8.1 セキュリティ対策

- **API Key 管理**: 環境変数での管理
- **Rate Limiting**: Flask-Limiter 使用
- **CORS 設定**: 適切なオリジン制限
- **入力検証**: パラメータの厳密な検証

### 8.2 パフォーマンス最適化

- **キャッシング**: Redis 使用 (オプション)
- **データベース最適化**: インデックス設定
- **API 呼び出し最適化**: ローカルキャッシュ活用
- **非同期処理**: Celery 使用 (大規模時)

## 9. 開発・デプロイ計画

### 9.1 開発フェーズ

#### Phase 1: 基盤構築 (2 週間)

- データベース設計・構築
- 基本 API 実装
- Alpha Vantage API 連携

#### Phase 2: 分析機能 (2 週間)

- テクニカル指標計算
- チャート表示機能
- 基本的な UI 実装

#### Phase 3: アラート・通知 (1 週間)

- アラート機能実装
- Discord 通知連携
- 管理画面作成

#### Phase 4: 最適化・テスト (1 週間)

- パフォーマンス最適化
- テストケース作成
- ドキュメント整備

### 9.2 デプロイ戦略

- **開発環境**: Docker Compose
- **本番環境**: Docker + GitHub Actions
- **監視**: ログ収集・アラート設定
- **バックアップ**: データベースの定期バックアップ

## 10. 今後の拡張計画

### 10.1 機能拡張

- **ポートフォリオ管理**: 複数通貨の管理
- **バックテスト機能**: 過去データでの戦略検証
- **機械学習**: 価格予測モデル
- **ソーシャル機能**: ユーザー間の情報共有

### 10.2 技術的改善

- **マイクロサービス化**: 機能別サービス分割
- **リアルタイム強化**: WebSocket の本格活用
- **クラウド対応**: AWS/GCP 対応
- **モバイルアプリ**: React Native 対応

## 11. 拡張性・プラグインシステム設計

### 11.1 分析エンジンのモジュール化

#### プラグインアーキテクチャ概要

```
┌─────────────────────────────────────────────────────────────┐
│                     分析エンジンコア                        │
├─────────────────────────────────────────────────────────────┤
│  Plugin Manager  │  Config Manager  │  Signal Aggregator  │
├─────────────────────────────────────────────────────────────┤
│           テクニカル指標プラグイン（動的ロード）             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ SMA Plugin  │ │ RSI Plugin  │ │ MACD Plugin │ │ Custom │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│             分析アルゴリズムプラグイン（拡張可能）           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ Trend Plugin│ │ Signal Plugin│ │ AI Plugin   │ │ Custom │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
├─────────────────────────────────────────────────────────────┤
│              レポートテンプレートシステム                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │Daily Report │ │Event Report │ │Custom Report│ │Template│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### プラグイン基底クラス設計

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
import pandas as pd

class AnalysisPlugin(ABC):
    """分析プラグインの基底クラス"""

    def __init__(self, name: str, version: str, config: Dict = None):
        self.name = name
        self.version = version
        self.config = config or {}
        self.dependencies = []
        self.enabled = True

    @abstractmethod
    def analyze(self, market_data: pd.DataFrame) -> Dict[str, Any]:
        """分析実行メソッド"""
        pass

    @abstractmethod
    def get_signals(self, analysis_result: Dict) -> List[Dict]:
        """売買シグナル生成"""
        pass

    def validate_config(self) -> bool:
        """設定値の検証"""
        return True

    def get_required_data(self) -> List[str]:
        """必要なデータカラムを返す"""
        return ['open', 'high', 'low', 'close', 'volume']

class TechnicalIndicatorPlugin(AnalysisPlugin):
    """テクニカル指標プラグインの基底クラス"""

    @abstractmethod
    def calculate(self, price_data: pd.DataFrame) -> pd.Series:
        """指標値計算"""
        pass

    def interpret_signal(self, current_value: float, context: Dict) -> str:
        """シグナル解釈（オーバーライド可能）"""
        return "neutral"
```

### 11.2 動的設定管理システム

#### 設定管理データベース

```sql
-- プラグイン設定テーブル
CREATE TABLE plugin_configs (
    id SERIAL PRIMARY KEY,
    plugin_name VARCHAR(100) NOT NULL,
    plugin_type VARCHAR(50) NOT NULL,  -- technical, analysis, report
    version VARCHAR(20) NOT NULL,
    config_data JSON NOT NULL,
    is_enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 100,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 通貨ペア別カスタム設定
CREATE TABLE pair_specific_configs (
    id SERIAL PRIMARY KEY,
    currency_pair VARCHAR(10) NOT NULL,
    plugin_name VARCHAR(100) NOT NULL,
    custom_config JSON,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 分析ルールセット
CREATE TABLE analysis_rulesets (
    id SERIAL PRIMARY KEY,
    ruleset_name VARCHAR(100) NOT NULL,
    description TEXT,
    plugins JSON NOT NULL,  -- [{name, config, weight}]
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 11.3 カスタムレポートテンプレート

#### テンプレート定義例

```python
# カスタムテンプレート設定例
CUSTOM_TEMPLATE_CONFIG = {
    "template_id": "daily_fx_report",
    "sections": [
        {
            "type": "summary",
            "title": "📊 市場概況",
            "data_sources": ["trend_analysis", "volatility"],
            "format": "bullet_points"
        },
        {
            "type": "technical",
            "title": "📈 テクニカル分析",
            "indicators": ["sma_20", "rsi", "macd"],
            "chart_type": "candlestick_with_indicators"
        },
        {
            "type": "ai_analysis",
            "title": "🤖 AI分析",
            "model": "gpt-4",
            "prompt_template": "fx_analysis_prompt_v2"
        },
        {
            "type": "signals",
            "title": "💡 売買シグナル",
            "signal_sources": ["technical", "ai"],
            "confidence_threshold": 0.7
        }
    ],
    "style": {
        "discord_color": "0x3498db",
        "max_field_length": 1024,
        "include_charts": true
    }
}
```

### 11.4 プラグイン管理 API

#### 拡張エンドポイント

```python
# プラグイン管理
@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """登録済みプラグイン一覧"""
    pass

@app.route('/api/plugins/<plugin_name>/config', methods=['GET', 'PUT'])
def plugin_config(plugin_name):
    """プラグイン設定の取得・更新"""
    pass

@app.route('/api/plugins/<plugin_name>/reload', methods=['POST'])
def reload_plugin(plugin_name):
    """プラグインのホットリロード"""
    pass

# テンプレート管理
@app.route('/api/report-templates', methods=['GET', 'POST'])
def report_templates():
    """レポートテンプレートの管理"""
    pass

@app.route('/api/report-templates/<template_id>/preview', methods=['POST'])
def preview_template(template_id):
    """テンプレートプレビュー"""
    pass

# カスタム分析
@app.route('/api/analysis/custom', methods=['POST'])
def custom_analysis():
    """カスタム分析実行"""
    pass
```

### 11.5 将来の拡張ロードマップ

#### Phase 1 拡張 (基本実装完了後)

- **基本プラグインシステム**: 指標・分析アルゴリズムの追加
- **設定管理 UI**: Web 画面での設定変更
- **カスタムテンプレート**: レポート形式のカスタマイズ

#### Phase 2 拡張 (運用開始後)

- **コミュニティプラグイン**: プラグイン共有機能
- **バックテスト対応**: 過去データでの戦略検証
- **機械学習プラグイン**: 予測モデルの追加

#### Phase 3 拡張 (本格運用後)

- **分散処理対応**: 大量データ処理の最適化
- **リアルタイム分析**: ストリーミング処理対応
- **外部データ連携**: ニュース・センチメント分析

---

この拡張可能な設計により、将来的に新しい分析手法やレポート形式を簡単に追加できるようになります。段階的に開発を進めていきましょう。
