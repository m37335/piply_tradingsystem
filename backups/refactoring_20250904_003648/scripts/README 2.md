# 📊 Scripts Directory

Exchange Analytics USD/JPY パターン検出システム - 運用スクリプト管理

## 🚀 **システム稼働状況**

**稼働開始**: 2025 年 8 月 10 日 日本時間 8:00 から
**稼働モード**: 24 時間自動稼働（平日）
**データ取得**: USD/JPY 5 分間隔
**パターン検出**: 6 つの為替パターンを自動検出
**通知**: Discord 自動配信

## 📁 ディレクトリ構造

```
scripts/
├── cron/          # cron実行スクリプト
├── monitoring/    # 監視・ヘルスチェック
├── deployment/    # デプロイメント
├── test/          # テストスクリプト
└── README.md      # このファイル
```

## ⏰ **cron/** - 本番稼働スクリプト

| ファイル              | 用途                     | 実行間隔      | 説明                 |
| --------------------- | ------------------------ | ------------- | -------------------- |
| `usdjpy_data_cron.py` | USD/JPY データ取得・分析 | 5 分間隔      | メイン稼働スクリプト |
| `daily_report.py`     | 日次レポート             | 毎日 6:00     | 日次統計レポート送信 |
| `weekly_report.py`    | 週次レポート             | 毎週土曜 6:00 | 週次システム統計     |

### メイン稼働スクリプト: `usdjpy_data_cron.py`

**機能**:

- USD/JPY 5 分足データ取得
- テクニカル指標計算（RSI、MACD、ボリンジャーバンド）
- 6 つのパターン検出
- Discord 自動通知
- エラーハンドリング・リカバリー

**実行方法**:

```bash
# 単発実行（テスト用）
cd /app && python scripts/cron/usdjpy_data_cron.py --once

# 継続実行（本番用）
cd /app && python scripts/cron/usdjpy_data_cron.py
```

## 📊 **monitoring/** - システム監視

| ファイル              | 用途             | 実行間隔  | 説明                         |
| --------------------- | ---------------- | --------- | ---------------------------- |
| `realtime_monitor.py` | リアルタイム監視 | 30 分間隔 | システム状態リアルタイム表示 |

### 監視項目

- CPU・メモリ使用率
- データベース接続状態
- データ取得成功率
- パターン検出状況
- Discord 通知状況

## 🚀 **deployment/** - デプロイメント

| ファイル                | 用途                 | 説明                       |
| ----------------------- | -------------------- | -------------------------- |
| `production_setup.py`   | 本番環境セットアップ | データベース・テーブル作成 |
| `production_startup.py` | 本番環境起動         | システム初期化・起動       |
| `deploy_production.py`  | 本番デプロイ         | 完全デプロイメント         |

## 🧪 **test/** - テストスクリプト

| ファイル                                 | 用途                       | 説明                     |
| ---------------------------------------- | -------------------------- | ------------------------ |
| `test_pattern_detection_with_discord.py` | パターン検出・Discord 通知 | 統合テスト               |
| `test_performance_optimization.py`       | パフォーマンス最適化       | システム性能テスト       |
| `test_error_recovery_system.py`          | エラーリカバリー           | エラーハンドリングテスト |
| `test_monitoring_system.py`              | 監視システム               | 監視機能テスト           |

## 🔄 **本番 crontab 設定**

### 現在の稼働設定

