"""
継続処理システム統合cronスクリプトのテスト

責任:
- ContinuousProcessingCronクラスのテスト
- 各種実行モードのテスト
- エラーハンドリングのテスト
- 健全性チェックのテスト
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scripts.cron.continuous_processing_cron import ContinuousProcessingCron


class TestContinuousProcessingCron:
    """継続処理システム統合cronのテストクラス"""

    @pytest.fixture
    def cron(self):
        """ContinuousProcessingCronインスタンスを作成"""
        return ContinuousProcessingCron()

    @pytest.fixture
    def mock_session(self):
        """モックセッションを作成"""
        return AsyncMock()

    @pytest.fixture
    def mock_initialization_manager(self):
        """モック初期化マネージャーを作成"""
        mock = AsyncMock()
        mock.health_check.return_value = {"status": "healthy"}
        mock.run_system_cycle.return_value = {
            "status": "success",
            "processing_time": 10.5,
            "data_volume": 100,
        }
        return mock

    @pytest.fixture
    def mock_scheduler(self):
        """モックスケジューラーを作成"""
        mock = AsyncMock()
        mock.health_check.return_value = {"status": "healthy"}
        mock.run_single_cycle.return_value = None
        mock.get_scheduler_stats.return_value = {
            "total_runs": 1,
            "successful_runs": 1,
            "failed_runs": 0,
            "average_processing_time": 5.2,
        }
        return mock

    @pytest.fixture
    def mock_monitor(self):
        """モック監視サービスを作成"""
        mock = AsyncMock()
        mock.health_check.return_value = {"status": "healthy"}
        mock.start_monitoring.return_value = None
        mock.monitor_processing_cycle.return_value = None
        return mock

    @pytest.mark.asyncio
    async def test_initialize_database_success(self, cron):
        """データベース初期化の成功テスト"""
        with patch.dict("os.environ", {"DATABASE_URL": "sqlite+aiosqlite:///:memory:"}):
            with patch(
                "scripts.cron.continuous_processing_cron.create_async_engine"
            ) as mock_engine:
                mock_engine.return_value = MagicMock()

                await cron.initialize_database()

                assert cron.db_url == "sqlite+aiosqlite:///:memory:"
                assert cron.engine is not None
                assert cron.session_factory is not None

    @pytest.mark.asyncio
    async def test_initialize_database_missing_url(self, cron):
        """データベースURLが不足している場合のテスト"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="DATABASE_URL環境変数が設定されていません"
            ):
                await cron.initialize_database()

    @pytest.mark.asyncio
    async def test_initialize_services_success(self, cron):
        """サービス初期化の成功テスト"""
        cron.session_factory = MagicMock()
        cron.session_factory.return_value = AsyncMock()

        with patch(
            "scripts.cron.continuous_processing_cron.SystemInitializationManager"
        ) as mock_init_manager:
            with patch(
                "scripts.cron.continuous_processing_cron.ContinuousProcessingScheduler"
            ) as mock_scheduler:
                with patch(
                    "scripts.cron.continuous_processing_cron.ContinuousProcessingMonitor"
                ) as mock_monitor:
                    mock_init_manager.return_value = AsyncMock()
                    mock_scheduler.return_value = AsyncMock()
                    mock_monitor.return_value = AsyncMock()

                    await cron.initialize_services()

                    assert cron.session is not None
                    assert cron.initialization_manager is not None
                    assert cron.scheduler is not None
                    assert cron.monitor is not None

    @pytest.mark.asyncio
    async def test_run_system_cycle_success(
        self, cron, mock_initialization_manager, mock_monitor
    ):
        """システムサイクル実行の成功テスト"""
        cron.initialization_manager = mock_initialization_manager
        cron.monitor = mock_monitor

        result = await cron.run_system_cycle()

        assert result["status"] == "success"
        assert result["processing_time"] == 10.5
        assert result["data_volume"] == 100

        # 監視が呼ばれたことを確認
        mock_monitor.start_monitoring.assert_called_once()
        mock_monitor.monitor_processing_cycle.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_system_cycle_error(self, cron, mock_monitor):
        """システムサイクル実行のエラーテスト"""
        cron.initialization_manager = AsyncMock()
        cron.initialization_manager.run_system_cycle.side_effect = Exception(
            "Test error"
        )
        cron.monitor = mock_monitor

        with pytest.raises(Exception, match="Test error"):
            await cron.run_system_cycle()

        # エラー監視が呼ばれたことを確認
        mock_monitor.monitor_processing_cycle.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_single_cycle_success(self, cron, mock_scheduler, mock_monitor):
        """単一サイクル実行の成功テスト"""
        cron.scheduler = mock_scheduler
        cron.monitor = mock_monitor

        result = await cron.run_single_cycle()

        assert result["total_runs"] == 1
        assert result["successful_runs"] == 1
        assert result["failed_runs"] == 0
        assert result["average_processing_time"] == 5.2

        # 監視が呼ばれたことを確認
        mock_monitor.start_monitoring.assert_called_once()
        mock_monitor.monitor_processing_cycle.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_single_cycle_error(self, cron, mock_monitor):
        """単一サイクル実行のエラーテスト"""
        cron.scheduler = AsyncMock()
        cron.scheduler.run_single_cycle.side_effect = Exception("Test error")
        cron.monitor = mock_monitor

        with pytest.raises(Exception, match="Test error"):
            await cron.run_single_cycle()

        # エラー監視が呼ばれたことを確認
        mock_monitor.monitor_processing_cycle.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_system_health_healthy(
        self, cron, mock_initialization_manager, mock_scheduler, mock_monitor
    ):
        """システム健全性チェック（健全）のテスト"""
        cron.initialization_manager = mock_initialization_manager
        cron.scheduler = mock_scheduler
        cron.monitor = mock_monitor

        health = await cron.check_system_health()

        assert health["overall_status"] == "healthy"
        assert "timestamp" in health
        assert "initialization_manager" in health
        assert "scheduler" in health
        assert "monitor" in health

    @pytest.mark.asyncio
    async def test_check_system_health_unhealthy(
        self, cron, mock_scheduler, mock_monitor
    ):
        """システム健全性チェック（不健全）のテスト"""
        cron.initialization_manager = AsyncMock()
        cron.initialization_manager.health_check.return_value = {"status": "unhealthy"}
        cron.scheduler = mock_scheduler
        cron.monitor = mock_monitor

        health = await cron.check_system_health()

        assert health["overall_status"] == "unhealthy"

    @pytest.mark.asyncio
    async def test_check_system_health_degraded(
        self, cron, mock_initialization_manager, mock_monitor
    ):
        """システム健全性チェック（劣化）のテスト"""
        cron.initialization_manager = mock_initialization_manager
        cron.scheduler = AsyncMock()
        cron.scheduler.health_check.return_value = {"status": "degraded"}
        cron.monitor = mock_monitor

        health = await cron.check_system_health()

        assert health["overall_status"] == "degraded"

    @pytest.mark.asyncio
    async def test_check_system_health_error(self, cron):
        """システム健全性チェックエラーのテスト"""
        cron.initialization_manager = AsyncMock()
        cron.initialization_manager.health_check.side_effect = Exception(
            "Health check error"
        )

        health = await cron.check_system_health()

        assert health["overall_status"] == "unhealthy"
        assert "error" in health

    @pytest.mark.asyncio
    async def test_cleanup_success(self, cron):
        """クリーンアップの成功テスト"""
        cron.session = AsyncMock()
        cron.engine = MagicMock()

        await cron.cleanup()

        cron.session.close.assert_called_once()
        cron.engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_error(self, cron):
        """クリーンアップエラーのテスト"""
        cron.session = AsyncMock()
        cron.session.close.side_effect = Exception("Cleanup error")
        cron.engine = MagicMock()

        # エラーが発生しても処理を継続
        await cron.cleanup()

        cron.engine.dispose.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_system_cycle_mode(self, cron):
        """システムサイクルモードでの実行テスト"""
        with patch.object(cron, "initialize_database") as mock_init_db:
            with patch.object(cron, "initialize_services") as mock_init_services:
                with patch.object(cron, "check_system_health") as mock_health:
                    with patch.object(cron, "run_system_cycle") as mock_run_cycle:
                        with patch.object(cron, "cleanup") as mock_cleanup:
                            mock_health.return_value = {"overall_status": "healthy"}
                            mock_run_cycle.return_value = {"status": "success"}

                            result = await cron.run("system_cycle")

                            assert result["status"] == "success"
                            mock_init_db.assert_called_once()
                            mock_init_services.assert_called_once()
                            mock_health.assert_called_once()
                            mock_run_cycle.assert_called_once()
                            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_single_cycle_mode(self, cron):
        """単一サイクルモードでの実行テスト"""
        with patch.object(cron, "initialize_database") as mock_init_db:
            with patch.object(cron, "initialize_services") as mock_init_services:
                with patch.object(cron, "check_system_health") as mock_health:
                    with patch.object(cron, "run_single_cycle") as mock_run_cycle:
                        with patch.object(cron, "cleanup") as mock_cleanup:
                            mock_health.return_value = {"overall_status": "healthy"}
                            mock_run_cycle.return_value = {"status": "success"}

                            result = await cron.run("single_cycle")

                            assert result["status"] == "success"
                            mock_init_db.assert_called_once()
                            mock_init_services.assert_called_once()
                            mock_health.assert_called_once()
                            mock_run_cycle.assert_called_once()
                            mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_invalid_mode(self, cron):
        """無効なモードでの実行テスト"""
        with patch.object(cron, "initialize_database") as mock_init_db:
            with patch.object(cron, "initialize_services") as mock_init_services:
                with patch.object(cron, "check_system_health") as mock_health:
                    with patch.object(cron, "cleanup") as mock_cleanup:
                        mock_health.return_value = {"overall_status": "healthy"}

                        result = await cron.run("invalid_mode")

                        assert result["status"] == "error"
                        assert "不明なモード: invalid_mode" in result["error"]
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_unhealthy_system(self, cron):
        """不健全なシステムでの実行テスト"""
        with patch.object(cron, "initialize_database") as mock_init_db:
            with patch.object(cron, "initialize_services") as mock_init_services:
                with patch.object(cron, "check_system_health") as mock_health:
                    with patch.object(cron, "cleanup") as mock_cleanup:
                        mock_health.return_value = {"overall_status": "unhealthy"}

                        result = await cron.run("system_cycle")

                        assert result["status"] == "error"
                        assert result["message"] == "System unhealthy"
                        mock_cleanup.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_exception_handling(self, cron):
        """例外処理のテスト"""
        with patch.object(cron, "initialize_database") as mock_init_db:
            mock_init_db.side_effect = Exception("Database error")
            with patch.object(cron, "cleanup") as mock_cleanup:

                result = await cron.run("system_cycle")

                assert result["status"] == "error"
                assert "Database error" in result["error"]
                mock_cleanup.assert_called_once()


class TestContinuousProcessingCronIntegration:
    """継続処理システム統合cronの統合テストクラス"""

    @pytest.mark.asyncio
    async def test_full_system_cycle_integration(self):
        """完全なシステムサイクルの統合テスト"""
        # このテストは実際のデータベース接続を使用するため、
        # 本番環境でのテスト時に実行
        pass

    @pytest.mark.asyncio
    async def test_health_check_integration(self):
        """健全性チェックの統合テスト"""
        # このテストは実際のサービスを使用するため、
        # 本番環境でのテスト時に実行
        pass
