"""
スナップ保存システム

エントリー・エグジット時点の相場環境を記録し、
後で分析・評価に使用するためのシステム。
"""

import logging
import uuid
import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

try:
    import pandas as pd
except ImportError:
    pd = None

from .data_preparator import LLMDataPreparator
from .scenario_manager import Scenario, Trade, ExitReason, TradeDirection


class SnapshotType(Enum):
    """スナップタイプ"""
    ENTRY = "entry"      # エントリー時
    EXIT = "exit"        # エグジット時
    TRIGGER = "trigger"  # トリガー時
    CANCEL = "cancel"    # キャンセル時


@dataclass
class MarketSnapshot:
    """市場スナップショット"""
    id: str
    snapshot_type: SnapshotType
    scenario_id: str
    trade_id: Optional[str]
    timestamp: datetime
    symbol: str
    
    # 価格データ
    price_data: Dict[str, Any]
    
    # テクニカル指標
    technical_indicators: Dict[str, Any]
    
    # フィボナッチレベル
    fibonacci_levels: Dict[str, Any]
    
    # セッション情報
    session_info: Dict[str, Any]
    
    # リスク指標
    risk_metrics: Dict[str, Any]
    
    # メタデータ
    metadata: Dict[str, Any]


@dataclass
class TradeSnapshot:
    """トレードスナップショット"""
    id: str
    trade_id: str
    scenario_id: str
    entry_snapshot_id: str
    exit_snapshot_id: Optional[str]
    
    # トレード情報
    direction: TradeDirection
    strategy: str
    entry_price: float
    exit_price: Optional[float]
    position_size: float
    
    # リスク管理
    stop_loss: Optional[float]
    take_profit_1: Optional[float]
    take_profit_2: Optional[float]
    take_profit_3: Optional[float]
    
    # タイミング
    entry_time: Optional[datetime]
    exit_time: Optional[datetime]
    hold_time_minutes: Optional[int]
    
    # 結果
    exit_reason: Optional[ExitReason]
    profit_loss: Optional[float]
    profit_loss_pips: Optional[float]
    
    # 評価
    adherence_score: Optional[float]
    violation_tags: List[str]
    
    # メタデータ
    metadata: Dict[str, Any]


