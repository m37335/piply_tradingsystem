"""
AIレポートエンティティ
ChatGPTによる経済イベント分析レポートを表現するドメインエンティティ
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from src.domain.entities.base import BaseEntity
from .usd_jpy_prediction import USDJPYPrediction


class ReportType(Enum):
    """レポートタイプの列挙型"""
    PRE_EVENT = "pre_event"           # イベント前
    POST_EVENT = "post_event"         # イベント後
    FORECAST_CHANGE = "forecast_change"  # 予測値変更


@dataclass
class AIReport(BaseEntity):
    """
    AIレポートエンティティ
    
    ChatGPTによる経済イベント分析レポートを表現
    ドル円予測データを含む
    """
    
    # 基本情報
    event_id: Optional[int] = None  # EconomicEventのID
    report_type: ReportType = ReportType.PRE_EVENT
    
    # レポート内容
    report_content: str = ""
    summary: str = ""
    
    # ドル円予測
    usd_jpy_prediction: Optional[USDJPYPrediction] = None
    
    # 信頼度
    confidence_score: Decimal = field(default_factory=lambda: Decimal("0.5"))
    
    # メタデータ
    generated_at: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """初期化後の処理"""
        if isinstance(self.report_type, str):
            self.report_type = ReportType(self.report_type)
        
        if isinstance(self.confidence_score, (int, float)):
            self.confidence_score = Decimal(str(self.confidence_score))
    
    @property
    def is_pre_event(self) -> bool:
        """イベント前レポートかどうか"""
        return self.report_type == ReportType.PRE_EVENT
    
    @property
    def is_post_event(self) -> bool:
        """イベント後レポートかどうか"""
        return self.report_type == ReportType.POST_EVENT
    
    @property
    def is_forecast_change(self) -> bool:
        """予測値変更レポートかどうか"""
        return self.report_type == ReportType.FORECAST_CHANGE
    
    @property
    def has_prediction(self) -> bool:
        """ドル円予測があるかどうか"""
        return self.usd_jpy_prediction is not None
    
    @property
    def is_high_confidence(self) -> bool:
        """高信頼度かどうか"""
        return self.confidence_score >= Decimal("0.7")
    
    @property
    def is_low_confidence(self) -> bool:
        """低信頼度かどうか"""
        return self.confidence_score < Decimal("0.3")
    
    @property
    def prediction_summary(self) -> str:
        """予測サマリーを取得"""
        if self.has_prediction:
            return self.usd_jpy_prediction.get_summary()
        return "予測データなし"
    
    def set_prediction(self, prediction: USDJPYPrediction) -> None:
        """ドル円予測を設定"""
        self.usd_jpy_prediction = prediction
        # 予測の信頼度をレポートの信頼度に反映
        if prediction.is_high_confidence:
            self.confidence_score = prediction.confidence_score
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        data = {
            "id": self.id,
            "event_id": self.event_id,
            "report_type": self.report_type.value,
            "report_content": self.report_content,
            "summary": self.summary,
            "confidence_score": float(self.confidence_score),
            "generated_at": self.generated_at.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if self.has_prediction:
            data["usd_jpy_prediction"] = self.usd_jpy_prediction.to_dict()
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIReport":
        """辞書からインスタンスを作成"""
        # 日時の変換
        for date_field in ["generated_at", "created_at", "updated_at"]:
            if date_field in data and isinstance(data[date_field], str):
                data[date_field] = datetime.fromisoformat(data[date_field])
        
        # USDJPYPredictionの変換
        if "usd_jpy_prediction" in data and data["usd_jpy_prediction"]:
            data["usd_jpy_prediction"] = USDJPYPrediction.from_dict(
                data["usd_jpy_prediction"]
            )
        
        return cls(**data)
    
    def __str__(self) -> str:
        """文字列表現"""
        confidence_pct = float(self.confidence_score) * 100
        return f"AIReport({self.report_type.value}, confidence={confidence_pct:.1f}%)"
    
    def __repr__(self) -> str:
        """詳細な文字列表現"""
        return (
            f"AIReport("
            f"id={self.id}, "
            f"event_id={self.event_id}, "
            f"report_type={self.report_type.value}, "
            f"confidence={float(self.confidence_score):.1%}"
            f")"
        )
