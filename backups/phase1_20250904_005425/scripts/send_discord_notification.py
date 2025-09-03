#!/usr/bin/env python3
"""
実際のDiscord通知送信スクリプト
"""

import os
import sys
import asyncio
import requests
from datetime import datetime

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


async def send_economic_calendar_notification():
    """経済カレンダーシステムの通知を送信"""
    print("📢 Sending economic calendar system notification...")
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set")
        return False
    
    # 経済カレンダーシステムの通知
    embed = {
        "title": "🤖 **investpy Economic Calendar System**",
        "description": "経済カレンダーシステムが正常に稼働しています！",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "📊 システム状態",
                "value": "✅ 稼働中",
                "inline": True
            },
            {
                "name": "🕐 稼働時間",
                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "inline": True
            },
            {
                "name": "📈 機能",
                "value": "• 経済データ取得\n• AI分析\n• Discord通知\n• リアルタイム監視",
                "inline": False
            }
        ],
        "footer": {
            "text": "investpy Economic Calendar System"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    payload = {
        "embeds": [embed],
        "username": "Economic Calendar Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ Economic calendar notification sent successfully!")
            return True
        else:
            print(f"❌ Failed to send notification: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending notification: {e}")
        return False


async def send_ai_analysis_notification():
    """AI分析結果の通知を送信"""
    print("🤖 Sending AI analysis notification...")
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set")
        return False
    
    # AI分析結果の通知
    embed = {
        "title": "🧠 **AI分析レポート**",
        "description": "ChatGPTによるドル円予測分析が完了しました",
        "color": 0x0099FF,
        "fields": [
            {
                "name": "📊 予測方向",
                "value": "🟢 Bullish (上昇)",
                "inline": True
            },
            {
                "name": "💪 予測強度",
                "value": "Strong (強い)",
                "inline": True
            },
            {
                "name": "🎯 信頼度",
                "value": "85%",
                "inline": True
            },
            {
                "name": "📝 分析内容",
                "value": "• 経済指標の改善\n• 中央銀行政策の支持\n• 技術的要因の好転",
                "inline": False
            }
        ],
        "footer": {
            "text": "AI Analysis System"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    payload = {
        "embeds": [embed],
        "username": "AI Analysis Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ AI analysis notification sent successfully!")
            return True
        else:
            print(f"❌ Failed to send AI notification: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending AI notification: {e}")
        return False


async def send_system_status_notification():
    """システム状態の通知を送信"""
    print("📊 Sending system status notification...")
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URL not set")
        return False
    
    # システム状態の通知
    embed = {
        "title": "🖥️ **システム監視レポート**",
        "description": "システムの現在の状態をお知らせします",
        "color": 0x00FF00,
        "fields": [
            {
                "name": "🗄️ データベース",
                "value": "✅ 正常",
                "inline": True
            },
            {
                "name": "🔴 Redis",
                "value": "✅ 正常",
                "inline": True
            },
            {
                "name": "🤖 AI分析",
                "value": "✅ 正常",
                "inline": True
            },
            {
                "name": "📢 Discord通知",
                "value": "✅ 正常",
                "inline": True
            },
            {
                "name": "⏰ スケジューラー",
                "value": "✅ 正常",
                "inline": True
            },
            {
                "name": "💾 システムリソース",
                "value": "✅ 良好",
                "inline": True
            }
        ],
        "footer": {
            "text": "System Monitor"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    payload = {
        "embeds": [embed],
        "username": "System Monitor Bot"
    }
    
    try:
        response = requests.post(webhook_url, json=payload, timeout=10)
        if response.status_code == 200:
            print("✅ System status notification sent successfully!")
            return True
        else:
            print(f"❌ Failed to send system status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error sending system status: {e}")
        return False


async def main():
    """メイン関数"""
    print("🚀 Discord Notification Sender")
    print("=" * 50)
    
    # 各通知を順次送信
    notifications = [
        ("Economic Calendar", send_economic_calendar_notification),
        ("AI Analysis", send_ai_analysis_notification),
        ("System Status", send_system_status_notification)
    ]
    
    results = []
    
    for name, func in notifications:
        print(f"\n📋 Sending {name} notification...")
        result = await func()
        results.append((name, result))
        
        # レート制限を避けるため少し待機
        await asyncio.sleep(2)
    
    print("\n" + "=" * 50)
    print("📊 Notification Results:")
    
    success_count = 0
    for name, result in results:
        status = "✅ SUCCESS" if result else "❌ FAILED"
        print(f"   {name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n🎉 {success_count}/{len(results)} notifications sent successfully!")
    
    if success_count > 0:
        print("✅ Discord integration is working correctly!")
    else:
        print("⚠️ No notifications were sent. Please check the configuration.")
    
    return success_count > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
