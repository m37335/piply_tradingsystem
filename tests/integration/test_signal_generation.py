#!/usr/bin/env python3
"""
シグナル生成テストスクリプト

過去のデータを使用してシグナル生成をテストし、
Discordへの配信を確認します
"""

import asyncio
import os
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

# 環境変数を読み込み
from dotenv import load_dotenv
from sqlalchemy import text

load_dotenv()


async def test_signal_generation():
    """シグナル生成テスト"""
    print("=" * 80)
    print("🚨 シグナル生成テスト")
    print("=" * 80)

    # データベース接続
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    database_url = os.getenv("DATABASE_URL")
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with async_session() as db_session:
            print("\n🔍 1. 過去のRSIデータでシグナル生成テスト...")
            
            # 過去のRSIデータを確認
            result = await db_session.execute(
                text("""
                SELECT 
                    value,
                    timestamp,
                    timeframe
                FROM technical_indicators
                WHERE indicator_type = 'RSI'
                AND timestamp >= NOW() - INTERVAL '7 days'
                ORDER BY timestamp DESC
                LIMIT 20
                """)
            )
            rsi_data = result.fetchall()
            
            print(f"✅ 過去7日のRSIデータ: {len(rsi_data)}件")
            
            # シグナル生成条件を満たすデータを探す
            signal_candidates = []
            for value, timestamp, timeframe in rsi_data:
                if value < 30 or value > 70:  # 過売りまたは過買い
                    signal_candidates.append((value, timestamp, timeframe))
            
            print(f"✅ シグナル候補: {len(signal_candidates)}件")
            for value, timestamp, timeframe in signal_candidates[:5]:
                status = "過売り" if value < 30 else "過買い"
                print(f"  📊 RSI ({timeframe}): {value:.2f} - {status} at {timestamp}")

            print("\n🎯 2. RSIエントリー検出器でシグナル生成...")
            
            from src.domain.services.alert_engine.rsi_entry_detector import RSIEntryDetector
            
            rsi_detector = RSIEntryDetector(db_session)
            
            # 複数のタイムフレームでテスト
            timeframes = ["M5", "H1", "H4"]
            all_signals = []
            
            for timeframe in timeframes:
                print(f"\n📊 {timeframe}タイムフレームでテスト...")
                signals = await rsi_detector.detect_rsi_entry_signals(timeframe)
                print(f"✅ {timeframe}: {len(signals)}個のシグナル生成")
                all_signals.extend(signals)
                
                for signal in signals[:2]:  # 最初の2個を表示
                    print(f"  🚨 {signal.signal_type} - 信頼度{signal.confidence_score}% - 価格{signal.entry_price}")

            print(f"\n🎉 総シグナル数: {len(all_signals)}個")

            if all_signals:
                print("\n📱 3. Discord通知テスト...")
                
                from src.domain.services.notification.discord_notification_service import DiscordNotificationService
                
                # テスト用のWebhook URL（実際のDiscord Webhook URLに変更してください）
                notification_service = DiscordNotificationService("https://discord.com/api/webhooks/test")
                
                # 最初のシグナルで通知テスト
                test_signal = all_signals[0]
                message = notification_service._format_entry_signal(test_signal)
                
                print(f"✅ 通知メッセージ生成: {len(str(message))}文字")
                print("📋 メッセージ内容:")
                print("-" * 50)
                print(str(message)[:500] + "..." if len(str(message)) > 500 else str(message))
                print("-" * 50)
                
                # 実際のDiscord Webhook URLがある場合は送信テスト
                webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
                if webhook_url:
                    print(f"\n🚀 実際のDiscord Webhook URLが設定されています")
                    print("⚠️ 実際のDiscordチャンネルに送信されます")
                    
                    # ユーザーに確認
                    response = input("Discordに送信しますか？ (y/N): ")
                    if response.lower() == 'y':
                        success = await notification_service.send_entry_signal(test_signal)
                        if success:
                            print("✅ Discord通知送信成功！")
                        else:
                            print("❌ Discord通知送信失敗")
                    else:
                        print("ℹ️ Discord送信をスキップしました")
                else:
                    print("ℹ️ DISCORD_WEBHOOK_URLが設定されていないため、送信テストをスキップ")
            else:
                print("\n⚠️ シグナルが生成されませんでした")
                print("🔧 条件を緩和してテストします...")
                
                # 条件を緩和したテスト
                print("\n🎯 4. 条件緩和テスト...")
                
                # RSIの閾値を緩和（30/70 → 35/65）
                result = await db_session.execute(
                    text("""
                    SELECT 
                        value,
                        timestamp,
                        timeframe
                    FROM technical_indicators
                    WHERE indicator_type = 'RSI'
                    AND (value < 35 OR value > 65)
                    AND timestamp >= NOW() - INTERVAL '7 days'
                    ORDER BY timestamp DESC
                    LIMIT 10
                    """)
                )
                relaxed_candidates = result.fetchall()
                
                print(f"✅ 緩和条件での候補: {len(relaxed_candidates)}件")
                for value, timestamp, timeframe in relaxed_candidates:
                    status = "過売り傾向" if value < 35 else "過買い傾向"
                    print(f"  📊 RSI ({timeframe}): {value:.2f} - {status} at {timestamp}")

    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if engine:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_signal_generation())
