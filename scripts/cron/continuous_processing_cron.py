#!/usr/bin/env python3
"""
継続処理システム統合cronスクリプト

責任:
- 既存システムとの統合
- システム初期化状態のチェック
- 適切な処理の実行（初回データ取得 or 継続処理）
- エラーハンドリングとログ記録

特徴:
- 既存の5分間隔データ取得と統合
- 自動的な初期化状態検出
- 包括的なエラーハンドリング
- 詳細なログ記録
"""

import asyncio
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.database.services.system_initialization_manager import (
    SystemInitializationManager,
)
from src.infrastructure.monitoring.continuous_processing_monitor import (
    ContinuousProcessingMonitor,
)
from src.infrastructure.schedulers.continuous_processing_scheduler import (
    ContinuousProcessingScheduler,
)

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/app/logs/continuous_processing_cron.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class ContinuousProcessingCron:
    """
    継続処理システム統合cronクラス
    """

    def __init__(self):
        self.db_url = None
        self.engine = None
        self.session_factory = None
        self.session = None
        self.initialization_manager = None
        self.scheduler = None
        self.monitor = None

    async def initialize_database(self):
        """
        データベース接続を初期化
        """
        try:
            # 環境変数からデータベースURLを取得
            import os

            self.db_url = os.getenv("DATABASE_URL")
            if not self.db_url:
                raise ValueError("DATABASE_URL環境変数が設定されていません")

            # データベースエンジンを作成
            self.engine = create_async_engine(self.db_url, echo=False)
            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            logger.info("✅ データベース接続を初期化しました")

        except Exception as e:
            logger.error(f"❌ データベース初期化エラー: {e}")
            raise

    async def initialize_services(self):
        """
        サービスを初期化
        """
        try:
            # セッションを作成
            self.session = self.session_factory()

            # サービスを初期化
            self.initialization_manager = SystemInitializationManager(self.session)
            self.scheduler = ContinuousProcessingScheduler(self.session)
            self.monitor = ContinuousProcessingMonitor()

            logger.info("✅ サービスを初期化しました")

        except Exception as e:
            logger.error(f"❌ サービス初期化エラー: {e}")
            raise

    async def run_system_cycle(self, force_reinitialize: bool = False):
        """
        システムサイクルを実行

        Args:
            force_reinitialize: 強制再初期化フラグ
        """
        try:
            logger.info("🔄 継続処理システムサイクル開始")

            # 監視を開始
            await self.monitor.start_monitoring()

            # システムサイクルを実行（初期化チェック + 継続処理）
            result = await self.initialization_manager.run_system_cycle(force_reinitialize)

            # 監視データを記録
            cycle_data = {
                "processing_time": result.get("processing_time", 0),
                "total_runs": 1,
                "successful_runs": 1 if result.get("status") == "success" else 0,
                "data_volume": result.get("data_volume", 0),
                "error_count": 0,
                "status": result.get("status", "unknown"),
            }

            await self.monitor.monitor_processing_cycle(cycle_data)

            logger.info(f"✅ システムサイクル完了: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ システムサイクルエラー: {e}")

            # エラー監視データを記録
            cycle_data = {
                "processing_time": 0,
                "total_runs": 1,
                "successful_runs": 0,
                "data_volume": 0,
                "error_count": 1,
                "status": "error",
            }

            await self.monitor.monitor_processing_cycle(cycle_data)
            raise

    async def run_single_cycle(self):
        """
        単一サイクルを実行（スケジューラーを使用）
        """
        try:
            logger.info("🔄 継続処理単一サイクル開始")

            # 監視を開始
            await self.monitor.start_monitoring()

            # 単一サイクルを実行
            await self.scheduler.run_single_cycle()

            # スケジューラー統計を取得
            stats = await self.scheduler.get_scheduler_stats()

            # 監視データを記録
            cycle_data = {
                "processing_time": stats.get("average_processing_time", 0),
                "total_runs": stats.get("total_runs", 0),
                "successful_runs": stats.get("successful_runs", 0),
                "data_volume": 1,  # 1サイクル分
                "error_count": stats.get("failed_runs", 0),
                "status": "success" if stats.get("failed_runs", 0) == 0 else "error",
            }

            await self.monitor.monitor_processing_cycle(cycle_data)

            logger.info(f"✅ 単一サイクル完了: {stats}")
            return stats

        except Exception as e:
            logger.error(f"❌ 単一サイクルエラー: {e}")

            # エラー監視データを記録
            cycle_data = {
                "processing_time": 0,
                "total_runs": 1,
                "successful_runs": 0,
                "data_volume": 0,
                "error_count": 1,
                "status": "error",
            }

            await self.monitor.monitor_processing_cycle(cycle_data)
            raise

    async def check_system_health(self):
        """
        システム健全性をチェック
        """
        try:
            logger.info("🔍 システム健全性チェック開始")

            # 各サービスの健全性をチェック
            init_health = await self.initialization_manager.health_check()
            scheduler_health = await self.scheduler.health_check()
            monitor_health = await self.monitor.check_system_health()

            health_summary = {
                "timestamp": datetime.now(),
                "initialization_manager": init_health,
                "scheduler": scheduler_health,
                "monitor": monitor_health,
                "overall_status": "healthy",
            }

            # 全体の健全性を判定
            if (
                init_health.get("status") == "unhealthy"
                or scheduler_health.get("status") == "unhealthy"
                or monitor_health.get("status") == "unhealthy"
            ):
                health_summary["overall_status"] = "unhealthy"
            elif (
                init_health.get("status") == "degraded"
                or scheduler_health.get("status") == "degraded"
                or monitor_health.get("status") == "degraded"
            ):
                health_summary["overall_status"] = "degraded"

            logger.info(
                f"✅ システム健全性チェック完了: {health_summary['overall_status']}"
            )
            return health_summary

        except Exception as e:
            logger.error(f"❌ システム健全性チェックエラー: {e}")
            return {
                "timestamp": datetime.now(),
                "overall_status": "unhealthy",
                "error": str(e),
            }

    async def cleanup(self):
        """
        リソースをクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
        except Exception as e:
            logger.error(f"❌ セッションクリーンアップエラー: {e}")

        try:
            if self.engine:
                await self.engine.dispose()
        except Exception as e:
            logger.error(f"❌ エンジンクリーンアップエラー: {e}")

        logger.info("✅ リソースをクリーンアップしました")

    async def run(self, mode="system_cycle", force_reinitialize=False):
        """
        メイン実行メソッド

        Args:
            mode: 実行モード ("system_cycle" or "single_cycle")
            force_reinitialize: 強制再初期化フラグ
        """
        try:
            logger.info(f"🚀 継続処理cron開始 (mode: {mode})")

            # データベースを初期化
            await self.initialize_database()

            # サービスを初期化
            await self.initialize_services()

            # システム健全性をチェック
            health = await self.check_system_health()
            logger.info(f"健全性チェック結果: {health}")

            if health["overall_status"] == "unhealthy":
                # 未初期化の場合は初期化を実行
                issues = health.get("issues", [])
                init_manager_issues = health.get("initialization_manager", {}).get("issues", [])
                all_issues = issues + init_manager_issues
                logger.info(f"健全性問題: {all_issues}")
                
                if any("システムが未初期化" in str(issue) for issue in all_issues):
                    logger.info("🔄 システムが未初期化のため、初期化を実行します")
                    # 初期化を実行するために処理を続行
                else:
                    logger.error("❌ システムが不健全な状態です")
                    return {"status": "error", "message": "System unhealthy"}

            # 指定されたモードで実行
            if mode == "system_cycle":
                result = await self.run_system_cycle(force_reinitialize)
            elif mode == "single_cycle":
                result = await self.run_single_cycle()
            else:
                raise ValueError(f"不明なモード: {mode}")

            logger.info("🎉 継続処理cron完了")
            return {"status": "success", "result": result}

        except Exception as e:
            logger.error(f"❌ 継続処理cronエラー: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "error": str(e)}

        finally:
            await self.cleanup()


async def main():
    """
    メイン関数
    """
    import argparse

    parser = argparse.ArgumentParser(description="継続処理システム統合cron")
    parser.add_argument(
        "--mode",
        choices=["system_cycle", "single_cycle"],
        default="system_cycle",
        help="実行モード",
    )
    parser.add_argument(
        "--health-check-only",
        action="store_true",
        help="健全性チェックのみ実行",
    )
    parser.add_argument(
        "--force-reinitialize",
        action="store_true",
        help="強制再初期化を実行",
    )

    args = parser.parse_args()

    cron = ContinuousProcessingCron()

    try:
        if args.health_check_only:
            # データベースを初期化
            await cron.initialize_database()
            await cron.initialize_services()

            # 健全性チェックのみ実行
            health = await cron.check_system_health()
            print(f"System Health: {health['overall_status']}")
            return

        # 通常の実行
        result = await cron.run(args.mode, args.force_reinitialize)
        print(f"Result: {result}")

    except Exception as e:
        logger.error(f"❌ メイン実行エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
