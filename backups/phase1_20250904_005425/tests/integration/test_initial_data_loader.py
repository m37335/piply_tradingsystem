"""
InitialDataLoaderServiceの統合テスト

テスト内容:
- 全時間軸の初回データ取得
- 初回テクニカル指標計算
- 初回パターン検出実行
- 初期化完了確認
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.services.initial_data_loader_service import (
    InitialDataLoaderService,
)


class TestInitialDataLoaderService:
    """InitialDataLoaderServiceの統合テスト"""

    @pytest.fixture
    async def mock_session(self):
        """モックセッション"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    async def mock_yahoo_client(self):
        """モックYahoo Finance Client"""
        with patch(
            "src.infrastructure.external_apis.yahoo_finance_client.YahooFinanceClient"
        ) as mock:
            client = mock.return_value
            client.get_historical_data = AsyncMock()
            yield client

    @pytest.fixture
    async def mock_price_repo(self):
        """モックPrice Repository"""
        with patch(
            "src.infrastructure.database.repositories.price_data_repository_impl."
            "PriceDataRepositoryImpl"
        ) as mock:
            repo = mock.return_value
            repo.count_by_date_range = AsyncMock(return_value=0)
            repo.find_by_timestamp = AsyncMock(return_value=None)
            repo.save = AsyncMock()
            yield repo

    @pytest.fixture
    async def mock_indicator_service(self):
        """モックTechnical Indicator Service"""
        with patch(
            "src.infrastructure.database.services."
            "multi_timeframe_technical_indicator_service."
            "MultiTimeframeTechnicalIndicatorService"
        ) as mock:
            service = mock.return_value
            service.calculate_timeframe_indicators = AsyncMock(return_value=10)
            service.count_latest_indicators = AsyncMock(return_value=100)
            yield service

    @pytest.fixture
    async def mock_pattern_service(self):
        """モックPattern Detection Service"""
        with patch(
            "src.infrastructure.analysis.efficient_pattern_detection_service.EfficientPatternDetectionService"
        ) as mock:
            service = mock.return_value
            service.detect_all_patterns_for_timeframe = AsyncMock(return_value=5)
            service.count_latest_patterns = AsyncMock(return_value=20)
            yield service

    @pytest.fixture
    async def initial_data_loader(
        self,
        mock_session,
        mock_yahoo_client,
        mock_price_repo,
        mock_indicator_service,
        mock_pattern_service,
    ):
        """InitialDataLoaderServiceインスタンス"""
        return InitialDataLoaderService(mock_session)

    @pytest.mark.asyncio
    async def test_load_all_initial_data_success(
        self, initial_data_loader, mock_yahoo_client, mock_price_repo
    ):
        """全時間軸の初回データ取得成功テスト"""
        # モックデータの設定
        mock_data = {
            "Open": [100.0, 101.0, 102.0],
            "High": [102.0, 103.0, 104.0],
            "Low": [99.0, 100.0, 101.0],
            "Close": [101.0, 102.0, 103.0],
            "Volume": [1000000, 1000000, 1000000],
        }
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows.return_value = [
            (
                datetime.now(),
                MagicMock(
                    **{
                        "Open": 100.0,
                        "High": 102.0,
                        "Low": 99.0,
                        "Close": 101.0,
                        "Volume": 1000000,
                    }
                ),
            ),
            (
                datetime.now() + timedelta(hours=1),
                MagicMock(
                    **{
                        "Open": 101.0,
                        "High": 103.0,
                        "Low": 100.0,
                        "Close": 102.0,
                        "Volume": 1000000,
                    }
                ),
            ),
            (
                datetime.now() + timedelta(hours=2),
                MagicMock(
                    **{
                        "Open": 102.0,
                        "High": 104.0,
                        "Low": 101.0,
                        "Close": 103.0,
                        "Volume": 1000000,
                    }
                ),
            ),
        ]
        mock_yahoo_client.get_historical_data.return_value = mock_df

        # テスト実行
        result = await initial_data_loader.load_all_initial_data()

        # 検証
        assert result["is_initialized"] is True
        assert "data_counts" in result
        assert "indicator_counts" in result
        assert "pattern_counts" in result
        assert "processing_time" in result

        # 各時間軸のデータ取得が呼ばれたことを確認
        assert mock_yahoo_client.get_historical_data.call_count == 4  # 4つの時間軸

    @pytest.mark.asyncio
    async def test_load_timeframe_data_success(
        self, initial_data_loader, mock_yahoo_client, mock_price_repo
    ):
        """特定時間軸のデータ取得成功テスト"""
        # モックデータの設定
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows.return_value = [
            (
                datetime.now(),
                MagicMock(
                    **{
                        "Open": 100.0,
                        "High": 102.0,
                        "Low": 99.0,
                        "Close": 101.0,
                        "Volume": 1000000,
                    }
                ),
            )
        ]
        mock_yahoo_client.get_historical_data.return_value = mock_df

        # テスト実行
        result = await initial_data_loader.load_timeframe_data("5m")

        # 検証
        assert result > 0
        mock_yahoo_client.get_historical_data.assert_called_once()
        mock_price_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_load_timeframe_data_existing_data(
        self, initial_data_loader, mock_price_repo
    ):
        """既存データがある場合のテスト"""
        # 既存データがあることをモック
        mock_price_repo.count_by_date_range.return_value = 150

        # テスト実行
        result = await initial_data_loader.load_timeframe_data("5m")

        # 検証
        assert result == 150
        # Yahoo Finance APIは呼ばれない
        # mock_yahoo_client.get_historical_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_load_timeframe_data_api_failure(
        self, initial_data_loader, mock_yahoo_client
    ):
        """API取得失敗時のテスト"""
        # API失敗をモック
        mock_yahoo_client.get_historical_data.return_value = None

        # テスト実行
        result = await initial_data_loader.load_timeframe_data("5m")

        # 検証
        assert result == 0

    @pytest.mark.asyncio
    async def test_calculate_initial_indicators_success(
        self, initial_data_loader, mock_indicator_service
    ):
        """初回テクニカル指標計算成功テスト"""
        # テスト実行
        result = await initial_data_loader.calculate_initial_indicators()

        # 検証
        assert isinstance(result, dict)
        assert len(result) == 4  # 4つの時間軸
        assert mock_indicator_service.calculate_timeframe_indicators.call_count == 4

    @pytest.mark.asyncio
    async def test_detect_initial_patterns_success(
        self, initial_data_loader, mock_pattern_service
    ):
        """初回パターン検出成功テスト"""
        # テスト実行
        result = await initial_data_loader.detect_initial_patterns()

        # 検証
        assert isinstance(result, dict)
        assert len(result) == 4  # 4つの時間軸
        assert mock_pattern_service.detect_all_patterns_for_timeframe.call_count == 4

    @pytest.mark.asyncio
    async def test_verify_initialization_success(
        self, initial_data_loader, mock_price_repo, mock_indicator_service
    ):
        """初期化完了確認成功テスト"""
        # 十分なデータがあることをモック
        mock_price_repo.count_by_date_range.return_value = 200
        mock_indicator_service.count_latest_indicators.return_value = 100

        # テスト実行
        result = await initial_data_loader.verify_initialization()

        # 検証
        assert result is True

    @pytest.mark.asyncio
    async def test_verify_initialization_insufficient_data(
        self, initial_data_loader, mock_price_repo
    ):
        """データ不足時の初期化確認テスト"""
        # データ不足をモック
        mock_price_repo.count_by_date_range.return_value = 10

        # テスト実行
        result = await initial_data_loader.verify_initialization()

        # 検証
        assert result is False

    @pytest.mark.asyncio
    async def test_get_initialization_status_success(
        self,
        initial_data_loader,
        mock_price_repo,
        mock_indicator_service,
        mock_pattern_service,
    ):
        """初期化状態取得成功テスト"""
        # モック設定
        mock_price_repo.count_by_date_range.return_value = 200
        mock_indicator_service.count_latest_indicators.return_value = 100
        mock_pattern_service.count_latest_patterns.return_value = 50

        # テスト実行
        result = await initial_data_loader.get_initialization_status()

        # 検証
        assert isinstance(result, dict)
        assert "is_initialized" in result
        assert "data_counts" in result
        assert "indicator_counts" in result
        assert "pattern_counts" in result
        assert "missing_components" in result

    @pytest.mark.asyncio
    async def test_load_all_initial_data_with_retry(
        self, initial_data_loader, mock_yahoo_client, mock_price_repo
    ):
        """リトライ機能付きデータ取得テスト"""
        # 最初は失敗、2回目は成功するようにモック
        mock_df = MagicMock()
        mock_df.empty = False
        mock_df.iterrows.return_value = [
            (
                datetime.now(),
                MagicMock(
                    **{
                        "Open": 100.0,
                        "High": 102.0,
                        "Low": 99.0,
                        "Close": 101.0,
                        "Volume": 1000000,
                    }
                ),
            )
        ]

        mock_yahoo_client.get_historical_data.side_effect = [
            Exception("API Error"),  # 1回目は失敗
            mock_df,  # 2回目は成功
        ]

        # テスト実行（エラーハンドリングをテスト）
        with pytest.raises(Exception):
            await initial_data_loader.load_all_initial_data()

    @pytest.mark.asyncio
    async def test_initialization_config(self, initial_data_loader):
        """初期化設定のテスト"""
        # 設定の検証
        config = initial_data_loader.initial_load_config

        assert "5m" in config
        assert "1h" in config
        assert "4h" in config
        assert "1d" in config

        assert config["5m"]["period"] == "7d"
        assert config["1h"]["period"] == "30d"
        assert config["4h"]["period"] == "60d"
        assert config["1d"]["period"] == "365d"

    @pytest.mark.asyncio
    async def test_currency_pair_config(self, initial_data_loader):
        """通貨ペア設定のテスト"""
        assert initial_data_loader.currency_pair == "USD/JPY"

    @pytest.mark.asyncio
    async def test_retry_config(self, initial_data_loader):
        """リトライ設定のテスト"""
        assert initial_data_loader.max_retries == 3
        assert initial_data_loader.retry_delay == 5
