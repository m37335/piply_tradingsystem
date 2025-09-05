#!/usr/bin/env python3
"""
運用開始スクリプト

USD/JPY特化の運用開始スクリプト
設計書参照: /app/note/database_implementation_design_2025.md

使用方法:
    python scripts/deployment/production_startup.py
"""

import asyncio
import os
import signal
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.data_fetcher_service import (
        DataFetcherService,
    )
    from src.infrastructure.database.services.notification_integration_service import (
        NotificationIntegrationService,
    )
    from src.infrastructure.database.services.pattern_detection_service import (
        PatternDetectionService,
    )
    from src.infrastructure.database.services.system_config_service import (
        SystemConfigService,
    )
    from src.infrastructure.database.services.technical_indicator_service import (
        TechnicalIndicatorService,
    )
    from src.infrastructure.scheduler.technical_indicator_scheduler import (
        TechnicalIndicatorScheduler,
    )
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class ProductionStartup:
    """
    運用開始クラス

    責任:
    - システムの起動
    - 監視の開始
    - 初期データの確認
    - 運用マニュアルの提供

    特徴:
    - USD/JPY特化設計
    - 包括的起動処理
    - 監視機能
    - 安全性重視
    """

    def __init__(self):
        """
        初期化
        """
        self.session = None
        self.services = {}
        self.schedulers = {}
        self.running = False

        # 起動設定
        self.startup_config = {
            "currency_pair": "USD/JPY",
            "health_check_interval": 60,  # 秒
            "max_startup_retries": 3,
            "startup_timeout": 300,  # 秒
        }

        # 統計情報
        self.startup_stats = {
            "start_time": None,
            "services_started": 0,
            "schedulers_started": 0,
            "health_checks_passed": 0,
            "health_checks_failed": 0,
            "last_health_check": None,
        }

        logger.info("Initialized ProductionStartup")

    async def start_production_system(self):
        """
        本番システムを起動
        """
        try:
            logger.info("Starting production system...")

            self.startup_stats["start_time"] = datetime.now()

            # 1. 環境チェック
            await self._check_environment()

            # 2. データベース接続
            await self._initialize_database()

            # 3. サービス初期化
            await self._initialize_services()

            # 4. スケジューラー起動
            await self._start_schedulers()

            # 5. 初期データ確認
            await self._verify_initial_data()

            # 6. 監視開始
            await self._start_monitoring()

            # 7. 運用マニュアル提供
            await self._provide_operation_manual()

            self.running = True
            logger.info("Production system started successfully!")

        except Exception as e:
            logger.error(f"Error starting production system: {e}")
            raise

    async def _check_environment(self):
        """
        環境をチェック
        """
        logger.info("Checking production environment...")

        # 必要な環境変数チェック
        required_vars = [
            "DATABASE_URL",
            "DISCORD_WEBHOOK_URL",
            "YAHOO_FINANCE_API_KEY",
            "LOG_LEVEL",
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            error_msg = f"Missing required environment variables: {missing_vars}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # ディレクトリ権限チェック
        required_dirs = ["logs", "data", "config"]
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_name}")

        logger.info("Environment check completed successfully")

    async def _initialize_database(self):
        """
        データベースを初期化
        """
        logger.info("Initializing database connection...")

        try:
            # データベースセッション作成
            self.session = await get_async_session().__anext__()

            # 接続テスト
            await self.session.execute("SELECT 1")
            await self.session.commit()

            logger.info("Database connection initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    async def _initialize_services(self):
        """
        サービスを初期化
        """
        logger.info("Initializing services...")

        try:
            # サービス初期化
            self.services = {
                "data_fetcher": DataFetcherService(self.session),
                "indicator_service": TechnicalIndicatorService(self.session),
                "pattern_service": PatternDetectionService(self.session),
                "notification_service": NotificationIntegrationService(self.session),
                "config_service": SystemConfigService(self.session),
            }

            # 各サービスの初期化確認
            for service_name, service in self.services.items():
                logger.info(f"Initialized {service_name}")
                self.startup_stats["services_started"] += 1

            logger.info("All services initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing services: {e}")
            raise

    async def _start_schedulers(self):
        """
        スケジューラーを起動
        """
        logger.info("Starting schedulers...")

        try:
            # テクニカル指標スケジューラー
            indicator_scheduler = TechnicalIndicatorScheduler()
            await indicator_scheduler.start()
            self.schedulers["indicator_scheduler"] = indicator_scheduler
            self.startup_stats["schedulers_started"] += 1

            logger.info("All schedulers started successfully")

        except Exception as e:
            logger.error(f"Error starting schedulers: {e}")
            raise

    async def _verify_initial_data(self):
        """
        初期データを確認
        """
        logger.info("Verifying initial data...")

        try:
            # 1. 価格データ確認
            await self._verify_price_data()

            # 2. テクニカル指標確認
            await self._verify_technical_indicators()

            # 3. パターン検出確認
            await self._verify_pattern_detections()

            # 4. システム設定確認
            await self._verify_system_configs()

            logger.info("Initial data verification completed successfully")

        except Exception as e:
            logger.error(f"Error verifying initial data: {e}")
            raise

    async def _verify_price_data(self):
        """
        価格データを確認
        """
        try:
            # 最新の価格データを取得
            latest_data = await self.services["data_fetcher"].get_latest_price_data()

            if latest_data:
                logger.info(f"Latest price data: {latest_data.timestamp}")
            else:
                logger.warning("No price data found")

        except Exception as e:
            logger.error(f"Error verifying price data: {e}")

    async def _verify_technical_indicators(self):
        """
        テクニカル指標を確認
        """
        try:
            # 最新の指標を取得
            latest_indicators = await self.services[
                "indicator_service"
            ].get_latest_indicators()

            if latest_indicators:
                logger.info(f"Latest indicators: {len(latest_indicators)} records")
            else:
                logger.warning("No technical indicators found")

        except Exception as e:
            logger.error(f"Error verifying technical indicators: {e}")

    async def _verify_pattern_detections(self):
        """
        パターン検出を確認
        """
        try:
            # 最新のパターンを取得
            latest_patterns = await self.services[
                "pattern_service"
            ].get_latest_patterns(limit=10)

            if latest_patterns:
                logger.info(f"Latest patterns: {len(latest_patterns)} records")
            else:
                logger.info("No pattern detections found (normal for new system)")

        except Exception as e:
            logger.error(f"Error verifying pattern detections: {e}")

    async def _verify_system_configs(self):
        """
        システム設定を確認
        """
        try:
            # 全設定を取得
            configs = await self.services["config_service"].get_all_configs()

            if configs:
                logger.info(f"System configs: {len(configs)} configurations")
            else:
                logger.warning("No system configurations found")

        except Exception as e:
            logger.error(f"Error verifying system configs: {e}")

    async def _start_monitoring(self):
        """
        監視を開始
        """
        logger.info("Starting monitoring...")

        try:
            # ヘルスチェック開始
            asyncio.create_task(self._health_check_loop())

            # 統計収集開始
            asyncio.create_task(self._statistics_collection_loop())

            logger.info("Monitoring started successfully")

        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            raise

    async def _health_check_loop(self):
        """
        ヘルスチェックループ
        """
        while self.running:
            try:
                await self._perform_health_check()
                await asyncio.sleep(self.startup_config["health_check_interval"])

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(10)

    async def _statistics_collection_loop(self):
        """
        統計収集ループ
        """
        while self.running:
            try:
                await self._collect_statistics()
                await asyncio.sleep(300)  # 5分間隔

            except Exception as e:
                logger.error(f"Error in statistics collection loop: {e}")
                await asyncio.sleep(60)

    async def _perform_health_check(self):
        """
        ヘルスチェックを実行
        """
        try:
            # データベース接続チェック
            await self.session.execute("SELECT 1")
            await self.session.commit()

            # スケジューラー状態チェック
            for scheduler_name, scheduler in self.schedulers.items():
                if not scheduler.running:
                    logger.warning(f"Scheduler {scheduler_name} is not running")

            self.startup_stats["health_checks_passed"] += 1
            self.startup_stats["last_health_check"] = datetime.now()

            logger.debug("Health check passed")

        except Exception as e:
            self.startup_stats["health_checks_failed"] += 1
            logger.error(f"Health check failed: {e}")

    async def _collect_statistics(self):
        """
        統計を収集
        """
        try:
            # システム統計を収集
            stats = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (
                    datetime.now() - self.startup_stats["start_time"]
                ).total_seconds(),
                "health_checks_passed": self.startup_stats["health_checks_passed"],
                "health_checks_failed": self.startup_stats["health_checks_failed"],
                "services_running": self.startup_stats["services_started"],
                "schedulers_running": self.startup_stats["schedulers_started"],
            }

            # 統計をログに記録
            logger.info(f"System statistics: {stats}")

        except Exception as e:
            logger.error(f"Error collecting statistics: {e}")

    async def _provide_operation_manual(self):
        """
        運用マニュアルを提供
        """
        logger.info("Providing operation manual...")

        try:
            manual_content = self._generate_operation_manual()

            # マニュアルファイルを作成
            manual_file = Path("docs/operation_manual.md")
            manual_file.parent.mkdir(exist_ok=True)

            with open(manual_file, "w", encoding="utf-8") as f:
                f.write(manual_content)

            logger.info(f"Operation manual created: {manual_file}")

        except Exception as e:
            logger.error(f"Error providing operation manual: {e}")

    def _generate_operation_manual(self) -> str:
        """
        運用マニュアルを生成

        Returns:
            str: マニュアル内容
        """
        return f"""# USD/JPY Trading System Operation Manual

## システム概要
- **通貨ペア**: USD/JPY
- **データ取得間隔**: 5分
- **テクニカル分析間隔**: 10分
- **起動日時**: {self.startup_stats['start_time']}

## 監視項目

### 1. データ取得
- 5分間隔でUSD/JPY価格データを取得
- Yahoo Finance APIを使用
- 取得失敗時の自動リトライ機能

### 2. テクニカル指標
- RSI, MACD, ボリンジャーバンド
- 移動平均線（SMA, EMA）
- 複数タイムフレーム対応（5m, 1h, 4h, 1d）

### 3. パターン検出
- 6種類のトレーディングパターン
- 信頼度・優先度によるフィルタリング
- 重複検出防止機能

### 4. 通知システム
- Discord通知
- 通知頻度制限
- 通知履歴管理

## 運用コマンド

### システム起動
```bash
python scripts/deployment/production_startup.py
```

### データ取得（手動）
```bash
python scripts/cron/simple_data_fetcher.py
```

### テクニカル分析（手動）
```bash
python scripts/cron/technical_analysis_cron.py --once
```

### 設定確認
```bash
python scripts/deployment/production_setup.py
```

## ログファイル
- システムログ: `logs/system.log`
- エラーログ: `logs/error.log`
- 移行ログ: `logs/migration.log`

## トラブルシューティング

### データ取得エラー
1. Yahoo Finance APIキーの確認
2. ネットワーク接続の確認
3. データベース接続の確認

### 通知エラー
1. Discord Webhook URLの確認
2. 通知頻度制限の確認
3. 通知履歴の確認

### パフォーマンス問題
1. データベース接続プールの確認
2. データクリーンアップの実行
3. システム設定の最適化

## 緊急時対応

### システム停止
```bash
# プロセス終了
pkill -f "python.*scheduler"
```

### データ復旧
```bash
# バックアップからの復旧
python scripts/migration/data_migration.py
```

### 設定リセット
```bash
# デフォルト設定への復帰
python scripts/deployment/production_setup.py
```

## 連絡先
- システム管理者: [管理者連絡先]
- 緊急時連絡先: [緊急時連絡先]
"""

    async def stop_production_system(self):
        """
        本番システムを停止
        """
        try:
            logger.info("Stopping production system...")

            self.running = False

            # スケジューラー停止
            for scheduler_name, scheduler in self.schedulers.items():
                await scheduler.stop()
                logger.info(f"Stopped {scheduler_name}")

            # データベース接続終了
            if self.session:
                await self.session.close()
                logger.info("Database connection closed")

            logger.info("Production system stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping production system: {e}")

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            await self.stop_production_system()
            logger.info("Production startup cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting production system startup...")

    startup = ProductionStartup()

    try:
        # 本番システム起動
        await startup.start_production_system()

        # シグナルハンドラー設定
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            asyncio.create_task(startup.stop_production_system())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # システム実行継続
        while startup.running:
            await asyncio.sleep(1)

    except Exception as e:
        logger.error(f"Production startup failed: {e}")
        sys.exit(1)
    finally:
        await startup.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
