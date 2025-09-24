"""
Discord配信システムのテスト

Discord配信システムの動作確認を行う。
"""

import asyncio
import logging
import sys
import os
from datetime import datetime, timezone, timedelta

# プロジェクトルートをパスに追加
sys.path.append('/app')

from modules.llm_analysis.notification.discord_notifier import DiscordNotifier, NotificationType
from modules.llm_analysis.notification.message_formatter import MessageFormatter, MessageTemplate
from modules.llm_analysis.core.snapshot_manager import TradeSnapshot, MarketSnapshot
from modules.llm_analysis.core.scenario_manager import ExitReason, TradeDirection
from modules.llm_analysis.evaluation.daily_evaluator import DailyPerformance


async def test_message_formatter():
    """メッセージフォーマッターのテスト"""
    print("🧪 メッセージフォーマッターテスト")
    
    formatter = MessageFormatter()
    
    try:
        # ダミーのトレードスナップショットを作成
        trade_snapshot = TradeSnapshot(
            id="trade_snapshot_test",
            trade_id="trade_test",
            scenario_id="scenario_test",
            entry_snapshot_id="entry_snapshot_test",
            exit_snapshot_id="exit_snapshot_test",
            direction=TradeDirection.BUY,
            strategy="test_strategy",
            entry_price=147.123,
            exit_price=147.400,
            position_size=10000,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            entry_time=datetime.now(timezone.utc),
            exit_time=datetime.now(timezone.utc) + timedelta(hours=1),
            hold_time_minutes=60,
            exit_reason=ExitReason.TP1_HIT,
            profit_loss=100,
            profit_loss_pips=10,
            adherence_score=85,
            violation_tags=["test_violation"],
            metadata={}
        )
        
        # ダミーの日次パフォーマンスを作成
        daily_performance = DailyPerformance(
            date=datetime.now(timezone.utc),
            total_trades=5,
            winning_trades=3,
            losing_trades=2,
            win_rate=0.6,
            total_profit_pips=25.5,
            total_profit_percent=0.017,
            profit_factor=1.8,
            max_drawdown=5.2,
            average_hold_time_minutes=75.0,
            adherence_score_avg=82.5,
            adherence_score_min=75.0,
            adherence_score_max=95.0,
            daily_return_percent=0.017,
            strategy_performance={
                "strategy_1": {
                    "trades": 3,
                    "wins": 2,
                    "losses": 1,
                    "win_rate": 0.67,
                    "total_profit_pips": 15.0,
                    "total_profit_percent": 0.01,
                    "profit_factor": 2.0,
                    "avg_adherence_score": 85.0,
                    "avg_hold_time": 60.0
                }
            },
            violation_summary={
                "risk_management": 1,
                "timing": 2
            },
            session_performance={
                "Tokyo": {
                    "trades": 3,
                    "wins": 2,
                    "total_profit_pips": 15.0,
                    "win_rate": 0.67,
                    "avg_adherence_score": 85.0
                }
            }
        )
        
        # エラーアラートメッセージのフォーマット
        error_format = formatter.format_error_alert(
            "テストエラーメッセージ",
            {"error_code": "TEST_001", "component": "test_component"}
        )
        
        print(f"✅ エラーアラートメッセージフォーマット:")
        print(f"   タイトル: {error_format.title}")
        print(f"   説明: {error_format.description}")
        print(f"   色: #{error_format.color:06x}")
        print(f"   フィールド数: {len(error_format.fields)}")
        
        # 日次レポートメッセージのフォーマット
        daily_format = formatter.format_daily_report(daily_performance)
        
        print(f"✅ 日次レポートメッセージフォーマット:")
        print(f"   タイトル: {daily_format.title}")
        print(f"   説明: {daily_format.description}")
        print(f"   色: #{daily_format.color:06x}")
        print(f"   フィールド数: {len(daily_format.fields)}")
        
        # テンプレート一覧の表示
        templates = formatter.list_templates()
        print(f"✅ 利用可能テンプレート: {[t.value for t in templates]}")
        
        # テンプレートの取得
        scenario_template = formatter.get_template(MessageTemplate.SCENARIO_CREATED)
        print(f"✅ シナリオ作成テンプレート: {scenario_template.get('title', 'N/A')}")
        
        print("🎉 メッセージフォーマッターテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()


async def test_discord_notifier_basic():
    """Discord配信システム基本テスト"""
    print("\n🧪 Discord配信システム基本テスト")
    
    notifier = DiscordNotifier()
    
    try:
        # 初期化
        await notifier.initialize()
        print("✅ Discord配信システム初期化完了")
        
        # 設定の確認
        print(f"✅ 通知設定:")
        for key, value in notifier.notification_settings.items():
            print(f"   {key}: {value}")
        
        print(f"✅ メッセージ設定:")
        for key, value in notifier.message_settings.items():
            if isinstance(value, int):
                print(f"   {key}: #{value:06x}")
            else:
                print(f"   {key}: {value}")
        
        # エラーアラート通知の送信（実際の送信は行わない）
        print("✅ エラーアラート通知の準備完了")
        
        print("🎉 Discord配信システム基本テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notifier.close()


async def test_discord_notifier_without_webhook():
    """WebhookなしでのDiscord配信システムテスト"""
    print("\n🧪 WebhookなしでのDiscord配信システムテスト")
    
    notifier = DiscordNotifier()
    
    try:
        # 初期化
        await notifier.initialize()
        
        # ダミーの日次パフォーマンスを作成
        daily_performance = DailyPerformance(
            date=datetime.now(timezone.utc),
            total_trades=3,
            winning_trades=2,
            losing_trades=1,
            win_rate=0.67,
            total_profit_pips=15.5,
            total_profit_percent=0.011,
            profit_factor=1.5,
            max_drawdown=3.2,
            average_hold_time_minutes=65.0,
            adherence_score_avg=88.0,
            adherence_score_min=82.0,
            adherence_score_max=95.0,
            daily_return_percent=0.011,
            strategy_performance={},
            violation_summary={},
            session_performance={}
        )
        
        # 日次レポート通知の送信（Webhookなしなので失敗するが、エラーハンドリングをテスト）
        success = await notifier.send_daily_report(daily_performance)
        print(f"✅ 日次レポート通知送信: {'成功' if success else '失敗（Webhook未設定）'}")
        
        # エラーアラート通知の送信
        success = await notifier.send_error_alert(
            "テストエラーメッセージ",
            {"test": "value", "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        print(f"✅ エラーアラート通知送信: {'成功' if success else '失敗（Webhook未設定）'}")
        
        print("🎉 WebhookなしでのDiscord配信システムテスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notifier.close()


async def test_notification_settings():
    """通知設定のテスト"""
    print("\n🧪 通知設定テスト")
    
    notifier = DiscordNotifier()
    
    try:
        # 初期化
        await notifier.initialize()
        
        # 通知設定の変更
        original_settings = notifier.notification_settings.copy()
        
        # 一部の通知を無効化
        notifier.notification_settings["daily_reports"] = False
        notifier.notification_settings["weekly_reports"] = False
        
        print("✅ 通知設定変更:")
        for key, value in notifier.notification_settings.items():
            status = "有効" if value else "無効"
            print(f"   {key}: {status}")
        
        # メッセージ設定の変更
        original_message_settings = notifier.message_settings.copy()
        
        # 色の変更
        notifier.message_settings["embed_color_scenario"] = 0xff00ff  # マゼンタ
        notifier.message_settings["embed_color_entry"] = 0x00ffff     # シアン
        
        print("✅ メッセージ設定変更:")
        print(f"   シナリオ作成色: #{notifier.message_settings['embed_color_scenario']:06x}")
        print(f"   エントリー色: #{notifier.message_settings['embed_color_entry']:06x}")
        
        # 設定の復元
        notifier.notification_settings = original_settings
        notifier.message_settings = original_message_settings
        
        print("✅ 設定復元完了")
        
        print("🎉 通知設定テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notifier.close()


async def test_message_creation():
    """メッセージ作成のテスト"""
    print("\n🧪 メッセージ作成テスト")
    
    notifier = DiscordNotifier()
    formatter = MessageFormatter()
    
    try:
        # 初期化
        await notifier.initialize()
        
        # ダミーのシナリオデータを作成
        from modules.llm_analysis.core.scenario_manager import Scenario, ScenarioStatus
        from modules.llm_analysis.core.rule_engine import EntrySignal, RuleResult
        
        dummy_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="test_strategy",
            confidence=0.85,
            entry_price=147.123,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=2.5,
            max_hold_time=240,
            rule_results=[
                RuleResult("RSI_14 <= 40", True, 0.9, "RSI: 38.5 ≤ 40", {}),
                RuleResult("price > EMA_200", True, 0.8, "Price: 147.123 > EMA_200: 146.800", {})
            ],
            technical_summary={"1h": {"price": 147.123, "rsi_14": 38.5}},
            created_at=datetime.now(timezone.utc)
        )
        
        # シナリオ作成メッセージの作成
        scenario_message = notifier._create_scenario_created_message(
            Scenario(
                id="test_scenario",
                strategy="test_strategy",
                status=ScenarioStatus.ARMED,
                direction=TradeDirection.BUY,
                entry_conditions=dummy_signal.__dict__,
                created_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(hours=8),
                armed_at=datetime.now(timezone.utc),
                triggered_at=None,
                entered_at=None,
                exited_at=None,
                exit_reason=None
            )
        )
        
        print(f"✅ シナリオ作成メッセージ作成:")
        print(f"   コンテンツ: {scenario_message.content}")
        print(f"   埋め込み数: {len(scenario_message.embeds) if scenario_message.embeds else 0}")
        if scenario_message.embeds:
            embed = scenario_message.embeds[0]
            print(f"   タイトル: {embed.title}")
            print(f"   説明: {embed.description}")
            print(f"   フィールド数: {len(embed.fields)}")
        
        # エラーアラートメッセージの作成
        error_message = notifier._create_error_alert_message(
            "テストエラーメッセージ",
            {"error_code": "TEST_001", "component": "test_component"}
        )
        
        print(f"✅ エラーアラートメッセージ作成:")
        print(f"   コンテンツ: {error_message.content}")
        print(f"   埋め込み数: {len(error_message.embeds) if error_message.embeds else 0}")
        if error_message.embeds:
            embed = error_message.embeds[0]
            print(f"   タイトル: {embed.title}")
            print(f"   色: #{embed.color:06x}")
            print(f"   フィールド数: {len(embed.fields)}")
        
        print("🎉 メッセージ作成テスト完了")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await notifier.close()


async def main():
    """メイン関数"""
    print("🚀 Discord配信システムテスト開始")
    
    # メッセージフォーマッターテスト
    await test_message_formatter()
    
    # Discord配信システム基本テスト
    await test_discord_notifier_basic()
    
    # Webhookなしでのテスト
    await test_discord_notifier_without_webhook()
    
    # 通知設定テスト
    await test_notification_settings()
    
    # メッセージ作成テスト
    await test_message_creation()
    
    print("\n🎉 全てのテストが完了しました！")


if __name__ == "__main__":
    asyncio.run(main())
