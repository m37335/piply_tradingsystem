"""
エントリーシグナルエンティティ

プロトレーダー向け為替アラートシステム用のエントリーシグナルエンティティ
設計書参照: /app/note/2025-01-15_アラートシステム_プロトレーダー向け為替アラートシステム設計書.md
"""

from datetime import datetime
from typing import Any, Dict, Optional


class EntrySignal:
    """
    エントリーシグナルエンティティ

    責任:
    - エントリーシグナルの表現
    - シグナル情報の管理
    - リスク管理情報の保持

    特徴:
    - 不変オブジェクト
    - バリデーション機能
    - リッチな情報保持
    """

    def __init__(
        self,
        signal_type: str,
        currency_pair: str,
        timestamp: datetime,
        timeframe: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        risk_reward_ratio: float,
        confidence_score: int,
        indicators_used: Dict[str, Any],
        risk_amount: Optional[float] = None,
        position_size: Optional[float] = None,
        market_conditions: Optional[Dict[str, Any]] = None,
        trend_strength: Optional[float] = None,
    ):
        """
        初期化

        Args:
            signal_type: シグナルタイプ（'BUY', 'SELL'）
            currency_pair: 通貨ペア
            timestamp: タイムスタンプ
            timeframe: タイムフレーム
            entry_price: エントリー価格
            stop_loss: ストップロス
            take_profit: 利益確定
            risk_reward_ratio: リスク/リワード比
            confidence_score: 信頼度スコア
            indicators_used: 使用した指標
            risk_amount: リスク額
            position_size: ポジションサイズ
            market_conditions: 市場状況
            trend_strength: トレンド強度
        """
        self.signal_type = signal_type
        self.currency_pair = currency_pair
        self.timestamp = timestamp
        self.timeframe = timeframe
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.risk_reward_ratio = risk_reward_ratio
        self.confidence_score = confidence_score
        self.indicators_used = indicators_used
        self.risk_amount = risk_amount
        self.position_size = position_size
        self.market_conditions = market_conditions or {}
        self.trend_strength = trend_strength

        # バリデーション
        if not self.validate():
            raise ValueError("Invalid entry signal data")

    def __repr__(self) -> str:
        """文字列表現"""
        return (
            f"<EntrySignal("
            f"type='{self.signal_type}', "
            f"pair='{self.currency_pair}', "
            f"price={self.entry_price}, "
            f"confidence={self.confidence_score}%"
            f")>"
        )

    def validate(self) -> bool:
        """
        データの妥当性を検証

        Returns:
            bool: 妥当性
        """
        # 基本チェック
        if self.signal_type not in ["BUY", "SELL"]:
            return False

        if not self.currency_pair:
            return False

        if not self.timeframe:
            return False

        if self.entry_price <= 0:
            return False

        if self.stop_loss <= 0:
            return False

        if self.take_profit <= 0:
            return False

        if self.risk_reward_ratio <= 0:
            return False

        if not (0 <= self.confidence_score <= 100):
            return False

        # 価格関係のチェック
        if self.signal_type == "BUY":
            if self.stop_loss >= self.entry_price:
                return False
            if self.take_profit <= self.entry_price:
                return False
        else:  # SELL
            if self.stop_loss <= self.entry_price:
                return False
            if self.take_profit >= self.entry_price:
                return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """
        辞書形式に変換

        Returns:
            Dict[str, Any]: 辞書形式のデータ
        """
        return {
            "signal_type": self.signal_type,
            "currency_pair": self.currency_pair,
            "timestamp": self.timestamp.isoformat(),
            "timeframe": self.timeframe,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "risk_reward_ratio": self.risk_reward_ratio,
            "confidence_score": self.confidence_score,
            "indicators_used": self.indicators_used,
            "risk_amount": self.risk_amount,
            "position_size": self.position_size,
            "market_conditions": self.market_conditions,
            "trend_strength": self.trend_strength,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntrySignal":
        """
        辞書からインスタンス作成

        Args:
            data: 辞書データ

        Returns:
            EntrySignal: インスタンス
        """
        return cls(
            signal_type=data["signal_type"],
            currency_pair=data["currency_pair"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            timeframe=data["timeframe"],
            entry_price=data["entry_price"],
            stop_loss=data["stop_loss"],
            take_profit=data["take_profit"],
            risk_reward_ratio=data["risk_reward_ratio"],
            confidence_score=data["confidence_score"],
            indicators_used=data["indicators_used"],
            risk_amount=data.get("risk_amount"),
            position_size=data.get("position_size"),
            market_conditions=data.get("market_conditions"),
            trend_strength=data.get("trend_strength"),
        )

    def calculate_risk_percentage(self) -> float:
        """
        リスク率を計算

        Returns:
            float: リスク率（%）
        """
        if self.signal_type == "BUY":
            risk = (self.entry_price - self.stop_loss) / self.entry_price
        else:  # SELL
            risk = (self.stop_loss - self.entry_price) / self.entry_price

        return risk * 100

    def calculate_profit_percentage(self) -> float:
        """
        利益率を計算

        Returns:
            float: 利益率（%）
        """
        if self.signal_type == "BUY":
            profit = (self.take_profit - self.entry_price) / self.entry_price
        else:  # SELL
            profit = (self.entry_price - self.take_profit) / self.entry_price

        return profit * 100

    def is_high_confidence(self) -> bool:
        """
        高信頼度かチェック

        Returns:
            bool: 高信頼度かどうか
        """
        return self.confidence_score >= 80

    def is_medium_confidence(self) -> bool:
        """
        中信頼度かチェック

        Returns:
            bool: 中信頼度かどうか
        """
        return 60 <= self.confidence_score < 80

    def is_low_confidence(self) -> bool:
        """
        低信頼度かチェック

        Returns:
            bool: 低信頼度かどうか
        """
        return self.confidence_score < 60

    def get_risk_level(self) -> str:
        """
        リスクレベルを取得

        Returns:
            str: リスクレベル
        """
        risk_percentage = self.calculate_risk_percentage()

        if risk_percentage <= 0.5:
            return "LOW"
        elif risk_percentage <= 1.0:
            return "MEDIUM"
        elif risk_percentage <= 2.0:
            return "HIGH"
        else:
            return "VERY_HIGH"

    def get_profit_potential(self) -> str:
        """
        利益ポテンシャルを取得

        Returns:
            str: 利益ポテンシャル
        """
        profit_percentage = self.calculate_profit_percentage()

        if profit_percentage >= 3.0:
            return "EXCELLENT"
        elif profit_percentage >= 2.0:
            return "GOOD"
        elif profit_percentage >= 1.0:
            return "MODERATE"
        else:
            return "LOW"
