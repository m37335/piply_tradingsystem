# 🧪 Tests Directory

Exchange Analytics システムのテストスイート

## 📁 ディレクトリ構造

```
tests/
├── api/           # API・外部サービステスト
├── integration/   # 統合テスト
├── unit/         # 単体テスト
├── e2e/          # エンドツーエンドテスト
└── README.md     # このファイル
```

## 🌐 **api/** - API・外部サービステスト

| ファイル                | 用途              | 説明                     |
| ----------------------- | ----------------- | ------------------------ |
| `test_alphavantage.py`  | Alpha Vantage API | FX・株価データ取得テスト |
| `test_openai.py`        | OpenAI API        | GPT 分析機能テスト       |
| `test_yahoo_finance.py` | Yahoo Finance API | 無料データソーステスト   |

### 実行方法

```bash
# Alpha Vantage接続テスト
cd /app && python tests/api/test_alphavantage.py --test connection

# OpenAI GPT分析テスト
cd /app && python tests/api/test_openai.py --test real

# Yahoo Finance複数通貨テスト
cd /app && python tests/api/test_yahoo_finance.py --test multiple
```

## 🔗 **integration/** - 統合テスト

| ファイル              | 用途           | 説明                              |
| --------------------- | -------------- | --------------------------------- |
| `test_env_loading.py` | 環境変数テスト | .env 読み込み・Discord 通知テスト |

### 実行方法

```bash
# 環境変数統合テスト
cd /app && python tests/integration/test_env_loading.py
```

## 🧮 **unit/** - 単体テスト

| ファイル                       | 用途           | 説明                          |
| ------------------------------ | -------------- | ----------------------------- |
| `test_technical_indicators.py` | テクニカル指標 | RSI・MACD・ボリンジャーバンド |

### 実行方法

```bash
# RSI単体テスト
cd /app && python tests/unit/test_technical_indicators.py --indicator rsi

# MACD単体テスト
cd /app && python tests/unit/test_technical_indicators.py --indicator macd

# マルチタイムフレーム分析
cd /app && python tests/unit/test_technical_indicators.py --indicator multi
```

## 🌍 **e2e/** - エンドツーエンドテスト

現在のシステム全体の動作テスト（継承済み）

## 🚀 **全テスト実行**

### API テスト一括実行

```bash
cd /app && echo "🌐 API Tests" && \
python tests/api/test_alphavantage.py --test connection && \
python tests/api/test_openai.py --test connection && \
python tests/api/test_yahoo_finance.py --test connection
```

### 統合テスト実行

```bash
cd /app && echo "🔗 Integration Tests" && \
python tests/integration/test_env_loading.py
```

### 単体テスト実行

```bash
cd /app && echo "🧮 Unit Tests" && \
python tests/unit/test_technical_indicators.py --indicator all
```

## 📊 **テスト結果ログ**

テスト実行時のログは以下の場所に保存されます：

- **API テスト**: `/app/logs/*_test_cron.log`
- **統合テスト**: `/app/logs/env_test_cron.log`
- **システムログ**: `/app/logs/`

## ⚙️ **環境要件**

### 必要な環境変数

```env
ALPHA_VANTAGE_API_KEY=your_key
OPENAI_API_KEY=your_key
DISCORD_WEBHOOK_URL=your_webhook
JWT_SECRET=your_secret
```

### 必要なパッケージ

```bash
pip install ta-lib yfinance httpx rich typer
```

## 🔄 **CI/CD 統合**

### GitHub Actions 例

```yaml
- name: Run API Tests
  run: |
    cd /app
    python tests/api/test_alphavantage.py --test connection
    python tests/api/test_openai.py --test connection
    python tests/api/test_yahoo_finance.py --test connection

- name: Run Integration Tests
  run: |
    cd /app
    python tests/integration/test_env_loading.py

- name: Run Unit Tests
  run: |
    cd /app
    python tests/unit/test_technical_indicators.py --indicator all
```

## 📞 **トラブルシューティング**

### 一般的な問題

1. **ImportError**: `sys.path.append('/app')`が各テストファイルに含まれていることを確認
2. **API Timeout**: ネットワーク接続と API 制限を確認
3. **環境変数エラー**: `.env`ファイルの存在と設定値を確認
4. **権限エラー**: ファイルの実行権限を確認（`chmod +x`）

### デバッグコマンド

```bash
# Python パス確認
python -c "import sys; print(sys.path)"

# 環境変数確認
python -c "import os; print([k for k in os.environ.keys() if 'API' in k])"

# モジュール確認
python -c "import sys; sys.path.append('/app'); from src.infrastructure.external_apis.yahoo_finance_client import YahooFinanceClient; print('OK')"
```
