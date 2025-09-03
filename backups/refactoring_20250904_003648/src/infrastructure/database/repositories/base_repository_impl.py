"""
Base Repository Implementation
基本リポジトリ実装
"""

from typing import List, Optional, Type, TypeVar

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

    async def find_all(self, entity_class: Type[T], model_class: Type[M]) -> List[T]:
        """
        全エンティティを取得

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

    async def delete(self, entity: T) -> bool:
        """
        エンティティを削除

        Args:
            entity: 削除するエンティティ

        Returns:
            bool: 削除成功の場合True
        """
        try:
            # モデルに変換
            model = entity.to_model()

            # セッションから削除
            await self.session.delete(model)
            await self.session.commit()

            return True

        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to delete entity: {str(e)}")
            raise

    async def count(self, model_class: Type[M]) -> int:
        """
        エンティティの総数を取得

        Args:
            model_class: モデルクラス

        Returns:
            int: エンティティの総数
        """
        try:
            stmt = select(model_class)
            result = await self.session.execute(stmt)
            return len(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to count entities: {str(e)}")
            raise
