#!/usr/bin/env python3
"""
Database Connection Test
データベース接続のテスト
"""

import asyncio
import os
import sys

# プロジェクトパス追加
sys.path.append("/app")

from src.infrastructure.database.connection import DatabaseManager, get_async_session
from src.infrastructure.database.models.analysis_cache_model import AnalysisCacheModel
from src.infrastructure.database.models.api_call_history_model import (
    ApiCallHistoryModel,
)
from src.infrastructure.database.models.notification_history_model import (
    NotificationHistoryModel,
)


async def test_database_connection():
    """データベース接続のテスト"""
    print("🧪 データベース接続テスト開始")

    try:
        # 環境変数確認
        database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
        print(f"📊 DATABASE_URL: {database_url}")

        # セッション取得テスト
        session = await get_async_session()
        print(f"✅ セッション取得成功: {type(session)}")

        # テーブル存在確認
        try:
            # 各テーブルの存在確認
            tables = [AnalysisCacheModel, NotificationHistoryModel, ApiCallHistoryModel]

            from sqlalchemy import text

            for table in tables:
                result = await session.execute(
                    text(
                        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table.__tablename__}'"
                    )
                )
                exists = result.scalar() is not None
                print(f"📋 テーブル {table.__tablename__}: {'✅ 存在' if exists else '❌ 不存在'}")

            await session.close()
            print("✅ データベース接続テスト完了")
            return True

        except Exception as e:
            print(f"❌ テーブル確認エラー: {str(e)}")
            await session.close()
            return False

    except Exception as e:
        print(f"❌ データベース接続エラー: {str(e)}")
        return False


async def test_database_manager():
    """データベースマネージャーのテスト"""
    print("🧪 データベースマネージャーテスト開始")

    try:
        # データベースマネージャー初期化
        db_manager = DatabaseManager()

        # データベースURL設定
        database_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
        if database_url.startswith("sqlite://") and "aiosqlite" not in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://")

        print(f"📊 初期化URL: {database_url}")

        # 初期化
        await db_manager.initialize(database_url, echo=False)
        print("✅ データベースマネージャー初期化成功")

        # セッションファクトリ取得
        session_factory = await db_manager.get_session_factory()
        print(f"✅ セッションファクトリ取得成功: {type(session_factory)}")

        # セッション作成テスト
        async with db_manager.get_session() as session:
            print(f"✅ セッション作成成功: {type(session)}")

            # 簡単なクエリテスト
            from sqlalchemy import text

            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            print(f"✅ クエリテスト成功: {test_value}")

        # ヘルスチェック
        health = await db_manager.health_check()
        print(f"✅ ヘルスチェック: {'成功' if health else '失敗'}")

        print("✅ データベースマネージャーテスト完了")
        return True

    except Exception as e:
        print(f"❌ データベースマネージャーエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_repository_operations():
    """リポジトリ操作のテスト"""
    print("🧪 リポジトリ操作テスト開始")

    try:
        from src.infrastructure.database.repositories.analysis_cache_repository_impl import (
            AnalysisCacheRepositoryImpl,
        )
        from src.infrastructure.database.repositories.api_call_history_repository_impl import (
            ApiCallHistoryRepositoryImpl,
        )
        from src.infrastructure.database.repositories.notification_history_repository_impl import (
            NotificationHistoryRepositoryImpl,
        )

        # セッション取得
        session = await get_async_session()

        # リポジトリ初期化
        analysis_repo = AnalysisCacheRepositoryImpl(session)
        notification_repo = NotificationHistoryRepositoryImpl(session)
        api_call_repo = ApiCallHistoryRepositoryImpl(session)

        print("✅ リポジトリ初期化成功")

        # 統計情報取得テスト
        try:
            analysis_stats = await analysis_repo.get_statistics()
            print(f"📊 分析キャッシュ統計: {analysis_stats}")
        except Exception as e:
            print(f"⚠️ 分析キャッシュ統計エラー: {str(e)}")

        try:
            notification_stats = await notification_repo.get_statistics()
            print(f"📊 通知履歴統計: {notification_stats}")
        except Exception as e:
            print(f"⚠️ 通知履歴統計エラー: {str(e)}")

        try:
            api_call_stats = await api_call_repo.get_call_statistics()
            print(f"📊 API呼び出し統計: {api_call_stats}")
        except Exception as e:
            print(f"⚠️ API呼び出し統計エラー: {str(e)}")

        await session.close()
        print("✅ リポジトリ操作テスト完了")
        return True

    except Exception as e:
        print(f"❌ リポジトリ操作エラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """メインテスト実行"""
    print("🚀 Database Connection テスト開始")
    print("=" * 50)

    results = []

    # 各テスト実行
    results.append(await test_database_connection())
    print()

    results.append(await test_database_manager())
    print()

    results.append(await test_repository_operations())
    print()

    # 結果サマリー
    success_count = sum(results)
    total_count = len(results)

    print("=" * 50)
    print(f"📊 テスト結果: {success_count}/{total_count} 成功")

    if success_count == total_count:
        print("🎉 すべてのデータベーステストが成功しました！")
    else:
        print("⚠️ 一部のテストが失敗しました。詳細を確認してください。")


if __name__ == "__main__":
    asyncio.run(main())
