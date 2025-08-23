"""
データ分析サービステストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.entities import EconomicEventFactory
from src.domain.services.data_analysis import (
    DataAnalysisService,
    ForecastChangeDetector,
    SurpriseCalculator,
    EventFilter
)


async def test_data_analysis_components():
    """データ分析コンポーネントの個別テスト"""
    print("=== データ分析コンポーネントテスト ===")

    try:
        # テスト用データの作成
        factory = EconomicEventFactory()
        
        # 1. ForecastChangeDetectorテスト
        change_detector = ForecastChangeDetector()
        old_events = [
            factory.create_from_dict({
                "event_id": "test_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 2.5,
                "previous_value": 2.3
            })
        ]
        
        new_events = [
            factory.create_from_dict({
                "event_id": "test_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 2.8,  # 変更
                "previous_value": 2.3
            })
        ]
        
        changes = await change_detector.detect_changes(old_events, new_events)
        print(f"✅ ForecastChangeDetectorテスト完了: {len(changes)}件の変更検出")

        # 2. SurpriseCalculatorテスト
        surprise_calculator = SurpriseCalculator()
        test_event = factory.create_from_dict({
            "event_id": "test_002",
            "date_utc": datetime.utcnow(),
            "country": "united states",
            "event_name": "Non-Farm Payrolls",
            "importance": "high",
            "actual_value": 200000,
            "forecast_value": 180000,
            "previous_value": 175000
        })
        
        surprise_data = await surprise_calculator.calculate_surprise(test_event)
        print(f"✅ SurpriseCalculatorテスト完了: {surprise_data.get('surprise_percentage', 0):.2f}%のサプライズ")

        # 3. EventFilterテスト
        event_filter = EventFilter()
        test_events = [
            factory.create_from_dict({
                "event_id": "test_filter_001",
                "date_utc": datetime.utcnow() + timedelta(hours=2),
                "country": "japan",
                "event_name": "Bank of Japan Policy Rate",
                "importance": "high",
                "forecast_value": 0.1,
                "previous_value": 0.1
            }),
            factory.create_from_dict({
                "event_id": "test_filter_002",
                "date_utc": datetime.utcnow() + timedelta(hours=3),
                "country": "canada",
                "event_name": "Minor Economic Data",
                "importance": "low",
                "forecast_value": 1.0,
                "previous_value": 1.0
            })
        ]
        
        high_impact_events = await event_filter.filter_high_impact_events(test_events)
        print(f"✅ EventFilterテスト完了: {len(high_impact_events)}/{len(test_events)}件の高影響度イベント")

        return True

    except Exception as e:
        print(f"❌ データ分析コンポーネントテストエラー: {e}")
        return False


async def test_data_analysis_service():
    """データ分析サービスの統合テスト"""
    print("\n=== データ分析サービス統合テスト ===")

    try:
        # データ分析サービスの作成
        analysis_service = DataAnalysisService()
        print("✅ データ分析サービス作成完了")

        # テスト用データの作成
        factory = EconomicEventFactory()
        
        # 変更前のイベント
        old_events = [
            factory.create_from_dict({
                "event_id": "integration_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "united states",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 3.2,
                "previous_value": 3.0
            }),
            factory.create_from_dict({
                "event_id": "integration_002",
                "date_utc": datetime.utcnow() + timedelta(hours=2),
                "country": "japan",
                "event_name": "Employment Rate",
                "importance": "medium",
                "forecast_value": 2.8,
                "previous_value": 2.7
            })
        ]
        
        # 変更後のイベント
        new_events = [
            factory.create_from_dict({
                "event_id": "integration_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "united states",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 3.5,  # 変更
                "previous_value": 3.0
            }),
            factory.create_from_dict({
                "event_id": "integration_002",
                "date_utc": datetime.utcnow() + timedelta(hours=2),
                "country": "japan",
                "event_name": "Employment Rate",
                "importance": "medium",
                "forecast_value": 2.8,  # 変更なし
                "previous_value": 2.7
            })
        ]

        # データ変更分析
        change_analysis = await analysis_service.analyze_data_changes(old_events, new_events)
        print(f"✅ データ変更分析完了: {change_analysis['summary']['total_changes']}件の変更")

        # 実際値を追加したイベントでサプライズ計算
        events_with_actual = [
            factory.create_from_dict({
                "event_id": "surprise_001",
                "date_utc": datetime.utcnow(),
                "country": "united states",
                "event_name": "Non-Farm Payrolls",
                "importance": "high",
                "actual_value": 220000,
                "forecast_value": 200000,
                "previous_value": 190000
            })
        ]

        surprise_analysis = await analysis_service.calculate_event_surprises(events_with_actual)
        print(f"✅ サプライズ分析完了: {surprise_analysis['summary']['total_surprises']}件のサプライズ")

        # 市場影響分析
        market_impact = await analysis_service.analyze_market_impact(new_events)
        print(f"✅ 市場影響分析完了: {market_impact['high_impact_events']}件の高影響度イベント")

        return True

    except Exception as e:
        print(f"❌ データ分析サービス統合テストエラー: {e}")
        return False


async def test_forecast_comparison():
    """予測値比較テスト"""
    print("\n=== 予測値比較テスト ===")

    try:
        analysis_service = DataAnalysisService()
        factory = EconomicEventFactory()

        # 比較対象1（古い予測）
        forecast1_events = [
            factory.create_from_dict({
                "event_id": "compare_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "GDP Growth Rate",
                "importance": "high",
                "forecast_value": 1.2,
                "actual_value": 1.5  # 実際値
            })
        ]

        # 比較対象2（新しい予測）
        forecast2_events = [
            factory.create_from_dict({
                "event_id": "compare_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "GDP Growth Rate",
                "importance": "high",
                "forecast_value": 1.4,  # より正確な予測
                "actual_value": 1.5
            })
        ]

        comparison_result = await analysis_service.compare_forecasts(
            forecast1_events, forecast2_events, "Old vs New Forecast"
        )
        
        print(f"✅ 予測値比較完了: {comparison_result['total_matched_events']}件の比較")
        print(f"   改善率: {comparison_result['summary']['improvement_rate']:.2%}")

        return True

    except Exception as e:
        print(f"❌ 予測値比較テストエラー: {e}")
        return False


async def test_event_filtering():
    """イベントフィルタリング詳細テスト"""
    print("\n=== イベントフィルタリング詳細テスト ===")

    try:
        event_filter = EventFilter()
        factory = EconomicEventFactory()

        # 多様なテストイベントの作成
        test_events = [
            # 高重要度・主要国
            factory.create_from_dict({
                "event_id": "filter_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "united states",
                "event_name": "Federal Reserve Interest Rate Decision",
                "importance": "high"
            }),
            # 中重要度・主要国
            factory.create_from_dict({
                "event_id": "filter_002",
                "date_utc": datetime.utcnow() + timedelta(hours=12),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "medium"
            }),
            # 低重要度・その他の国
            factory.create_from_dict({
                "event_id": "filter_003",
                "date_utc": datetime.utcnow() + timedelta(hours=48),
                "country": "australia",
                "event_name": "Minor Economic Indicator",
                "importance": "low"
            }),
            # 高重要度・遠い将来
            factory.create_from_dict({
                "event_id": "filter_004",
                "date_utc": datetime.utcnow() + timedelta(days=7),
                "country": "euro zone",
                "event_name": "ECB Interest Rate Decision",
                "importance": "high"
            })
        ]

        # 各種フィルタリングテスト
        high_importance = await event_filter.filter_by_importance(test_events, ["high"])
        print(f"✅ 重要度フィルタリング: {len(high_importance)}/{len(test_events)}件（高重要度）")

        major_countries = await event_filter.filter_by_countries(
            test_events, ["united states", "japan", "euro zone"]
        )
        print(f"✅ 国フィルタリング: {len(major_countries)}/{len(test_events)}件（主要国）")

        upcoming_24h = await event_filter.filter_upcoming_events(test_events, 24)
        print(f"✅ 時間フィルタリング: {len(upcoming_24h)}/{len(test_events)}件（24時間以内）")

        priority_events = await event_filter.get_priority_events(test_events, 3)
        print(f"✅ 優先度フィルタリング: {len(priority_events)}件の優先イベント")

        impact_classification = await event_filter.classify_events_by_impact(test_events)
        print(f"✅ 影響度分類:")
        for impact, events in impact_classification.items():
            print(f"    {impact}: {len(events)}件")

        return True

    except Exception as e:
        print(f"❌ イベントフィルタリング詳細テストエラー: {e}")
        return False


async def test_surprise_patterns():
    """サプライズパターン分析テスト"""
    print("\n=== サプライズパターン分析テスト ===")

    try:
        surprise_calculator = SurpriseCalculator()
        factory = EconomicEventFactory()

        # 様々なサプライズパターンのテストイベント
        surprise_events = [
            # 大きな正のサプライズ
            factory.create_from_dict({
                "event_id": "surprise_pattern_001",
                "country": "united states",
                "event_name": "Non-Farm Payrolls",
                "importance": "high",
                "actual_value": 250000,
                "forecast_value": 200000
            }),
            # 小さな負のサプライズ
            factory.create_from_dict({
                "event_id": "surprise_pattern_002",
                "country": "japan",
                "event_name": "CPI",
                "importance": "medium",
                "actual_value": 2.1,
                "forecast_value": 2.2
            }),
            # サプライズなし
            factory.create_from_dict({
                "event_id": "surprise_pattern_003",
                "country": "euro zone",
                "event_name": "ECB Rate",
                "importance": "high",
                "actual_value": 4.5,
                "forecast_value": 4.5
            })
        ]

        # 一括サプライズ計算
        bulk_result = await surprise_calculator.calculate_bulk_surprises(surprise_events)
        print(f"✅ 一括サプライズ計算: {bulk_result['total_surprises']}件の計算")

        # パターン分析
        pattern_analysis = await surprise_calculator.analyze_surprise_patterns(
            bulk_result['surprises']
        )
        print(f"✅ サプライズパターン分析:")
        print(f"    正のサプライズ: {pattern_analysis['direction_analysis']['positive']}件")
        print(f"    負のサプライズ: {pattern_analysis['direction_analysis']['negative']}件")
        print(f"    中立: {pattern_analysis['direction_analysis']['neutral']}件")

        return True

    except Exception as e:
        print(f"❌ サプライズパターン分析テストエラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("データ分析サービステスト")
    print("=" * 60)

    # 各テストの実行
    components_ok = await test_data_analysis_components()
    service_ok = await test_data_analysis_service()
    comparison_ok = await test_forecast_comparison()
    filtering_ok = await test_event_filtering()
    patterns_ok = await test_surprise_patterns()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  データ分析コンポーネント: {'✅' if components_ok else '❌'}")
    print(f"  データ分析サービス統合: {'✅' if service_ok else '❌'}")
    print(f"  予測値比較: {'✅' if comparison_ok else '❌'}")
    print(f"  イベントフィルタリング詳細: {'✅' if filtering_ok else '❌'}")
    print(f"  サプライズパターン分析: {'✅' if patterns_ok else '❌'}")

    if all([components_ok, service_ok, comparison_ok, filtering_ok, patterns_ok]):
        print("\n🎉 全てのデータ分析サービステストが成功しました！")
        print("📊 経済データの分析・差分検出・サプライズ計算システム完成！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
