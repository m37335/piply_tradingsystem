# 時間足集計システム実装仕様書

## 📋 プロジェクト概要

**プロジェクト名**: Exchange Analytics System - 時間足集計システム実装仕様書  
**作成日**: 2025 年 8 月 15 日  
**バージョン**: 1.0.0  
**目的**: 設計書に基づく具体的な実装仕様の定義

---

## 🏗️ システムアーキテクチャ

### 依存関係図

```
hourly_aggregator.py
├── src/infrastructure/database/
│   ├── connection.py (データベース接続)
│   ├── models/price_data_model.py (データモデル)
│   └── repositories/price_data_repository_impl.py (リポジトリ)
├── src/infrastructure/external_apis/
│   └── yahoo_finance_client.py (外部API)
└── src/utils/
    └── logging_config.py (ログ設定)

four_hour_aggregator.py
└── (同上の依存関係)

daily_aggregator.py
└── (同上の依存関係)
```

### ファイル構成

```
/app/
├── scripts/cron/
│   ├── hourly_aggregator.py (新規)
│   ├── four_hour_aggregator.py (新規)
│   ├── daily_aggregator.py (新規)
│   └── simple_data_fetcher.py (既存・参考)
├── src/infrastructure/database/
│   ├── connection.py (既存)
│   ├── models/price_data_model.py (既存)
│   └── repositories/price_data_repository_impl.py (既存)
├── src/infrastructure/external_apis/
│   └── yahoo_finance_client.py (既存)
├── src/utils/
│   └── logging_config.py (既存)
├── logs/
│   ├── hourly_aggregator.log (新規)
│   ├── four_hour_aggregator.log (新規)
│   └── daily_aggregator.log (新規)
└── current_crontab.txt (更新)
```

---

## 📊 クラス設計

### BaseAggregator (基底クラス)

```python
class BaseAggregator:
    """
    時間足集計の基底クラス

    責任:
    - 共通の集計ロジック
    - データベース接続管理
    - エラーハンドリング
    - ログ出力
    """

    def __init__(self, timeframe: str, data_source: str):
        self.timeframe = timeframe  # "1h", "4h", "1d"
        self.data_source = data_source  # "yahoo_finance_1h_aggregated"
        self.currency_pair = "USD/JPY"
        self.db_url = None
        self.engine = None
        self.session_factory = None
        self.session = None
        self.price_repo = None

    async def initialize_database(self):
        """データベース接続を初期化"""

    async def cleanup(self):
        """リソースをクリーンアップ"""

    async def aggregate_and_save(self):
        """集計と保存を実行（抽象メソッド）"""
        raise NotImplementedError

    async def get_aggregation_period(self) -> tuple[datetime, datetime]:
        """集計期間を取得（抽象メソッド）"""
        raise NotImplementedError
```

### HourlyAggregator (1 時間足集計)

```python
class HourlyAggregator(BaseAggregator):
    """
    1時間足集計クラス

    責任:
    - 1時間足データの集計
    - 前1時間の5分足データからOHLCV計算
    - データベースへの保存
    """

    def __init__(self):
        super().__init__("1h", "yahoo_finance_1h_aggregated")

    async def get_aggregation_period(self) -> tuple[datetime, datetime]:
        """
        集計期間を取得

        Returns:
            tuple: (start_time, end_time) 前1時間の期間
        """
        # 現在時刻から1時間前を計算
        # 例: 01:05実行時 → 00:00-00:55の期間

    async def aggregate_and_save(self):
        """
        1時間足集計と保存を実行

        Workflow:
        1. 集計期間の決定
        2. 5分足データの取得
        3. OHLCV計算
        4. 重複チェック
        5. データベース保存
        """
```

### FourHourAggregator (4 時間足集計)

```python
class FourHourAggregator(BaseAggregator):
    """
    4時間足集計クラス

    責任:
    - 4時間足データの集計
    - 前4時間の5分足データからOHLCV計算
    - データベースへの保存
    """

    def __init__(self):
        super().__init__("4h", "yahoo_finance_4h_aggregated")

    async def get_aggregation_period(self) -> tuple[datetime, datetime]:
        """
        集計期間を取得

        Returns:
            tuple: (start_time, end_time) 前4時間の期間
        """
        # 4時間単位での期間計算
        # 例: 04:05実行時 → 00:00-03:55の期間
```

