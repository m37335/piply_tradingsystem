#!/usr/bin/env python3
"""
日本語化Discord通知テストスクリプト
レート制限を考慮した間隔テスト
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List

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


async def test_japanese_economic_event():
    """日本語化された経済イベント通知のテスト"""
    print("📊 Testing Japanese economic event notification...")

    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        async with DiscordClient(webhook_url) as discord_client:
            # 日本語化された経済イベントデータ
            event_data = {
                "event_id": "jp_cpi_test",
                "date_utc": datetime(2025, 8, 22, 0, 0).isoformat(),
                "country": "japan",
                "event_name": "Consumer Price Index (CPI) y/y",
                "importance": "high",
                "actual_value": 2.8,
                "forecast_value": 2.5,
                "previous_value": 2.3,
                "currency": "JPY",
                "unit": "%",
                "surprise": 0.3,
            }

            success = await discord_client.send_economic_event_notification(
                event_data, "actual_announcement"
            )

            if success:
                print("✅ Japanese economic event notification sent successfully")
                return True
            else:
                print("❌ Japanese economic event notification failed")
                return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_japanese_ai_report():
    """日本語化されたAI分析レポートのテスト"""
    print("🤖 Testing Japanese AI analysis report...")

    # レート制限を避けるため待機
    await asyncio.sleep(3)

    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        async with DiscordClient(webhook_url) as discord_client:
            # 日本語化されたAI分析レポートデータ
            ai_report_data = {
                "event_id": 1,
                "event_name": "Consumer Price Index (CPI) y/y",
                "country": "japan",
                "date_utc": datetime(2025, 8, 22, 0, 0).isoformat(),
                "report_type": "post_event",
                "report_content": "日本の消費者物価指数（CPI）は予想を上回る2.8%となり、インフレ圧力が継続していることを示しています。日銀の金融政策に影響を与える可能性があり、USD/JPYは短期的に上昇傾向が続く見込みです。",
                "usd_jpy_prediction": {
                    "direction": "bullish",
                    "strength": "strong",
                    "confidence_score": 0.82,
                    "reasons": [
                        "インフレ圧力の継続",
                        "日銀の金融政策見直しの可能性",
                        "米国の利上げサイクル継続",
                        "リスク回避需要の高まり",
                    ],
                    "timeframe": "1-4時間",
                    "target_price": "148.50-150.00",
                },
                "confidence_score": 0.82,
            }

            success = await discord_client.send_ai_report_notification(ai_report_data)

            if success:
                print("✅ Japanese AI analysis report sent successfully")
                return True
            else:
                print("❌ Japanese AI analysis report failed")
                return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_japanese_summary():
    """日本語化されたサマリー通知のテスト"""
    print("📋 Testing Japanese summary notification...")

    # レート制限を避けるため待機
    await asyncio.sleep(3)

    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        async with DiscordClient(webhook_url) as discord_client:
            success = await discord_client.send_embed(
                title="📊 日次経済指標サマリー",
                description="本日の主要経済指標の発表結果",
                color=0x0000FF,
                fields=[
                    {
                        "name": "🇯🇵 日本CPI",
                        "value": "実際値: 2.8% (予想上回り)",
                        "inline": True,
                    },
                    {
                        "name": "🇺🇸 米国雇用統計",
                        "value": "実際値: 210K (予想上回り)",
                        "inline": True,
                    },
                    {
                        "name": "🇪🇺 ECB金利",
                        "value": "実際値: 4.50% (予想上回り)",
                        "inline": True,
                    },
                ],
                footer={"text": "経済カレンダーシステム • 自動生成"},
                timestamp=datetime.now(),
            )

            if success:
                print("✅ Japanese summary notification sent successfully")
                return True
            else:
                print("❌ Japanese summary notification failed")
                return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def test_japanese_alert():
    """日本語化されたアラート通知のテスト"""
    print("⚡ Testing Japanese alert notification...")

    # レート制限を避けるため待機
    await asyncio.sleep(3)

    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set")
            return False

        async with DiscordClient(webhook_url) as discord_client:
            success = await discord_client.send_embed(
                title="🚨 リアルタイム経済アラート 🚨",
                description="予想外の高インフレデータが発表されました！",
                color=0xFF0000,
                fields=[
                    {
                        "name": "📈 イベント",
                        "value": "消費者物価指数（CPI）",
                        "inline": True,
                    },
                    {
                        "name": "💥 影響",
                        "value": "高 - USD/JPYの変動性増加",
                        "inline": True,
                    },
                    {
                        "name": "⏰ 時刻",
                        "value": datetime.now().strftime("%Y年%m月%d日 %H:%M JST"),
                        "inline": True,
                    },
                ],
                footer={"text": "即座の対応を推奨"},
                timestamp=datetime.now(),
            )

            if success:
                print("✅ Japanese alert notification sent successfully")
                return True
            else:
                print("❌ Japanese alert notification failed")
                return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


async def main():
    """メイン関数"""
    print("🚀 Japanese Discord Notification Test Suite")
    print("=" * 50)

    results = {}

    # 各テストを順次実行（レート制限を考慮）
    print("\n📊 Running Japanese Discord notification tests...")

    results["economic_event"] = await test_japanese_economic_event()
    await asyncio.sleep(5)  # レート制限を避けるため待機

    results["ai_report"] = await test_japanese_ai_report()
    await asyncio.sleep(5)  # レート制限を避けるため待機

    results["summary"] = await test_japanese_summary()
    await asyncio.sleep(5)  # レート制限を避けるため待機

    results["alert"] = await test_japanese_alert()

    # 結果の表示
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(
        f"   Japanese Economic Event: {'✅ PASS' if results['economic_event'] else '❌ FAIL'}"
    )
    print(f"   Japanese AI Report: {'✅ PASS' if results['ai_report'] else '❌ FAIL'}")
    print(f"   Japanese Summary: {'✅ PASS' if results['summary'] else '❌ FAIL'}")
    print(f"   Japanese Alert: {'✅ PASS' if results['alert'] else '❌ FAIL'}")

    success_count = sum(results.values())
    total_count = len(results)

    if success_count == total_count:
        print("\n🎉 All Japanese Discord notification tests passed!")
        print("✅ Japanese Discord integration is working perfectly")
        print("📈 Ready for live economic data distribution in Japanese")
    elif success_count > 0:
        print(f"\n⚠️ {success_count}/{total_count} tests passed")
        print("✅ Partial Japanese Discord integration is working")
        print("📈 Some features are ready for production")
    else:
        print("\n❌ All Japanese Discord notification tests failed")
        print("Please check the configuration and environment variables")

    return success_count > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
