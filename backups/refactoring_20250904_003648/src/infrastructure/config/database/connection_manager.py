"""
データベース接続管理
SQLAlchemyエンジンとセッションの管理を担当
"""

import logging
from typing import Optional, AsyncGenerator
from contextlib import asynccontextmanager, contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.exc import SQLAlchemyError

from .database_config import DatabaseConfig


class ConnectionManager:
    """データベース接続管理クラス"""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # エンジンとセッションファクトリ
        self._engine: Optional[Engine] = None
        self._async_engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[sessionmaker] = None
        self._async_session_factory: Optional[async_sessionmaker] = None
    
    def get_engine(self) -> Engine:
        """同期SQLAlchemyエンジンを取得"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    def get_async_engine(self) -> AsyncEngine:
        """非同期SQLAlchemyエンジンを取得"""
        if self._async_engine is None:
            self._async_engine = self._create_async_engine()
        return self._async_engine
    
    def _create_engine(self) -> Engine:
        """同期エンジンを作成"""
        try:
            sqlalchemy_config = self.config.get_sqlalchemy_config()
            engine = create_engine(**sqlalchemy_config)
            
            self.logger.info(f"Created synchronous database engine: {self.config.host}:{self.config.port}")
            return engine
            
        except Exception as e:
            self.logger.error(f"Failed to create database engine: {e}")
            raise
    
    def _create_async_engine(self) -> AsyncEngine:
        """非同期エンジンを作成"""
        try:
            sqlalchemy_config = self.config.get_async_sqlalchemy_config()
            engine = create_async_engine(**sqlalchemy_config)
            
            self.logger.info(f"Created asynchronous database engine: {self.config.host}:{self.config.port}")
            return engine
            
        except Exception as e:
            self.logger.error(f"Failed to create async database engine: {e}")
            raise
    
    def get_session_factory(self) -> sessionmaker:
        """同期セッションファクトリを取得"""
        if self._session_factory is None:
            engine = self.get_engine()
            self._session_factory = sessionmaker(
                bind=engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._session_factory
    
    def get_async_session_factory(self) -> async_sessionmaker:
        """非同期セッションファクトリを取得"""
        if self._async_session_factory is None:
            engine = self.get_async_engine()
            self._async_session_factory = async_sessionmaker(
                bind=engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False
            )
        return self._async_session_factory
    
    @contextmanager
    def get_session(self):
        """同期セッションのコンテキストマネージャー"""
        session_factory = self.get_session_factory()
        session = session_factory()
        
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """非同期セッションのコンテキストマネージャー"""
        session_factory = self.get_async_session_factory()
        session = session_factory()
        
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            self.logger.error(f"Async database session error: {e}")
            raise
        finally:
            await session.close()
    
    def test_connection(self) -> bool:
        """データベース接続をテスト"""
        try:
            engine = self.get_engine()
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            
            self.logger.info("Database connection test successful")
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection test: {e}")
            return False
    
    async def test_async_connection(self) -> bool:
        """非同期データベース接続をテスト"""
        try:
            engine = self.get_async_engine()
            async with engine.begin() as connection:
                result = await connection.execute(text("SELECT 1"))
                await result.fetchone()
            
            self.logger.info("Async database connection test successful")
            return True
            
        except SQLAlchemyError as e:
            self.logger.error(f"Async database connection test failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during async connection test: {e}")
            return False
    
    def close_connections(self) -> None:
        """全ての接続を閉じる"""
        try:
            if self._engine:
                self._engine.dispose()
                self.logger.info("Disposed synchronous database engine")
            
            if self._async_engine:
                # 非同期エンジンは直接disposeできないため、ログのみ
                self.logger.info("Async database engine will be disposed automatically")
                
        except Exception as e:
            self.logger.error(f"Error closing database connections: {e}")
    
    async def close_async_connections(self) -> None:
        """非同期接続を閉じる"""
        try:
            if self._async_engine:
                await self._async_engine.dispose()
                self.logger.info("Disposed asynchronous database engine")
                
        except Exception as e:
            self.logger.error(f"Error closing async database connections: {e}")
    
    def get_connection_info(self) -> dict:
        """接続情報を取得"""
        return {
            "host": self.config.host,
            "port": self.config.port,
            "database": self.config.database,
            "username": self.config.username,
            "pool_size": self.config.pool_size,
            "max_overflow": self.config.max_overflow,
            "engine_created": self._engine is not None,
            "async_engine_created": self._async_engine is not None
        }
