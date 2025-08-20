# 📚 Exchange Analytics System CLI 機能説明書

**旧ファイル名**: `CLI機能説明書.md`  
**作成日**: 2025 年 1 月 15 日  
**更新日**: 2025 年 8 月 16 日  
**バージョン**: 2.1.0  
**対象システム**: Exchange Analytics System CLI

## 📋 概要

Exchange Analytics System CLI は、USD/JPY 為替分析システムの管理・運用を行うためのコマンドラインツールです。データ管理、API サーバー管理、監視、設定管理、AI 分析などの機能を提供します。

### 🚀 メインコマンド

```bash
python -m src.presentation.cli.main [コマンド] [オプション]
```

## 📁 コマンド構成

### 1. 🌐 `api` - API サーバー管理

API サーバーの起動・停止・状態確認を行うコマンド群です。

#### 📋 利用可能コマンド

| コマンド | 機能             | 説明                     |
| -------- | ---------------- | ------------------------ |
| `start`  | API サーバー起動 | FastAPI サーバーを起動   |
| `stop`   | API サーバー停止 | 実行中のサーバーを停止   |
| `status` | サーバー状態確認 | サーバーの稼働状況を確認 |
| `logs`   | ログ表示         | サーバーログを表示       |

#### 🔧 主要コマンド詳細

##### `api start` - API サーバー起動

**機能**: FastAPI サーバーを起動します。

**目的**: システムの API エンドポイントを提供し、外部からのアクセスを受け付けます。

**オプション**:

- `--host, -h`: バインドホスト (デフォルト: 0.0.0.0)
- `--port, -p`: ポート番号 (デフォルト: 8000)
- `--reload, -r`: ホットリロード有効
- `--workers, -w`: ワーカー数 (デフォルト: 1)
- `--log-level, -l`: ログレベル (デフォルト: info)
- `--background, -d`: バックグラウンド実行

**結果**: API サーバーが起動し、指定されたホスト・ポートでリクエストを受け付けます。

**コマンド例**:

```bash
# 基本的な起動
python -m src.presentation.cli.main api start

# カスタムポートで起動
python -m src.presentation.cli.main api start --port 8080

# ホットリロード有効で起動
python -m src.presentation.cli.main api start --reload

# バックグラウンドで起動
python -m src.presentation.cli.main api start --background
```

##### `api stop` - API サーバー停止

**機能**: 実行中の API サーバーを停止します。

**目的**: サーバーを安全に停止し、リソースを解放します。

**結果**: サーバーが停止し、ポートが解放されます。

**コマンド例**:

```bash
python -m src.presentation.cli.main api stop
```

##### `api status` - サーバー状態確認

**機能**: API サーバーの稼働状況を確認します。

**目的**: サーバーが正常に動作しているかを確認します。

**結果**: サーバーの状態、レスポンス時間、稼働時間などの情報を表示します。

**コマンド例**:

```bash
python -m src.presentation.cli.main api status
```

### 2. 💱 `data` - データ管理・取得

為替データの取得・表示・管理を行うコマンド群です。**2025 年 8 月 15 日の更新により、機能別に分割された階層構造に変更されました。**

#### 🏗️ 新しい階層構造

```
data/
├── show/     📊 データ表示コマンド
├── fetch/    📥 データ取得コマンド
├── backup/   💾 バックアップ・復元コマンド
├── calc/     🧮 計算・分析コマンド
└── manage/   ⚙️ データ管理コマンド
```

#### 📋 利用可能サブコマンド

| サブコマンド | 機能                  | 説明                             |
| ------------ | --------------------- | -------------------------------- |
| `show`       | 📊 データ表示コマンド | データベースの状態・データ表示   |
| `fetch`      | 📥 データ取得コマンド | 為替データの取得・初期化         |
| `backup`     | 💾 バックアップ・復元 | データベースのバックアップ・復元 |
| `calc`       | 🧮 計算・分析コマンド | テクニカル指標の計算・分析       |
| `manage`     | ⚙️ データ管理コマンド | システムセットアップ・管理       |

