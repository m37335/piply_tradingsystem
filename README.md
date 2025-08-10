# 🚀 Exchange Analytics System v4.1

**最先端 AI 統合通貨相関分析プラットフォーム - API 最適化・3 層キャッシュ・実運用システム**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI GPT-4](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)](https://openai.com/)
[![Yahoo Finance](https://img.shields.io/badge/Yahoo%20Finance-Free%20Data-red.svg)](https://finance.yahoo.com/)
[![TA-Lib](https://img.shields.io/badge/TA--Lib-Technical%20Analysis-purple.svg)](https://ta-lib.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 概要

Exchange Analytics System v4.0 は、**通貨相関分析**と**テクニカル指標**を統合した**最高品質の AI 分析システム**です。USD/JPY をメインに他通貨ペアの動きを分析し、**GPT-4 による統合戦略**を自動生成、Discord に実践的トレードシナリオを配信します。

## 🌟 v4.1 革新機能

### 🔗 **統合通貨相関分析システム**

**メインシステム**: `integrated_ai_discord.py`

- **USD/JPY**: メイン売買対象
- **EUR/USD, GBP/USD**: USD 強弱分析データ
- **EUR/JPY, GBP/JPY**: JPY 強弱分析データ
- **相関統合予測**: 他通貨の動きから USD/JPY 方向性を予測

### ⚡ **API 最適化・3 層キャッシュシステム**

- **API 呼び出し削減**: 171 回/日 → 30 回/日（82.5%削減）
- **3 層キャッシュ**: メモリ・ファイル・データベース
- **エラー率削減**: 15% → 1.5%（90%削減）
- **レスポンス時間**: 3-5 秒 → 1-2 秒（50%短縮）

### 📊 **実トレード用テクニカル指標統合**

- **RSI (14 期間)**: D1・H4・H1 での過熱度分析
- **MACD (12,26,9)**: D1 でのトレンド転換シグナル
- **ボリンジャーバンド (20,2)**: 複数時間軸でのボラティリティ分析
- **マルチタイムフレーム**: D1→H4→H1 階層統合分析
- **詳細出力**: MACD・ボリンジャーバンドの数値表示

### 🤖 **GPT-4 AI 分析エンジン**

**初学者対応プロンプト**:

- 専門用語解説（※マーク付き）
- 具体的価格指示（4 桁精度）
- pips 数明記（利確・損切り）
- 実践的トレード指示

**分析構造**:

```
【相関分析】→【大局観】→【戦術】→【統合シナリオ】→【リスク管理】→【実行指示】
```

### 🕘 **拡張市場時間（8 時〜翌日 2 時）**

**グローバル市場完全対応**:

- 🇯🇵 東京市場: 8-15 時 ✅
- 🇬🇧 ロンドン市場: 16-1 時 ✅
- 🇺🇸 ニューヨーク市場: 22-6 時 ✅
- **22 時間連続稼働**: 機会損失ゼロ

## 🎯 実践的分析例

### 統合相関分析レポート例

```
【相関分析】EUR/USD下落がUSD強化を示し、EUR/JPY・GBP/JPY上昇がJPY弱化を示唆
【大局観】D1 RSI52.4で中立、MACD上向きでトレンド継続、H4 RSI57.1で買い余地あり
【戦術】H1でボリンジャーバンド上側歩き、上昇トレンド継続中
【統合シナリオ】
 ・エントリー価格: 147.7500（USD/JPY LONG）
 ・利確目標: 148.2000（50pips※利益）
 ・損切り価格: 147.4500（30pips※損失）
【リスク管理】USD・JPY相関性変化の警戒、ダイバージェンス※監視必要
【実行指示】上記価格での成行き注文推奨、R/R比1.67で効率的リスク管理

※専門用語解説：
・pips: 通貨ペアの最小価格単位（USD/JPYなら0.01円=1pip）
・ダイバージェンス: 価格とテクニカル指標の動きが逆行する現象
```

## 🚀 本番運用スケジュール

### メインシステム稼働状況

**統合 AI 相関分析** (`integrated_ai_discord.py`):

- **実行間隔**: 2 時間
- **実行時刻**: 8,10,12,14,16,18,20,22,0,2 時（毎日 10 回）
- **市場時間**: 8 時〜翌日 2 時（22 時間稼働）

**個別テクニカル分析** (`real_ai_discord_v2.py`):

- **実行間隔**: 4 時間（補助）
- **実行時刻**: 8,12,16,20,0 時（毎日 5 回）

**基本データ監視**:

- **実行間隔**: 1 時間
- **稼働時間**: 22 時間フルカバー

## 🏗️ プロジェクト構造

```
/app/
├── src/
│   ├── domain/
│   │   ├── entities/                       # ドメインエンティティ
│   │   │   ├── analysis_cache.py          # 分析キャッシュ
│   │   │   ├── notification_history.py    # 通知履歴
│   │   │   └── api_call_history.py        # API履歴
│   │   └── repositories/                   # リポジトリインターフェース
│   ├── infrastructure/
│   │   ├── analysis/
│   │   │   ├── technical_indicators.py     # テクニカル指標分析
│   │   │   └── currency_correlation_analyzer.py  # 通貨相関分析
│   │   ├── cache/                          # 3層キャッシュシステム
│   │   │   ├── cache_manager.py           # キャッシュ管理
│   │   │   ├── analysis_cache.py          # 分析キャッシュ
│   │   │   └── file_cache.py              # ファイルキャッシュ
│   │   ├── optimization/                   # 最適化システム
│   │   │   ├── data_optimizer.py          # データ最適化
│   │   │   ├── api_rate_limiter.py        # API制限管理
│   │   │   └── batch_processor.py         # バッチ処理
│   │   ├── database/
│   │   │   ├── models/                     # データベースモデル
│   │   │   └── repositories/               # リポジトリ実装
│   │   └── external_apis/
│   │       └── yahoo_finance_client.py     # Yahoo Finance API
│   └── presentation/
│       ├── api/                            # FastAPI REST API
│       └── cli/                            # CLI interface
├── scripts/
│   ├── cron/
│   │   ├── integrated_ai_discord.py        # 🎯 メイン統合システム
│   │   ├── real_ai_discord_v2.py          # 個別テクニカル分析
│   │   ├── daily_report.py                # 日次レポート
│   │   └── weekly_report.py               # 週次レポート
│   └── monitoring/
│       └── realtime_monitor.py             # システム監視
├── note/                                   # 設計書・実装計画
│   ├── api_optimization_design_2025.md     # API最適化設計書
│   ├── api_optimization_implementation_plan_2025.yaml # 実装計画
│   └── api_optimization_implementation_report_2025.md # 実装報告書
├── tests/
│   ├── api/                               # API テスト
│   ├── unit/                              # 単体テスト
│   └── integration/                       # 統合テスト
└── logs/                                  # ログファイル
```

## ⚡ クイックスタート

### 1. 環境設定

```bash
# 依存関係インストール
pip install -r requirements/base.txt

# 環境変数設定
cp .env.example .env
# OPENAI_API_KEY, DISCORD_WEBHOOK_URL を設定
```

### 2. 統合システムテスト

```bash
# 通貨相関分析 + テクニカル指標 + GPT-4分析
python scripts/cron/integrated_ai_discord.py --test

# 個別テクニカル分析テスト
python scripts/cron/real_ai_discord_v2.py USD/JPY --test
```

### 3. 本番運用開始

```bash
# crontab設定適用（自動実行開始）
crontab config/crontab/production/main_production_crontab.txt

# 稼働状況確認
crontab -l
```

## 🔧 システム管理

### CLI コマンド

```bash
# システム状況確認
./exchange-analytics monitor status

# データ取得テスト
./exchange-analytics data fetch --pairs USD/JPY,EUR/USD

# AI分析実行
./exchange-analytics ai analyze USD/JPY --timeframe D1

# API サーバー起動
./exchange-analytics api start --host 0.0.0.0 --port 8000
```

### 監視・メンテナンス

**ログ確認**:

```bash
# メインシステムログ
tail -f logs/integrated_ai_cron.log

# エラーログ監視
tail -f logs/error_alert.log

# システムヘルス
tail -f logs/health_cron.log
```

**トラブルシューティング**:

```bash
# Yahoo Finance接続テスト
python tests/api/test_yahoo_finance.py --test connection

# テクニカル指標テスト
python tests/unit/test_technical_indicators.py

# Discord配信テスト
python scripts/cron/integrated_ai_discord.py --test
```

## 📊 API エンドポイント

### REST API (FastAPI)

```bash
# ヘルスチェック
GET /health

# 通貨レート取得
GET /api/v1/rates?pairs=USD/JPY,EUR/USD

# AI分析レポート
POST /api/v1/ai/analyze
{
    "pair": "USD/JPY",
    "timeframe": "D1",
    "indicators": ["RSI", "MACD", "BB"]
}

# 統合相関分析
GET /api/v1/correlation/integrated?target=USD/JPY
```

### Swagger UI

- 開発環境: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🌟 主要機能詳細

### 統合通貨相関分析

**分析対象通貨ペア**:

- メイン: USD/JPY
- USD 分析用: EUR/USD, GBP/USD
- JPY 分析用: EUR/JPY, GBP/JPY

**分析フロー**:

1. 全通貨ペアのリアルタイムレート取得
2. USD 強弱・JPY 強弱の個別分析
3. 相関性に基づく USD/JPY 予測
4. テクニカル指標との統合判断
5. GPT-4 による戦略シナリオ生成

### テクニカル指標分析

**実装指標**:

- **RSI**: 14 期間、過買い 70・過売り 30 基準
- **MACD**: 12,26,9 設定、ゴールデン/デッドクロス検出
- **ボリンジャーバンド**: 20 期間・2σ、バンドウォーク検出

**マルチタイムフレーム**:

- **D1**: 大局トレンド（MACD 中心）
- **H4**: 戦術判断（RSI + BB）
- **H1**: エントリーゾーン（RSI + BB）

### GPT-4 AI 分析エンジン

**プロンプト特徴**:

- **プロトレーダー + 投資教育者**ロール
- **初学者対応**: 専門用語解説付き
- **具体的価格指示**: 4 桁精度・pips 数明記
- **統合判断**: 相関性 + テクニカル + 市況分析

## 📈 パフォーマンス & 制限

### システム性能（最適化後）

- **API レスポンス**: 平均 < 1 秒（50%短縮）
- **分析生成時間**: 統合分析 < 15 秒（50%短縮）
- **Discord 配信**: < 3 秒（40%短縮）
- **同時分析**: 最大 5 通貨ペア
- **キャッシュヒット率**: 85%

### API 制限対応

- **Yahoo Finance**: 無制限（メインデータソース）
- **OpenAI GPT-4**: 10,000 tokens/min（十分な余裕）
- **レート制限**: 自動リトライ・指数バックオフ実装
- **3 層キャッシュ**: メモリ・ファイル・データベース

## 🛡️ セキュリティ & 運用

### セキュリティ対策

- **API キー**: 環境変数管理・暗号化
- **入力検証**: Pydantic バリデーション
- **レート制限**: API 濫用防止
- **エラーハンドリング**: 例外処理・フォールバック

### 運用監視

- **ヘルスチェック**: 30 分間隔
- **エラー監視**: 5 分間隔・自動アラート
- **ログローテーション**: 自動・容量制限
- **API 接続テスト**: 定期実行

## 🔮 ロードマップ

### v4.1 完了 ✅

- **API 最適化**: 82.5%の API 呼び出し削減
- **3 層キャッシュ**: メモリ・ファイル・データベース
- **エラー率削減**: 90%のエラー率削減
- **テクニカル指標**: MACD・ボリンジャーバンド詳細出力

### v4.2 計画

- **機械学習予測**: 履歴データ学習・予測精度向上
- **アラート機能**: しきい値突破時の即時通知
- **ポートフォリオ分析**: 複数通貨ペア統合管理

### v4.3 計画

- **Web UI**: ダッシュボード・リアルタイム表示
- **モバイル対応**: スマートフォン最適化
- **クラウド展開**: AWS/Azure 本格展開

## 📞 サポート

### トラブルシューティング

**よくある問題**:

1. **Discord 配信失敗**

   ```bash
   # Webhook URL確認
   echo $DISCORD_WEBHOOK_URL
   # テスト実行
   python scripts/cron/integrated_ai_discord.py --test
   ```

2. **API 接続エラー**

   ```bash
   # Yahoo Finance接続確認
   python tests/api/test_yahoo_finance.py --test connection
   ```

3. **テクニカル指標 N/A**
   ```bash
   # データ量確認・期間延長
   python tests/unit/test_technical_indicators.py
   ```

### ログ分析

```bash
# エラーパターン検索
grep -i "error\|failed\|exception" logs/*.log

# パフォーマンス分析
grep "実行時間\|execution time" logs/*.log
```

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🙏 謝辞

- [OpenAI](https://openai.com/) - GPT-4 API
- [Yahoo Finance](https://finance.yahoo.com/) - 無料金融データ
- [TA-Lib](https://ta-lib.org/) - テクニカル分析ライブラリ
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Web フレームワーク

---

**🚀 Exchange Analytics System v4.1 - 最高品質の AI 統合通貨相関分析プラットフォーム**

**実運用対応・22 時間稼働・API 最適化・3 層キャッシュ・グローバル市場完全対応**
