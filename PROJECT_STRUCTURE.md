# プロジェクト構造設計

## 拡張可能なディレクトリ構造

```
exchangeApp/
├── app.py                          # メインアプリケーション
├── config/                         # 設定管理
│   ├── __init__.py
│   ├── settings.py                # 基本設定
│   ├── database.py                # DB設定
│   └── plugins.py                 # プラグイン設定
├── models/                         # データモデル
│   ├── __init__.py
│   ├── exchange_rate.py           # 為替レートモデル
│   ├── technical_indicator.py     # テクニカル指標モデル
│   ├── ai_report.py              # AI分析レポートモデル
│   └── plugin_config.py          # プラグイン設定モデル
├── services/                       # ビジネスロジック
│   ├── __init__.py
│   ├── data_fetcher.py           # データ取得サービス
│   ├── analysis_engine.py        # 分析エンジン
│   ├── ai_analyzer.py            # AI分析サービス
│   ├── discord_notifier.py       # Discord通知サービス
│   └── scheduler.py              # スケジューラー
├── plugins/                        # プラグインシステム
│   ├── __init__.py
│   ├── base/                      # 基底クラス
│   │   ├── __init__.py
│   │   ├── analysis_plugin.py     # 分析プラグイン基底
│   │   ├── indicator_plugin.py    # 指標プラグイン基底
│   │   └── report_plugin.py       # レポートプラグイン基底
│   ├── technical/                 # テクニカル指標プラグイン
│   │   ├── __init__.py
│   │   ├── sma_plugin.py         # 単純移動平均
│   │   ├── rsi_plugin.py         # RSI
│   │   ├── macd_plugin.py        # MACD
│   │   └── custom/               # カスタム指標
│   │       └── __init__.py
│   ├── analysis/                  # 分析アルゴリズムプラグイン
│   │   ├── __init__.py
│   │   ├── trend_analysis.py     # トレンド分析
│   │   ├── signal_generator.py   # シグナル生成
│   │   ├── ai_analysis.py        # AI分析
│   │   └── custom/               # カスタム分析
│   │       └── __init__.py
│   └── reports/                   # レポートテンプレートプラグイン
│       ├── __init__.py
│       ├── daily_report.py       # 日次レポート
│       ├── event_report.py       # イベント駆動レポート
│       └── custom/               # カスタムレポート
│           └── __init__.py
├── api/                           # API エンドポイント
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── rates.py              # 為替レート API
│   │   ├── analysis.py           # 分析 API
│   │   ├── alerts.py             # アラート API
│   │   ├── ai_reports.py         # AI レポート API
│   │   └── plugins.py            # プラグイン管理 API
│   └── middleware/
│       ├── __init__.py
│       ├── auth.py               # 認証ミドルウェア
│       └── rate_limit.py         # レート制限
├── frontend/                      # フロントエンド
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   ├── js/
│   │   │   ├── chart.js          # チャート表示
│   │   │   ├── dashboard.js      # ダッシュボード
│   │   │   └── plugin-manager.js # プラグイン管理画面
│   │   └── img/
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── chart.html
│       ├── analysis.html
│       ├── alerts.html
│       └── admin/
│           ├── plugins.html      # プラグイン管理
│           └── settings.html     # 設定画面
├── utils/                         # ユーティリティ
│   ├── __init__.py
│   ├── decorators.py             # デコレータ
│   ├── validators.py             # バリデータ
│   ├── formatters.py             # フォーマッタ
│   └── plugin_loader.py          # プラグインローダー
├── database/                      # データベース関連
│   ├── __init__.py
│   ├── migrations/               # マイグレーション
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_add_ai_reports.sql
│   │   └── 003_add_plugin_configs.sql
│   └── seeds/                    # 初期データ
│       ├── currency_pairs.sql
│       └── default_plugins.sql
├── tests/                         # テスト
│   ├── __init__.py
│   ├── test_app.py              # アプリケーションテスト
│   ├── test_plugins/            # プラグインテスト
│   │   ├── __init__.py
│   │   ├── test_technical.py    # テクニカル指標テスト
│   │   └── test_analysis.py     # 分析アルゴリズムテスト
│   ├── test_services/           # サービステスト
│   │   ├── __init__.py
│   │   ├── test_data_fetcher.py
│   │   └── test_ai_analyzer.py
│   └── fixtures/                # テストデータ
│       ├── sample_rates.json
│       └── sample_reports.json
├── docs/                         # ドキュメント
│   ├── DESIGN.md               # 設計書
│   ├── API.md                  # API仕様書
│   ├── PLUGIN_DEVELOPMENT.md   # プラグイン開発ガイド
│   └── DEPLOYMENT.md           # デプロイガイド
├── scripts/                      # スクリプト
│   ├── setup_db.py             # DB初期化
│   ├── migrate.py              # マイグレーション実行
│   ├── seed_data.py            # 初期データ投入
│   └── backup.py               # バックアップ
├── docker/                       # Docker関連
│   ├── Dockerfile.dev          # 開発用
│   ├── Dockerfile.prod         # 本番用
│   └── docker-compose.override.yml
├── .github/                      # GitHub Actions
│   └── workflows/
│       ├── ci.yml              # CI/CD
│       └── deploy.yml          # デプロイ
├── requirements/                 # 依存関係管理
│   ├── base.txt               # 基本依存関係
│   ├── dev.txt                # 開発用依存関係
│   └── prod.txt               # 本番用依存関係
├── .env.example                 # 環境変数テンプレート
├── .gitignore                   # Git除外設定
├── README.md                    # プロジェクト説明
├── PROJECT_STRUCTURE.md         # このファイル
├── requirements.txt             # 依存関係（統合版）
├── docker-compose.yml          # Docker Compose設定
└── Dockerfile                  # Docker設定
```

