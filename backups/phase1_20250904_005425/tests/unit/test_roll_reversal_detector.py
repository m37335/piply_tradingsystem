#!/usr/bin/env python3
"""
Roll Reversal Detector Test
ロールリバーサル検出器のテスト
"""

import unittest

import numpy as np
import pandas as pd

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.pattern_detectors.roll_reversal_detector import (
    RollReversalDetector,
)


class TestRollReversalDetector(unittest.TestCase):
    """ロールリバーサル検出器のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.detector = RollReversalDetector()
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self) -> pd.DataFrame:
        """サンプルデータ作成"""
        # ロールリバーサルパターンのサンプルデータ
        dates = pd.date_range(start="2024-01-01", periods=50, freq="H")
        data = []

        for i in range(50):
            # 下降トレンド後の上昇転換
            if i < 30:
                # 下降トレンド
                high = 150.0 - i * 0.01 + np.random.normal(0, 0.05)
                low = 149.5 - i * 0.01 + np.random.normal(0, 0.05)
            else:
                # 上昇転換
                high = 149.7 + (i - 30) * 0.02 + np.random.normal(0, 0.05)
                low = 149.2 + (i - 30) * 0.02 + np.random.normal(0, 0.05)

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
        self.assertEqual(self.detector.pattern.pattern_number, 16)
        self.assertEqual(self.detector.pattern.name, "ロールリバーサル検出")

    def test_detect_with_none_data(self):
        """Noneデータでの検出テスト"""
        result = self.detector.detect(None)
        self.assertIsNone(result)

    def test_detect_with_insufficient_data(self):
        """不十分なデータでの検出テスト"""
        short_data = pd.DataFrame({"high": [150.0], "low": [149.5], "close": [149.8]})
        result = self.detector.detect(short_data)
        self.assertIsNone(result)

    def test_find_bearish_roll_points(self):
        """下降ロールポイント検出テスト"""
        roll_points = self.detector._find_bearish_roll_points(self.sample_data)
        self.assertIsInstance(roll_points, list)

    def test_find_bullish_roll_points(self):
        """上昇ロールポイント検出テスト"""
        roll_points = self.detector._find_bullish_roll_points(self.sample_data)
        self.assertIsInstance(roll_points, list)

    def test_identify_roll_pattern(self):
        """ロールパターン識別テスト"""
        result = self.detector._identify_roll_pattern(self.sample_data, "bearish")
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_calculate_roll_characteristics(self):
        """ロール特徴計算テスト"""
        roll_points = [5, 15, 25, 35]
        characteristics = self.detector._calculate_roll_characteristics(
            self.sample_data, roll_points, "bearish"
        )

        if characteristics:
            self.assertIn("roll_length", characteristics)
            self.assertIn("avg_price_change", characteristics)
            self.assertIn("price_consistency", characteristics)
            self.assertIn("momentum", characteristics)
            self.assertIn("trend_strength", characteristics)

    def test_detect_reversal_signal(self):
        """リバーサルシグナル検出テスト"""
        roll_data = {"roll_points": [5, 15, 25, 35]}
        result = self.detector._detect_reversal_signal(
            self.sample_data, roll_data, "bullish"
        )
        self.assertIsInstance(result, bool)

    def test_calculate_momentum(self):
        """モメンタム計算テスト"""
        points = [5, 15, 25, 35]
        momentum = self.detector._calculate_momentum(self.sample_data, points)
        self.assertIsInstance(momentum, float)

    def test_validate_roll_reversal(self):
        """ロールリバーサル検証テスト"""
        pattern_data = {
            "characteristics": {
                "roll_length": 8,
                "trend_strength": 0.025,
                "price_consistency": 0.75,
                "momentum": 0.02,
            }
        }
        result = self.detector._validate_roll_reversal(self.sample_data, pattern_data)
        self.assertIsInstance(result, bool)

    def test_calculate_roll_reversal_confidence(self):
        """ロールリバーサル信頼度計算テスト"""
        pattern_data = {
            "pattern_type": "bullish_roll_reversal",
            "roll_data": {
                "characteristics": {
                    "roll_length": 10,
                    "trend_strength": 0.03,
                    "price_consistency": 0.85,
                    "momentum": 0.025,
                }
            },
        }
        confidence = self.detector._calculate_roll_reversal_confidence(pattern_data)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_create_detection_result(self):
        """検出結果作成テスト"""
        pattern_data = {
            "pattern_type": "bullish_roll_reversal",
            "roll_data": {},
            "direction": "BUY",
        }
        result = self.detector._create_detection_result(
            self.sample_data, "bullish_roll_reversal", pattern_data
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["pattern_number"], 16)
        self.assertEqual(result["priority"], PatternPriority.MEDIUM)
        self.assertIn("confidence_score", result)
        self.assertIn("detection_time", result)

    def test_detect_bullish_roll_reversal(self):
        """強気ロールリバーサル検出テスト"""
        result = self.detector._detect_bullish_roll_reversal(self.sample_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_detect_bearish_roll_reversal(self):
        """弱気ロールリバーサル検出テスト"""
        result = self.detector._detect_bearish_roll_reversal(self.sample_data)
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
        self.assertEqual(self.detector.pattern.priority, PatternPriority.MEDIUM)

    def test_pattern_conditions(self):
        """パターン条件テスト"""
        conditions = self.detector.pattern.conditions
        self.assertIn("D1", conditions)
        self.assertIn("H4", conditions)
        self.assertIn("H1", conditions)
        self.assertIn("M5", conditions)

    def test_bullish_roll_reversal_detection(self):
        """強気ロールリバーサル検出の詳細テスト"""
        # 強気ロールリバーサルの特徴的なデータを作成
        bullish_data = self._create_bullish_roll_data()
        result = self.detector._detect_bullish_roll_reversal(bullish_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_bearish_roll_reversal_detection(self):
        """弱気ロールリバーサル検出の詳細テスト"""
        # 弱気ロールリバーサルの特徴的なデータを作成
        bearish_data = self._create_bearish_roll_data()
        result = self.detector._detect_bearish_roll_reversal(bearish_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def _create_bullish_roll_data(self) -> pd.DataFrame:
        """強気ロールリバーサルデータ作成"""
        dates = pd.date_range(start="2024-01-01", periods=40, freq="H")
        data = []

        for i in range(40):
            # 下降トレンド後の上昇転換
            if i < 25:
                # 下降トレンド
                high = 150.0 - i * 0.015 + np.random.normal(0, 0.03)
                low = 149.5 - i * 0.015 + np.random.normal(0, 0.03)
            else:
                # 上昇転換
                high = 149.6 + (i - 25) * 0.025 + np.random.normal(0, 0.03)
                low = 149.1 + (i - 25) * 0.025 + np.random.normal(0, 0.03)

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

    def _create_bearish_roll_data(self) -> pd.DataFrame:
        """弱気ロールリバーサルデータ作成"""
        dates = pd.date_range(start="2024-01-01", periods=40, freq="H")
        data = []

        for i in range(40):
            # 上昇トレンド後の下降転換
            if i < 25:
                # 上昇トレンド
                high = 150.0 + i * 0.015 + np.random.normal(0, 0.03)
                low = 149.5 + i * 0.015 + np.random.normal(0, 0.03)
            else:
                # 下降転換
                high = 150.4 - (i - 25) * 0.025 + np.random.normal(0, 0.03)
                low = 149.9 - (i - 25) * 0.025 + np.random.normal(0, 0.03)

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
