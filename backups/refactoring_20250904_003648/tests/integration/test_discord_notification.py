"""
Discord通知配信テスト

実際のDiscord Webhookを使用して各パターンの通知を送信するテスト
"""

import asyncio
import os
import sys
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.domain.value_objects.pattern_priority import PatternPriority
from src.infrastructure.discord_webhook_sender import DiscordWebhookSender
from src.infrastructure.messaging.templates import (
    Pattern1Template,
    Pattern2Template,
    Pattern3Template,
    Pattern4Template,
    Pattern6Template,
)


async def test_pattern1_notification(webhook_sender: DiscordWebhookSender):
    """パターン1の通知テスト"""
    print("=== パターン1: 強力なトレンド転換シグナル ===")

    template = Pattern1Template()

    # モック検出結果
    detection_result = {
        "pattern_number": 1,
        "pattern_name": "強力なトレンド転換シグナル",
        "priority": PatternPriority.HIGH,
        "confidence_score": 0.85,
        "notification_title": "🚨 強力な売りシグナル検出！",
        "notification_color": "0xFF0000",
        "take_profit": "-50pips",
        "stop_loss": "+30pips",
        "current_price": 150.25,
        "rsi_value": 75.5,
        "macd_value": -0.15,
        "bb_upper": 150.80,
        "bb_lower": 149.70,
    }

    # Embedを作成
    embed = template.create_embed(detection_result, "USD/JPY")

    # Discordに送信
    success = await webhook_sender.send_embed(embed)

    if success:
        print("✅ パターン1通知を送信しました")
    else:
        print("❌ パターン1通知の送信に失敗しました")

    return success


async def test_pattern2_notification(webhook_sender: DiscordWebhookSender):
    """パターン2の通知テスト"""
    print("\n=== パターン2: 押し目買いチャンス ===")

    template = Pattern2Template()

    # モック検出結果
    detection_result = {
        "pattern_number": 2,
        "pattern_name": "押し目買いチャンス",
        "priority": PatternPriority.MEDIUM,
        "confidence_score": 0.75,
        "notification_title": "📈 押し目買いチャンス！",
        "notification_color": "0x00FF00",
        "take_profit": "+80pips",
        "stop_loss": "-40pips",
        "current_price": 149.85,
        "rsi_value": 35.2,
        "macd_value": 0.08,
        "bb_upper": 150.20,
        "bb_lower": 149.50,
    }

    # Embedを作成
    embed = template.create_embed(detection_result, "USD/JPY")

    # Discordに送信
    success = await webhook_sender.send_embed(embed)

    if success:
        print("✅ パターン2通知を送信しました")
    else:
        print("❌ パターン2通知の送信に失敗しました")

    return success


async def test_pattern3_notification(webhook_sender: DiscordWebhookSender):
    """パターン3の通知テスト"""
    print("\n=== パターン3: ダイバージェンス警戒 ===")

    template = Pattern3Template()

    # モック検出結果
    detection_result = {
        "pattern_number": 3,
        "pattern_name": "ダイバージェンス警戒",
        "priority": PatternPriority.HIGH,
        "confidence_score": 0.80,
        "notification_title": "⚠️ ダイバージェンス警戒！",
        "notification_color": "0xFFFF00",
        "strategy": "利確推奨",
        "risk": "急落可能性",
        "current_price": 150.10,
        "rsi_value": 85.0,
        "macd_value": -0.25,
        "bb_upper": 150.60,
        "bb_lower": 149.90,
    }

    # Embedを作成
    embed = template.create_embed(detection_result, "USD/JPY")

    # Discordに送信
    success = await webhook_sender.send_embed(embed)

    if success:
        print("✅ パターン3通知を送信しました")
    else:
        print("❌ パターン3通知の送信に失敗しました")

    return success


