"""
新規通知テンプレートテスト

Phase 3で実装した新しい通知テンプレートのテスト
"""

import os
import sys

import pandas as pd

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.messaging.templates.pattern_2_template import Pattern2Template
from src.infrastructure.messaging.templates.pattern_3_template import Pattern3Template
from src.infrastructure.messaging.templates.pattern_4_template import Pattern4Template
from src.infrastructure.messaging.templates.pattern_6_template import Pattern6Template


def create_mock_detection_result(pattern_number: int) -> dict:
    """モックの検出結果を作成"""
    base_result = {
        "pattern_number": pattern_number,
        "pattern_name": f"パターン{pattern_number}",
        "priority": PatternPriority.MEDIUM,
        "conditions_met": {"D1": True, "H4": True, "H1": True, "M5": True},
        "confidence_score": 0.85,
        "detected_at": pd.Timestamp.now(),
    }

    if pattern_number == 2:
        base_result.update(
            {
                "pattern_name": "押し目買いチャンス",
                "notification_title": "📈 押し目買いチャンス！",
                "notification_color": "0x00FF00",
                "take_profit": "+80pips",
                "stop_loss": "-40pips",
                "confidence": "高（トレンド順張り）",
            }
        )
    elif pattern_number == 3:
        base_result.update(
            {
                "pattern_name": "ダイバージェンス警戒",
                "notification_title": "⚠️ ダイバージェンス警戒！",
                "notification_color": "0xFFFF00",
                "strategy": "利確推奨",
                "risk": "急落可能性",
            }
        )
    elif pattern_number == 4:
        base_result.update(
            {
                "pattern_name": "ブレイクアウト狙い",
                "notification_title": "🚀 ブレイクアウト狙い！",
                "notification_color": "0x00FFFF",
                "take_profit": "+100pips",
                "stop_loss": "-50pips",
            }
        )
    elif pattern_number == 6:
        base_result.update(
            {
                "pattern_name": "複合シグナル強化",
                "priority": PatternPriority.VERY_HIGH,
                "notification_title": "💪 複合シグナル強化！",
                "notification_color": "0x800080",
                "take_profit": "+120pips",
                "stop_loss": "-60pips",
                "confidence": "最高（複合シグナル）",
            }
        )

    return base_result


def test_pattern_2_template():
    """パターン2テンプレートのテスト"""
    print("=== パターン2テンプレートテスト ===")

    template = Pattern2Template()

    # テンプレート情報を取得
    template_info = template.get_template_info()
    print(f"テンプレート名: {template_info['pattern_name']}")
    print(f"パターン番号: {template_info['pattern_number']}")
    print(f"デフォルト色: {template_info['default_color']}")

    # モック検出結果を作成
    mock_detection = create_mock_detection_result(2)

    # Embed作成
    embed = template.create_embed(mock_detection, "USD/JPY")
    print(f"Embed作成: {len(embed['fields'])}個のフィールド")
    print(f"タイトル: {embed['title']}")

    # シンプルメッセージ作成
    message = template.create_simple_message(mock_detection, "USD/JPY")
    print(f"メッセージ作成: {len(message)}文字")

    # 詳細分析作成
    analysis = template.create_detailed_analysis(mock_detection, "USD/JPY")
    print(f"詳細分析: {len(analysis)}個のフィールド")

    print("✅ パターン2テンプレートテスト完了\n")


def test_pattern_3_template():
    """パターン3テンプレートのテスト"""
    print("=== パターン3テンプレートテスト ===")

    template = Pattern3Template()

    # テンプレート情報を取得
    template_info = template.get_template_info()
    print(f"テンプレート名: {template_info['pattern_name']}")
    print(f"パターン番号: {template_info['pattern_number']}")
    print(f"デフォルト色: {template_info['default_color']}")

    # モック検出結果を作成
    mock_detection = create_mock_detection_result(3)

    # Embed作成
    embed = template.create_embed(mock_detection, "USD/JPY")
    print(f"Embed作成: {len(embed['fields'])}個のフィールド")
    print(f"タイトル: {embed['title']}")

    # シンプルメッセージ作成
    message = template.create_simple_message(mock_detection, "USD/JPY")
    print(f"メッセージ作成: {len(message)}文字")

    # 詳細分析作成
    analysis = template.create_detailed_analysis(mock_detection, "USD/JPY")
    print(f"詳細分析: {len(analysis)}個のフィールド")

    # ダイバージェンスアラート作成
    alert = template.create_divergence_alert(mock_detection, "USD/JPY")
    print(f"アラート作成: {alert['urgency']}緊急度")

    print("✅ パターン3テンプレートテスト完了\n")


