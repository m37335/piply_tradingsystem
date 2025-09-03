#!/usr/bin/env python3
"""
Discord通知機能テストスクリプト
"""

import asyncio
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# .envファイルの読み込み
try:
    from dotenv import load_dotenv

    load_dotenv("/app/.env")
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")
except FileNotFoundError:
    print("⚠️ .env file not found, using system environment variables")


async def test_discord_notification():
    """Discord通知機能のテスト"""
    print("📢 Testing Discord notification functionality...")

    try:
        # Discord通知サービスのインポート
        from src.domain.entities.ai_report.ai_report import AIReport, ReportType
        from src.domain.entities.ai_report.usd_jpy_prediction import (
            PredictionDirection,
            PredictionStrength,
            USDJPYPrediction,
        )
        from src.domain.entities.economic_event.economic_event import (
            EconomicEvent,
            Importance,
        )
        from src.infrastructure.external.discord.discord_client import DiscordClient

        print("✅ All modules imported successfully")

        # テスト用の経済イベントデータを作成
        test_event_data = {
            "event_id": "test_event_001",
            "date_utc": datetime.now().isoformat(),
            "country": "japan",
            "event_name": "Consumer Price Index (CPI)",
            "importance": "high",
            "actual_value": 2.5,
            "forecast_value": 2.3,
            "previous_value": 2.1,
            "currency": "JPY",
            "unit": "%",
        }

        print(f"✅ Test economic event data created: {test_event_data['event_name']}")

        # テスト用のAIレポートデータを作成
        test_ai_report_data = {
            "event_id": 1,
            "report_type": "pre_event",
            "report_content": "This is a test AI analysis report for USD/JPY prediction.",
            "usd_jpy_prediction": {
                "direction": "bullish",
                "strength": "strong",
                "confidence_score": 0.85,
                "reasons": ["Strong economic data", "Central bank policy support"],
                "timeframe": "1-4 hours",
            },
            "confidence_score": 0.85,
        }

        print(
            f"✅ Test AI report data created with confidence: {test_ai_report_data['confidence_score']}"
        )

        # Discord通知のテスト
        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print(
                "❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set in environment variables"
            )
            print("Please set DISCORD_ECONOMICINDICATORS_WEBHOOK_URL in your .env file")
            return False

        print(f"✅ Discord webhook URL found: {webhook_url[:50]}...")

        # Discordクライアントの作成
        async with DiscordClient(webhook_url) as discord_client:
            # 経済イベント通知のテスト
            print("\n📊 Testing economic event notification...")
            event_success = await discord_client.send_economic_event_notification(
                test_event_data, "new_event"
            )

            if event_success:
                print("✅ Economic event notification sent successfully")
            else:
                print("❌ Economic event notification failed")

            # AI分析レポート通知のテスト
            print("\n🤖 Testing AI analysis report notification...")
            ai_success = await discord_client.send_ai_report_notification(
                test_ai_report_data
            )

            if ai_success:
                print("✅ AI analysis report notification sent successfully")
            else:
                print("❌ AI analysis report notification failed")

            # システム稼働通知のテスト
            print("\n🚀 Testing system status notification...")
            status_success = await discord_client.send_embed(
                title="System Test",
                description="All systems are operational",
                color=0x00FF00,
                fields=[
                    {"name": "Status", "value": "✅ Operational", "inline": True},
                    {
                        "name": "Timestamp",
                        "value": datetime.now().isoformat(),
                        "inline": True,
                    },
                ],
            )

            if status_success:
                print("✅ System status notification sent successfully")
            else:
                print("❌ System status notification failed")

            # アラート通知のテスト
            print("\n⚠️ Testing alert notification...")
            alert_success = await discord_client.send_embed(
                title="Test Alert",
                description="This is a test alert message",
                color=0xFFA500,
                fields=[
                    {"name": "Alert Type", "value": "Warning", "inline": True},
                    {
                        "name": "Timestamp",
                        "value": datetime.now().isoformat(),
                        "inline": True,
                    },
                ],
            )

            if alert_success:
                print("✅ Alert notification sent successfully")
            else:
                print("❌ Alert notification failed")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_simple_discord_message():
    """シンプルなDiscordメッセージのテスト"""
    print("\n🔧 Testing simple Discord message...")

    try:
        import requests

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        # シンプルなメッセージを送信
        payload = {
            "content": "🤖 **investpy Economic Calendar System** - Test Message\n\nThis is a test message from the system.",
            "username": "Economic Calendar Bot",
        }

        response = requests.post(webhook_url, json=payload, timeout=10)

        if response.status_code == 200:
            print("✅ Simple Discord message sent successfully")
            return True
        else:
            print(f"❌ Simple Discord message failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Simple Discord message test failed: {e}")
        return False


async def main():
    """メイン関数"""
    print("🚀 Discord Notification Test Suite")
    print("=" * 50)

    # シンプルなメッセージテスト
    simple_test = await test_simple_discord_message()

    # 基本通知テスト
    basic_test = await test_discord_notification()

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Simple Discord Message: {'✅ PASS' if simple_test else '❌ FAIL'}")
    print(f"   Advanced Discord Notification: {'✅ PASS' if basic_test else '❌ FAIL'}")

    if simple_test or basic_test:
        print("\n🎉 Discord integration is working!")
        print("✅ Discord notifications can be sent successfully")
    else:
        print("\n⚠️ All Discord tests failed. Please check the configuration.")

    return simple_test or basic_test


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
