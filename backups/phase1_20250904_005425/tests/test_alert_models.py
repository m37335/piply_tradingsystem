"""
アラートシステムモデルテスト

プロトレーダー向け為替アラートシステムのモデルテスト
"""

from datetime import datetime, timedelta

import pytest

from src.infrastructure.database.models.alert_settings_model import AlertSettingsModel
from src.infrastructure.database.models.entry_signal_model import EntrySignalModel
from src.infrastructure.database.models.risk_alert_model import RiskAlertModel
from src.infrastructure.database.models.signal_performance_model import (
    SignalPerformanceModel,
)


class TestAlertSettingsModel:
    """アラート設定モデルテスト"""

    def test_create_rsi_entry_setting(self):
        """RSIエントリー設定作成テスト"""
        setting = AlertSettingsModel.create_rsi_entry_signal(
            timeframe="M5",
            threshold_value=30.0,
            risk_reward_min=2.0,
            confidence_min=70,
        )

        assert setting.alert_type == "entry_signal"
        assert setting.indicator_type == "RSI"
        assert setting.timeframe == "M5"
        assert setting.threshold_value == 30.0
        assert setting.condition_type == "below"
        assert setting.risk_reward_min == 2.0
        assert setting.confidence_min == 70
        assert setting.is_active is True
        assert setting.validate() is True

    def test_create_bollinger_bands_entry_setting(self):
        """ボリンジャーバンドエントリー設定作成テスト"""
        setting = AlertSettingsModel.create_bollinger_bands_entry_signal(
            timeframe="M15",
            risk_reward_min=2.5,
            confidence_min=75,
        )

        assert setting.alert_type == "entry_signal"
        assert setting.indicator_type == "BB"
        assert setting.timeframe == "M15"
        assert setting.condition_type == "cross"
        assert setting.risk_reward_min == 2.5
        assert setting.confidence_min == 75
        assert setting.validate() is True

    def test_create_volatility_risk_setting(self):
        """ボラティリティリスク設定作成テスト"""
        setting = AlertSettingsModel.create_volatility_risk_alert(
            timeframe="M5",
            threshold_value=2.0,
        )

        assert setting.alert_type == "risk_alert"
        assert setting.indicator_type == "ATR"
        assert setting.timeframe == "M5"
        assert setting.threshold_value == 2.0
        assert setting.condition_type == "above"
        assert setting.validate() is True

    def test_validation_failure(self):
        """バリデーション失敗テスト"""
        # 無効なタイムフレーム
        setting = AlertSettingsModel(
            alert_type="entry_signal",
            indicator_type="RSI",
            timeframe="INVALID",
            threshold_value=30.0,
        )
        assert setting.validate() is False

        # 無効な指標タイプ
        setting = AlertSettingsModel(
            alert_type="entry_signal",
            indicator_type="INVALID",
            timeframe="M5",
            threshold_value=30.0,
        )
        assert setting.validate() is False


