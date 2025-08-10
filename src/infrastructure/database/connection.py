"""
Database Connection Management
データベース接続管理

設計書参照:
- インフラ・プラグイン設計_20250809.md

SQLAlchemyを使用したデータベース接続とセッション管理
"""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from ...utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()


class DatabaseManager:
    """
    データベース接続管理クラス

    責任:
    - 非同期データベースエンジンの管理
    - セッションファクトリの提供
    - 接続プールの管理
    - ヘルスチェック機能
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._is_initialized = False

    async def initialize(
        self,
        database_url: str,
        echo: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        **kwargs,
    ) -> None:
        """
        データベース接続を初期化

        Args:
            database_url: データベースURL
            echo: SQLログ出力フラグ
            pool_size: 接続プールサイズ
            max_overflow: 最大オーバーフロー接続数
            pool_timeout: 接続タイムアウト（秒）
            pool_recycle: 接続リサイクル時間（秒）
            **kwargs: その他のエンジン設定
        """
        if self._is_initialized:
            logger.warning("Database manager is already initialized")
            return

        try:
            # SQLiteの場合は特別な設定
            if database_url.startswith("sqlite"):
                if "aiosqlite" in database_url:
                    # aiosqliteの場合
                    engine_kwargs = {
                        "poolclass": StaticPool,
                        "connect_args": {
                            "check_same_thread": False,
                        },
                        **kwargs,
                    }
                else:
                    # 通常のsqliteの場合
                    engine_kwargs = {
                        "poolclass": StaticPool,
                        "connect_args": {
                            "check_same_thread": False,
                        },
                        **kwargs,
                    }
            else:
                # PostgreSQL等の場合
                engine_kwargs = {
                    "pool_size": pool_size,
                    "max_overflow": max_overflow,
                    "pool_timeout": pool_timeout,
                    "pool_recycle": pool_recycle,
                    **kwargs,
                }

            # 非同期エンジンを作成
            self._engine = create_async_engine(database_url, echo=echo, **engine_kwargs)

            # セッションファクトリを作成
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False,
            )

            self._is_initialized = True

            logger.info(
                f"Database initialized with URL: {self._mask_password(database_url)}"
            )

            # 接続テスト
            await self.health_check()

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    async def close(self) -> None:
        """
        データベース接続を閉じる
        """
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            self._is_initialized = False
            logger.info("Database connection closed")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        データベースセッションを取得（コンテキストマネージャー）

        Yields:
            AsyncSession: データベースセッション

        Example:
            async with db_manager.get_session() as session:
                # セッションを使用した処理
                result = await session.execute(select(Model))
        """
        if not self._is_initialized:
            raise RuntimeError("Database manager is not initialized")

        session = self._session_factory()
        try:
            logger.debug("Database session created")
            yield session
            await session.commit()
            logger.debug("Database session committed")
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session rolled back due to error: {str(e)}")
            raise
        finally:
            await session.close()
            logger.debug("Database session closed")

    async def get_session_factory(self) -> async_sessionmaker:
        """
        セッションファクトリを取得

        Returns:
            async_sessionmaker: セッションファクトリ
        """
        if not self._is_initialized:
            raise RuntimeError("Database manager is not initialized")

        return self._session_factory

    async def health_check(self) -> bool:
        """
        データベースヘルスチェック

        Returns:
            bool: 接続正常時True
        """
        if not self._is_initialized:
            return False

        try:
            from sqlalchemy import text

            async with self.get_session() as session:
                # 簡単なクエリでテスト
                await session.execute(text("SELECT 1"))
                logger.debug("Database health check passed")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False

    async def create_tables(self) -> None:
        """
        データベーステーブルを作成

        Note:
            本番環境では Alembic を使用することを推奨
        """
        if not self._is_initialized:
            raise RuntimeError("Database manager is not initialized")

        try:
            from .models.base import Base

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Failed to create tables: {str(e)}")
            raise

    async def drop_tables(self) -> None:
        """
        データベーステーブルを削除

        Warning:
            開発・テスト環境でのみ使用すること
        """
        if not self._is_initialized:
            raise RuntimeError("Database manager is not initialized")

        try:
            from .models.base import Base

            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            logger.warning("Database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {str(e)}")
            raise

    def _mask_password(self, database_url: str) -> str:
        """
        データベースURLのパスワードをマスク

        Args:
            database_url: データベースURL

        Returns:
            str: パスワードがマスクされたURL
        """
        import re

        # パスワード部分を *** でマスク
        return re.sub(r"://([^:]+):([^@]+)@", r"://\1:***@", database_url)

    @property
    def is_initialized(self) -> bool:
        """
        初期化状態を取得

        Returns:
            bool: 初期化済みの場合True
        """
        return self._is_initialized

    @property
    def engine(self):
        """
        エンジンを取得

        Returns:
            AsyncEngine: SQLAlchemyエンジン
        """
        return self._engine


