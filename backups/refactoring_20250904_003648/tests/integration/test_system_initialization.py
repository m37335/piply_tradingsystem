"""
SystemInitializationManagerの統合テスト

テスト内容:
- 初期化状態のチェック
- 初回初期化の実行
- 継続処理の開始
- システムサイクルの実行
- システム健全性の検証
"""

from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.services.system_initialization_manager import (
    SystemInitializationManager,
)


class TestSystemInitializationManager:
    """SystemInitializationManagerの統合テスト"""

    @pytest.fixture
    async def mock_session(self):
        """モックセッション"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def mock_initial_loader(self):
        """モックInitial Data Loader"""
        with patch(
            "src.infrastructure.database.services."
            "initial_data_loader_service.InitialDataLoaderService"
        ) as mock:
            loader = mock.return_value
            loader.get_initialization_status = AsyncMock()
            loader.load_all_initial_data = AsyncMock()
            yield loader

    @pytest.fixture
    async def mock_continuous_service(self):
        """モックContinuous Processing Service"""
        with patch(
            "src.infrastructure.database.services."
            "continuous_processing_service.ContinuousProcessingService"
        ) as mock:
            service = mock.return_value
            service.initialize = AsyncMock()
            service.process_latest_data = AsyncMock()
            service.get_status = AsyncMock()
            yield service

    @pytest.fixture
    async def mock_monitor(self):
        """モックContinuous Processing Monitor"""
        with patch(
            "src.infrastructure.monitoring."
            "continuous_processing_monitor.ContinuousProcessingMonitor"
        ) as mock:
            monitor = mock.return_value
            monitor.start_monitoring = AsyncMock()
            monitor.get_status = AsyncMock()
            yield monitor

    @pytest.fixture
    async def system_manager(
        self, mock_session, mock_initial_loader, mock_continuous_service, mock_monitor
    ):
        """SystemInitializationManagerインスタンス"""
        return SystemInitializationManager(mock_session)

    @pytest.mark.asyncio
    async def test_check_initialization_status_success(
        self, system_manager, mock_initial_loader
    ):
        """初期化状態チェック成功テスト"""
        # モック設定
        mock_initial_loader.price_repo.count_by_date_range.return_value = 200
        mock_initial_loader.indicator_service.count_latest_indicators.return_value = 100

        # テスト実行
        result = await system_manager.check_initialization_status()

        # 検証
        assert result is True

    @pytest.mark.asyncio
    async def test_check_initialization_status_insufficient_data(
        self, system_manager, mock_initial_loader
    ):
        """データ不足時の初期化状態チェックテスト"""
        # データ不足をモック
        mock_initial_loader.price_repo.count_by_date_range.return_value = 10

        # テスト実行
        result = await system_manager.check_initialization_status()

        # 検証
        assert result is False

    @pytest.mark.asyncio
    async def test_perform_initial_initialization_success(
        self, system_manager, mock_initial_loader
    ):
        """初回初期化成功テスト"""
        # モック設定
        mock_initial_loader.load_all_initial_data.return_value = {
            "is_initialized": True,
            "data_counts": {"5m": 100, "1h": 50, "4h": 30, "1d": 30},
            "indicator_counts": {"total": 100},
            "pattern_counts": {"total": 20},
        }

        # テスト実行
        result = await system_manager.perform_initial_initialization()

        # 検証
        assert result["is_initialized"] is True
        assert system_manager.initialization_status["is_initialized"] is True
        assert system_manager.initialization_status["initialization_date"] is not None

    @pytest.mark.asyncio
    async def test_perform_initial_initialization_failure(
        self, system_manager, mock_initial_loader
    ):
        """初回初期化失敗テスト"""
        # モック設定
        mock_initial_loader.load_all_initial_data.return_value = {
            "is_initialized": False,
            "error": "Initialization failed",
        }

        # テスト実行
        result = await system_manager.perform_initial_initialization()

        # 検証
        assert result["is_initialized"] is False
        assert system_manager.initialization_status["is_initialized"] is False

    @pytest.mark.asyncio
    async def test_start_continuous_processing_success(
        self, system_manager, mock_continuous_service, mock_monitor
    ):
        """継続処理開始成功テスト"""
        # テスト実行
        result = await system_manager.start_continuous_processing()

        # 検証
        assert result is True
        mock_continuous_service.initialize.assert_called_once()
        mock_monitor.start_monitoring.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_continuous_processing_failure(
        self, system_manager, mock_continuous_service
    ):
        """継続処理開始失敗テスト"""
        # モック設定
        mock_continuous_service.initialize.side_effect = Exception("Init failed")

        # テスト実行
        result = await system_manager.start_continuous_processing()

        # 検証
        assert result is False

    @pytest.mark.asyncio
    async def test_run_system_cycle_initialization_needed(
        self, system_manager, mock_initial_loader, mock_continuous_service
    ):
        """初期化が必要なシステムサイクルテスト"""
        # 初期化が必要な状態をモック
        mock_initial_loader.price_repo.count_by_date_range.return_value = 10
        mock_initial_loader.load_all_initial_data.return_value = {
            "is_initialized": True,
            "data_counts": {"5m": 100, "1h": 50, "4h": 30, "1d": 30},
        }

        # テスト実行
        result = await system_manager.run_system_cycle()

        # 検証
        assert result["is_initialized"] is True
        mock_initial_loader.load_all_initial_data.assert_called_once()
        mock_continuous_service.process_latest_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_system_cycle_continuous_processing(
        self, system_manager, mock_initial_loader, mock_continuous_service
    ):
        """継続処理実行のシステムサイクルテスト"""
        # 初期化済みの状態をモック
        mock_initial_loader.price_repo.count_by_date_range.return_value = 200
        mock_initial_loader.indicator_service.count_latest_indicators.return_value = 100
        mock_continuous_service.process_latest_data.return_value = {
            "status": "success",
            "processed_data": 1,
        }

        # テスト実行
        result = await system_manager.run_system_cycle()

        # 検証
        assert result["status"] == "success"
        mock_initial_loader.load_all_initial_data.assert_not_called()
        mock_continuous_service.process_latest_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_system_status_success(
        self, system_manager, mock_initial_loader, mock_continuous_service, mock_monitor
    ):
        """システム状態取得成功テスト"""
        # モック設定
        mock_initial_loader.get_initialization_status.return_value = {
            "is_initialized": True
        }
        mock_continuous_service.get_status.return_value = {"is_running": True}
        mock_monitor.get_status.return_value = {"is_active": True}

        # テスト実行
        result = await system_manager.get_system_status()

        # 検証
        assert "initialization" in result
        assert "continuous_processing" in result
        assert "monitoring" in result
        assert "last_updated" in result

    @pytest.mark.asyncio
    async def test_retry_initialization_success(
        self, system_manager, mock_initial_loader
    ):
        """初期化再試行成功テスト"""
        # モック設定
        mock_initial_loader.load_all_initial_data.return_value = {
            "is_initialized": True
        }

        # テスト実行
        result = await system_manager.retry_initialization()

        # 検証
        assert result["is_initialized"] is True

    @pytest.mark.asyncio
    async def test_retry_initialization_failure(
        self, system_manager, mock_initial_loader
    ):
        """初期化再試行失敗テスト"""
        # モック設定
        mock_initial_loader.load_all_initial_data.side_effect = Exception("Failed")

        # テスト実行
        result = await system_manager.retry_initialization()

        # 検証
        assert result["is_initialized"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_reset_initialization_success(self, system_manager):
        """初期化状態リセット成功テスト"""
        # 初期化状態を設定
        system_manager.initialization_status["is_initialized"] = True
        system_manager.initialization_status["initialization_date"] = datetime.now()

        # テスト実行
        result = await system_manager.reset_initialization()

        # 検証
        assert result is True
        assert system_manager.initialization_status["is_initialized"] is False
        assert system_manager.initialization_status["initialization_date"] is None

    @pytest.mark.asyncio
    async def test_validate_system_health_healthy(
        self, system_manager, mock_initial_loader, mock_continuous_service, mock_monitor
    ):
        """システム健全性検証（健全）テスト"""
        # モック設定
        mock_initial_loader.get_initialization_status.return_value = {
            "is_initialized": True
        }
        mock_continuous_service.get_status.return_value = {"is_running": True}
        mock_monitor.get_status.return_value = {"is_active": True}

        # テスト実行
        result = await system_manager.validate_system_health()

        # 検証
        assert result["overall_health"] == "healthy"
        assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_validate_system_health_warning(
        self, system_manager, mock_initial_loader, mock_continuous_service, mock_monitor
    ):
        """システム健全性検証（警告）テスト"""
        # モック設定
        mock_initial_loader.get_initialization_status.return_value = {
            "is_initialized": False
        }
        mock_continuous_service.get_status.return_value = {"is_running": True}
        mock_monitor.get_status.return_value = {"is_active": True}

        # テスト実行
        result = await system_manager.validate_system_health()

        # 検証
        assert result["overall_health"] == "warning"
        assert len(result["issues"]) > 0

    @pytest.mark.asyncio
    async def test_validate_system_health_critical(
        self, system_manager, mock_initial_loader, mock_continuous_service, mock_monitor
    ):
        """システム健全性検証（重大）テスト"""
        # モック設定
        mock_initial_loader.get_initialization_status.return_value = {
            "is_initialized": False
        }
        mock_continuous_service.get_status.return_value = {"is_running": False}
        mock_monitor.get_status.return_value = {"is_active": False}

        # テスト実行
        result = await system_manager.validate_system_health()

        # 検証
        assert result["overall_health"] == "critical"
        assert len(result["issues"]) >= 3

    @pytest.mark.asyncio
    async def test_validate_system_health_error(
        self, system_manager, mock_initial_loader
    ):
        """システム健全性検証（エラー）テスト"""
        # モック設定
        mock_initial_loader.get_initialization_status.side_effect = Exception("Error")

        # テスト実行
        result = await system_manager.validate_system_health()

        # 検証
        assert result["overall_health"] == "error"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_configuration(self, system_manager):
        """設定のテスト"""
        assert system_manager.currency_pair == "USD/JPY"
        assert system_manager.max_retry_attempts == 3
        assert system_manager.retry_delay == 30

    @pytest.mark.asyncio
    async def test_initialization_status_structure(self, system_manager):
        """初期化状態構造のテスト"""
        status = system_manager.initialization_status

        assert "is_initialized" in status
        assert "initialization_date" in status
        assert "data_counts" in status
        assert "indicator_counts" in status
        assert "pattern_counts" in status

        assert status["is_initialized"] is False
        assert status["initialization_date"] is None