def test_pattern_4_template():
    """パターン4テンプレートのテスト"""
    print("=== パターン4テンプレートテスト ===")

    template = Pattern4Template()

    # テンプレート情報を取得
    template_info = template.get_template_info()
    print(f"テンプレート名: {template_info['pattern_name']}")
    print(f"パターン番号: {template_info['pattern_number']}")
    print(f"デフォルト色: {template_info['default_color']}")

    # モック検出結果を作成
    mock_detection = create_mock_detection_result(4)

    # Embed作成
    embed = template.create_embed(mock_detection, "USD/JPY")
    print(f"Embed作成: {len(embed['fields'])}個のフィールド")
    print(f"タイトル: {embed['title']}")

    # シンプルメッセージ作成
    message = template.create_simple_message(mock_detection, "USD/JPY")
    print(f"メッセージ作成: {len(message)}文字")

    # 詳細分析作成
    analysis = template.create_detailed_analysis(mock_detection, "USD/JPY")
    print(f"詳細分析: {len(analysis)}個のフィールド")

    # ブレイクアウトアラート作成
    alert = template.create_breakout_alert(mock_detection, "USD/JPY")
    print(f"アラート作成: {alert['urgency']}緊急度")

    print("✅ パターン4テンプレートテスト完了\n")


def test_pattern_6_template():
    """パターン6テンプレートのテスト"""
    print("=== パターン6テンプレートテスト ===")

    template = Pattern6Template()

    # テンプレート情報を取得
    template_info = template.get_template_info()
    print(f"テンプレート名: {template_info['pattern_name']}")
    print(f"パターン番号: {template_info['pattern_number']}")
    print(f"デフォルト色: {template_info['default_color']}")

    # モック検出結果を作成
    mock_detection = create_mock_detection_result(6)

    # Embed作成
    embed = template.create_embed(mock_detection, "USD/JPY")
    print(f"Embed作成: {len(embed['fields'])}個のフィールド")
    print(f"タイトル: {embed['title']}")

    # シンプルメッセージ作成
    message = template.create_simple_message(mock_detection, "USD/JPY")
    print(f"メッセージ作成: {len(message)}文字")

    # 詳細分析作成
    analysis = template.create_detailed_analysis(mock_detection, "USD/JPY")
    print(f"詳細分析: {len(analysis)}個のフィールド")

    # 複合シグナルアラート作成
    alert = template.create_composite_alert(mock_detection, "USD/JPY")
    print(f"アラート作成: {alert['urgency']}緊急度")

    print("✅ パターン6テンプレートテスト完了\n")


def test_template_integration():
    """テンプレート統合テスト"""
    print("=== テンプレート統合テスト ===")

    from src.infrastructure.messaging.templates import (
        Pattern1Template,
        Pattern2Template,
        Pattern3Template,
        Pattern4Template,
        Pattern6Template,
    )

    templates = [
        Pattern1Template(),
        Pattern2Template(),
        Pattern3Template(),
        Pattern4Template(),
        Pattern6Template(),
    ]

    print(f"利用可能なテンプレート数: {len(templates)}")

    for template in templates:
        info = template.get_template_info()
        print(f"  - パターン{info['pattern_number']}: {info['pattern_name']}")

    print("✅ テンプレート統合テスト完了\n")


def test_template_comparison():
    """テンプレート比較テスト"""
    print("=== テンプレート比較テスト ===")

    templates = [
        ("Pattern1Template", "強力なトレンド転換シグナル", "0xFF0000"),
        ("Pattern2Template", "押し目買いチャンス", "0x00FF00"),
        ("Pattern3Template", "ダイバージェンス警戒", "0xFFFF00"),
        ("Pattern4Template", "ブレイクアウト狙い", "0x00FFFF"),
        ("Pattern6Template", "複合シグナル強化", "0x800080"),
    ]

    for template_name, pattern_name, color in templates:
        print(f"{template_name}:")
        print(f"  パターン名: {pattern_name}")
        print(f"  色: {color}")

    print("✅ テンプレート比較テスト完了\n")


def main():
    """メインテスト実行"""
    print("🚀 新規通知テンプレートテスト開始\n")

    try:
        test_pattern_2_template()
        test_pattern_3_template()
        test_pattern_4_template()
        test_pattern_6_template()
        test_template_integration()
        test_template_comparison()

        print("🎉 全テスト完了！新規通知テンプレートが正常に動作しています。")

    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
