"""
Base Entity Classes
基底エンティティクラス

設計書参照:
- 詳細内部設計_20250809.md

Domain-Driven Design (DDD) に基づいたエンティティの基底クラス
全てのドメインエンティティはこのクラスを継承する
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, TypeVar

from src.utils.logging_config import get_domain_logger

logger = get_domain_logger()

# Type variable for Entity types
T = TypeVar("T", bound="BaseEntity")


@dataclass
class BaseEntity(ABC):
    """
    全エンティティの基底クラス

    責任:
    - エンティティの一意性保証
    - 作成・更新時刻の管理
    - バージョン管理（楽観的ロック）
    - 基本的なシリアライゼーション
    """

    id: Optional[int] = None
    uuid: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 1

    def __post_init__(self) -> None:
        """
        初期化後処理
        作成・更新時刻の自動設定
        """
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

        logger.debug(f"Created {self.__class__.__name__} entity with ID: {self.id}")

    def update_version(self) -> None:
        """
        バージョン更新
        楽観的ロック用のバージョン管理
        """
        self.version += 1
        self.updated_at = datetime.utcnow()

        logger.debug(
            f"Updated {self.__class__.__name__} entity version to {self.version}"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換
        シリアライゼーション用

        Returns:
            Dict[str, Any]: エンティティの辞書表現
        """
        return {
            "id": self.id,
            "uuid": self.uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """
        辞書からエンティティを復元
        デシリアライゼーション用

        Args:
            data: エンティティデータの辞書

        Returns:
            T: 復元されたエンティティインスタンス
        """
        # 日時文字列をdatetimeオブジェクトに変換
        if "created_at" in data and data["created_at"]:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and data["updated_at"]:
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])

        # uuidフィールドが存在しない場合はNoneを設定
        if "uuid" not in data:
            data["uuid"] = None

        return cls(**data)

    def is_new(self) -> bool:
        """
        新規エンティティかどうかを判定

        Returns:
            bool: IDが未設定の場合True
        """
        return self.id is None

    def __eq__(self, other: object) -> bool:
        """
        エンティティの等価性判定
        IDで比較

        Args:
            other: 比較対象

        Returns:
            bool: 等価性判定結果
        """
        if not isinstance(other, BaseEntity):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """
        ハッシュ値の計算
        IDベース

        Returns:
            int: ハッシュ値
        """
        return hash(self.id) if self.id is not None else hash(id(self))


@dataclass
class AggregateRoot(BaseEntity):
    """
    集約ルートの基底クラス

    Domain-Driven Designにおける集約の概念を実装
    ドメインイベントの管理も担当
    """

    _domain_events: list = field(default_factory=list, init=False)

    def add_domain_event(self, event: Any) -> None:
        """
        ドメインイベントを追加

        Args:
            event: 発生したドメインイベント
        """
        self._domain_events.append(event)
        logger.debug(f"Added domain event: {event.__class__.__name__}")

    def clear_domain_events(self) -> list:
        """
        ドメインイベントをクリアして返す

        Returns:
            list: 発生していたドメインイベントのリスト
        """
        events = self._domain_events.copy()
        self._domain_events.clear()
        logger.debug(f"Cleared {len(events)} domain events")
        return events

    def get_domain_events(self) -> list:
        """
        ドメインイベントを取得（クリアしない）

        Returns:
            list: 発生しているドメインイベントのリスト
        """
        return self._domain_events.copy()
