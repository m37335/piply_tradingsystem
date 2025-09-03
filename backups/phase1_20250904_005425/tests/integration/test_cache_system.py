#!/usr/bin/env python3
"""
Cache System Test
キャッシュシステムのテスト
"""

import asyncio
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

# プロジェクトパス追加
sys.path.append("/app")

from src.infrastructure.cache.analysis_cache import AnalysisCacheManager
from src.infrastructure.cache.cache_manager import CacheManager
from src.infrastructure.cache.file_cache import FileCache


class MockAnalysisCacheRepository:
    """モック分析キャッシュリポジトリ"""

    def __init__(self):
        self.cache_data = {}

    async def find_by_cache_key(self, cache_key):
        """モック検索"""
        return self.cache_data.get(cache_key)

    async def save(self, analysis_cache):
        """モック保存"""
        self.cache_data[analysis_cache.cache_key] = analysis_cache

    async def delete_expired(self):
        """モック削除"""
        expired_keys = []
        for key, cache in self.cache_data.items():
            if cache.expires_at < datetime.utcnow():
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache_data[key]

        return len(expired_keys)


async def test_file_cache():
    """ファイルキャッシュのテスト"""
    print("🧪 ファイルキャッシュテスト開始")

    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = FileCache(cache_dir=temp_dir, max_size_mb=10, ttl_seconds=60)

        # テストデータ
        test_data = {
            "currency": "USD/JPY",
            "price": 147.693,
            "timestamp": datetime.utcnow().isoformat(),
        }
        cache_key = "test_usdjpy_data"

        # データ保存
        cache.set(cache_key, test_data)
        print(f"✅ データ保存: {cache_key}")

        # データ取得
        retrieved_data = cache.get(cache_key)
        assert retrieved_data is not None
        assert retrieved_data["currency"] == "USD/JPY"
        assert retrieved_data["price"] == 147.693
        print(f"✅ データ取得: {retrieved_data}")

        # 存在確認
        exists = cache.get(cache_key) is not None
        assert exists == True
        print(f"✅ 存在確認: {exists}")

        # データ削除
        cache.delete(cache_key)
        deleted_data = cache.get(cache_key)
        assert deleted_data is None
        print(f"✅ データ削除確認")

    print("✅ ファイルキャッシュテスト完了")


async def test_cache_manager():
    """キャッシュマネージャーのテスト"""
    print("🧪 キャッシュマネージャーテスト開始")

    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        # モックリポジトリ作成
        mock_repo = MockAnalysisCacheRepository()

        cache_manager = CacheManager(
            analysis_cache_repository=mock_repo,
            file_cache_dir=temp_dir,
            memory_cache_size=100,
            file_cache_size_mb=10,
        )

        # テストデータ
        test_data = {
            "analysis_type": "technical_indicators",
            "currency_pair": "USD/JPY",
            "data": {"rsi": 65.5, "macd": 0.123},
        }
        cache_key = "usdjpy_technical_analysis"

        # データ保存（3層キャッシュ）
        await cache_manager.set(
            cache_type="analysis",
            components={"key": cache_key},
            data=test_data,
            ttl_seconds=300,
        )
        print(f"✅ 3層キャッシュ保存: {cache_key}")

        # データ取得
        retrieved_data = await cache_manager.get(
            cache_type="analysis", components={"key": cache_key}
        )
        assert retrieved_data is not None
        assert retrieved_data["analysis_type"] == "technical_indicators"
        assert retrieved_data["currency_pair"] == "USD/JPY"
        print(f"✅ 3層キャッシュ取得: {retrieved_data}")

        # 統計情報
        stats = await cache_manager.get_statistics()
        print(f"📊 キャッシュ統計: {stats}")

        # キャッシュクリア
        await cache_manager.clear_all()
        cleared_data = await cache_manager.get(
            cache_type="analysis", components={"key": cache_key}
        )
        assert cleared_data is None
        print(f"✅ キャッシュクリア確認")

    print("✅ キャッシュマネージャーテスト完了")


