"""
Base Repository Implementation
基底リポジトリ実装

設計書参照:
- インフラ・プラグイン設計_20250809.md

ドメインリポジトリインターフェースの基底実装
"""

from typing import Any, Dict, List, Optional, Type, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ....domain.entities.base import BaseEntity
from ....domain.repositories.base import BaseRepository
from ....utils.logging_config import get_infrastructure_logger
from ..models.base import BaseModel

logger = get_infrastructure_logger()

# Type variables
E = TypeVar("E", bound=BaseEntity)
M = TypeVar("M", bound=BaseModel)


class BaseRepositoryImpl(BaseRepository[E]):
    """
    基底リポジトリ実装クラス

    責任:
    - ドメインリポジトリインターフェースの実装
    - モデル↔エンティティ変換
    - 基本的なCRUD操作
    - エラーハンドリング
    - ログ記録

    Type Parameters:
    - E: ドメインエンティティ型
    - M: データベースモデル型
    """

    def __init__(
        self, session: AsyncSession, model_class: Type[M], entity_class: Type[E]
    ):
        """
        初期化

        Args:
            session: データベースセッション
            model_class: データベースモデルクラス
            entity_class: ドメインエンティティクラス
        """
        self._session = session
        self._model_class = model_class
        self._entity_class = entity_class

        logger.debug(
            f"Initialized {self.__class__.__name__} "
            f"for {entity_class.__name__} -> {model_class.__name__}"
        )

    async def add(self, entity: E) -> E:
        """
        新しいエンティティを追加

        Args:
            entity: 追加するエンティティ

        Returns:
            E: 追加されたエンティティ（IDなどが設定された状態）
        """
        try:
            # エンティティをモデルに変換
            model = self._entity_to_model(entity)

            # データベースに追加
            self._session.add(model)
            await self._session.flush()  # IDを取得するためにflush

            # モデルをエンティティに変換して返す
            result_entity = self._model_to_entity(model)

            logger.debug(f"Added {self._entity_class.__name__} with ID: {model.id}")
            return result_entity

        except Exception as e:
            logger.error(f"Failed to add {self._entity_class.__name__}: {str(e)}")
            raise

    async def get_by_id(self, entity_id: int) -> Optional[E]:
        """
        IDでエンティティを取得

        Args:
            entity_id: 取得するエンティティのID

        Returns:
            Optional[E]: エンティティ、存在しない場合None
        """
        try:
            result = await self._session.execute(
                select(self._model_class).where(self._model_class.id == entity_id)
            )
            model = result.scalar_one_or_none()

            if model:
                entity = self._model_to_entity(model)
                logger.debug(
                    f"Found {self._entity_class.__name__} by ID: "
                    f"{entity_id}"
                )
                return entity
            else:
                logger.debug(
                    f"No {self._entity_class.__name__} found with ID: {entity_id}"
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to get {self._entity_class.__name__} by ID {entity_id}: {str(e)}"
            )
            raise

    async def update(self, entity: E) -> E:
        """
        既存のエンティティを更新

        Args:
            entity: 更新するエンティティ

        Returns:
            E: 更新されたエンティティ
        """
        try:
            # 既存のモデルを取得
            if entity.id:
                result = await self._session.execute(
                    select(self._model_class).where(self._model_class.id == entity.id)
                )
                existing_model = result.scalar_one_or_none()

                if not existing_model:
                    raise ValueError(f"Entity with ID {entity.id} not found")

                # モデルを更新
                self._update_model_from_entity(existing_model, entity)
                await self._session.flush()

                # 更新されたエンティティを返す
                result_entity = self._model_to_entity(existing_model)
                logger.debug(
                    f"Updated {self._entity_class.__name__} with ID: {entity.id}"
                )
                return result_entity
            else:
                # IDがない場合は新規追加として扱う
                logger.warning("Entity has no ID, treating as new")
                return await self.add(entity)

        except Exception as e:
            logger.error(f"Failed to update {self._entity_class.__name__}: {str(e)}")
            raise

    async def delete(self, entity: E) -> None:
        """
        エンティティを削除

        Args:
            entity: 削除するエンティティ
        """
        try:
            if entity.id:
                await self._session.execute(
                    delete(self._model_class).where(self._model_class.id == entity.id)
                )
                logger.debug(
                    f"Deleted {self._entity_class.__name__} with ID: {entity.id}"
                )
            else:
                raise ValueError("Cannot delete entity without ID")

        except Exception as e:
            logger.error(f"Failed to delete {self._entity_class.__name__}: {str(e)}")
            raise

    async def list_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[E]:
        """
        全てのエンティティをリスト

        Args:
            limit: 取得する最大件数
            offset: 取得開始位置

        Returns:
            List[E]: エンティティのリスト
        """
        try:
            query = select(self._model_class).order_by(
                self._model_class.created_at.desc()
            )

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            result = await self._session.execute(query)
            models = result.scalars().all()

            entities = [self._model_to_entity(model) for model in models]

            logger.debug(
                f"Retrieved {len(entities)} {self._entity_class.__name__} entities"
            )
            return entities

        except Exception as e:
            logger.error(
                f"Failed to list {self._entity_class.__name__} entities: {str(e)}"
            )
            raise

    async def count(self) -> int:
        """
        エンティティの総数を取得

        Returns:
            int: エンティティの総数
        """
        try:
            result = await self._session.execute(
                select(func.count(self._model_class.id))
            )
            count = result.scalar()

            logger.debug(f"Counted {count} {self._entity_class.__name__} entities")
            return count or 0

        except Exception as e:
            logger.error(
                f"Failed to count {self._entity_class.__name__} entities: {str(e)}"
            )
            raise

    async def save_changes(self) -> None:
        """
        現在のセッションでの変更を永続化
        """
        try:
            await self._session.commit()
            logger.debug("Session changes committed")
        except Exception as e:
            await self._session.rollback()
            logger.error(f"Failed to save changes, rolled back: {str(e)}")
            raise

    # 内部メソッド（サブクラスでオーバーライド可能）

    def _entity_to_model(self, entity: E) -> M:
        """
        エンティティをモデルに変換

        Args:
            entity: ドメインエンティティ

        Returns:
            M: データベースモデル
        """
        if hasattr(self._model_class, "from_entity"):
            return self._model_class.from_entity(entity)
        else:
            raise NotImplementedError(
                f"{self._model_class.__name__} must implement from_entity method"
            )

    def _model_to_entity(self, model: M) -> E:
        """
        モデルをエンティティに変換

        Args:
            model: データベースモデル

        Returns:
            E: ドメインエンティティ
        """
        if hasattr(model, "to_entity"):
            return model.to_entity()
        else:
            raise NotImplementedError(
                f"{self._model_class.__name__} must implement to_entity method"
            )

    def _update_model_from_entity(self, model: M, entity: E) -> None:
        """
        エンティティからモデルを更新

        Args:
            model: 更新対象のデータベースモデル
            entity: 更新元のドメインエンティティ
        """
        if hasattr(model, "update_from_entity"):
            model.update_from_entity(entity)
        else:
            # フォールバック: 手動で基本フィールドを更新
            if hasattr(entity, "updated_at"):
                model.updated_at = entity.updated_at
            if hasattr(entity, "version"):
                model.version = entity.version

            logger.warning(
                f"{self._model_class.__name__} does not implement update_from_entity method"
            )

    # ユーティリティメソッド

    async def exists_by_id(self, entity_id: int) -> bool:
        """
        指定IDのエンティティが存在するかチェック

        Args:
            entity_id: チェックするID

        Returns:
            bool: 存在する場合True
        """
        try:
            result = await self._session.execute(
                select(func.count(self._model_class.id)).where(
                    self._model_class.id == entity_id
                )
            )
            count = result.scalar()
            return count > 0
        except Exception as e:
            logger.error(f"Failed to check existence by ID {entity_id}: {str(e)}")
            raise

    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[E]:
        """
        指定条件でエンティティを検索

        Args:
            criteria: 検索条件の辞書

        Returns:
            List[E]: 条件に合致するエンティティのリスト
        """
        try:
            query = select(self._model_class)

            # 動的に条件を追加
            for field, value in criteria.items():
                if hasattr(self._model_class, field):
                    query = query.where(getattr(self._model_class, field) == value)

            result = await self._session.execute(query)
            models = result.scalars().all()

            entities = [self._model_to_entity(model) for model in models]

            logger.debug(
                f"Found {len(entities)} {self._entity_class.__name__} entities "
                f"matching criteria: {criteria}"
            )
            return entities

        except Exception as e:
            logger.error(f"Failed to find by criteria {criteria}: {str(e)}")
            raise