#### 🔧 各サブコマンドの詳細

##### 📊 `data show` - データ表示コマンド

**機能**: データベースの状態とデータを表示します。

**特徴**:

- 環境変数`DATABASE_URL`を自動設定し、PostgreSQL データベースに直接接続
- SQLite エラーを回避し、確実に PostgreSQL に接続
- データベースの状態確認とデータ表示を統合管理

**利用可能コマンド**:

| コマンド | 機能             | 説明                                |
| -------- | ---------------- | ----------------------------------- |
| `data`   | データ表示       | 価格データ・テクニカル指標を表示    |
| `status` | データベース状態 | PostgreSQL データベースの状態を表示 |

**コマンド例**:

```bash
# データベースの状態確認
python -m src.presentation.cli.main data show status

# 価格データの表示
python -m src.presentation.cli.main data show data --table price_data

# テクニカル指標の表示
python -m src.presentation.cli.main data show data --table technical_indicators

# 特定の指標をフィルタリング
python -m src.presentation.cli.main data show data --table technical_indicators --indicator-type RSI --period 14

# 時間足と件数指定で価格データ表示
python -m src.presentation.cli.main data show data --timeframe 5m --limit 50
```

##### 📥 `data fetch` - データ取得コマンド

**機能**: 為替データの取得とシステム初期化を行います。

**特徴**:

- 環境変数`PYTHONPATH`を自動設定し、モジュールインポートエラーを回避
- `differential_updater.py`スクリプトを直接呼び出し、無限ループを防止
- 実行結果の詳細出力を表示

**利用可能コマンド**:

| コマンド       | 機能           | 説明                            |
| -------------- | -------------- | ------------------------------- |
| `fetch`        | 為替データ取得 | 外部 API から為替データを取得   |
| `init`         | システム初期化 | 基盤データ復元 + 差分データ取得 |
| `restore-base` | 基盤データ復元 | SQLite バックアップから復元     |
| `update`       | 差分データ更新 | 最新データを差分取得            |

**コマンド例**:

```bash
# システム完全初期化
python -m src.presentation.cli.main data fetch init

# 基盤データのみ復元
python -m src.presentation.cli.main data fetch restore-base

# 差分データ更新
python -m src.presentation.cli.main data fetch update

# 為替データ取得（シミュレーション）
python -m src.presentation.cli.main data fetch fetch --pairs "USD/JPY,EUR/USD"
```

##### 💾 `data backup` - バックアップ・復元コマンド

**機能**: PostgreSQL データベースのバックアップと復元を行います。

**利用可能コマンド**:

| コマンド  | 機能                     | 説明                                  |
| --------- | ------------------------ | ------------------------------------- |
| `backup`  | データベースバックアップ | PostgreSQL データベースをバックアップ |
| `restore` | データベース復元         | バックアップからデータベースを復元    |

**コマンド例**:

```bash
# データベースバックアップ
python -m src.presentation.cli.main data backup backup --output my_backup.sql

# データのみバックアップ
python -m src.presentation.cli.main data backup backup --data-only

# バックアップから復元
python -m src.presentation.cli.main data backup restore backup.sql

# 確認なしで復元
python -m src.presentation.cli.main data backup restore backup.sql --force
```

##### 🧮 `data calc` - 計算・分析コマンド

**機能**: テクニカル指標の計算と分析を行います。

**利用可能コマンド**:

| コマンド                     | 機能                       | 説明                                   |
| ---------------------------- | -------------------------- | -------------------------------------- |
| `calculate`                  | テクニカル指標計算         | 基本的なテクニカル指標を計算           |
| `test-technical-calculator`  | テクニカル指標計算         | 差分検知機能付きの統合計算実行（推奨） |
| `visualize`                  | 指標可視化                 | テクニカル指標を可視化                 |
| `detect-divergences`         | ダイバージェンス検出       | 価格と指標の乖離を検出                 |
| `analyze-support-resistance` | サポート・レジスタンス分析 | 支持線・抵抗線を分析                   |
| `analyze-momentum`           | モメンタム分析             | 価格の勢いを分析                       |
| `comprehensive-analysis`     | 包括的分析                 | 複数の分析を統合実行                   |
| `analyze-signals`            | トレードシグナル分析       | 売買シグナルを分析                     |

**コマンド例**:

```bash
# テクニカル指標計算
python -m src.presentation.cli.main data calc calculate --limit 300

# テクニカル指標計算（差分検知機能付き）
python -m src.presentation.cli.main data calc test-technical-calculator --diff-only --limit 300

# 指標可視化
python -m src.presentation.cli.main data calc visualize --indicator RSI --period 14

# ダイバージェンス検出
python -m src.presentation.cli.main data calc detect-divergences --pair USD/JPY

# 包括的分析
python -m src.presentation.cli.main data calc comprehensive-analysis
```

#### 🔧 主要計算コマンド詳細

##### `data calc test-technical-calculator` - テクニカル指標計算（統合版）

**機能**: 差分検知機能付きのテクニカル指標計算を実行します。

**目的**: 未計算データのみを効率的に処理し、差分検知機能を活用した計算を実行します。

**特徴**:

- **統合コマンド**: 旧`calculate-unified`コマンドの機能を統合
- **差分検知**: 未計算データのみを効率的に処理
- **環境変数自動設定**: `DATABASE_URL`と`PYTHONPATH`を自動設定
- **本番対応**: テスト機能から本番機能に進化

**オプション**:

- `--limit, -l`: 各時間足の取得件数制限（例: 10, 50, 100）
- `--diff-only, -d`: 差分検知のみ実行（未計算データのみ）
- `--full, -f`: 制限なしで全件計算（本番実行）

**結果**: 計算結果と差分検知結果が表示されます。

**コマンド例**:

```bash
# 基本的な計算（制限10件）
python -m src.presentation.cli.main data calc test-technical-calculator --limit 10

# 差分検知のみ実行
python -m src.presentation.cli.main data calc test-technical-calculator --diff-only --limit 50

# 本番実行（制限なし）
python -m src.presentation.cli.main data calc test-technical-calculator --full
```

**出力例**:

```
🧮 テクニカル指標計算開始（差分検知機能付き）...
🔧 コマンド: python scripts/cron/test_technical_calculator.py --diff-only --limit 10
✅ テクニカル指標計算完了
📊 差分検知結果サマリー
📈 実行ステータス: success
⏱️ 実行時間: 8.58秒
📊 処理件数: 421件
🔍 差分検知結果:
   📈 5m: 67件の未計算データ
   📈 1h: 5件の未計算データ
   📈 4h: 12件の未計算データ
   📈 1d: 1件の未計算データ
📊 全体進捗: 3.4%
```

##### ⚙️ `data manage` - データ管理コマンド

**機能**: システムのセットアップとデータ管理を行います。

**利用可能コマンド**:

| コマンド   | 機能                 | 説明                       |
| ---------- | -------------------- | -------------------------- |
| `setup`    | システムセットアップ | 完全なシステム初期化       |
| `clear`    | テーブルクリア       | 指定テーブルのデータを削除 |
| `optimize` | データベース最適化   | データベースの最適化       |
| `validate` | データ整合性検証     | データの整合性を検証       |
| `cleanup`  | データクリーンアップ | 不要データの削除           |

**コマンド例**:

```bash
# システムセットアップ
python -m src.presentation.cli.main data manage setup

# テクニカル指標テーブルクリア
python -m src.presentation.cli.main data manage clear --table technical_indicators

# 確認なしでクリア
python -m src.presentation.cli.main data manage clear --table price_data --confirm

# データベース最適化
python -m src.presentation.cli.main data manage optimize

# データ整合性検証
python -m src.presentation.cli.main data manage validate
```