## プラグイン開発のディレクトリ例

### カスタムテクニカル指標プラグイン
```
plugins/technical/custom/my_indicator/
├── __init__.py
├── indicator.py                # メイン実装
├── config.json                # 設定定義
├── tests/
│   └── test_indicator.py      # テスト
└── README.md                  # 説明書
```

### カスタム分析アルゴリズムプラグイン
```
plugins/analysis/custom/trend_predictor/
├── __init__.py
├── analyzer.py               # メイン実装
├── ml_model.pkl             # 機械学習モデル（オプション）
├── config.json              # 設定定義
├── requirements.txt         # 追加依存関係
├── tests/
│   └── test_analyzer.py     # テスト
└── README.md                # 説明書
```

### カスタムレポートテンプレート
```
plugins/reports/custom/weekly_summary/
├── __init__.py
├── template.py              # テンプレート実装
├── template.json            # テンプレート定義
├── styles/
│   └── discord_format.json  # Discord用スタイル
└── README.md                # 説明書
```

## ファイル命名規則

### Python ファイル
- **ファイル名**: snake_case
- **クラス名**: PascalCase
- **関数名**: snake_case
- **定数**: UPPER_SNAKE_CASE

### プラグインファイル
- **プラグインディレクトリ**: snake_case
- **メインファイル**: プラグインタイプに応じて統一
  - テクニカル指標: `indicator.py`
  - 分析アルゴリズム: `analyzer.py`
  - レポートテンプレート: `template.py`

### 設定ファイル
- **JSON設定**: `config.json`
- **Python設定**: `settings.py`
- **環境変数**: `.env`

## モジュール間の依存関係

```
app.py
├── config/ (設定管理)
├── models/ (データモデル)
├── services/ (ビジネスロジック)
│   └── plugins/ (プラグインシステム)
├── api/ (API層)
│   └── services/
└── utils/ (ユーティリティ)
    └── plugins/
```

## プラグイン読み込みの流れ

1. **アプリ起動時**
   ```python
   # app.py
   from utils.plugin_loader import PluginLoader
   from services.analysis_engine import AnalysisEngine

   # プラグイン読み込み
   plugin_loader = PluginLoader()
   plugin_loader.load_all_plugins()

   # 分析エンジン初期化
   analysis_engine = AnalysisEngine(plugin_loader)
   ```

2. **動的プラグイン追加時**
   ```python
   # プラグイン管理API
   @app.route('/api/plugins/install', methods=['POST'])
   def install_plugin():
       plugin_loader.install_plugin(plugin_path)
       analysis_engine.reload_plugins()
   ```

3. **設定変更時**
   ```python
   # 設定更新API
   @app.route('/api/plugins/<name>/config', methods=['PUT'])
   def update_plugin_config(name):
       plugin_loader.update_config(name, new_config)
       analysis_engine.reload_plugin(name)
   ```

この構造により、将来的な機能拡張や新しい分析手法の追加が容易になります。