class TestEntrySignalModel:
    """エントリーシグナルモデルテスト"""

    def test_create_buy_signal(self):
        """買いシグナル作成テスト"""
        signal = EntrySignalModel.create_buy_signal(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M5",
            entry_price=150.000,
            stop_loss=149.500,
            take_profit=150.750,
            confidence_score=75,
            indicators_used={"RSI": 25.5, "SMA_20": 150.100},
        )

        assert signal.signal_type == "BUY"
        assert signal.currency_pair == "USD/JPY"
        assert signal.timeframe == "M5"
        assert signal.entry_price == 150.000
        assert signal.stop_loss == 149.500
        assert signal.take_profit == 150.750
        assert signal.confidence_score == 75
        assert signal.risk_reward_ratio == 1.5
        assert signal.validate() is True

    def test_create_sell_signal(self):
        """売りシグナル作成テスト"""
        signal = EntrySignalModel.create_sell_signal(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M15",
            entry_price=150.000,
            stop_loss=150.500,
            take_profit=149.250,
            confidence_score=80,
            indicators_used={"RSI": 75.5, "BB_upper": 150.200},
        )

        assert signal.signal_type == "SELL"
        assert signal.currency_pair == "USD/JPY"
        assert signal.timeframe == "M15"
        assert signal.entry_price == 150.000
        assert signal.stop_loss == 150.500
        assert signal.take_profit == 149.250
        assert signal.confidence_score == 80
        assert signal.risk_reward_ratio == 1.5
        assert signal.validate() is True

    def test_calculate_risk_percentage(self):
        """リスク率計算テスト"""
        signal = EntrySignalModel.create_buy_signal(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M5",
            entry_price=150.000,
            stop_loss=149.500,
            take_profit=150.750,
            confidence_score=75,
        )

        risk_percentage = signal.calculate_risk_percentage()
        expected_risk = ((150.000 - 149.500) / 150.000) * 100
        assert abs(risk_percentage - expected_risk) < 0.01

    def test_calculate_profit_percentage(self):
        """利益率計算テスト"""
        signal = EntrySignalModel.create_buy_signal(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M5",
            entry_price=150.000,
            stop_loss=149.500,
            take_profit=150.750,
            confidence_score=75,
        )

        profit_percentage = signal.calculate_profit_percentage()
        expected_profit = ((150.750 - 150.000) / 150.000) * 100
        assert abs(profit_percentage - expected_profit) < 0.01

    def test_mark_as_executed(self):
        """実行済みマークテスト"""
        signal = EntrySignalModel.create_buy_signal(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M5",
            entry_price=150.000,
            stop_loss=149.500,
            take_profit=150.750,
            confidence_score=75,
        )

        assert signal.is_executed is False
        assert signal.executed_at is None

        executed_time = datetime.utcnow()
        signal.mark_as_executed(executed_time)

        assert signal.is_executed is True
        assert signal.executed_at == executed_time


class TestRiskAlertModel:
    """リスクアラートモデルテスト"""

    def test_create_volatility_spike_alert(self):
        """ボラティリティ急増アラート作成テスト"""
        alert = RiskAlertModel.create_volatility_spike_alert(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M5",
            current_atr=0.050,
            avg_atr=0.020,
            price_change_24h=2.5,
            volume_ratio=3.0,
            severity="HIGH",
        )

        assert alert.alert_type == "volatility_spike"
        assert alert.currency_pair == "USD/JPY"
        assert alert.timeframe == "M5"
        assert alert.severity == "HIGH"
        assert "ボラティリティ急増検出" in alert.message
        assert "ポジションサイズを50%削減" in alert.recommended_action
        assert alert.current_atr == 0.050
        assert alert.avg_atr == 0.020
        assert alert.validate() is True

    def test_create_correlation_alert(self):
        """相関性アラート作成テスト"""
        alert = RiskAlertModel.create_correlation_alert(
            currency_pair="USD/JPY",
            timestamp=datetime.utcnow(),
            timeframe="M5",
            current_correlation=0.85,
            avg_correlation=0.45,
            correlation_change=0.40,
            alert_type="high_correlation",
            severity="MEDIUM",
        )

        assert alert.alert_type == "high_correlation"
        assert alert.currency_pair == "USD/JPY"
        assert alert.severity == "MEDIUM"
        assert "高相関検出" in alert.message
        assert "ポジションの分散化" in alert.recommended_action
        assert alert.current_correlation == 0.85
        assert alert.validate() is True

    def test_acknowledge_alert(self):
        """アラート承認テスト"""
        alert = RiskAlertModel.create_volatility_spike_alert(
            currency_pair="USD/JPY",
            timeframe="M5",
            current_atr=0.050,
            avg_atr=0.020,
        )

        assert alert.is_acknowledged is False
        assert alert.acknowledged_at is None

        acknowledge_time = datetime.utcnow()
        alert.acknowledge(acknowledge_time)

        assert alert.is_acknowledged is True
        assert alert.acknowledged_at == acknowledge_time

    def test_is_critical(self):
        """重要度チェックテスト"""
        alert = RiskAlertModel.create_volatility_spike_alert(
            currency_pair="USD/JPY",
            timeframe="M5",
            current_atr=0.050,
            avg_atr=0.020,
            severity="CRITICAL",
        )

        assert alert.is_critical() is True
        assert alert.is_high_priority() is True

        alert.severity = "MEDIUM"
        assert alert.is_critical() is False
        assert alert.is_high_priority() is False

    def test_get_market_data_value(self):
        """市場データ取得テスト"""
        alert = RiskAlertModel.create_volatility_spike_alert(
            currency_pair="USD/JPY",
            timeframe="M5",
            current_atr=0.050,
            avg_atr=0.020,
        )

        assert alert.get_market_data_value("current_atr") == 0.050
        assert alert.get_market_data_value("avg_atr") == 0.020
        assert alert.get_market_data_value("nonexistent") is None


