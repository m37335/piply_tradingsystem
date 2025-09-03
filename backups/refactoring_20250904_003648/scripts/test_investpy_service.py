"""
Investpyサービスのテストスクリプト
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.domain.services.investpy import (
    InvestpyService,
    InvestpyDataProcessor,
    InvestpyTimezoneHandler,
    InvestpyValidator,
)
from src.infrastructure.external.investpy import InvestpyClient
from src.infrastructure.config.investpy import InvestpyConfig, TimezoneConfig


async def test_investpy_service():
    """Investpyサービスのテスト"""
    print("=== Investpyサービステスト ===")

    try:
        # 設定の作成
        investpy_config = InvestpyConfig.from_env()
        timezone_config = TimezoneConfig.from_env()

        # クライアントの作成
        investpy_client = InvestpyClient()

        # サービスの作成
        service = InvestpyService(
            investpy_client=investpy_client,
            config=investpy_config,
            timezone_config=timezone_config,
        )

        print("✅ Investpyサービス作成完了")

        # ヘルスチェック
        print("\n--- ヘルスチェック ---")
        health = await service.health_check()
        print(f"  ヘルスチェック: {'✅' if health else '❌'}")

        # 統計情報
        print("\n--- 統計情報 ---")
        stats = await service.get_service_stats()
        print(f"  統計情報: {stats}")

        # 今日のイベント取得テスト
        print("\n--- 今日のイベント取得 ---")
        today_events = await service.fetch_today_events(
            countries=["japan", "united states"],
            importances=["high", "medium"],
        )
        print(f"  取得イベント数: {len(today_events)}")

        if today_events:
            print(f"  最初のイベント:")
            event = today_events[0]
            print(f"    ID: {event.event_id}")
            print(f"    名前: {event.event_name}")
            print(f"    国: {event.country}")
            print(f"    重要度: {event.importance}")
            print(f"    日付: {event.date_utc}")

        # 週間イベント取得テスト
        print("\n--- 週間イベント取得 ---")
        weekly_events = await service.fetch_weekly_events(
            countries=["japan", "united states"],
            importances=["high"],
        )
        print(f"  取得イベント数: {len(weekly_events)}")

        # データ品質チェック
        print("\n--- データ品質チェック ---")
        all_events = today_events + weekly_events
        if all_events:
            quality_report = service.validator.validate_data_quality(all_events)
            print(f"  品質スコア: {quality_report['quality_score']:.2f}")
            print(f"  総イベント数: {quality_report['total_events']}")
            if quality_report['issues']:
                print(f"  問題: {quality_report['issues']}")

        return True

    except Exception as e:
        print(f"❌ Investpyサービステストエラー: {e}")
        return False


async def test_data_processor():
    """データプロセッサーのテスト"""
    print("\n=== データプロセッサーテスト ===")

    try:
        config = InvestpyConfig.from_env()
        processor = InvestpyDataProcessor(config)

        # サンプルデータの作成
        import pandas as pd
        
        sample_data = pd.DataFrame({
            "Date": [datetime.now(), datetime.now() + timedelta(days=1)],
            "Time": ["09:30", "14:00"],
            "Country": ["Japan", "United States"],
            "Event": ["CPI", "Employment Report"],
            "Importance": ["High", "Medium"],
            "Actual": [1.5, None],
            "Forecast": [1.3, 150.0],
            "Previous": [1.2, 145.0],
        })

        print(f"  入力データ: {len(sample_data)}行")

        # データ処理
        processed_data = processor.process_raw_data(sample_data)
        print(f"  処理後データ: {len(processed_data)}行")

        # 統計情報
        stats = processor.get_processing_stats(processed_data)
        print(f"  統計情報: {stats}")

        return True

    except Exception as e:
        print(f"❌ データプロセッサーテストエラー: {e}")
        return False


async def test_timezone_handler():
    """タイムゾーンハンドラーのテスト"""
    print("\n=== タイムゾーンハンドラーテスト ===")

    try:
        config = TimezoneConfig.from_env()
        handler = InvestpyTimezoneHandler(config)

        # サンプルデータの作成
        import pandas as pd
        
        sample_data = pd.DataFrame({
            "date_utc": [datetime.now(), datetime.now() + timedelta(hours=1)],
            "country": ["Japan", "United States"],
        })

        print(f"  入力データ: {len(sample_data)}行")

        # UTC変換
        utc_data = handler.convert_to_utc(sample_data)
        print(f"  UTC変換後: {len(utc_data)}行")

        # JST変換
        jst_data = handler.convert_to_jst(utc_data)
        print(f"  JST変換後: {len(jst_data)}行")

        # タイムゾーン情報
        jp_tz_info = handler.get_timezone_info("japan")
        us_tz_info = handler.get_timezone_info("united states")
        print(f"  日本タイムゾーン: {jp_tz_info}")
        print(f"  米国タイムゾーン: {us_tz_info}")

        # 統計情報
        stats = handler.get_handler_stats()
        print(f"  統計情報: {stats}")

        return True

    except Exception as e:
        print(f"❌ タイムゾーンハンドラーテストエラー: {e}")
        return False


async def test_validator():
    """バリデーターのテスト"""
    print("\n=== バリデーターテスト ===")

    try:
        config = InvestpyConfig.from_env()
        validator = InvestpyValidator(config)

        # パラメータ検証テスト
        print("  パラメータ検証:")
        try:
            today = datetime.now().strftime("%d/%m/%Y")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
            
            result = validator.validate_fetch_parameters(
                from_date=today,
                to_date=tomorrow,
                countries=["japan", "united states"],
                importances=["high", "medium"],
            )
            print(f"    パラメータ検証: {'✅' if result else '❌'}")
        except Exception as e:
            print(f"    パラメータ検証: ❌ ({e})")

        # 検証ルール
        rules = validator.get_validation_rules()
        print(f"  検証ルール: {rules}")

        # 統計情報
        stats = validator.get_validator_stats()
        print(f"  統計情報: {stats}")

        return True

    except Exception as e:
        print(f"❌ バリデーターテストエラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("investpy 経済カレンダーシステム Investpyサービステスト")
    print("=" * 60)

    # 各テストの実行
    service_ok = await test_investpy_service()
    processor_ok = await test_data_processor()
    timezone_ok = await test_timezone_handler()
    validator_ok = await test_validator()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  Investpyサービス: {'✅' if service_ok else '❌'}")
    print(f"  データプロセッサー: {'✅' if processor_ok else '❌'}")
    print(f"  タイムゾーンハンドラー: {'✅' if timezone_ok else '❌'}")
    print(f"  バリデーター: {'✅' if validator_ok else '❌'}")

    if all([service_ok, processor_ok, timezone_ok, validator_ok]):
        print("\n🎉 全てのInvestpyサービステストが成功しました！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
