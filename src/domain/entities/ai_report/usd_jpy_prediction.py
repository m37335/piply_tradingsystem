"""
ドル円予測データエンティティ
ChatGPTによるドル円予測結果を表現するドメインエンティティ
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from src.domain.entities.base import BaseEntity


class PredictionDirection(Enum):
    """予測方向の列挙型"""
    STRONG_BUY = "strong_buy"      # 強力な買い
    BUY = "buy"                    # 買い
    NEUTRAL = "neutral"            # 中立
    SELL = "sell"                  # 売り
    STRONG_SELL = "strong_sell"    # 強力な売り


class PredictionStrength(Enum):
    """予測強度の列挙型"""
    VERY_WEAK = "very_weak"        # 非常に弱い
    WEAK = "weak"                  # 弱い
    MODERATE = "moderate"          # 中程度
    STRONG = "strong"              # 強い
    VERY_STRONG = "very_strong"    # 非常に強い


@dataclass
class USDJPYPrediction(BaseEntity):
    """
    ドル円予測データエンティティ
    
    ChatGPTによるドル円予測結果を構造化して保持
    """
    
    # 基本予測情報
    direction: PredictionDirection = PredictionDirection.NEUTRAL
    strength: PredictionStrength = PredictionStrength.MODERATE
    
    # 数値予測
    target_price: Optional[Decimal] = None
    price_range_low: Optional[Decimal] = None
    price_range_high: Optional[Decimal] = None
    
    # 時間枠
    timeframe: str = "1-4 hours"
    
    # 信頼度
    confidence_score: Decimal = field(default_factory=lambda: Decimal("0.5"))
    
    # 分析根拠
    fundamental_reasons: List[str] = field(default_factory=list)
    technical_reasons: List[str] = field(default_factory=list)
    risk_factors: List[str] = field(default_factory=list)
    
    # メタデータ
    generated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """初期化後の処理"""
        if isinstance(self.direction, str):
            self.direction = PredictionDirection(self.direction)
        
        if isinstance(self.strength, str):
            self.strength = PredictionStrength(self.strength)
        
        # 数値の変換
        if isinstance(self.target_price, (int, float)):
            self.target_price = Decimal(str(self.target_price))
        if isinstance(self.price_range_low, (int, float)):
            self.price_range_low = Decimal(str(self.price_range_low))
        if isinstance(self.price_range_high, (int, float)):
            self.price_range_high = Decimal(str(self.price_range_high))
        if isinstance(self.confidence_score, (int, float)):
            self.confidence_score = Decimal(str(self.confidence_score))
    
    @property
    def is_bullish(self) -> bool:
        """買い方向かどうか"""
        return self.direction in [PredictionDirection.BUY, PredictionDirection.STRONG_BUY]
    
    @property
    def is_bearish(self) -> bool:
        """売り方向かどうか"""
        return self.direction in [PredictionDirection.SELL, PredictionDirection.STRONG_SELL]
    
    @property
    def is_neutral(self) -> bool:
        """中立かどうか"""
        return self.direction == PredictionDirection.NEUTRAL
    
    @property
    def is_strong_signal(self) -> bool:
        """強いシグナルかどうか"""
        return self.strength in [PredictionStrength.STRONG, PredictionStrength.VERY_STRONG]
    
    @property
    def is_weak_signal(self) -> bool:
        """弱いシグナルかどうか"""
        return self.strength in [PredictionStrength.WEAK, PredictionStrength.VERY_WEAK]
    
    @property
    def has_price_target(self) -> bool:
        """価格目標があるかどうか"""
        return self.target_price is not None
    
    @property
    def has_price_range(self) -> bool:
        """価格範囲があるかどうか"""
        return (self.price_range_low is not None and
                self.price_range_high is not None)
    
    @property
    def is_high_confidence(self) -> bool:
        """高信頼度かどうか"""
        return self.confidence_score >= Decimal("0.7")
    
    @property
    def is_low_confidence(self) -> bool:
        """低信頼度かどうか"""
        return self.confidence_score < Decimal("0.3")
    
    @property
    def direction_score(self) -> float:
        """方向性スコア（-1.0 から 1.0）"""
        direction_scores = {
            PredictionDirection.STRONG_SELL: -1.0,
            PredictionDirection.SELL: -0.5,
            PredictionDirection.NEUTRAL: 0.0,
            PredictionDirection.BUY: 0.5,
            PredictionDirection.STRONG_BUY: 1.0
        }
        return direction_scores.get(self.direction, 0.0)
    
    @property
    def strength_score(self) -> float:
        """強度スコア（0.0 から 1.0）"""
        strength_scores = {
            PredictionStrength.VERY_WEAK: 0.1,
            PredictionStrength.WEAK: 0.3,
            PredictionStrength.MODERATE: 0.5,
            PredictionStrength.STRONG: 0.7,
            PredictionStrength.VERY_STRONG: 0.9
        }
        return strength_scores.get(self.strength, 0.5)
    
    @property
    def composite_score(self) -> float:
        """総合スコア（-1.0 から 1.0）"""
        return self.direction_score * self.strength_score * float(self.confidence_score)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "id": self.id,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "target_price": float(self.target_price) if self.target_price else None,
            "price_range_low": float(self.price_range_low) if self.price_range_low else None,
            "price_range_high": float(self.price_range_high) if self.price_range_high else None,
            "timeframe": self.timeframe,
            "confidence_score": float(self.confidence_score),
            "fundamental_reasons": self.fundamental_reasons,
            "technical_reasons": self.technical_reasons,
            "risk_factors": self.risk_factors,
            "generated_at": self.generated_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "USDJPYPrediction":
        """辞書からインスタンスを作成"""
        # 日時の変換
        for date_field in ["generated_at", "created_at", "updated_at"]:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        return cls(**data)
    
    def add_fundamental_reason(self, reason: str) -> None:
        """ファンダメンタル理由を追加"""
        if reason and reason not in self.fundamental_reasons:
            self.fundamental_reasons.append(reason)
    
    def add_technical_reason(self, reason: str) -> None:
        """テクニカル理由を追加"""
        if reason and reason not in self.technical_reasons:
            self.technical_reasons.append(reason)
    
    def add_risk_factor(self, risk: str) -> None:
        """リスク要因を追加"""
        if risk and risk not in self.risk_factors:
            self.risk_factors.append(risk)
    
    def get_summary(self) -> str:
        """予測サマリーを取得"""
        direction_text = {
            PredictionDirection.STRONG_BUY: "強力な買い",
            PredictionDirection.BUY: "買い",
            PredictionDirection.NEUTRAL: "中立",
            PredictionDirection.SELL: "売り",
            PredictionDirection.STRONG_SELL: "強力な売り"
        }
        
        strength_text = {
            PredictionStrength.VERY_WEAK: "非常に弱い",
            PredictionStrength.WEAK: "弱い",
            PredictionStrength.MODERATE: "中程度",
            PredictionStrength.STRONG: "強い",
            PredictionStrength.VERY_STRONG: "非常に強い"
        }
        
        summary = f"ドル円: {direction_text[self.direction]} ({strength_text[self.strength]})"
        
        if self.has_price_target:
            summary += f" 目標: {self.target_price}"
        
        if self.has_price_range:
            summary += f" 範囲: {self.price_range_low}-{self.price_range_high}"
        
        summary += f" 信頼度: {float(self.confidence_score):.1%}"
        
        return summary
    
    def __str__(self) -> str:
        """文字列表現"""
        return f"USDJPYPrediction({self.direction.value}, {self.strength.value})"
    
    def __repr__(self) -> str:
        """詳細な文字列表現"""
        return (
            f"USDJPYPrediction("
            f"id={self.id}, "
            f"direction={self.direction.value}, "
            f"strength={self.strength.value}, "
            f"confidence={float(self.confidence_score):.1%}"
            f")"
        )
