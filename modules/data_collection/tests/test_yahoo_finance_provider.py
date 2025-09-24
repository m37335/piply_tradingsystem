"""
Yahoo Finance プロバイダーのテスト

Yahoo Finance APIプロバイダーの機能をテストします。
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import pytest

from ..providers.base_provider import TimeFrame
from ..providers.yahoo_finance import YahooFinanceProvider


class TestYahooFinanceProvider:
    """Yahoo Finance プロバイダーのテストクラス"""

    @pytest.fixture
    def provider(self):
        """プロバイダーのフィクスチャ"""
        return YahooFinanceProvider()

    @pytest.fixture
    def mock_ticker_data(self):
        """モックティッカーデータ"""
        import pandas as pd

        dates = pd.date_range(
            start=datetime.now() - timedelta(days=1), end=datetime.now(), freq="5T"
        )

        data = {
            "Open": [110.0, 110.5, 111.0, 111.5, 112.0],
            "High": [110.5, 111.0, 111.5, 112.0, 112.5],
            "Low": [109.5, 110.0, 110.5, 111.0, 111.5],
            "Close": [110.5, 111.0, 111.5, 112.0, 112.5],
            "Volume": [1000, 1200, 1100, 1300, 1400],
        }

        return pd.DataFrame(data, index=dates[:5])

    @pytest.mark.asyncio
    async def test_get_historical_data_success(self, provider, mock_ticker_data):
        """履歴データ取得の成功テスト"""
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = mock_ticker_data
            mock_ticker.return_value = mock_ticker_instance

            start_date = datetime.now() - timedelta(days=1)
            end_date = datetime.now()

            result = await provider.get_historical_data(
                symbol="USDJPY=X",
                timeframe=TimeFrame.M5,
                start_date=start_date,
                end_date=end_date,
            )

            assert result.success is True
            assert len(result.data) == 5
            assert result.data[0].symbol == "USDJPY=X"
            assert result.data[0].timeframe == TimeFrame.M5
            assert result.data[0].source == "yahoo_finance"

    @pytest.mark.asyncio
    async def test_get_historical_data_empty(self, provider):
        """履歴データ取得の空データテスト"""
        with patch("yfinance.Ticker") as mock_ticker:
            import pandas as pd

            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = pd.DataFrame()
            mock_ticker.return_value = mock_ticker_instance

            start_date = datetime.now() - timedelta(days=1)
            end_date = datetime.now()

            result = await provider.get_historical_data(
                symbol="INVALID_SYMBOL",
                timeframe=TimeFrame.M5,
                start_date=start_date,
                end_date=end_date,
            )

            assert result.success is False
            assert len(result.data) == 0
            assert "No data found" in result.error_message

    @pytest.mark.asyncio
    async def test_get_latest_data(self, provider, mock_ticker_data):
        """最新データ取得のテスト"""
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.return_value = mock_ticker_data
            mock_ticker.return_value = mock_ticker_instance

            result = await provider.get_latest_data(
                symbol="USDJPY=X", timeframe=TimeFrame.M5
            )

            assert result.success is True
            assert len(result.data) > 0

    def test_get_available_symbols(self, provider):
        """利用可能シンボル取得のテスト"""
        symbols = provider.get_available_symbols()

        assert isinstance(symbols, list)
        assert len(symbols) > 0
        assert "USDJPY=X" in symbols
        assert "^N225" in symbols

    def test_is_available(self, provider):
        """利用可能性チェックのテスト"""
        assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_health_check_success(self, provider):
        """ヘルスチェック成功のテスト"""
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {"symbol": "USDJPY=X"}
            mock_ticker.return_value = mock_ticker_instance

            result = await provider.health_check()

            assert result is True
            assert provider.is_available() is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, provider):
        """ヘルスチェック失敗のテスト"""
        with patch("yfinance.Ticker") as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {}
            mock_ticker.return_value = mock_ticker_instance

            result = await provider.health_check()

            assert result is False
            assert provider.is_available() is False

    def test_convert_timeframe(self, provider):
        """時間軸変換のテスト"""
        assert provider._convert_timeframe(TimeFrame.M1) == "1m"
        assert provider._convert_timeframe(TimeFrame.M5) == "5m"
        assert provider._convert_timeframe(TimeFrame.H1) == "1h"
        assert provider._convert_timeframe(TimeFrame.D1) == "1d"

    def test_calculate_quality_score(self, provider):
        """品質スコア計算のテスト"""
        import pandas as pd

        # 正常なデータ
        normal_row = pd.Series(
            {"Open": 110.0, "High": 111.0, "Low": 109.0, "Close": 110.5, "Volume": 1000}
        )

        score = provider._calculate_quality_score(normal_row)
        assert score == 1.0

        # 異常なデータ（High < Low）
        abnormal_row = pd.Series(
            {
                "Open": 110.0,
                "High": 109.0,  # High < Low
                "Low": 111.0,
                "Close": 110.5,
                "Volume": 1000,
            }
        )

        score = provider._calculate_quality_score(abnormal_row)
        assert score < 1.0

    def test_set_rate_limiter(self, provider):
        """レート制限器設定のテスト"""
        mock_limiter = Mock()
        provider.set_rate_limiter(mock_limiter)

        assert provider._rate_limiter == mock_limiter
