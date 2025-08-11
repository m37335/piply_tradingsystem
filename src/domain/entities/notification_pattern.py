"""
通知パターンドメインエンティティ

マルチタイムフレーム戦略に基づく通知パターンを表すエンティティ
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..value_objects.pattern_priority import PatternPriority


@dataclass
class NotificationPattern:
    """通知パターンエンティティ"""

    # 基本情報
    pattern_number: int
    name: str
    description: str
    priority: PatternPriority

    # 検出条件
    conditions: Dict[str, List[str]]  # 時間軸 -> 条件リスト

    # 通知設定
    notification_title: str
    notification_color: str
    take_profit: Optional[str] = None
    stop_loss: Optional[str] = None
    strategy: Optional[str] = None
    risk: Optional[str] = None
    confidence: Optional[str] = None

    # メタデータ
    created_at: datetime = None
    last_detected: Optional[datetime] = None
    detection_count: int = 0

    def __post_init__(self):
        """初期化後の処理"""
        if self.created_at is None:
            self.created_at = datetime.now()

    @classmethod
    def create_pattern_1(cls) -> "NotificationPattern":
        """パターン1: 強力なトレンド転換シグナルを作成"""
        return cls(
            pattern_number=1,
            name="強力なトレンド転換シグナル",
            description="全時間軸一致による強力な売りシグナル",
            priority=PatternPriority.HIGH,
            conditions={
                "D1": ["RSI > 70", "MACD デッドクロス"],
                "H4": ["RSI > 70", "ボリンジャーバンド +2σ タッチ"],
                "H1": ["RSI > 70", "ボリンジャーバンド +2σ タッチ"],
                "M5": ["RSI > 70", "ヒゲ形成"],
            },
            notification_title="🚨 強力な売りシグナル検出！",
            notification_color="0xFF0000",
            take_profit="-50pips",
            stop_loss="+30pips",
        )

    @classmethod
    def create_pattern_2(cls) -> "NotificationPattern":
        """パターン2: 押し目買いチャンスを作成"""
        return cls(
            pattern_number=2,
            name="押し目買いチャンス",
            description="上位足トレンド継続中の押し目買い",
            priority=PatternPriority.MEDIUM,
            conditions={
                "D1": ["RSI 30-50", "MACD 上昇継続"],
                "H4": ["RSI 30-40", "ボリンジャーバンド -2σ タッチ"],
                "H1": ["RSI 30-35", "ボリンジャーバンド -2σ タッチ"],
                "M5": ["RSI 30以下", "反発サイン"],
            },
            notification_title="📈 押し目買いチャンス！",
            notification_color="0x00FF00",
            take_profit="+80pips",
            stop_loss="-40pips",
            confidence="高（トレンド順張り）",
        )

    @classmethod
    def create_pattern_2_2(cls) -> "NotificationPattern":
        """パターン2-2: 戻り売りチャンスを作成"""
        return cls(
            pattern_number=2,
            name="戻り売りチャンス",
            description="上位足下降トレンド継続中の戻り売り",
            priority=PatternPriority.MEDIUM,
            conditions={
                "D1": ["RSI 50-70", "MACD 下降継続"],
                "H4": ["RSI 60-70", "ボリンジャーバンド +2σ タッチ"],
                "H1": ["RSI 65-70", "ボリンジャーバンド +2σ タッチ"],
                "M5": ["RSI 70以上", "反転サイン"],
            },
            notification_title="📉 戻り売りチャンス！",
            notification_color="0xFF6600",
            take_profit="-80pips",
            stop_loss="+40pips",
        )

    @classmethod
    def create_pattern_3(cls) -> "NotificationPattern":
        """パターン3: ダイバージェンス警戒を作成"""
        return cls(
            pattern_number=3,
            name="ダイバージェンス警戒",
            description="価格とRSIの逆行による警戒シグナル",
            priority=PatternPriority.MEDIUM,
            conditions={
                "D1": ["価格新高値", "RSI 前回高値未達"],
                "H4": ["価格上昇", "RSI 下降"],
                "H1": ["価格上昇", "RSI 下降"],
                "M5": ["価格上昇", "RSI 下降"],
            },
            notification_title="⚠️ ダイバージェンス警戒！",
            notification_color="0xFFFF00",
            strategy="利確推奨",
            risk="急落可能性",
        )

    @classmethod
    def create_pattern_4(cls) -> "NotificationPattern":
        """パターン4: ブレイクアウト狙いを作成"""
        return cls(
            pattern_number=4,
            name="ブレイクアウト狙い",
            description="ボリンジャーバンド突破による急騰狙い",
            priority=PatternPriority.MEDIUM,
            conditions={
                "D1": ["RSI 50-70", "MACD 上昇"],
                "H4": ["ボリンジャーバンド +2σ 突破"],
                "H1": ["ボリンジャーバンド +2σ 突破"],
                "M5": ["強い上昇モメンタム"],
            },
            notification_title="🚀 ブレイクアウト狙い！",
            notification_color="0x00FFFF",
            take_profit="+100pips",
            stop_loss="-50pips",
        )

    @classmethod
    def create_pattern_5(cls) -> "NotificationPattern":
        """パターン5: RSI50ライン攻防を作成"""
        return cls(
            pattern_number=5,
            name="RSI50ライン攻防",
            description="トレンド継続/転換の分岐点",
            priority=PatternPriority.LOW,
            conditions={
                "D1": ["RSI 45-55", "MACD ゼロライン付近"],
                "H4": ["RSI 45-55", "ボリンジャーバンド ミドル付近"],
                "H1": ["RSI 45-55", "価格変動増加"],
                "M5": ["RSI 50ライン 攻防"],
            },
            notification_title="🔄 RSI50ライン攻防！",
            notification_color="0x808080",
            strategy="様子見推奨",
        )

    @classmethod
    def create_pattern_6(cls) -> "NotificationPattern":
        """パターン6: 複合シグナル強化を作成"""
        return cls(
            pattern_number=6,
            name="複合シグナル強化",
            description="複数指標の一致による高信頼度シグナル",
            priority=PatternPriority.VERY_HIGH,
            conditions={
                "D1": ["RSI + MACD + 価格 3つ一致"],
                "H4": ["RSI + ボリンジャーバンド 2つ一致"],
                "H1": ["RSI + ボリンジャーバンド 2つ一致"],
                "M5": ["RSI + 価格形状 2つ一致"],
            },
            notification_title="💪 複合シグナル強化！",
            notification_color="0x800080",
            take_profit="+120pips",
            stop_loss="-60pips",
            confidence="最高（複合シグナル）",
        )

    @classmethod
    def create_pattern_7(cls) -> "NotificationPattern":
        """パターン7: つつみ足検出を作成"""
        return cls(
            pattern_number=7,
            name="つつみ足検出",
            description="前の足を完全に包み込むローソク足パターン",
            priority=PatternPriority.HIGH,
            conditions={
                "D1": ["陽のつつみ足", "陰のつつみ足"],
                "H4": ["陽のつつみ足", "陰のつつみ足"],
                "H1": ["陽のつつみ足", "陰のつつみ足"],
                "M5": ["陽のつつみ足", "陰のつつみ足"],
            },
            notification_title="🔄 つつみ足パターン検出",
            notification_color="0xFF6B6B",
            take_profit="+80pips",
            stop_loss="-40pips",
            confidence="高（85-90%）",
        )

    @classmethod
    def create_pattern_8(cls) -> "NotificationPattern":
        """パターン8: 赤三兵検出を作成"""
        return cls(
            pattern_number=8,
            name="赤三兵検出",
            description="3本連続陽線による強い上昇トレンド",
            priority=PatternPriority.HIGH,
            conditions={
                "D1": ["3本連続陽線", "終値高値更新"],
                "H4": ["3本連続陽線", "終値高値更新"],
                "H1": ["3本連続陽線", "終値高値更新"],
                "M5": ["3本連続陽線", "終値高値更新"],
            },
            notification_title="🔴 赤三兵パターン検出",
            notification_color="0x4ECDC4",
            take_profit="+100pips",
            stop_loss="-50pips",
            confidence="高（80-85%）",
        )

    @classmethod
    def create_pattern_9(cls) -> "NotificationPattern":
        """パターン9: 引け坊主検出を作成"""
        return cls(
            pattern_number=9,
            name="引け坊主検出",
            description="ヒゲのない強いローソク足パターン",
            priority=PatternPriority.MEDIUM,
            conditions={
                "D1": ["大陽線引け坊主", "大陰線引け坊主"],
                "H4": ["大陽線引け坊主", "大陰線引け坊主"],
                "H1": ["大陽線引け坊主", "大陰線引け坊主"],
                "M5": ["大陽線引け坊主", "大陰線引け坊主"],
            },
            notification_title="⚡ 引け坊主パターン検出",
            notification_color="0x45B7D1",
            take_profit="+60pips",
            stop_loss="-30pips",
            confidence="中（75-80%）",
        )

    def increment_detection_count(self) -> None:
        """検出回数を増加"""
        self.detection_count += 1
        self.last_detected = datetime.now()

    def get_notification_delay(self) -> int:
        """通知遅延時間を取得"""
        return self.priority.get_notification_delay()

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "pattern_number": self.pattern_number,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "conditions": self.conditions,
            "notification_title": self.notification_title,
            "notification_color": self.notification_color,
            "take_profit": self.take_profit,
            "stop_loss": self.stop_loss,
            "strategy": self.strategy,
            "risk": self.risk,
            "confidence": self.confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_detected": (
                self.last_detected.isoformat() if self.last_detected else None
            ),
            "detection_count": self.detection_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NotificationPattern":
        """辞書から作成"""
        return cls(
            pattern_number=data["pattern_number"],
            name=data["name"],
            description=data["description"],
            priority=PatternPriority(data["priority"]),
            conditions=data["conditions"],
            notification_title=data["notification_title"],
            notification_color=data["notification_color"],
            take_profit=data.get("take_profit"),
            stop_loss=data.get("stop_loss"),
            strategy=data.get("strategy"),
            risk=data.get("risk"),
            confidence=data.get("confidence"),
            created_at=(
                datetime.fromisoformat(data["created_at"])
                if data.get("created_at")
                else None
            ),
            last_detected=(
                datetime.fromisoformat(data["last_detected"])
                if data.get("last_detected")
                else None
            ),
            detection_count=data.get("detection_count", 0),
        )
