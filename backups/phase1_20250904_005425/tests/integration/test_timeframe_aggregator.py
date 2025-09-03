"""
TimeframeAggregatorServiceの統合テスト

テスト内容:
- 5分足から1時間足への集計
- 5分足から4時間足への集計
- 集計データのデータベース保存
- 重複データの防止
- 集計品質の監視

TDDアプローチ:
- 実装前にテストケース作成
- 正常系・異常系・境界値テスト
- モックを使用した依存関係のテスト
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
import pandas as pd

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.services.timeframe_aggregator_service import (
    TimeframeAggregatorService
)


class TestTimeframeAggregatorService:
    """TimeframeAggregatorServiceの統合テスト"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_price_repo(self):
        """モックPrice Repository"""
        repo = MagicMock()
        repo.find_by_date_range_and_timeframe = AsyncMock()
        repo.find_by_timestamp = AsyncMock(return_value=None)
        repo.save = AsyncMock()
        repo.find_latest = AsyncMock()
        repo.count_by_date_range = AsyncMock(return_value=100)
        return repo

    @pytest.fixture
    def mock_saved_price_data(self):
        """モック保存済み価格データ"""
        return PriceDataModel(
            currency_pair="USD/JPY",
            timestamp=datetime.now(),
            open_price=100.0,
            high_price=102.0,
            low_price=99.0,
            close_price=101.0,
            volume=1000000,
            data_source="Aggregated from 5m to 1h"
        )

    @pytest.fixture
    def timeframe_aggregator(self, mock_session, mock_price_repo):
        """TimeframeAggregatorServiceインスタンス"""
        service = TimeframeAggregatorService(mock_session)
        # 直接price_repoをモックに置き換え
        service.price_repo = mock_price_repo
        return service

    @pytest.fixture
    def sample_5m_data(self):
        """サンプル5分足データ"""
        data = []
        base_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        for i in range(12):  # 1時間分の5分足データ
            timestamp = base_time + timedelta(minutes=i * 5)
            price_data = PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=timestamp,
                open_price=100.0 + i * 0.1,
                high_price=100.0 + i * 0.1 + 0.05,
                low_price=100.0 + i * 0.1 - 0.05,
                close_price=100.0 + i * 0.1 + 0.02,
                volume=1000000 + i * 1000,
                data_source="Test Data"
            )
            data.append(price_data)
        
        return data

    @pytest.mark.asyncio
    async def test_aggregate_1h_data_success(
        self, timeframe_aggregator, mock_price_repo, sample_5m_data,
        mock_saved_price_data
    ):
        """1時間足集計成功テスト"""
        # モック設定
        mock_price_repo.find_by_date_range_and_timeframe.return_value = sample_5m_data
        mock_price_repo.save.return_value = mock_saved_price_data

        # テスト実行
        result = await timeframe_aggregator.aggregate_1h_data()

        # 検証
        assert len(result) > 0
        assert isinstance(result[0], PriceDataModel)
        assert result[0].data_source == "Aggregated from 5m to 1h"
        
        # リポジトリメソッドが呼ばれたことを確認
        mock_price_repo.find_by_date_range_and_timeframe.assert_called_once()
        mock_price_repo.save.assert_called()

    @pytest.mark.asyncio
    async def test_aggregate_1h_data_insufficient_data(
        self, timeframe_aggregator, mock_price_repo
    ):
        """データ不足時の1時間足集計テスト"""
        # データ不足をモック
        mock_price_repo.find_by_date_range_and_timeframe.return_value = []

        # テスト実行
        result = await timeframe_aggregator.aggregate_1h_data()

        # 検証
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_aggregate_4h_data_success(
        self, timeframe_aggregator, mock_price_repo, sample_5m_data,
        mock_saved_price_data
    ):
        """4時間足集計成功テスト"""
        # 4時間分のデータを準備
        extended_data = sample_5m_data * 4  # 4時間分
        mock_price_repo.find_by_date_range_and_timeframe.return_value = extended_data
        
        # 4時間足用のモックデータを作成
        mock_4h_data = PriceDataModel(
            currency_pair="USD/JPY",
            timestamp=datetime.now(),
            open_price=100.0,
            high_price=102.0,
            low_price=99.0,
            close_price=101.0,
            volume=1000000,
            data_source="Aggregated from 5m to 4h"
        )
        mock_price_repo.save.return_value = mock_4h_data

        # テスト実行
        result = await timeframe_aggregator.aggregate_4h_data()

        # 検証
        assert len(result) > 0
        assert isinstance(result[0], PriceDataModel)
        assert result[0].data_source == "Aggregated from 5m to 4h"

    @pytest.mark.asyncio
    async def test_aggregate_4h_data_insufficient_data(
        self, timeframe_aggregator, mock_price_repo
    ):
        """データ不足時の4時間足集計テスト"""
        # データ不足をモック
        mock_price_repo.find_by_date_range_and_timeframe.return_value = []

        # テスト実行
        result = await timeframe_aggregator.aggregate_4h_data()

        # 検証
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_aggregate_all_timeframes_success(
        self, timeframe_aggregator, mock_price_repo, sample_5m_data
    ):
        """全時間軸集計成功テスト"""
        # モック設定
        mock_price_repo.find_by_date_range_and_timeframe.return_value = sample_5m_data

        # テスト実行
        result = await timeframe_aggregator.aggregate_all_timeframes()

        # 検証
        assert isinstance(result, dict)
        assert "1h" in result
        assert "4h" in result
        assert result["1h"] >= 0
        assert result["4h"] >= 0

    @pytest.mark.asyncio
    async def test_convert_to_dataframe_success(
        self, timeframe_aggregator, sample_5m_data
    ):
        """DataFrame変換成功テスト"""
        # テスト実行
        df = timeframe_aggregator._convert_to_dataframe(sample_5m_data)

        # 検証
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert len(df) == len(sample_5m_data)
        assert "open" in df.columns
        assert "high" in df.columns
        assert "low" in df.columns
        assert "close" in df.columns
        assert "volume" in df.columns

    @pytest.mark.asyncio
    async def test_convert_to_dataframe_empty_list(
        self, timeframe_aggregator
    ):
        """空リストのDataFrame変換テスト"""
        # テスト実行
        df = timeframe_aggregator._convert_to_dataframe([])

        # 検証
        assert isinstance(df, pd.DataFrame)
        assert df.empty

    @pytest.mark.asyncio
    async def test_aggregate_timeframe_data_1h(
        self, timeframe_aggregator, sample_5m_data
    ):
        """1時間足への時間軸集計テスト"""
        # DataFrameを作成
        df = timeframe_aggregator._convert_to_dataframe(sample_5m_data)

        # テスト実行
        result_df = timeframe_aggregator._aggregate_timeframe_data(df, "1H")

        # 検証
        assert isinstance(result_df, pd.DataFrame)
        assert not result_df.empty
        assert len(result_df) <= len(df)  # 集計後は件数が減る

    @pytest.mark.asyncio
    async def test_aggregate_timeframe_data_4h(
        self, timeframe_aggregator, sample_5m_data
    ):
        """4時間足への時間軸集計テスト"""
        # 4時間分のデータを準備
        extended_data = sample_5m_data * 4
        df = timeframe_aggregator._convert_to_dataframe(extended_data)

        # テスト実行
        result_df = timeframe_aggregator._aggregate_timeframe_data(df, "4H")

        # 検証
        assert isinstance(result_df, pd.DataFrame)
        assert not result_df.empty
        assert len(result_df) <= len(df)

    @pytest.mark.asyncio
    async def test_aggregate_timeframe_data_empty_dataframe(
        self, timeframe_aggregator
    ):
        """空DataFrameの時間軸集計テスト"""
        # 空のDataFrameを作成
        df = pd.DataFrame()

        # テスト実行
        result_df = timeframe_aggregator._aggregate_timeframe_data(df, "1H")

        # 検証
        assert isinstance(result_df, pd.DataFrame)
        assert result_df.empty

    @pytest.mark.asyncio
    async def test_save_aggregated_data_success(
        self, timeframe_aggregator, mock_price_repo, mock_saved_price_data
    ):
        """集計データ保存成功テスト"""
        # サンプルDataFrameを作成
        data = {
            "open": [100.0, 101.0],
            "high": [102.0, 103.0],
            "low": [99.0, 100.0],
            "close": [101.0, 102.0],
            "volume": [1000000, 1000000]
        }
        timestamps = [datetime.now(), datetime.now() + timedelta(hours=1)]
        df = pd.DataFrame(data, index=timestamps)

        # モック設定 - 2つの異なるデータを返すように設定
        mock_price_repo.save.side_effect = [
            mock_saved_price_data,
            PriceDataModel(
                currency_pair="USD/JPY",
                timestamp=datetime.now() + timedelta(hours=1),
                open_price=101.0,
                high_price=103.0,
                low_price=100.0,
                close_price=102.0,
                volume=1000000,
                data_source="Aggregated from 5m to 1h"
            )
        ]

        # テスト実行
        result = await timeframe_aggregator._save_aggregated_data(df, "1h")

        # 検証
        assert len(result) == 2
        assert isinstance(result[0], PriceDataModel)
        mock_price_repo.save.assert_called()

    @pytest.mark.asyncio
    async def test_save_aggregated_data_duplicate_prevention(
        self, timeframe_aggregator, mock_price_repo
    ):
        """重複データ防止テスト"""
        # サンプルDataFrameを作成
        data = {
            "open": [100.0],
            "high": [102.0],
            "low": [99.0],
            "close": [101.0],
            "volume": [1000000]
        }
        timestamps = [datetime.now()]
        df = pd.DataFrame(data, index=timestamps)

        # 既存データがあることをモック
        mock_price_repo.find_by_timestamp.return_value = MagicMock()

        # テスト実行
        result = await timeframe_aggregator._save_aggregated_data(df, "1h")

        # 検証
        assert len(result) == 0  # 重複のため保存されない
        mock_price_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_aggregation_status_success(
        self, timeframe_aggregator, mock_price_repo
    ):
        """集計状態取得成功テスト"""
        # モック設定
        mock_price_repo.find_latest.return_value = [
            MagicMock(
                timestamp=datetime.now(),
                data_source="Aggregated from 5m to 1h"
            )
        ]

        # テスト実行
        result = await timeframe_aggregator.get_aggregation_status()

        # 検証
        assert isinstance(result, dict)
        assert "last_aggregation" in result
        assert "total_aggregated" in result
        assert result["total_aggregated"] == 100

    @pytest.mark.asyncio
    async def test_configuration(self, timeframe_aggregator):
        """設定のテスト"""
        # 集計設定の検証
        assert "1h" in timeframe_aggregator.aggregation_rules
        assert "4h" in timeframe_aggregator.aggregation_rules
        
        assert timeframe_aggregator.aggregation_rules["1h"]["minutes"] == 60
        assert timeframe_aggregator.aggregation_rules["4h"]["minutes"] == 240
        
        # 品質設定の検証
        assert "min_data_points" in timeframe_aggregator.quality_thresholds
        assert "max_gap_minutes" in timeframe_aggregator.quality_thresholds
        
        assert timeframe_aggregator.quality_thresholds["min_data_points"]["1h"] == 12
        assert timeframe_aggregator.quality_thresholds["min_data_points"]["4h"] == 48

    @pytest.mark.asyncio
    async def test_currency_pair_config(self, timeframe_aggregator):
        """通貨ペア設定のテスト"""
        assert timeframe_aggregator.currency_pair == "USD/JPY"

    @pytest.mark.asyncio
    async def test_error_handling_dataframe_conversion(
        self, timeframe_aggregator
    ):
        """DataFrame変換エラーハンドリングテスト"""
        # 不正なデータでテスト
        invalid_data = [{"invalid": "data"}]

        # テスト実行
        df = timeframe_aggregator._convert_to_dataframe(invalid_data)

        # 検証
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.asyncio
    async def test_error_handling_aggregation(
        self, timeframe_aggregator, mock_price_repo
    ):
        """集計エラーハンドリングテスト"""
        # エラーを発生させるモック設定
        mock_price_repo.find_by_date_range_and_timeframe.side_effect = Exception("Database error")

        # テスト実行
        result = await timeframe_aggregator.aggregate_1h_data()

        # 検証
        assert len(result) == 0  # エラー時は空リストを返す
