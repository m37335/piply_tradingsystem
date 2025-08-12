#!/usr/bin/env python3
"""
ダブルボトムのデバッグ用スクリプト
"""

from tests.unit.test_double_top_bottom_detector import TestDoubleTopBottomDetector

def debug_double_bottom():
    """ダブルボトムをデバッグ"""
    test_class = TestDoubleTopBottomDetector()
    test_class.setup_method()
    
    # ダブルボトムテストデータを作成
    price_data = test_class._create_double_bottom_test_data()
    print("ダブルボトムテストデータ:")
    print(f"データ数: {len(price_data)}")
    
    # _detect_double_bottomの各ステップをデバッグ
    detector = test_class.detector
    
    # ステップ1: データ長チェック
    print(f"\nステップ1: データ長チェック")
    print(f"データ長: {len(price_data)}, 最小要件: 20")
    if len(price_data) < 20:
        print("❌ データ不足")
        return
    else:
        print("✅ データ長OK")
    
    # ステップ2: ピーク検出
    print(f"\nステップ2: ピーク検出")
    peaks = detector._find_peaks(price_data, 'low', window=3)
    print(f"検出されたピーク: {peaks}")
    if len(peaks) < 2:
        print("❌ ピーク不足")
        return
    else:
        print("✅ ピーク数OK")
    
    # ステップ3: 最新の2つのピークを取得
    print(f"\nステップ3: 最新の2つのピーク")
    recent_peaks = peaks[-2:]
    print(f"最新のピーク: {recent_peaks}")
    
    # ステップ4: ピーク間の距離をチェック
    print(f"\nステップ4: ピーク間の距離チェック")
    peak_distance = recent_peaks[1] - recent_peaks[0]
    print(f"ピーク間の距離: {peak_distance}, 最小要件: {detector.min_peak_distance}")
    if peak_distance < detector.min_peak_distance:
        print("❌ ピーク間距離不足")
        return
    else:
        print("✅ ピーク間距離OK")
    
    # ステップ5: ピークの高さが類似しているかチェック
    print(f"\nステップ5: ピーク高さ類似性チェック")
    peak1_low = price_data.iloc[recent_peaks[0]]['low']
    peak2_low = price_data.iloc[recent_peaks[1]]['low']
    height_diff = abs(peak1_low - peak2_low) / peak1_low
    print(f"ピーク1の安値: {peak1_low}")
    print(f"ピーク2の安値: {peak2_low}")
    print(f"高さの差率: {height_diff}, 許容誤差: {detector.peak_tolerance}")
    if height_diff > detector.peak_tolerance:
        print("❌ ピーク高さの差が大きすぎる")
        return
    else:
        print("✅ ピーク高さ類似性OK")
    
    # ステップ6: ネックラインの検証
    print(f"\nステップ6: ネックライン検証")
    neckline_result = detector._validate_neckline(price_data, recent_peaks, 'bottom')
    print(f"ネックライン検証結果: {neckline_result}")
    if not neckline_result:
        print("❌ ネックライン検証失敗")
        return
    else:
        print("✅ ネックライン検証OK")
    
    print("\n🎉 全ステップ成功！ダブルボトムが検出されるはずです。")

if __name__ == "__main__":
    debug_double_bottom()
