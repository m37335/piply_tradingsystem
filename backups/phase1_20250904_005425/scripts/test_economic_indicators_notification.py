#!/usr/bin/env python3
"""
経済指標チャンネルへのDiscord通知テストスクリプト（日本語版）
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import Any, Dict, List

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# .envファイルの読み込み
try:
    from dotenv import load_dotenv
    load_dotenv('/app/.env')
    print("✅ .env file loaded successfully")
except ImportError:
    print("⚠️ python-dotenv not available, using system environment variables")
except FileNotFoundError:
    print("⚠️ .env file not found, using system environment variables")

async def test_economic_indicators_channel_notification():
    """経済指標チャンネルへのDiscord通知機能のテスト（日本語版）"""
    print("📊 Testing economic indicators channel notification (Japanese)...")

    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient
        from src.domain.entities.economic_event.economic_event import EconomicEvent, Importance
        from src.domain.entities.ai_report.ai_report import AIReport, ReportType
        from src.domain.entities.ai_report.usd_jpy_prediction import USDJPYPrediction, PredictionDirection, PredictionStrength

        # 経済指標チャンネルのWebhook URLを取得
        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print("❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set in environment variables")
            print("Please set DISCORD_ECONOMICINDICATORS_WEBHOOK_URL in your .env file")
            return False

        print(f"✅ Economic indicators webhook URL found: {webhook_url[:50]}...")

        async with DiscordClient(webhook_url) as discord_client:
            print("\n📈 Testing economic indicator notifications (Japanese)...")

            # テスト用の経済イベントデータ（日本語対応）
            events_to_test = [
                {
                    "event_id": "jp_cpi_001",
                    "date_utc": datetime(2025, 8, 22, 0, 0).isoformat(),
                    "country": "japan",
                    "event_name": "Consumer Price Index (CPI) y/y",
                    "importance": "high",
                    "actual_value": 2.8,
                    "forecast_value": 2.5,
                    "previous_value": 2.3,
                    "currency": "JPY",
                    "unit": "%",
                    "surprise": 0.3, # Positive surprise
                },
                {
                    "event_id": "us_nfp_001",
                    "date_utc": datetime(2025, 8, 22, 12, 30).isoformat(),
                    "country": "united states",
                    "event_name": "Non-Farm Payrolls",
                    "importance": "high",
                    "actual_value": 210000,
                    "forecast_value": 185000,
                    "previous_value": 180000,
                    "currency": "USD",
                    "unit": "K",
                    "surprise": 25000, # Positive surprise
                },
                {
                    "event_id": "eu_ecb_001",
                    "date_utc": datetime(2025, 8, 22, 14, 0).isoformat(),
                    "country": "euro zone",
                    "event_name": "ECB Interest Rate Decision",
                    "importance": "high",
                    "actual_value": 4.50,
                    "forecast_value": 4.25,
                    "previous_value": 4.25,
                    "currency": "EUR",
                    "unit": "%",
                    "surprise": 0.25, # Positive surprise
                },
            ]

            sent_count = 0
            for i, event_data in enumerate(events_to_test):
                print(f"\n📊 Testing event {i+1}/{len(events_to_test)}: {event_data['event_name']}")
                success = await discord_client.send_economic_event_notification(event_data, "actual_announcement")
                if success:
                    print(f"✅ {event_data['country']} {event_data['event_name']} notification sent")
                    sent_count += 1
                else:
                    print(f"❌ {event_data['country']} {event_data['event_name']} notification failed")

            # AI分析レポート通知のテスト（レポート形式）
            print("\n🤖 Testing AI analysis report (Report format)...")
            test_ai_report_data = {
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
                        "リスク回避需要の高まり"
                    ],
                    "timeframe": "1-4時間",
                    "target_price": "148.50-150.00"
                },
                "confidence_score": 0.82,
            }
            ai_success = await discord_client.send_ai_report_notification(test_ai_report_data)
            if ai_success:
                print("✅ AI analysis report notification sent")
                sent_count += 1
            else:
                print("❌ AI analysis report notification failed")

            # サマリー通知のテスト（日本語版）
            print("\n📋 Testing summary notification (Japanese)...")
            summary_success = await discord_client.send_embed(
                title="📊 日次経済指標サマリー",
                description="本日の主要経済指標の発表結果",
                color=0x0000FF,
                fields=[
                    {"name": "🇯🇵 日本CPI", "value": "実際値: 2.8% (予想上回り)", "inline": True},
                    {"name": "🇺🇸 米国雇用統計", "value": "実際値: 210K (予想上回り)", "inline": True},
                    {"name": "🇪🇺 ECB金利", "value": "実際値: 4.50% (予想上回り)", "inline": True},
                ],
                footer={"text": "経済カレンダーシステム • 自動生成"},
                timestamp=datetime.now()
            )
            if summary_success:
                print("✅ Summary notification sent")
                sent_count += 1
            else:
                print("❌ Summary notification failed")

            print(f"\n📊 Test Results: {sent_count}/{len(events_to_test) + 2} notifications sent successfully")

            # リアルタイム経済アラートのテスト（日本語版）
            print("\n⚡ Testing real-time economic alert (Japanese)...")
            alert_success = await discord_client.send_embed(
                title="🚨 リアルタイム経済アラート 🚨",
                description="予想外の高インフレデータが発表されました！",
                color=0xFF0000, # Red for alert
                fields=[
                    {"name": "📈 イベント", "value": "消費者物価指数（CPI）", "inline": True},
                    {"name": "💥 影響", "value": "高 - USD/JPYの変動性増加", "inline": True},
                    {"name": "⏰ 時刻", "value": datetime.now().strftime("%Y年%m月%d日 %H:%M JST"), "inline": True},
                ],
                footer={"text": "即座の対応を推奨"},
                timestamp=datetime.now()
            )
            if alert_success:
                print("✅ Real-time economic alert sent successfully")
                sent_count += 1
            else:
                print("❌ Real-time economic alert failed")

            return sent_count == (len(events_to_test) + 3) # All 3 events + AI + Summary + Alert

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def main():
    """メイン関数"""
    print("🚀 Economic Indicators Channel Test Suite (Japanese)")
    print("=" * 60)

    success = await test_economic_indicators_channel_notification()

    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Economic Indicators Notification (Japanese): {'✅ PASS' if success else '❌ FAIL'}")
    print(f"   AI Analysis Report Format: {'✅ PASS' if success else '❌ FAIL'}")
    print(f"   Real-time Economic Alert (Japanese): {'✅ PASS' if success else '❌ FAIL'}")

    if success:
        print("\n🎉 All economic indicators channel tests passed!")
        print("✅ Japanese Discord integration is working correctly")
        print("📈 Ready for live economic data distribution in Japanese")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration and environment variables.")

    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
