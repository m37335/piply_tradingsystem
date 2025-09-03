"""
Base Command Classes
基底コマンドクラス

設計書参照:
- アプリケーション層設計_20250809.md

CQRSパターンのCommandサイドを実装
全ての書き込み操作（データ変更）はCommandとして定義される
"""

import uuid
from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

from ...utils.logging_config import get_application_logger

logger = get_application_logger()


@dataclass
class BaseCommand(ABC):
    """
    全コマンドの基底クラス

    責任:
    - コマンドの一意性保証
    - 実行時刻の記録
    - メタデータ管理
    - ユーザー追跡

    CQRSパターンの原則:
    - コマンドは書き込み操作を表現
    - 副作用を持つ操作
    - 戻り値は成功/失敗のみ
    """

    # 基本フィールド
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # オプションフィールド
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        初期化後処理
        ログ記録とメタデータ初期化
        """
        logger.debug(f"Created {self.__class__.__name__} with ID: {self.command_id}")

        # メタデータにコマンド情報を追加
        self.add_metadata("command_type", self.__class__.__name__)
        self.add_metadata("created_at", self.timestamp.isoformat())

    def add_metadata(self, key: str, value: Any) -> None:
        """
        メタデータを追加

        Args:
            key: メタデータのキー
            value: メタデータの値
        """
        self.metadata[key] = value
        logger.debug(f"Added metadata to {self.command_id}: {key}={value}")

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

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換
        ログやシリアライゼーション用

        Returns:
            Dict[str, Any]: コマンドの辞書表現
        """
        return {
            "command_id": self.command_id,
            "command_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata.copy(),
        }

    def is_expired(self, max_age_seconds: int = 3600) -> bool:
        """
        コマンドが期限切れかどうかを判定

        Args:
            max_age_seconds: 最大有効時間（秒）

        Returns:
            bool: 期限切れの場合True
        """
        age = datetime.utcnow() - self.timestamp
        return age.total_seconds() > max_age_seconds

    def validate(self) -> None:
        """
        コマンドのバリデーション
        サブクラスでオーバーライドして具体的なバリデーションを実装

        Raises:
            ValueError: バリデーションエラー
        """
        if not self.command_id:
            raise ValueError("Command ID is required")

        if not self.timestamp:
            raise ValueError("Timestamp is required")

    def __str__(self) -> str:
        """
        文字列表現

        Returns:
            str: コマンドの文字列表現
        """
        return f"{self.__class__.__name__}(id={self.command_id})"

    def __repr__(self) -> str:
        """
        詳細文字列表現

        Returns:
            str: コマンドの詳細文字列表現
        """
        return (
            f"{self.__class__.__name__}("
            f"command_id={self.command_id}, "
            f"timestamp={self.timestamp}, "
            f"user_id={self.user_id})"
        )
