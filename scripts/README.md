# 📊 Scripts Directory

Exchange Analytics システムの運用スクリプト管理

## 📁 ディレクトリ構造

```
scripts/
├── cron/          # cron実行スクリプト
├── monitoring/    # 監視・ヘルスチェック
├── deployment/    # デプロイメント
└── README.md      # このファイル
```

## ⏰ **cron/** - cron 実行スクリプト

| ファイル                    | 用途                     | 実行間隔  | 説明                          |
| --------------------------- | ------------------------ | --------- | ----------------------------- |
| `data_scheduler.py`         | データ取得スケジューラー | 15 分     | Alpha Vantage FX データ取得   |
| `real_ai_discord.py`        | AI 分析・Discord 配信    | 1 時間    | GPT 分析結果を Discord に配信 |
| `ai_discord_integration.py` | AI 統合分析              | 随時      | 総合 AI 分析システム          |
| `daily_report.py`           | 日次レポート             | 毎日 0 時 | 日次統計レポート送信          |
| `weekly_report.py`          | 週次レポート             | 毎週月曜  | 週次システム統計              |
| `yahoo_finance_discord.py`  | Yahoo Finance 配信       | 30 分     | Yahoo Finance 為替レポート    |

### 実行方法

```bash
# データスケジューラー（テスト実行）
cd /app && python scripts/cron/data_scheduler.py --test

# AI分析・Discord配信
cd /app && python scripts/cron/real_ai_discord.py USD/JPY

# Yahoo Finance為替レポート
cd /app && python scripts/cron/yahoo_finance_discord.py --type rates
```

## 📊 **monitoring/** - 監視・ヘルスチェック

| ファイル              | 用途             | 実行間隔 | 説明                              |
| --------------------- | ---------------- | -------- | --------------------------------- |
| `realtime_monitor.py` | リアルタイム監視 | 随時     | システム状態リアルタイム表示      |
| `cron_monitor.py`     | cron 監視        | 随時     | cron ジョブログのリアルタイム監視 |

### 実行方法

```bash
# リアルタイムシステム監視（30秒間）
cd /app && python scripts/monitoring/realtime_monitor.py --interval 1

# cron監視（30秒間）
cd /app && python scripts/monitoring/cron_monitor.py
```

## 🚀 **deployment/** - デプロイメント

継承済みのデプロイメントスクリプト（既存）

## 🔄 **crontab 統合**

### 本番 crontab 設定例

```bash
# データ取得（15分間隔、平日市場時間）
*/15 9-17 * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 300 python scripts/cron/data_scheduler.py --test >> /app/logs/data_cron.log 2>&1

# AI分析・Discord配信（1時間間隔）
0 */1 9-17 * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 120 python scripts/cron/real_ai_discord.py USD/JPY >> /app/logs/ai_cron.log 2>&1

# Yahoo Finance配信（30分間隔）
*/30 9-17 * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 60 python scripts/cron/yahoo_finance_discord.py --type rates >> /app/logs/yahoo_cron.log 2>&1

# リアルタイム監視（30分間隔）
*/30 * * * * cd /app && timeout 10 python scripts/monitoring/realtime_monitor.py --interval 1 --no-alerts >> /app/logs/health_cron.log 2>&1
```

## 📋 **環境変数要件**

各スクリプトで必要な環境変数：

### API 系スクリプト

```env
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
OPENAI_API_KEY=your_openai_key
DISCORD_WEBHOOK_URL=your_discord_webhook
```

### その他

```env
JWT_SECRET=your_jwt_secret
```

## 🔧 **開発・運用ガイド**

### 新しい cron スクリプト追加

1. `scripts/cron/`に新しいスクリプトを配置
2. 適切なエラーハンドリングを実装
3. ログ出力を標準化
4. crontab 設定を更新

### 監視スクリプト追加

1. `scripts/monitoring/`に配置
2. Rich UI を使用してきれいな表示
3. アラート機能を実装
4. 必要に応じて Discord 通知を追加

### テンプレート構造

```python
#!/usr/bin/env python3
"""
スクリプト名と説明
"""

import asyncio
import os
import sys
from datetime import datetime

import pytz
from rich.console import Console

# プロジェクトパス追加
sys.path.append("/app")

class YourScript:
    def __init__(self):
        self.console = Console()
        self.jst = pytz.timezone("Asia/Tokyo")

    async def main_function(self):
        # メイン処理
        pass

async def main():
    script = YourScript()
    await script.main_function()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📞 **トラブルシューティング**

### よくある問題

1. **ImportError**: `sys.path.append('/app')`を確認
2. **環境変数エラー**: `.env`ファイルと crontab での環境変数読み込みを確認
3. **タイムアウト**: crontab での timeout 設定を確認
4. **権限エラー**: スクリプトファイルの実行権限を確認

### デバッグコマンド

```bash
# スクリプト実行権限確認
ls -la scripts/cron/

# 手動実行テスト
cd /app && python scripts/cron/data_scheduler.py --test

# ログ確認
tail -f /app/logs/data_cron.log
```

### パフォーマンス最適化

- API 制限を考慮したレート制限
- 適切なタイムアウト設定
- 非同期処理の活用
- エラー時の自動リトライ

## 📈 **監視指標**

### 重要な監視項目

- データ取得成功率
- API 応答時間
- Discord 配信成功率
- システムリソース使用率
- エラー発生頻度

### アラート条件

- データ取得失敗率 > 50%
- API 応答時間 > 30 秒
- 2 時間以上データ取得なし
- システムメモリ使用率 > 90%
