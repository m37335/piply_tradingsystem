"""
Base Repository Implementation 2
基底リポジトリ実装 2

設計書参照:
- インフラ・プラグイン設計_20250809.md

ドメインリポジトリインターフェースの基底実装（バックアップ版）
"""

import logging
from typing import List, Optional, Type, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.base import BaseEntity
from src.infrastructure.database.models.base import BaseModel

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T", bound=BaseEntity)
M = TypeVar("M", bound=BaseModel)


class BaseRepositoryImpl2:
    """
    基底リポジトリ実装クラス 2

    責任:
    - ドメインリポジトリインターフェースの実装
    - モデル↔エンティティ変換
    - 基本的なCRUD操作
    - エラーハンドリング
    - ログ記録

    Type Parameters:
    - T: ドメインエンティティ型
    - M: データベースモデル型
    """

    def __init__(self, session: AsyncSession):
        """
        初期化

        Args:
            session: データベースセッション
        """
        self.session = session

    async def save(self, entity: T, model_class: Type[M]) -> T:
        """
        エンティティを保存

        Args:
            entity: 保存するエンティティ
            model_class: モデルクラス

        Returns:
            T: 保存されたエンティティ
        """
        try:
            model = entity.to_model()
            self.session.add(model)
            await self.session.commit()
            await self.session.refresh(model)
            return entity.__class__.from_model(model)

        except Exception as e:
            logger.error(f"Failed to save entity: {str(e)}")
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
            logger.error(f"Failed to delete entity by id: {str(e)}")
            raise

    async def update(self, entity: T, model_class: Type[M]) -> T:
        """
        エンティティを更新

        Args:
            entity: 更新するエンティティ
            model_class: モデルクラス

        Returns:
            T: 更新されたエンティティ
        """
        try:
            model = entity.to_model()
            await self.session.merge(model)
            await self.session.commit()
            await self.session.refresh(model)
            return entity.__class__.from_model(model)

        except Exception as e:
            logger.error(f"Failed to update entity: {str(e)}")
            raise

    async def count(self, model_class: Type[M]) -> int:
        """
        エンティティの数を取得

        Args:
            model_class: モデルクラス

        Returns:
            int: エンティティの数
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count(model_class.id))
            result = await self.session.execute(stmt)
            return result.scalar()

        except Exception as e:
            logger.error(f"Failed to count entities: {str(e)}")
            raise
