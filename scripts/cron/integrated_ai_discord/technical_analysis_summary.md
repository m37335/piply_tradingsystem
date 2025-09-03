# 統合 AI 分析システム - テクニカル分析総まとめ

## 概要

このシステムは、多時間軸での市場分析から AI 戦略生成、チャート可視化まで一貫したトレーディング分析を提供する包括的な分析システムです。

## 1. データ取得期間と時間軸

| 時間軸 | 取得期間 | データ間隔 | 用途                 |
| ------ | -------- | ---------- | -------------------- |
| **D1** | 1 年     | 日足       | MA200 計算、長期分析 |
| **H4** | 1 ヶ月   | 1 時間足   | 中期分析             |
| **H1** | 1 週間   | 1 時間足   | 短期分析             |
| **M5** | 3 日     | 5 分足     | 超短期分析           |

## 2. テクニカル指標（TA-Lib 使用）

### RSI（相対力指数）

- **期間**: 30, 50, 70（短期・中期・長期）
- **計算**: TA-Lib RSI 関数
- **出力**: 現在値、前回値、状態（overbought/neutral/oversold）、シグナル、ダイバージェンス

### MACD（移動平均収束拡散）

- **設定**: Fast=12, Slow=26, Signal=9
- **計算**: TA-Lib MACD 関数
- **出力**: MACD 線、シグナル線、ヒストグラム、状態、シグナル
- **対象**: D1 のみ

### ボリンジャーバンド

- **設定**: 期間=20, 標準偏差=2
- **計算**: TA-Lib BBANDS 関数
- **出力**: 上限・中限・下限バンド、現在価格位置、バンド幅

### 移動平均線

- **D1**: SMA200（長期）、SMA50（中期）
- **H4**: SMA50（中期）、SMA20（短期）
- **H1**: SMA20（短期）
- **M5**: SMA20（短期）
- **計算**: TA-Lib SMA/EMA 関数
- **出力**: 現在値、価格位置、傾き

## 3. フィボナッチリトレースメント

### 計算期間

- **D1**: 過去 3 ヶ月（90 日）
- **H4**: 過去 7 日（42 時間）
- **H1**: 過去 7 日（168 時間）
- **M5**: 過去 2 日（576 分）

### フィボナッチレベル

- **0.0%**: 高値（High）
- **23.6%**: 第 1 リトレースメント
- **38.2%**: 第 2 リトレースメント
- **50.0%**: 中間レベル
- **61.8%**: 第 3 リトレースメント
- **78.6%**: 第 4 リトレースメント
- **100.0%**: 安値（Low）

### 出力情報

- スイング高値・安値
- 各フィボナッチレベルの価格
- 現在価格の位置（パーセンテージ）
- 最寄りのフィボナッチレベル
- データポイント数

## 4. 通貨相関分析

### 対象通貨ペア

- USD/JPY（メイン）
- EUR/USD
- GBP/USD
- EUR/JPY
- GBP/JPY

### 分析内容

- USD 強弱分析（方向性、信頼度、サポート要因、リスク要因）
- JPY 強弱分析
- 統合予測（現在レート、変動率、予測方向、信頼度、戦略バイアス）

## 5. AI 戦略分析

### 入力情報

- 通貨相関分析結果
- 全時間軸のテクニカル指標
- 現在の市場環境

### 出力内容

- 基本バイアス（LONG/SHORT、信頼度）
- 市場環境分析
- テクニカル分析（MA、MACD、BB、RSI、Fibonacci）
- エントリー戦略（根拠、計算）
- 利確ポイント
- 損切りポイント
- 実行条件
- 代替案
- リスク管理

## 6. チャート生成

### H1 チャート

- 期間: 1 週間表示
- EMA20, EMA50, EMA200
- フィボナッチレベル
- 現在価格表示

### H4 チャート

- 期間: 1 ヶ月表示
- EMA20, EMA50, EMA200
- フィボナッチレベル
- 現在価格表示

## 7. データ保存・配信

### 保存形式

- データベースキャッシュ（PostgreSQL）
- チャート画像（PNG 形式）
- ログファイル

### 配信先

- Discord（テキスト + チャート画像）
- コンソール出力
- ログファイル

## 8. システム構成

### ディレクトリ構造

```
integrated_ai_discord/
├── analyzers/          # テクニカル分析モジュール
│   ├── talib_technical_analyzer.py
│   ├── fibonacci_analyzer.py
│   └── chart_visualizer.py
├── ai_analysis/        # AI戦略生成
│   └── ai_strategy_generator.py
├── integrated/         # 統合処理
│   └── integrated_reporter.py
├── notifications/      # 通知機能
│   └── discord_sender.py
├── utils/             # ユーティリティ
├── charts/            # チャート保存
├── main.py            # メインエントリーポイント
└── README.md          # ドキュメント
```

### 主要コンポーネント

- **TALibTechnicalIndicatorsAnalyzer**: TA-Lib を使用したテクニカル指標計算
- **FibonacciAnalyzer**: フィボナッチリトレースメント分析
- **ChartVisualizer**: チャート生成・可視化
- **AIStrategyGenerator**: AI 戦略生成
- **IntegratedAIDiscordReporter**: 統合分析・レポート生成

## 9. 実行方法

### CLI 実行

```bash
# 基本実行
python scripts/cron/integrated_ai_discord/main.py

# チャート生成付き実行
python scripts/cron/integrated_ai_discord/main.py --chart

# テストモード実行
python scripts/cron/integrated_ai_discord/main.py --test
```

### Crontab 設定

```bash
# 平日実行（9:00, 17:00）
0 9,17 * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && export PYTHONPATH=/app && python scripts/cron/integrated_ai_discord/main.py --chart

# 土曜日実行（9:00）
0 9 * * 6 cd /app && export $(cat .env | grep -v '^#' | xargs) && export PYTHONPATH=/app && python scripts/cron/integrated_ai_discord/main.py --chart
```

## 10. 技術仕様

### 使用ライブラリ

- **TA-Lib**: テクニカル指標計算
- **pandas**: データ処理
- **matplotlib**: チャート生成
- **httpx**: HTTP 通信
- **rich**: コンソール出力
- **pytz**: タイムゾーン処理

### データベース

- **PostgreSQL**: 分析結果キャッシュ
- **Redis**: セッション管理（オプション）

### API

- **Yahoo Finance**: 価格データ取得
- **OpenAI GPT-4**: AI 戦略生成
- **Discord Webhook**: 通知配信

---

_最終更新: 2025 年 8 月 27 日_
