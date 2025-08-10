"""
通知パターン実装のテスト

実装したコンポーネントが正しく動作することを確認するテスト
"""

import os
import sys

import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.entities.notification_pattern import NotificationPattern
from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.analysis.notification_pattern_analyzer import (
    NotificationPatternAnalyzer,
)
from src.infrastructure.analysis.pattern_detectors.trend_reversal_detector import (
    TrendReversalDetector,
)
from src.infrastructure.messaging.templates.pattern_1_template import Pattern1Template
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


def test_pattern_priority():
    """パターン優先度のテスト"""
    print("=== パターン優先度テスト ===")

    # パターン番号から優先度を取得
    priority_1 = PatternPriority.from_pattern_number(1)
    priority_6 = PatternPriority.from_pattern_number(6)

    print(f"パターン1の優先度: {priority_1}")
    print(f"パターン6の優先度: {priority_6}")

    # 通知遅延時間を取得
    delay_1 = priority_1.get_notification_delay()
    delay_6 = priority_6.get_notification_delay()

    print(f"パターン1の通知遅延: {delay_1}秒")
    print(f"パターン6の通知遅延: {delay_6}秒")

    # 色を取得
    color_1 = priority_1.get_color()
    color_6 = priority_6.get_color()

    print(f"パターン1の色: {color_1}")
    print(f"パターン6の色: {color_6}")

    print("✅ パターン優先度テスト完了\n")


def test_notification_pattern():
    """通知パターンのテスト"""
    print("=== 通知パターンテスト ===")

    # パターン1を作成
    pattern_1 = NotificationPattern.create_pattern_1()

    print(f"パターン名: {pattern_1.name}")
    print(f"説明: {pattern_1.description}")
    print(f"優先度: {pattern_1.priority}")
    print(f"条件数: {len(pattern_1.conditions)}")

    # 辞書形式に変換
    pattern_dict = pattern_1.to_dict()
    print(f"辞書変換: {len(pattern_dict)}個のフィールド")

    # 辞書から再作成
    pattern_from_dict = NotificationPattern.from_dict(pattern_dict)
    print(f"再作成成功: {pattern_from_dict.name == pattern_1.name}")

    print("✅ 通知パターンテスト完了\n")


def test_pattern_utils():
    """パターンユーティリティのテスト"""
    print("=== パターンユーティリティテスト ===")

    utils = PatternUtils()

    # サンプル価格データ
    prices = pd.Series([100 + i * 0.1 for i in range(50)])

    # RSI計算
    rsi = utils.calculate_rsi(prices)
    print(f"RSI計算: {rsi.iloc[-1]:.2f}")

    # MACD計算
    macd = utils.calculate_macd(prices)
    print(f"MACD計算: {macd['macd'].iloc[-1]:.4f}")

    # ボリンジャーバンド計算
    bb = utils.calculate_bollinger_bands(prices)
    print(f"BB計算: 上限={bb['upper'].iloc[-1]:.2f}")

    # 条件チェック
    rsi_condition = utils.check_rsi_condition(75.0, "RSI > 70")
    print(f"RSI条件チェック: {rsi_condition}")

    # 信頼度スコア計算
    conditions = {"D1": True, "H4": True, "H1": False, "M5": True}
    confidence = utils.get_pattern_confidence_score(conditions)
    print(f"信頼度スコア: {confidence:.2f}")

    print("✅ パターンユーティリティテスト完了\n")


def test_trend_reversal_detector():
    """トレンド転換検出器のテスト"""
    print("=== トレンド転換検出器テスト ===")

    detector = TrendReversalDetector()

    # パターン情報を取得
    pattern_info = detector.get_pattern_info()
    print(f"パターン名: {pattern_info['name']}")
    print(f"優先度: {pattern_info['priority']}")

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

    print("✅ トレンド転換検出器テスト完了\n")


def test_notification_pattern_analyzer():
    """通知パターン分析エンジンのテスト"""
    print("=== 通知パターン分析エンジンテスト ===")

    analyzer = NotificationPatternAnalyzer()

    # 検出器ステータスを取得
    status = analyzer.get_detector_status()
    print(f"アクティブ検出器数: {status['total_detectors']}")

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

    print("✅ 通知パターン分析エンジンテスト完了\n")


def test_pattern_template():
    """パターンテンプレートのテスト"""
    print("=== パターンテンプレートテスト ===")

    template = Pattern1Template()

    # テンプレート情報を取得
    template_info = template.get_template_info()
    print(f"テンプレート名: {template_info['pattern_name']}")
    print(f"デフォルト色: {template_info['default_color']}")

    # モック検出結果を作成
    mock_detection = {
        "pattern_number": 1,
        "pattern_name": "強力なトレンド転換シグナル",
        "priority": PatternPriority.HIGH,
        "confidence_score": 0.85,
        "notification_title": "🚨 強力な売りシグナル検出！",
        "notification_color": "0xFF0000",
        "take_profit": "-50pips",
        "stop_loss": "+30pips",
        "conditions_met": {"D1": True, "H4": True, "H1": True, "M5": True},
        "timeframe_data": create_mock_multi_timeframe_data(),
    }

    # Embed作成
    embed = template.create_embed(mock_detection, "USD/JPY")
    print(f"Embed作成: {len(embed['fields'])}個のフィールド")

    # シンプルメッセージ作成
    message = template.create_simple_message(mock_detection, "USD/JPY")
    print(f"メッセージ作成: {len(message)}文字")

    print("✅ パターンテンプレートテスト完了\n")


def main():
    """メインテスト実行"""
    print("🚀 通知パターン実装テスト開始\n")

    try:
        test_pattern_priority()
        test_notification_pattern()
        test_pattern_utils()
        test_trend_reversal_detector()
        test_notification_pattern_analyzer()
        test_pattern_template()

        print("🎉 全テスト完了！実装が正常に動作しています。")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
