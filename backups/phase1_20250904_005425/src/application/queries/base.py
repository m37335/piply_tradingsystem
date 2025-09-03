"""
Base Query Classes
基底クエリクラス

設計書参照:
- アプリケーション層設計_20250809.md

CQRSパターンのQueryサイドを実装
全ての読み込み操作（データ取得）はQueryとして定義される
"""

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, Optional, TypeVar

from ...utils.logging_config import get_application_logger

logger = get_application_logger()

# Type variable for Query result types
TResult = TypeVar("TResult")


@dataclass
class BaseQuery(ABC, Generic[TResult]):
    """
    全クエリの基底クラス

    責任:
    - クエリの一意性保証
    - 実行時刻の記録
    - メタデータ管理
    - パフォーマンス追跡

    CQRSパターンの原則:
    - クエリは読み込み操作を表現
    - 副作用を持たない
    - データを返す
    """

    # 基本フィールド
    query_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # オプションフィールド
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # パフォーマンス追跡
    execution_start: Optional[datetime] = None
    execution_end: Optional[datetime] = None

    def __post_init__(self) -> None:
        """
        初期化後処理
        ログ記録とメタデータ初期化
        """
        logger.debug(f"Created {self.__class__.__name__} with ID: {self.query_id}")

        # メタデータにクエリ情報を追加
        self.add_metadata("query_type", self.__class__.__name__)
        self.add_metadata("created_at", self.timestamp.isoformat())

    def add_metadata(self, key: str, value: Any) -> None:
        """
        メタデータを追加

        Args:
            key: メタデータのキー
            value: メタデータの値
        """
        self.metadata[key] = value
        logger.debug(f"Added metadata to {self.query_id}: {key}={value}")

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        メタデータを取得

        Args:
            key: メタデータのキー
            default: デフォルト値

        Returns:
            Any: メタデータの値
        """
        return self.metadata.get(key, default)

    def set_correlation_id(self, correlation_id: str) -> None:
        """
        相関IDを設定
        分散システムでのトレーシング用

        Args:
            correlation_id: 相関ID
        """
        self.correlation_id = correlation_id
        self.add_metadata("correlation_id", correlation_id)

    def set_user_context(self, user_id: str, **user_info) -> None:
        """
        ユーザーコンテキストを設定

        Args:
            user_id: ユーザーID
            **user_info: 追加のユーザー情報
        """
        self.user_id = user_id
        self.add_metadata("user_id", user_id)

        for key, value in user_info.items():
            self.add_metadata(f"user_{key}", value)

    def start_execution(self) -> None:
        """
        実行開始を記録
        パフォーマンス測定用
        """
        self.execution_start = datetime.utcnow()
        self.add_metadata("execution_start", self.execution_start.isoformat())
        logger.debug(f"Started execution of {self.query_id}")

    def end_execution(self) -> None:
        """
        実行終了を記録
        パフォーマンス測定用
        """
        self.execution_end = datetime.utcnow()
        self.add_metadata("execution_end", self.execution_end.isoformat())

        if self.execution_start:
            duration = self.execution_end - self.execution_start
            duration_ms = duration.total_seconds() * 1000
            self.add_metadata("execution_duration_ms", duration_ms)

            logger.debug(
                f"Completed execution of {self.query_id} in {duration_ms:.2f}ms"
            )
        else:
            logger.warning(
                f"Execution ended for {self.query_id} but start time was not recorded"
            )

    def get_execution_duration_ms(self) -> Optional[float]:
        """
        実行時間を取得（ミリ秒）

        Returns:
            Optional[float]: 実行時間（ミリ秒）、未計測の場合None
        """
        if self.execution_start and self.execution_end:
            duration = self.execution_end - self.execution_start
            return duration.total_seconds() * 1000
        return None

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換
        ログやシリアライゼーション用

        Returns:
            Dict[str, Any]: クエリの辞書表現
        """
        result = {
            "query_id": self.query_id,
            "query_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata.copy(),
        }

        if self.execution_start:
            result["execution_start"] = self.execution_start.isoformat()

        if self.execution_end:
            result["execution_end"] = self.execution_end.isoformat()

        duration = self.get_execution_duration_ms()
        if duration is not None:
            result["execution_duration_ms"] = duration

        return result

    def is_expired(self, max_age_seconds: int = 300) -> bool:
        """
        クエリが期限切れかどうかを判定

        Args:
            max_age_seconds: 最大有効時間（秒）デフォルト5分

        Returns:
            bool: 期限切れの場合True
        """
        age = datetime.utcnow() - self.timestamp
        return age.total_seconds() > max_age_seconds

    def validate(self) -> None:
        """
        クエリのバリデーション
        サブクラスでオーバーライドして具体的なバリデーションを実装

        Raises:
            ValueError: バリデーションエラー
        """
        if not self.query_id:
            raise ValueError("Query ID is required")

        if not self.timestamp:
            raise ValueError("Timestamp is required")

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: クエリの文字列表現
        """
        return f"{self.__class__.__name__}(id={self.query_id})"

    def __repr__(self) -> str:
        """
        詳細文字列表現

        Returns:
            str: クエリの詳細文字列表現
        """
        return (
            f"{self.__class__.__name__}("
            f"query_id={self.query_id}, "
            f"timestamp={self.timestamp}, "
            f"user_id={self.user_id})"
        )
