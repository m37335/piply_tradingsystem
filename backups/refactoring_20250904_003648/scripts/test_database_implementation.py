#!/usr/bin/env python3
"""
データベース実装テストスクリプト
実装したデータベース機能の動作確認を行う
"""

import asyncio
import sys
import os
from datetime import datetime, date
from decimal import Decimal

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.domain.entities.economic_event import EconomicEvent, Importance
from src.domain.entities.ai_report import AIReport, USDJPYPrediction, ReportType
from src.infrastructure.config.database import DatabaseConfig, ConnectionManager
from src.infrastructure.database.repositories.sql import (
    SQLEconomicCalendarRepository, SQLAIReportRepository, SQLNotificationLogRepository
)


async def test_database_connection():
    """データベース接続テスト"""
    print("=== データベース接続テスト ===")
    
    try:
        config = DatabaseConfig()
        manager = ConnectionManager(config)
        
        print(f"設定: {config}")
        
        # 接続テスト
        is_connected = manager.test_connection()
        print(f"同期接続テスト: {'✅ 成功' if is_connected else '❌ 失敗'}")
        
        is_async_connected = await manager.test_async_connection()
        print(f"非同期接続テスト: {'✅ 成功' if is_async_connected else '❌ 失敗'}")
        
        # 接続情報
        info = manager.get_connection_info()
        print(f"接続情報: {info}")
        
        return is_connected and is_async_connected
        
    except Exception as e:
        print(f"❌ データベース接続テストエラー: {e}")
        return False
    
    print()


async def test_economic_event_repository():
    """経済イベントリポジトリテスト"""
    print("=== 経済イベントリポジトリテスト ===")
    
    try:
        config = DatabaseConfig()
        manager = ConnectionManager(config)
        repo = SQLEconomicCalendarRepository(manager)
        
        # テスト用イベントの作成
        test_event = EconomicEvent(
            event_id="test_event_001",
            date_utc=datetime(2025, 1, 15, 8, 30),
            country="japan",
            event_name="Test Consumer Price Index",
            importance=Importance.HIGH,
            forecast_value=Decimal("2.3"),
            previous_value=Decimal("2.1")
        )
        
        print(f"テストイベント作成: {test_event}")
        
        # 保存テスト
        saved_event = await repo.save(test_event)
        print(f"保存成功: ID={saved_event.id}")
        
        # 検索テスト
        found_event = await repo.find_by_id(saved_event.id)
        print(f"ID検索成功: {found_event}")
        
        found_by_event_id = await repo.find_by_event_id(test_event.event_id)
        print(f"イベントID検索成功: {found_by_event_id}")
        
        # 日付範囲検索テスト
        events_in_range = await repo.find_by_date_range(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31),
            countries=["japan"],
            importances=[Importance.HIGH]
        )
        print(f"日付範囲検索結果: {len(events_in_range)}件")
        
        # 件数テスト
        count = await repo.count_events(
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 31)
        )
        print(f"件数取得: {count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ 経済イベントリポジトリテストエラー: {e}")
        return False
    
    print()


async def test_ai_report_repository():
    """AIレポートリポジトリテスト"""
    print("=== AIレポートリポジトリテスト ===")
    
    try:
        config = DatabaseConfig()
        manager = ConnectionManager(config)
        repo = SQLAIReportRepository(manager)
        
        # テスト用予測の作成
        test_prediction = USDJPYPrediction(
            direction="buy",
            strength="strong",
            target_price=Decimal("150.50"),
            confidence_score=Decimal("0.8")
        )
        test_prediction.add_fundamental_reason("テスト用ファンダメンタル理由")
        test_prediction.add_technical_reason("テスト用テクニカル理由")
        
        # テスト用レポートの作成
        test_report = AIReport(
            event_id=1,  # 存在する経済イベントIDを想定
            report_type=ReportType.PRE_EVENT,
            report_content="テスト用レポート内容です。",
            summary="テスト用サマリー",
            usd_jpy_prediction=test_prediction,
            confidence_score=Decimal("0.8")
        )
        
        print(f"テストレポート作成: {test_report}")
        
        # 保存テスト
        saved_report = await repo.save(test_report)
        print(f"保存成功: ID={saved_report.id}")
        
        # 検索テスト
        found_report = await repo.find_by_id(saved_report.id)
        print(f"ID検索成功: {found_report}")
        
        # 最近のレポート検索
        recent_reports = await repo.find_recent_reports(limit=10)
        print(f"最近のレポート: {len(recent_reports)}件")
        
        # 統計情報取得
        stats = await repo.get_statistics()
        print(f"統計情報: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ AIレポートリポジトリテストエラー: {e}")
        return False
    
    print()


async def test_notification_log_repository():
    """通知ログリポジトリテスト"""
    print("=== 通知ログリポジトリテスト ===")
    
    try:
        config = DatabaseConfig()
        manager = ConnectionManager(config)
        repo = SQLNotificationLogRepository(manager)
        
        # テスト用ログの作成
        from src.infrastructure.database.models.notification_log.notification_log_mapper import (
            NotificationLog, NotificationType, NotificationStatus
        )
        
        test_log = NotificationLog(
            event_id=1,  # 存在する経済イベントIDを想定
            notification_type=NotificationType.NEW_EVENT,
            message_content="テスト通知メッセージです。",
            status=NotificationStatus.SENT,
            sent_at=datetime.utcnow()
        )
        
        print(f"テストログ作成: {test_log}")
        
        # 保存テスト
        saved_log = await repo.save(test_log)
        print(f"保存成功: ID={saved_log.id}")
        
        # 検索テスト
        found_log = await repo.find_by_id(saved_log.id)
        print(f"ID検索成功: {found_log}")
        
        # 最近のログ検索
        recent_logs = await repo.find_recent_logs(limit=10)
        print(f"最近のログ: {len(recent_logs)}件")
        
        # 統計情報取得
        stats = await repo.get_statistics()
        print(f"統計情報: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ 通知ログリポジトリテストエラー: {e}")
        return False
    
    print()


async def main():
    """メイン関数"""
    print("investpy経済カレンダーシステム データベース実装テスト")
    print("=" * 60)
    
    # 各テストの実行
    connection_ok = await test_database_connection()
    
    if connection_ok:
        event_repo_ok = await test_economic_event_repository()
        ai_repo_ok = await test_ai_report_repository()
        log_repo_ok = await test_notification_log_repository()
        
        print("=" * 60)
        print("テスト結果サマリー:")
        print(f"  データベース接続: {'✅' if connection_ok else '❌'}")
        print(f"  経済イベントリポジトリ: {'✅' if event_repo_ok else '❌'}")
        print(f"  AIレポートリポジトリ: {'✅' if ai_repo_ok else '❌'}")
        print(f"  通知ログリポジトリ: {'✅' if log_repo_ok else '❌'}")
        
        if all([connection_ok, event_repo_ok, ai_repo_ok, log_repo_ok]):
            print("\n🎉 全てのテストが成功しました！")
        else:
            print("\n⚠️ 一部のテストが失敗しました。")
    else:
        print("❌ データベース接続に失敗したため、他のテストをスキップします。")
    
    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
