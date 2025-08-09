"""
Base Repository Interface
基底リポジトリインターフェース

設計書参照:
- 詳細内部設計_20250809.md
- モジュール設計思想_20250809.md

Domain-Driven Design (DDD) のリポジトリパターンを実装
インフラストラクチャ層の実装から分離された抽象インターフェース
"""

from abc import ABC, abstractmethod

# datetime imported in other modules
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..entities.base import BaseEntity

# Type variable for Entity types
T = TypeVar("T", bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """
    基底リポジトリインターフェース

    責任:
    - エンティティの永続化インターフェース定義
    - CRUD操作の抽象化
    - データアクセス層からドメイン層の分離

    原則:
    - 実装の詳細をドメイン層から隠蔽
    - インフラストラクチャ層で具象実装
    - ドメインロジックに集中可能
    """

    @abstractmethod
    async def save(self, entity: T) -> T:
        """
        エンティティの保存

        Args:
            entity: 保存するエンティティ

        Returns:
            T: 保存されたエンティティ（IDが設定される）

        Raises:
            RepositoryError: 保存エラー
        """
        pass

    @abstractmethod
    async def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        IDによるエンティティの検索

        Args:
            entity_id: エンティティのID

        Returns:
            Optional[T]: 見つかったエンティティ、存在しない場合None

        Raises:
            RepositoryError: 検索エラー
        """
        pass

    @abstractmethod
    async def find_by_uuid(self, uuid: str) -> Optional[T]:
        """
        UUIDによるエンティティの検索

        Args:
            uuid: エンティティのUUID

        Returns:
            Optional[T]: 見つかったエンティティ、存在しない場合None

        Raises:
            RepositoryError: 検索エラー
        """
        pass

    @abstractmethod
    async def find_all(self, limit: int = 100, offset: int = 0) -> List[T]:
        """
        全エンティティの取得（ページング）

        Args:
            limit: 最大取得件数
            offset: 取得開始位置

        Returns:
            List[T]: エンティティのリスト

        Raises:
            RepositoryError: 検索エラー
        """
        pass

    @abstractmethod
    async def count(self) -> int:
        """
        エンティティの総数を取得

        Returns:
            int: エンティティの総数

        Raises:
            RepositoryError: カウントエラー
        """
        pass

    @abstractmethod
    async def delete(self, entity: T) -> bool:
        """
        エンティティの削除

        Args:
            entity: 削除するエンティティ

        Returns:
            bool: 削除成功の場合True

        Raises:
            RepositoryError: 削除エラー
        """
        pass

    @abstractmethod
    async def delete_by_id(self, entity_id: int) -> bool:
        """
        IDによるエンティティの削除

        Args:
            entity_id: 削除するエンティティのID

        Returns:
            bool: 削除成功の場合True

        Raises:
            RepositoryError: 削除エラー
        """
        pass

    @abstractmethod
    async def exists(self, entity_id: int) -> bool:
        """
        エンティティの存在確認

        Args:
            entity_id: 確認するエンティティのID

        Returns:
            bool: 存在する場合True

        Raises:
            RepositoryError: 確認エラー
        """
        pass

    @abstractmethod
    async def find_by_criteria(self, criteria: Dict[str, Any]) -> List[T]:
        """
        条件によるエンティティの検索

        Args:
            criteria: 検索条件の辞書

        Returns:
            List[T]: 条件に合致するエンティティのリスト

        Raises:
            RepositoryError: 検索エラー
        """
        pass


class RepositoryError(Exception):
    """
    リポジトリ操作エラー
    データアクセス層で発生するエラーの基底クラス
    """

    def __init__(self, message: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.original_error = original_error


class EntityNotFoundError(RepositoryError):
    """
    エンティティが見つからないエラー
    """

    def __init__(self, entity_type: str, identifier: Any):
        message = f"{entity_type} with identifier {identifier} not found"
        super().__init__(message)
        self.entity_type = entity_type
        self.identifier = identifier


class DuplicateEntityError(RepositoryError):
    """
    重複エンティティエラー
    """

    def __init__(self, entity_type: str, field: str, value: Any):
        message = f"Duplicate {entity_type} with {field}={value}"
        super().__init__(message)
        self.entity_type = entity_type
        self.field = field
        self.value = value


class OptimisticLockError(RepositoryError):
    """
    楽観的ロックエラー
    """

    def __init__(
        self,
        entity_type: str,
        entity_id: Any,
        expected_version: int,
        actual_version: int,
    ):
        message = (
            f"Optimistic lock conflict for {entity_type} {entity_id}: "
            f"expected version {expected_version}, but was {actual_version}"
        )
        super().__init__(message)
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.expected_version = expected_version
        self.actual_version = actual_version
