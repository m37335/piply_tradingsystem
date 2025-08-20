#!/usr/bin/env python3
"""
Discord通知の簡単なテスト
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_discord_simple():
    """Discord通知の簡単なテスト"""
    print("🔍 Discord通知の簡単なテスト")
    print("=" * 50)
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    print(f"Webhook URL: {webhook_url[:50]}..." if webhook_url else "Webhook URL: 未設定")
    
    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URLが設定されていません")
        return
    
    try:
        # DiscordNotificationServiceをインポート
        from src.domain.services.notification.discord_notification_service import DiscordNotificationService
        
        print("📤 Discordにテストメッセージを送信中...")
        
        async with DiscordNotificationService(webhook_url) as notification_service:
            # 簡単なテストメッセージ
            test_message = """
🧪 **Discord通知テスト**

✅ このメッセージが表示されれば、Discord通知は正常に動作しています！

📊 **テスト内容**
- アラートシステムのDiscord通知機能
- 最適化された戦略の配信
- プロトレーダー向けアラート

🚀 システムは正常に稼働中です！
            """
            
            await notification_service._send_message(test_message)
            print("✅ Discord通知テスト成功！")
            
            # 買いシグナルのテスト
            buy_message = """
🚨 **最適化アラートシステム**

🟢 **買いエントリー**
📈 **上昇トレンドシグナル検出**

📊 **シグナル詳細**
- 時刻: 2025-01-14 00:00:00
- エントリー方向: 🟢 買いエントリー
- RSI: 37.3
- 現在価格: 146.959

🎯 **エントリー戦略**
- エントリー価格: 147.289
- 利確目標: 147.289
- 損切り: 147.289

💰 **期待値**
- 期待利益: 66.1pips
- 期待リスク: 106.2pips
- リスク/リワード比: 0.62

📈 **戦略**
- 戦略名: EMA_12_Optimized
- 信頼度: HIGH

---
*最適化された移動平均線戦略による自動アラート*
            """
            
            await notification_service._send_message(buy_message)
            print("✅ 買いシグナルテスト成功！")
            
    except Exception as e:
        print(f"❌ Discord通知エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_discord_simple())
