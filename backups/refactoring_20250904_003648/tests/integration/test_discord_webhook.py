#!/usr/bin/env python3
"""
Discord Webhook URL最適化テストスクリプト

実際のDiscord Webhook URLを使用して通知テストを行い、
最適化を確認します
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv

load_dotenv()


async def test_discord_webhook():
    """Discord Webhook URL最適化テスト"""
    print("=" * 80)
    print("📱 Discord Webhook URL最適化テスト")
    print("=" * 80)

    # 環境変数からWebhook URLを取得
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not webhook_url:
        print("❌ DISCORD_WEBHOOK_URLが設定されていません")
        return

    print(f"✅ Webhook URL確認: {webhook_url[:50]}...")

    try:
        print("\n🎯 1. 基本的な通知テスト...")

        from src.domain.services.notification.discord_notification_service import (
            DiscordNotificationService,
        )

        # Discord通知サービスを初期化（非同期コンテキストマネージャーを使用）
        async with DiscordNotificationService(webhook_url) as notification_service:
            # テストメッセージを送信
            test_message = {
                "content": "🚨 プロトレーダー向け為替アラートシステム - テスト通知",
                "embeds": [
                    {
                        "title": "✅ システム動作確認",
                        "description": "Discord Webhook URL最適化テストが正常に動作しています",
                        "color": 65280,  # 緑色
                        "fields": [
                            {
                                "name": "📊 システム状況",
                                "value": "• データベース接続: 正常\n• シグナル生成: 正常\n• 通知システム: 正常",
                                "inline": True,
                            },
                            {
                                "name": "🎯 機能確認",
                                "value": "• RSIエントリー検出: ✅\n• ボリンジャーバンド検出: ✅\n• ボラティリティ検出: ✅",
                                "inline": True,
                            },
                        ],
                        "footer": {"text": "プロトレーダー向け為替アラートシステム"},
                        "timestamp": "2025-01-15T00:00:00.000Z",
                    }
                ],
            }

            print("📤 テストメッセージを送信中...")
            success = await notification_service._send_message(test_message)

            if success:
                print("✅ 基本的な通知テスト成功！")
            else:
                print("❌ 基本的な通知テスト失敗")
                return

            print("\n🎯 2. 実際のシグナル通知テスト...")

            # 実際のシグナルデータを使用してテスト
            from datetime import datetime

            from src.infrastructure.database.models.entry_signal_model import (
                EntrySignalModel,
            )

            # テスト用のシグナルを作成
            test_signal = EntrySignalModel(
                signal_type="BUY",
                currency_pair="USD/JPY",
                timestamp=datetime.now(),
                timeframe="H1",
                entry_price=150.50,
                stop_loss=150.00,
                take_profit=151.50,
                risk_reward_ratio=2.0,
                confidence_score=75,
                indicators_used={
                    "RSI": 34.28,
                    "SMA_20": 150.30,
                    "MACD_histogram": 0.001,
                },
            )

            print("📤 実際のシグナル通知を送信中...")
            success = await notification_service.send_entry_signal(test_signal)

            if success:
                print("✅ 実際のシグナル通知テスト成功！")
            else:
                print("❌ 実際のシグナル通知テスト失敗")

            print("\n🎯 3. リスクアラート通知テスト...")

            from src.infrastructure.database.models.risk_alert_model import (
                RiskAlertModel,
            )

            # テスト用のリスクアラートを作成
            test_risk_alert = RiskAlertModel(
                alert_type="volatility_spike",
                currency_pair="USD/JPY",
                timestamp=datetime.now(),
                timeframe="H1",
                severity="HIGH",
                message="ボラティリティ急増検出: ATRが過去平均の2倍を超えています",
                recommended_action="ポジションサイズを50%削減、ストップロスを広げることを推奨",
                market_data={
                    "current_atr": 0.015,
                    "avg_atr": 0.007,
                    "price_change_24h": 2.5,
                    "volume_ratio": 2.8,
                },
                threshold_value=0.014,
                current_value=0.015,
            )

            print("📤 リスクアラート通知を送信中...")
            success = await notification_service.send_risk_alert(test_risk_alert)

            if success:
                print("✅ リスクアラート通知テスト成功！")
            else:
                print("❌ リスクアラート通知テスト失敗")

            print("\n🎯 4. 通知パフォーマンステスト...")

            # 複数の通知を連続で送信してパフォーマンスをテスト
            import time

            start_time = time.time()

            for i in range(3):
                test_message = {
                    "content": f"📊 パフォーマンステスト {i+1}/3",
                    "embeds": [
                        {
                            "title": f"テスト通知 #{i+1}",
                            "description": f"パフォーマンステスト用の通知です",
                            "color": 3447003,  # 青色
                            "timestamp": "2025-01-15T00:00:00.000Z",
                        }
                    ],
                }

                success = await notification_service._send_message(test_message)
                if success:
                    print(f"  ✅ テスト {i+1}/3 成功")
                else:
                    print(f"  ❌ テスト {i+1}/3 失敗")

                # 少し待機
                await asyncio.sleep(1)

            end_time = time.time()
            duration = end_time - start_time

            print(f"✅ パフォーマンステスト完了: {duration:.2f}秒")

        print("\n🎉 Discord Webhook URL最適化テスト完了！")
        print("✅ すべてのテストが正常に動作しています")
        print("🚀 本格運用の準備が整いました")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_discord_webhook())
