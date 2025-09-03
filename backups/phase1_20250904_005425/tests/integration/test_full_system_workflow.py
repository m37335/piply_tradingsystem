"""
システム全体のワークフローテスト
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, AsyncMock

from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.entities.ai_report import AIReport, ReportType
from src.domain.entities.ai_report.usd_jpy_prediction import (
    USDJPYPrediction,
    PredictionDirection,
    PredictionStrength
)
from src.application.use_cases.fetch import FetchEconomicCalendarUseCase
from src.application.use_cases.analysis import DetectChangesUseCase
from src.application.use_cases.notification import SendNotificationsUseCase
from src.application.use_cases.ai_report import GenerateAIReportUseCase


class TestFullSystemWorkflow:
    """システム全体のワークフローテスト"""
    
    @pytest.fixture
    def mock_investpy_service(self):
        """InvestpyServiceのモック"""
        mock_service = Mock()
        mock_service.fetch_economic_calendar = AsyncMock()
        mock_service.fetch_today_events = AsyncMock()
        mock_service.fetch_weekly_events = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def mock_notification_service(self):
        """NotificationServiceのモック"""
        mock_service = Mock()
        mock_service.send_event_notification = AsyncMock(return_value=True)
        mock_service.send_forecast_change_notification = AsyncMock(return_value=True)
        mock_service.send_actual_announcement_notification = AsyncMock(return_value=True)
        return mock_service
    
    @pytest.fixture
    def mock_ai_analysis_service(self):
        """AIAnalysisServiceのモック"""
        mock_service = Mock()
        mock_service.generate_pre_event_report = AsyncMock()
        mock_service.generate_post_event_report = AsyncMock()
        mock_service.generate_forecast_change_report = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def mock_repository(self):
        """リポジトリのモック"""
        mock_repo = Mock()
        mock_repo.save = AsyncMock()
        mock_repo.find_by_date_range = AsyncMock(return_value=[])
        mock_repo.find_by_event_id = AsyncMock(return_value=None)
        return mock_repo
    
    @pytest.fixture
    def sample_economic_events(self):
        """サンプル経済イベント"""
        return [
            EconomicEvent(
                event_id="test_event_001",
                date_utc=datetime(2023, 12, 1, 9, 0, 0),
                country="japan",
                event_name="Consumer Price Index (CPI)",
                importance=Importance.HIGH,
                actual_value=Decimal("2.5"),
                forecast_value=Decimal("2.3"),
                previous_value=Decimal("2.1"),
                currency="JPY",
                unit="YoY %",
                category="inflation"
            ),
            EconomicEvent(
                event_id="test_event_002",
                date_utc=datetime(2023, 12, 1, 14, 0, 0),
                country="united states",
                event_name="Non-Farm Payrolls",
                importance=Importance.HIGH,
                actual_value=Decimal("180"),
                forecast_value=Decimal("175"),
                previous_value=Decimal("165"),
                currency="USD",
                unit="K",
                category="employment"
            )
        ]
    
    @pytest.fixture
    def sample_ai_report(self):
        """サンプルAIレポート"""
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Inflation data above expectations"],
            technical_reasons=["USD/JPY broke resistance level"]
        )
        
        return AIReport(
            event_id="test_event_001",
            report_type=ReportType.PRE_EVENT,
            report_content="This is a test AI report content",
            usd_jpy_prediction=prediction,
            confidence_score=Decimal("0.85"),
            generated_at=datetime(2023, 12, 1, 8, 30, 0)
        )
    
    @pytest.mark.asyncio
    async def test_complete_data_fetch_workflow(
        self,
        mock_investpy_service,
        mock_repository,
        sample_economic_events
    ):
        """完全なデータ取得ワークフローテスト"""
        # Given
        mock_investpy_service.fetch_economic_calendar.return_value = sample_economic_events
        
        use_case = FetchEconomicCalendarUseCase(
            investpy_service=mock_investpy_service,
            repository=mock_repository
        )
        
        # When
        result = await use_case.execute(
            from_date="01/12/2023",
            to_date="01/12/2023",
            fetch_type="daily"
        )
        
        # Then
        assert result["success"] is True
        assert result["records_fetched"] == 2
        assert result["records_new"] == 2
        assert result["records_updated"] == 0
        
        # リポジトリのsaveが呼ばれたことを確認
        assert mock_repository.save.call_count == 2
    
    @pytest.mark.asyncio
    async def test_complete_change_detection_workflow(
        self,
        mock_repository,
        sample_economic_events
    ):
        """完全な変更検出ワークフローテスト"""
        # Given
        # 古いデータ（予測値が異なる）
        old_events = [
            EconomicEvent(
                event_id="test_event_001",
                date_utc=datetime(2023, 12, 1, 9, 0, 0),
                country="japan",
                event_name="Consumer Price Index (CPI)",
                importance=Importance.HIGH,
                forecast_value=Decimal("2.1"),  # 古い予測値
                currency="JPY",
                unit="YoY %",
                category="inflation"
            )
        ]
        
        mock_repository.find_by_date_range.return_value = old_events
        
        use_case = DetectChangesUseCase(
            repository=mock_repository
        )
        
        # When
        result = await use_case.execute(
            new_events=sample_economic_events,
            change_types=["forecast_change", "new_event"]
        )
        
        # Then
        assert result["success"] is True
        assert len(result["changes"]) > 0
        
        # 予測値変更が検出されたことを確認
        forecast_changes = [c for c in result["changes"] if c["type"] == "forecast_change"]
        assert len(forecast_changes) > 0
    
    @pytest.mark.asyncio
    async def test_complete_notification_workflow(
        self,
        mock_notification_service,
        mock_repository,
        sample_economic_events
    ):
        """完全な通知ワークフローテスト"""
        # Given
        use_case = SendNotificationsUseCase(
            notification_service=mock_notification_service,
            notification_history_repository=mock_repository
        )
        
        # When
        result = await use_case.send_bulk_notifications(
            events=sample_economic_events,
            notification_type="new_event",
            message_template="🚨 重要経済指標: {country} - {event_name} ({date} {time})"
        )
        
        # Then
        assert result["success"] is True
        assert result["results"]["total_requests"] == 2
        assert result["results"]["successful"] == 2
        
        # 通知サービスが呼ばれたことを確認
        assert mock_notification_service.send_event_notification.call_count == 2
    
    @pytest.mark.asyncio
    async def test_complete_ai_report_generation_workflow(
        self,
        mock_ai_analysis_service,
        mock_repository,
        sample_economic_events,
        sample_ai_report
    ):
        """完全なAIレポート生成ワークフローテスト"""
        # Given
        mock_ai_analysis_service.generate_pre_event_report.return_value = sample_ai_report
        
        use_case = GenerateAIReportUseCase(
            ai_analysis_service=mock_ai_analysis_service,
            repository=mock_repository
        )
        
        # When
        result = await use_case.generate_pre_event_reports(
            events=sample_economic_events
        )
        
        # Then
        assert result["success"] is True
        assert result["reports_generated"] == 2
        assert result["reports_saved"] == 2
        
        # AI分析サービスが呼ばれたことを確認
        assert mock_ai_analysis_service.generate_pre_event_report.call_count == 2
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(
        self,
        mock_investpy_service,
        mock_notification_service,
        mock_ai_analysis_service,
        mock_repository,
        sample_economic_events,
        sample_ai_report
    ):
        """エンドツーエンドワークフローテスト"""
        # Given
        mock_investpy_service.fetch_economic_calendar.return_value = sample_economic_events
        mock_ai_analysis_service.generate_pre_event_report.return_value = sample_ai_report
        
        # 各ユースケースのインスタンス化
        fetch_use_case = FetchEconomicCalendarUseCase(
            investpy_service=mock_investpy_service,
            repository=mock_repository
        )
        
        change_detection_use_case = DetectChangesUseCase(
            repository=mock_repository
        )
        
        notification_use_case = SendNotificationsUseCase(
            notification_service=mock_notification_service,
            notification_history_repository=mock_repository
        )
        
        ai_report_use_case = GenerateAIReportUseCase(
            ai_analysis_service=mock_ai_analysis_service,
            repository=mock_repository
        )
        
        # When - 1. データ取得
        fetch_result = await fetch_use_case.execute(
            from_date="01/12/2023",
            to_date="01/12/2023",
            fetch_type="daily"
        )
        
        # When - 2. 変更検出
        change_result = await change_detection_use_case.execute(
            new_events=sample_economic_events,
            change_types=["forecast_change", "new_event"]
        )
        
        # When - 3. AIレポート生成
        ai_report_result = await ai_report_use_case.generate_pre_event_reports(
            events=sample_economic_events
        )
        
        # When - 4. 通知送信
        notification_result = await notification_use_case.send_bulk_notifications(
            events=sample_economic_events,
            notification_type="new_event",
            message_template="🚨 重要経済指標: {country} - {event_name} ({date} {time})"
        )
        
        # Then
        assert fetch_result["success"] is True
        assert change_result["success"] is True
        assert ai_report_result["success"] is True
        assert notification_result["success"] is True
        
        # 各ステップが正常に実行されたことを確認
        assert fetch_result["records_fetched"] == 2
        assert len(change_result["changes"]) >= 0
        assert ai_report_result["reports_generated"] == 2
        assert notification_result["results"]["successful"] == 2
    
    @pytest.mark.asyncio
    async def test_error_handling_in_workflow(
        self,
        mock_investpy_service,
        mock_repository
    ):
        """ワークフローでのエラーハンドリングテスト"""
        # Given
        mock_investpy_service.fetch_economic_calendar.side_effect = Exception("API Error")
        
        use_case = FetchEconomicCalendarUseCase(
            investpy_service=mock_investpy_service,
            repository=mock_repository
        )
        
        # When
        result = await use_case.execute(
            from_date="01/12/2023",
            to_date="01/12/2023",
            fetch_type="daily"
        )
        
        # Then
        assert result["success"] is False
        assert "error" in result
        assert "API Error" in result["error"]
    
    @pytest.mark.asyncio
    async def test_workflow_with_empty_data(
        self,
        mock_investpy_service,
        mock_repository
    ):
        """空データでのワークフローテスト"""
        # Given
        mock_investpy_service.fetch_economic_calendar.return_value = []
        
        use_case = FetchEconomicCalendarUseCase(
            investpy_service=mock_investpy_service,
            repository=mock_repository
        )
        
        # When
        result = await use_case.execute(
            from_date="01/12/2023",
            to_date="01/12/2023",
            fetch_type="daily"
        )
        
        # Then
        assert result["success"] is True
        assert result["records_fetched"] == 0
        assert result["records_new"] == 0
        assert result["records_updated"] == 0
    
    @pytest.mark.asyncio
    async def test_workflow_performance(
        self,
        mock_investpy_service,
        mock_notification_service,
        mock_ai_analysis_service,
        mock_repository,
        sample_economic_events,
        sample_ai_report
    ):
        """ワークフローのパフォーマンステスト"""
        # Given
        # 大量のデータをシミュレート
        large_event_list = sample_economic_events * 100  # 200イベント
        
        mock_investpy_service.fetch_economic_calendar.return_value = large_event_list
        mock_ai_analysis_service.generate_pre_event_report.return_value = sample_ai_report
        
        fetch_use_case = FetchEconomicCalendarUseCase(
            investpy_service=mock_investpy_service,
            repository=mock_repository
        )
        
        ai_report_use_case = GenerateAIReportUseCase(
            ai_analysis_service=mock_ai_analysis_service,
            repository=mock_repository
        )
        
        # When
        start_time = datetime.now()
        
        fetch_result = await fetch_use_case.execute(
            from_date="01/12/2023",
            to_date="01/12/2023",
            fetch_type="daily"
        )
        
        ai_report_result = await ai_report_use_case.generate_pre_event_reports(
            events=large_event_list
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Then
        assert fetch_result["success"] is True
        assert ai_report_result["success"] is True
        assert fetch_result["records_fetched"] == 200
        assert ai_report_result["reports_generated"] == 200
        
        # 実行時間が妥当な範囲内であることを確認（5秒以内）
        assert execution_time < 5.0
    
    @pytest.mark.asyncio
    async def test_workflow_data_consistency(
        self,
        mock_investpy_service,
        mock_repository,
        sample_economic_events
    ):
        """ワークフローのデータ整合性テスト"""
        # Given
        mock_investpy_service.fetch_economic_calendar.return_value = sample_economic_events
        
        use_case = FetchEconomicCalendarUseCase(
            investpy_service=mock_investpy_service,
            repository=mock_repository
        )
        
        # When
        result = await use_case.execute(
            from_date="01/12/2023",
            to_date="01/12/2023",
            fetch_type="daily"
        )
        
        # Then
        assert result["success"] is True
        
        # 保存されたデータの整合性を確認
        saved_events = []
        for call in mock_repository.save.call_args_list:
            saved_events.append(call[0][0])  # 最初の引数がイベント
        
        assert len(saved_events) == 2
        
        # イベントIDの確認
        event_ids = [event.event_id for event in saved_events]
        assert "test_event_001" in event_ids
        assert "test_event_002" in event_ids
        
        # データの内容確認
        for saved_event in saved_events:
            assert saved_event.country in ["japan", "united states"]
            assert saved_event.importance == Importance.HIGH
            assert saved_event.actual_value is not None
            assert saved_event.forecast_value is not None