### DailyAggregator (日足集計)

```python
class DailyAggregator(BaseAggregator):
    """
    日足集計クラス

    責任:
    - 日足データの集計
    - 前日の5分足データからOHLCV計算
    - データベースへの保存
    """

    def __init__(self):
        super().__init__("1d", "yahoo_finance_1d_aggregated")

    async def get_aggregation_period(self) -> tuple[datetime, datetime]:
        """
        集計期間を取得

        Returns:
            tuple: (start_time, end_time) 前日の期間
        """
        # 前日の期間計算
        # 例: 00:05実行時 → 前日00:00-23:55の期間
```

---

## 🔄 ワークフロー詳細

### 1 時間足集計ワークフロー

```python
async def hourly_aggregation_workflow():
    """
    1時間足集計の完全なワークフロー

    Steps:
    1. 初期化
    2. 集計期間決定
    3. データ取得
    4. 集計計算
    5. 重複チェック
    6. データ保存
    7. クリーンアップ
    """

    # Step 1: 初期化
    aggregator = HourlyAggregator()
    await aggregator.initialize_database()

    try:
        # Step 2: 集計期間決定
        start_time, end_time = await aggregator.get_aggregation_period()
        logger.info(f"集計期間: {start_time} - {end_time}")

        # Step 3: データ取得
        five_min_data = await aggregator.get_five_min_data(start_time, end_time)
        if not five_min_data:
            logger.warning("集計対象データがありません")
            return

        # Step 4: 集計計算
        aggregated_data = await aggregator.calculate_ohlcv(five_min_data)

        # Step 5: 重複チェック
        existing = await aggregator.check_duplicate(aggregated_data.timestamp)
        if existing:
            logger.info("既存データが存在します。スキップします。")
            return

        # Step 6: データ保存
        await aggregator.save_aggregated_data(aggregated_data)
        logger.info(f"1時間足データを保存しました: {aggregated_data.timestamp}")

    except Exception as e:
        logger.error(f"集計処理エラー: {e}")
        raise
    finally:
        # Step 7: クリーンアップ
        await aggregator.cleanup()
```

### 集計計算ロジック

```python
async def calculate_ohlcv(self, five_min_data: List[PriceDataModel]) -> PriceDataModel:
    """
    OHLCV計算

    Args:
        five_min_data: 5分足データのリスト

    Returns:
        PriceDataModel: 集計されたOHLCVデータ
    """

    if not five_min_data:
        raise ValueError("集計対象データがありません")

    # データをタイムスタンプ順にソート
    sorted_data = sorted(five_min_data, key=lambda x: x.timestamp)

    # OHLCV計算
    open_price = sorted_data[0].open_price  # 最初の始値
    high_price = max(d.high_price for d in sorted_data)  # 最高値
    low_price = min(d.low_price for d in sorted_data)    # 最低値
    close_price = sorted_data[-1].close_price  # 最後の終値
    volume = sum(d.volume or 0 for d in sorted_data)     # 取引量合計

    # 集計タイムスタンプ（期間の開始時刻）
    aggregated_timestamp = sorted_data[0].timestamp.replace(
        minute=0, second=0, microsecond=0
    )

    return PriceDataModel(
        currency_pair=self.currency_pair,
        timestamp=aggregated_timestamp,
        data_timestamp=aggregated_timestamp,
        fetched_at=datetime.now(pytz.timezone("Asia/Tokyo")),
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
        data_source=self.data_source
    )
```

---

## 🗄️ データベース保存仕様

### 保存データ仕様

