"""
トリプルトップ/ボトム検出器の単体テスト

パターン11の検出機能をテスト
"""

from unittest.mock import Mock

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.triple_top_bottom_detector import (
    TripleTopBottomDetector,
)


class TestTripleTopBottomDetector:
    """トリプルトップ/ボトム検出器のテストクラス"""

    def setup_method(self):
        """テスト前の準備"""
        self.detector = TripleTopBottomDetector()
        self.mock_utils = Mock()
        self.detector.utils = self.mock_utils

    def test_init(self):
        """初期化テスト"""
        assert self.detector.pattern.pattern_number == 11
        assert self.detector.pattern.name == "トリプルトップ/ボトム検出"
        assert self.detector.min_peak_distance == 5
        assert self.detector.peak_tolerance == 0.015
        assert self.detector.neckline_tolerance == 0.008

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

    def test_detect_triple_top_success(self):
        """トリプルトップ検出成功テスト"""
        price_data = self._create_triple_top_test_data()

        result = self.detector._detect_triple_top(price_data)
        assert result

    def test_detect_triple_bottom_success(self):
        """トリプルボトム検出成功テスト"""
        price_data = self._create_triple_bottom_test_data()

        result = self.detector._detect_triple_bottom(price_data)
        assert result

    def test_detect_triple_top_failure_insufficient_data(self):
        """トリプルトップ検出失敗テスト（データ不足）"""
        price_data = pd.DataFrame(
            {
                "high": [100, 101, 102],
                "low": [99, 100, 101],
                "close": [100.5, 100.8, 101.5],
            }
        )

        result = self.detector._detect_triple_top(price_data)
        assert result is False

    def test_identify_flagpole_success(self):
        """フラッグポール識別成功テスト"""
        price_data = self._create_triple_top_test_data()

        result = self.detector._identify_flagpole(price_data)
        assert result is not None
        assert "start_index" in result
        assert "end_index" in result
        assert "direction" in result

    def test_identify_flag_success(self):
        """フラッグ識別成功テスト"""
        price_data = self._create_triple_top_test_data()
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

    def test_validate_triple_neckline_success(self):
        """トリプルネックライン検証成功テスト"""
        price_data = self._create_triple_top_test_data()
        peaks = [5, 15, 25]  # 3つのピーク位置

        result = self.detector._validate_triple_neckline(price_data, peaks, "top")
        assert result

    def test_calculate_triple_pattern_confidence(self):
        """トリプルパターン信頼度計算テスト"""
        conditions_met = {"D1": True, "H4": True, "H1": True, "M5": True}

        confidence = self.detector._calculate_triple_pattern_confidence(conditions_met)
        assert 0.6 <= confidence <= 0.95
        assert abs(confidence - 0.85) < 0.001  # 全条件満たした場合の期待値

    def test_detect_integration_success(self):
        """統合検出テスト（成功）"""
        mock_data = {
            "D1": {"price_data": self._create_triple_top_test_data()},
            "H4": {"price_data": self._create_triple_top_test_data()},
            "H1": {"price_data": self._create_triple_top_test_data()},
            "M5": {"price_data": self._create_triple_top_test_data()},
        }

        self.mock_utils.validate_timeframe_data.return_value = True

        result = self.detector.detect(mock_data)

        assert result is not None
        assert result["pattern_number"] == 11
        assert result["pattern_name"] == "トリプルトップ/ボトム検出"
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

    def _create_triple_top_test_data(self) -> pd.DataFrame:
        """トリプルトップパターンのテストデータを作成"""
        data = []

        # 最初のピーク
        for i in range(5):
            data.append(
                {"high": 100 + i * 0.5, "low": 99 + i * 0.5, "close": 100.5 + i * 0.5}
            )
        data.append({"high": 105, "low": 104, "close": 104.5})  # 最初のピーク

        # 谷
        for i in range(5):
            data.append(
                {
                    "high": 104.5 - i * 0.3,
                    "low": 103.5 - i * 0.3,
                    "close": 104 - i * 0.3,
                }
            )

        # 2番目のピーク
        for i in range(5):
            data.append(
                {"high": 103 + i * 0.4, "low": 102 + i * 0.4, "close": 102.5 + i * 0.4}
            )
        data.append({"high": 105, "low": 104, "close": 104.5})  # 2番目のピーク

        # 谷
        for i in range(5):
            data.append(
                {
                    "high": 104.5 - i * 0.3,
                    "low": 103.5 - i * 0.3,
                    "close": 104 - i * 0.3,
                }
            )

        # 3番目のピーク
        for i in range(5):
            data.append(
                {"high": 103 + i * 0.4, "low": 102 + i * 0.4, "close": 102.5 + i * 0.4}
            )
        data.append({"high": 105, "low": 104, "close": 104.5})  # 3番目のピーク

        return pd.DataFrame(data)

    def _create_triple_bottom_test_data(self) -> pd.DataFrame:
        """トリプルボトムパターンのテストデータを作成"""
        data = []

        # 最初のボトム
        for i in range(5):
            data.append(
                {"high": 105 - i * 0.5, "low": 104 - i * 0.5, "close": 104.5 - i * 0.5}
            )
        data.append({"high": 101, "low": 100, "close": 100.5})  # 最初のボトム

        # 山
        for i in range(5):
            data.append(
                {"high": 100.5 + i * 0.3, "low": 99.5 + i * 0.3, "close": 100 + i * 0.3}
            )

        # 2番目のボトム
        for i in range(5):
            data.append(
                {
                    "high": 101.5 - i * 0.4,
                    "low": 100.5 - i * 0.4,
                    "close": 101 - i * 0.4,
                }
            )
        data.append({"high": 101, "low": 100, "close": 100.5})  # 2番目のボトム

        # 山
        for i in range(5):
            data.append(
                {"high": 100.5 + i * 0.3, "low": 99.5 + i * 0.3, "close": 100 + i * 0.3}
            )

        # 3番目のボトム
        for i in range(5):
            data.append(
                {
                    "high": 101.5 - i * 0.4,
                    "low": 100.5 - i * 0.4,
                    "close": 101 - i * 0.4,
                }
            )
        data.append({"high": 101, "low": 100, "close": 100.5})  # 3番目のボトム

        return pd.DataFrame(data)
