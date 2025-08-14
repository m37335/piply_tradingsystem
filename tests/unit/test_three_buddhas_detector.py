#!/usr/bin/env python3
"""
Three Buddhas Detector Test
三尊天井/逆三尊検出器のテスト
"""

import unittest
import pandas as pd
import numpy as np

from src.infrastructure.analysis.pattern_detectors.three_buddhas_detector import (
    ThreeBuddhasDetector
)
from src.domain.value_objects.pattern_priority import PatternPriority


class TestThreeBuddhasDetector(unittest.TestCase):
    """三尊天井/逆三尊検出器のテスト"""

    def setUp(self):
        """テスト前の準備"""
        self.detector = ThreeBuddhasDetector()
        self.sample_data = self._create_sample_data()

    def _create_sample_data(self) -> pd.DataFrame:
        """サンプルデータ作成"""
        # 三尊天井パターンのサンプルデータ
        dates = pd.date_range(start='2024-01-01', periods=50, freq='H')
        data = []
        
        for i in range(50):
            if i < 10:
                # 最初のピーク
                high = 150.0 + np.random.normal(0, 0.1)
                low = 149.5 + np.random.normal(0, 0.1)
            elif 10 <= i < 20:
                # 中央のピーク（最も高い）
                high = 151.0 + np.random.normal(0, 0.1)
                low = 149.8 + np.random.normal(0, 0.1)
            elif 20 <= i < 30:
                # 最後のピーク
                high = 150.2 + np.random.normal(0, 0.1)
                low = 149.6 + np.random.normal(0, 0.1)
            else:
                # その他
                high = 150.0 + np.random.normal(0, 0.1)
                low = 149.5 + np.random.normal(0, 0.1)
            
            close = (high + low) / 2 + np.random.normal(0, 0.05)
            data.append({
                'timestamp': dates[i],
                'open': close + np.random.normal(0, 0.05),
                'high': high,
                'low': low,
                'close': close,
                'volume': 1000 + np.random.randint(0, 1000)
            })
        
        return pd.DataFrame(data)

    def test_detector_initialization(self):
        """検出器の初期化テスト"""
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.pattern.pattern_number, 13)
        self.assertEqual(self.detector.pattern.name, "三尊天井/逆三尊検出")

    def test_detect_with_none_data(self):
        """Noneデータでの検出テスト"""
        result = self.detector.detect(None)
        self.assertIsNone(result)

    def test_detect_with_insufficient_data(self):
        """不十分なデータでの検出テスト"""
        short_data = pd.DataFrame({'high': [150.0], 'low': [149.5], 'close': [149.8]})
        result = self.detector.detect(short_data)
        self.assertIsNone(result)

    def test_find_peaks_high(self):
        """高値ピーク検出テスト"""
        peaks = self.detector._find_peaks(self.sample_data, 'high')
        self.assertIsInstance(peaks, list)
        # ピークが検出されることを確認
        self.assertGreater(len(peaks), 0)

    def test_find_peaks_low(self):
        """安値ピーク検出テスト"""
        peaks = self.detector._find_peaks(self.sample_data, 'low')
        self.assertIsInstance(peaks, list)
        # ピークが検出されることを確認
        self.assertGreater(len(peaks), 0)

    def test_check_peak_distances(self):
        """ピーク間距離チェックテスト"""
        # 適切な距離のピーク
        peaks = [5, 15, 25]
        result = self.detector._check_peak_distances(peaks)
        self.assertTrue(result)

        # 距離が短すぎるピーク
        peaks = [5, 10, 15]
        result = self.detector._check_peak_distances(peaks)
        self.assertFalse(result)

    def test_is_middle_highest(self):
        """中央が最も高いかチェックテスト"""
        # 中央が最も高い場合
        peaks = [5, 15, 25]
        # サンプルデータを修正して中央を最も高くする
        test_data = self.sample_data.copy()
        test_data.iloc[5, test_data.columns.get_loc('high')] = 150.0
        test_data.iloc[15, test_data.columns.get_loc('high')] = 151.0
        test_data.iloc[25, test_data.columns.get_loc('high')] = 150.2
        
        result = self.detector._is_middle_highest(test_data, peaks)
        self.assertTrue(result)

    def test_is_middle_lowest(self):
        """中央が最も低いかチェックテスト"""
        # 中央が最も低い場合
        peaks = [5, 15, 25]
        # サンプルデータを修正して中央を最も低くする
        test_data = self.sample_data.copy()
        test_data.iloc[5, test_data.columns.get_loc('low')] = 149.8
        test_data.iloc[15, test_data.columns.get_loc('low')] = 149.5
        test_data.iloc[25, test_data.columns.get_loc('low')] = 149.9
        
        result = self.detector._is_middle_lowest(test_data, peaks)
        self.assertTrue(result)

    def test_validate_three_buddhas_pattern(self):
        """三尊パターン検証テスト"""
        peaks = [5, 15, 25]
        result = self.detector._validate_three_buddhas_pattern(self.sample_data, peaks)
        self.assertIsInstance(result, bool)

    def test_calculate_neckline(self):
        """ネックライン計算テスト"""
        peaks = [5, 15, 25]
        neckline = self.detector._calculate_neckline(self.sample_data, peaks)
        self.assertIsInstance(neckline, (float, type(None)))

    def test_calculate_three_buddhas_confidence(self):
        """三尊パターン信頼度計算テスト"""
        pattern_data = {
            "pattern_type": "three_buddhas_top",
            "peaks": [5, 15, 25],
            "neckline": 150.0
        }
        confidence = self.detector._calculate_three_buddhas_confidence(pattern_data)
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_create_detection_result(self):
        """検出結果作成テスト"""
        pattern_data = {
            "pattern_type": "three_buddhas_top",
            "peaks": [5, 15, 25],
            "neckline": 150.0,
            "direction": "SELL"
        }
        result = self.detector._create_detection_result(
            self.sample_data, "three_buddhas_top", pattern_data
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result["pattern_number"], 13)
        self.assertEqual(result["priority"], PatternPriority.HIGH)
        self.assertIn("confidence_score", result)
        self.assertIn("detection_time", result)

    def test_detect_three_buddhas_top(self):
        """三尊天井検出テスト"""
        result = self.detector._detect_three_buddhas_top(self.sample_data)
        # 結果はNoneまたは辞書
        self.assertIsInstance(result, (dict, type(None)))

    def test_detect_inverse_three_buddhas(self):
        """逆三尊検出テスト"""
        result = self.detector._detect_inverse_three_buddhas(self.sample_data)
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
        invalid_data = pd.DataFrame({
            'high': ['invalid', 'invalid', 'invalid'],
            'low': ['invalid', 'invalid', 'invalid'],
            'close': ['invalid', 'invalid', 'invalid']
        })
        
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


if __name__ == "__main__":
    unittest.main()