### 3. ⚙️ `config` - 設定管理

システム設定の表示・変更・管理を行うコマンド群です。

#### 📋 利用可能コマンド

| コマンド   | 機能             | 説明                       |
| ---------- | ---------------- | -------------------------- |
| `show`     | 設定表示         | 現在の設定を表示           |
| `set`      | 設定変更         | 設定値を変更               |
| `reset`    | 設定リセット     | 設定をデフォルトに戻す     |
| `validate` | 設定検証         | 設定の妥当性を検証         |
| `export`   | 設定エクスポート | 設定をファイルに出力       |
| `import`   | 設定インポート   | ファイルから設定を読み込み |

#### 🔧 主要コマンド詳細

##### `config show` - 設定表示

**機能**: 現在のシステム設定を表示します。

**目的**: 設定値を確認し、システムの状態を把握します。

**オプション**:

- `--format, -f`: 出力形式 (json, yaml, table) (デフォルト: table)
- `--section, -s`: 特定のセクションのみ表示

**結果**: 現在の設定が指定された形式で表示されます。

**コマンド例**:

```bash
# 基本的な設定表示
python -m src.presentation.cli.main config show

# JSON形式で表示
python -m src.presentation.cli.main config show --format json

# データベース設定のみ表示
python -m src.presentation.cli.main config show --section database
```

##### `config set` - 設定変更

**機能**: システム設定を変更します。

**目的**: 設定値を動的に変更し、システムの動作を調整します。

**オプション**:

- `--key, -k`: 設定キー (必須)
- `--value, -v`: 設定値 (必須)
- `--section, -s`: 設定セクション

**結果**: 指定された設定が更新されます。

**コマンド例**:

```bash
# データベース接続設定を変更
python -m src.presentation.cli.main config set --key host --value localhost --section database

# API設定を変更
python -m src.presentation.cli.main config set --key timeout --value 30 --section api
```

### 4. 📊 `monitor` - 監視・ヘルスチェック

システムの監視とヘルスチェックを行うコマンド群です。

#### 📋 利用可能コマンド

| コマンド      | 機能               | 説明                   |
| ------------- | ------------------ | ---------------------- |
| `health`      | ヘルスチェック     | システムの健全性を確認 |
| `performance` | パフォーマンス監視 | システムの性能を監視   |
| `logs`        | ログ監視           | システムログを監視     |
| `alerts`      | アラート管理       | アラートの設定・管理   |

#### 🔧 主要コマンド詳細

##### `monitor health` - ヘルスチェック

**機能**: システム全体の健全性を確認します。

**目的**: 各コンポーネントが正常に動作しているかを確認します。

**オプション**:

- `--continuous, -c`: 継続監視モード
- `--interval, -i`: チェック間隔（秒） (デフォルト: 30)
- `--timeout, -t`: タイムアウト時間（秒） (デフォルト: 10)

**結果**: 各コンポーネントの状態が表示されます。

**コマンド例**:

```bash
# 基本的なヘルスチェック
python -m src.presentation.cli.main monitor health

# 継続監視モード
python -m src.presentation.cli.main monitor health --continuous

# 5秒間隔でチェック
python -m src.presentation.cli.main monitor health --interval 5
```

##### `monitor performance` - パフォーマンス監視

**機能**: システムの性能指標を監視します。

**目的**: CPU、メモリ、ディスク、ネットワークの使用状況を確認します。

**オプション**:

- `--continuous, -c`: 継続監視モード
- `--interval, -i`: 更新間隔（秒） (デフォルト: 5)
- `--history, -h`: 履歴表示

**結果**: システムの性能指標が表示されます。

**コマンド例**:

```bash
# 基本的なパフォーマンス監視
python -m src.presentation.cli.main monitor performance

# 継続監視モード
python -m src.presentation.cli.main monitor performance --continuous

# 履歴付きで表示
python -m src.presentation.cli.main monitor performance --history
```

