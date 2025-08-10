"""
API Call History Domain Entity
API呼び出し履歴ドメインエンティティ

設計書参照:
- api_optimization_design_2025.md

API呼び出し履歴用ドメインエンティティ
"""

from datetime import datetime
from typing import Dict, Optional

from ...utils.logging_config import get_domain_logger
from .base import BaseEntity

logger = get_domain_logger()


class ApiCallHistory(BaseEntity):
    """
    API呼び出し履歴エンティティ

    責任:
    - API呼び出し履歴の管理
    - レート制限監視
    - パフォーマンス測定
    - エラー追跡

    特徴:
    - 不変性: 一度作成された履歴は変更不可
    - 時系列: 呼び出し時刻による時系列管理
    - 統計: パフォーマンス統計の提供
    """

    def __init__(
        self,
        api_name: str,
        endpoint: str,
        success: bool,
        called_at: datetime,
        currency_pair: Optional[str] = None,
        response_time_ms: Optional[int] = None,
        status_code: Optional[int] = None,
        error_message: Optional[str] = None,
        id: Optional[int] = None,
        uuid: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: int = 1,
    ):
        """
        初期化

        Args:
            api_name: API名
            endpoint: エンドポイント
            success: 成功/失敗フラグ
            called_at: 呼び出し時刻
            currency_pair: 通貨ペア（オプション）
            response_time_ms: レスポンス時間（ミリ秒）
            status_code: HTTPステータスコード
            error_message: エラーメッセージ
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

        self.api_name = api_name
        self.endpoint = endpoint
        self.currency_pair = currency_pair
        self.response_time_ms = response_time_ms
        self.status_code = status_code
        self.success = success
        self.error_message = error_message
        self.called_at = called_at

        logger.debug(f"Created ApiCallHistory entity: {self.api_name}")

    def is_rate_limit_error(self) -> bool:
        """
        レート制限エラーかどうかを判定

        Returns:
            bool: レート制限エラーの場合True
        """
        return (
            self.status_code == 429
            or (self.error_message and "rate limit" in self.error_message.lower())
            or (
                self.error_message and "too many requests" in self.error_message.lower()
            )
        )

    def is_slow_response(self, threshold_ms: int = 5000) -> bool:
        """
        遅いレスポンスかどうかを判定

        Args:
            threshold_ms: 閾値（ミリ秒）

        Returns:
            bool: 遅いレスポンスの場合True
        """
        return (
            self.response_time_ms is not None and self.response_time_ms > threshold_ms
        )

    def get_performance_category(self) -> str:
        """
        パフォーマンスカテゴリを取得

        Returns:
            str: パフォーマンスカテゴリ（fast, normal, slow, error）
        """
        if not self.success:
            return "error"
        elif self.response_time_ms is None:
            return "unknown"
        elif self.response_time_ms < 1000:
            return "fast"
        elif self.response_time_ms < 5000:
            return "normal"
        else:
            return "slow"

    def get_call_summary(self) -> Dict[str, str]:
        """
        呼び出しサマリーを取得

        Returns:
            Dict[str, str]: 呼び出しサマリー
        """
        return {
            "api_name": self.api_name,
            "endpoint": self.endpoint,
            "currency_pair": self.currency_pair or "N/A",
            "success": str(self.success),
            "status_code": str(self.status_code) if self.status_code else "N/A",
            "response_time_ms": (
                str(self.response_time_ms) if self.response_time_ms else "N/A"
            ),
            "called_at": self.called_at.isoformat(),
            "performance_category": self.get_performance_category(),
            "is_rate_limit_error": str(self.is_rate_limit_error()),
        }

    def to_dict(self) -> Dict[str, str]:
        """
        辞書変換

        Returns:
            Dict[str, str]: エンティティの辞書表現
        """
        base_dict = super().to_dict()
        base_dict.update(
            {
                "api_name": self.api_name,
                "endpoint": self.endpoint,
                "currency_pair": self.currency_pair,
                "response_time_ms": (
                    str(self.response_time_ms) if self.response_time_ms else None
                ),
                "status_code": str(self.status_code) if self.status_code else None,
                "success": str(self.success),
                "error_message": self.error_message,
                "called_at": self.called_at.isoformat() if self.called_at else None,
            }
        )
        return base_dict

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "ApiCallHistory":
        """
        辞書からエンティティを復元

        Args:
            data: エンティティデータの辞書

        Returns:
            ApiCallHistory: 復元されたエンティティインスタンス
        """
        # 日時文字列をdatetimeオブジェクトに変換
        called_at = None
        if data.get("called_at"):
            called_at = datetime.fromisoformat(data["called_at"])

        # 数値フィールドの変換
        response_time_ms = None
        if data.get("response_time_ms"):
            try:
                response_time_ms = int(data["response_time_ms"])
            except (ValueError, TypeError):
                pass

        status_code = None
        if data.get("status_code"):
            try:
                status_code = int(data["status_code"])
            except (ValueError, TypeError):
                pass

        return cls(
            id=int(data["id"]) if data.get("id") else None,
            uuid=data.get("uuid"),
            api_name=data["api_name"],
            endpoint=data["endpoint"],
            currency_pair=data.get("currency_pair"),
            response_time_ms=response_time_ms,
            status_code=status_code,
            success=data.get("success", "True").lower() == "true",
            error_message=data.get("error_message"),
            called_at=called_at,
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
            version=int(data.get("version", 1)),
        )

    def __repr__(self) -> str:
        """
        文字列表現

        Returns:
            str: エンティティの文字列表現
        """
        return (
            f"ApiCallHistory("
            f"id={self.id}, "
            f"api_name='{self.api_name}', "
            f"endpoint='{self.endpoint}', "
            f"currency_pair='{self.currency_pair}', "
            f"success={self.success}, "
            f"status_code={self.status_code}, "
            f"response_time_ms={self.response_time_ms}"
            f")"
        )
