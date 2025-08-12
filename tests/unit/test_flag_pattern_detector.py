"""
フラッグパターン検出器の単体テスト

パターン12の検出機能をテスト
"""

from unittest.mock import Mock

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.flag_pattern_detector import (
    FlagPatternDetector,
)


class TestFlagPatternDetector:
    """フラッグパターン検出器のテストクラス"""

    def setup_method(self):
        """テスト前の準備"""
        self.detector = FlagPatternDetector()
        self.mock_utils = Mock()
        self.detector.utils = self.mock_utils

    def test_init(self):
        """初期化テスト"""
        assert self.detector.pattern.pattern_number == 12
        assert self.detector.pattern.name == "フラッグパターン検出"
        assert self.detector.min_flag_length == 3
        assert self.detector.max_flag_length == 15
        assert self.detector.flag_angle_tolerance == 30

    def test_validate_data_success(self):
        """データ妥当性チェック成功テスト"""
        mock_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            "H1": {"price_data": pd.DataFrame()},
            "M5": {"price_data": pd.DataFrame()},
        }

        self.mock_utils.validate_timeframe_data.return_value = True

        result = self.detector._validate_data(mock_data)
        assert result is True

    def test_validate_data_failure_missing_timeframe(self):
        """データ妥当性チェック失敗テスト（時間軸不足）"""
        mock_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            # H1, M5が不足
        }

        result = self.detector._validate_data(mock_data)
        assert result is False

    def test_detect_bull_flag_success(self):
        """ブルフラッグ検出成功テスト"""
        price_data = self._create_bull_flag_test_data()
        
        result = self.detector._detect_bull_flag(price_data)
        assert result

    def test_detect_bear_flag_success(self):
        """ベアフラッグ検出成功テスト"""
        price_data = self._create_bear_flag_test_data()

        result = self.detector._detect_bear_flag(price_data)
        assert result

    def test_detect_bull_flag_failure_insufficient_data(self):
        """ブルフラッグ検出失敗テスト（データ不足）"""
        price_data = pd.DataFrame(
            {
                "high": [100, 101, 102],
                "low": [99, 100, 101],
                "close": [100.5, 100.8, 101.5],
            }
        )

        result = self.detector._detect_bull_flag(price_data)
        assert result is False

    def test_identify_flagpole_success(self):
        """フラッグポール識別成功テスト"""
        price_data = self._create_bull_flag_test_data()

        result = self.detector._identify_flagpole(price_data)
        assert result is not None
        assert "start_index" in result
        assert "end_index" in result
        assert "direction" in result

    def test_identify_flag_success(self):
        """フラッグ識別成功テスト"""
        price_data = self._create_bull_flag_test_data()
        pole_end = 10  # フラッグポールの終了位置

        result = self.detector._identify_flag(price_data, pole_end)
        assert result is not None
        assert "start_index" in result
        assert "end_index" in result
        assert "angle" in result

    def test_is_linear_trend_up(self):
        """上昇直線トレンドテスト"""
        data = pd.DataFrame({"close": [100, 101, 102, 103, 104, 105]})

        result = self.detector._is_linear_trend(data, "up")
        assert result is True

    def test_is_linear_trend_down(self):
        """下降直線トレンドテスト"""
        data = pd.DataFrame({"close": [105, 104, 103, 102, 101, 100]})

        result = self.detector._is_linear_trend(data, "down")
        assert result is True

    def test_calculate_flag_angle(self):
        """フラッグ角度計算テスト"""
        flag_data = pd.DataFrame({"close": [100, 99, 98, 97, 96]})

        angle = self.detector._calculate_flag_angle(flag_data)
        assert isinstance(angle, float)
        assert angle < 0  # 下降フラッグ

    def test_validate_flag_breakout_success(self):
        """フラッグブレイクアウト検証成功テスト"""
        price_data = self._create_bull_flag_test_data()
        flag_data = {"start_index": 10, "end_index": 20}

        result = self.detector._validate_flag_breakout(price_data, flag_data)
        assert result

    def test_calculate_flag_pattern_confidence(self):
        """フラッグパターン信頼度計算テスト"""
        conditions_met = {"D1": True, "H4": True, "H1": True, "M5": True}

        confidence = self.detector._calculate_flag_pattern_confidence(conditions_met)
        assert 0.6 <= confidence <= 0.95
        assert abs(confidence - 0.75) < 0.001  # 全条件満たした場合の期待値

    def test_detect_integration_success(self):
        """統合検出テスト（成功）"""
        mock_data = {
            "D1": {"price_data": self._create_bull_flag_test_data()},
            "H4": {"price_data": self._create_bull_flag_test_data()},
            "H1": {"price_data": self._create_bull_flag_test_data()},
            "M5": {"price_data": self._create_bull_flag_test_data()},
        }

        self.mock_utils.validate_timeframe_data.return_value = True

        result = self.detector.detect(mock_data)

        assert result is not None
        assert result["pattern_number"] == 12
        assert result["pattern_name"] == "フラッグパターン検出"
        assert result["confidence_score"] > 0.6

    def test_detect_integration_failure(self):
        """統合検出テスト（失敗）"""
        mock_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            "H1": {"price_data": pd.DataFrame()},
            "M5": {"price_data": pd.DataFrame()},
        }

        self.mock_utils.validate_timeframe_data.return_value = False

        result = self.detector.detect(mock_data)
        assert result is None

    def _create_bull_flag_test_data(self) -> pd.DataFrame:
        """ブルフラッグパターンのテストデータを作成"""
        data = []

        # フラッグポール（上昇）
        for i in range(10):
            data.append(
                {"high": 100 + i * 1.0, "low": 99 + i * 1.0, "close": 100.5 + i * 1.0}
            )

        # フラッグ（横ばい）
        for i in range(8):
            data.append(
                {"high": 110 + i * 0.1, "low": 109 + i * 0.1, "close": 109.5 + i * 0.1}
            )

        # ブレイクアウト
        data.append({"high": 112, "low": 111, "close": 111.5})

        # データ長を20以上にするために追加
        data.append({"high": 113, "low": 112, "close": 112.5})

        # ブレイクアウト後のデータを追加
        data.append({"high": 114, "low": 113, "close": 113.5})

        return pd.DataFrame(data)

    def _create_bear_flag_test_data(self) -> pd.DataFrame:
        """ベアフラッグパターンのテストデータを作成"""
        data = []

        # フラッグポール（下降）
        for i in range(10):
            data.append(
                {"high": 110 - i * 1.0, "low": 109 - i * 1.0, "close": 109.5 - i * 1.0}
            )

        # フラッグ（横ばい）
        for i in range(8):
            data.append(
                {"high": 101 + i * 0.1, "low": 100 + i * 0.1, "close": 100.5 + i * 0.1}
            )

        # ブレイクアウト
        data.append({"high": 102, "low": 99, "close": 99.5})

        # データ長を20以上にするために追加
        data.append({"high": 101, "low": 98, "close": 98.5})

        # ブレイクアウト後のデータを追加
        data.append({"high": 100, "low": 97, "close": 97.5})

        return pd.DataFrame(data)
