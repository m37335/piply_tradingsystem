"""
データベースモデルテスト

USD/JPY特化の5分おきデータ取得システム用のデータベースモデルテスト
"""

from datetime import datetime
from decimal import Decimal

from src.infrastructure.database.models.price_data_model import PriceDataModel
from src.infrastructure.database.models.technical_indicator_model import (
    TechnicalIndicatorModel,
)
from src.infrastructure.database.models.pattern_detection_model import (
    PatternDetectionModel,
)
from src.infrastructure.database.models.system_config_model import SystemConfigModel
from src.infrastructure.database.models.data_fetch_history_model import (
    DataFetchHistoryModel,
)


class TestPriceDataModel:
    """価格データモデルのテスト"""

    def test_create_price_data(self):
        """価格データの作成テスト"""
        timestamp = datetime.now()
        price_data = PriceDataModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            open_price=Decimal("150.00"),
            high_price=Decimal("150.50"),
            low_price=Decimal("149.80"),
            close_price=Decimal("150.20"),
            volume=1000,
        )

        assert price_data.currency_pair == "USD/JPY"
        assert price_data.timestamp == timestamp
        assert price_data.open_price == Decimal("150.00")
        assert price_data.high_price == Decimal("150.50")
        assert price_data.low_price == Decimal("149.80")
        assert price_data.close_price == Decimal("150.20")
        assert price_data.volume == 1000

    def test_validate_price_data(self):
        """価格データのバリデーションテスト"""
        timestamp = datetime.now()
        price_data = PriceDataModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            open_price=Decimal("150.00"),
            high_price=Decimal("150.50"),
            low_price=Decimal("149.80"),
            close_price=Decimal("150.20"),
            volume=1000,
        )

        assert price_data.validate() is True

    def test_invalid_price_data(self):
        """無効な価格データのテスト"""
        timestamp = datetime.now()
        price_data = PriceDataModel(
            currency_pair="",  # 空の通貨ペア
            timestamp=timestamp,
            open_price=Decimal("150.00"),
            high_price=Decimal("150.50"),
            low_price=Decimal("149.80"),
            close_price=Decimal("150.20"),
            volume=1000,
        )

        assert price_data.validate() is False


class TestTechnicalIndicatorModel:
    """テクニカル指標モデルのテスト"""

    def test_create_technical_indicator(self):
        """テクニカル指標の作成テスト"""
        timestamp = datetime.now()
        indicator = TechnicalIndicatorModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            indicator_type="RSI",
            timeframe="5m",
            value=Decimal("65.5"),
            parameters={"period": 14},
        )

        assert indicator.currency_pair == "USD/JPY"
        assert indicator.timestamp == timestamp
        assert indicator.indicator_type == "RSI"
        assert indicator.timeframe == "5m"
        assert indicator.value == Decimal("65.5")
        assert indicator.parameters == {"period": 14}

    def test_validate_technical_indicator(self):
        """テクニカル指標のバリデーションテスト"""
        timestamp = datetime.now()
        indicator = TechnicalIndicatorModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            indicator_type="RSI",
            timeframe="5m",
            value=Decimal("65.5"),
            parameters={"period": 14},
        )

        assert indicator.validate() is True

    def test_invalid_technical_indicator(self):
        """無効なテクニカル指標のテスト"""
        timestamp = datetime.now()
        indicator = TechnicalIndicatorModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            indicator_type="",  # 空の指標タイプ
            timeframe="5m",
            value=Decimal("65.5"),
            parameters={"period": 14},
        )

        assert indicator.validate() is False


class TestPatternDetectionModel:
    """パターン検出モデルのテスト"""

    def test_create_pattern_detection(self):
        """パターン検出の作成テスト"""
        timestamp = datetime.now()
        pattern = PatternDetectionModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            pattern_type="Pattern 1",
            pattern_name="ブレイクアウト検出",
            confidence_score=Decimal("75.5"),
            direction="BUY",
            detection_data={"breakout_level": 150.50},
            indicator_data={"rsi": 65.5},
        )

        assert pattern.currency_pair == "USD/JPY"
        assert pattern.timestamp == timestamp
        assert pattern.pattern_type == "Pattern 1"
        assert pattern.pattern_name == "ブレイクアウト検出"
        assert pattern.confidence_score == Decimal("75.5")
        assert pattern.direction == "BUY"
        assert pattern.detection_data == {"breakout_level": 150.50}
        assert pattern.indicator_data == {"rsi": 65.5}

    def test_validate_pattern_detection(self):
        """パターン検出のバリデーションテスト"""
        timestamp = datetime.now()
        pattern = PatternDetectionModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            pattern_type="Pattern 1",
            pattern_name="ブレイクアウト検出",
            confidence_score=Decimal("75.5"),
            direction="BUY",
        )

        assert pattern.validate() is True

    def test_invalid_pattern_detection(self):
        """無効なパターン検出のテスト"""
        timestamp = datetime.now()
        pattern = PatternDetectionModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            pattern_type="",  # 空のパターンタイプ
            pattern_name="ブレイクアウト検出",
            confidence_score=Decimal("75.5"),
            direction="BUY",
        )

        assert pattern.validate() is False

    def test_confidence_levels(self):
        """信頼度レベルのテスト"""
        timestamp = datetime.now()
        
        # 高信頼度
        high_confidence = PatternDetectionModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            pattern_type="Pattern 1",
            pattern_name="ブレイクアウト検出",
            confidence_score=Decimal("85.0"),
            direction="BUY",
        )
        assert high_confidence.is_high_confidence() is True
        assert high_confidence.is_medium_confidence() is False
        assert high_confidence.is_low_confidence() is False

        # 中信頼度
        medium_confidence = PatternDetectionModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            pattern_type="Pattern 1",
            pattern_name="ブレイクアウト検出",
            confidence_score=Decimal("65.0"),
            direction="BUY",
        )
        assert medium_confidence.is_high_confidence() is False
        assert medium_confidence.is_medium_confidence() is True
        assert medium_confidence.is_low_confidence() is False

        # 低信頼度
        low_confidence = PatternDetectionModel(
            currency_pair="USD/JPY",
            timestamp=timestamp,
            pattern_type="Pattern 1",
            pattern_name="ブレイクアウト検出",
            confidence_score=Decimal("45.0"),
            direction="BUY",
        )
        assert low_confidence.is_high_confidence() is False
        assert low_confidence.is_medium_confidence() is False
        assert low_confidence.is_low_confidence() is True