```python
# 1時間足データ保存例
{
    "id": 自動採番,
    "currency_pair": "USD/JPY",
    "timestamp": "2025-08-15 00:00:00+09:00",  # 1時間の開始時刻
    "data_timestamp": "2025-08-15 00:00:00+09:00",
    "fetched_at": "2025-08-15 01:05:30+09:00",  # 集計実行時刻
    "open_price": 146.92500,  # 00:00の始値
    "high_price": 146.97000,  # 期間内最高値
    "low_price": 146.92200,   # 期間内最低値
    "close_price": 146.94099, # 00:55の終値
    "volume": 0,              # 期間内取引量合計
    "data_source": "yahoo_finance_1h_aggregated",
    "created_at": "2025-08-15 01:05:30+09:00",
    "updated_at": "2025-08-15 01:05:30+09:00",
    "version": 1
}
```

### 重複回避ロジック

```python
async def check_duplicate(self, timestamp: datetime) -> Optional[PriceDataModel]:
    """
    重複データチェック

    Args:
        timestamp: チェック対象のタイムスタンプ

    Returns:
        Optional[PriceDataModel]: 既存データ（存在する場合）
    """
    try:
        existing = await self.price_repo.find_by_timestamp_and_source(
            timestamp, self.currency_pair, self.data_source
        )
        return existing
    except Exception as e:
        logger.error(f"重複チェックエラー: {e}")
        return None
```

### データ保存ロジック

```python
async def save_aggregated_data(self, aggregated_data: PriceDataModel):
    """
    集計データを保存

    Args:
        aggregated_data: 保存する集計データ
    """
    try:
        # リポジトリのsaveメソッドを使用（重複チェック含む）
        saved_data = await self.price_repo.save(aggregated_data)
        logger.info(f"集計データを保存しました: {saved_data.timestamp}")
        return saved_data
    except Exception as e:
        logger.error(f"データ保存エラー: {e}")
        raise
```

---

## 📊 集計期間計算仕様

### 1 時間足集計期間

```python
def calculate_hourly_period(self) -> tuple[datetime, datetime]:
    """
    1時間足集計期間を計算

    Returns:
        tuple: (start_time, end_time)
    """
    # 現在時刻から1時間前の期間を計算
    now = datetime.now(pytz.timezone("Asia/Tokyo"))

    # 前1時間の開始時刻（00分に丸める）
    start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)

    # 前1時間の終了時刻（55分まで）
    end_time = start_time + timedelta(hours=1) - timedelta(minutes=5)

    return start_time, end_time
```

### 4 時間足集計期間

```python
def calculate_four_hour_period(self) -> tuple[datetime, datetime]:
    """
    4時間足集計期間を計算

    Returns:
        tuple: (start_time, end_time)
    """
    now = datetime.now(pytz.timezone("Asia/Tokyo"))

    # 4時間単位での開始時刻を計算
    hour = (now.hour // 4) * 4
    start_time = now.replace(hour=hour, minute=0, second=0, microsecond=0) - timedelta(hours=4)

    # 4時間後の終了時刻（55分まで）
    end_time = start_time + timedelta(hours=4) - timedelta(minutes=5)

    return start_time, end_time
```

### 日足集計期間

```python
def calculate_daily_period(self) -> tuple[datetime, datetime]:
    """
    日足集計期間を計算

    Returns:
        tuple: (start_time, end_time)
    """
    now = datetime.now(pytz.timezone("Asia/Tokyo"))

    # 前日の開始時刻
    start_time = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)

    # 前日の終了時刻（23:55まで）
    end_time = start_time + timedelta(days=1) - timedelta(minutes=5)

    return start_time, end_time
```

---

## 🔧 実装詳細

### メインスクリプト構造

```python
#!/usr/bin/env python3
"""
Hourly Aggregator - 1時間足集計スクリプト

責任:
- 5分足データから1時間足を集計
- PostgreSQLデータベースへの保存
- エラーハンドリングとログ出力
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import pytz

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.repositories.price_data_repository_impl import PriceDataRepositoryImpl

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/hourly_aggregator.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

async def main():
    """メイン関数"""
    try:
        aggregator = HourlyAggregator()
        await aggregator.aggregate_and_save()
        logger.info("1時間足集計が正常に完了しました")
    except Exception as e:
        logger.error(f"1時間足集計エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### エラーハンドリング仕様

```python
class AggregationError(Exception):
    """集計処理エラー"""
    pass

