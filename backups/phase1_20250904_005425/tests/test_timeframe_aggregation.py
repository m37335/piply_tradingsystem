#!/usr/bin/env python3
"""
時間足集計システムの単体テスト

責任:
- BaseAggregatorのテスト
- HourlyAggregatorのテスト
- FourHourAggregatorのテスト
- DailyAggregatorのテスト
"""

import asyncio

# プロジェクトルートをパスに追加
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytz

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.cron.base_aggregator import (
    AggregationError,
    BaseAggregator,
    InsufficientDataError,
)
from scripts.cron.daily_aggregator import DailyAggregator
from scripts.cron.four_hour_aggregator import FourHourAggregator
from scripts.cron.hourly_aggregator import HourlyAggregator
from src.infrastructure.database.models.price_data_model import PriceDataModel


class TestBaseAggregator:
    """BaseAggregatorのテスト"""

    @pytest.fixture
    def mock_price_repo(self):
        """モック価格データリポジトリ"""
        mock_repo = AsyncMock()
        return mock_repo

    @pytest.fixture
    def base_aggregator(self, mock_price_repo):
        """BaseAggregatorインスタンス"""
        with patch(
            "scripts.cron.base_aggregator.PriceDataRepositoryImpl"
        ) as mock_repo_class:
            mock_repo_class.return_value = mock_price_repo
            aggregator = BaseAggregator("1h", "test_source")
            return aggregator

    @pytest.mark.asyncio
    async def test_calculate_ohlcv(self, base_aggregator):
        """OHLCV計算のテスト"""
        # テストデータ作成
        test_data = [
            PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=datetime(
                    2025, 1, 1, 10, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
                ),
                open_price=100.0,
                high_price=105.0,
                low_price=99.0,
                close_price=102.0,
                volume=1000,
                data_source="test",
            ),
            PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=datetime(
                    2025, 1, 1, 10, 5, 0, tzinfo=pytz.timezone("Asia/Tokyo")
                ),
                open_price=102.0,
                high_price=107.0,
                low_price=101.0,
                close_price=104.0,
                volume=1500,
                data_source="test",
            ),
        ]

        # OHLCV計算実行
        result = await base_aggregator.calculate_ohlcv(test_data)

        # 検証
        assert result.open_price == 100.0  # 最初の始値
        assert result.high_price == 107.0  # 最高値
        assert result.low_price == 99.0  # 最低値
        assert result.close_price == 104.0  # 最後の終値
        assert result.volume == 2500  # 取引量合計
        assert result.timestamp == datetime(
            2025, 1, 1, 10, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
        )

    @pytest.mark.asyncio
    async def test_calculate_ohlcv_empty_data(self, base_aggregator):
        """空データでのOHLCV計算テスト"""
        with pytest.raises(InsufficientDataError):
            await base_aggregator.calculate_ohlcv([])

    @pytest.mark.asyncio
    async def test_check_duplicate(self, base_aggregator, mock_price_repo):
        """重複チェックのテスト"""
        test_timestamp = datetime(
            2025, 1, 1, 10, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
        )
        mock_price_repo.find_by_timestamp_and_source.return_value = None

        result = await base_aggregator.check_duplicate(test_timestamp)
        assert result is None

        # 既存データがある場合
        existing_data = PriceDataModel(
            currency_pair="USD/JPY",
            timestamp=test_timestamp,
            open_price=100.0,
            high_price=105.0,
            low_price=99.0,
            close_price=102.0,
            volume=1000,
            data_source="test",
        )
        mock_price_repo.find_by_timestamp_and_source.return_value = existing_data

        result = await base_aggregator.check_duplicate(test_timestamp)
        assert result == existing_data


class TestHourlyAggregator:
    """HourlyAggregatorのテスト"""

    @pytest.fixture
    def hourly_aggregator(self):
        """HourlyAggregatorインスタンス"""
        return HourlyAggregator()

    @pytest.mark.asyncio
    async def test_get_aggregation_period(self, hourly_aggregator):
        """1時間足集計期間計算のテスト"""
        with patch("scripts.cron.hourly_aggregator.datetime") as mock_datetime:
            # 現在時刻を2025年1月1日 10:30に設定
            mock_now = datetime(
                2025, 1, 1, 10, 30, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )
            mock_datetime.now.return_value = mock_now

            start_time, end_time = await hourly_aggregator.get_aggregation_period()

            # 前1時間の期間（09:00-09:55）が返されることを確認
            expected_start = datetime(
                2025, 1, 1, 9, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )
            expected_end = datetime(
                2025, 1, 1, 9, 55, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )

            assert start_time == expected_start
            assert end_time == expected_end


class TestFourHourAggregator:
    """FourHourAggregatorのテスト"""

    @pytest.fixture
    def four_hour_aggregator(self):
        """FourHourAggregatorインスタンス"""
        return FourHourAggregator()

    @pytest.mark.asyncio
    async def test_get_aggregation_period(self, four_hour_aggregator):
        """4時間足集計期間計算のテスト"""
        with patch("scripts.cron.four_hour_aggregator.datetime") as mock_datetime:
            # 現在時刻を2025年1月1日 10:30に設定
            mock_now = datetime(
                2025, 1, 1, 10, 30, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )
            mock_datetime.now.return_value = mock_now

            start_time, end_time = await four_hour_aggregator.get_aggregation_period()

            # 前4時間の期間（06:00-09:55）が返されることを確認
            expected_start = datetime(
                2025, 1, 1, 6, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )
            expected_end = datetime(
                2025, 1, 1, 9, 55, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )

            assert start_time == expected_start
            assert end_time == expected_end


class TestDailyAggregator:
    """DailyAggregatorのテスト"""

    @pytest.fixture
    def daily_aggregator(self):
        """DailyAggregatorインスタンス"""
        return DailyAggregator()

    @pytest.mark.asyncio
    async def test_get_aggregation_period(self, daily_aggregator):
        """日足集計期間計算のテスト"""
        with patch("scripts.cron.daily_aggregator.datetime") as mock_datetime:
            # 現在時刻を2025年1月2日 10:30に設定
            mock_now = datetime(
                2025, 1, 2, 10, 30, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )
            mock_datetime.now.return_value = mock_now

            start_time, end_time = await daily_aggregator.get_aggregation_period()

            # 前日の期間（2025年1月1日 00:00-23:55）が返されることを確認
            expected_start = datetime(
                2025, 1, 1, 0, 0, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )
            expected_end = datetime(
                2025, 1, 1, 23, 55, 0, tzinfo=pytz.timezone("Asia/Tokyo")
            )

            assert start_time == expected_start
            assert end_time == expected_end


if __name__ == "__main__":
    pytest.main([__file__])
