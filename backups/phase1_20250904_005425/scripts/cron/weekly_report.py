#!/usr/bin/env python3
"""
Weekly Report Script for Cron
週次レポート送信スクリプト
"""

import asyncio
import os
import subprocess
from datetime import datetime

import pytz


async def weekly_report():
    try:
        jst = pytz.timezone("Asia/Tokyo")
        current_time = datetime.now(jst)
        print(f'Weekly stats: {current_time.strftime("%Y-%m-%d %H:%M:%S JST")}')

        # Alpha Vantage接続テスト
        result = subprocess.run(
            ["python", "test_alphavantage.py", "--test", "connection"],
            capture_output=True,
            text=True,
            cwd="/app",
        )
        av_status = result.returncode == 0

        # 環境変数テスト
        env_result = subprocess.run(
            ["python", "test_env_loading.py"],
            capture_output=True,
            text=True,
            cwd="/app",
        )
        env_status = env_result.returncode == 0

        print(f"Alpha Vantage test: {av_status}")
        print(f"Environment loading: {env_status}")

        # Discord週次レポート送信
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            import httpx

            message = {
                "content": "📊 **週次システムレポート**",
                "embeds": [
                    {
                        "title": "📈 Weekly System Report",
                        "description": "Exchange Analytics システム週次統計",
                        "color": 0x0099FF,
                        "fields": [
                            {
                                "name": "⏰ 時刻",
                                "value": current_time.strftime("%Y-%m-%d %H:%M:%S JST"),
                                "inline": True,
                            },
                            {
                                "name": "🔑 Alpha Vantage",
                                "value": "✅ 正常" if av_status else "❌ エラー",
                                "inline": True,
                            },
                            {
                                "name": "🔧 環境変数",
                                "value": "✅ 正常" if env_status else "❌ エラー",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "Weekly System Monitor"},
                    }
                ],
            }

            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(webhook_url, json=message)
            print("Discord週次レポート送信完了")

    except Exception as e:
        print(f"Weekly stats error: {e}")


if __name__ == "__main__":
    asyncio.run(weekly_report())
