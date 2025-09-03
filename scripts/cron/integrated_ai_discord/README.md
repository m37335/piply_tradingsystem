# Integrated AI Discord Reporter (モジュール化版)

通貨相関性を活用した統合 AI 分析 Discord 配信システムのモジュール化版です。
**チャート画像生成・配信機能**を統合し、視覚的な分析結果も提供します。

## 📁 ディレクトリ構造

```
integrated_ai_discord/
├── __init__.py
├── main.py                          # メインスクリプト
├── README.md                        # このファイル
├── analyzers/                       # 分析モジュール
│   ├── __init__.py
│   ├── fibonacci_analyzer.py        # フィボナッチ分析
│   ├── talib_technical_analyzer.py  # TA-Libテクニカル指標分析
│   └── chart_visualizer.py          # チャート生成・可視化
├── ai_analysis/                     # AI分析モジュール
│   ├── __init__.py
│   └── ai_strategy_generator.py     # AI戦略生成
├── notifications/                   # 通知モジュール
│   ├── __init__.py
│   └── discord_sender.py           # Discord送信（分析結果 + チャート画像）
├── integrated/                      # 統合モジュール
│   ├── __init__.py
│   └── integrated_reporter.py      # 統合レポーター
├── utils/                          # ユーティリティモジュール
│   ├── __init__.py
│   ├── config_manager.py           # 設定管理
│   └── error_handler.py            # エラーハンドリング
└── charts/                         # チャート保存ディレクトリ
    └── USDJPY/                     # 通貨ペア別チャート
```

## 🚀 使用方法

### 1. 基本的な実行（分析結果 + チャート画像配信）

```bash
cd /app/scripts/cron/integrated_ai_discord
python main.py --chart
```

### 2. 分析結果のみ（チャート生成なし）

```bash
python main.py
```

### 3. テストモード（Discord 送信なし）

```bash
python main.py --test
```

### 4. テストモード + チャート生成

```bash
python main.py --test --chart
```

### 5. 最適化機能無効

```bash
python main.py --no-optimization
```

### 6. CLI 経由での実行

```bash
# 分析実行
./exchange-analytics ai analyze

# チャート付き分析実行
./exchange-analytics ai analyze --chart

# テスト実行
./exchange-analytics ai analyze --test --chart
```

## 📋 モジュール説明

### analyzers/

- **fibonacci_analyzer.py**: フィボナッチリトレースメント分析

  - 期間別階層アプローチ（D1: 3 ヶ月、H4/H1: 7 日、M5: 2 日）
  - 複数時間軸での分析
  - 現在価格の位置判定
  - 0%と 100%レベルを含む完全なフィボナッチ分析

- **talib_technical_analyzer.py**: TA-Lib テクニカル指標分析（標準）

  - 業界標準の高精度計算エンジン
  - 既存設定との完全互換
  - RSI、MACD、ボリンジャーバンド、移動平均線

- **chart_visualizer.py**: チャート生成・可視化
  - H1 時間足チャート生成
  - 日本式ローソク足（陽線：赤、陰線：緑）
  - フィボナッチレベル表示（価格付き）
  - EMA20、EMA50、EMA200 移動平均線（曲線）
  - 現在価格表示
  - 1 週間表示範囲（データは 3 ヶ月取得）

### ai_analysis/

- **ai_strategy_generator.py**: AI 戦略生成
  - OpenAI API を使用した統合分析
  - テクニカル指標と相関分析の組み合わせ
  - 売買シナリオ生成

### notifications/

- **discord_sender.py**: Discord 送信機能
  - 統合分析結果の送信
  - **チャート画像の添付送信**
  - エラー通知
  - メッセージフォーマット
  - ファイルサイズ制限チェック（8MB）

### integrated/

- **integrated_reporter.py**: 統合レポーター
  - 全モジュールの統合
  - 最適化コンポーネント管理
  - データベースセッション管理
  - **チャート生成・配信の統合**

### utils/

- **config_manager.py**: 設定管理
  - 環境変数の読み込み
  - 設定の妥当性検証
- **error_handler.py**: エラーハンドリング
  - エラーメッセージのフォーマット
  - エラー種別の判定

## 🔧 設定

`.env`ファイルに以下の設定が必要です：

```env
OPENAI_API_KEY=your_openai_api_key
DISCORD_WEBHOOK_URL=your_discord_webhook_url
DISCORD_MONITORING_WEBHOOK_URL=your_monitoring_webhook_url
```

## 📊 機能