class InsufficientDataError(AggregationError):
    """データ不足エラー"""
    pass

class DatabaseError(AggregationError):
    """データベースエラー"""
    pass

# エラーハンドリング例
try:
    await aggregator.aggregate_and_save()
except InsufficientDataError:
    logger.warning("集計対象データが不足しています")
    # 正常終了（エラーではない）
except DatabaseError:
    logger.error("データベースエラーが発生しました")
    sys.exit(1)
except Exception as e:
    logger.error(f"予期しないエラー: {e}")
    sys.exit(1)
```

---

## 📈 パフォーマンス仕様

### 処理時間目標

- **データ取得**: 5 秒以内
- **集計計算**: 3 秒以内
- **データベース保存**: 2 秒以内
- **合計処理時間**: 10 秒以内

### メモリ使用量目標

- **データ取得**: 20MB 以内
- **集計処理**: 10MB 以内
- **合計メモリ使用量**: 50MB 以内

### データ処理量

- **1 時間足**: 12 件の 5 分足 → 1 件の 1 時間足
- **4 時間足**: 48 件の 5 分足 → 1 件の 4 時間足
- **日足**: 288 件の 5 分足 → 1 件の日足

---

## 🧪 テスト仕様

### 単体テスト

```python
class TestHourlyAggregator:
    """1時間足集計のテスト"""

    async def test_calculate_ohlcv(self):
        """OHLCV計算のテスト"""

    async def test_get_aggregation_period(self):
        """集計期間計算のテスト"""

    async def test_check_duplicate(self):
        """重複チェックのテスト"""

    async def test_save_aggregated_data(self):
        """データ保存のテスト"""
```

### 統合テスト

```python
class TestHourlyAggregationIntegration:
    """1時間足集計の統合テスト"""

    async def test_full_workflow(self):
        """完全なワークフローのテスト"""

    async def test_error_handling(self):
        """エラーハンドリングのテスト"""

    async def test_performance(self):
        """パフォーマンステスト"""
```

---

## 📋 実装チェックリスト

### Phase 1: 1 時間足集計

- [ ] `BaseAggregator`クラス作成
- [ ] `HourlyAggregator`クラス作成
- [ ] 集計期間計算ロジック実装
- [ ] OHLCV 計算ロジック実装
- [ ] 重複チェックロジック実装
- [ ] データ保存ロジック実装
- [ ] エラーハンドリング実装
- [ ] ログ出力実装
- [ ] 単体テスト作成
- [ ] 統合テスト作成
- [ ] パフォーマンステスト実行
- [ ] crontab 設定追加

### Phase 2: 4 時間足集計

- [ ] `FourHourAggregator`クラス作成
- [ ] 4 時間足集計ロジック実装
- [ ] テスト作成・実行
- [ ] crontab 設定追加

### Phase 3: 日足集計

- [ ] `DailyAggregator`クラス作成
- [ ] 日足集計ロジック実装
- [ ] テスト作成・実行
- [ ] crontab 設定追加

---

## 🔄 更新履歴

| 日付       | バージョン | 更新内容 | 担当者 |
| ---------- | ---------- | -------- | ------ |
| 2025-08-15 | 1.0.0      | 初版作成 | -      |

---

## 📞 関連ドキュメント

### 設計書

- [時間足集計システム設計書](./timeframe_aggregation_system_design.md)

### 技術仕様

- [Exchange Analytics System CLI 機能説明書](../docs/2025-08-15_CLI機能_ExchangeAnalyticsSystem_CLI機能説明書.md)
- [PostgreSQL 移行ガイド](../data/POSTGRESQL_BASE_DATA_README.md)

### 技術スタック

- **言語**: Python 3.9+
- **データベース**: PostgreSQL 13+
- **ORM**: SQLAlchemy (asyncio)
- **スケジューラー**: crontab
- **ログ**: Python logging

---

_この実装仕様書は設計書に基づいて作成され、具体的な実装指針を提供します。_
