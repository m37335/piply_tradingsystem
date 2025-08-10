"""
Base Repository Implementation
基本リポジトリ実装
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from src.domain.entities.base import BaseEntity
from src.utils.logging_config import get_infrastructure_logger

logger = get_infrastructure_logger()

T = TypeVar("T", bound=BaseEntity)
M = TypeVar("M", bound=DeclarativeBase)


class BaseRepositoryImpl:
    """
    基本リポジトリ実装クラス
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save(self, entity: T) -> T:
        """
        エンティティを保存

        Args:
            entity: 保存するエンティティ

        Returns:
            T: 保存されたエンティティ
        """
        try:
            # モデルに変換
            model = entity.to_model()

            # セッションに追加
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)

            # エンティティに変換して返す
            return entity.__class__.from_model(model)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to save entity: {str(e)}")
            logger.error(f"Entity type: {type(entity)}")
            logger.error(f"Entity has to_model: {hasattr(entity, 'to_model')}")
            raise

    async def find_by_id(
        self, entity_class: Type[T], model_class: Type[M], id: int
    ) -> Optional[T]:
        """
        IDでエンティティを検索

        Args:
            entity_class: エンティティクラス
            model_class: モデルクラス
            id: 検索するID

        Returns:
            Optional[T]: 見つかったエンティティ、見つからない場合はNone
        """
        try:
            stmt = select(model_class).where(model_class.id == id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return entity_class.from_model(model)
            return None

        except Exception as e:
            logger.error(f"Failed to find entity by id: {str(e)}")
            raise

    async def find_by_uuid(
        self, entity_class: Type[T], model_class: Type[M], uuid: str
    ) -> Optional[T]:
        """
        UUIDでエンティティを検索

        Args:
            entity_class: エンティティクラス
            model_class: モデルクラス
            uuid: 検索するUUID

        Returns:
            Optional[T]: 見つかったエンティティ、見つからない場合はNone
        """
        try:
            stmt = select(model_class).where(model_class.uuid == uuid)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return entity_class.from_model(model)
            return None

        except Exception as e:
            logger.error(f"Failed to find entity by uuid: {str(e)}")
            raise

    async def find_all(self, entity_class: Type[T], model_class: Type[M]) -> List[T]:
        """
        すべてのエンティティを取得

        Args:
            entity_class: エンティティクラス
            model_class: モデルクラス

        Returns:
            List[T]: エンティティのリスト
        """
        try:
            stmt = select(model_class)
            result = await self.session.execute(stmt)
            models = result.scalars().all()

            return [entity_class.from_model(model) for model in models]

        except Exception as e:
            logger.error(f"Failed to find all entities: {str(e)}")
            raise

    async def exists(self, model_class: Type[M], **filters) -> bool:
        """
        エンティティの存在確認

        Args:
            model_class: モデルクラス
            **filters: フィルタ条件

        Returns:
            bool: 存在する場合True
        """
        try:
            stmt = select(model_class)
            for key, value in filters.items():
                stmt = stmt.where(getattr(model_class, key) == value)

            result = await self.session.execute(stmt)
            return result.scalar_one_or_none() is not None

        except Exception as e:
            logger.error(f"Failed to check entity existence: {str(e)}")
            raise

    async def delete_by_id(self, model_class: Type[M], id: int) -> bool:
        """
        IDでエンティティを削除

        Args:
            model_class: モデルクラス
            id: 削除するID

        Returns:
            bool: 削除成功時True
        """
        try:
            stmt = select(model_class).where(model_class.id == id)
            result = await self.session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                await self.session.delete(model)
                await self.session.commit()
                return True
            return False

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete entity by id: {str(e)}")
            raise

    async def update(self, entity: T) -> T:
        """
        エンティティを更新

        Args:
            entity: 更新するエンティティ

        Returns:
            T: 更新されたエンティティ
        """
        try:
            # モデルに変換
            model = entity.to_model()

            # セッションにマージ
            merged_model = await self.session.merge(model)
            await self.session.commit()
            await self.session.refresh(merged_model)

            # エンティティに変換して返す
            return entity.__class__.from_model(merged_model)

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to update entity: {str(e)}")
            raise
