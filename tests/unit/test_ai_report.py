"""
AIレポートエンティティの単体テスト
"""

from datetime import datetime
from decimal import Decimal
from unittest.mock import Mock

from src.domain.entities.ai_report import AIReport, ReportType
from src.domain.entities.ai_report.usd_jpy_prediction import (
    USDJPYPrediction,
    PredictionDirection,
    PredictionStrength
)
from src.domain.entities.economic_event import EconomicEvent, Importance


class TestAIReport:
    """AIReportエンティティのテスト"""
    
    def test_ai_report_creation(self):
        """AIレポートの作成テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_event_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Inflation data above expectations"],
            technical_reasons=["USD/JPY broke resistance level"]
        )
        
        # When
        report = AIReport(
            event_id=event.event_id,
            report_type=ReportType.PRE_EVENT,
            report_content="This is a test AI report content",
            usd_jpy_prediction=prediction,
            confidence_score=Decimal("0.85"),
            generated_at=datetime(2023, 12, 1, 8, 30, 0)
        )
        
        # Then
        assert report.event_id == "test_event_001"
        assert report.report_type == ReportType.PRE_EVENT
        assert report.report_content == "This is a test AI report content"
        assert report.usd_jpy_prediction == prediction
        assert report.confidence_score == Decimal("0.85")
        assert report.generated_at == datetime(2023, 12, 1, 8, 30, 0)
    
    def test_ai_report_without_prediction(self):
        """予測なしのAIレポート作成テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_event_002",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="united states",
            event_name="GDP",
            importance=Importance.MEDIUM
        )
        
        # When
        report = AIReport(
            event_id=event.event_id,
            report_type=ReportType.POST_EVENT,
            report_content="Post-event analysis report",
            confidence_score=Decimal("0.70")
        )
        
        # Then
        assert report.event_id == "test_event_002"
        assert report.report_type == ReportType.POST_EVENT
        assert report.report_content == "Post-event analysis report"
        assert report.usd_jpy_prediction is None
        assert report.confidence_score == Decimal("0.70")
        assert report.generated_at is not None
    
    def test_report_type_enum_values(self):
        """レポートタイプの列挙値テスト"""
        # Then
        assert ReportType.PRE_EVENT.value == "pre_event"
        assert ReportType.POST_EVENT.value == "post_event"
        assert ReportType.FORECAST_CHANGE.value == "forecast_change"
    
    def test_ai_report_equality(self):
        """AIレポートの等価性テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_event_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        report1 = AIReport(
            event_id=event.event_id,
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            confidence_score=Decimal("0.85")
        )
        
        report2 = AIReport(
            event_id=event.event_id,
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            confidence_score=Decimal("0.85")
        )
        
        report3 = AIReport(
            event_id="different_event",
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            confidence_score=Decimal("0.85")
        )
        
        # Then
        assert report1 == report2
        assert report1 != report3
        assert hash(report1) == hash(report2)
        assert hash(report1) != hash(report3)
    
    def test_ai_report_string_representation(self):
        """AIレポートの文字列表現テスト"""
        # Given
        report = AIReport(
            event_id="test_event_001",
            report_type=ReportType.PRE_EVENT,
            report_content="Test AI report",
            confidence_score=Decimal("0.85")
        )
        
        # When
        string_repr = str(report)
        
        # Then
        assert "test_event_001" in string_repr
        assert "pre_event" in string_repr
        assert "0.85" in string_repr
    
    def test_ai_report_to_dict(self):
        """AIレポートの辞書変換テスト"""
        # Given
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Inflation data above expectations"],
            technical_reasons=["USD/JPY broke resistance level"]
        )
        
        report = AIReport(
            event_id="test_event_001",
            report_type=ReportType.PRE_EVENT,
            report_content="Test AI report content",
            usd_jpy_prediction=prediction,
            confidence_score=Decimal("0.85"),
            generated_at=datetime(2023, 12, 1, 8, 30, 0)
        )
        
        # When
        report_dict = report.to_dict()
        
        # Then
        assert report_dict["event_id"] == "test_event_001"
        assert report_dict["report_type"] == "pre_event"
        assert report_dict["report_content"] == "Test AI report content"
        assert report_dict["confidence_score"] == "0.85"
        assert "usd_jpy_prediction" in report_dict
        assert report_dict["usd_jpy_prediction"]["direction"] == "bullish"
        assert report_dict["usd_jpy_prediction"]["strength"] == "strong"
    
    def test_ai_report_from_dict(self):
        """辞書からのAIレポート作成テスト"""
        # Given
        report_dict = {
            "event_id": "test_event_001",
            "report_type": "pre_event",
            "report_content": "Test AI report content",
            "confidence_score": "0.85",
            "usd_jpy_prediction": {
                "direction": "bullish",
                "strength": "strong",
                "confidence_score": "0.85",
                "fundamental_reasons": ["Inflation data above expectations"],
                "technical_reasons": ["USD/JPY broke resistance level"]
            },
            "generated_at": "2023-12-01T08:30:00"
        }
        
        # When
        report = AIReport.from_dict(report_dict)
        
        # Then
        assert report.event_id == "test_event_001"
        assert report.report_type == ReportType.PRE_EVENT
        assert report.report_content == "Test AI report content"
        assert report.confidence_score == Decimal("0.85")
        assert report.usd_jpy_prediction is not None
        assert report.usd_jpy_prediction.direction == PredictionDirection.BULLISH
        assert report.usd_jpy_prediction.strength == PredictionStrength.STRONG
    
    def test_ai_report_is_high_confidence(self):
        """高信頼度判定テスト"""
        # Given
        high_confidence_report = AIReport(
            event_id="test_event_001",
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            confidence_score=Decimal("0.85")
        )
        
        low_confidence_report = AIReport(
            event_id="test_event_002",
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            confidence_score=Decimal("0.60")
        )
        
        # Then
        assert high_confidence_report.is_high_confidence() is True
        assert low_confidence_report.is_high_confidence() is False
    
    def test_ai_report_has_prediction(self):
        """予測の有無判定テスト"""
        # Given
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        report_with_prediction = AIReport(
            event_id="test_event_001",
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            usd_jpy_prediction=prediction,
            confidence_score=Decimal("0.85")
        )
        
        report_without_prediction = AIReport(
            event_id="test_event_002",
            report_type=ReportType.PRE_EVENT,
            report_content="Test report",
            confidence_score=Decimal("0.85")
        )
        
        # Then
        assert report_with_prediction.has_prediction() is True
        assert report_without_prediction.has_prediction() is False


class TestUSDJPYPrediction:
    """USDJPYPredictionエンティティのテスト"""
    
    def test_usd_jpy_prediction_creation(self):
        """USD/JPY予測の作成テスト"""
        # Given
        direction = PredictionDirection.BULLISH
        strength = PredictionStrength.STRONG
        confidence_score = Decimal("0.85")
        fundamental_reasons = ["Inflation data above expectations"]
        technical_reasons = ["USD/JPY broke resistance level"]
        
        # When
        prediction = USDJPYPrediction(
            direction=direction,
            strength=strength,
            confidence_score=confidence_score,
            fundamental_reasons=fundamental_reasons,
            technical_reasons=technical_reasons
        )
        
        # Then
        assert prediction.direction == direction
        assert prediction.strength == strength
        assert prediction.confidence_score == confidence_score
        assert prediction.fundamental_reasons == fundamental_reasons
        assert prediction.technical_reasons == technical_reasons
    
    def test_prediction_direction_enum_values(self):
        """予測方向の列挙値テスト"""
        # Then
        assert PredictionDirection.BULLISH.value == "bullish"
        assert PredictionDirection.BEARISH.value == "bearish"
        assert PredictionDirection.NEUTRAL.value == "neutral"
    
    def test_prediction_strength_enum_values(self):
        """予測強度の列挙値テスト"""
        # Then
        assert PredictionStrength.WEAK.value == "weak"
        assert PredictionStrength.MEDIUM.value == "medium"
        assert PredictionStrength.STRONG.value == "strong"
    
    def test_usd_jpy_prediction_equality(self):
        """USD/JPY予測の等価性テスト"""
        # Given
        prediction1 = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        prediction2 = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        prediction3 = USDJPYPrediction(
            direction=PredictionDirection.BEARISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        # Then
        assert prediction1 == prediction2
        assert prediction1 != prediction3
        assert hash(prediction1) == hash(prediction2)
        assert hash(prediction1) != hash(prediction3)
    
    def test_usd_jpy_prediction_string_representation(self):
        """USD/JPY予測の文字列表現テスト"""
        # Given
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        # When
        string_repr = str(prediction)
        
        # Then
        assert "bullish" in string_repr
        assert "strong" in string_repr
        assert "0.85" in string_repr
    
    def test_usd_jpy_prediction_to_dict(self):
        """USD/JPY予測の辞書変換テスト"""
        # Given
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Inflation data above expectations"],
            technical_reasons=["USD/JPY broke resistance level"]
        )
        
        # When
        prediction_dict = prediction.to_dict()
        
        # Then
        assert prediction_dict["direction"] == "bullish"
        assert prediction_dict["strength"] == "strong"
        assert prediction_dict["confidence_score"] == "0.85"
        assert prediction_dict["fundamental_reasons"] == ["Inflation data above expectations"]
        assert prediction_dict["technical_reasons"] == ["USD/JPY broke resistance level"]
    
    def test_usd_jpy_prediction_from_dict(self):
        """辞書からのUSD/JPY予測作成テスト"""
        # Given
        prediction_dict = {
            "direction": "bullish",
            "strength": "strong",
            "confidence_score": "0.85",
            "fundamental_reasons": ["Inflation data above expectations"],
            "technical_reasons": ["USD/JPY broke resistance level"]
        }
        
        # When
        prediction = USDJPYPrediction.from_dict(prediction_dict)
        
        # Then
        assert prediction.direction == PredictionDirection.BULLISH
        assert prediction.strength == PredictionStrength.STRONG
        assert prediction.confidence_score == Decimal("0.85")
        assert prediction.fundamental_reasons == ["Inflation data above expectations"]
        assert prediction.technical_reasons == ["USD/JPY broke resistance level"]
    
    def test_usd_jpy_prediction_is_bullish(self):
        """強気予測判定テスト"""
        # Given
        bullish_prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        bearish_prediction = USDJPYPrediction(
            direction=PredictionDirection.BEARISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        # Then
        assert bullish_prediction.is_bullish() is True
        assert bearish_prediction.is_bullish() is False
    
    def test_usd_jpy_prediction_is_bearish(self):
        """弱気予測判定テスト"""
        # Given
        bullish_prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        bearish_prediction = USDJPYPrediction(
            direction=PredictionDirection.BEARISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        # Then
        assert bullish_prediction.is_bearish() is False
        assert bearish_prediction.is_bearish() is True
    
    def test_usd_jpy_prediction_is_strong(self):
        """強度予測判定テスト"""
        # Given
        strong_prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        weak_prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.WEAK,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Test reason"],
            technical_reasons=["Test reason"]
        )
        
        # Then
        assert strong_prediction.is_strong() is True
        assert weak_prediction.is_strong() is False
    
    def test_usd_jpy_prediction_get_all_reasons(self):
        """全理由取得テスト"""
        # Given
        prediction = USDJPYPrediction(
            direction=PredictionDirection.BULLISH,
            strength=PredictionStrength.STRONG,
            confidence_score=Decimal("0.85"),
            fundamental_reasons=["Fundamental reason 1", "Fundamental reason 2"],
            technical_reasons=["Technical reason 1", "Technical reason 2"]
        )
        
        # When
        all_reasons = prediction.get_all_reasons()
        
        # Then
        assert len(all_reasons) == 4
        assert "Fundamental reason 1" in all_reasons
        assert "Fundamental reason 2" in all_reasons
        assert "Technical reason 1" in all_reasons
        assert "Technical reason 2" in all_reasons
