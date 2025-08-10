"""
Analysis Cache Domain Entity
分析キャッシュドメインエンティティ

設計書参照:
- api_optimization_design_2025.md

分析結果のキャッシュ用ドメインエンティティ
"""

from datetime import datetime
from typing import Any, Dict, Optional

from ...utils.logging_config import get_domain_logger
from .base import BaseEntity

logger = get_domain_logger()


class AnalysisCache(BaseEntity):
    """
    分析キャッシュエンティティ

    責任:
    - 分析結果のキャッシュ管理
    - 有効期限の管理
    - キャッシュキーの生成
    - データの整合性保証

    特徴:
    - 不変性: 一度作成されたキャッシュは変更不可
    - 有効期限: 自動的な期限切れ管理
    - 一意性: キャッシュキーによる一意性保証
    """

    def __init__(
        self,
        analysis_type: str,
        currency_pair: str,
        analysis_data: Dict[str, Any],
        cache_key: str,
        expires_at: datetime,
        timeframe: Optional[str] = None,
        id: Optional[int] = None,
        uuid: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: int = 1,
    ):
        """
        初期化

        Args:
            analysis_type: 分析タイプ
            currency_pair: 通貨ペア
            analysis_data: 分析結果データ
            cache_key: キャッシュキー
            expires_at: 有効期限
            timeframe: 時間軸（オプション）
            id: データベースID
            uuid: UUID
            created_at: 作成時刻
            updated_at: 更新時刻
            version: バージョン
        """
        super().__init__(
            id=id,
            uuid=uuid,
            created_at=created_at,
            updated_at=updated_at,
            version=version,
        )

        self.analysis_type = analysis_type
        self.currency_pair = currency_pair
        self.timeframe = timeframe
        self.analysis_data = analysis_data
        self.cache_key = cache_key
        self.expires_at = expires_at

        logger.debug(f"Created AnalysisCache entity: {self.cache_key}")

    def is_expired(self) -> bool:
        """
        有効期限切れかどうかを判定

        Returns:
            bool: 有効期限切れの場合True
        """
        return datetime.utcnow() > self.expires_at

    def get_remaining_ttl_seconds(self) -> int:
        """
        残り有効期限（秒）を取得

        Returns:
            int: 残り有効期限（秒）、期限切れの場合は0
        """
        if self.is_expired():
            return 0

        remaining = self.expires_at - datetime.utcnow()
        return max(0, int(remaining.total_seconds()))

    def get_cache_key_components(self) -> Dict[str, str]:
        """
        キャッシュキーの構成要素を取得

        Returns:
            Dict[str, str]: キャッシュキー構成要素
        """
        return {
            "analysis_type": self.analysis_type,
            "currency_pair": self.currency_pair,
            "timeframe": self.timeframe or "",
        }

    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        分析サマリーを取得

        Returns:
            Dict[str, Any]: 分析サマリー
        """
        return {
            "analysis_type": self.analysis_type,
            "currency_pair": self.currency_pair,
            "timeframe": self.timeframe,
            "cache_key": self.cache_key,
            "expires_at": self.expires_at.isoformat(),
            "is_expired": self.is_expired(),
            "remaining_ttl_seconds": self.get_remaining_ttl_seconds(),
            "data_keys": list(self.analysis_data.keys()) if self.analysis_data else [],
        }

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書変換

        Returns:
            Dict[str, Any]: エンティティの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "analysis_type": self.analysis_type,
                "currency_pair": self.currency_pair,
                "timeframe": self.timeframe,
                "analysis_data": self.analysis_data,
                "cache_key": self.cache_key,
                "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisCache":
        """
        辞書からエンティティを復元

        Args:
            data: エンティティデータの辞書

        Returns:
            AnalysisCache: 復元されたエンティティインスタンス
        """
        # 日時文字列をdatetimeオブジェクトに変換
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"])

        return cls(
            id=data.get("id"),
            uuid=data.get("uuid"),
            analysis_type=data["analysis_type"],
            currency_pair=data["currency_pair"],
            timeframe=data.get("timeframe"),
            analysis_data=data["analysis_data"],
            cache_key=data["cache_key"],
            expires_at=expires_at,
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updated_at"])
                if data.get("updated_at")
                else None
            ),
            version=data.get("version", 1),
        )

    def to_model(self):
        """
        データベースモデルに変換

        Returns:
            AnalysisCacheModel: データベースモデル
        """
        from ...infrastructure.database.models.analysis_cache_model import (
            AnalysisCacheModel,
        )

        return AnalysisCacheModel(
            id=self.id,
            uuid=self.uuid,
            analysis_type=self.analysis_type,
            currency_pair=self.currency_pair,
            timeframe=self.timeframe,
            analysis_data=self.analysis_data,
            cache_key=self.cache_key,
            expires_at=self.expires_at,
            created_at=self.created_at,
            updated_at=self.updated_at,
            version=self.version,
        )

    @classmethod
    def from_model(cls, model):
        """
        データベースモデルからエンティティを作成

        Args:
            model: AnalysisCacheModel

        Returns:
            AnalysisCache: エンティティ
        """
        return cls(
            id=model.id,
            uuid=model.uuid,
            analysis_type=model.analysis_type,
            currency_pair=model.currency_pair,
            timeframe=model.timeframe,
            analysis_data=model.analysis_data,
            cache_key=model.cache_key,
            expires_at=model.expires_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            version=model.version,
        )

    def __repr__(self) -> str:
        """
        文字列表現

        Returns:
            str: エンティティの文字列表現
        """
        return (
            f"AnalysisCache("
            f"id={self.id}, "
            f"analysis_type='{self.analysis_type}', "
            f"currency_pair='{self.currency_pair}', "
            f"timeframe='{self.timeframe}', "
            f"expires_at='{self.expires_at}', "
            f"cache_key='{self.cache_key[:20]}...'"
            f")"
        )
