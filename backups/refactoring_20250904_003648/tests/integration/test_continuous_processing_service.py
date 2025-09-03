"""
ContinuousProcessingServiceの統合テスト

テスト内容:
- 5分足データの継続処理
- 時間軸集計の統合
- テクニカル指標計算の統合
- パターン検出の統合
- 通知処理の統合
- エラーハンドリング
- 統計情報の管理

TDDアプローチ:
- 実装前にテストケース作成
- 正常系・異常系・境界値テスト
- モックを使用した依存関係のテスト
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.services.continuous_processing_service import (
    ContinuousProcessingService,
)


class TestContinuousProcessingService:
    """ContinuousProcessingServiceの統合テスト"""

    @pytest.fixture
    def mock_session(self):
        """モックセッション"""
        session = AsyncMock(spec=AsyncSession)
        return session

    @pytest.fixture
    def mock_timeframe_aggregator(self):
        """モックTimeframeAggregatorService"""
        aggregator = MagicMock()
        aggregator.aggregate_1h_data = AsyncMock(return_value=[])
        aggregator.aggregate_4h_data = AsyncMock(return_value=[])
        aggregator.get_aggregation_status = AsyncMock(return_value={})
        aggregator.price_repo = MagicMock()
        aggregator.price_repo.find_by_timestamp = AsyncMock(return_value=None)
        aggregator.price_repo.save = AsyncMock()
        return aggregator

    @pytest.fixture
    def mock_technical_indicator_service(self):
        """モックMultiTimeframeTechnicalIndicatorService"""
        service = MagicMock()
        service.calculate_indicators_for_timeframe = AsyncMock(return_value=5)
        service.get_service_status = AsyncMock(return_value={})
        return service

    @pytest.fixture
    def mock_pattern_detection_service(self):
        """モックEfficientPatternDetectionService"""
        service = MagicMock()
        service.detect_patterns_for_timeframe = AsyncMock(return_value=2)
        service.get_unnotified_patterns = AsyncMock(return_value=[])
        service.mark_notification_sent = AsyncMock(return_value=True)
        service.get_service_status = AsyncMock(return_value={})
        return service

    @pytest.fixture
    def mock_notification_service(self):
        """モックNotificationManager"""
        service = MagicMock()
        service.send_pattern_notification = AsyncMock(return_value=True)
        return service

    @pytest.fixture
    def continuous_processing_service(
        self,
        mock_session,
        mock_timeframe_aggregator,
        mock_technical_indicator_service,
        mock_pattern_detection_service,
        mock_notification_service,
    ):
        """ContinuousProcessingServiceインスタンス"""
        service = ContinuousProcessingService(mock_session)
        # 依存サービスをモックに置き換え
        service.timeframe_aggregator = mock_timeframe_aggregator
        service.technical_indicator_service = mock_technical_indicator_service
        service.pattern_detection_service = mock_pattern_detection_service
        service.notification_service = mock_notification_service
        return service

    @pytest.fixture
    def sample_5m_price_data(self):
        """サンプル5分足価格データ"""
        return PriceDataModel(
            currency_pair="USD/JPY",
            timestamp=datetime.now(),
            open_price=100.0,
            high_price=102.0,
            low_price=99.0,
            close_price=101.0,
            volume=1000000,
            data_source="Test Data",
        )

    @pytest.mark.asyncio
    async def test_process_5m_data_success(
        self,
        continuous_processing_service,
        sample_5m_price_data,
        mock_timeframe_aggregator,
        mock_technical_indicator_service,
        mock_pattern_detection_service,
        mock_notification_service,
    ):
        """5分足データ処理成功テスト"""
        # モック設定
        mock_timeframe_aggregator.price_repo.save.return_value = sample_5m_price_data
        mock_timeframe_aggregator.aggregate_1h_data.return_value = [MagicMock()]
        mock_timeframe_aggregator.aggregate_4h_data.return_value = [MagicMock()]

        # テスト実行
        result = await continuous_processing_service.process_5m_data(
            sample_5m_price_data
        )

        # 検証
        assert result["status"] == "success"
        assert "processing_time" in result
        assert "aggregation" in result
        assert "indicators" in result
        assert "patterns" in result
        assert "notifications" in result

        # 各ステップが呼ばれたことを確認
        mock_timeframe_aggregator.price_repo.save.assert_called_once()
        mock_timeframe_aggregator.aggregate_1h_data.assert_called_once()
        mock_timeframe_aggregator.aggregate_4h_data.assert_called_once()
        mock_technical_indicator_service.calculate_indicators_for_timeframe.assert_called()
        mock_pattern_detection_service.detect_patterns_for_timeframe.assert_called()

    @pytest.mark.asyncio
    async def test_process_5m_data_duplicate_prevention(
        self,
        continuous_processing_service,
        sample_5m_price_data,
        mock_timeframe_aggregator,
    ):
        """重複データ防止テスト"""
        # 既存データがあることをモック
        mock_timeframe_aggregator.price_repo.find_by_timestamp.return_value = (
            sample_5m_price_data
        )

        # テスト実行
        result = await continuous_processing_service.process_5m_data(
            sample_5m_price_data
        )

        # 検証
        assert result["status"] == "success"
        # 保存は呼ばれない（重複のため）
        mock_timeframe_aggregator.price_repo.save.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_5m_data_error_handling(
        self,
        continuous_processing_service,
        sample_5m_price_data,
        mock_timeframe_aggregator,
    ):
        """エラーハンドリングテスト"""
        # エラーを発生させるモック設定
        mock_timeframe_aggregator.price_repo.save.side_effect = Exception(
            "Database error"
        )

        # テスト実行
        result = await continuous_processing_service.process_5m_data(
            sample_5m_price_data
        )

        # 検証
        assert result["status"] == "failed"
        assert "error" in result
        assert "Database error" in result["error"]

    @pytest.mark.asyncio
    async def test_aggregate_timeframes_success(
        self, continuous_processing_service, mock_timeframe_aggregator
    ):
        """時間軸集計成功テスト"""
        # モック設定
        mock_timeframe_aggregator.aggregate_1h_data.return_value = [
            MagicMock(),
            MagicMock(),
        ]
        mock_timeframe_aggregator.aggregate_4h_data.return_value = [MagicMock()]

        # テスト実行
        result = await continuous_processing_service.aggregate_timeframes()

        # 検証
        assert result["1h"] == 2
        assert result["4h"] == 1
        mock_timeframe_aggregator.aggregate_1h_data.assert_called_once()
        mock_timeframe_aggregator.aggregate_4h_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_aggregate_timeframes_error(
        self, continuous_processing_service, mock_timeframe_aggregator
    ):
        """時間軸集計エラーテスト"""
        # エラーを発生させるモック設定
        mock_timeframe_aggregator.aggregate_1h_data.side_effect = Exception(
            "Aggregation error"
        )

        # テスト実行
        result = await continuous_processing_service.aggregate_timeframes()

        # 検証
        assert "error" in result
        assert "Aggregation error" in result["error"]

    @pytest.mark.asyncio
    async def test_calculate_all_indicators_success(
        self, continuous_processing_service, mock_technical_indicator_service
    ):
        """テクニカル指標計算成功テスト"""
        # テスト実行
        result = await continuous_processing_service.calculate_all_indicators()

        # 検証
        assert result["5m"] == 5
        assert result["1h"] == 5
        assert result["4h"] == 5
        assert (
            mock_technical_indicator_service.calculate_indicators_for_timeframe.call_count
            == 3
        )

    @pytest.mark.asyncio
    async def test_calculate_all_indicators_error(
        self, continuous_processing_service, mock_technical_indicator_service
    ):
        """テクニカル指標計算エラーテスト"""
        # エラーを発生させるモック設定
        mock_technical_indicator_service.calculate_indicators_for_timeframe.side_effect = Exception(
            "Calculation error"
        )

        # テスト実行
        result = await continuous_processing_service.calculate_all_indicators()

        # 検証
        assert "error" in result
        assert "Calculation error" in result["error"]

    @pytest.mark.asyncio
    async def test_detect_patterns_success(
        self, continuous_processing_service, mock_pattern_detection_service
    ):
        """パターン検出成功テスト"""
        # テスト実行
        result = await continuous_processing_service.detect_patterns()

        # 検証
        assert result["5m"] == 2
        assert result["1h"] == 2
        assert result["4h"] == 2
        assert (
            mock_pattern_detection_service.detect_patterns_for_timeframe.call_count == 3
        )

    @pytest.mark.asyncio
    async def test_detect_patterns_error(
        self, continuous_processing_service, mock_pattern_detection_service
    ):
        """パターン検出エラーテスト"""
        # エラーを発生させるモック設定
        mock_pattern_detection_service.detect_patterns_for_timeframe.side_effect = (
            Exception("Detection error")
        )

        # テスト実行
        result = await continuous_processing_service.detect_patterns()

        # 検証
        assert "error" in result
        assert "Detection error" in result["error"]

    @pytest.mark.asyncio
    async def test_process_notifications_success(
        self,
        continuous_processing_service,
        mock_pattern_detection_service,
        mock_notification_service,
    ):
        """通知処理成功テスト"""
        # モック設定
        mock_pattern = MagicMock()
        mock_pattern.id = 1
        mock_pattern_detection_service.get_unnotified_patterns.return_value = [
            mock_pattern
        ]

        # テスト実行
        result = await continuous_processing_service.process_notifications()

        # 検証
        assert result["sent"] == 1
        assert result["total"] == 1
        mock_notification_service.send_pattern_notification.assert_called_once_with(
            mock_pattern
        )
        mock_pattern_detection_service.mark_notification_sent.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_process_notifications_no_patterns(
        self, continuous_processing_service, mock_pattern_detection_service
    ):
        """通知処理（パターンなし）テスト"""
        # モック設定
        mock_pattern_detection_service.get_unnotified_patterns.return_value = []

        # テスト実行
        result = await continuous_processing_service.process_notifications()

        # 検証
        assert result["sent"] == 0
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_process_notifications_error(
        self, continuous_processing_service, mock_pattern_detection_service
    ):
        """通知処理エラーテスト"""
        # エラーを発生させるモック設定
        mock_pattern_detection_service.get_unnotified_patterns.side_effect = Exception(
            "Notification error"
        )

        # テスト実行
        result = await continuous_processing_service.process_notifications()

        # 検証
        assert "error" in result
        assert "Notification error" in result["error"]

    @pytest.mark.asyncio
    async def test_get_processing_stats(self, continuous_processing_service):
        """処理統計取得テスト"""
        # テスト実行
        result = await continuous_processing_service.get_processing_stats()

        # 検証
        assert "total_cycles" in result
        assert "successful_cycles" in result
        assert "failed_cycles" in result
        assert "success_rate" in result
        assert "currency_pair" in result
        assert "timeframes" in result
        assert result["currency_pair"] == "USD/JPY"
        assert result["timeframes"] == ["5m", "1h", "4h"]

    @pytest.mark.asyncio
    async def test_reset_stats(self, continuous_processing_service):
        """統計リセットテスト"""
        # 初期状態を確認
        initial_stats = await continuous_processing_service.get_processing_stats()
        assert initial_stats["total_cycles"] == 0

        # 統計をリセット
        await continuous_processing_service.reset_stats()

        # リセット後の状態を確認
        reset_stats = await continuous_processing_service.get_processing_stats()
        assert reset_stats["total_cycles"] == 0
        assert reset_stats["successful_cycles"] == 0
        assert reset_stats["failed_cycles"] == 0

    @pytest.mark.asyncio
    async def test_health_check_success(
        self,
        continuous_processing_service,
        mock_timeframe_aggregator,
        mock_technical_indicator_service,
        mock_pattern_detection_service,
    ):
        """健全性チェック成功テスト"""
        # テスト実行
        result = await continuous_processing_service.health_check()

        # 検証
        assert result["service"] == "ContinuousProcessingService"
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "dependencies" in result
        assert result["dependencies"]["timeframe_aggregator"] == "healthy"
        assert result["dependencies"]["technical_indicator_service"] == "healthy"
        assert result["dependencies"]["pattern_detection_service"] == "healthy"

    @pytest.mark.asyncio
    async def test_health_check_degraded(
        self, continuous_processing_service, mock_timeframe_aggregator
    ):
        """健全性チェック（一部障害）テスト"""
        # エラーを発生させるモック設定
        mock_timeframe_aggregator.get_aggregation_status.side_effect = Exception(
            "Service error"
        )

        # テスト実行
        result = await continuous_processing_service.health_check()

        # 検証
        assert result["status"] == "degraded"
        assert "issues" in result
        assert (
            result["dependencies"]["timeframe_aggregator"] == "unhealthy: Service error"
        )

    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, continuous_processing_service):
        """健全性チェック（完全障害）テスト"""
        # エラーを発生させるモック設定
        continuous_processing_service.timeframe_aggregator = None

        # テスト実行
        result = await continuous_processing_service.health_check()

        # 検証
        assert result["status"] == "degraded"  # 一部の依存関係が障害の場合はdegraded
        assert "issues" in result

    @pytest.mark.asyncio
    async def test_configuration(self, continuous_processing_service):
        """設定のテスト"""
        # 設定の検証
        assert continuous_processing_service.currency_pair == "USD/JPY"
        assert continuous_processing_service.timeframes == ["5m", "1h", "4h"]
        assert continuous_processing_service.retry_attempts == 3
        assert continuous_processing_service.retry_delay == 30

    @pytest.mark.asyncio
    async def test_processing_stats_increment(
        self, continuous_processing_service, sample_5m_price_data
    ):
        """処理統計の増加テスト"""
        # 初期状態を確認
        initial_stats = await continuous_processing_service.get_processing_stats()
        initial_total = initial_stats["total_cycles"]

        # 処理を実行
        await continuous_processing_service.process_5m_data(sample_5m_price_data)

        # 統計が増加したことを確認
        updated_stats = await continuous_processing_service.get_processing_stats()
        assert updated_stats["total_cycles"] == initial_total + 1
        assert updated_stats["successful_cycles"] == 1
        assert updated_stats["failed_cycles"] == 0