### 5. 🤖 `ai` - AI 分析・通知

AI による為替分析と通知機能を提供するコマンド群です。

#### 📋 利用可能コマンド

| コマンド  | 機能         | 説明                       |
| --------- | ------------ | -------------------------- |
| `analyze` | AI 分析実行  | 為替データの AI 分析を実行 |
| `notify`  | 通知送信     | 分析結果を通知             |
| `reports` | レポート一覧 | 生成されたレポートを表示   |

#### 🔧 主要コマンド詳細

##### `ai analyze` - AI 分析実行

**機能**: 指定された通貨ペアの AI 分析を実行します。

**目的**: 機械学習モデルを使用して為替データを分析し、予測や洞察を提供します。

**オプション**:

- `--pair, -p`: 通貨ペア (デフォルト: USD/JPY)
- `--timeframe, -t`: 時間足 (デフォルト: 5m)
- `--model, -m`: 使用するモデル
- `--discord, -d`: Discord 通知を有効
- `--no-discord`: Discord 通知を無効
- `--demo`: デモデータを使用

**結果**: AI 分析結果が表示され、必要に応じて通知が送信されます。

**コマンド例**:

```bash
# 基本的なAI分析
python -m src.presentation.cli.main ai analyze

# 特定の通貨ペアを分析
python -m src.presentation.cli.main ai analyze --pair EUR/USD

# Discord通知なしで分析
python -m src.presentation.cli.main ai analyze GBP/JPY --no-discord

# デモデータで分析
python -m src.presentation.cli.main ai analyze USD/JPY --demo
```

##### `ai reports` - レポート一覧

**機能**: 生成された AI 分析レポートの一覧を表示します。

**目的**: 過去に生成されたレポートを確認します。

**オプション**:

- `--limit, -n`: 表示件数 (デフォルト: 10)
- `--pair, -p`: 通貨ペアフィルタ

**結果**: 生成されたレポートの一覧が表示されます。

**コマンド例**:

```bash
# 基本的なレポート一覧
python -m src.presentation.cli.main ai reports

# 最新5件を表示
python -m src.presentation.cli.main ai reports --limit 5

# USD/JPYのレポートのみ表示
python -m src.presentation.cli.main ai reports --pair USD/JPY
```

## 🎯 よく使用されるコマンド例

### システム起動シーケンス

```bash
# 1. システム完全初期化
python -m src.presentation.cli.main data fetch init

# 2. データベース状態確認
python -m src.presentation.cli.main data show status

# 3. APIサーバー起動
python -m src.presentation.cli.main api start --reload

# 4. ヘルスチェック
python -m src.presentation.cli.main monitor health
```

### 日常的な運用

```bash
# データ確認
python -m src.presentation.cli.main data show data --table price_data

# テクニカル指標計算（差分検知機能付き・統合版）
python -m src.presentation.cli.main data calc test-technical-calculator --diff-only --limit 300

# 指標可視化
python -m src.presentation.cli.main data calc visualize --indicator RSI

# AI分析実行
python -m src.presentation.cli.main ai analyze USD/JPY

# システム監視
python -m src.presentation.cli.main monitor health --continuous
```

### データ管理

```bash
# バックアップ作成
python -m src.presentation.cli.main data backup backup --output daily_backup.sql

# 差分データ更新
python -m src.presentation.cli.main data fetch update

# テーブルクリア（再計算用）
python -m src.presentation.cli.main data manage clear --table technical_indicators

# データ整合性検証
python -m src.presentation.cli.main data manage validate
```

### トラブルシューティング

```bash
# 設定確認
python -m src.presentation.cli.main config show

# パフォーマンス監視
python -m src.presentation.cli.main monitor performance

# ログ確認
python -m src.presentation.cli.main monitor logs

# データベース最適化
python -m src.presentation.cli.main data manage optimize
```

## 📝 注意事項

