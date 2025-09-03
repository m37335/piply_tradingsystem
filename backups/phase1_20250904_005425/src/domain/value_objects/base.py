"""
Base Value Object Classes
基底値オブジェクトクラス

設計書参照:
- 詳細内部設計_20250809.md

Domain-Driven Design (DDD) に基づいた値オブジェクトの基底クラス
値オブジェクトは不変性と等価性が重要
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any, Dict, Generic, TypeVar

# Type variable for Value Object types
T = TypeVar("T", bound="BaseValueObject")


@dataclass(frozen=True)
class BaseValueObject(ABC):
    """
    値オブジェクトの基底クラス

    責任:
    - 不変性の保証 (frozen=True)
    - 値による等価性判定
    - バリデーション
    - シリアライゼーション

    特徴:
    - frozen=True により不変性を保証
    - __eq__ と __hash__ は自動生成される
    - 値による比較が行われる
    """

    def __post_init__(self) -> None:
        """
        初期化後処理
        バリデーションを実行
        """
        self._validate()

    def _validate(self) -> None:
        """
        値オブジェクトのバリデーション
        サブクラスでオーバーライドして具体的なバリデーションを実装

        Raises:
            ValueError: バリデーションエラー
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換
        シリアライゼーション用

        Returns:
            Dict[str, Any]: 値オブジェクトの辞書表現
        """
        result = {}
        for field_name, field_value in self.__dict__.items():
            if hasattr(field_value, "to_dict"):
                result[field_name] = field_value.to_dict()
            elif hasattr(field_value, "isoformat"):  # datetime objects
                result[field_name] = field_value.isoformat()
            else:
                result[field_name] = field_value
        return result

    @classmethod
    def from_dict(cls: type[T], data: Dict[str, Any]) -> T:
        """
        辞書から値オブジェクトを復元
        デシリアライゼーション用

        Args:
            data: 値オブジェクトデータの辞書

        Returns:
            T: 復元された値オブジェクトインスタンス
        """
        return cls(**data)

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: 値オブジェクトの文字列表現
        """
        fields = ", ".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"
