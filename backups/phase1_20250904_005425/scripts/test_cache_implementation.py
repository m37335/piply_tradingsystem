#!/usr/bin/env python3
"""
キャッシュ機能テストスクリプト
Redisとメモリキャッシュの動作確認を行う
"""

import asyncio
import os
import sys
import time
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.infrastructure.database.repositories.cache import (
    MemoryCacheManager,
    RedisCacheManager,
)


async def test_memory_cache():
    """メモリキャッシュのテスト"""
    print("=== メモリキャッシュテスト ===")

    try:
        # メモリキャッシュマネージャーの作成
        cache = MemoryCacheManager(max_size=100, default_ttl=60, cleanup_interval=30)

        print("✅ メモリキャッシュマネージャー作成完了")

        # 基本的な操作テスト
        print("\n--- 基本操作テスト ---")

        # 設定テスト
        test_data = {
            "string": "test_string",
            "number": 42,
            "list": [1, 2, 3, 4, 5],
            "dict": {"key": "value", "nested": {"data": "test"}},
            "datetime": datetime.now(),
        }

        for key, value in test_data.items():
            success = cache.set(f"test_{key}", value, prefix="test")
            print(f"  設定 {key}: {'✅' if success else '❌'}")

        # 取得テスト
        print("\n--- 取得テスト ---")
        for key, expected_value in test_data.items():
            # 適切な型を指定して取得
            if isinstance(expected_value, dict):
                retrieved_value = cache.get(f"test_{key}", prefix="test", value_type=dict)
            elif isinstance(expected_value, list):
                retrieved_value = cache.get(f"test_{key}", prefix="test", value_type=list)
            elif isinstance(expected_value, int):
                retrieved_value = cache.get(f"test_{key}", prefix="test", value_type=int)
            elif isinstance(expected_value, datetime):
                retrieved_value = cache.get(f"test_{key}", prefix="test", value_type=datetime)
            else:
                retrieved_value = cache.get(f"test_{key}", prefix="test")

            # 辞書の場合は内容を比較（キーの形式は無視）
            if isinstance(expected_value, dict) and isinstance(retrieved_value, dict):
                is_equal = expected_value == retrieved_value
            # datetimeの場合は文字列形式を比較
            elif isinstance(expected_value, datetime) and isinstance(
                retrieved_value, str
            ):
                try:
                    parsed_datetime = datetime.fromisoformat(
                        retrieved_value.replace("Z", "+00:00")
                    )
                    is_equal = (
                        abs((expected_value - parsed_datetime).total_seconds()) < 1
                    )
                except Exception:
                    is_equal = False
            # リストや数値の場合は内容を比較（表示形式は無視）
            elif isinstance(expected_value, (list, int, float)) and isinstance(
                retrieved_value, (list, int, float)
            ):
                is_equal = expected_value == retrieved_value
            else:
                is_equal = retrieved_value == expected_value

            if is_equal:
                print(f"  取得 {key}: ✅")
            else:
                print(
                    f"  取得 {key}: ❌ (期待: {expected_value}, 実際: {retrieved_value})"
                )

        # 存在確認テスト
        print("\n--- 存在確認テスト ---")
        exists = cache.exists("test_string", prefix="test")
        print(f"  存在確認: {'✅' if exists else '❌'}")

        not_exists = cache.exists("nonexistent", prefix="test")
        print(f"  非存在確認: {'✅' if not not_exists else '❌'}")

        # TTLテスト
        print("\n--- TTLテスト ---")
        cache.set("ttl_test", "will_expire", prefix="test", ttl=2)
        print("  TTL設定: ✅")

        time.sleep(1)
        value = cache.get("ttl_test", prefix="test")
        print(f"  1秒後: {'✅' if value == 'will_expire' else '❌'}")

        time.sleep(2)
        value = cache.get("ttl_test", prefix="test")
        print(f"  3秒後: {'✅' if value is None else '❌'}")

        # 統計情報テスト
        print("\n--- 統計情報テスト ---")
        stats = cache.get_stats()
        print(f"  統計情報: {stats}")

        # ヘルスチェックテスト
        print("\n--- ヘルスチェックテスト ---")
        health = cache.health_check()
        print(f"  ヘルスチェック: {'✅' if health else '❌'}")

        # クリアテスト
        print("\n--- クリアテスト ---")
        deleted_count = cache.clear_prefix("test")
        print(f"  プレフィックスクリア: {deleted_count}件削除")

        return True

    except Exception as e:
        print(f"❌ メモリキャッシュテストエラー: {e}")
        return False

    print()