class SnapshotManager:
    """スナップ保存システム"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.data_preparator = LLMDataPreparator()
        self.snapshots: Dict[str, MarketSnapshot] = {}
        self.trade_snapshots: Dict[str, TradeSnapshot] = {}
        self._lock = None
        self._initialized = False

    async def initialize(self):
        """非同期初期化"""
        if self._lock is None:
            self._lock = asyncio.Lock()
        self._initialized = True
        self.logger.info("✅ スナップ保存システム初期化完了")

    async def save_entry_snapshot(
        self,
        scenario: Scenario,
        trade: Trade,
        symbol: str = 'USDJPY=X'
    ) -> str:
        """
        エントリースナップの保存
        
        Args:
            scenario: シナリオ
            trade: トレード
            symbol: 通貨ペアシンボル
        
        Returns:
            スナップショットID
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            try:
                # 現在の市場データを取得
                market_data = await self._get_current_market_data(symbol)
                
                # スナップショットIDの生成
                snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
                
                # エントリースナップの作成
                snapshot = MarketSnapshot(
                    id=snapshot_id,
                    snapshot_type=SnapshotType.ENTRY,
                    scenario_id=scenario.id,
                    trade_id=trade.id,
                    timestamp=datetime.now(timezone.utc),
                    symbol=symbol,
                    price_data=market_data['price_data'],
                    technical_indicators=market_data['technical_indicators'],
                    fibonacci_levels=market_data['fibonacci_levels'],
                    session_info=market_data['session_info'],
                    risk_metrics=market_data['risk_metrics'],
                    metadata={
                        "strategy": scenario.strategy,
                        "confidence": scenario.entry_conditions.get("confidence", 0.0),
                        "rule_results": scenario.entry_conditions.get("rule_results", []),
                        "created_by": "snapshot_manager"
                    }
                )
                
                self.snapshots[snapshot_id] = snapshot
                
                # トレードスナップショットの作成
                trade_snapshot = TradeSnapshot(
                    id=f"trade_snapshot_{trade.id}",
                    trade_id=trade.id,
                    scenario_id=scenario.id,
                    entry_snapshot_id=snapshot_id,
                    exit_snapshot_id=None,
                    direction=trade.direction,
                    strategy=scenario.strategy,
                    entry_price=trade.entry_price,
                    exit_price=None,
                    position_size=trade.position_size,
                    stop_loss=trade.stop_loss,
                    take_profit_1=trade.take_profit_1,
                    take_profit_2=trade.take_profit_2,
                    take_profit_3=trade.take_profit_3,
                    entry_time=trade.entry_time,
                    exit_time=None,
                    hold_time_minutes=None,
                    exit_reason=None,
                    profit_loss=None,
                    profit_loss_pips=None,
                    adherence_score=None,
                    violation_tags=[],
                    metadata={
                        "entry_snapshot": asdict(snapshot),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                )
                
                self.trade_snapshots[trade.id] = trade_snapshot
                
                self.logger.info(f"✅ エントリースナップ保存: {snapshot_id} for trade {trade.id}")
                return snapshot_id
                
            except Exception as e:
                self.logger.error(f"❌ エントリースナップ保存エラー: {e}")
                raise

    async def save_exit_snapshot(
        self,
        trade: Trade,
        exit_reason: ExitReason,
        symbol: str = 'USDJPY=X'
    ) -> str:
        """
        エグジットスナップの保存
        
        Args:
            trade: トレード
            exit_reason: エグジット理由
            symbol: 通貨ペアシンボル
        
        Returns:
            スナップショットID
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            try:
                # 現在の市場データを取得
                market_data = await self._get_current_market_data(symbol)
                
                # スナップショットIDの生成
                snapshot_id = f"snapshot_{uuid.uuid4().hex[:8]}"
                
                # エグジットスナップの作成
                snapshot = MarketSnapshot(
                    id=snapshot_id,
                    snapshot_type=SnapshotType.EXIT,
                    scenario_id=trade.scenario_id,
                    trade_id=trade.id,
                    timestamp=datetime.now(timezone.utc),
                    symbol=symbol,
                    price_data=market_data['price_data'],
                    technical_indicators=market_data['technical_indicators'],
                    fibonacci_levels=market_data['fibonacci_levels'],
                    session_info=market_data['session_info'],
                    risk_metrics=market_data['risk_metrics'],
                    metadata={
                        "exit_reason": exit_reason.value,
                        "profit_loss": trade.profit_loss,
                        "profit_loss_pips": trade.profit_loss_pips,
                        "hold_time_minutes": trade.hold_time_minutes,
                        "created_by": "snapshot_manager"
                    }
                )
                
                self.snapshots[snapshot_id] = snapshot
                
                # トレードスナップショットの更新
                if trade.id in self.trade_snapshots:
                    trade_snapshot = self.trade_snapshots[trade.id]
                    trade_snapshot.exit_snapshot_id = snapshot_id
                    trade_snapshot.exit_price = trade.exit_price
                    trade_snapshot.exit_time = trade.exit_time
                    trade_snapshot.hold_time_minutes = trade.hold_time_minutes
                    trade_snapshot.exit_reason = exit_reason
                    trade_snapshot.profit_loss = trade.profit_loss
                    trade_snapshot.profit_loss_pips = trade.profit_loss_pips
                    trade_snapshot.metadata["exit_snapshot"] = asdict(snapshot)
                    trade_snapshot.metadata["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                self.logger.info(f"✅ エグジットスナップ保存: {snapshot_id} for trade {trade.id}")
                return snapshot_id
                
            except Exception as e:
                self.logger.error(f"❌ エグジットスナップ保存エラー: {e}")
                raise

    async def _get_current_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        現在の市場データを取得
        
        Args:
            symbol: 通貨ペアシンボル
        
        Returns:
            市場データ辞書
        """
        try:
            # 複数時間足のデータを取得
            data = await self.data_preparator.prepare_analysis_data(
                "trend_reinforcement", symbol
            )
            
            # 価格データの構築
            price_data = {}
            technical_indicators = {}
            fibonacci_levels = {}
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame) and not df.empty:
                    latest = df.iloc[-1]
                    
                    # 価格データ
                    price_data[timeframe] = {
                        "open": float(latest.get('open', 0)),
                        "high": float(latest.get('high', 0)),
                        "low": float(latest.get('low', 0)),
                        "close": float(latest.get('close', 0)),
                        "volume": int(latest.get('volume', 0)) if not pd.isna(latest.get('volume')) else 0
                    }
                    
                    # テクニカル指標
                    technical_indicators[timeframe] = {
                        "rsi_14": float(latest.get('RSI_14', 0)) if not pd.isna(latest.get('RSI_14')) else None,
                        "ema_21": float(latest.get('EMA_21', 0)) if not pd.isna(latest.get('EMA_21')) else None,
                        "ema_55": float(latest.get('EMA_55', 0)) if not pd.isna(latest.get('EMA_55')) else None,
                        "ema_200": float(latest.get('EMA_200', 0)) if not pd.isna(latest.get('EMA_200')) else None,
                        "macd": float(latest.get('MACD', 0)) if not pd.isna(latest.get('MACD')) else None,
                        "macd_signal": float(latest.get('MACD_Signal', 0)) if not pd.isna(latest.get('MACD_Signal')) else None,
                        "atr_14": float(latest.get('ATR_14', 0)) if not pd.isna(latest.get('ATR_14')) else None,
                        "volume_ratio": float(latest.get('Volume_Ratio', 0)) if not pd.isna(latest.get('Volume_Ratio')) else None
                    }
                    
                    # フィボナッチレベル
                    fib_levels = {}
                    for col in df.columns:
                        if col.startswith('Fib_'):
                            level = col.replace('Fib_', '')
                            value = latest.get(col)
                            if not pd.isna(value):
                                fib_levels[level] = float(value)
                    
                    fibonacci_levels[timeframe] = fib_levels
            
            # セッション情報
            session_info = self._get_session_info()
            
            # リスク指標
            risk_metrics = await self._get_risk_metrics()
            
            return {
                "price_data": price_data,
                "technical_indicators": technical_indicators,
                "fibonacci_levels": fibonacci_levels,
                "session_info": session_info,
                "risk_metrics": risk_metrics
            }
            
        except Exception as e:
            self.logger.error(f"❌ 市場データ取得エラー: {e}")
            return {
                "price_data": {},
                "technical_indicators": {},
                "fibonacci_levels": {},
                "session_info": {},
                "risk_metrics": {}
            }

    def _get_session_info(self) -> Dict[str, Any]:
        """セッション情報の取得"""
        try:
            # 現在時刻の取得（JST）
            now_jst = datetime.now(timezone(timedelta(hours=9)))
            current_time = now_jst.time()
            
            # アクティブセッションの判定
            active_sessions = []
            
            session_times = {
                "Tokyo": {"start": "09:00", "end": "15:00"},
                "London": {"start": "16:00", "end": "23:59"},
                "NewYork": {"start": "22:00", "end": "05:59"}
            }
            
            for session_name, times in session_times.items():
                start_time = datetime.strptime(times["start"], "%H:%M").time()
                end_time = datetime.strptime(times["end"], "%H:%M").time()
                
                if start_time <= end_time:
                    # 同日内のセッション
                    if start_time <= current_time <= end_time:
                        active_sessions.append(session_name)
                else:
                    # 日をまたぐセッション（ニューヨーク）
                    if current_time >= start_time or current_time <= end_time:
                        active_sessions.append(session_name)
            
            return {
                "active_sessions": active_sessions,
                "current_time_jst": current_time.isoformat(),
                "current_time_utc": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ セッション情報取得エラー: {e}")
            return {
                "active_sessions": [],
                "current_time_jst": None,
                "current_time_utc": datetime.now(timezone.utc).isoformat()
            }

    async def _get_risk_metrics(self) -> Dict[str, Any]:
        """リスク指標の取得"""
        try:
            # 簡易実装（実際はデータベースから取得）
            return {
                "daily_trades": 2,  # 仮の値
                "daily_risk_percent": 1.2,  # 仮の値
                "max_risk_per_trade": 1.0,
                "max_risk_per_day": 3.0,
                "max_trades_per_day": 5,
                "correlation_risk": 0.3  # 仮の値
            }
            
        except Exception as e:
            self.logger.error(f"❌ リスク指標取得エラー: {e}")
            return {}

    async def get_trade_history(self, days: int = 30) -> List[TradeSnapshot]:
        """
        トレード履歴の取得
        
        Args:
            days: 取得日数
        
        Returns:
            トレードスナップショットのリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            trade_snapshots = []
            for trade_snapshot in self.trade_snapshots.values():
                if trade_snapshot.entry_time and trade_snapshot.entry_time >= cutoff_date:
                    trade_snapshots.append(trade_snapshot)
            
            # エントリー時間でソート
            trade_snapshots.sort(key=lambda t: t.entry_time or datetime.min.replace(tzinfo=timezone.utc))
            return trade_snapshots

    async def get_snapshots_by_trade(self, trade_id: str) -> List[MarketSnapshot]:
        """
        トレード別スナップショットの取得
        
        Args:
            trade_id: トレードID
        
        Returns:
            スナップショットのリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            snapshots = []
            for snapshot in self.snapshots.values():
                if snapshot.trade_id == trade_id:
                    snapshots.append(snapshot)
            
            # タイムスタンプでソート
            snapshots.sort(key=lambda s: s.timestamp)
            return snapshots

    async def get_snapshots_by_scenario(self, scenario_id: str) -> List[MarketSnapshot]:
        """
        シナリオ別スナップショットの取得
        
        Args:
            scenario_id: シナリオID
        
        Returns:
            スナップショットのリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            snapshots = []
            for snapshot in self.snapshots.values():
                if snapshot.scenario_id == scenario_id:
                    snapshots.append(snapshot)
            
            # タイムスタンプでソート
            snapshots.sort(key=lambda s: s.timestamp)
            return snapshots

    async def get_performance_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        パフォーマンス分析の取得
        
        Args:
            days: 分析日数
        
        Returns:
            パフォーマンス分析結果
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            trade_snapshots = await self.get_trade_history(days)
            
            if not trade_snapshots:
                return {
                    "total_trades": 0,
                    "analysis": "No trades found"
                }
            
            # 基本統計
            total_trades = len(trade_snapshots)
            completed_trades = [t for t in trade_snapshots if t.exit_reason is not None]
            winning_trades = [t for t in completed_trades if t.profit_loss and t.profit_loss > 0]
            losing_trades = [t for t in completed_trades if t.profit_loss and t.profit_loss < 0]
            
            win_rate = (len(winning_trades) / len(completed_trades) * 100) if completed_trades else 0.0
            
            # 損益統計
            total_profit = sum(t.profit_loss or 0 for t in completed_trades)
            total_profit_pips = sum(t.profit_loss_pips or 0 for t in completed_trades)
            
            # 戦略別分析
            strategy_analysis = {}
            for trade_snapshot in completed_trades:
                strategy = trade_snapshot.strategy
                if strategy not in strategy_analysis:
                    strategy_analysis[strategy] = {
                        "trades": 0,
                        "wins": 0,
                        "losses": 0,
                        "total_profit": 0.0,
                        "total_profit_pips": 0.0
                    }
                
                analysis = strategy_analysis[strategy]
                analysis["trades"] += 1
                analysis["total_profit"] += trade_snapshot.profit_loss or 0
                analysis["total_profit_pips"] += trade_snapshot.profit_loss_pips or 0
                
                if trade_snapshot.profit_loss and trade_snapshot.profit_loss > 0:
                    analysis["wins"] += 1
                else:
                    analysis["losses"] += 1
            
            # 勝率計算
            for strategy, analysis in strategy_analysis.items():
                if analysis["trades"] > 0:
                    analysis["win_rate"] = (analysis["wins"] / analysis["trades"]) * 100
                else:
                    analysis["win_rate"] = 0.0
            
            return {
                "total_trades": total_trades,
                "completed_trades": len(completed_trades),
                "winning_trades": len(winning_trades),
                "losing_trades": len(losing_trades),
                "win_rate": win_rate,
                "total_profit": total_profit,
                "total_profit_pips": total_profit_pips,
                "strategy_analysis": strategy_analysis,
                "period_days": days
            }

    def to_dict(self) -> Dict[str, Any]:
        """スナップマネージャーの状態を辞書に変換"""
        return {
            "snapshots": {sid: asdict(snapshot) for sid, snapshot in self.snapshots.items()},
            "trade_snapshots": {tid: asdict(trade_snapshot) for tid, trade_snapshot in self.trade_snapshots.items()},
            "total_snapshots": len(self.snapshots),
            "total_trade_snapshots": len(self.trade_snapshots)
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """辞書からスナップマネージャーの状態を復元"""
        self.snapshots.clear()
        self.trade_snapshots.clear()
        
        # スナップショットの復元
        for sid, snapshot_data in data.get("snapshots", {}).items():
            # 日時文字列をdatetimeオブジェクトに変換
            for date_field in ["timestamp"]:
                if snapshot_data.get(date_field):
                    snapshot_data[date_field] = datetime.fromisoformat(snapshot_data[date_field].replace('Z', '+00:00'))
            
            # 列挙型の復元
            snapshot_data["snapshot_type"] = SnapshotType(snapshot_data["snapshot_type"])
            
            snapshot = MarketSnapshot(**snapshot_data)
            self.snapshots[sid] = snapshot
        
        # トレードスナップショットの復元
        for tid, trade_snapshot_data in data.get("trade_snapshots", {}).items():
            # 日時文字列をdatetimeオブジェクトに変換
            for date_field in ["entry_time", "exit_time"]:
                if trade_snapshot_data.get(date_field):
                    trade_snapshot_data[date_field] = datetime.fromisoformat(trade_snapshot_data[date_field].replace('Z', '+00:00'))
            
            # 列挙型の復元
            trade_snapshot_data["direction"] = TradeDirection(trade_snapshot_data["direction"])
            if trade_snapshot_data.get("exit_reason"):
                trade_snapshot_data["exit_reason"] = ExitReason(trade_snapshot_data["exit_reason"])
            
            trade_snapshot = TradeSnapshot(**trade_snapshot_data)
            self.trade_snapshots[tid] = trade_snapshot

    async def close(self):
        """リソースのクリーンアップ"""
        await self.data_preparator.close()


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from .scenario_manager import ScenarioManager, ScenarioStatus, TradeDirection
    from .rule_engine import EntrySignal, RuleResult
    
    snapshot_manager = SnapshotManager()
    scenario_manager = ScenarioManager()
    
    try:
        print("🧪 スナップ保存システムテスト...")
        
        # ダミーのエントリーシグナルとシナリオを作成
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
        
        # シナリオとトレードの作成
        scenario = await scenario_manager.create_scenario(dummy_signal)
        await scenario_manager.arm_scenario(scenario.id)
        await scenario_manager.trigger_scenario(scenario.id, 147.125)
        trade = await scenario_manager.enter_scenario(scenario.id, 147.125)
        
        # エントリースナップの保存
        if trade is not None:
            entry_snapshot_id = await snapshot_manager.save_entry_snapshot(scenario, trade)
            print(f"✅ エントリースナップ保存: {entry_snapshot_id}")
            
            # エグジットの実行
            await scenario_manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
            
            # エグジットスナップの保存
            exit_snapshot_id = await snapshot_manager.save_exit_snapshot(trade, ExitReason.TP1_HIT)
            print(f"✅ エグジットスナップ保存: {exit_snapshot_id}")
        
        # パフォーマンス分析の取得
        analysis = await snapshot_manager.get_performance_analysis()
        print(f"✅ パフォーマンス分析: {analysis['total_trades']}トレード, 勝率{analysis['win_rate']:.1f}%")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await snapshot_manager.close()
        await scenario_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
