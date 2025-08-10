"""
Phase 4 統合テスト

cronスクリプト、通知マネージャー統合、パフォーマンス最適化の統合テスト
"""

import asyncio
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.notification_cron import NotificationCron
from src.infrastructure.notification_manager_integration import (
    NotificationManagerIntegration,
)
from src.infrastructure.performance_optimizer import PerformanceOptimizer


async def test_notification_cron():
    """通知cronスクリプトのテスト"""
    print("=== 通知cronスクリプトテスト ===")

    cron = NotificationCron()

    # ステータスサマリーを取得
    status = cron.get_status_summary()
    print("cronステータス:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # 単発チェックを実行
    print("\n単発チェックを実行中...")
    await cron.run_single_check()

    print("✅ cronスクリプトテスト完了")


async def test_notification_manager_integration():
    """通知マネージャー統合のテスト"""
    print("\n=== 通知マネージャー統合テスト ===")

    integration = NotificationManagerIntegration()

    # 統合ステータスを取得
    status = integration.get_integration_status()
    print("統合ステータス:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # モック検出結果を作成
    mock_detections = [
        {
            "pattern_number": 1,
            "pattern_name": "強力なトレンド転換シグナル",
            "priority": PatternPriority.HIGH,
            "confidence_score": 0.85,
            "notification_title": "🚨 強力な売りシグナル検出！",
            "notification_color": "0xFF0000",
            "take_profit": "-50pips",
            "stop_loss": "+30pips",
        },
        {
            "pattern_number": 2,
            "pattern_name": "押し目買いチャンス",
            "priority": PatternPriority.MEDIUM,
            "confidence_score": 0.75,
            "notification_title": "📈 押し目買いチャンス！",
            "notification_color": "0x00FF00",
            "take_profit": "+80pips",
            "stop_loss": "-40pips",
        },
        {
            "pattern_number": 6,
            "pattern_name": "複合シグナル強化",
            "priority": PatternPriority.VERY_HIGH,
            "confidence_score": 0.95,
            "notification_title": "💪 複合シグナル強化！",
            "notification_color": "0x800080",
            "take_profit": "+120pips",
            "stop_loss": "-60pips",
        },
    ]

    # 各検出結果を処理
    for i, detection in enumerate(mock_detections, 1):
        print(f"\n検出結果{i}を処理中...")
        result = await integration.process_detection_result(detection, "USD/JPY")
        print(f"  処理結果: {result}")

    print("✅ 通知マネージャー統合テスト完了")


async def test_performance_optimizer():
    """パフォーマンス最適化のテスト"""
    print("\n=== パフォーマンス最適化テスト ===")

    optimizer = PerformanceOptimizer()

    # 単一データ取得テスト
    print("単一データ取得テスト...")
    data = await optimizer.get_optimized_data("USD/JPY", "D1")
    print(f"  データ取得: {len(data)}個のフィールド")

    # 並列分析テスト
    print("\n並列分析テスト...")
    currency_pairs = ["USD/JPY", "EUR/USD", "GBP/USD"]
    timeframes = ["D1", "H4", "H1"]

    results = await optimizer.analyze_multiple_currency_pairs(
        currency_pairs, timeframes
    )
    print(f"  並列分析結果: {len(results)}通貨ペア")

    # パフォーマンス統計
    print("\nパフォーマンス統計:")
    stats = optimizer.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # メモリ最適化
    print("\nメモリ最適化実行...")
    optimizer.optimize_memory_usage()

    print("✅ パフォーマンス最適化テスト完了")


async def test_integrated_workflow():
    """統合ワークフローのテスト"""
    print("\n=== 統合ワークフローテスト ===")

    # 各コンポーネントを初期化
    cron = NotificationCron()
    integration = NotificationManagerIntegration()
    optimizer = PerformanceOptimizer()

    print("統合ワークフロー開始...")

    # 1. 最適化されたデータ取得
    print("1. 最適化されたデータ取得...")
    multi_timeframe_data = await optimizer.get_optimized_data("USD/JPY", "D1")

    # 2. パターン分析
    print("2. パターン分析...")
    detected_patterns = cron.analyzer.analyze_multi_timeframe_data(
        {"D1": multi_timeframe_data}, "USD/JPY"
    )

    if detected_patterns:
        print(f"  検出されたパターン: {len(detected_patterns)}個")

        # 3. 通知処理
        print("3. 通知処理...")
        for pattern in detected_patterns:
            result = await integration.process_detection_result(pattern, "USD/JPY")
            print(f"  通知結果: {result}")
    else:
        print("  パターンは検出されませんでした")

    # 4. パフォーマンス統計
    print("4. パフォーマンス統計...")
    stats = optimizer.get_performance_stats()
    print(f"  キャッシュヒット率: {stats.get('cache_hit_rate_percent', 0):.1f}%")
    print(f"  平均レスポンス時間: {stats.get('average_response_time', 0):.3f}秒")

    print("✅ 統合ワークフローテスト完了")


async def test_error_handling():
    """エラーハンドリングのテスト"""
    print("\n=== エラーハンドリングテスト ===")

    integration = NotificationManagerIntegration()

    # 無効なパターン番号
    print("無効なパターン番号のテスト...")
    invalid_detection = {
        "pattern_number": 999,
        "pattern_name": "無効なパターン",
        "priority": PatternPriority.LOW,
    }
    result = await integration.process_detection_result(invalid_detection, "USD/JPY")
    print(f"  結果: {result}")

    # 無効な優先度
    print("無効な優先度のテスト...")
    low_priority_detection = {
        "pattern_number": 1,
        "pattern_name": "低優先度パターン",
        "priority": PatternPriority.LOW,
    }
    result = await integration.process_detection_result(
        low_priority_detection, "USD/JPY"
    )
    print(f"  結果: {result}")

    print("✅ エラーハンドリングテスト完了")


async def main():
    """メイン関数"""
    print("🚀 Phase 4 統合テスト開始")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 各テストを実行
        await test_notification_cron()
        await test_notification_manager_integration()
        await test_performance_optimizer()
        await test_integrated_workflow()
        await test_error_handling()

        print(f"\n🎉 Phase 4 統合テスト完了")
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n❌ テスト中にエラーが発生しました: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