1. **権限**: 一部のコマンドは管理者権限が必要な場合があります
2. **ネットワーク**: データ取得コマンドはインターネット接続が必要です
3. **API 制限**: 外部 API には利用制限がある場合があります
4. **データベース**: PostgreSQL データベースが起動していることを確認してください
5. **ファイル分割**: 2025 年 8 月 15 日の更新により、data コマンドが機能別に分割されました
6. **環境変数**: `data show`と`data fetch`コマンドは環境変数を自動設定します
7. **コマンド統合**: `calculate-unified`コマンドは`test-technical-calculator`に統合されました

## 🔧 トラブルシューティング

### よくある問題と解決方法

| 問題               | 原因                          | 解決方法                    |
| ------------------ | ----------------------------- | --------------------------- |
| 接続エラー         | サーバーが起動していない      | `api start`でサーバーを起動 |
| データ取得失敗     | API 制限に達した              | しばらく待ってから再実行    |
| 設定エラー         | 設定ファイルが不正            | `config validate`で検証     |
| データベースエラー | PostgreSQL が起動していない   | PostgreSQL サービスを起動   |
| SQLite エラー      | 環境変数が設定されていない    | CLI コマンドが自動設定済み  |
| モジュールエラー   | PYTHONPATH が設定されていない | CLI コマンドが自動設定済み  |

### 新しい階層構造について

2025 年 8 月 15 日の更新により、`data`コマンドが以下のように分割されました：

- **ファイル構造**: `src/presentation/cli/commands/data/`ディレクトリ配下に機能別ファイル
- **コマンド構造**: `data [サブコマンド] [アクション]`の形式
- **利点**: ファイルサイズの削減、責任の分離、保守性の向上

#### 📁 分割されたファイル構成

```
src/presentation/cli/commands/data/
├── __init__.py                    # パッケージ初期化（統合）
├── data_show_commands.py         # 📊 データ表示コマンド（407行）
├── data_fetch_commands.py        # 📥 データ取得コマンド（214行）
├── data_backup_commands.py       # 💾 バックアップ・復元コマンド（207行）
├── data_calculation_commands.py  # 🧮 計算・分析コマンド（444行）
└── data_management_commands.py   # ⚙️ データ管理コマンド（224行）
```

#### 🔄 移行前後の比較

| 項目               | 移行前                     | 移行後                 |
| ------------------ | -------------------------- | ---------------------- |
| ファイル数         | 1 個（data_commands.py）   | 6 個（パッケージ構造） |
| 最大ファイルサイズ | 2,512 行                   | 444 行                 |
| 責任分離           | 単一ファイルに全機能       | 機能別に分割           |
| 保守性             | 低（ファイルが大きすぎる） | 高（機能別管理）       |
| チーム開発         | 困難（競合が発生）         | 容易（並行開発可能）   |

#### 🆕 最新の改善点（2025 年 8 月 15 日以降）

| 改善項目         | 内容                                                   | 効果                    |
| ---------------- | ------------------------------------------------------ | ----------------------- |
| 環境変数自動設定 | `data show`と`data fetch`で自動設定                    | SQLite エラーの完全解決 |
| コマンド統合     | `calculate-unified`を`test-technical-calculator`に統合 | 重複排除、機能統一      |
| 無限ループ修正   | `data fetch update`の無限ループを修正                  | 安定したデータ更新      |
| 出力表示改善     | サブプロセス実行結果の詳細表示                         | デバッグ情報の充実      |

## 📚 関連ドキュメント

- [システム設計書](../note/アーキテクチャ設計/2025-08-09_基本設計_基本設計書.md)
- [CLI システム設計書](../note/CLI・データ管理/2025-01_システム設計_CLIデータベース初期化システム設計書.md)
- [API 仕様書](../note/API最適化/2025-01_システム設計_API最適化設計書.md)
- [PostgreSQL 移行ガイド](../note/データベース/PostgreSQL_MIGRATION_README.md)
