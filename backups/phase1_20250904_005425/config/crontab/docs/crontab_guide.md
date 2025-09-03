# 📋 Crontab 完全ガイド - Exchange Analytics 向け

## 🎯 基本構文

```
分 時 日 月 曜日 コマンド
*  *  *  *  *   /path/to/command
```

### 📝 各フィールドの詳細

| フィールド     | 値の範囲 | 説明                            |
| -------------- | -------- | ------------------------------- |
| 分 (minute)    | 0-59     | 実行する分                      |
| 時 (hour)      | 0-23     | 実行する時（24 時間形式）       |
| 日 (day)       | 1-31     | 実行する日                      |
| 月 (month)     | 1-12     | 実行する月                      |
| 曜日 (weekday) | 0-7      | 実行する曜日（0 と 7 は日曜日） |

### 🔧 特殊文字

| 文字 | 意味       | 例                                          |
| ---- | ---------- | ------------------------------------------- |
| `*`  | すべての値 | `* * * * *` = 毎分実行                      |
| `,`  | 複数値指定 | `0,30 * * * *` = 0 分と 30 分に実行         |
| `-`  | 範囲指定   | `0 9-17 * * *` = 9 時から 17 時まで毎時実行 |
| `/`  | 間隔指定   | `*/15 * * * *` = 15 分間隔で実行            |
| `?`  | 任意の値   | 日または曜日で使用                          |

## 🚀 Exchange Analytics 実用例

### 📊 基本的な定期実行

```bash
# 15分間隔でデータ取得
*/15 * * * * cd /app && python data_scheduler.py --test

# 毎時0分にAI分析
0 * * * * cd /app && python real_ai_discord.py USD/JPY

# 毎日9時に日次レポート
0 9 * * * cd /app && python data_scheduler.py --test
```

### 🕒 時間指定の例

```bash
# 平日の市場時間のみ（9:00-17:00）
0 9-17 * * 1-5 command

# 毎週月曜日の9時
0 9 * * 1 command

# 月末（30日と31日）
0 0 30,31 * * command

# 平日の30分間隔（9:00-17:30）
*/30 9-17 * * 1-5 command
```

### 🌍 JST（日本時間）対応

```bash
# システムタイムゾーンがUTCの場合、JST = UTC+9時間
# JST 9:00 = UTC 0:00
0 0 * * * command  # JST 9:00実行

# JST 17:00 = UTC 8:00
0 8 * * * command  # JST 17:00実行
```

## 🛠️ 実践的な設定手順

### 1️⃣ 環境変数の設定

```bash
# crontabファイルの先頭に環境変数を設定
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/app
ALPHA_VANTAGE_API_KEY=your_key_here
OPENAI_API_KEY=your_openai_key
DISCORD_WEBHOOK_URL=your_webhook_url
```

### 2️⃣ ログ設定

```bash
# 標準出力とエラーをログファイルに保存
command >> /app/logs/cron.log 2>&1

# エラーのみログ
command 2>> /app/logs/cron_error.log

# 出力を破棄
command > /dev/null 2>&1
```

### 3️⃣ タイムアウト設定

```bash
# 10秒でタイムアウト
timeout 10 command

# 1分でタイムアウト
timeout 60 python script.py
```

## 📈 Exchange Analytics 推奨設定

### 🔄 メインスケジュール

```bash
# Exchange Analytics Crontab設定
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/app

# 環境変数（実際の値に置き換え）
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
OPENAI_API_KEY=your_openai_key
DISCORD_WEBHOOK_URL=your_discord_webhook

# 15分間隔データ取得（平日市場時間）
*/15 9-17 * * 1-5 cd /app && timeout 300 python data_scheduler.py --test >> /app/logs/data_cron.log 2>&1

# 1時間間隔AI分析（平日のみ）
0 */1 9-17 * * 1-5 cd /app && timeout 120 python real_ai_discord.py USD/JPY >> /app/logs/ai_cron.log 2>&1

# 日次レポート（毎日18:00 JST）
0 9 * * * cd /app && timeout 60 python -c "
import asyncio
from data_scheduler import DataScheduler
scheduler = DataScheduler()
asyncio.run(scheduler._send_daily_report())
" >> /app/logs/daily_cron.log 2>&1

# システム監視（30分間隔）
*/30 * * * * cd /app && timeout 30 python realtime_monitor.py --interval 1 --no-alerts >> /app/logs/monitor_cron.log 2>&1

# ログクリーンアップ（毎日2:00 JST = UTC 17:00）
0 17 * * * cd /app/logs && find . -name "*.log" -size +10M -exec gzip {} \; && find . -name "*.gz" -mtime +7 -delete
```

