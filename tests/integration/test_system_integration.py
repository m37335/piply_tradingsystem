"""
SystemInitializationManager 統合テスト

テスト対象:
- SystemInitializationManager の UnifiedTechnicalCalculator 統合
- システムサイクルの動作確認
- 新機能の活用確認
- エラーハンドリングとロールバック機能
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.database.services.system_initialization_manager import (
    SystemInitializationManager,
)


class TestSystemIntegration:
    """SystemInitializationManager 統合テストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        return AsyncMock()

    @pytest.fixture
    def system_manager(self, mock_session):
        """SystemInitializationManager インスタンス"""
        return SystemInitializationManager(mock_session)

    async def test_system_manager_initialization(self, system_manager):
        """SystemInitializationManager の初期化テスト"""
        # ContinuousProcessingService が正しく初期化されていることを確認
        assert hasattr(system_manager, "continuous_service")
        assert system_manager.continuous_service is not None
        assert (
            system_manager.continuous_service.__class__.__name__
            == "ContinuousProcessingService"
        )

        # UnifiedTechnicalIndicatorService が間接的に統合されていることを確認
        assert hasattr(system_manager.continuous_service, "technical_indicator_service")
        assert (
            system_manager.continuous_service.technical_indicator_service.__class__.__name__
            == "UnifiedTechnicalIndicatorService"
        )

    async def test_system_cycle_execution(self, system_manager):
        """システムサイクル実行テスト"""
        with patch.object(
            system_manager, "check_initialization_status", return_value=True
        ):
            with patch.object(
                system_manager.continuous_service,
                "process_latest_data",
                return_value={
                    "status": "success",
                    "processing_time": 1.5,
                    "data_volume": 100,
                    "indicators": {"RSI": 10, "MACD": 5, "STOCH": 6, "ATR": 4},
                },
            ):
                result = await system_manager.run_system_cycle()

                assert result["status"] == "success"
                assert "processing_time" in result
                assert "data_volume" in result
                assert "indicators" in result
                assert "STOCH" in result["indicators"]  # 新機能確認
                assert "ATR" in result["indicators"]  # 新機能確認

    async def test_initialization_check(self, system_manager):
        """初期化状態チェックテスト"""
        with patch.object(
            system_manager.initial_loader.price_repo,
            "count_by_date_range",
            return_value=200,  # 十分なデータ
        ):
            with patch.object(
                system_manager.initial_loader.indicator_service,
                "count_latest_indicators",
                return_value=50,  # 十分な指標
            ):
                result = await system_manager.check_initialization_status()
                assert result is True

    async def test_force_reinitialization(self, system_manager):
        """強制再初期化テスト"""
        with patch.object(
            system_manager,
            "perform_initial_initialization",
            return_value={
                "is_initialized": True,
                "data_counts": {"5m": 100, "1h": 50},
                "indicator_counts": {"RSI": 20, "MACD": 15},
            },
        ):
            result = await system_manager.run_system_cycle(force_reinitialize=True)

            assert result["is_initialized"] is True
            assert "data_counts" in result
            assert "indicator_counts" in result

    async def test_health_check(self, system_manager):
        """健全性チェックテスト"""
        # 基本的な健全性チェックのみ実行
        status = await system_manager.get_system_status()

        # 基本的な構造を確認
        assert "last_updated" in status

    async def test_error_handling(self, system_manager):
        """エラーハンドリングテスト"""
        with patch.object(
            system_manager,
            "check_initialization_status",
            side_effect=Exception("初期化状態チェックエラー"),
        ):
            with pytest.raises(Exception) as exc_info:
                await system_manager.run_system_cycle()

            assert "初期化状態チェックエラー" in str(exc_info.value)

    async def test_retry_initialization(self, system_manager):
        """初期化再試行テスト"""
        with patch.object(
            system_manager,
            "perform_initial_initialization",
            side_effect=[
                {"is_initialized": False, "error": "失敗1"},
                {"is_initialized": True, "data_counts": {"5m": 100}},
            ],
        ):
            result = await system_manager.retry_initialization()

            assert result["is_initialized"] is True
            assert "data_counts" in result

    async def test_reset_initialization(self, system_manager):
        """初期化状態リセットテスト"""
        # 初期状態を設定
        system_manager.initialization_status["is_initialized"] = True
        system_manager.initialization_status["initialization_date"] = "2025-01-01"

        result = await system_manager.reset_initialization()

        assert result is True
        assert system_manager.initialization_status["is_initialized"] is False
        assert system_manager.initialization_status["initialization_date"] is None

    async def test_unified_technical_integration(self, system_manager):
        """UnifiedTechnicalCalculator 統合テスト"""
        # ContinuousProcessingService 経由での統合確認
        health = await (
            system_manager.continuous_service.technical_indicator_service.health_check()
        )

        # 初期化前は uninitialized 状態
        assert health["status"] in ["uninitialized", "healthy"]

    async def test_new_features_utilization(self, system_manager):
        """新機能活用テスト"""
        with patch.object(
            system_manager, "check_initialization_status", return_value=True
        ):
            with patch.object(
                system_manager.continuous_service,
                "process_latest_data",
                return_value={
                    "status": "success",
                    "indicators": {
                        "RSI": 10,
                        "MACD": 5,
                        "BB": 8,
                        "STOCH": 6,  # 新機能：ストキャスティクス
                        "ATR": 4,  # 新機能：ATR
                    },
                },
            ):
                result = await system_manager.run_system_cycle()

                # 新機能が含まれていることを確認
                indicators = result.get("indicators", {})
                assert "STOCH" in indicators
                assert "ATR" in indicators
                assert indicators["STOCH"] == 6
                assert indicators["ATR"] == 4
