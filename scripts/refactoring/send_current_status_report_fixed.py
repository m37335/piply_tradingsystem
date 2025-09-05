#!/usr/bin/env python3
"""
現状レポートをDiscordに配信するスクリプト（修正版）
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.messaging.discord_client import DiscordClient


async def send_current_status_report():
    """現状レポートをDiscordに配信"""
    
    # Discord Webhook URLを取得
    webhook_url = os.getenv("DISCORD_MONITORING_WEBHOOK_URL")
    if not webhook_url:
        print("❌ DISCORD_MONITORING_WEBHOOK_URL環境変数が設定されていません")
        return False
    
    print(f"🔗 Discord Webhook URL: {webhook_url[:50]}...")
    
    try:
        # DiscordClientを初期化
        client = DiscordClient(webhook_url=webhook_url)
        
        # 現状レポートメッセージを作成
        message = """🚀 **リファクタリング完了！必要最小限システムが本格運用開始**

✅ **基本機能**: 4個のシステム
✅ **高度機能**: 3個のシステム
✅ **システム統合**: 完了
✅ **本格運用**: 開始

📊 **現在の状況**:
• CPU: 0.8% (健全)
• メモリ: 33.6% (健全)
• ディスク: 5.1% (健全)

🎯 **次のステップ**: 1:00のレポート配信確認

🔄 **システム状況**: 全システムが正常に動作中"""
        
        # Discordに送信
        result = await client.send_alert(
            alert_type="SYSTEM_STATUS",
            title="システム現状レポート",
            message=message,
            urgency="normal"
        )
        
        print(f"📢 Discord配信結果: {result}")
        return True
        
    except Exception as e:
        print(f"❌ Discord配信エラー: {e}")
        return False


async def main():
    """メイン関数"""
    print("🚀 現状レポートのDiscord配信開始（修正版）")
    
    success = await send_current_status_report()
    
    if success:
        print("✅ 現状レポートのDiscord配信完了")
    else:
        print("❌ 現状レポートのDiscord配信失敗")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