class TestSignalPerformanceModel:
    """シグナルパフォーマンスモデルテスト"""

    def test_create_from_signal(self):
        """シグナルからパフォーマンス記録作成テスト"""
        performance = SignalPerformanceModel.create_from_signal(
            signal_id=1,
            currency_pair="USD/JPY",
            timeframe="M5",
            entry_time=datetime.utcnow(),
            entry_price=150.000,
        )

        assert performance.signal_id == 1
        assert performance.currency_pair == "USD/JPY"
        assert performance.timeframe == "M5"
        assert performance.entry_price == 150.000
        assert performance.exit_price is None
        assert performance.pnl is None
        assert performance.validate() is True

    def test_close_position(self):
        """ポジションクローズテスト"""
        performance = SignalPerformanceModel.create_from_signal(
            signal_id=1,
            currency_pair="USD/JPY",
            timeframe="M5",
            entry_time=datetime.utcnow(),
            entry_price=150.000,
        )

        exit_time = datetime.utcnow() + timedelta(hours=1)
        performance.close_position(
            exit_price=150.500,
            exit_time=exit_time,
            exit_reason="take_profit",
        )

        assert performance.exit_price == 150.500
        assert performance.exit_time == exit_time
        assert performance.exit_reason == "take_profit"
        assert performance.pnl == 0.500
        assert abs(performance.pnl_percentage - 0.333) < 0.01
        assert performance.duration_minutes == 60

    def test_calculate_pnl(self):
        """損益計算テスト"""
        performance = SignalPerformanceModel(
            entry_price=150.000,
            exit_price=150.500,
        )

        pnl = performance.calculate_pnl()
        assert pnl == 0.500

        performance.exit_price = 149.500
        pnl = performance.calculate_pnl()
        assert pnl == -0.500

    def test_calculate_pnl_percentage(self):
        """損益率計算テスト"""
        performance = SignalPerformanceModel(
            entry_price=150.000,
            exit_price=150.500,
        )

        pnl_percentage = performance.calculate_pnl_percentage()
        expected_percentage = (0.500 / 150.000) * 100
        assert abs(pnl_percentage - expected_percentage) < 0.01

    def test_calculate_duration_minutes(self):
        """保有時間計算テスト"""
        entry_time = datetime.utcnow()
        exit_time = entry_time + timedelta(minutes=30)

        performance = SignalPerformanceModel(
            entry_time=entry_time,
            exit_time=exit_time,
        )

        duration = performance.calculate_duration_minutes()
        assert duration == 30

    def test_performance_categories(self):
        """パフォーマンスカテゴリテスト"""
        # 優秀なパフォーマンス
        performance = SignalPerformanceModel(pnl_percentage=2.5)
        assert performance.get_performance_category() == "excellent"

        # 良いパフォーマンス
        performance.pnl_percentage = 1.5
        assert performance.get_performance_category() == "good"

        # 利益
        performance.pnl_percentage = 0.5
        assert performance.get_performance_category() == "profitable"

        # 損益分岐点
        performance.pnl_percentage = 0.0
        assert performance.get_performance_category() == "breakeven"

        # 小損失
        performance.pnl_percentage = -0.5
        assert performance.get_performance_category() == "small_loss"

        # 損失
        performance.pnl_percentage = -1.5
        assert performance.get_performance_category() == "loss"

        # 大損失
        performance.pnl_percentage = -3.0
        assert performance.get_performance_category() == "big_loss"

    def test_profitability_checks(self):
        """利益性チェックテスト"""
        # 利益
        performance = SignalPerformanceModel(pnl_percentage=1.0)
        assert performance.is_profitable() is True
        assert performance.is_losing() is False
        assert performance.is_breakeven() is False

        # 損失
        performance.pnl_percentage = -1.0
        assert performance.is_profitable() is False
        assert performance.is_losing() is True
        assert performance.is_breakeven() is False

        # 損益分岐点
        performance.pnl_percentage = 0.0
        assert performance.is_profitable() is False
        assert performance.is_losing() is False
        assert performance.is_breakeven() is True


if __name__ == "__main__":
    pytest.main([__file__])
