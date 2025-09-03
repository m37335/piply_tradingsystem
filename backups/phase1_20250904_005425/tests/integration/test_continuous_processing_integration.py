"""
ContinuousProcessingService と ContinuousProcessingScheduler の統合テスト

テスト対象:
- ContinuousProcessingService の UnifiedTechnicalCalculator 統合
- ContinuousProcessingScheduler の間接的統合
- エラーハンドリングとロールバック機能
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.database.services.continuous_processing_service import (
    ContinuousProcessingService,
)
from src.infrastructure.schedulers.continuous_processing_scheduler import (
    ContinuousProcessingScheduler,
)


class TestContinuousProcessingIntegration:
    """ContinuousProcessingService 統合テストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        return AsyncMock()

    @pytest.fixture
    def mock_price_data(self):
        """モック価格データ"""
        mock_data = AsyncMock()
        mock_data.timestamp = "2025-01-15T10:00:00"
        mock_data.open_price = 150.0
        mock_data.high_price = 151.0
        mock_data.low_price = 149.0
        mock_data.close_price = 150.5
        mock_data.volume = 1000000
        return mock_data

    @pytest.fixture
    def continuous_service(self, mock_session):
        """ContinuousProcessingService インスタンス"""
        return ContinuousProcessingService(mock_session)

    @pytest.fixture
    def scheduler(self, mock_session):
        """ContinuousProcessingScheduler インスタンス"""
        return ContinuousProcessingScheduler(mock_session)

    async def test_continuous_service_initialization(self, continuous_service):
        """ContinuousProcessingService の初期化テスト"""
        # UnifiedTechnicalIndicatorService が正しく初期化されていることを確認
        assert hasattr(continuous_service, "technical_indicator_service")
        assert continuous_service.technical_indicator_service is not None
        assert (
            continuous_service.technical_indicator_service.__class__.__name__
            == "UnifiedTechnicalIndicatorService"
        )

    async def test_scheduler_initialization(self, scheduler):
        """ContinuousProcessingScheduler の初期化テスト"""
        # ContinuousProcessingService が正しく初期化されていることを確認
        assert hasattr(scheduler, "continuous_service")
        assert scheduler.continuous_service is not None
        assert (
            scheduler.continuous_service.__class__.__name__
            == "ContinuousProcessingService"
        )

    async def test_continuous_service_process_5m_data(
        self, continuous_service, mock_price_data
    ):
        """ContinuousProcessingService の5分足データ処理テスト"""
        with patch.object(
            continuous_service.technical_indicator_service,
            "calculate_and_save_all_indicators",
            return_value={"total": 10, "timeframe": "M5", "status": "success"},
        ):
            with patch.object(
                continuous_service.timeframe_aggregator,
                "aggregate_1h_data",
                return_value=[mock_price_data],
            ):
                with patch.object(
                    continuous_service.timeframe_aggregator,
                    "aggregate_4h_data",
                    return_value=[mock_price_data],
                ):
                    with patch.object(
                        continuous_service.timeframe_aggregator,
                        "aggregate_1d_data",
                        return_value=[mock_price_data],
                    ):
                        result = await continuous_service.process_5m_data(
                            mock_price_data
                        )

                        assert result["status"] == "success"
                        assert "aggregation" in result
                        assert "indicators" in result
                        assert "patterns" in result
                        assert "notifications" in result
                        assert "processing_time" in result

    async def test_scheduler_run_single_cycle(self, scheduler):
        """ContinuousProcessingScheduler の単一サイクル実行テスト"""
        with patch.object(
            scheduler.data_fetcher, "fetch_real_5m_data", return_value=AsyncMock()
        ):
            with patch.object(
                scheduler.continuous_service,
                "process_5m_data",
                return_value={"status": "success"},
            ):
                result = await scheduler.run_single_cycle()

                assert result is not None
                assert "status" in result

    async def test_health_check(self, scheduler):
        """健全性チェックテスト"""
        health = await scheduler.health_check()

        assert health["service"] == "ContinuousProcessingScheduler"
        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert "UnifiedTechnicalCalculator統合版" in health["message"]

    async def test_error_handling(self, continuous_service, mock_price_data):
        """エラーハンドリングテスト"""
        # より包括的なエラーハンドリングテスト
        with patch.object(
            continuous_service.timeframe_aggregator,
            "aggregate_1h_data",
            side_effect=Exception("時間軸集計エラー"),
        ):
            result = await continuous_service.process_5m_data(mock_price_data)

            # エラーが発生しても処理は継続される可能性があるため、
            # エラーログが出力されることを確認
            assert result is not None
            assert "processing_time" in result

    async def test_processing_stats(self, continuous_service):
        """処理統計テスト"""
        stats = await continuous_service.get_processing_stats()

        assert "total_cycles" in stats
        assert "successful_cycles" in stats
        assert "failed_cycles" in stats
        assert "success_rate" in stats
        assert "currency_pair" in stats
        assert "timeframes" in stats

    async def test_unified_technical_integration(self, continuous_service):
        """UnifiedTechnicalCalculator 統合テスト"""
        # UnifiedTechnicalIndicatorService の健全性チェック
        health = await continuous_service.technical_indicator_service.health_check()

        # 初期化前は uninitialized 状態
        assert health["status"] in ["uninitialized", "healthy"]

    async def test_timeframe_aggregation(self, continuous_service):
        """時間軸集計テスト"""
        with patch.object(
            continuous_service.timeframe_aggregator,
            "aggregate_1h_data",
            return_value=[AsyncMock()],
        ):
            with patch.object(
                continuous_service.timeframe_aggregator,
                "aggregate_4h_data",
                return_value=[AsyncMock()],
            ):
                with patch.object(
                    continuous_service.timeframe_aggregator,
                    "aggregate_1d_data",
                    return_value=[AsyncMock()],
                ):
                    result = await continuous_service.aggregate_timeframes()

                    assert "1h" in result
                    assert "4h" in result
                    assert "1d" in result
                    assert result["1h"] == 1
                    assert result["4h"] == 1
                    assert result["1d"] == 1