class TestSystemConfigModel:
    """システム設定モデルのテスト"""

    def test_create_system_config(self):
        """システム設定の作成テスト"""
        config = SystemConfigModel(
            key="test_key",
            value="test_value",
            value_type="str",
            category="test_category",
            description="Test configuration",
            is_active=True,
        )

        assert config.key == "test_key"
        assert config.value == "test_value"
        assert config.value_type == "str"
        assert config.category == "test_category"
        assert config.description == "Test configuration"
        assert config.is_active is True

    def test_validate_system_config(self):
        """システム設定のバリデーションテスト"""
        config = SystemConfigModel(
            key="test_key",
            value="test_value",
            value_type="str",
            category="test_category",
            description="Test configuration",
            is_active=True,
        )

        assert config.validate() is True

    def test_invalid_system_config(self):
        """無効なシステム設定のテスト"""
        config = SystemConfigModel(
            key="",  # 空のキー
            value="test_value",
            value_type="str",
            category="test_category",
            description="Test configuration",
            is_active=True,
        )

        assert config.validate() is False

    def test_get_value(self):
        """設定値の取得テスト"""
        # 文字列値
        str_config = SystemConfigModel(
            key="str_key",
            value="test_string",
            value_type="str",
            category="test",
        )
        assert str_config.get_value() == "test_string"

        # 数値値
        int_config = SystemConfigModel(
            key="int_key",
            value="123",
            value_type="int",
            category="test",
        )
        assert int_config.get_value() == 123

        # 浮動小数点値
        float_config = SystemConfigModel(
            key="float_key",
            value="123.45",
            value_type="float",
            category="test",
        )
        assert float_config.get_value() == 123.45

        # 真偽値
        bool_config = SystemConfigModel(
            key="bool_key",
            value="true",
            value_type="bool",
            category="test",
        )
        assert bool_config.get_value() is True

        # JSON値
        json_config = SystemConfigModel(
            key="json_key",
            value='{"key": "value"}',
            value_type="json",
            category="test",
        )
        assert json_config.get_value() == {"key": "value"}


class TestDataFetchHistoryModel:
    """データ取得履歴モデルのテスト"""

    def test_create_data_fetch_history(self):
        """データ取得履歴の作成テスト"""
        timestamp = datetime.now()
        history = DataFetchHistoryModel(
            currency_pair="USD/JPY",
            fetch_timestamp=timestamp,
            data_source="yahoo_finance",
            fetch_type="price_data",
            status="success",
            response_time=Decimal("1.5"),
            records_fetched=100,
            error_message=None,
        )

        assert history.currency_pair == "USD/JPY"
        assert history.fetch_timestamp == timestamp
        assert history.data_source == "yahoo_finance"
        assert history.fetch_type == "price_data"
        assert history.status == "success"
        assert history.response_time == Decimal("1.5")
        assert history.records_fetched == 100
        assert history.error_message is None

    def test_validate_data_fetch_history(self):
        """データ取得履歴のバリデーションテスト"""
        timestamp = datetime.now()
        history = DataFetchHistoryModel(
            currency_pair="USD/JPY",
            fetch_timestamp=timestamp,
            data_source="yahoo_finance",
            fetch_type="price_data",
            status="success",
            response_time=Decimal("1.5"),
            records_fetched=100,
        )

        assert history.validate() is True

    def test_invalid_data_fetch_history(self):
        """無効なデータ取得履歴のテスト"""
        timestamp = datetime.now()
        history = DataFetchHistoryModel(
            currency_pair="",  # 空の通貨ペア
            fetch_timestamp=timestamp,
            data_source="yahoo_finance",
            fetch_type="price_data",
            status="success",
            response_time=Decimal("1.5"),
            records_fetched=100,
        )

        assert history.validate() is False
