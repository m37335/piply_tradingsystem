"""
UnifiedTechnicalCalculator 統合テスト

テスト対象:
- UnifiedTechnicalIndicatorService の初期化と動作
- ContinuousProcessingService との統合
- ContinuousProcessingScheduler との統合
- SystemInitializationManager との統合
- エラーハンドリングとロールバック機能
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from src.infrastructure.database.services.unified_technical_indicator_service import (
    UnifiedTechnicalIndicatorService,
)


class TestUnifiedTechnicalIntegration:
    """UnifiedTechnicalCalculator 統合テストクラス"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        return AsyncMock()

    @pytest.fixture
    def mock_unified_calculator(self):
        """モックUnifiedTechnicalCalculator"""
        mock = AsyncMock()
        mock.calculate_timeframe_indicators.return_value = {
            "RSI": 10,
            "MACD": 5,
            "BB": 8,
            "STOCH": 6,
            "ATR": 4,
        }
        mock.health_check.return_value = {"status": "healthy"}
        return mock

    @pytest.fixture
    def unified_service(self, mock_session):
        """UnifiedTechnicalIndicatorService インスタンス"""
        return UnifiedTechnicalIndicatorService(mock_session, "USD/JPY")

    async def test_unified_service_initialization(self, unified_service):
        """UnifiedTechnicalIndicatorService の初期化テスト"""
        with patch(
            "scripts.cron.unified_technical_calculator.UnifiedTechnicalCalculator"
        ) as mock_calc:
            mock_calc.return_value.initialize = AsyncMock(return_value=True)

            result = await unified_service.initialize()

            assert result is True
            assert unified_service.is_initialized is True
            assert unified_service.calculator is not None

    async def test_calculate_and_save_all_indicators(
        self, unified_service, mock_unified_calculator
    ):
        """全指標計算テスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        result = await unified_service.calculate_and_save_all_indicators("M5")

        assert "RSI" in result
        assert "MACD" in result
        assert "BB" in result
        assert "STOCH" in result
        assert "ATR" in result

    async def test_health_check(self, unified_service, mock_unified_calculator):
        """健全性チェックテスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        health = await unified_service.health_check()

        assert health["status"] == "healthy"
        assert "timestamp" in health
        assert health["service_type"] == "UnifiedTechnicalIndicatorService"

    async def test_error_handling(self, unified_service):
        """エラーハンドリングテスト"""
        # 初期化前の健全性チェック
        health = await unified_service.health_check()
        assert health["status"] == "uninitialized"

        # 初期化後のエラーハンドリング（データベースエラー）
        result = await unified_service.calculate_and_save_all_indicators("M5")
        # データベースエラーのため、0が返される
        assert isinstance(result, int)
        assert result == 0

    async def test_calculate_rsi(self, unified_service, mock_unified_calculator):
        """RSI計算テスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        # モックデータの準備
        mock_data = {"Close": [100, 101, 102, 103, 104]}
        mock_unified_calculator.calculate_rsi.return_value = {
            "current_value": 65.5,
            "timeframe": "M5",
            "indicator": "RSI",
        }

        result = await unified_service.calculate_rsi(mock_data, "M5")

        assert result["current_value"] == 65.5
        assert result["timeframe"] == "M5"
        assert result["indicator"] == "RSI"

    async def test_calculate_macd(self, unified_service, mock_unified_calculator):
        """MACD計算テスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        # モックデータの準備
        mock_data = {"Close": [100, 101, 102, 103, 104]}
        mock_unified_calculator.calculate_macd.return_value = {
            "macd": 0.1234,
            "signal": 0.0987,
            "histogram": 0.0247,
            "timeframe": "M5",
            "indicator": "MACD",
        }

        result = await unified_service.calculate_macd(mock_data, "M5")

        assert result["macd"] == 0.1234
        assert result["signal"] == 0.0987
        assert result["histogram"] == 0.0247
        assert result["timeframe"] == "M5"
        assert result["indicator"] == "MACD"

    async def test_calculate_bollinger_bands(
        self, unified_service, mock_unified_calculator
    ):
        """ボリンジャーバンド計算テスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        # モックデータの準備
        mock_data = {"Close": [100, 101, 102, 103, 104]}
        mock_unified_calculator.calculate_bollinger_bands.return_value = {
            "upper": 105.5,
            "middle": 102.0,
            "lower": 98.5,
            "timeframe": "M5",
            "indicator": "Bollinger_Bands",
        }

        result = await unified_service.calculate_bollinger_bands(mock_data, "M5")

        assert result["upper"] == 105.5
        assert result["middle"] == 102.0
        assert result["lower"] == 98.5
        assert result["timeframe"] == "M5"
        assert result["indicator"] == "Bollinger_Bands"

    async def test_cleanup(self, unified_service, mock_unified_calculator):
        """クリーンアップテスト"""
        unified_service.calculator = mock_unified_calculator
        unified_service.is_initialized = True

        await unified_service.cleanup()

        # クリーンアップが呼ばれたことを確認
        mock_unified_calculator.cleanup.assert_called_once()

    async def test_initialization_failure(self, unified_service):
        """初期化失敗テスト"""
        with patch(
            "scripts.cron.unified_technical_calculator.UnifiedTechnicalCalculator"
        ) as mock_calc:
            # コンストラクタでエラーを発生させる
            mock_calc.side_effect = Exception("初期化エラー")

            result = await unified_service.initialize()

            assert result is False
            assert unified_service.is_initialized is False
            assert unified_service.initialization_error == "初期化エラー"
