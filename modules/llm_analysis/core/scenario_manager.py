"""
シナリオ管理システム

ルールベース判定エンジンで生成されたエントリーシグナルを
シナリオとして管理し、ライフサイクルを追跡する。
"""

import logging
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .rule_engine import EntrySignal, TradeDirection


class ScenarioStatus(Enum):
    """シナリオステータス"""
    PLANNED = "planned"      # 計画段階
    ARMED = "armed"          # 監視中
    TRIGGERED = "triggered"  # 条件成立
    ENTERED = "entered"      # 約定済み
    EXITED = "exited"        # 決済済み
    CANCELED = "canceled"    # キャンセル
    EXPIRED = "expired"      # 期限切れ


class ExitReason(Enum):
    """エグジット理由"""
    TP1_HIT = "tp1_hit"           # テイクプロフィット1達成
    TP2_HIT = "tp2_hit"           # テイクプロフィット2達成
    TP3_HIT = "tp3_hit"           # テイクプロフィット3達成
    STOP_LOSS = "stop_loss"       # ストップロス
    TIME_EXIT = "time_exit"       # 時間切れ
    MANUAL_EXIT = "manual_exit"   # 手動決済
    CANCELED = "canceled"         # キャンセル
    EXPIRED = "expired"           # 期限切れ


