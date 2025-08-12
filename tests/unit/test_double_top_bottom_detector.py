"""
ダブルトップ/ボトム検出器の単体テスト

パターン10の検出機能をテスト
"""

import pandas as pd
from unittest.mock import Mock

from src.infrastructure.analysis.pattern_detectors.double_top_bottom_detector import (
    DoubleTopBottomDetector
)


class TestDoubleTopBottomDetector:
    """ダブルトップ/ボトム検出器のテストクラス"""

    def setup_method(self):
        """テスト前の準備"""
        self.detector = DoubleTopBottomDetector()
        self.mock_utils = Mock()
        self.detector.utils = self.mock_utils

    def test_init(self):
        """初期化テスト"""
        assert self.detector.pattern.pattern_number == 10
        assert self.detector.pattern.name == "ダブルトップ/ボトム検出"
        assert self.detector.min_peak_distance == 5
        assert self.detector.peak_tolerance == 0.02
        assert self.detector.neckline_tolerance == 0.01

    def test_validate_data_success(self):
        """データ妥当性チェック成功テスト"""
        # モックデータの準備
        mock_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            "H1": {"price_data": pd.DataFrame()},
            "M5": {"price_data": pd.DataFrame()}
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

    def test_validate_data_failure_invalid_data(self):
        """データ妥当性チェック失敗テスト（無効データ）"""
        mock_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            "H1": {"price_data": pd.DataFrame()},
            "M5": {"price_data": pd.DataFrame()}
        }
        
        self.mock_utils.validate_timeframe_data.return_value = False
        
        result = self.detector._validate_data(mock_data)
        assert result is False

    def test_detect_double_top_success(self):
        """ダブルトップ検出成功テスト"""
        # ダブルトップパターンのテストデータを作成
        price_data = self._create_double_top_test_data()
        
        result = self.detector._detect_double_top(price_data)
        assert result is True

    def test_detect_double_bottom_success(self):
        """ダブルボトム検出成功テスト"""
        # ダブルボトムパターンのテストデータを作成
        price_data = self._create_double_bottom_test_data()
        
        result = self.detector._detect_double_bottom(price_data)
        assert result is True

    def test_detect_double_top_failure_insufficient_data(self):
        """ダブルトップ検出失敗テスト（データ不足）"""
        price_data = pd.DataFrame({
            'high': [100, 101, 102],
            'low': [99, 100, 101],
            'close': [100.5, 100.8, 101.5]
        })
        
        result = self.detector._detect_double_top(price_data)
        assert result is False

    def test_detect_double_top_failure_no_peaks(self):
        """ダブルトップ検出失敗テスト（ピークなし）"""
        # 単調上昇のデータ
        price_data = pd.DataFrame({
            'high': [100 + i for i in range(30)],
            'low': [99 + i for i in range(30)],
            'close': [100.5 + i for i in range(30)]
        })
        
        result = self.detector._detect_double_top(price_data)
        assert result is False

    def test_find_peaks_high(self):
        """高値ピーク検出テスト"""
        price_data = pd.DataFrame({
            'high': [100, 101, 102, 101, 100, 101, 102, 101, 100],
            'low': [99, 100, 101, 100, 99, 100, 101, 100, 99],
            'close': [100.5, 100.8, 101.5, 100.8, 100.2, 100.8, 101.5, 100.8, 100.2]
        })
        
        peaks = self.detector._find_peaks(price_data, 'high', window=2)
        assert len(peaks) > 0
        assert 2 in peaks  # インデックス2がピーク
        assert 6 in peaks  # インデックス6がピーク

    def test_find_peaks_low(self):
        """安値ピーク検出テスト"""
        price_data = pd.DataFrame({
            'high': [102, 101, 100, 101, 102, 101, 100, 101, 102],
            'low': [101, 100, 99, 100, 101, 100, 99, 100, 101],
            'close': [101.5, 100.8, 100.2, 100.8, 101.5, 100.8, 100.2, 100.8, 101.5]
        })
        
        peaks = self.detector._find_peaks(price_data, 'low', window=2)
        assert len(peaks) > 0
        assert 2 in peaks  # インデックス2がピーク
        assert 6 in peaks  # インデックス6がピーク

    def test_validate_neckline_success(self):
        """ネックライン検証成功テスト"""
        price_data = pd.DataFrame({
            'high': [100, 101, 102, 101, 100, 101, 102, 101, 100],
            'low': [99, 100, 101, 100, 99, 100, 101, 100, 99],
            'close': [100.5, 100.8, 101.5, 100.8, 100.2, 100.8, 101.5, 100.8, 100.2]
        })
        
        peaks = [2, 6]  # ダブルトップのピーク位置
        
        result = self.detector._validate_neckline(price_data, peaks, 'top')
        assert result is True

    def test_validate_neckline_failure_insufficient_peaks(self):
        """ネックライン検証失敗テスト（ピーク不足）"""
        price_data = pd.DataFrame({
            'high': [100, 101, 102],
            'low': [99, 100, 101],
            'close': [100.5, 100.8, 101.5]
        })
        
        peaks = [2]  # ピークが1つだけ
        
        result = self.detector._validate_neckline(price_data, peaks, 'top')
        assert result is False

    def test_calculate_double_pattern_confidence(self):
        """ダブルパターン信頼度計算テスト"""
        conditions_met = {
            "D1": True,
            "H4": True,
            "H1": True,
            "M5": True
        }
        
        confidence = self.detector._calculate_double_pattern_confidence(conditions_met)
        assert 0.6 <= confidence <= 0.95
        assert abs(confidence - 0.8) < 0.001  # 浮動小数点の誤差を考慮

    def test_calculate_double_pattern_confidence_partial(self):
        """ダブルパターン信頼度計算テスト（部分的条件）"""
        conditions_met = {
            "D1": True,
            "H4": True,
            "H1": False,
            "M5": False
        }
        
        confidence = self.detector._calculate_double_pattern_confidence(conditions_met)
        assert 0.6 <= confidence <= 0.95
        # 最小値制限により0.6になる
        assert confidence == 0.6

    def test_detect_integration_success(self):
        """統合検出テスト（成功）"""
        # モックデータの準備
        mock_data = {
            "D1": {"price_data": self._create_double_top_test_data()},
            "H4": {"price_data": self._create_double_top_test_data()},
            "H1": {"price_data": self._create_double_top_test_data()},
            "M5": {"price_data": self._create_double_top_test_data()}
        }
        
        self.mock_utils.validate_timeframe_data.return_value = True
        
        result = self.detector.detect(mock_data)
        
        assert result is not None
        assert result["pattern_number"] == 10
        assert result["pattern_name"] == "ダブルトップ/ボトム検出"
        assert result["confidence_score"] > 0.6

    def test_detect_integration_failure(self):
        """統合検出テスト（失敗）"""
        # モックデータの準備
        mock_data = {
            "D1": {"price_data": pd.DataFrame()},
            "H4": {"price_data": pd.DataFrame()},
            "H1": {"price_data": pd.DataFrame()},
            "M5": {"price_data": pd.DataFrame()}
        }
        
        self.mock_utils.validate_timeframe_data.return_value = False
        
        result = self.detector.detect(mock_data)
        assert result is None

    def _create_double_top_test_data(self) -> pd.DataFrame:
        """ダブルトップパターンのテストデータを作成"""
        data = []
        
        # 最初の上昇
        for i in range(8):
            data.append({
                'high': 100 + i * 0.6,
                'low': 99 + i * 0.6,
                'close': 100.5 + i * 0.6
            })
        
        # 最初のピーク（明確なピーク）
        data.append({
            'high': 105,
            'low': 104,
            'close': 104.5
        })
        
        # 下降（谷を形成）
        for i in range(4):
            data.append({
                'high': 104.5 - i * 0.3,
                'low': 103.5 - i * 0.3,
                'close': 104 - i * 0.3
            })
        
        # 2番目の上昇
        for i in range(4):
            data.append({
                'high': 103.3 + i * 0.4,
                'low': 102.3 + i * 0.4,
                'close': 102.8 + i * 0.4
            })
        
        # 2番目のピーク（最初のピークと同じレベル）
        data.append({
            'high': 105,
            'low': 104,
            'close': 104.5
        })
        
        # さらに数行追加してピークを明確にする
        for i in range(2):
            data.append({
                'high': 104.5 - i * 0.2,
                'low': 103.5 - i * 0.2,
                'close': 104 - i * 0.2
            })
        
        # データ長を20以上にするために追加
        for i in range(3):
            data.append({
                'high': 104.3 - i * 0.1,
                'low': 103.3 - i * 0.1,
                'close': 103.8 - i * 0.1
            })
        
        return pd.DataFrame(data)

    def _create_double_bottom_test_data(self) -> pd.DataFrame:
        """ダブルボトムパターンのテストデータを作成"""
        data = [
            {'high': 105, 'low': 104, 'close': 104.5},
            {'high': 104, 'low': 103, 'close': 103.5},
            {'high': 103, 'low': 102, 'close': 102.5},
            {'high': 102, 'low': 101, 'close': 101.5},
            {'high': 101, 'low': 100, 'close': 100.5},
            {'high': 100, 'low': 99, 'close': 99.5},
            {'high': 99, 'low': 98, 'close': 98.5},
            {'high': 100, 'low': 99, 'close': 99.5},  # 最初のボトム
            {'high': 101, 'low': 100, 'close': 100.5},
            {'high': 102, 'low': 101, 'close': 101.5},
            {'high': 103, 'low': 102, 'close': 102.5},
            {'high': 104, 'low': 103, 'close': 103.5},
            {'high': 103, 'low': 102, 'close': 102.5},
            {'high': 102, 'low': 101, 'close': 101.5},
            {'high': 101, 'low': 100, 'close': 100.5},
            {'high': 100, 'low': 99, 'close': 99.5},
            {'high': 99, 'low': 98, 'close': 98.5},
            {'high': 100, 'low': 99, 'close': 99.5},  # 2番目のボトム
            {'high': 101, 'low': 100, 'close': 100.5},
            {'high': 102, 'low': 101, 'close': 101.5},
            {'high': 103, 'low': 102, 'close': 102.5},
            {'high': 104, 'low': 103, 'close': 103.5},
            {'high': 105, 'low': 104, 'close': 104.5},
        ]
        return pd.DataFrame(data)
