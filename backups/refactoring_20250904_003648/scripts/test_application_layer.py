"""
アプリケーション層テストスクリプト
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.application.interfaces.schedulers.base import BaseScheduler, SchedulerConfig
from src.application.use_cases.analysis import DetectChangesUseCase
from src.application.use_cases.fetch import (
    FetchEconomicCalendarUseCase,
    FetchTodayEventsUseCase,
    FetchWeeklyEventsUseCase,
)
from src.domain.services.data_analysis import DataAnalysisService
from src.domain.services.investpy import InvestpyService
from src.infrastructure.database.repositories.sql import SQLEconomicCalendarRepository


async def test_fetch_use_cases():
    """データ取得ユースケースのテスト"""
    print("=== データ取得ユースケーステスト ===")

    try:
        # モックオブジェクトの作成
        class MockInvestpyService:
            async def fetch_economic_calendar(self, *args, **kwargs):
                return []

            async def health_check(self):
                return True

            def get_stats(self):
                return {"total_requests": 0, "success_rate": 100.0}

        class MockRepository:
            async def save(self, event):
                return event

            async def find_by_date_range(self, *args, **kwargs):
                return []

            async def get_statistics(self, *args, **kwargs):
                return {"total_events": 0}

            async def health_check(self):
                return True

            def get_events_since(self, *args, **kwargs):
                return []

        # モックサービスの作成
        investpy_service = MockInvestpyService()
        repository = MockRepository()

        # ユースケースの作成
        fetch_calendar_uc = FetchEconomicCalendarUseCase(
            investpy_service=investpy_service, repository=repository
        )

        fetch_today_uc = FetchTodayEventsUseCase(
            investpy_service=investpy_service, repository=repository
        )

        fetch_weekly_uc = FetchWeeklyEventsUseCase(
            investpy_service=investpy_service, repository=repository
        )

        print("✅ データ取得ユースケース作成完了")

        # 統計情報の取得テスト
        stats = await fetch_calendar_uc.get_fetch_statistics()
        print(f"✅ 統計情報取得: {len(stats)}件の統計データ")

        # ヘルスチェックテスト
        health = await fetch_calendar_uc.health_check()
        print(f"✅ ヘルスチェック: {'正常' if health else '異常'}")

        return True

    except Exception as e:
        print(f"❌ データ取得ユースケーステストエラー: {e}")
        return False


async def test_analysis_use_cases():
    """データ分析ユースケースのテスト"""
    print("\n=== データ分析ユースケーステスト ===")

    try:
        # モックオブジェクトの作成
        class MockDataAnalysisService:
            async def detect_changes(self, *args, **kwargs):
                return []

            async def detect_forecast_change(self, *args, **kwargs):
                return {"has_change": False}

            async def calculate_surprise(self, *args, **kwargs):
                return {"has_surprise": False}

            async def health_check(self):
                return True

            def get_stats(self):
                return {"total_analysis": 0, "success_rate": 100.0}

        class MockRepository:
            async def find_by_date_range(self, *args, **kwargs):
                return []

            async def get_statistics(self, *args, **kwargs):
                return {"total_changes": 0}

            async def health_check(self):
                return True

            def get_events_since(self, *args, **kwargs):
                return []

        # モックサービスの作成
        data_analysis_service = MockDataAnalysisService()
        repository = MockRepository()

        # ユースケースの作成
        detect_changes_uc = DetectChangesUseCase(
            data_analysis_service=data_analysis_service, repository=repository
        )

        print("✅ データ分析ユースケース作成完了")

        # 変更統計情報の取得テスト
        stats = await detect_changes_uc.get_change_statistics()
        print(f"✅ 変更統計情報取得: {len(stats)}件の統計データ")

        # リアルタイム監視テスト
        monitoring_result = await detect_changes_uc.execute_realtime_monitoring()
        print(
            f"✅ リアルタイム監視: {'成功' if monitoring_result['success'] else '失敗'}"
        )

        return True

    except Exception as e:
        print(f"❌ データ分析ユースケーステストエラー: {e}")
        return False


async def test_base_scheduler():
    """基底スケジューラーのテスト"""
    print("\n=== 基底スケジューラーテスト ===")

    try:
        # 設定の作成
        config = SchedulerConfig(
            name="test_scheduler",
            description="テスト用スケジューラー",
            enabled=True,
            max_retries=3,
            retry_delay=60,
            timeout=300,
        )

        print("✅ スケジューラー設定作成完了")

        # 設定の検証
        is_valid = config.validate()
        print(f"✅ 設定検証: {'有効' if is_valid else '無効'}")

        # 設定の辞書変換
        config_dict = config.to_dict()
        print(f"✅ 設定辞書変換: {len(config_dict)}件の設定項目")

        # 辞書からの設定復元
        restored_config = SchedulerConfig.from_dict(config_dict)
        print(f"✅ 設定復元: {restored_config.name}")

        return True

    except Exception as e:
        print(f"❌ 基底スケジューラーテストエラー: {e}")
        return False


class TestScheduler(BaseScheduler):
    """テスト用スケジューラー"""

    async def execute_task(self):
        """テストタスクの実行"""
        return {
            "success": True,
            "message": "テストタスクが正常に実行されました",
            "timestamp": datetime.utcnow().isoformat(),
        }


async def test_scheduler_execution():
    """スケジューラー実行のテスト"""
    print("\n=== スケジューラー実行テスト ===")

    try:
        # 設定の作成
        config = SchedulerConfig(
            name="test_execution_scheduler",
            description="テスト実行用スケジューラー",
            enabled=True,
            timeout=10,
        )

        # テストスケジューラーの作成
        scheduler = TestScheduler(config)

        print("✅ テストスケジューラー作成完了")

        # 実行テスト
        result = await scheduler.execute()
        print(f"✅ スケジューラー実行: {'成功' if result else '失敗'}")

        # 統計情報の取得
        stats = scheduler.get_stats()
        print(f"✅ 統計情報: {stats['execution_count']}回実行")

        # ヘルスチェック
        health = scheduler.health_check()
        print(f"✅ ヘルスチェック: {'正常' if health else '異常'}")

        return True

    except Exception as e:
        print(f"❌ スケジューラー実行テストエラー: {e}")
        return False


async def test_use_case_integration():
    """ユースケース統合テスト"""
    print("\n=== ユースケース統合テスト ===")

    try:
        # モックオブジェクトの作成
        class MockInvestpyService:
            async def fetch_economic_calendar(self, *args, **kwargs):
                return []

            async def health_check(self):
                return True

            def get_stats(self):
                return {"total_requests": 0, "success_rate": 100.0}

        class MockDataAnalysisService:
            async def detect_changes(self, *args, **kwargs):
                return []

            async def health_check(self):
                return True

            def get_stats(self):
                return {"total_analysis": 0, "success_rate": 100.0}

        class MockRepository:
            async def find_by_date_range(self, *args, **kwargs):
                return []

            async def get_statistics(self, *args, **kwargs):
                return {"total_events": 0}

            async def health_check(self):
                return True

            def get_events_since(self, *args, **kwargs):
                return []

        # モックサービスの作成
        investpy_service = MockInvestpyService()
        data_analysis_service = MockDataAnalysisService()
        repository = MockRepository()

        # ユースケースの作成
        fetch_uc = FetchEconomicCalendarUseCase(
            investpy_service=investpy_service, repository=repository
        )

        detect_uc = DetectChangesUseCase(
            data_analysis_service=data_analysis_service, repository=repository
        )

        print("✅ ユースケース統合作成完了")

        # 統合テスト（モック実行）
        print("📝 統合テスト（モック実行）")

        # 各ユースケースの統計情報を取得
        fetch_stats = await fetch_uc.get_fetch_statistics()
        change_stats = await detect_uc.get_change_statistics()

        print(f"✅ 取得統計: {len(fetch_stats)}件")
        print(f"✅ 変更統計: {len(change_stats)}件")

        return True

    except Exception as e:
        print(f"❌ ユースケース統合テストエラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("アプリケーション層テスト")
    print("=" * 60)

    # 各テストの実行
    fetch_ok = await test_fetch_use_cases()
    analysis_ok = await test_analysis_use_cases()
    scheduler_ok = await test_base_scheduler()
    execution_ok = await test_scheduler_execution()
    integration_ok = await test_use_case_integration()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  データ取得ユースケース: {'✅' if fetch_ok else '❌'}")
    print(f"  データ分析ユースケース: {'✅' if analysis_ok else '❌'}")
    print(f"  基底スケジューラー: {'✅' if scheduler_ok else '❌'}")
    print(f"  スケジューラー実行: {'✅' if execution_ok else '❌'}")
    print(f"  ユースケース統合: {'✅' if integration_ok else '❌'}")

    if all([fetch_ok, analysis_ok, scheduler_ok, execution_ok, integration_ok]):
        print("\n🎉 全てのアプリケーション層テストが成功しました！")
        print("📋 ユースケースとスケジューラーの基盤完成！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
