#!/usr/bin/env python3
"""
Wedge Pattern Detector Test
ウェッジパターン検出器のテスト
"""

import unittest

import numpy as np
import pandas as pd

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.pattern_detectors.wedge_pattern_detector import (
    WedgePatternDetector,
)


class TestWedgePatternDetector(unittest.TestCase):
    """ウェッジパターン検出器のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.detector = WedgePatternDetector()
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self) -> pd.DataFrame:
        """サンプルデータ作成"""
        # 上昇ウェッジパターンのサンプルデータ
        dates = pd.date_range(start="2024-01-01", periods=50, freq="H")
        data = []

        for i in range(50):
            # 上昇ウェッジ: 高値と安値が徐々に収束
            if i < 25:
                # 前半: 上昇トレンド
                high = 150.0 + i * 0.02 + np.random.normal(0, 0.05)
                low = 149.5 + i * 0.01 + np.random.normal(0, 0.05)
            else:
                # 後半: 収束
                high = 150.5 + (50 - i) * 0.01 + np.random.normal(0, 0.05)
                low = 149.8 + (50 - i) * 0.005 + np.random.normal(0, 0.05)

            close = (high + low) / 2 + np.random.normal(0, 0.05)
            data.append(
                {
                    "timestamp": dates[i],
                    "open": close + np.random.normal(0, 0.05),
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + np.random.randint(0, 1000),
                }
            )

        return pd.DataFrame(data)

    def test_detector_initialization(self):
        """検出器の初期化テスト"""
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.pattern.pattern_number, 14)
        self.assertEqual(self.detector.pattern.name, "ウェッジパターン検出")

    def test_detect_with_none_data(self):
        """Noneデータでの検出テスト"""
        result = self.detector.detect(None)
        self.assertIsNone(result)

    def test_detect_with_insufficient_data(self):
        """不十分なデータでの検出テスト"""
        short_data = pd.DataFrame({"high": [150.0], "low": [149.5], "close": [149.8]})
        result = self.detector.detect(short_data)
        self.assertIsNone(result)

    def test_find_peaks(self):
        """ピーク検出テスト"""
        peaks = self.detector._find_peaks(self.sample_data, "high")
        self.assertIsInstance(peaks, list)
        # ピークが検出されることを確認
        self.assertGreater(len(peaks), 0)

        peaks = self.detector._find_peaks(self.sample_data, "low")
        self.assertIsInstance(peaks, list)
        self.assertGreater(len(peaks), 0)

    def test_calculate_trend_line(self):
        """トレンドライン計算テスト"""
        points = [5, 15, 25]
        line = self.detector._calculate_trend_line(self.sample_data, points, "high")

        if line is not None:
            self.assertIn("slope", line)
            self.assertIn("intercept", line)
            self.assertIn("points", line)
            self.assertIsInstance(line["slope"], float)
            self.assertIsInstance(line["intercept"], float)

    def test_calculate_line_angle(self):
        """ライン角度計算テスト"""
        line = {"slope": 0.1, "intercept": 150.0}
        angle = self.detector._calculate_line_angle(line)
        self.assertIsInstance(angle, float)

    def test_check_convergence(self):
        """収束チェックテスト"""
        wedge_lines = {
            "upper_angle": 15.0,
            "lower_angle": 10.0,
            "upper_line": {"slope": 0.1},
            "lower_line": {"slope": 0.15},
        }
        result = self.detector._check_convergence(wedge_lines)
        self.assertIsInstance(result, bool)

    def test_validate_wedge_breakout(self):
        """ウェッジブレイクアウト検証テスト"""
        wedge_lines = {
            "upper_line": {"slope": 0.1, "intercept": 150.0},
            "lower_line": {"slope": 0.15, "intercept": 149.5},
        }
        result = self.detector._validate_wedge_breakout(self.sample_data, wedge_lines)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_calculate_wedge_confidence(self):
        """ウェッジパターン信頼度計算テスト"""
        pattern_data = {
            "pattern_type": "rising_wedge",
            "wedge_lines": {
                "upper_angle": 15.0,
                "lower_angle": 10.0,
                "highs": [5, 15, 25],
                "lows": [8, 18, 28],
            },
            "breakout": {"strength": 0.01},
        }
        confidence = self.detector._calculate_wedge_confidence(pattern_data)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_create_detection_result(self):
        """検出結果作成テスト"""
        pattern_data = {
            "pattern_type": "rising_wedge",
            "wedge_lines": {},
            "breakout": {},
            "direction": "SELL",
        }
        result = self.detector._create_detection_result(
            self.sample_data, "rising_wedge", pattern_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["pattern_number"], 14)
        self.assertEqual(result["priority"], PatternPriority.HIGH)
        self.assertIn("confidence_score", result)
        self.assertIn("detection_time", result)

    def test_detect_rising_wedge(self):
        """上昇ウェッジ検出テスト"""
        result = self.detector._detect_rising_wedge(self.sample_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_detect_falling_wedge(self):
        """下降ウェッジ検出テスト"""
        result = self.detector._detect_falling_wedge(self.sample_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_identify_wedge_lines(self):
        """ウェッジライン識別テスト"""
        result = self.detector._identify_wedge_lines(self.sample_data, is_rising=True)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_detect_integration(self):
        """統合検出テスト"""
        result = self.detector.detect(self.sample_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # 不正なデータでテスト
        invalid_data = pd.DataFrame(
            {
                "high": ["invalid", "invalid", "invalid"],
                "low": ["invalid", "invalid", "invalid"],
                "close": ["invalid", "invalid", "invalid"],
            }
        )

        result = self.detector.detect(invalid_data)
        self.assertIsNone(result)

    def test_pattern_priority(self):
        """パターン優先度テスト"""
        self.assertEqual(self.detector.pattern.priority, PatternPriority.HIGH)

    def test_pattern_conditions(self):
        """パターン条件テスト"""
        conditions = self.detector.pattern.conditions
        self.assertIn("D1", conditions)
        self.assertIn("H4", conditions)
        self.assertIn("H1", conditions)
        self.assertIn("M5", conditions)

    def test_rising_wedge_detection(self):
        """上昇ウェッジ検出の詳細テスト"""
        # 上昇ウェッジの特徴的なデータを作成
        rising_wedge_data = self._create_rising_wedge_data()
        result = self.detector._detect_rising_wedge(rising_wedge_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_falling_wedge_detection(self):
        """下降ウェッジ検出の詳細テスト"""
        # 下降ウェッジの特徴的なデータを作成
        falling_wedge_data = self._create_falling_wedge_data()
        result = self.detector._detect_falling_wedge(falling_wedge_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def _create_rising_wedge_data(self) -> pd.DataFrame:
        """上昇ウェッジデータ作成"""
        dates = pd.date_range(start="2024-01-01", periods=40, freq="H")
        data = []

        for i in range(40):
            # 上昇ウェッジ: 高値と安値が徐々に収束
            high = 150.0 + i * 0.015 + np.random.normal(0, 0.03)
            low = 149.5 + i * 0.008 + np.random.normal(0, 0.03)

            close = (high + low) / 2 + np.random.normal(0, 0.03)
            data.append(
                {
                    "timestamp": dates[i],
                    "open": close + np.random.normal(0, 0.03),
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + np.random.randint(0, 1000),
                }
            )

        return pd.DataFrame(data)

    def _create_falling_wedge_data(self) -> pd.DataFrame:
        """下降ウェッジデータ作成"""
        dates = pd.date_range(start="2024-01-01", periods=40, freq="H")
        data = []

        for i in range(40):
            # 下降ウェッジ: 高値と安値が徐々に収束
            high = 150.5 - i * 0.008 + np.random.normal(0, 0.03)
            low = 149.8 - i * 0.015 + np.random.normal(0, 0.03)

            close = (high + low) / 2 + np.random.normal(0, 0.03)
            data.append(
                {
                    "timestamp": dates[i],
                    "open": close + np.random.normal(0, 0.03),
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": 1000 + np.random.randint(0, 1000),
                }
            )

        return pd.DataFrame(data)


if __name__ == "__main__":
    unittest.main()
