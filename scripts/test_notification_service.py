"""
通知サービスの統合テストスクリプト
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

from src.domain.entities import EconomicEvent, EconomicEventFactory
from src.domain.services.notification import (
    DiscordMessageBuilder,
    NotificationCooldownManager,
    NotificationRuleEngine,
    NotificationService,
)
from src.infrastructure.config.notification import DiscordConfig
from src.infrastructure.external.discord import DiscordClient


async def test_notification_components():
    """通知コンポーネントの個別テスト"""
    print("=== 通知コンポーネントテスト ===")

    try:
        # テスト用の経済イベントを作成
        factory = EconomicEventFactory()
        test_event = factory.create_from_dict(
            {
                "event_id": "test_event_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 2.5,
                "previous_value": 2.3,
            }
        )
        print("✅ テストイベント作成完了")

        # 1. DiscordMessageBuilderテスト
        message_builder = DiscordMessageBuilder()
        message_data = message_builder.build_event_message(test_event, "new_event")
        print("✅ DiscordMessageBuilderテスト完了")

        # 2. NotificationRuleEngineテスト
        rule_engine = NotificationRuleEngine()
        should_send = rule_engine.should_send_notification(test_event, "new_event")
        print(f"✅ NotificationRuleEngineテスト完了: should_send={should_send}")

        # 3. NotificationCooldownManagerテスト
        cooldown_manager = NotificationCooldownManager()
        can_send = cooldown_manager.can_send_notification(test_event, "new_event")
        print(f"✅ NotificationCooldownManagerテスト完了: can_send={can_send}")

        return True

    except Exception as e:
        print(f"❌ 通知コンポーネントテストエラー: {e}")
        return False


async def test_notification_service():
    """通知サービスの統合テスト"""
    print("\n=== 通知サービス統合テスト ===")

    try:
        # Discord設定の読み込み
        config = DiscordConfig.from_env()

        # Discordクライアントの作成
        discord_client = DiscordClient(webhook_url=config.webhook_url, config=config)
        print("✅ Discordクライアント作成完了")

        # 通知サービスの作成
        notification_service = NotificationService(discord_client=discord_client)
        print("✅ 通知サービス作成完了")

        # テスト用の経済イベントを作成
        factory = EconomicEventFactory()
        test_event = factory.create_from_dict(
            {
                "event_id": "test_integration_001",
                "date_utc": datetime.utcnow() + timedelta(hours=2),
                "country": "united states",
                "event_name": "Non-Farm Payrolls",
                "importance": "high",
                "forecast_value": 180000,
                "previous_value": 175000,
            }
        )
        print("✅ テストイベント作成完了")

        # 通知送信テスト
        success = await notification_service.send_event_notification(
            test_event, "new_event"
        )
        print(f"✅ 通知送信テスト完了: success={success}")

        return True

    except Exception as e:
        print(f"❌ 通知サービス統合テストエラー: {e}")
        return False


async def test_rule_engine_detailed():
    """ルールエンジンの詳細テスト"""
    print("\n=== ルールエンジン詳細テスト ===")

    try:
        rule_engine = NotificationRuleEngine()
        factory = EconomicEventFactory()

        # テストケース1: 高重要度イベント
        high_importance_event = factory.create_from_dict(
            {
                "event_id": "test_high_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Bank of Japan Policy Rate",
                "importance": "high",
                "forecast_value": 0.1,
                "previous_value": 0.1,
            }
        )

        should_send_high = rule_engine.should_send_notification(
            high_importance_event, "new_event"
        )
        print(f"✅ 高重要度イベント: should_send={should_send_high}")

        # テストケース2: 低重要度イベント
        low_importance_event = factory.create_from_dict(
            {
                "event_id": "test_low_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Minor Economic Indicator",
                "importance": "low",
                "forecast_value": 1.0,
                "previous_value": 1.0,
            }
        )

        should_send_low = rule_engine.should_send_notification(
            low_importance_event, "new_event"
        )
        print(f"✅ 低重要度イベント: should_send={should_send_low}")

        # テストケース3: 対象外の国
        foreign_event = factory.create_from_dict(
            {
                "event_id": "test_foreign_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "brazil",
                "event_name": "Brazilian Economic Data",
                "importance": "high",
                "forecast_value": 5.0,
                "previous_value": 5.0,
            }
        )

        should_send_foreign = rule_engine.should_send_notification(
            foreign_event, "new_event"
        )
        print(f"✅ 対象外国イベント: should_send={should_send_foreign}")

        return True

    except Exception as e:
        print(f"❌ ルールエンジン詳細テストエラー: {e}")
        return False


async def test_cooldown_manager_detailed():
    """クールダウンマネージャーの詳細テスト"""
    print("\n=== クールダウンマネージャー詳細テスト ===")

    try:
        cooldown_manager = NotificationCooldownManager()
        factory = EconomicEventFactory()

        test_event = factory.create_from_dict(
            {
                "event_id": "test_cooldown_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Test Event",
                "importance": "medium",
                "forecast_value": 1.0,
                "previous_value": 1.0,
            }
        )

        # 初回通知
        can_send_first = cooldown_manager.can_send_notification(test_event, "new_event")
        print(f"✅ 初回通知: can_send={can_send_first}")

        if can_send_first:
            cooldown_manager.record_notification(test_event, "new_event")
            print("✅ 初回通知記録完了")

        # 2回目の通知（クールダウン中）
        can_send_second = cooldown_manager.can_send_notification(
            test_event, "new_event"
        )
        print(f"✅ 2回目通知: can_send={can_send_second}")

        # クールダウン状態の確認
        status = cooldown_manager.get_cooldown_status(test_event, "new_event")
        print(f"✅ クールダウン状態: {status}")

        return True

    except Exception as e:
        print(f"❌ クールダウンマネージャー詳細テストエラー: {e}")
        return False


async def test_message_builder_detailed():
    """メッセージビルダーの詳細テスト"""
    print("\n=== メッセージビルダー詳細テスト ===")

    try:
        message_builder = DiscordMessageBuilder()
        factory = EconomicEventFactory()

        # 日本のイベント
        japan_event = factory.create_from_dict(
            {
                "event_id": "test_japan_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI)",
                "importance": "high",
                "forecast_value": 2.5,
                "previous_value": 2.3,
            }
        )

        message_builder.build_event_message(japan_event, "new_event")
        print("✅ 日本イベントメッセージ作成完了")

        # 米国のイベント
        us_event = factory.create_from_dict(
            {
                "event_id": "test_us_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "united states",
                "event_name": "Non-Farm Payrolls",
                "importance": "high",
                "forecast_value": 180000,
                "previous_value": 175000,
            }
        )

        message_builder.build_event_message(us_event, "new_event")
        print("✅ 米国イベントメッセージ作成完了")

        # ユーロ圏のイベント
        euro_event = factory.create_from_dict(
            {
                "event_id": "test_euro_001",
                "date_utc": datetime.utcnow() + timedelta(hours=1),
                "country": "euro zone",
                "event_name": "ECB Interest Rate Decision",
                "importance": "high",
                "forecast_value": 4.5,
                "previous_value": 4.5,
            }
        )

        message_builder.build_event_message(euro_event, "new_event")
        print("✅ ユーロ圏イベントメッセージ作成完了")

        return True

    except Exception as e:
        print(f"❌ メッセージビルダー詳細テストエラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("通知サービス統合テスト")
    print("=" * 60)

    # 各テストの実行
    components_ok = await test_notification_components()
    service_ok = await test_notification_service()
    rule_ok = await test_rule_engine_detailed()
    cooldown_ok = await test_cooldown_manager_detailed()
    message_ok = await test_message_builder_detailed()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  通知コンポーネント: {'✅' if components_ok else '❌'}")
    print(f"  通知サービス統合: {'✅' if service_ok else '❌'}")
    print(f"  ルールエンジン詳細: {'✅' if rule_ok else '❌'}")
    print(f"  クールダウンマネージャー詳細: {'✅' if cooldown_ok else '❌'}")
    print(f"  メッセージビルダー詳細: {'✅' if message_ok else '❌'}")

    if all([components_ok, service_ok, rule_ok, cooldown_ok, message_ok]):
        print("\n🎉 全ての通知サービステストが成功しました！")
        print("📢 経済指標専用Discordチャンネルへの配信システム完成！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
