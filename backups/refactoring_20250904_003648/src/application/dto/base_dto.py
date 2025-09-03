"""
Base DTO Classes
基底DTOクラス

設計書参照:
- アプリケーション層設計_20250809.md
- 補足設計_Application層_20250809.md

Data Transfer Object (DTO) パターンを実装
アプリケーション層とプレゼンテーション層間でのデータ転送に使用
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Type, TypeVar

T = TypeVar("T", bound="BaseDTO")


@dataclass
class BaseDTO(ABC):
    """
    基底DTOクラス

    責任:
    - レイヤー間でのデータ転送
    - シリアライゼーション/デシリアライゼーション
    - バリデーション
    - 型安全性の保証

    原則:
    - 不変オブジェクトとして設計
    - ビジネスロジックを含まない
    - 外部インターフェースとの契約
    """

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            Dict[str, Any]: DTO の辞書表現
        """
        result = {}

        for field_name, field_value in self.__dict__.items():
            result[field_name] = self._serialize_value(field_value)

        return result

    def _serialize_value(self, value: Any) -> Any:
        """
        値をシリアライズ用に変換

        Args:
            value: 変換する値

        Returns:
            Any: シリアライズ可能な値
        """
        if value is None:
            return None
        elif isinstance(value, BaseDTO):
            return value.to_dict()
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, list):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        elif hasattr(value, "to_dict"):
            return value.to_dict()
        elif hasattr(value, "__dict__"):
            # 他のオブジェクトの場合は辞書変換を試行
            try:
                return self._serialize_value(value.__dict__)
            except Exception:
                return str(value)
        else:
            return value

    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        辞書からDTOインスタンスを作成

        Args:
            data: ソースデータ辞書

        Returns:
            T: DTOインスタンス
        """
        # フィールドの型ヒントを取得
        import inspect

        signature = inspect.signature(cls.__init__)
        field_types = {}

        for param_name, param in signature.parameters.items():
            if param_name != "self":
                field_types[param_name] = param.annotation

        # データを適切な型に変換
        converted_data = {}
        for field_name, field_type in field_types.items():
            if field_name in data:
                converted_data[field_name] = cls._deserialize_value(
                    data[field_name], field_type
                )

        return cls(**converted_data)

    @classmethod
    def _deserialize_value(cls, value: Any, target_type: Any) -> Any:
        """
        値をデシリアライズ

        Args:
            value: 変換する値
            target_type: 目標の型

        Returns:
            Any: 変換された値
        """
        if value is None:
            return None

        # datetime型の変換
        if target_type == datetime and isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

        # BaseDTO派生クラスの変換
        if (
            isinstance(target_type, type)
            and issubclass(target_type, BaseDTO)
            and isinstance(value, dict)
        ):
            return target_type.from_dict(value)

        # リスト型の変換
        if hasattr(target_type, "__origin__") and target_type.__origin__ is list:
            if isinstance(value, list):
                list_item_type = (
                    target_type.__args__[0] if target_type.__args__ else Any
                )
                return [cls._deserialize_value(item, list_item_type) for item in value]

        # Optional型の処理
        try:
            if hasattr(target_type, "__origin__"):
                # Union型（Optional含む）の処理
                if str(target_type).startswith("typing.Union") or str(
                    target_type
                ).startswith("typing.Optional"):
                    # Optional[T] は Union[T, None] なので最初の引数を取得
                    if hasattr(target_type, "__args__") and target_type.__args__:
                        inner_type = target_type.__args__[0]
                        if inner_type != type(None):
                            return cls._deserialize_value(value, inner_type)
        except Exception:
            pass

        return value

    def to_json(self, indent: Optional[int] = None) -> str:
        """
        JSON文字列に変換

        Args:
            indent: インデント（pretty print用）

        Returns:
            str: JSON文字列
        """
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        JSON文字列からDTOインスタンスを作成

        Args:
            json_str: JSON文字列

        Returns:
            T: DTOインスタンス
        """
        data = json.loads(json_str)
        return cls.from_dict(data)

    def validate(self) -> None:
        """
        DTOの妥当性を検証
        サブクラスでオーバーライドして具体的なバリデーションを実装

        Raises:
            ValueError: バリデーションエラー
        """
        pass

    def __post_init__(self) -> None:
        """
        初期化後処理
        バリデーションを実行
        """
        self.validate()

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: DTOの文字列表現
        """
        fields = []
        for field_name, field_value in self.__dict__.items():
            if field_value is not None:
                if isinstance(field_value, str) and len(field_value) > 50:
                    value_str = field_value[:47] + "..."
                else:
                    value_str = str(field_value)
                fields.append(f"{field_name}={value_str}")

        return f"{self.__class__.__name__}({', '.join(fields)})"

    def __repr__(self) -> str:
        """
        詳細文字列表現

        Returns:
            str: DTOの詳細文字列表現
        """
        return self.__str__()


@dataclass
class PaginatedDTO(BaseDTO):
    """
    ページング付きDTOの基底クラス

    リスト形式のデータを返す際のページング情報を含む
    """

    items: list
    total_count: int
    page: int = 1
    per_page: int = 100
    total_pages: Optional[int] = None
    has_next: Optional[bool] = None
    has_prev: Optional[bool] = None

    def __post_init__(self) -> None:
        """
        初期化後処理
        ページング情報の計算
        """
        super().__post_init__()

        # 総ページ数の計算
        if self.total_pages is None:
            self.total_pages = (self.total_count + self.per_page - 1) // self.per_page

        # 前後ページの存在フラグ
        if self.has_next is None:
            self.has_next = self.page < self.total_pages

        if self.has_prev is None:
            self.has_prev = self.page > 1

    def get_pagination_info(self) -> Dict[str, Any]:
        """
        ページング情報を取得

        Returns:
            Dict[str, Any]: ページング情報
        """
        return {
            "total_count": self.total_count,
            "page": self.page,
            "per_page": self.per_page,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
            "items_count": len(self.items),
        }


@dataclass
class ErrorDTO(BaseDTO):
    """
    エラー情報DTO

    APIエラーレスポンス用の標準化されたエラー情報
    """

    error_code: str
    error_message: str
    error_type: str = "ApplicationError"
    timestamp: datetime = None
    details: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None

    def __post_init__(self) -> None:
        """
        初期化後処理
        """
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

        super().__post_init__()

    def validate(self) -> None:
        """
        エラーDTOのバリデーション
        """
        if not self.error_code:
            raise ValueError("Error code is required")

        if not self.error_message:
            raise ValueError("Error message is required")


@dataclass
class SuccessDTO(BaseDTO):
    """
    成功レスポンスDTO

    API成功レスポンス用の標準化された成功情報
    """

    success: bool = True
    message: str = "Operation completed successfully"
    data: Optional[Any] = None
    timestamp: datetime = None
    operation_id: Optional[str] = None

    def __post_init__(self) -> None:
        """
        初期化後処理
        """
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.utcnow())

        super().__post_init__()