async def test_analysis_cache():
    """分析キャッシュのテスト"""
    print("🧪 分析キャッシュテスト開始")

    # モックリポジトリ作成
    mock_repo = MockAnalysisCacheRepository()

    # 分析キャッシュマネージャー初期化
    analysis_cache = AnalysisCacheManager(mock_repo)

    # テスト分析データ
    analysis_data = {
        "rsi": {"current_value": 65.5, "signal": "neutral"},
        "macd": {"current_value": 0.123, "signal": "buy"},
        "bollinger_bands": {"upper": 148.5, "lower": 146.8, "middle": 147.6},
    }

    # 分析結果をキャッシュ
    await analysis_cache.set_analysis(
        analysis_type="technical_indicators",
        currency_pair="USD/JPY",
        analysis_data=analysis_data,
        timeframe="D1",
    )
    print(f"✅ 分析結果キャッシュ保存")

    # キャッシュから分析結果取得
    cached_data = await analysis_cache.get_analysis(
        analysis_type="technical_indicators", currency_pair="USD/JPY", timeframe="D1"
    )

    assert cached_data is not None
    assert cached_data["rsi"]["current_value"] == 65.5
    assert cached_data["macd"]["signal"] == "buy"
    print(f"✅ 分析結果キャッシュ取得: {cached_data}")

    # キャッシュ情報取得
    cache_info = await analysis_cache.get_cache_info(
        analysis_type="technical_indicators", currency_pair="USD/JPY", timeframe="D1"
    )
    print(f"📊 キャッシュ情報: {cache_info}")

    # キャッシュ無効化
    await analysis_cache.invalidate_analysis(currency_pair="USD/JPY")
    invalidated_data = await analysis_cache.get_analysis(
        analysis_type="technical_indicators", currency_pair="USD/JPY", timeframe="D1"
    )
    assert invalidated_data is None
    print(f"✅ キャッシュ無効化確認")

    print("✅ 分析キャッシュテスト完了")


async def test_cache_integration():
    """キャッシュ統合テスト"""
    print("🧪 キャッシュ統合テスト開始")

    # 一時ディレクトリ作成
    with tempfile.TemporaryDirectory() as temp_dir:
        # モックリポジトリ作成
        mock_repo = MockAnalysisCacheRepository()

        # キャッシュマネージャー初期化
        cache_manager = CacheManager(
            analysis_cache_repository=mock_repo,
            file_cache_dir=temp_dir,
            memory_cache_size=50,
            file_cache_size_mb=5,
        )

        # 複数の分析データをキャッシュ
        analysis_types = ["technical_indicators", "correlation_analysis", "ai_analysis"]
        currency_pairs = ["USD/JPY", "EUR/USD", "GBP/USD"]

        for analysis_type in analysis_types:
            for currency_pair in currency_pairs:
                cache_key = f"{analysis_type}_{currency_pair}"
                test_data = {
                    "analysis_type": analysis_type,
                    "currency_pair": currency_pair,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": {"value": f"test_data_{analysis_type}_{currency_pair}"},
                }

                await cache_manager.set(cache_key, test_data, ttl_seconds=600)

        print(f"✅ {len(analysis_types) * len(currency_pairs)}件のデータをキャッシュ")

        # 統計情報確認
        stats = cache_manager.get_statistics()
        print(f"📊 統合キャッシュ統計: {stats}")

        # ヒット率テスト
        hit_count = 0
        total_requests = 0

        for analysis_type in analysis_types:
            for currency_pair in currency_pairs:
                cache_key = f"{analysis_type}_{currency_pair}"
                data = await cache_manager.get(cache_key)
                total_requests += 1
                if data is not None:
                    hit_count += 1

        hit_rate = (hit_count / total_requests) * 100 if total_requests > 0 else 0
        print(f"📊 キャッシュヒット率: {hit_rate:.1f}% ({hit_count}/{total_requests})")

        assert hit_rate > 90  # 90%以上のヒット率を期待

    print("✅ キャッシュ統合テスト完了")


async def main():
    """メインテスト実行"""
    print("🚀 Cache System テスト開始")
    print("=" * 50)

    try:
        # 各テスト実行
        await test_file_cache()
        print()

        await test_cache_manager()
        print()

        await test_analysis_cache()
        print()

        await test_cache_integration()
        print()

        print("🎉 すべてのキャッシュテストが成功しました！")

    except Exception as e:
        print(f"❌ テストエラー: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
