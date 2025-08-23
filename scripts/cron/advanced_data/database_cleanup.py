"""
Database Cleanup Module
データベースクリーンアップ機能

責任:
- 既存データベースファイルの完全削除
- テーブル構造の再作成
- クリーンな環境の提供
"""

import asyncio
import logging
import os
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.database.models.base import Base

logger = logging.getLogger(__name__)


class DatabaseCleanup:
    """データベースクリーンアップクラス"""

    def __init__(self):
        default_url = "sqlite+aiosqlite:///data/exchange_analytics.db"
        self.database_url: str = os.getenv("DATABASE_URL", default_url)
        self.db_path: str = "/app/data/exchange_analytics.db"
        self.session: Optional[AsyncSession] = None
        self.engine = None

    async def cleanup_database(self) -> bool:
        """
        データベースを完全にクリーンアップ

        Returns:
            bool: 成功/失敗
        """
        try:
            print("🗄️ データベースクリーンアップを開始します")

            # 1. 既存データベースファイルの削除
            if await self._remove_database_file():
                print("✅ 既存データベースファイルを削除しました")
            else:
                print("⚠️ データベースファイルが存在しませんでした")

            # 2. データベース接続の初期化
            if not await self.initialize_session():
                print("❌ データベース接続の初期化に失敗しました")
                return False

            # 3. テーブル構造の作成
            if not await self.create_tables():
                print("❌ テーブル構造の作成に失敗しました")
                return False

            # 4. クリーンアップの確認
            if not await self.verify_cleanup():
                print("❌ クリーンアップの確認に失敗しました")
                return False

            print("✅ データベースクリーンアップが完了しました")
            return True

        except Exception as e:
            print(f"❌ データベースクリーンアップ中にエラーが発生しました: {e}")
            return False

    async def create_tables(self) -> bool:
        """
        テーブル構造を作成

        Returns:
            bool: 成功/失敗
        """
        try:
            print("📋 テーブル構造を作成しています")

            # 1. Base.metadata.create_all()の実行
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            print("✅ テーブル構造の作成が完了しました")
            return True

        except Exception as e:
            print(f"❌ テーブル構造の作成中にエラーが発生しました: {e}")
            return False

    async def verify_cleanup(self) -> bool:
        """
        クリーンアップの確認

        Returns:
            bool: 成功/失敗
        """
        try:
            print("🔍 クリーンアップの確認を実行しています")

            # 1. データベースファイルの存在確認
            if not os.path.exists(self.db_path):
                print("❌ データベースファイルが存在しません")
                return False

            # 2. テーブル構造の検証
            async with self.engine.begin() as conn:
                # テーブル一覧を取得
                from sqlalchemy import text

                result = await conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table'")
                )
                tables = [row[0] for row in result.fetchall()]

                if not tables:
                    print("❌ テーブルが作成されていません")
                    return False

                print(f"📊 作成されたテーブル: {tables}")

            # 3. 接続テスト
            if not await self._test_connection():
                print("❌ データベース接続テストに失敗しました")
                return False

            print("✅ クリーンアップの確認が完了しました")
            return True

        except Exception as e:
            print(f"❌ クリーンアップ確認中にエラーが発生しました: {e}")
            return False

    async def initialize_session(self) -> bool:
        """
        セッションの初期化

        Returns:
            bool: 成功/失敗
        """
        try:
            print("🔌 データベースセッションを初期化しています")

            # エンジンの作成
            self.engine = create_async_engine(
                self.database_url, echo=False, pool_pre_ping=True
            )

            # セッションファクトリの作成
            async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            # セッションの作成
            self.session = async_session()

            print("✅ データベースセッションの初期化が完了しました")
            return True

        except Exception as e:
            print(f"❌ セッション初期化中にエラーが発生しました: {e}")
            return False

    async def cleanup(self) -> None:
        """リソースのクリーンアップ"""
        try:
            if self.session:
                await self.session.close()
                print("🔒 セッションをクローズしました")

            if self.engine:
                await self.engine.dispose()
                print("🗑️ エンジンを破棄しました")

        except Exception as e:
            print(f"❌ リソースクリーンアップ中にエラーが発生しました: {e}")

    async def _remove_database_file(self) -> bool:
        """
        既存データベースファイルを削除

        Returns:
            bool: ファイルが存在していたかどうか
        """
        try:
            if os.path.exists(self.db_path):
                os.remove(self.db_path)
                print(f"🗑️ データベースファイルを削除しました: {self.db_path}")
                return True
            else:
                print(f"⚠️ データベースファイルが存在しません: {self.db_path}")
                return False

        except Exception as e:
            print(f"❌ データベースファイル削除中にエラーが発生しました: {e}")
            return False

    async def _test_connection(self) -> bool:
        """
        データベース接続テスト

        Returns:
            bool: 成功/失敗
        """
        try:
            async with self.engine.begin() as conn:
                from sqlalchemy import text

                await conn.execute(text("SELECT 1"))
            return True

        except Exception as e:
            print(f"❌ 接続テスト中にエラーが発生しました: {e}")
            return False


async def main():
    """メイン実行関数"""
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    cleanup = DatabaseCleanup()

    try:
        # データベースクリーンアップを実行
        success = await cleanup.cleanup_database()

        if success:
            print("✅ データベースクリーンアップが完了しました")
            return 0
        else:
            print("❌ データベースクリーンアップに失敗しました")
            return 1

    except Exception as e:
        print(f"❌ 予期しないエラーが発生しました: {e}")
        return 1

    finally:
        await cleanup.cleanup()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
