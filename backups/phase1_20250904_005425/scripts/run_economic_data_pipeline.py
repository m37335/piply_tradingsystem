#!/usr/bin/env python3
"""
investpy Economic Calendar System - データパイプライン実行スクリプト（日本語版）
経済カレンダーデータの取得、AI分析、Discord通知を統合して実行
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
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


async def run_japanese_discord_pipeline():
    """
    日本語化されたDiscord配信パイプラインのテスト実行
    """
    print("🚀 Starting Japanese Discord Pipeline Test...")
    print("============================================================")

    try:
        from src.infrastructure.external.discord.discord_client import DiscordClient

        print("✅ Discord client imported successfully")

        # 経済指標チャンネルのWebhook URLを取得
        webhook_url = os.getenv("DISCORD_ECONOMICINDICATORS_WEBHOOK_URL")
        if not webhook_url:
            print(
                "❌ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL not set. Cannot send test notification."
            )
            return False

        async with DiscordClient(webhook_url) as discord_client:
            print("✅ Discord client connected successfully")

            # 日本語化された経済イベント通知のテスト
            print("\n📊 Testing Japanese economic event notification...")
            event_data = {
                "event_id": "jp_cpi_pipeline_test",
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

            event_success = await discord_client.send_economic_event_notification(
                event_data, "actual_announcement"
            )

            if event_success:
                print("✅ Japanese economic event notification sent successfully")
            else:
                print("❌ Japanese economic event notification failed")
                return False

            # 日本語化されたAI分析レポートのテスト
            print("\n🤖 Testing Japanese AI analysis report...")
            await asyncio.sleep(3)  # レート制限を避けるため待機

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

            ai_success = await discord_client.send_ai_report_notification(
                ai_report_data
            )

            if ai_success:
                print("✅ Japanese AI analysis report sent successfully")
            else:
                print("❌ Japanese AI analysis report failed")
                return False

            # 日本語化されたサマリー通知のテスト
            print("\n📋 Testing Japanese summary notification...")
            await asyncio.sleep(3)  # レート制限を避けるため待機

            summary_success = await discord_client.send_embed(
                title="📊 経済データパイプライン稼働報告",
                description="日本語化されたDiscord配信システムが正常に稼働しています",
                color=0x00C851,
                fields=[
                    {
                        "name": "🇯🇵 日本語化",
                        "value": "✅ 経済指標名・国名・時刻表示",
                        "inline": True,
                    },
                    {
                        "name": "🤖 AI分析",
                        "value": "✅ レポート形式・分析理由",
                        "inline": True,
                    },
                    {
                        "name": "📈 配信先",
                        "value": "✅ DISCORD_ECONOMICINDICATORS_WEBHOOK_URL",
                        "inline": True,
                    },
                    {
                        "name": "⏰ 稼働時刻",
                        "value": datetime.now().strftime("%Y年%m月%d日 %H:%M:%S JST"),
                        "inline": True,
                    },
                ],
                footer={"text": "🎉 日本語化Discord配信パイプライン稼働中"},
                timestamp=datetime.now(),
            )

            if summary_success:
                print("✅ Japanese summary notification sent successfully")
            else:
                print("❌ Japanese summary notification failed")
                return False

            print("\n🎉 All Japanese Discord pipeline tests completed successfully!")
            return True

    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False
    finally:
        print("============================================================")


async def main():
    """メイン実行関数"""
    pipeline_success = await run_japanese_discord_pipeline()

    print("\n============================================================")
    if pipeline_success:
        print("✅ Japanese Discord pipeline completed successfully!")
        print("📈 The system is ready for live economic data distribution in Japanese")
        print(
            "🎯 All notifications will be sent to DISCORD_ECONOMICINDICATORS_WEBHOOK_URL"
        )
    else:
        print("⚠️ Japanese Discord pipeline completed with some issues")
        print("🔧 Please check configuration and module implementations")
    print("============================================================")
    sys.exit(0 if pipeline_success else 1)


if __name__ == "__main__":
    asyncio.run(main())
