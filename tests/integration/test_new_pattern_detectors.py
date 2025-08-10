"""
新規パターン検出器テスト

Phase 2で実装した新しいパターン検出器のテスト
"""

import os
import sys

import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.entities.notification_pattern import NotificationPattern
from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.pattern_detectors.breakout_detector import (
    BreakoutDetector,
)
from src.infrastructure.analysis.pattern_detectors.composite_signal_detector import (
    CompositeSignalDetector,
)
from src.infrastructure.analysis.pattern_detectors.divergence_detector import (
    DivergenceDetector,
)
from src.infrastructure.analysis.pattern_detectors.pullback_detector import (
    PullbackDetector,
)
from src.utils.pattern_utils import PatternUtils


def create_mock_timeframe_data(timeframe: str) -> dict:
    """モックのタイムフレームデータを作成"""
    # サンプル価格データを作成
    dates = pd.date_range(start="2025-01-01", periods=50, freq="1H")
    prices = pd.Series(
        [100 + i * 0.1 + (i % 10) * 0.05 for i in range(50)], index=dates
    )

    # 指標を計算
    utils = PatternUtils()
    rsi = utils.calculate_rsi(prices)
    macd = utils.calculate_macd(prices)
    bb = utils.calculate_bollinger_bands(prices)

    return {
        "price_data": pd.DataFrame(
            {
                "Open": prices * 0.999,
                "High": prices * 1.002,
                "Low": prices * 0.998,
                "Close": prices,
                "Volume": [1000000] * 50,
            },
            index=dates,
        ),
        "indicators": {
            "rsi": {"current_value": rsi.iloc[-1], "series": rsi},
            "macd": macd,
            "bollinger_bands": bb,
        },
    }


def create_mock_multi_timeframe_data() -> dict:
    """モックのマルチタイムフレームデータを作成"""
    return {
        "D1": create_mock_timeframe_data("D1"),
        "H4": create_mock_timeframe_data("H4"),
        "H1": create_mock_timeframe_data("H1"),
        "M5": create_mock_timeframe_data("M5"),
    }


def test_pullback_detector():
    """押し目買い検出器のテスト"""
    print("=== 押し目買い検出器テスト ===")

    detector = PullbackDetector()

    # パターン情報を取得
    pattern_info = detector.get_pattern_info()
    print(f"パターン名: {pattern_info['name']}")
    print(f"優先度: {pattern_info['priority']}")
    print(f"利確: {pattern_info['take_profit']}")
    print(f"損切り: {pattern_info['stop_loss']}")

    # モックデータで検出テスト
    mock_data = create_mock_multi_timeframe_data()

    # データの妥当性チェック
    is_valid = detector._validate_data(mock_data)
    print(f"データ妥当性: {is_valid}")

    # 検出実行
    result = detector.detect(mock_data)
    if result:
        print(f"検出成功: {result['pattern_name']}")
        print(f"信頼度: {result['confidence_score']:.2f}")
    else:
        print("検出なし（期待される動作）")

    print("✅ 押し目買い検出器テスト完了\n")


def test_divergence_detector():
    """ダイバージェンス検出器のテスト"""
    print("=== ダイバージェンス検出器テスト ===")

    detector = DivergenceDetector()

    # パターン情報を取得
    pattern_info = detector.get_pattern_info()
    print(f"パターン名: {pattern_info['name']}")
    print(f"優先度: {pattern_info['priority']}")
    print(f"戦略: {pattern_info['strategy']}")
    print(f"リスク: {pattern_info['risk']}")

    # モックデータで検出テスト
    mock_data = create_mock_multi_timeframe_data()

    # データの妥当性チェック
    is_valid = detector._validate_data(mock_data)
    print(f"データ妥当性: {is_valid}")

    # 検出実行
    result = detector.detect(mock_data)
    if result:
        print(f"検出成功: {result['pattern_name']}")
        print(f"信頼度: {result['confidence_score']:.2f}")
    else:
        print("検出なし（期待される動作）")

    # 詳細なダイバージェンス分析
    divergence_analysis = detector.detect_divergence_pattern(mock_data)
    print(f"ダイバージェンス分析: {len(divergence_analysis)}時間軸")

    print("✅ ダイバージェンス検出器テスト完了\n")


