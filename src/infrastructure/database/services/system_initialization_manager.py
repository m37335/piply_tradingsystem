"""
システム初期化マネージャー

責任:
- 基盤データ復元と差分データ取得の統合管理
- 初期化状態の管理
- 初回実行と継続実行の切り替え
- システム状態の監視

特徴:
- 基盤データの自動復元
- 差分データの自動取得
- 段階的初期化プロセス
- 初期化失敗時の自動復旧
- 継続処理への自動移行
"""

import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.services.initial_data_loader_service import (
    InitialDataLoaderService,
)
from src.infrastructure.monitoring.continuous_processing_monitor import (
    ContinuousProcessingMonitor,
)

logger = logging.getLogger(__name__)


class SystemInitializationManager:
    """
    システム初期化マネージャー

    責任:
    - 基盤データ復元と差分データ取得の統合管理
    - 初期化状態の管理
    - 初回実行と継続実行の切り替え
    - システム状態の監視
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.initial_loader = InitialDataLoaderService(session)
        self.monitor = ContinuousProcessingMonitor()

        # 初期化状態
        self.initialization_status = {
            "is_initialized": False,
            "initialization_date": None,
            "base_data_restored": False,
            "differential_data_updated": False,
            "data_counts": {},
            "indicator_counts": {},
            "pattern_counts": {},
        }

        # 設定
        self.currency_pair = "USD/JPY"
        self.max_retry_attempts = 3
        self.retry_delay = 30  # 秒

        # スクリプトパス
        self.base_data_restorer_path = Path("/app/scripts/cron/base_data_restorer.py")
        self.differential_updater_path = Path(
            "/app/scripts/cron/differential_updater.py"
        )
        self.base_data_path = Path(
            "/app/data/exchange_analytics_phase2_complete_2025-08-14.db"
        )

    async def check_initialization_status(self) -> bool:
        """
        初期化状態をチェック（基盤データ復元→差分取得ワークフロー対応）

        Returns:
            bool: 初期化済みフラグ
        """
        try:
            logger.info(
                "🔍 初期化状態チェック開始（基盤データ復元→差分取得ワークフロー）"
            )

            # 1. 基盤データの存在確認
            if not self.base_data_path.exists():
                logger.info("初期化未完了: 基盤データファイルが存在しません")
                return False

            # 2. 基盤データの復元状態確認
            base_data_restored = await self._check_base_data_restoration()
            if not base_data_restored:
                logger.info("初期化未完了: 基盤データが復元されていません")
                return False

            # 3. 差分データの更新状態確認
            differential_updated = await self._check_differential_data_update()
            if not differential_updated:
                logger.info("初期化未完了: 差分データが更新されていません")
                return False

            # 4. テクニカル指標の存在確認
            indicator_count = await (
                self.initial_loader.indicator_service.count_latest_indicators()
            )
            if indicator_count < 10:
                logger.info(
                    f"初期化未完了: テクニカル指標不足 (現在: {indicator_count}/10)"
                )
                return False

            logger.info("✅ 初期化完了確認済み（基盤データ復元→差分取得ワークフロー）")
            return True

        except Exception as e:
            logger.error(f"初期化状態チェックエラー: {e}")
            return False

    async def _check_base_data_restoration(self) -> bool:
        """
        基盤データの復元状態を確認

        Returns:
            bool: 基盤データが復元されているか
        """
        try:
            # データベース内のデータ件数を確認
            # 基盤データは22,320件（5分足: 16,690件、4時間足: 2,179件、1時間足: 1,394件、日足: 362件）
            min_total_count = 20000  # 基盤データの最小件数

            total_count = await self.initial_loader.price_repo.count_all()

            if total_count >= min_total_count:
                logger.info(f"基盤データ復元確認: {total_count}件")
                return True
            else:
                logger.info(
                    f"基盤データ復元未完了: {total_count}件（最小: {min_total_count}件）"
                )
                return False

        except Exception as e:
            logger.error(f"基盤データ復元状態確認エラー: {e}")
            return False

    async def _check_differential_data_update(self) -> bool:
        """
        差分データの更新状態を確認

        Returns:
            bool: 差分データが更新されているか
        """
        try:
            # 現在時刻から1日以内のデータがあるかチェック
            recent_data_count = (
                await self.initial_loader.price_repo.count_by_date_range(
                    datetime.now() - timedelta(days=1),
                    datetime.now(),
                    self.currency_pair,
                )
            )

            if recent_data_count > 0:
                logger.info(f"差分データ更新確認: 最新{recent_data_count}件")
                return True
            else:
                logger.info("差分データ更新未完了: 最新データがありません")
                return False

        except Exception as e:
            logger.error(f"差分データ更新状態確認エラー: {e}")
            return False

    async def perform_initial_initialization(self) -> Dict[str, Any]:
        """
        初回初期化を実行（基盤データ復元→差分取得ワークフロー）

        Returns:
            Dict[str, Any]: 初期化結果
        """
        try:
            logger.info("🚀 初回初期化開始（基盤データ復元→差分取得ワークフロー）")

            initialization_result = {
                "is_initialized": False,
                "base_data_restored": False,
                "differential_data_updated": False,
                "data_counts": {},
                "indicator_counts": {},
                "pattern_counts": {},
                "errors": [],
            }

            # Step 1: 基盤データ復元
            logger.info("📋 Step 1: 基盤データ復元")
            base_restore_success = await self._restore_base_data()
            initialization_result["base_data_restored"] = base_restore_success

            if not base_restore_success:
                error_msg = "基盤データ復元に失敗しました"
                initialization_result["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
                return initialization_result

            # Step 2: 差分データ更新
            logger.info("📋 Step 2: 差分データ更新")
            differential_update_success = await self._update_differential_data()
            initialization_result["differential_data_updated"] = (
                differential_update_success
            )

            if not differential_update_success:
                error_msg = "差分データ更新に失敗しました"
                initialization_result["errors"].append(error_msg)
                logger.error(f"❌ {error_msg}")
                return initialization_result

            # Step 3: データ件数の確認
            data_counts = await self._get_data_counts()
            initialization_result["data_counts"] = data_counts

            # 初期化状態を更新
            if base_restore_success and differential_update_success:
                self.initialization_status.update(
                    {
                        "is_initialized": True,
                        "initialization_date": datetime.now(),
                        "base_data_restored": True,
                        "differential_data_updated": True,
                        "data_counts": data_counts,
                    }
                )
                initialization_result["is_initialized"] = True

                logger.info("🎉 初回初期化完了（基盤データ復元→差分取得ワークフロー）")
            else:
                logger.error("❌ 初回初期化失敗")

            return initialization_result

        except Exception as e:
            logger.error(f"初回初期化エラー: {e}")
            raise

    async def _restore_base_data(self) -> bool:
        """
        基盤データを復元

        Returns:
            bool: 復元成功時True、失敗時False
        """
        try:
            logger.info("🔄 基盤データ復元を開始...")

            if not self.base_data_restorer_path.exists():
                logger.error(
                    f"❌ 基盤データ復元スクリプトが見つかりません: "
                    f"{self.base_data_restorer_path}"
                )
                return False

            # 環境変数を設定
            env = os.environ.copy()
            if not env.get("DATABASE_URL"):
                env["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"
            env["PYTHONPATH"] = "/app"

            # 基盤データ復元スクリプトを実行
            result = subprocess.run(
                [sys.executable, str(self.base_data_restorer_path)],
                capture_output=True,
                text=True,
                cwd="/app",
                env=env,
            )

            if result.returncode == 0:
                logger.info("✅ 基盤データ復元完了")
                if result.stdout:
                    logger.info(result.stdout)
                return True
            else:
                logger.error(f"❌ 基盤データ復元エラー: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ 基盤データ復元エラー: {e}")
            return False

    async def _update_differential_data(self) -> bool:
        """
        差分データを更新

        Returns:
            bool: 更新成功時True、失敗時False
        """
        try:
            logger.info("🔄 差分データ更新を開始...")

            if not self.differential_updater_path.exists():
                logger.error(
                    f"❌ 差分データ更新スクリプトが見つかりません: "
                    f"{self.differential_updater_path}"
                )
                return False

            # 環境変数を設定
            env = os.environ.copy()
            if not env.get("DATABASE_URL"):
                env["DATABASE_URL"] = "sqlite+aiosqlite:///data/exchange_analytics.db"
            env["PYTHONPATH"] = "/app"

            # 差分データ更新スクリプトを実行
            result = subprocess.run(
                [sys.executable, str(self.differential_updater_path)],
                capture_output=True,
                text=True,
                cwd="/app",
                env=env,
            )

            if result.returncode == 0:
                logger.info("✅ 差分データ更新完了")
                if result.stdout:
                    logger.info(result.stdout)
                return True
            else:
                logger.error(f"❌ 差分データ更新エラー: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ 差分データ更新エラー: {e}")
            return False

    async def _get_data_counts(self) -> Dict[str, int]:
        """
        各時間足のデータ件数を取得

        Returns:
            Dict[str, int]: 各時間足のデータ件数
        """
        try:
            timeframes = ["5m", "1h", "4h", "1d"]
            data_counts = {}

            for timeframe in timeframes:
                count = await self.initial_loader.price_repo.count_by_timeframe(
                    self.currency_pair, timeframe
                )
                data_counts[timeframe] = count

            return data_counts

        except Exception as e:
            logger.error(f"データ件数取得エラー: {e}")
            return {}

    async def start_continuous_processing(self) -> bool:
        """
        継続処理を開始

        Returns:
            bool: 開始成功フラグ
        """
        try:
            logger.info("🔄 継続処理開始")

            # 継続処理サービスの初期化
            await self.continuous_service.initialize()

            # 監視システムの開始
            await self.monitor.start_monitoring()

            logger.info("✅ 継続処理開始完了")
            return True

        except Exception as e:
            logger.error(f"継続処理開始エラー: {e}")
            return False

    async def run_system_cycle(
        self, force_reinitialize: bool = False
    ) -> Dict[str, Any]:
        """
        システムサイクルを実行（基盤データ復元→差分取得ワークフロー対応）

        Args:
            force_reinitialize: 強制再初期化フラグ

        Returns:
            Dict[str, Any]: 実行結果
        """
        try:
            logger.info(
                "🔄 システムサイクル開始（基盤データ復元→差分取得ワークフロー）"
            )

            # 1. 初期化状態をチェック
            is_initialized = await self.check_initialization_status()

            if not is_initialized or force_reinitialize:
                if force_reinitialize:
                    logger.info(
                        "=== 強制再初期化を実行（基盤データ復元→差分取得ワークフロー）==="
                    )
                else:
                    logger.info(
                        "=== 初回初期化を実行（基盤データ復元→差分取得ワークフロー）==="
                    )
                return await self.perform_initial_initialization()

            # 2. 継続処理を開始
            logger.info("=== 継続処理を開始 ===")
            continuous_success = await self.start_continuous_processing()

            if continuous_success:
                return {
                    "is_initialized": True,
                    "continuous_processing_started": True,
                    "message": "継続処理が開始されました",
                }
            else:
                return {
                    "is_initialized": True,
                    "continuous_processing_started": False,
                    "message": "継続処理の開始に失敗しました",
                }

        except Exception as e:
            logger.error(f"システムサイクル実行エラー: {e}")
            raise

    async def get_initialization_status(self) -> Dict[str, Any]:
        """
        初期化状態を取得

        Returns:
            Dict[str, Any]: 初期化状態
        """
        return self.initialization_status.copy()

    async def health_check(self) -> Dict[str, Any]:
        """
        システム健全性チェック（継続処理スクリプトとの互換性のため）

        Returns:
            Dict[str, Any]: 健全性情報
        """
        try:
            logger.info("🔍 システム初期化マネージャー健全性チェック開始")

            health_info = {
                "timestamp": datetime.now(),
                "status": "healthy",
                "components": {},
                "issues": [],
            }

            # 1. 初期化状態チェック
            try:
                is_initialized = await self.check_initialization_status()
                health_info["components"]["initialization"] = (
                    "healthy" if is_initialized else "degraded"
                )
                if not is_initialized:
                    health_info["issues"].append("システムが未初期化")
                    if health_info["status"] == "healthy":
                        health_info["status"] = "degraded"
            except Exception as e:
                health_info["components"]["initialization"] = "unhealthy"
                health_info["issues"].append(f"初期化状態チェックエラー: {e}")
                health_info["status"] = "unhealthy"

            # 2. データベース接続チェック
            try:
                from sqlalchemy import text

                await self.session.execute(text("SELECT 1"))
                health_info["components"]["database"] = "healthy"
            except Exception as e:
                health_info["components"]["database"] = "unhealthy"
                health_info["issues"].append(f"データベース接続エラー: {e}")
                health_info["status"] = "unhealthy"

            # 3. 基盤データファイルチェック
            try:
                if self.base_data_path.exists():
                    health_info["components"]["base_data"] = "healthy"
                else:
                    health_info["components"]["base_data"] = "unhealthy"
                    health_info["issues"].append("基盤データファイルが存在しません")
                    if health_info["status"] == "healthy":
                        health_info["status"] = "degraded"
            except Exception as e:
                health_info["components"]["base_data"] = "unhealthy"
                health_info["issues"].append(f"基盤データチェックエラー: {e}")
                health_info["status"] = "unhealthy"

            logger.info(
                f"✅ システム初期化マネージャー健全性チェック完了: {health_info['status']}"
            )
            return health_info

        except Exception as e:
            logger.error(f"❌ システム初期化マネージャー健全性チェックエラー: {e}")
            return {
                "timestamp": datetime.now(),
                "status": "unhealthy",
                "components": {},
                "issues": [f"健全性チェックエラー: {e}"],
            }

    async def reset_initialization_status(self) -> None:
        """
        初期化状態をリセット
        """
        self.initialization_status = {
            "is_initialized": False,
            "initialization_date": None,
            "base_data_restored": False,
            "differential_data_updated": False,
            "data_counts": {},
            "indicator_counts": {},
            "pattern_counts": {},
        }
        logger.info("🔄 初期化状態をリセットしました")

    async def cleanup(self) -> None:
        """
        リソースのクリーンアップ
        """
        try:
            if self.session:
                await self.session.close()
            logger.info("✅ システム初期化マネージャーのクリーンアップ完了")
        except Exception as e:
            logger.error(f"クリーンアップエラー: {e}")