async def test_pattern4_notification(webhook_sender: DiscordWebhookSender):
    """パターン4の通知テスト"""
    print("\n=== パターン4: ブレイクアウト狙い ===")

    template = Pattern4Template()

    # モック検出結果
    detection_result = {
        "pattern_number": 4,
        "pattern_name": "ブレイクアウト狙い",
        "priority": PatternPriority.MEDIUM,
        "confidence_score": 0.70,
        "notification_title": "🚀 ブレイクアウト狙い！",
        "notification_color": "0x00FFFF",
        "take_profit": "+100pips",
        "stop_loss": "-50pips",
        "current_price": 150.40,
        "rsi_value": 65.5,
        "macd_value": 0.12,
        "bb_upper": 150.90,
        "bb_lower": 149.80,
    }

    # Embedを作成
    embed = template.create_embed(detection_result, "USD/JPY")

    # Discordに送信
    success = await webhook_sender.send_embed(embed)

    if success:
        print("✅ パターン4通知を送信しました")
    else:
        print("❌ パターン4通知の送信に失敗しました")

    return success


async def test_pattern6_notification(webhook_sender: DiscordWebhookSender):
    """パターン6の通知テスト"""
    print("\n=== パターン6: 複合シグナル強化 ===")

    template = Pattern6Template()

    # モック検出結果
    detection_result = {
        "pattern_number": 6,
        "pattern_name": "複合シグナル強化",
        "priority": PatternPriority.VERY_HIGH,
        "confidence_score": 0.95,
        "notification_title": "💪 複合シグナル強化！",
        "notification_color": "0x800080",
        "take_profit": "+120pips",
        "stop_loss": "-60pips",
        "current_price": 150.15,
        "rsi_value": 45.8,
        "macd_value": 0.18,
        "bb_upper": 150.70,
        "bb_lower": 149.60,
    }

    # Embedを作成
    embed = template.create_embed(detection_result, "USD/JPY")

    # Discordに送信
    success = await webhook_sender.send_embed(embed)

    if success:
        print("✅ パターン6通知を送信しました")
    else:
        print("❌ パターン6通知の送信に失敗しました")

    return success


async def test_simple_message(webhook_sender: DiscordWebhookSender):
    """シンプルメッセージのテスト"""
    print("\n=== シンプルメッセージテスト ===")

    message = (
        "🎯 **Discord通知パターンシステム**\n"
        "テスト配信が完了しました！\n"
        f"時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        "✅ 全パターンの通知が正常に送信されました"
    )

    success = await webhook_sender.send_simple_message(message)

    if success:
        print("✅ シンプルメッセージを送信しました")
    else:
        print("❌ シンプルメッセージの送信に失敗しました")

    return success


async def main():
    """メイン関数"""
    print("🚀 Discord通知配信テスト開始")
    print(f"開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Webhook URLを取得（環境変数または入力）
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "")

    if not webhook_url:
        print("Discord Webhook URLを入力してください:")
        webhook_url = input().strip()

    if not webhook_url:
        print("❌ Webhook URLが設定されていません")
        return

    # テスト実行
    async with DiscordWebhookSender(webhook_url) as webhook_sender:
        results = []

        # 各パターンのテスト
        results.append(await test_pattern1_notification(webhook_sender))
        await asyncio.sleep(2)  # 2秒間隔

        results.append(await test_pattern2_notification(webhook_sender))
        await asyncio.sleep(2)

        results.append(await test_pattern3_notification(webhook_sender))
        await asyncio.sleep(2)

        results.append(await test_pattern4_notification(webhook_sender))
        await asyncio.sleep(2)

        results.append(await test_pattern6_notification(webhook_sender))
        await asyncio.sleep(2)

        # シンプルメッセージ
        results.append(await test_simple_message(webhook_sender))

        # 結果サマリー
        print(f"\n📊 テスト結果サマリー")
        print(f"成功: {sum(results)}件")
        print(f"失敗: {len(results) - sum(results)}件")
        print(f"成功率: {sum(results) / len(results) * 100:.1f}%")

        if all(results):
            print("🎉 全てのテストが成功しました！")
        else:
            print("⚠️ 一部のテストが失敗しました")

    print(f"\n完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    asyncio.run(main())