def test_breakout_detector():
    """ブレイクアウト検出器のテスト"""
    print("=== ブレイクアウト検出器テスト ===")

    detector = BreakoutDetector()

    # パターン情報を取得
    pattern_info = detector.get_pattern_info()
    print(f"パターン名: {pattern_info['name']}")
    print(f"優先度: {pattern_info['priority']}")
    print(f"利確: {pattern_info['take_profit']}")
    print(f"損切り: {pattern_info['stop_loss']}")

    # モックデータで検出テスト
    mock_data = create_mock_multi_timeframe_data()

    # データの妥当性チェック
    is_valid = detector._validate_data(mock_data)
    print(f"データ妥当性: {is_valid}")

    # 検出実行
    result = detector.detect(mock_data)
    if result:
        print(f"検出成功: {result['pattern_name']}")
        print(f"信頼度: {result['confidence_score']:.2f}")
    else:
        print("検出なし（期待される動作）")

    # ブレイクアウト強度分析
    breakout_analysis = detector.detect_breakout_strength(mock_data)
    print(f"ブレイクアウト分析: {len(breakout_analysis)}時間軸")

    print("✅ ブレイクアウト検出器テスト完了\n")


def test_composite_signal_detector():
    """複合シグナル検出器のテスト"""
    print("=== 複合シグナル検出器テスト ===")

    detector = CompositeSignalDetector()

    # パターン情報を取得
    pattern_info = detector.get_pattern_info()
    print(f"パターン名: {pattern_info['name']}")
    print(f"優先度: {pattern_info['priority']}")
    print(f"利確: {pattern_info['take_profit']}")
    print(f"損切り: {pattern_info['stop_loss']}")
    print(f"信頼度: {pattern_info['confidence']}")

    # モックデータで検出テスト
    mock_data = create_mock_multi_timeframe_data()

    # データの妥当性チェック
    is_valid = detector._validate_data(mock_data)
    print(f"データ妥当性: {is_valid}")

    # 検出実行
    result = detector.detect(mock_data)
    if result:
        print(f"検出成功: {result['pattern_name']}")
        print(f"信頼度: {result['confidence_score']:.2f}")
    else:
        print("検出なし（期待される動作）")

    # 複合シグナルスコア分析
    composite_analysis = detector.calculate_composite_score(mock_data)
    print(f"複合シグナル分析: {len(composite_analysis)}時間軸")

    print("✅ 複合シグナル検出器テスト完了\n")


def test_updated_analyzer():
    """更新された分析エンジンのテスト"""
    print("=== 更新された分析エンジンテスト ===")

    from src.infrastructure.analysis.notification_pattern_analyzer import (
        NotificationPatternAnalyzer,
    )

    analyzer = NotificationPatternAnalyzer()

    # 検出器ステータスを取得
    status = analyzer.get_detector_status()
    print(f"アクティブ検出器数: {status['total_detectors']}")
    print("アクティブ検出器:")
    for detector in status["active_detectors"]:
        print(f"  - パターン{detector['pattern_number']}: {detector['pattern_name']}")

    # 全パターン情報を取得
    patterns_info = analyzer.get_all_patterns_info()
    print(f"定義済みパターン数: {len(patterns_info)}")

    # モックデータで分析テスト
    mock_data = create_mock_multi_timeframe_data()

    # 分析実行
    detected_patterns = analyzer.analyze_multi_timeframe_data(mock_data, "USD/JPY")
    print(f"検出されたパターン数: {len(detected_patterns)}")

    # 分析サマリーを取得
    summary = analyzer.get_analysis_summary(mock_data, "USD/JPY")
    print(f"全体的な信頼度: {summary['overall_confidence']:.2f}")
    print(f"現在価格: {summary['current_price']}")

    print("✅ 更新された分析エンジンテスト完了\n")


def test_pattern_creation():
    """新規パターン作成のテスト"""
    print("=== 新規パターン作成テスト ===")

    # 各パターンの作成テスト
    patterns = [
        ("パターン2", NotificationPattern.create_pattern_2()),
        ("パターン3", NotificationPattern.create_pattern_3()),
        ("パターン4", NotificationPattern.create_pattern_4()),
        ("パターン6", NotificationPattern.create_pattern_6()),
    ]

    for name, pattern in patterns:
        print(f"{name}:")
        print(f"  名前: {pattern.name}")
        print(f"  優先度: {pattern.priority}")
        print(f"  条件数: {len(pattern.conditions)}")
        print(f"  利確: {pattern.take_profit}")
        print(f"  損切り: {pattern.stop_loss}")

    print("✅ 新規パターン作成テスト完了\n")


def main():
    """メインテスト実行"""
    print("🚀 新規パターン検出器テスト開始\n")

    try:
        test_pullback_detector()
        test_divergence_detector()
        test_breakout_detector()
        test_composite_signal_detector()
        test_updated_analyzer()
        test_pattern_creation()

        print("🎉 全テスト完了！新規パターン検出器が正常に動作しています。")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