# グローバルなデータベースマネージャーインスタンス
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    データベースセッションを取得する依存性注入用関数

    Yields:
        AsyncSession: データベースセッション

    Usage:
        # Dependency Injection での使用例
        async def some_handler(session: AsyncSession = Depends(get_db_session)):
            # セッションを使用した処理
    """
    async with db_manager.get_session() as session:
        yield session


async def init_database(database_url: str, **kwargs) -> None:
    """
    データベースを初期化する便利関数

    Args:
        database_url: データベースURL
        **kwargs: その他の初期化パラメータ
    """
    await db_manager.initialize(database_url, **kwargs)


async def close_database() -> None:
    """
    データベース接続を閉じる便利関数
    """
    await db_manager.close()


# アプリケーション終了時のクリーンアップ
async def cleanup_database():
    """
    データベースリソースのクリーンアップ

    アプリケーション終了時に呼び出される
    """
    try:
        await close_database()
        logger.info("Database cleanup completed")
    except Exception as e:
        logger.error(f"Database cleanup failed: {str(e)}")


# 開発・テスト用のユーティリティ関数
async def reset_database() -> None:
    """
    データベースをリセット（テーブル削除→作成）

    Warning:
        開発・テスト環境でのみ使用すること
    """
    if not db_manager.is_initialized:
        raise RuntimeError("Database manager is not initialized")

    logger.warning("Resetting database - this will delete all data!")
    await db_manager.drop_tables()
    await db_manager.create_tables()
    logger.info("Database reset completed")


async def get_async_session() -> AsyncSession:
    """
    非同期セッションを取得

    Returns:
        AsyncSession: 非同期セッション
    """
    try:
        import os

        # SQLite専用の設定に強制変更
        database_url = "sqlite+aiosqlite:///./app.db"

        # データベースマネージャーを初期化
        if not hasattr(get_async_session, "_db_manager"):
            get_async_session._db_manager = DatabaseManager()
            await get_async_session._db_manager.initialize(
                database_url,
                echo=False,  # デバッグ時はTrueに変更
                pool_size=5,
                max_overflow=10,
            )

        # セッションファクトリからセッションを取得
        session_factory = await get_async_session._db_manager.get_session_factory()
        return session_factory()

    except Exception as e:
        logger.error(f"Failed to get async session: {str(e)}")
        # フォールバック: 基本的なセッション作成
        try:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

            fallback_url = "sqlite+aiosqlite:///./app.db"
            engine = create_async_engine(fallback_url, echo=False)
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
            return session_factory()
        except Exception as fallback_error:
            logger.error(
                f"Fallback session creation also failed: {str(fallback_error)}"
            )
            raise


async def migrate_database() -> None:
    """
    データベースマイグレーション実行

    Note:
        実際の実装では Alembic を使用
    """
    # TODO: Alembic マイグレーション実装
    logger.info(
        "Database migration would be executed here (Alembic integration needed)"
    )
    pass
