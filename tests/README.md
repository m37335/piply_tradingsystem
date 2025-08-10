# 🧪 テストディレクトリ構造

## 📁 ディレクトリ構成

```
tests/
├── unit/                    # ユニットテスト
│   ├── test_technical_indicators.py
│   └── test_indicators_extended.py
├── integration/             # 統合テスト
│   ├── test_notification_integration.py
│   ├── test_pattern5_completion.py
│   ├── test_discord_notification.py
│   ├── test_phase4_integration.py
│   ├── test_new_templates.py
│   ├── test_new_pattern_detectors.py
│   ├── test_notification_patterns.py
│   ├── test_cache_system.py
│   ├── test_notification_manager.py
│   ├── test_discord_simple.py
│   ├── multi_currency_trading_test.py
│   └── test_env_loading.py
├── database/                # データベーステスト
│   ├── test_models.py
│   ├── test_database_connection.py
│   └── test_data_generator_service.py
├── api/                     # APIテスト
│   ├── test_openai.py
│   ├── test_alphavantage.py
│   └── test_yahoo_finance.py
├── e2e/                     # エンドツーエンドテスト
└── test_app.py              # アプリケーションテスト
```

## 🎯 テスト分類

### ユニットテスト (`unit/`)

- **目的**: 個別の関数・クラスの動作確認
- **対象**: テクニカル指標計算、個別コンポーネント
- **実行時間**: 短時間（数秒）

### 統合テスト (`integration/`)

- **目的**: 複数コンポーネント間の連携確認
- **対象**: パターン検出、通知システム、Discord 連携
- **実行時間**: 中程度（数分）

### データベーステスト (`database/`)

- **目的**: データベース操作の確認
- **対象**: モデル、接続、データ生成
- **実行時間**: 中程度（数分）

### API テスト (`api/`)

- **目的**: 外部 API 連携の確認
- **対象**: Yahoo Finance、OpenAI、Alpha Vantage
- **実行時間**: 中程度（数分）

## 🚀 テスト実行方法

### 全テスト実行

```bash
pytest tests/
```

### 特定カテゴリのテスト実行

```bash
# ユニットテストのみ
pytest tests/unit/

# 統合テストのみ
pytest tests/integration/

# データベーステストのみ
pytest tests/database/

# APIテストのみ
pytest tests/api/
```

### 特定のテストファイル実行

```bash
pytest tests/integration/test_pattern5_completion.py
```

## 📋 テストファイル詳細

### 統合テスト (`integration/`)

#### パターン検出関連

- `test_pattern5_completion.py` - パターン 5（RSI50 ライン攻防）の完成テスト
- `test_new_pattern_detectors.py` - 新しいパターン検出器のテスト
- `test_new_templates.py` - 新しい通知テンプレートのテスト

#### 通知システム関連

- `test_notification_integration.py` - 通知システム統合テスト
- `test_discord_notification.py` - Discord 通知機能テスト
- `test_discord_simple.py` - Discord 簡易テスト
- `test_notification_patterns.py` - 通知パターンテスト
- `test_notification_manager.py` - 通知マネージャーテスト

#### システム統合関連

- `test_phase4_integration.py` - Phase 4 統合テスト
- `test_cache_system.py` - キャッシュシステムテスト
- `multi_currency_trading_test.py` - マルチ通貨取引テスト
- `test_env_loading.py` - 環境設定読み込みテスト

### データベーステスト (`database/`)

- `test_models.py` - データベースモデルテスト
- `test_database_connection.py` - データベース接続テスト
- `test_data_generator_service.py` - テストデータ生成サービス

### ユニットテスト (`unit/`)

- `test_technical_indicators.py` - テクニカル指標計算テスト
- `test_indicators_extended.py` - 拡張テクニカル指標テスト

### API テスト (`api/`)

- `test_openai.py` - OpenAI API 連携テスト
- `test_alphavantage.py` - Alpha Vantage API 連携テスト
- `test_yahoo_finance.py` - Yahoo Finance API 連携テスト

## 🔧 テスト環境設定

### 必要な環境変数

```bash
# データベース
DATABASE_URL=sqlite:///./test_app.db

# Discord通知
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# 外部API
ALPHA_VANTAGE_API_KEY=your_api_key
OPENAI_API_KEY=your_api_key
```

### テストデータ

- テスト用データベース: `data/test_app.db`
- Discord 設定: `data/discord_test.json`

## 📊 テスト結果

### 成功基準

- ✅ 全テストが正常に実行される
- ✅ エラーが発生しない
- ✅ 期待される結果が得られる

### 失敗時の対処

1. 環境変数の確認
2. データベース接続の確認
3. 外部 API 接続の確認
4. ログファイルの確認

## 🎯 テスト方針

### 継続的テスト

- 新機能追加時は必ずテストを作成
- 既存テストの更新・保守
- 定期的なテスト実行

### テスト品質

- 明確なテストケース
- 適切なエラーハンドリング
- 詳細なログ出力
- 再現可能なテスト環境