@dataclass
class Scenario:
    """シナリオ"""
    id: str
    strategy: str
    direction: TradeDirection
    status: ScenarioStatus
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    risk_parameters: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    triggered_at: Optional[datetime] = None
    entered_at: Optional[datetime] = None
    exited_at: Optional[datetime] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    profit_loss: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    hold_time_minutes: Optional[int] = None
    trades: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.trades is None:
            self.trades = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Trade:
    """トレード"""
    id: str
    scenario_id: str
    direction: TradeDirection
    entry_price: float
    exit_price: Optional[float] = None
    position_size: float = 1.0
    stop_loss: Optional[float] = None
    take_profit_1: Optional[float] = None
    take_profit_2: Optional[float] = None
    take_profit_3: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[ExitReason] = None
    profit_loss: Optional[float] = None
    profit_loss_pips: Optional[float] = None
    hold_time_minutes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ScenarioManager:
    """シナリオ管理システム"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.scenarios: Dict[str, Scenario] = {}
        self.trades: Dict[str, Trade] = {}
        self._lock = None  # 非同期コンテキストで初期化
        self._initialized = False

    async def initialize(self):
        """非同期初期化"""
        if not self._initialized:
            self._lock = asyncio.Lock()
            self._initialized = True
            self.logger.info("✅ シナリオ管理システム初期化完了")

    async def create_scenario(
        self,
        entry_signal: EntrySignal,
        symbol: str = 'USDJPY=X',
        expires_hours: int = 8
    ) -> Scenario:
        """
        シナリオの作成
        
        Args:
            entry_signal: エントリーシグナル
            symbol: 通貨ペアシンボル
            expires_hours: 有効期限（時間）
        
        Returns:
            作成されたシナリオ
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            scenario_id = f"scenario_{uuid.uuid4().hex[:8]}"
            
            # 有効期限の計算
            expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
            
            # エントリー条件の構築
            entry_conditions = {
                "price": entry_signal.entry_price,
                "direction": entry_signal.direction.value,
                "confidence": entry_signal.confidence,
                "rule_results": [asdict(result) for result in entry_signal.rule_results]
            }
            
            # エグジット条件の構築
            exit_conditions = {
                "stop_loss": entry_signal.stop_loss,
                "take_profit_1": entry_signal.take_profit_1,
                "take_profit_2": entry_signal.take_profit_2,
                "take_profit_3": entry_signal.take_profit_3,
                "max_hold_time": entry_signal.max_hold_time
            }
            
            # リスクパラメータの構築
            risk_parameters = {
                "risk_reward_ratio": entry_signal.risk_reward_ratio,
                "position_size": 1.0,  # デフォルト
                "max_risk_percent": 1.0  # デフォルト
            }
            
            # シナリオの作成
            scenario = Scenario(
                id=scenario_id,
                strategy=entry_signal.strategy,
                direction=entry_signal.direction,
                status=ScenarioStatus.PLANNED,
                entry_conditions=entry_conditions,
                exit_conditions=exit_conditions,
                risk_parameters=risk_parameters,
                created_at=datetime.now(timezone.utc),
                expires_at=expires_at,
                metadata={
                    "symbol": symbol,
                    "technical_summary": entry_signal.technical_summary,
                    "created_by": "rule_engine"
                }
            )
            
            self.scenarios[scenario_id] = scenario
            
            self.logger.info(f"✅ シナリオ作成: {scenario_id} ({scenario.strategy})")
            return scenario

    async def arm_scenario(self, scenario_id: str) -> bool:
        """
        シナリオをアーム状態にする（監視開始）
        
        Args:
            scenario_id: シナリオID
        
        Returns:
            成功した場合True
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if scenario_id not in self.scenarios:
                self.logger.error(f"❌ シナリオが見つかりません: {scenario_id}")
                return False
            
            scenario = self.scenarios[scenario_id]
            
            if scenario.status != ScenarioStatus.PLANNED:
                self.logger.error(f"❌ シナリオがPLANNED状態ではありません: {scenario_id} ({scenario.status.value})")
                return False
            
            # 期限チェック
            if datetime.now(timezone.utc) > scenario.expires_at:
                scenario.status = ScenarioStatus.EXPIRED
                self.logger.warning(f"⚠️ シナリオが期限切れ: {scenario_id}")
                return False
            
            scenario.status = ScenarioStatus.ARMED
            self.logger.info(f"🔍 シナリオアーム: {scenario_id}")
            return True

    async def trigger_scenario(self, scenario_id: str, current_price: float) -> bool:
        """
        シナリオをトリガー状態にする（条件成立）
        
        Args:
            scenario_id: シナリオID
            current_price: 現在価格
        
        Returns:
            成功した場合True
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if scenario_id not in self.scenarios:
                self.logger.error(f"❌ シナリオが見つかりません: {scenario_id}")
                return False
            
            scenario = self.scenarios[scenario_id]
            
            if scenario.status != ScenarioStatus.ARMED:
                self.logger.error(f"❌ シナリオがARMED状態ではありません: {scenario_id} ({scenario.status.value})")
                return False
            
            # 期限チェック
            if datetime.now(timezone.utc) > scenario.expires_at:
                scenario.status = ScenarioStatus.EXPIRED
                self.logger.warning(f"⚠️ シナリオが期限切れ: {scenario_id}")
                return False
            
            scenario.status = ScenarioStatus.TRIGGERED
            scenario.triggered_at = datetime.now(timezone.utc)
            scenario.entry_price = current_price
            
            self.logger.info(f"🎯 シナリオトリガー: {scenario_id} @ {current_price}")
            return True

    async def enter_scenario(self, scenario_id: str, actual_entry_price: float) -> Optional[Trade]:
        """
        シナリオをエントリー状態にする（約定）
        
        Args:
            scenario_id: シナリオID
            actual_entry_price: 実際のエントリー価格
        
        Returns:
            作成されたトレード
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if scenario_id not in self.scenarios:
                self.logger.error(f"❌ シナリオが見つかりません: {scenario_id}")
                return None
            
            scenario = self.scenarios[scenario_id]
            
            if scenario.status != ScenarioStatus.TRIGGERED:
                self.logger.error(f"❌ シナリオがTRIGGERED状態ではありません: {scenario_id} ({scenario.status.value})")
                return None
            
            scenario.status = ScenarioStatus.ENTERED
            scenario.entered_at = datetime.now(timezone.utc)
            scenario.entry_price = actual_entry_price
            
            # トレードの作成
            trade_id = f"trade_{uuid.uuid4().hex[:8]}"
            trade = Trade(
                id=trade_id,
                scenario_id=scenario_id,
                direction=scenario.direction,
                entry_price=actual_entry_price,
                position_size=scenario.risk_parameters.get("position_size", 1.0),
                stop_loss=scenario.exit_conditions["stop_loss"],
                take_profit_1=scenario.exit_conditions["take_profit_1"],
                take_profit_2=scenario.exit_conditions["take_profit_2"],
                take_profit_3=scenario.exit_conditions["take_profit_3"],
                entry_time=scenario.entered_at,
                metadata={
                    "strategy": scenario.strategy,
                    "confidence": scenario.entry_conditions.get("confidence", 0.0)
                }
            )
            
            self.trades[trade_id] = trade
            if scenario.trades is not None:
                scenario.trades.append(trade_id)
            
            self.logger.info(f"📈 シナリオエントリー: {scenario_id} @ {actual_entry_price}")
            return trade

    async def exit_scenario(
        self,
        scenario_id: str,
        exit_price: float,
        exit_reason: ExitReason
    ) -> bool:
        """
        シナリオをエグジット状態にする（決済）
        
        Args:
            scenario_id: シナリオID
            exit_price: エグジット価格
            exit_reason: エグジット理由
        
        Returns:
            成功した場合True
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if scenario_id not in self.scenarios:
                self.logger.error(f"❌ シナリオが見つかりません: {scenario_id}")
                return False
            
            scenario = self.scenarios[scenario_id]
            
            if scenario.status != ScenarioStatus.ENTERED:
                self.logger.error(f"❌ シナリオがENTERED状態ではありません: {scenario_id} ({scenario.status.value})")
                return False
            
            scenario.status = ScenarioStatus.EXITED
            scenario.exited_at = datetime.now(timezone.utc)
            scenario.exit_price = exit_price
            scenario.exit_reason = exit_reason
            
            # 損益の計算
            if scenario.entry_price is not None:
                if scenario.direction == TradeDirection.BUY:
                    scenario.profit_loss = exit_price - scenario.entry_price
                else:
                    scenario.profit_loss = scenario.entry_price - exit_price
                
                # ピップス計算（USD/JPYの場合）
                scenario.profit_loss_pips = scenario.profit_loss * 10000
                
                # 保有時間の計算
                if scenario.entered_at:
                    hold_time = scenario.exited_at - scenario.entered_at
                    scenario.hold_time_minutes = int(hold_time.total_seconds() / 60)
            
            # 関連するトレードも更新
            if scenario.trades is not None:
                for trade_id in scenario.trades:
                    if trade_id in self.trades:
                        trade = self.trades[trade_id]
                        trade.exit_price = exit_price
                        trade.exit_time = scenario.exited_at
                        trade.exit_reason = exit_reason
                        trade.profit_loss = scenario.profit_loss
                        trade.profit_loss_pips = scenario.profit_loss_pips
                        trade.hold_time_minutes = scenario.hold_time_minutes
            
            self.logger.info(f"📉 シナリオエグジット: {scenario_id} @ {exit_price} ({exit_reason.value})")
            return True

    async def cancel_scenario(self, scenario_id: str, reason: str = "manual") -> bool:
        """
        シナリオをキャンセル
        
        Args:
            scenario_id: シナリオID
            reason: キャンセル理由
        
        Returns:
            成功した場合True
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if scenario_id not in self.scenarios:
                self.logger.error(f"❌ シナリオが見つかりません: {scenario_id}")
                return False
            
            scenario = self.scenarios[scenario_id]
            
            if scenario.status in [ScenarioStatus.EXITED, ScenarioStatus.CANCELED, ScenarioStatus.EXPIRED]:
                self.logger.error(f"❌ シナリオが既に終了状態です: {scenario_id} ({scenario.status.value})")
                return False
            
            scenario.status = ScenarioStatus.CANCELED
            if scenario.metadata is not None:
                scenario.metadata["cancel_reason"] = reason
            
            self.logger.info(f"❌ シナリオキャンセル: {scenario_id} ({reason})")
            return True

    async def get_active_scenarios(self) -> List[Scenario]:
        """
        アクティブなシナリオの取得
        
        Returns:
            アクティブなシナリオのリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            active_statuses = [
                ScenarioStatus.PLANNED,
                ScenarioStatus.ARMED,
                ScenarioStatus.TRIGGERED,
                ScenarioStatus.ENTERED
            ]
            
            active_scenarios = []
            for scenario in self.scenarios.values():
                if scenario.status in active_statuses:
                    # 期限チェック
                    if datetime.now(timezone.utc) > scenario.expires_at:
                        scenario.status = ScenarioStatus.EXPIRED
                        continue
                    active_scenarios.append(scenario)
            
            return active_scenarios

    async def get_scenario(self, scenario_id: str) -> Optional[Scenario]:
        """
        シナリオの取得
        
        Args:
            scenario_id: シナリオID
        
        Returns:
            シナリオ（見つからない場合はNone）
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            return self.scenarios.get(scenario_id)

    async def get_trade(self, trade_id: str) -> Optional[Trade]:
        """
        トレードの取得
        
        Args:
            trade_id: トレードID
        
        Returns:
            トレード（見つからない場合はNone）
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            return self.trades.get(trade_id)

    async def get_scenarios_by_status(self, status: ScenarioStatus) -> List[Scenario]:
        """
        ステータス別シナリオの取得
        
        Args:
            status: シナリオステータス
        
        Returns:
            該当するシナリオのリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            return [s for s in self.scenarios.values() if s.status == status]

    async def get_scenarios_by_strategy(self, strategy: str) -> List[Scenario]:
        """
        戦略別シナリオの取得
        
        Args:
            strategy: 戦略名
        
        Returns:
            該当するシナリオのリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            return [s for s in self.scenarios.values() if s.strategy == strategy]

    async def get_trade_history(
        self,
        days: int = 30,
        strategy: Optional[str] = None
    ) -> List[Trade]:
        """
        トレード履歴の取得
        
        Args:
            days: 取得日数
            strategy: 戦略名（フィルタ用）
        
        Returns:
            トレード履歴のリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            trades = []
            for trade in self.trades.values():
                if trade.entry_time and trade.entry_time >= cutoff_date:
                    if strategy is None or (trade.metadata is not None and trade.metadata.get("strategy") == strategy):
                        trades.append(trade)
            
            # エントリー時間でソート
            trades.sort(key=lambda t: t.entry_time or datetime.min.replace(tzinfo=timezone.utc))
            return trades

    async def get_performance_summary(
        self,
        days: int = 30,
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        パフォーマンスサマリーの取得
        
        Args:
            days: 取得日数
            strategy: 戦略名（フィルタ用）
        
        Returns:
            パフォーマンスサマリー
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            trades = await self.get_trade_history(days, strategy)
            
            if not trades:
                return {
                    "total_trades": 0,
                    "winning_trades": 0,
                    "losing_trades": 0,
                    "win_rate": 0.0,
                    "total_profit": 0.0,
                    "total_profit_pips": 0.0,
                    "average_profit": 0.0,
                    "average_profit_pips": 0.0,
                    "max_profit": 0.0,
                    "max_loss": 0.0,
                    "average_hold_time": 0.0
                }
            
            # 統計計算
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t.profit_loss and t.profit_loss > 0])
            losing_trades = len([t for t in trades if t.profit_loss and t.profit_loss < 0])
            win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0
            
            total_profit = sum(t.profit_loss or 0 for t in trades)
            total_profit_pips = sum(t.profit_loss_pips or 0 for t in trades)
            average_profit = total_profit / total_trades if total_trades > 0 else 0.0
            average_profit_pips = total_profit_pips / total_trades if total_trades > 0 else 0.0
            
            profits = [t.profit_loss for t in trades if t.profit_loss is not None]
            max_profit = max(profits) if profits else 0.0
            max_loss = min(profits) if profits else 0.0
            
            hold_times = [t.hold_time_minutes for t in trades if t.hold_time_minutes is not None]
            average_hold_time = sum(hold_times) / len(hold_times) if hold_times else 0.0
            
            return {
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "total_profit": total_profit,
                "total_profit_pips": total_profit_pips,
                "average_profit": average_profit,
                "average_profit_pips": average_profit_pips,
                "max_profit": max_profit,
                "max_loss": max_loss,
                "average_hold_time": average_hold_time,
                "strategy": strategy,
                "period_days": days
            }

    async def cleanup_expired_scenarios(self) -> int:
        """
        期限切れシナリオのクリーンアップ
        
        Returns:
            クリーンアップされたシナリオ数
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            now = datetime.now(timezone.utc)
            expired_count = 0
            
            for scenario in self.scenarios.values():
                if scenario.status in [ScenarioStatus.PLANNED, ScenarioStatus.ARMED, ScenarioStatus.TRIGGERED]:
                    if now > scenario.expires_at:
                        scenario.status = ScenarioStatus.EXPIRED
                        expired_count += 1
            
            if expired_count > 0:
                self.logger.info(f"🧹 期限切れシナリオクリーンアップ: {expired_count}件")
            
            return expired_count

    def to_dict(self) -> Dict[str, Any]:
        """シナリオマネージャーの状態を辞書に変換"""
        return {
            "scenarios": {sid: asdict(scenario) for sid, scenario in self.scenarios.items()},
            "trades": {tid: asdict(trade) for tid, trade in self.trades.items()},
            "total_scenarios": len(self.scenarios),
            "total_trades": len(self.trades)
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """辞書からシナリオマネージャーの状態を復元"""
        self.scenarios.clear()
        self.trades.clear()
        
        # シナリオの復元
        for sid, scenario_data in data.get("scenarios", {}).items():
            # 日時文字列をdatetimeオブジェクトに変換
            for date_field in ["created_at", "expires_at", "triggered_at", "entered_at", "exited_at"]:
                if scenario_data.get(date_field):
                    scenario_data[date_field] = datetime.fromisoformat(scenario_data[date_field].replace('Z', '+00:00'))
            
            # 列挙型の復元
            scenario_data["direction"] = TradeDirection(scenario_data["direction"])
            scenario_data["status"] = ScenarioStatus(scenario_data["status"])
            if scenario_data.get("exit_reason"):
                scenario_data["exit_reason"] = ExitReason(scenario_data["exit_reason"])
            
            scenario = Scenario(**scenario_data)
            self.scenarios[sid] = scenario
        
        # トレードの復元
        for tid, trade_data in data.get("trades", {}).items():
            # 日時文字列をdatetimeオブジェクトに変換
            for date_field in ["entry_time", "exit_time"]:
                if trade_data.get(date_field):
                    trade_data[date_field] = datetime.fromisoformat(trade_data[date_field].replace('Z', '+00:00'))
            
            # 列挙型の復元
            trade_data["direction"] = TradeDirection(trade_data["direction"])
            if trade_data.get("exit_reason"):
                trade_data["exit_reason"] = ExitReason(trade_data["exit_reason"])
            
            trade = Trade(**trade_data)
            self.trades[tid] = trade

    async def close(self):
        """リソースのクリーンアップ"""
        # 現在は特にリソースのクリーンアップは不要
        # 将来的にデータベース接続やファイルハンドルなどが追加された場合に対応
        self.logger.info("ScenarioManager closed")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from .rule_engine import RuleBasedEngine
    
    manager = ScenarioManager()
    engine = RuleBasedEngine()
    
    try:
        # エントリーシグナルの生成（テスト用）
        print("🧪 シナリオ管理システムテスト...")
        
        # ダミーのエントリーシグナルを作成
        from .rule_engine import RuleResult
        
        dummy_signal = EntrySignal(
            direction=TradeDirection.BUY,
            strategy="pullback_buy",
            confidence=0.85,
            entry_price=147.123,
            stop_loss=146.800,
            take_profit_1=147.400,
            take_profit_2=147.600,
            take_profit_3=147.800,
            risk_reward_ratio=2.5,
            max_hold_time=240,
            rule_results=[
                RuleResult("RSI_14 <= 40", True, 0.9, "RSI: 38.5 ≤ 40", {}),
                RuleResult("price > EMA_200", True, 0.8, "Price: 147.123 > EMA_200: 146.800", {})
            ],
            technical_summary={"1h": {"price": 147.123, "rsi_14": 38.5}},
            created_at=datetime.now(timezone.utc)
        )
        
        # シナリオの作成
        scenario = await manager.create_scenario(dummy_signal)
        print(f"✅ シナリオ作成: {scenario.id}")
        
        # シナリオのアーム
        success = await manager.arm_scenario(scenario.id)
        print(f"✅ シナリオアーム: {success}")
        
        # シナリオのトリガー
        success = await manager.trigger_scenario(scenario.id, 147.125)
        print(f"✅ シナリオトリガー: {success}")
        
        # シナリオのエントリー
        trade = await manager.enter_scenario(scenario.id, 147.125)
        print(f"✅ シナリオエントリー: {trade.id if trade else 'Failed'}")
        
        # シナリオのエグジット
        success = await manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
        print(f"✅ シナリオエグジット: {success}")
        
        # パフォーマンスサマリーの取得
        summary = await manager.get_performance_summary()
        print(f"✅ パフォーマンスサマリー: {summary}")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    asyncio.run(main())