```bash
# Exchange Analytics Production Crontab - 24時間稼働版
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
HOME=/app

# 📊 基本データ取得（5分間隔、平日24時間稼働）
*/5 * * * 1-5 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 300 python scripts/cron/usdjpy_data_cron.py >> /app/logs/data_cron.log 2>&1

# 📈 日次レポート（毎日6:00 JST = 21:00 UTC）
0 21 * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 120 python scripts/cron/daily_report.py >> /app/logs/daily_cron.log 2>&1

# 📊 週次統計・レポート（毎週土曜日 6:00 JST = 21:00 UTC）
0 21 * * 6 cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 180 python scripts/cron/weekly_report.py >> /app/logs/weekly_cron.log 2>&1

# 🔍 システムヘルスチェック（30分間隔）
*/30 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 10 python scripts/monitoring/realtime_monitor.py --interval 1 --no-alerts >> /app/logs/health_cron.log 2>&1

# 🗑️ ログローテーション（毎日2:00 JST = 17:00 UTC）
0 17 * * * cd /app/logs && find . -name "*.log" -size +10M -exec gzip {} \; && find . -name "*.gz" -mtime +7 -delete >> /app/logs/cleanup.log 2>&1

# 🔍 エラーログ監視（10分間隔）
*/10 * * * * [ -f /app/logs/data_cron.log ] && tail -10 /app/logs/data_cron.log | grep -i "error\|failed" && echo "$(date): Data fetch errors detected" >> /app/logs/error_alert.log

# 🧪 環境変数テスト（30分間隔、デバッグ用）
*/30 * * * * cd /app && export $(cat .env | grep -v '^#' | xargs) && timeout 30 python tests/integration/test_env_loading.py >> /app/logs/env_test_cron.log 2>&1
```

## 📋 **環境変数要件**

### 必須環境変数

```env
# Discord通知
DISCORD_WEBHOOK_URL=https://canary.discord.com/api/webhooks/...
DISCORD_MONITORING_WEBHOOK_URL=https://canary.discord.com/api/webhooks/...

# データベース（テスト用SQLite）
DATABASE_URL=sqlite+aiosqlite:///data/test_app.db

# API設定
YAHOO_FINANCE_API_KEY=test_key
```

## 🔧 **開発・運用ガイド**

### システム稼働確認

```bash
# メインスクリプト動作確認
cd /app && python scripts/cron/usdjpy_data_cron.py --once

# ログ確認
tail -f /app/logs/data_cron.log

# システム監視
cd /app && python scripts/monitoring/realtime_monitor.py --interval 1
```

### 新しい機能追加

1. `scripts/cron/`に新しいスクリプトを配置
2. 適切なエラーハンドリングを実装
3. ログ出力を標準化
4. crontab 設定を更新
5. テストスクリプトを作成

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
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()

class YourScript:
    def __init__(self):
        self.running = False

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

1. **データベース接続エラー**: SQLite ファイルの権限確認
2. **Discord 通知エラー**: Webhook URL の確認
3. **インポートエラー**: PYTHONPATH 設定確認
4. **タイムアウト**: crontab の timeout 設定確認

### デバッグコマンド

```bash
# スクリプト実行権限確認
ls -la scripts/cron/

# 手動実行テスト
cd /app && python scripts/cron/usdjpy_data_cron.py --once

# ログ確認
tail -f /app/logs/data_cron.log

# エラーログ確認
tail -f /app/logs/error_alert.log
```

### パフォーマンス最適化

- 非同期処理の活用
- データベース接続プール
- エラー時の自動リトライ
- 適切なタイムアウト設定

## 📈 **監視指標**

### 重要な監視項目

- USD/JPY データ取得成功率
- テクニカル指標計算成功率
- パターン検出数
- Discord 通知成功率
- システムリソース使用率
- エラー発生頻度

### アラート条件

- データ取得失敗率 > 50%
- パターン検出失敗 > 30 分
- Discord 通知失敗 > 10 回連続
- システムメモリ使用率 > 90%

## 🎯 **システム機能**

### パターン検出機能

1. **トレンド転換パターン**: 上昇/下降トレンドの転換点検出
2. **プルバックパターン**: トレンド中の一時的な戻り検出
3. **ダイバージェンスパターン**: 価格と指標の乖離検出
4. **ブレイクアウトパターン**: 重要な価格レベルの突破検出
5. **RSI バトルパターン**: RSI 指標の戦い検出
6. **複合シグナルパターン**: 複数指標の組み合わせ検出

### テクニカル指標

- **RSI**: 相対力指数
- **MACD**: 移動平均収束拡散
- **ボリンジャーバンド**: 価格変動の統計的範囲

### 通知機能

- **Discord 通知**: パターン検出時の自動配信
- **システム監視**: システム状態の定期報告
- **エラー通知**: 異常発生時の即座通知

## 🚀 **今後の拡張予定**

- 追加パターン検出機能
- 機械学習による予測機能
- 複数通貨ペア対応
- Web UI ダッシュボード
- モバイルアプリ対応