### 🚨 エラー監視

```bash
# エラーログ監視（5分間隔）
*/5 * * * * [ -f /app/logs/data_scheduler.log ] && tail -20 /app/logs/data_scheduler.log | grep -i "error\|failed" && echo "$(date): Errors detected" >> /app/logs/error_alert.log

# API稼働確認（10分間隔）
*/10 * * * * cd /app && timeout 10 curl -s http://localhost:8000/health || echo "$(date): API down" >> /app/logs/api_alert.log
```

## 🛠️ Crontab 管理コマンド

### 📝 編集・表示

```bash
# crontab編集
crontab -e

# 現在のcrontab表示
crontab -l

# crontabを削除
crontab -r

# ファイルからcrontabを読み込み
crontab /path/to/crontab_file

# 特定ユーザーのcrontab編集（rootのみ）
crontab -e -u username
```

### 🔍 デバッグ・監視

```bash
# cron実行ログ確認（システムによって異なる）
tail -f /var/log/cron
tail -f /var/log/syslog | grep CRON

# cron daemon状態確認
systemctl status cron
systemctl status crond

# 手動でcronジョブテスト
cd /app && python data_scheduler.py --test
```

## ⚠️ よくある問題と解決法

### 1️⃣ 環境変数が読み込まれない

```bash
# 解決法1: crontab内で明示的に設定
ALPHA_VANTAGE_API_KEY=your_key

# 解決法2: .envファイル読み込み
*/15 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && python script.py

# 解決法3: シェルスクリプト経由
*/15 * * * * /app/run_scheduler.sh
```

### 2️⃣ パスが見つからない

```bash
# 解決法: 絶対パス使用
*/15 * * * * cd /app && /usr/bin/python3 /app/data_scheduler.py --test

# PATH設定
PATH=/usr/local/bin:/usr/bin:/bin
```

### 3️⃣ 権限エラー

```bash
# 解決法: 実行権限確認
chmod +x /app/data_scheduler.py
chmod +x /app/run_scheduler.sh

# ログディレクトリの権限
chmod 755 /app/logs
```

### 4️⃣ タイムゾーン問題

```bash
# システムタイムゾーン確認
timedatectl
date

# タイムゾーン設定
export TZ=Asia/Tokyo
```

## 🎯 実際の設定例

### 📊 段階的なスケジュール

```bash
# Phase 1: データ取得のみ（15分間隔）
*/15 * * * * cd /app && python data_scheduler.py --test >> /app/logs/phase1.log 2>&1

# Phase 2: AI分析追加（1時間間隔）
0 * * * * cd /app && python real_ai_discord.py USD/JPY >> /app/logs/phase2.log 2>&1

# Phase 3: 複数通貨対応
0 */2 * * * cd /app && for pair in USD/JPY EUR/USD GBP/USD; do python real_ai_discord.py $pair; sleep 30; done >> /app/logs/phase3.log 2>&1
```

### 🔄 メンテナンス

```bash
# 週次システムチェック（毎週日曜日1:00）
0 16 * * 0 cd /app && python -c "
import subprocess
import json
try:
    # システム統計収集
    result = subprocess.run(['df', '-h'], capture_output=True, text=True)
    print(f'Disk usage: {result.stdout}')
    # 追加の監視コード
except Exception as e:
    print(f'Weekly check error: {e}')
" >> /app/logs/weekly_check.log 2>&1

# 月次ログアーカイブ（毎月1日2:00）
0 17 1 * * cd /app && tar -czf logs/archive_$(date +%Y%m).tar.gz logs/*.log && rm logs/*.log
```

これで基本的な crontab 設定は完璧です！🎉
