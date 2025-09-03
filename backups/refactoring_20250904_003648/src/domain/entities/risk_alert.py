"""
リスクアラートエンティティ

プロトレーダー向け為替アラートシステム用のリスクアラートエンティティ
設計書参照: /app/note/2025-01-15_アラートシステム_プロトレーダー向け為替アラートシステム設計書.md
"""

from datetime import datetime
from typing import Any, Dict, Optional


class RiskAlert:
    """
    リスクアラートエンティティ

    責任:
    - リスクアラートの表現
    - リスク情報の管理
    - 推奨アクションの保持

    特徴:
    - 不変オブジェクト
    - バリデーション機能
    - 重要度レベル管理
    """

    def __init__(
        self,
        alert_type: str,
        currency_pair: str,
        timestamp: datetime,
        timeframe: str,
        severity: str,
        message: str,
        recommended_action: str,
        market_data: Dict[str, Any],
        threshold_value: float,
        current_value: float,
    ):
        """
        初期化

        Args:
            alert_type: アラートタイプ
            currency_pair: 通貨ペア
            timestamp: タイムスタンプ
            timeframe: タイムフレーム
            severity: 重要度
            message: メッセージ
            recommended_action: 推奨アクション
            market_data: 市場データ
            threshold_value: 閾値
            current_value: 現在値
        """
        self.alert_type = alert_type
        self.currency_pair = currency_pair
        self.timestamp = timestamp
        self.timeframe = timeframe
        self.severity = severity
        self.message = message
        self.recommended_action = recommended_action
        self.market_data = market_data
        self.threshold_value = threshold_value
        self.current_value = current_value

        # バリデーション
        if not self.validate():
            raise ValueError("Invalid risk alert data")

    def __repr__(self) -> str:
        """文字列表現"""
        return (
            f"<RiskAlert("
            f"type='{self.alert_type}', "
            f"pair='{self.currency_pair}', "
            f"severity='{self.severity}', "
            f"value={self.current_value}"
            f")>"
        )

    def validate(self) -> bool:
        """
        データの妥当性を検証

        Returns:
            bool: 妥当性
        """
        # 基本チェック
        if not self.alert_type:
            return False

        if not self.currency_pair:
            return False

        if not self.timeframe:
            return False

        if self.severity not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            return False

        if not self.message:
            return False

        if not self.recommended_action:
            return False

        if not isinstance(self.market_data, dict):
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            Dict[str, Any]: 辞書形式のデータ
        """
        return {
            "alert_type": self.alert_type,
            "currency_pair": self.currency_pair,
            "timestamp": self.timestamp.isoformat(),
            "timeframe": self.timeframe,
            "severity": self.severity,
            "message": self.message,
            "recommended_action": self.recommended_action,
            "market_data": self.market_data,
            "threshold_value": self.threshold_value,
            "current_value": self.current_value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RiskAlert":
        """
        辞書からインスタンス作成

        Args:
            data: 辞書データ

        Returns:
            RiskAlert: インスタンス
        """
        return cls(
            alert_type=data["alert_type"],
            currency_pair=data["currency_pair"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            timeframe=data["timeframe"],
            severity=data["severity"],
            message=data["message"],
            recommended_action=data["recommended_action"],
            market_data=data["market_data"],
            threshold_value=data["threshold_value"],
            current_value=data["current_value"],
        )

    def is_critical(self) -> bool:
        """
        クリティカルかチェック

        Returns:
            bool: クリティカルかどうか
        """
        return self.severity == "CRITICAL"

    def is_high(self) -> bool:
        """
        高重要度かチェック

        Returns:
            bool: 高重要度かどうか
        """
        return self.severity in ["HIGH", "CRITICAL"]

    def is_medium(self) -> bool:
        """
        中重要度かチェック

        Returns:
            bool: 中重要度かどうか
        """
        return self.severity == "MEDIUM"

    def is_low(self) -> bool:
        """
        低重要度かチェック

        Returns:
            bool: 低重要度かどうか
        """
        return self.severity == "LOW"

    def get_severity_level(self) -> int:
        """
        重要度レベルを数値で取得

        Returns:
            int: 重要度レベル（1-4）
        """
        severity_map = {
            "LOW": 1,
            "MEDIUM": 2,
            "HIGH": 3,
            "CRITICAL": 4,
        }
        return severity_map.get(self.severity, 1)

    def get_market_data_value(self, key: str) -> Optional[Any]:
        """
        市場データから値を取得

        Args:
            key: キー

        Returns:
            Optional[Any]: 値
        """
        return self.market_data.get(key)

    def exceeds_threshold(self) -> bool:
        """
        閾値を超過しているかチェック

        Returns:
            bool: 閾値超過かどうか
        """
        return self.current_value > self.threshold_value

    def get_threshold_ratio(self) -> float:
        """
        閾値比率を取得

        Returns:
            float: 閾値比率
        """
        if self.threshold_value == 0:
            return 0.0
        return self.current_value / self.threshold_value
