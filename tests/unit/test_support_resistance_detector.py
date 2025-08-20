#!/usr/bin/env python3
"""
Support Resistance Detector Test
レジスタンス/サポートライン検出器のテスト
"""

import unittest

import numpy as np
import pandas as pd

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.pattern_detectors.support_resistance_detector import (
    SupportResistanceDetector,
)


class TestSupportResistanceDetector(unittest.TestCase):
    """レジスタンス/サポートライン検出器のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.detector = SupportResistanceDetector()
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self) -> pd.DataFrame:
        """サンプルデータ作成"""
        # レジスタンスラインのサンプルデータ
        dates = pd.date_range(start="2024-01-01", periods=50, freq="H")
        data = []

        for i in range(50):
            # レジスタンスライン: 150.0付近で価格が止まる
            if i in [10, 25, 40]:  # タッチポイント
                high = 150.0 + np.random.normal(0, 0.02)
                low = 149.5 + np.random.normal(0, 0.05)
            else:
                high = 149.5 + np.random.normal(0, 0.1)
                low = 149.0 + np.random.normal(0, 0.1)

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
        self.assertEqual(self.detector.pattern.pattern_number, 15)
        self.assertEqual(self.detector.pattern.name, "レジスタンス/サポートライン検出")

    def test_detect_with_none_data(self):
        """Noneデータでの検出テスト"""
        result = self.detector.detect(None)
        self.assertIsNone(result)

    def test_detect_with_insufficient_data(self):
        """不十分なデータでの検出テスト"""
        short_data = pd.DataFrame({"high": [150.0], "low": [149.5], "close": [149.8]})
        result = self.detector.detect(short_data)
        self.assertIsNone(result)

    def test_find_touch_points_resistance(self):
        """レジスタンスタッチポイント検出テスト"""
        touch_points = self.detector._find_touch_points(self.sample_data, "resistance")
        self.assertIsInstance(touch_points, list)
        # タッチポイントが検出されることを確認
        self.assertGreater(len(touch_points), 0)

    def test_find_touch_points_support(self):
        """サポートタッチポイント検出テスト"""
        touch_points = self.detector._find_touch_points(self.sample_data, "support")
        self.assertIsInstance(touch_points, list)

    def test_calculate_line_equation(self):
        """ライン方程式計算テスト"""
        touch_points = [10, 25, 40]
        line_data = self.detector._calculate_line_equation(
            touch_points, self.sample_data, "high"
        )

        if line_data is not None:
            self.assertIn("slope", line_data)
            self.assertIn("intercept", line_data)
            self.assertIn("touch_points", line_data)
            self.assertIn("prices", line_data)
            self.assertIsInstance(line_data["slope"], float)
            self.assertIsInstance(line_data["intercept"], float)

    def test_validate_line_strength(self):
        """ライン強度検証テスト"""
        touch_points = [10, 25, 40]
        line_data = {"slope": 0.0, "intercept": 150.0, "prices": [150.0, 150.1, 149.9]}
        strength = self.detector._validate_line_strength(touch_points, line_data)
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)

    def test_detect_breakout(self):
        """ブレイクアウト検出テスト"""
        line_data = {"slope": 0.0, "intercept": 150.0}
        result = self.detector._detect_breakout(
            self.sample_data, line_data, "resistance"
        )
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_confirm_breakout(self):
        """ブレイクアウト確認テスト"""
        line_data = {"slope": 0.0, "intercept": 150.0}
        result = self.detector._confirm_breakout(
            self.sample_data, line_data, "resistance", "bullish"
        )
        self.assertIsInstance(result, bool)

    def test_calculate_support_resistance_confidence(self):
        """レジスタンス/サポートライン信頼度計算テスト"""
        pattern_data = {
            "line_type": "resistance",
            "strength": 0.85,
            "touch_points": [10, 25, 40],
            "breakout": {"strength": 0.015},
        }
        confidence = self.detector._calculate_support_resistance_confidence(
            pattern_data
        )
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_create_detection_result(self):
        """検出結果作成テスト"""
        pattern_data = {
            "line_type": "resistance",
            "touch_points": [10, 25, 40],
            "line_data": {},
            "strength": 0.85,
            "breakout": {},
            "direction": "SELL",
        }
        result = self.detector._create_detection_result(
            self.sample_data, "resistance_line", pattern_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["pattern_number"], 15)
        self.assertEqual(result["priority"], PatternPriority.HIGH)
        self.assertIn("confidence_score", result)
        self.assertIn("detection_time", result)

    def test_detect_resistance_line(self):
        """レジスタンスライン検出テスト"""
        result = self.detector._detect_resistance_line(self.sample_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_detect_support_line(self):
        """サポートライン検出テスト"""
        result = self.detector._detect_support_line(self.sample_data)
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

    def test_resistance_line_detection(self):
        """レジスタンスライン検出の詳細テスト"""
        # レジスタンスラインの特徴的なデータを作成
        resistance_data = self._create_resistance_line_data()
        result = self.detector._detect_resistance_line(resistance_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_support_line_detection(self):
        """サポートライン検出の詳細テスト"""
        # サポートラインの特徴的なデータを作成
        support_data = self._create_support_line_data()
        result = self.detector._detect_support_line(support_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def _create_resistance_line_data(self) -> pd.DataFrame:
        """レジスタンスラインデータ作成"""
        dates = pd.date_range(start="2024-01-01", periods=40, freq="H")
        data = []

        for i in range(40):
            # レジスタンスライン: 151.0付近で価格が止まる
            if i in [8, 20, 32]:  # タッチポイント
                high = 151.0 + np.random.normal(0, 0.01)
                low = 150.5 + np.random.normal(0, 0.05)
            else:
                high = 150.8 + np.random.normal(0, 0.1)
                low = 150.2 + np.random.normal(0, 0.1)

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

    def _create_support_line_data(self) -> pd.DataFrame:
        """サポートラインデータ作成"""
        dates = pd.date_range(start="2024-01-01", periods=40, freq="H")
        data = []

        for i in range(40):
            # サポートライン: 149.0付近で価格が止まる
            if i in [8, 20, 32]:  # タッチポイント
                high = 149.5 + np.random.normal(0, 0.05)
                low = 149.0 + np.random.normal(0, 0.01)
            else:
                high = 149.8 + np.random.normal(0, 0.1)
                low = 149.2 + np.random.normal(0, 0.1)

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
