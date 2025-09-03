#!/usr/bin/env python3
"""
NotificationManager Test
通知管理システムのテスト
"""

import asyncio
import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# プロジェクトパス追加
sys.path.append("/app")

from src.infrastructure.messaging.discord_client import DiscordClient
from src.infrastructure.messaging.notification_manager import (
    NotificationManager,
    NotificationPattern,
)


class MockDiscordClient:
    """モックDiscordクライアント"""

    def __init__(self):
        self.total_messages_sent = 0
        self.total_embeds_sent = 0
        self.message_errors = 0

    async def send_rich_embed(self, title, description, fields, color):
        """モック送信"""
        self.total_messages_sent += 1
        self.total_embeds_sent += 1
        return f"mock_message_id_{self.total_messages_sent}"


class MockNotificationHistoryRepository:
    """モック通知履歴リポジトリ"""

    def __init__(self):
        self.notifications = []

    async def find_recent_by_pattern(self, pattern_type, currency_pair, hours):
        """モック検索"""
        return []

    async def save(self, notification_history):
        """モック保存"""
        self.notifications.append(notification_history)

    async def get_statistics(self, hours):
        """モック統計"""
        return {
            "total_notifications": len(self.notifications),
            "recent_notifications": len(self.notifications),
            "success_rate": 100.0,
        }


async def test_notification_pattern():
    """通知パターンのテスト"""
    print("🧪 通知パターンテスト開始")

    # テストパターン作成
    pattern = NotificationPattern(
        pattern_type="trend_reversal",
        currency_pair="USD/JPY",
        pattern_data={"price": 147.693, "trend": "up"},
        priority=80,
        confidence=0.85,
        timeframe="D1",
    )

    # パターンキー確認
    assert pattern.get_pattern_key() == "trend_reversal_USD/JPY_D1"

    # 優先度スコア確認
    priority_score = pattern.get_priority_score()
    expected_score = (80 * 0.7) + (0.85 * 100 * 0.3)
    assert abs(priority_score - expected_score) < 0.1

    print(f"✅ パターンキー: {pattern.get_pattern_key()}")
    print(f"✅ 優先度スコア: {priority_score:.1f}")
    print("✅ 通知パターンテスト完了")


async def test_notification_manager():
    """通知マネージャーのテスト"""
    print("🧪 通知マネージャーテスト開始")

    # モックコンポーネント作成
    mock_discord = MockDiscordClient()
    mock_repo = MockNotificationHistoryRepository()

    # 通知マネージャー初期化
    notification_manager = NotificationManager(
        discord_client=mock_discord,
        notification_history_repository=mock_repo,
        duplicate_check_window_minutes=5,  # 短縮
        max_notifications_per_hour=5,  # 短縮
        enable_priority_filtering=True,
        enable_duplicate_prevention=True,
    )

    # テストパターン作成
    patterns = [
        NotificationPattern(
            pattern_type="trend_reversal",
            currency_pair="USD/JPY",
            pattern_data={"price": 147.693, "trend": "up"},
            priority=80,
            confidence=0.85,
            timeframe="D1",
        ),
        NotificationPattern(
            pattern_type="pullback",
            currency_pair="EUR/USD",
            pattern_data={"price": 1.164, "trend": "down"},
            priority=60,
            confidence=0.70,
            timeframe="H4",
        ),
        NotificationPattern(
            pattern_type="low_priority",
            currency_pair="GBP/USD",
            pattern_data={"price": 1.345, "trend": "sideways"},
            priority=20,  # 低優先度
            confidence=0.30,
            timeframe="H1",
        ),
    ]

    # 通知処理実行
    results = await notification_manager.process_notification_patterns(patterns)

    print(f"📊 処理結果: {results}")
    print(f"📊 送信数: {results['sent']}")
    print(f"📊 重複ブロック数: {results['duplicate_blocked']}")
    print(f"📊 低優先度フィルタ数: {results['low_priority_filtered']}")
    print(f"📊 エラー数: {results['errors']}")

    # 統計情報取得
    stats = await notification_manager.get_notification_statistics()
    print(f"📊 統計情報: {stats}")

    # 検証
    assert results["total_patterns"] == 3
    assert results["sent"] >= 1  # 少なくとも1つは送信される
    assert results["low_priority_filtered"] >= 1  # 低優先度はフィルタされる

    print("✅ 通知マネージャーテスト完了")


async def test_duplicate_prevention():
    """重複防止機能のテスト"""
    print("🧪 重複防止機能テスト開始")

    # モックコンポーネント作成
    mock_discord = MockDiscordClient()
    mock_repo = MockNotificationHistoryRepository()

    # 通知マネージャー初期化
    notification_manager = NotificationManager(
        discord_client=mock_discord,
        notification_history_repository=mock_repo,
        duplicate_check_window_minutes=1,  # 1分
        max_notifications_per_hour=10,
        enable_priority_filtering=False,  # 無効化
        enable_duplicate_prevention=True,
    )

    # 同じパターンを2回送信
    pattern = NotificationPattern(
        pattern_type="test_pattern",
        currency_pair="USD/JPY",
        pattern_data={"test": "data"},
        priority=50,
        confidence=0.5,
        timeframe="D1",
    )

    # 1回目送信
    result1 = await notification_manager.send_pattern_notification(pattern)
    print(f"📤 1回目送信結果: {result1}")

    # 2回目送信（重複）
    result2 = await notification_manager.send_pattern_notification(pattern)
    print(f"📤 2回目送信結果: {result2}")

    # 検証
    assert result1 == True  # 1回目は成功
    assert result2 == False  # 2回目は重複でブロック

    print("✅ 重複防止機能テスト完了")


async def test_priority_filtering():
    """優先度フィルタリングのテスト"""
    print("🧪 優先度フィルタリングテスト開始")

    # モックコンポーネント作成
    mock_discord = MockDiscordClient()
    mock_repo = MockNotificationHistoryRepository()

    # 通知マネージャー初期化
    notification_manager = NotificationManager(
        discord_client=mock_discord,
        notification_history_repository=mock_repo,
        duplicate_check_window_minutes=5,
        max_notifications_per_hour=10,
        enable_priority_filtering=True,
        enable_duplicate_prevention=False,  # 無効化
    )

    # 高優先度パターン
    high_priority_pattern = NotificationPattern(
        pattern_type="high_priority",
        currency_pair="USD/JPY",
        pattern_data={"test": "high"},
        priority=90,
        confidence=0.9,
        timeframe="D1",
    )

    # 低優先度パターン
    low_priority_pattern = NotificationPattern(
        pattern_type="low_priority",
        currency_pair="EUR/USD",
        pattern_data={"test": "low"},
        priority=10,  # 低優先度
        confidence=0.1,
        timeframe="H1",
    )

    # 高優先度送信
    result1 = await notification_manager.send_pattern_notification(
        high_priority_pattern
    )
    print(f"📤 高優先度送信結果: {result1}")

    # 低優先度送信
    result2 = await notification_manager.send_pattern_notification(low_priority_pattern)
    print(f"📤 低優先度送信結果: {result2}")

    # 検証
    assert result1 == True  # 高優先度は成功
    assert result2 == False  # 低優先度はフィルタ

    print("✅ 優先度フィルタリングテスト完了")


async def main():
    """メインテスト実行"""
    print("🚀 NotificationManager テスト開始")
    print("=" * 50)

    try:
        # 各テスト実行
        await test_notification_pattern()
        print()

        await test_notification_manager()
        print()

        await test_duplicate_prevention()
        print()

        await test_priority_filtering()
        print()

        print("🎉 すべてのテストが成功しました！")

    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