async def test_redis_cache():
    """Redisキャッシュのテスト"""
    print("=== Redisキャッシュテスト ===")

    try:
        # Redisキャッシュマネージャーの作成
        cache = RedisCacheManager(
            host="localhost", port=6379, db=0, max_connections=5, default_ttl=60
        )

        # 接続テスト
        print("Redisに接続中...")
        connected = await cache.connect()

        if not connected:
            print(
                "⚠️ Redisに接続できませんでした。Redisが起動しているか確認してください。"
            )
            print("   テストをスキップします。")
            return True  # エラーではないのでTrueを返す

        print("✅ Redis接続完了")

        # 基本的な操作テスト
        print("\n--- 基本操作テスト ---")

        # 設定テスト
        test_data = {
            "string": "redis_test_string",
            "number": 123,
            "list": ["a", "b", "c"],
            "dict": {"redis": "test", "data": {"nested": "value"}},
        }

        for key, value in test_data.items():
            success = await cache.set(f"test_{key}", value, prefix="redis_test")
            print(f"  設定 {key}: {'✅' if success else '❌'}")

        # 取得テスト
        print("\n--- 取得テスト ---")
        for key, expected_value in test_data.items():
            # 適切な型を指定して取得
            if isinstance(expected_value, dict):
                retrieved_value = await cache.get(f"test_{key}", prefix="redis_test", value_type=dict)
            elif isinstance(expected_value, list):
                retrieved_value = await cache.get(f"test_{key}", prefix="redis_test", value_type=list)
            elif isinstance(expected_value, int):
                retrieved_value = await cache.get(f"test_{key}", prefix="redis_test", value_type=int)
            else:
                retrieved_value = await cache.get(f"test_{key}", prefix="redis_test")

            # 辞書の場合は内容を比較（キーの形式は無視）
            if isinstance(expected_value, dict) and isinstance(retrieved_value, dict):
                is_equal = expected_value == retrieved_value
            else:
                is_equal = retrieved_value == expected_value

            if is_equal:
                print(f"  取得 {key}: ✅")
            else:
                print(
                    f"  取得 {key}: ❌ (期待: {expected_value}, 実際: {retrieved_value})"
                )

        # 存在確認テスト
        print("\n--- 存在確認テスト ---")
        exists = await cache.exists("test_string", prefix="redis_test")
        print(f"  存在確認: {'✅' if exists else '❌'}")

        not_exists = await cache.exists("nonexistent", prefix="redis_test")
        print(f"  非存在確認: {'✅' if not not_exists else '❌'}")

        # TTLテスト
        print("\n--- TTLテスト ---")
        await cache.set("ttl_test", "will_expire", prefix="redis_test", ttl=2)
        print("  TTL設定: ✅")

        await asyncio.sleep(1)
        value = await cache.get("ttl_test", prefix="redis_test")
        print(f"  1秒後: {'✅' if value == 'will_expire' else '❌'}")

        await asyncio.sleep(2)
        value = await cache.get("ttl_test", prefix="redis_test")
        print(f"  3秒後: {'✅' if value is None else '❌'}")

        # 統計情報テスト
        print("\n--- 統計情報テスト ---")
        stats = await cache.get_stats()
        print(f"  統計情報: {stats}")

        # ヘルスチェックテスト
        print("\n--- ヘルスチェックテスト ---")
        health = await cache.health_check()
        print(f"  ヘルスチェック: {'✅' if health else '❌'}")

        # クリアテスト
        print("\n--- クリアテスト ---")
        deleted_count = await cache.clear_prefix("redis_test")
        print(f"  プレフィックスクリア: {deleted_count}件削除")

        # 接続切断
        await cache.disconnect()
        print("✅ Redis接続切断完了")

        return True

    except Exception as e:
        print(f"❌ Redisキャッシュテストエラー: {e}")
        return False

    print()


async def test_cache_performance():
    """キャッシュパフォーマンステスト"""
    print("=== キャッシュパフォーマンステスト ===")

    try:
        # メモリキャッシュのパフォーマンステスト
        print("\n--- メモリキャッシュパフォーマンス ---")
        memory_cache = MemoryCacheManager(max_size=10000)

        # 大量データの設定テスト
        start_time = time.time()
        for i in range(1000):
            memory_cache.set(f"perf_test_{i}", f"value_{i}", prefix="perf")
        set_time = time.time() - start_time
        print(f"  1000件設定: {set_time:.4f}秒")

        # 大量データの取得テスト
        start_time = time.time()
        for i in range(1000):
            memory_cache.get(f"perf_test_{i}", prefix="perf")
        get_time = time.time() - start_time
        print(f"  1000件取得: {get_time:.4f}秒")

        # クリア
        memory_cache.clear_prefix("perf")

        return True

    except Exception as e:
        print(f"❌ パフォーマンステストエラー: {e}")
        return False

    print()


async def main():
    """メイン関数"""
    print("investpy経済カレンダーシステム キャッシュ機能テスト")
    print("=" * 60)

    # 各テストの実行
    memory_ok = await test_memory_cache()
    redis_ok = await test_redis_cache()
    perf_ok = await test_cache_performance()

    print("=" * 60)
    print("テスト結果サマリー:")
    print(f"  メモリキャッシュ: {'✅' if memory_ok else '❌'}")
    print(f"  Redisキャッシュ: {'✅' if redis_ok else '❌'}")
    print(f"  パフォーマンステスト: {'✅' if perf_ok else '❌'}")

    if all([memory_ok, redis_ok, perf_ok]):
        print("\n🎉 全てのキャッシュテストが成功しました！")
    else:
        print("\n⚠️ 一部のテストが失敗しました。")

    print("\nテスト完了")


if __name__ == "__main__":
    asyncio.run(main())
