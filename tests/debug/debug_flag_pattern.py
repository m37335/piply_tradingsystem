#!/usr/bin/env python3
"""
フラッグパターンのデバッグ用スクリプト
"""

from tests.unit.test_flag_pattern_detector import TestFlagPatternDetector


def debug_flag_pattern():
    """フラッグパターンをデバッグ"""
    test_class = TestFlagPatternDetector()
    test_class.setup_method()

    # ブルフラッグテストデータを作成
    price_data = test_class._create_bull_flag_test_data()
    print("ブルフラッグテストデータ:")
    print(f"データ数: {len(price_data)}")

    # _detect_bull_flagの各ステップをデバッグ
    detector = test_class.detector

    # ステップ1: データ長チェック
    print(f"\nステップ1: データ長チェック")
    print(f"データ長: {len(price_data)}, 最小要件: 20")
    if len(price_data) < 20:
        print("❌ データ不足")
        return
    else:
        print("✅ データ長OK")

    # ステップ2: フラッグポール識別
    print(f"\nステップ2: フラッグポール識別")
    pole_data = detector._identify_flagpole(price_data)
    if pole_data is None:
        print("❌ フラッグポール識別失敗")
        return
    else:
        print("✅ フラッグポール識別成功")
        print(f"ポールデータ: {pole_data}")

    # ステップ3: フラッグ識別
    print(f"\nステップ3: フラッグ識別")
    flag_data = detector._identify_flag(price_data, pole_data["end_index"])
    if flag_data is None:
        print("❌ フラッグ識別失敗")
        return
    else:
        print("✅ フラッグ識別成功")
        print(f"フラッグデータ: {flag_data}")

    # ステップ4: フラッグブレイクアウト検証
    print(f"\nステップ4: フラッグブレイクアウト検証")

    # ブレイクアウト検証の詳細
    flag_end = flag_data["end_index"]
    print(f"フラッグ終了位置: {flag_end}")
    print(f"データ長: {len(price_data)}")

    if flag_end >= len(price_data):
        print("❌ ブレイクアウト後のデータが不足")
        return

    # フラッグの高値・安値を確認
    flag_high = price_data.iloc[flag_data["start_index"] : flag_data["end_index"]][
        "high"
    ].max()
    flag_low = price_data.iloc[flag_data["start_index"] : flag_data["end_index"]][
        "low"
    ].min()
    print(f"フラッグ高値: {flag_high}")
    print(f"フラッグ安値: {flag_low}")

    # ブレイクアウト後の価格を確認
    breakout_price = price_data.iloc[flag_end]["close"]
    print(f"ブレイクアウト後価格: {breakout_price}")

    # ブレイクアウト条件をチェック
    up_breakout = breakout_price > flag_high
    down_breakout = breakout_price < flag_low
    print(f"上向きブレイクアウト: {up_breakout}")
    print(f"下向きブレイクアウト: {down_breakout}")

    breakout_result = detector._validate_flag_breakout(price_data, flag_data)
    print(f"ブレイクアウト検証結果: {breakout_result}")
    if not breakout_result:
        print("❌ ブレイクアウト検証失敗")
        return
    else:
        print("✅ ブレイクアウト検証成功")

    print("\n🎉 全ステップ成功！ブルフラッグが検出されるはずです。")


if __name__ == "__main__":
    debug_flag_pattern()
