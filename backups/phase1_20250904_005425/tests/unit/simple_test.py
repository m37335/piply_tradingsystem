#!/usr/bin/env python3
"""
シンプルなダブルトップテスト
"""

import pandas as pd

from src.infrastructure.analysis.pattern_detectors.double_top_bottom_detector import (
    DoubleTopBottomDetector,
)


def create_simple_double_top():
    """シンプルなダブルトップデータを作成"""
    data = [
        {"high": 100, "low": 99, "close": 99.5},
        {"high": 101, "low": 100, "close": 100.5},
        {"high": 102, "low": 101, "close": 101.5},
        {"high": 103, "low": 102, "close": 102.5},
        {"high": 104, "low": 103, "close": 103.5},
        {"high": 105, "low": 104, "close": 104.5},  # 最初のピーク
        {"high": 104, "low": 103, "close": 103.5},
        {"high": 103, "low": 102, "close": 102.5},
        {"high": 102, "low": 101, "close": 101.5},
        {"high": 101, "low": 100, "close": 100.5},
        {"high": 102, "low": 101, "close": 101.5},
        {"high": 103, "low": 102, "close": 102.5},
        {"high": 104, "low": 103, "close": 103.5},
        {"high": 105, "low": 104, "close": 104.5},  # 2番目のピーク
        {"high": 104, "low": 103, "close": 103.5},
        {"high": 103, "low": 102, "close": 102.5},
        {"high": 102, "low": 101, "close": 101.5},
        {"high": 101, "low": 100, "close": 100.5},
        {"high": 100, "low": 99, "close": 99.5},
        {"high": 99, "low": 98, "close": 98.5},
        {"high": 98, "low": 97, "close": 97.5},
    ]
    return pd.DataFrame(data)


def test_simple_double_top():
    """シンプルなダブルトップをテスト"""
    detector = DoubleTopBottomDetector()
    price_data = create_simple_double_top()

    print("シンプルなダブルトップテストデータ:")
    print(f"データ数: {len(price_data)}")
    print(f"最小データ要件: 20")

    # データ長チェック
    if len(price_data) < 20:
        print("❌ データ不足のため、ダブルトップ検出は失敗します")
        return

    # ピーク検出
    peaks = detector._find_peaks(price_data, "high", window=2)
    print(f"\n検出されたピーク: {peaks}")

    if len(peaks) >= 2:
        # ピーク間の距離を確認
        recent_peaks = peaks[-2:]
        peak_distance = recent_peaks[1] - recent_peaks[0]
        print(f"ピーク間の距離: {peak_distance}")
        print(f"最小距離要件: {detector.min_peak_distance}")

        # ピークの高さを確認
        peak1_high = price_data.iloc[recent_peaks[0]]["high"]
        peak2_high = price_data.iloc[recent_peaks[1]]["high"]
        height_diff = abs(peak1_high - peak2_high) / peak1_high
        print(f"ピーク1の高さ: {peak1_high}")
        print(f"ピーク2の高さ: {peak2_high}")
        print(f"高さの差率: {height_diff}")
        print(f"許容誤差: {detector.peak_tolerance}")

        # ネックライン検証
        neckline_result = detector._validate_neckline(price_data, recent_peaks, "top")
        print(f"ネックライン検証結果: {neckline_result}")

    # ダブルトップ検出
    result = detector._detect_double_top(price_data)
    print(f"\nダブルトップ検出結果: {result}")


if __name__ == "__main__":
    test_simple_double_top()