### 分析機能

- 通貨相関分析
- テクニカル指標分析（RSI、MACD、ボリンジャーバンド、移動平均線）
- フィボナッチ分析
- AI 統合分析

### チャート機能

- **H1 時間足チャート生成**
- **日本式ローソク足表示**
- **フィボナッチレベル表示**
- **移動平均線表示（EMA20、EMA50、EMA200）**
- **現在価格表示**
- **1 週間表示範囲**

### 最適化機能

- データキャッシュ
- API 制限管理
- バッチ処理
- 重複通知防止

### 通知機能

- Discord 配信（分析結果）
- **Discord 配信（チャート画像）**
- エラー通知
- 統計情報

## ⏰ 自動実行設定

### crontab 設定

```bash
# 🤖 統合AI分析（モジュール化版）- 平日8:00-6:00、金曜日は翌朝6:00まで
0 8,9,10,12,14,16,18,19,20,21,22,23,0,2,4,6 * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && export PYTHONPATH=/app && timeout 180 python scripts/cron/integrated_ai_discord/main.py --chart >> /app/logs/integrated_ai_cron.log 2>&1

# 🤖 統合AI分析（モジュール化版）- 土曜日8:00-6:00
0 8,9,10,12,14,16,18,19,20,21,22,23,0,2,4,6 * * 6 cd /app && export $(cat .env | grep -v '^#' | xargs) && export PYTHONPATH=/app && timeout 180 python scripts/cron/integrated_ai_discord/main.py --chart >> /app/logs/integrated_ai_cron.log 2>&1
```

### 実行スケジュール

- **平日（月-金）**: 8:00, 9:00, 10:00, 12:00, 14:00, 16:00, 18:00, 19:00, 20:00, 21:00, 22:00, 23:00, 0:00, 2:00, 4:00, 6:00
- **土曜日**: 平日と同じスケジュール
- **日曜日**: 実行なし

## 🛠️ 開発・拡張

### 新しい分析モジュールの追加

1. `analyzers/`ディレクトリに新しいファイルを作成
2. `analyzers/__init__.py`にインポートを追加
3. `integrated_reporter.py`で使用

### 新しい通知方法の追加

1. `notifications/`ディレクトリに新しいファイルを作成
2. `notifications/__init__.py`にインポートを追加
3. `integrated_reporter.py`で統合

### チャート機能の拡張

1. `analyzers/chart_visualizer.py`に新しいチャートタイプを追加
2. 新しい時間軸や指標の表示機能を実装
3. `integrated_reporter.py`で統合

## 📈 パフォーマンス

- 元のファイル（約 2000 行）を約 300-400 行のモジュールに分割
- 各モジュールの責任が明確
- テストとメンテナンスが容易
- 拡張性が向上
- **チャート生成時間**: 約 3-5 秒
- **ファイルサイズ**: 約 115KB（最適化済み）

## 🔍 トラブルシューティング

### よくある問題

1. **インポートエラー**

   - プロジェクトパスが正しく設定されているか確認
   - `sys.path.append("/app")`が必要

2. **設定エラー**

   - `.env`ファイルの存在確認
   - 環境変数の設定確認

3. **データベース接続エラー**

   - データベースサービスの起動確認
   - 接続設定の確認

4. **チャート生成エラー**

   - matplotlib、pandas、numpy のインストール確認
   - ディスク容量の確認
   - 権限設定の確認

5. **Discord 配信エラー**
   - Webhook URL の有効性確認
   - ファイルサイズ制限（8MB）の確認
   - ネットワーク接続の確認

## 📝 ログ

各モジュールで適切なログ出力を行っています：

- ✅ 成功
- ⚠️ 警告
- ❌ エラー
- 🔄 処理中
- 📊 統計情報
- 📈 チャート生成
- 💬 Discord 配信

### ログファイル

- `/app/logs/integrated_ai_cron.log`: 統合 AI 分析の実行ログ
- `/app/scripts/cron/integrated_ai_discord/charts/`: 生成されたチャート画像

## 🎯 配信内容

### Discord 配信（分析結果）

- 通貨相関分析サマリー
- テクニカル指標分析結果
- AI 戦略分析・売買シナリオ
- エントリーポイント、利確・損切り設定

### Discord 配信（チャート画像）

- USD/JPY H1 チャート（1 週間分）
- ローソク足（日本式）
- フィボナッチレベル（価格付き）
- 移動平均線（EMA20、EMA50、EMA200）
- 現在価格表示
