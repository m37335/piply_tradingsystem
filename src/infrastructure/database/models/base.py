"""
Base Database Model
基本データベースモデル

設計書参照:
- データベース実装設計書_202501.md

SQLAlchemy 2.0 に基づいた基本モデルクラス
全てのデータベースモデルはこのクラスを継承する
"""

from datetime import datetime
from typing import Any, Dict

import pytz
from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 基本クラス"""

    pass


def get_jst_now() -> datetime:
    """日本時間の現在時刻を取得"""
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).replace(tzinfo=None)


class BaseModel(Base):
    """
    全モデルの基底クラス

    責任:
    - 共通フィールドの定義
    - メタデータ管理
    - 基本的なシリアライゼーション
    """

    __abstract__ = True

    # 基本フィールド
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主キー")
    uuid = Column(String(36), nullable=True, unique=True, comment="UUID")
    created_at = Column(
        DateTime(timezone=True), nullable=False, default=get_jst_now, comment="作成日時"
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=get_jst_now,
        onupdate=get_jst_now,
        comment="更新日時",
    )
    version = Column(
        Integer, nullable=False, default=1, comment="バージョン（楽観的ロック用）"
    )

    @declared_attr
    def __tablename__(cls) -> str:
        """
        テーブル名を自動生成
        クラス名をスネークケースに変換
        """
        import re

        name = re.sub("(?!^)([A-Z][a-z]+)", r"_\1", cls.__name__)
        return name.lower()

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換
        シリアライゼーション用

        Returns:
            Dict[str, Any]: モデルの辞書表現
        """
        return {
            "id": self.id,
            "uuid": self.uuid,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
        }

    def update_version(self) -> None:
        """
        バージョン更新
        楽観的ロック用のバージョン管理
        """
        self.version += 1
        self.updated_at = get_jst_now()

    def __repr__(self) -> str:
        """
        文字列表現

        Returns:
            str: モデルの文字列表現
        """
        return f"{self.__class__.__name__}(id={self.id})"
