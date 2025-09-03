"""
経済イベントエンティティの単体テスト
"""

import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import Mock

from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.entities.economic_event.economic_event_validator import EconomicEventValidator
from src.domain.entities.economic_event.economic_event_factory import EconomicEventFactory


class TestEconomicEvent:
    """EconomicEventエンティティのテスト"""
    
    def test_economic_event_creation(self):
        """経済イベントの作成テスト"""
        # Given
        event_id = "test_event_001"
        date_utc = datetime(2023, 12, 1, 9, 0, 0)
        time_utc = time(9, 0)
        country = "japan"
        zone = "Asia/Tokyo"
        event_name = "Consumer Price Index (CPI)"
        importance = Importance.HIGH
        actual_value = Decimal("2.5")
        forecast_value = Decimal("2.3")
        previous_value = Decimal("2.1")
        currency = "JPY"
        unit = "YoY %"
        category = "inflation"
        
        # When
        event = EconomicEvent(
            event_id=event_id,
            date_utc=date_utc,
            time_utc=time_utc,
            country=country,
            zone=zone,
            event_name=event_name,
            importance=importance,
            actual_value=actual_value,
            forecast_value=forecast_value,
            previous_value=previous_value,
            currency=currency,
            unit=unit,
            category=category
        )
        
        # Then
        assert event.event_id == event_id
        assert event.date_utc == date_utc
        assert event.time_utc == time_utc
        assert event.country == country
        assert event.zone == zone
        assert event.event_name == event_name
        assert event.importance == importance
        assert event.actual_value == actual_value
        assert event.forecast_value == forecast_value
        assert event.previous_value == previous_value
        assert event.currency == currency
        assert event.unit == unit
        assert event.category == category
    
    def test_economic_event_with_optional_fields(self):
        """オプションフィールド付きの経済イベント作成テスト"""
        # Given
        event_id = "test_event_002"
        date_utc = datetime(2023, 12, 1, 9, 0, 0)
        country = "united states"
        event_name = "Non-Farm Payrolls"
        importance = Importance.MEDIUM
        
        # When
        event = EconomicEvent(
            event_id=event_id,
            date_utc=date_utc,
            country=country,
            event_name=event_name,
            importance=importance
        )
        
        # Then
        assert event.event_id == event_id
        assert event.date_utc == date_utc
        assert event.country == country
        assert event.event_name == event_name
        assert event.importance == importance
        assert event.time_utc is None
        assert event.zone is None
        assert event.actual_value is None
        assert event.forecast_value is None
        assert event.previous_value is None
        assert event.currency is None
        assert event.unit is None
        assert event.category is None
    
    def test_importance_enum_values(self):
        """重要度の列挙値テスト"""
        # Then
        assert Importance.LOW.value == "low"
        assert Importance.MEDIUM.value == "medium"
        assert Importance.HIGH.value == "high"
    
    def test_economic_event_equality(self):
        """経済イベントの等価性テスト"""
        # Given
        event1 = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        event2 = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        event3 = EconomicEvent(
            event_id="test_002",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        # Then
        assert event1 == event2
        assert event1 != event3
        assert hash(event1) == hash(event2)
        assert hash(event1) != hash(event3)
    
    def test_economic_event_string_representation(self):
        """経済イベントの文字列表現テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="Consumer Price Index (CPI)",
            importance=Importance.HIGH
        )
        
        # When
        string_repr = str(event)
        
        # Then
        assert "test_001" in string_repr
        assert "japan" in string_repr
        assert "Consumer Price Index (CPI)" in string_repr
        assert "HIGH" in string_repr
    
    def test_economic_event_to_dict(self):
        """経済イベントの辞書変換テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            time_utc=time(9, 0),
            country="japan",
            zone="Asia/Tokyo",
            event_name="CPI",
            importance=Importance.HIGH,
            actual_value=Decimal("2.5"),
            forecast_value=Decimal("2.3"),
            previous_value=Decimal("2.1"),
            currency="JPY",
            unit="YoY %",
            category="inflation"
        )
        
        # When
        event_dict = event.to_dict()
        
        # Then
        assert event_dict["event_id"] == "test_001"
        assert event_dict["country"] == "japan"
        assert event_dict["event_name"] == "CPI"
        assert event_dict["importance"] == "high"
        assert event_dict["actual_value"] == "2.5"
        assert event_dict["forecast_value"] == "2.3"
        assert event_dict["previous_value"] == "2.1"
        assert event_dict["currency"] == "JPY"
        assert event_dict["unit"] == "YoY %"
        assert event_dict["category"] == "inflation"
    
    def test_economic_event_from_dict(self):
        """辞書からの経済イベント作成テスト"""
        # Given
        event_dict = {
            "event_id": "test_001",
            "date_utc": "2023-12-01T09:00:00",
            "time_utc": "09:00:00",
            "country": "japan",
            "zone": "Asia/Tokyo",
            "event_name": "CPI",
            "importance": "high",
            "actual_value": "2.5",
            "forecast_value": "2.3",
            "previous_value": "2.1",
            "currency": "JPY",
            "unit": "YoY %",
            "category": "inflation"
        }
        
        # When
        event = EconomicEvent.from_dict(event_dict)
        
        # Then
        assert event.event_id == "test_001"
        assert event.country == "japan"
        assert event.event_name == "CPI"
        assert event.importance == Importance.HIGH
        assert event.actual_value == Decimal("2.5")
        assert event.forecast_value == Decimal("2.3")
        assert event.previous_value == Decimal("2.1")
        assert event.currency == "JPY"
        assert event.unit == "YoY %"
        assert event.category == "inflation"
    
    def test_economic_event_is_high_importance(self):
        """高重要度判定テスト"""
        # Given
        high_importance_event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        medium_importance_event = EconomicEvent(
            event_id="test_002",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="GDP",
            importance=Importance.MEDIUM
        )
        
        # Then
        assert high_importance_event.is_high_importance() is True
        assert medium_importance_event.is_high_importance() is False
    
    def test_economic_event_has_actual_value(self):
        """実際値の有無判定テスト"""
        # Given
        event_with_actual = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH,
            actual_value=Decimal("2.5")
        )
        
        event_without_actual = EconomicEvent(
            event_id="test_002",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="GDP",
            importance=Importance.HIGH
        )
        
        # Then
        assert event_with_actual.has_actual_value() is True
        assert event_without_actual.has_actual_value() is False
    
    def test_economic_event_has_forecast_value(self):
        """予測値の有無判定テスト"""
        # Given
        event_with_forecast = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH,
            forecast_value=Decimal("2.3")
        )
        
        event_without_forecast = EconomicEvent(
            event_id="test_002",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="GDP",
            importance=Importance.HIGH
        )
        
        # Then
        assert event_with_forecast.has_forecast_value() is True
        assert event_without_forecast.has_forecast_value() is False
    
    def test_economic_event_calculate_surprise(self):
        """サプライズ計算テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH,
            actual_value=Decimal("2.5"),
            forecast_value=Decimal("2.3")
        )
        
        # When
        surprise = event.calculate_surprise()
        
        # Then
        assert surprise == Decimal("0.087")  # (2.5 - 2.3) / 2.3 * 100
    
    def test_economic_event_calculate_surprise_no_forecast(self):
        """予測値なしでのサプライズ計算テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH,
            actual_value=Decimal("2.5")
        )
        
        # When
        surprise = event.calculate_surprise()
        
        # Then
        assert surprise is None
    
    def test_economic_event_calculate_surprise_no_actual(self):
        """実際値なしでのサプライズ計算テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH,
            forecast_value=Decimal("2.3")
        )
        
        # When
        surprise = event.calculate_surprise()
        
        # Then
        assert surprise is None


class TestEconomicEventValidator:
    """EconomicEventValidatorのテスト"""
    
    def setup_method(self):
        """テスト前のセットアップ"""
        self.validator = EconomicEventValidator()
    
    def test_valid_economic_event(self):
        """有効な経済イベントの検証テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        # When
        is_valid = self.validator.validate(event)
        
        # Then
        assert is_valid is True
        assert len(self.validator.errors) == 0
    
    def test_invalid_event_id(self):
        """無効なイベントIDの検証テスト"""
        # Given
        event = EconomicEvent(
            event_id="",  # 空のID
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        # When
        is_valid = self.validator.validate(event)
        
        # Then
        assert is_valid is False
        assert len(self.validator.errors) > 0
        assert any("event_id" in error for error in self.validator.errors)
    
    def test_invalid_country(self):
        """無効な国の検証テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="",  # 空の国名
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        # When
        is_valid = self.validator.validate(event)
        
        # Then
        assert is_valid is False
        assert len(self.validator.errors) > 0
        assert any("country" in error for error in self.validator.errors)
    
    def test_invalid_event_name(self):
        """無効なイベント名の検証テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="",  # 空のイベント名
            importance=Importance.HIGH
        )
        
        # When
        is_valid = self.validator.validate(event)
        
        # Then
        assert is_valid is False
        assert len(self.validator.errors) > 0
        assert any("event_name" in error for error in self.validator.errors)
    
    def test_invalid_date_utc(self):
        """無効な日時の検証テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=None,  # Noneの日時
            country="japan",
            event_name="CPI",
            importance=Importance.HIGH
        )
        
        # When
        is_valid = self.validator.validate(event)
        
        # Then
        assert is_valid is False
        assert len(self.validator.errors) > 0
        assert any("date_utc" in error for error in self.validator.errors)
    
    def test_invalid_importance(self):
        """無効な重要度の検証テスト"""
        # Given
        event = EconomicEvent(
            event_id="test_001",
            date_utc=datetime(2023, 12, 1, 9, 0, 0),
            country="japan",
            event_name="CPI",
            importance=None  # Noneの重要度
        )
        
        # When
        is_valid = self.validator.validate(event)
        
        # Then
        assert is_valid is False
        assert len(self.validator.errors) > 0
        assert any("importance" in error for error in self.validator.errors)


class TestEconomicEventFactory:
    """EconomicEventFactoryのテスト"""
    
    def setup_method(self):
        """テスト前のセットアップ"""
        self.factory = EconomicEventFactory()
    
    def test_create_economic_event(self):
        """経済イベントの作成テスト"""
        # Given
        event_data = {
            "event_id": "test_001",
            "date_utc": datetime(2023, 12, 1, 9, 0, 0),
            "country": "japan",
            "event_name": "CPI",
            "importance": "high"
        }
        
        # When
        event = self.factory.create_economic_event(event_data)
        
        # Then
        assert event.event_id == "test_001"
        assert event.country == "japan"
        assert event.event_name == "CPI"
        assert event.importance == Importance.HIGH
    
    def test_create_economic_event_from_dict(self):
        """辞書からの経済イベント作成テスト"""
        # Given
        event_dict = {
            "event_id": "test_001",
            "date_utc": "2023-12-01T09:00:00",
            "country": "japan",
            "event_name": "CPI",
            "importance": "high",
            "actual_value": "2.5",
            "forecast_value": "2.3"
        }
        
        # When
        event = self.factory.create_economic_event_from_dict(event_dict)
        
        # Then
        assert event.event_id == "test_001"
        assert event.country == "japan"
        assert event.event_name == "CPI"
        assert event.importance == Importance.HIGH
        assert event.actual_value == Decimal("2.5")
        assert event.forecast_value == Decimal("2.3")
    
    def test_create_economic_event_with_defaults(self):
        """デフォルト値付きの経済イベント作成テスト"""
        # Given
        event_data = {
            "event_id": "test_001",
            "date_utc": datetime(2023, 12, 1, 9, 0, 0),
            "country": "japan",
            "event_name": "CPI"
        }
        
        # When
        event = self.factory.create_economic_event_with_defaults(event_data)
        
        # Then
        assert event.event_id == "test_001"
        assert event.country == "japan"
        assert event.event_name == "CPI"
        assert event.importance == Importance.MEDIUM  # デフォルト値
        assert event.zone is None
        assert event.time_utc is None
