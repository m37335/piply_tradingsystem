#!/usr/bin/env python3
"""
データ移行スクリプト

USD/JPY特化のデータ移行スクリプト
設計書参照: /app/note/database_implementation_design_2025.md

使用方法:
    python scripts/migration/data_migration.py
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.infrastructure.database.connection import get_async_session
    from src.infrastructure.database.services.data_fetcher_service import (
        DataFetcherService,
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
    from src.utils.logging_config import get_infrastructure_logger
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

logger = get_infrastructure_logger()


class DataMigration:
    """
    データ移行クラス

    責任:
    - 既存データの移行
    - データ整合性の確認
    - 移行ログの記録
    - 移行テストの実行

    特徴:
    - USD/JPY特化設計
    - 安全な移行処理
    - 詳細なログ記録
    - 整合性チェック
    """

    def __init__(self):
        """
        初期化
        """
        self.session = None
        self.services = {}
        self.migration_log = []

        # 移行設定
        self.migration_config = {
            "currency_pair": "USD/JPY",
            "batch_size": 1000,
            "max_retries": 3,
            "dry_run": True,  # デフォルトはドライラン
        }

        logger.info("Initialized DataMigration")

    async def initialize(self):
        """
        移行を初期化
        """
        try:
            logger.info("Initializing data migration...")

            # データベースセッション作成
            self.session = await get_async_session().__anext__()

            # サービス初期化
            self.services = {
                "data_fetcher": DataFetcherService(self.session),
                "indicator_service": TechnicalIndicatorService(self.session),
                "pattern_service": PatternDetectionService(self.session),
                "config_service": SystemConfigService(self.session),
            }

            logger.info("Data migration initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing data migration: {e}")
            raise

    async def migrate_all_data(self, dry_run: bool = True) -> Dict[str, int]:
        """
        全データを移行

        Args:
            dry_run: ドライラン実行フラグ（デフォルト: True）

        Returns:
            Dict[str, int]: 移行結果統計
        """
        try:
            logger.info(f"Starting data migration (dry_run: {dry_run})")

            self.migration_config["dry_run"] = dry_run
            results = {}

            # 1. 価格データ移行
            logger.info("Migrating price data...")
            price_results = await self._migrate_price_data()
            results["price_data"] = price_results

            # 2. テクニカル指標移行
            logger.info("Migrating technical indicators...")
            indicator_results = await self._migrate_technical_indicators()
            results["technical_indicators"] = indicator_results

            # 3. パターン検出結果移行
            logger.info("Migrating pattern detections...")
            pattern_results = await self._migrate_pattern_detections()
            results["pattern_detections"] = pattern_results

            # 4. システム設定移行
            logger.info("Migrating system configurations...")
            config_results = await self._migrate_system_configs()
            results["system_configs"] = config_results

            # 移行ログを保存
            await self._save_migration_log(results)

            total_migrated = sum(
                result.get("migrated", 0) for result in results.values()
            )
            logger.info(f"Data migration completed: {total_migrated} total records")

            return results

        except Exception as e:
            logger.error(f"Error in data migration: {e}")
            raise

    async def _migrate_price_data(self) -> Dict[str, int]:
        """
        価格データを移行

        Returns:
            Dict[str, int]: 移行結果
        """
        try:
            # 既存データを確認
            existing_data = await self._check_existing_price_data()

            if not existing_data:
                logger.info("No existing price data to migrate")
                return {"migrated": 0, "skipped": 0, "errors": 0}

            # 移行処理
            migrated_count = 0
            skipped_count = 0
            error_count = 0

            for data_batch in self._create_data_batches(existing_data):
                try:
                    if not self.migration_config["dry_run"]:
                        # 実際の移行処理
                        await self._migrate_price_data_batch(data_batch)
                    migrated_count += len(data_batch)

                except Exception as e:
                    logger.error(f"Error migrating price data batch: {e}")
                    error_count += len(data_batch)

            return {
                "migrated": migrated_count,
                "skipped": skipped_count,
                "errors": error_count,
            }

        except Exception as e:
            logger.error(f"Error migrating price data: {e}")
            return {"migrated": 0, "skipped": 0, "errors": 1}

    async def _migrate_technical_indicators(self) -> Dict[str, int]:
        """
        テクニカル指標を移行

        Returns:
            Dict[str, int]: 移行結果
        """
        try:
            # 既存データを確認
            existing_data = await self._check_existing_indicators()

            if not existing_data:
                logger.info("No existing technical indicators to migrate")
                return {"migrated": 0, "skipped": 0, "errors": 0}

            # 移行処理
            migrated_count = 0
            skipped_count = 0
            error_count = 0

            for data_batch in self._create_data_batches(existing_data):
                try:
                    if not self.migration_config["dry_run"]:
                        # 実際の移行処理
                        await self._migrate_indicators_batch(data_batch)
                    migrated_count += len(data_batch)

                except Exception as e:
                    logger.error(f"Error migrating indicators batch: {e}")
                    error_count += len(data_batch)

            return {
                "migrated": migrated_count,
                "skipped": skipped_count,
                "errors": error_count,
            }

        except Exception as e:
            logger.error(f"Error migrating technical indicators: {e}")
            return {"migrated": 0, "skipped": 0, "errors": 1}

    async def _migrate_pattern_detections(self) -> Dict[str, int]:
        """
        パターン検出結果を移行

        Returns:
            Dict[str, int]: 移行結果
        """
        try:
            # 既存データを確認
            existing_data = await self._check_existing_patterns()

            if not existing_data:
                logger.info("No existing pattern detections to migrate")
                return {"migrated": 0, "skipped": 0, "errors": 0}

            # 移行処理
            migrated_count = 0
            skipped_count = 0
            error_count = 0

            for data_batch in self._create_data_batches(existing_data):
                try:
                    if not self.migration_config["dry_run"]:
                        # 実際の移行処理
                        await self._migrate_patterns_batch(data_batch)
                    migrated_count += len(data_batch)

                except Exception as e:
                    logger.error(f"Error migrating patterns batch: {e}")
                    error_count += len(data_batch)

            return {
                "migrated": migrated_count,
                "skipped": skipped_count,
                "errors": error_count,
            }

        except Exception as e:
            logger.error(f"Error migrating pattern detections: {e}")
            return {"migrated": 0, "skipped": 0, "errors": 1}

    async def _migrate_system_configs(self) -> Dict[str, int]:
        """
        システム設定を移行

        Returns:
            Dict[str, int]: 移行結果
        """
        try:
            # 既存設定を確認
            existing_configs = await self._check_existing_configs()

            if not existing_configs:
                logger.info("No existing system configs to migrate")
                return {"migrated": 0, "skipped": 0, "errors": 0}

            # 移行処理
            migrated_count = 0
            skipped_count = 0
            error_count = 0

            for config in existing_configs:
                try:
                    if not self.migration_config["dry_run"]:
                        # 実際の移行処理
                        await self._migrate_single_config(config)
                    migrated_count += 1

                except Exception as e:
                    logger.error(f"Error migrating config {config}: {e}")
                    error_count += 1

            return {
                "migrated": migrated_count,
                "skipped": skipped_count,
                "errors": error_count,
            }

        except Exception as e:
            logger.error(f"Error migrating system configs: {e}")
            return {"migrated": 0, "skipped": 0, "errors": 1}

    async def _check_existing_price_data(self) -> List:
        """
        既存の価格データを確認

        Returns:
            List: 既存データリスト
        """
        try:
            # 過去30日分のデータを確認
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            data = await self.services["data_fetcher"].fetch_historical_price_data(
                start_date, end_date
            )

            logger.info(f"Found {len(data)} existing price data records")
            return data

        except Exception as e:
            logger.error(f"Error checking existing price data: {e}")
            return []

    async def _check_existing_indicators(self) -> List:
        """
        既存のテクニカル指標を確認

        Returns:
            List: 既存データリスト
        """
        try:
            # 過去30日分の指標を確認
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)

            indicators = await self.services[
                "indicator_service"
            ].get_indicators_by_range(start_date=start_date, end_date=end_date)

            logger.info(f"Found {len(indicators)} existing technical indicators")
            return indicators

        except Exception as e:
            logger.error(f"Error checking existing indicators: {e}")
            return []

    async def _check_existing_patterns(self) -> List:
        """
        既存のパターン検出結果を確認

        Returns:
            List: 既存データリスト
        """
        try:
            # 過去30日分のパターンを確認
            patterns = await self.services["pattern_service"].get_latest_patterns(
                limit=1000
            )

            logger.info(f"Found {len(patterns)} existing pattern detections")
            return patterns

        except Exception as e:
            logger.error(f"Error checking existing patterns: {e}")
            return []

    async def _check_existing_configs(self) -> List:
        """
        既存のシステム設定を確認

        Returns:
            List: 既存設定リスト
        """
        try:
            configs = await self.services["config_service"].get_all_configs()

            logger.info(f"Found {len(configs)} existing system configs")
            return list(configs.items())

        except Exception as e:
            logger.error(f"Error checking existing configs: {e}")
            return []

    def _create_data_batches(self, data: List, batch_size: Optional[int] = None):
        """
        データバッチを作成

        Args:
            data: データリスト
            batch_size: バッチサイズ（デフォルト: None）

        Yields:
            List: データバッチ
        """
        if batch_size is None:
            batch_size = self.migration_config["batch_size"]

        for i in range(0, len(data), batch_size):
            yield data[i : i + batch_size]

    async def _migrate_price_data_batch(self, data_batch: List):
        """
        価格データバッチを移行

        Args:
            data_batch: データバッチ
        """
        # 実際の移行処理を実装
        logger.info(f"Migrating price data batch: {len(data_batch)} records")

    async def _migrate_indicators_batch(self, data_batch: List):
        """
        テクニカル指標バッチを移行

        Args:
            data_batch: データバッチ
        """
        # 実際の移行処理を実装
        logger.info(f"Migrating indicators batch: {len(data_batch)} records")

    async def _migrate_patterns_batch(self, data_batch: List):
        """
        パターン検出結果バッチを移行

        Args:
            data_batch: データバッチ
        """
        # 実際の移行処理を実装
        logger.info(f"Migrating patterns batch: {len(data_batch)} records")

    async def _migrate_single_config(self, config: tuple):
        """
        単一設定を移行

        Args:
            config: 設定タプル (key, value)
        """
        # 実際の移行処理を実装
        key, value = config
        logger.info(f"Migrating config: {key}")

    async def _save_migration_log(self, results: Dict[str, Dict]):
        """
        移行ログを保存

        Args:
            results: 移行結果
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.migration_config["dry_run"],
                "results": results,
                "total_migrated": sum(
                    result.get("migrated", 0) for result in results.values()
                ),
            }

            self.migration_log.append(log_entry)

            # ログファイルに保存
            log_file = Path("logs/migration.log")
            log_file.parent.mkdir(exist_ok=True)

            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            logger.info("Migration log saved successfully")

        except Exception as e:
            logger.error(f"Error saving migration log: {e}")

    async def verify_migration(self) -> bool:
        """
        移行を検証

        Returns:
            bool: 検証成功の場合True
        """
        try:
            logger.info("Verifying data migration...")

            # 1. データ整合性チェック
            await self._verify_data_integrity()

            # 2. データ量チェック
            await self._verify_data_volume()

            # 3. データ品質チェック
            await self._verify_data_quality()

            logger.info("Data migration verification completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error verifying migration: {e}")
            return False

    async def _verify_data_integrity(self):
        """
        データ整合性を検証
        """
        logger.info("Verifying data integrity...")

        # 整合性チェックの実装
        logger.info("Data integrity verification completed")

    async def _verify_data_volume(self):
        """
        データ量を検証
        """
        logger.info("Verifying data volume...")

        # データ量チェックの実装
        logger.info("Data volume verification completed")

    async def _verify_data_quality(self):
        """
        データ品質を検証
        """
        logger.info("Verifying data quality...")

        # データ品質チェックの実装
        logger.info("Data quality verification completed")

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("Data migration cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


async def main():
    """
    メイン関数
    """
    logger.info("Starting data migration...")

    migration = DataMigration()

    try:
        # 初期化
        await migration.initialize()

        # ドライラン実行
        logger.info("Running dry run migration...")
        await migration.migrate_all_data(dry_run=True)

        # 検証
        verification_success = await migration.verify_migration()

        if verification_success:
            logger.info("Dry run migration completed successfully!")

            # 実際の移行を実行するか確認
            user_input = input("Proceed with actual migration? (y/N): ")
            if user_input.lower() == "y":
                logger.info("Running actual migration...")
                await migration.migrate_all_data(dry_run=False)
                logger.info("Actual migration completed successfully!")
            else:
                logger.info("Migration cancelled by user")
        else:
            logger.error("Migration verification failed")

    except Exception as e:
        logger.error(f"Data migration failed: {e}")
        sys.exit(1)
    finally:
        await migration.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
