"""
日次評価・改善サイクルシステム

日々のトレードパフォーマンスを分析し、
ルールの改善提案を自動生成するシステム。
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics

from ..core.snapshot_manager import TradeSnapshot, MarketSnapshot
from ..core.adherence_evaluator import AdherenceEvaluator, ViolationType
from ..core.scenario_manager import ScenarioManager, ExitReason, TradeDirection


class PerformanceMetric(Enum):
    """パフォーマンス指標"""
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    AVERAGE_HOLD_TIME = "average_hold_time"
    ADHERENCE_SCORE = "adherence_score"
    DAILY_RETURN = "daily_return"


class ImprovementCategory(Enum):
    """改善カテゴリ"""
    RISK_MANAGEMENT = "risk_management"
    TIMING = "timing"
    POSITION_SIZING = "position_sizing"
    RULE_LOGIC = "rule_logic"
    SESSION_OPTIMIZATION = "session_optimization"
    PARAMETER_TUNING = "parameter_tuning"


@dataclass
class DailyPerformance:
    """日次パフォーマンス"""
    date: datetime
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_profit_pips: float
    total_profit_percent: float
    profit_factor: float
    max_drawdown: float
    average_hold_time_minutes: float
    adherence_score_avg: float
    adherence_score_min: float
    adherence_score_max: float
    daily_return_percent: float
    
    # 戦略別パフォーマンス
    strategy_performance: Dict[str, Dict[str, Any]]
    
    # 違反分析
    violation_summary: Dict[str, int]
    
    # セッション分析
    session_performance: Dict[str, Dict[str, Any]]


@dataclass
class ImprovementSuggestion:
    """改善提案"""
    category: ImprovementCategory
    title: str
    description: str
    current_value: Any
    suggested_value: Any
    confidence: float  # 0.0-1.0
    expected_impact: str  # "high", "medium", "low"
    implementation_difficulty: str  # "easy", "medium", "hard"
    supporting_data: Dict[str, Any]
    created_at: datetime


@dataclass
class WeeklyReport:
    """週次レポート"""
    week_start: datetime
    week_end: datetime
    total_trades: int
    overall_performance: DailyPerformance
    daily_performances: List[DailyPerformance]
    improvement_suggestions: List[ImprovementSuggestion]
    rule_performance_analysis: Dict[str, Any]
    risk_analysis: Dict[str, Any]
    generated_at: datetime


class DailyEvaluator:
    """日次評価・改善サイクルシステム"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.adherence_evaluator = AdherenceEvaluator()
        self.scenario_manager = ScenarioManager()
        self._lock = None
        
        # パフォーマンス閾値
        self.performance_thresholds = {
            "min_win_rate": 0.6,           # 最低勝率60%
            "min_profit_factor": 1.5,      # 最低プロフィットファクター1.5
            "min_adherence_score": 80,     # 最低遵守スコア80点
            "max_drawdown": 0.05,          # 最大ドローダウン5%
            "max_daily_trades": 5,         # 日次最大トレード数5回
            "min_hold_time": 30,           # 最低保有時間30分
            "max_hold_time": 240           # 最大保有時間240分
        }

    async def evaluate_daily_performance(
        self,
        trade_snapshots: List[TradeSnapshot],
        target_date: Optional[datetime] = None
    ) -> DailyPerformance:
        """
        日次パフォーマンスの評価
        
        Args:
            trade_snapshots: トレードスナップショットのリスト
            target_date: 評価対象日（指定しない場合は今日）
        
        Returns:
            日次パフォーマンス
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if target_date is None:
                target_date = datetime.now(timezone.utc).date()
            else:
                target_date = target_date.date()
            
            self.logger.info(f"📊 日次パフォーマンス評価開始: {target_date}")
            
            try:
                # 対象日のトレードをフィルタリング
                daily_trades = [
                    ts for ts in trade_snapshots
                    if ts.entry_time and ts.entry_time.date() == target_date
                ]
                
                if not daily_trades:
                    return self._create_empty_daily_performance(target_date)
                
                # 基本統計の計算
                basic_stats = self._calculate_basic_statistics(daily_trades)
                
                # 戦略別パフォーマンスの計算
                strategy_performance = self._calculate_strategy_performance(daily_trades)
                
                # 違反分析
                violation_summary = self._analyze_violations(daily_trades)
                
                # セッション分析
                session_performance = self._analyze_session_performance(daily_trades)
                
                # 日次パフォーマンスオブジェクトの作成
                daily_performance = DailyPerformance(
                    date=datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc),
                    total_trades=basic_stats["total_trades"],
                    winning_trades=basic_stats["winning_trades"],
                    losing_trades=basic_stats["losing_trades"],
                    win_rate=basic_stats["win_rate"],
                    total_profit_pips=basic_stats["total_profit_pips"],
                    total_profit_percent=basic_stats["total_profit_percent"],
                    profit_factor=basic_stats["profit_factor"],
                    max_drawdown=basic_stats["max_drawdown"],
                    average_hold_time_minutes=basic_stats["average_hold_time_minutes"],
                    adherence_score_avg=basic_stats["adherence_score_avg"],
                    adherence_score_min=basic_stats["adherence_score_min"],
                    adherence_score_max=basic_stats["adherence_score_max"],
                    daily_return_percent=basic_stats["daily_return_percent"],
                    strategy_performance=strategy_performance,
                    violation_summary=violation_summary,
                    session_performance=session_performance
                )
                
                self.logger.info(f"✅ 日次パフォーマンス評価完了: {target_date}, トレード数: {daily_performance.total_trades}")
                return daily_performance
                
            except Exception as e:
                self.logger.error(f"❌ 日次パフォーマンス評価エラー: {e}")
                return self._create_empty_daily_performance(target_date)

    def _calculate_basic_statistics(self, trades: List[TradeSnapshot]) -> Dict[str, Any]:
        """基本統計の計算"""
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0.0,
                "total_profit_pips": 0.0,
                "total_profit_percent": 0.0,
                "profit_factor": 0.0,
                "max_drawdown": 0.0,
                "average_hold_time_minutes": 0.0,
                "adherence_score_avg": 0.0,
                "adherence_score_min": 0.0,
                "adherence_score_max": 0.0,
                "daily_return_percent": 0.0
            }
        
        # 基本統計
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit_loss_pips and t.profit_loss_pips > 0])
        losing_trades = len([t for t in trades if t.profit_loss_pips and t.profit_loss_pips <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # 損益統計
        total_profit_pips = sum(t.profit_loss_pips or 0 for t in trades)
        total_profit_percent = sum(t.profit_loss or 0 for t in trades)
        
        # プロフィットファクター
        gross_profit = sum(t.profit_loss_pips or 0 for t in trades if t.profit_loss_pips and t.profit_loss_pips > 0)
        gross_loss = abs(sum(t.profit_loss_pips or 0 for t in trades if t.profit_loss_pips and t.profit_loss_pips < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
        
        # ドローダウン（簡易計算）
        cumulative_pnl = 0
        max_cumulative = 0
        max_drawdown = 0
        for trade in trades:
            cumulative_pnl += trade.profit_loss_pips or 0
            max_cumulative = max(max_cumulative, cumulative_pnl)
            drawdown = max_cumulative - cumulative_pnl
            max_drawdown = max(max_drawdown, drawdown)
        
        # 保有時間統計
        hold_times = [t.hold_time_minutes for t in trades if t.hold_time_minutes is not None]
        average_hold_time_minutes = statistics.mean(hold_times) if hold_times else 0.0
        
        # 遵守スコア統計
        adherence_scores = [t.adherence_score for t in trades if t.adherence_score is not None]
        adherence_score_avg = statistics.mean(adherence_scores) if adherence_scores else 0.0
        adherence_score_min = min(adherence_scores) if adherence_scores else 0.0
        adherence_score_max = max(adherence_scores) if adherence_scores else 0.0
        
        # 日次リターン（仮の計算）
        daily_return_percent = total_profit_percent * 100  # 簡易計算
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_profit_pips": total_profit_pips,
            "total_profit_percent": total_profit_percent,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "average_hold_time_minutes": average_hold_time_minutes,
            "adherence_score_avg": adherence_score_avg,
            "adherence_score_min": adherence_score_min,
            "adherence_score_max": adherence_score_max,
            "daily_return_percent": daily_return_percent
        }

    def _calculate_strategy_performance(self, trades: List[TradeSnapshot]) -> Dict[str, Dict[str, Any]]:
        """戦略別パフォーマンスの計算"""
        strategy_stats = {}
        
        for trade in trades:
            strategy = trade.strategy
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "trades": 0,
                    "wins": 0,
                    "losses": 0,
                    "total_profit_pips": 0.0,
                    "total_profit_percent": 0.0,
                    "adherence_scores": [],
                    "hold_times": []
                }
            
            stats = strategy_stats[strategy]
            stats["trades"] += 1
            stats["total_profit_pips"] += trade.profit_loss_pips or 0
            stats["total_profit_percent"] += trade.profit_loss or 0
            
            if trade.profit_loss_pips and trade.profit_loss_pips > 0:
                stats["wins"] += 1
            else:
                stats["losses"] += 1
            
            if trade.adherence_score is not None:
                stats["adherence_scores"].append(trade.adherence_score)
            
            if trade.hold_time_minutes is not None:
                stats["hold_times"].append(trade.hold_time_minutes)
        
        # 統計の計算
        for strategy, stats in strategy_stats.items():
            stats["win_rate"] = stats["wins"] / stats["trades"] if stats["trades"] > 0 else 0.0
            stats["profit_factor"] = self._calculate_profit_factor(stats["wins"], stats["losses"], stats["total_profit_pips"])
            stats["avg_adherence_score"] = statistics.mean(stats["adherence_scores"]) if stats["adherence_scores"] else 0.0
            stats["avg_hold_time"] = statistics.mean(stats["hold_times"]) if stats["hold_times"] else 0.0
        
        return strategy_stats

    def _calculate_profit_factor(self, wins: int, losses: int, total_profit: float) -> float:
        """プロフィットファクターの計算"""
        if losses == 0:
            return float('inf') if total_profit > 0 else 0.0
        
        # 簡易計算（実際はより複雑な計算が必要）
        return total_profit / abs(total_profit) if total_profit != 0 else 0.0

    def _analyze_violations(self, trades: List[TradeSnapshot]) -> Dict[str, int]:
        """違反分析"""
        violation_counts = {}
        
        for trade in trades:
            if hasattr(trade, 'violation_tags') and trade.violation_tags:
                for violation in trade.violation_tags:
                    violation_counts[violation] = violation_counts.get(violation, 0) + 1
        
        return violation_counts

    def _analyze_session_performance(self, trades: List[TradeSnapshot]) -> Dict[str, Dict[str, Any]]:
        """セッション分析"""
        session_stats = {}
        
        for trade in trades:
            # エントリー時間からセッションを推定（簡易実装）
            entry_hour = trade.entry_time.hour if trade.entry_time else 0
            
            if 9 <= entry_hour < 15:
                session = "Tokyo"
            elif 16 <= entry_hour < 24:
                session = "London"
            elif 22 <= entry_hour or entry_hour < 6:
                session = "NewYork"
            else:
                session = "Other"
            
            if session not in session_stats:
                session_stats[session] = {
                    "trades": 0,
                    "wins": 0,
                    "total_profit_pips": 0.0,
                    "adherence_scores": []
                }
            
            stats = session_stats[session]
            stats["trades"] += 1
            stats["total_profit_pips"] += trade.profit_loss_pips or 0
            
            if trade.profit_loss_pips and trade.profit_loss_pips > 0:
                stats["wins"] += 1
            
            if trade.adherence_score is not None:
                stats["adherence_scores"].append(trade.adherence_score)
        
        # 統計の計算
        for session, stats in session_stats.items():
            stats["win_rate"] = stats["wins"] / stats["trades"] if stats["trades"] > 0 else 0.0
            stats["avg_adherence_score"] = statistics.mean(stats["adherence_scores"]) if stats["adherence_scores"] else 0.0
        
        return session_stats

    def _create_empty_daily_performance(self, target_date) -> DailyPerformance:
        """空の日次パフォーマンスの作成"""
        return DailyPerformance(
            date=datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc),
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            win_rate=0.0,
            total_profit_pips=0.0,
            total_profit_percent=0.0,
            profit_factor=0.0,
            max_drawdown=0.0,
            average_hold_time_minutes=0.0,
            adherence_score_avg=0.0,
            adherence_score_min=0.0,
            adherence_score_max=0.0,
            daily_return_percent=0.0,
            strategy_performance={},
            violation_summary={},
            session_performance={}
        )

    async def generate_improvement_suggestions(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> List[ImprovementSuggestion]:
        """
        改善提案の生成
        
        Args:
            daily_performance: 当日のパフォーマンス
            historical_performance: 過去のパフォーマンス履歴
        
        Returns:
            改善提案のリスト
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            suggestions = []
            
            try:
                # 1. 勝率改善提案
                if daily_performance.win_rate < self.performance_thresholds["min_win_rate"]:
                    suggestions.append(self._create_win_rate_improvement_suggestion(
                        daily_performance, historical_performance
                    ))
                
                # 2. プロフィットファクター改善提案
                if daily_performance.profit_factor < self.performance_thresholds["min_profit_factor"]:
                    suggestions.append(self._create_profit_factor_improvement_suggestion(
                        daily_performance, historical_performance
                    ))
                
                # 3. 遵守スコア改善提案
                if daily_performance.adherence_score_avg < self.performance_thresholds["min_adherence_score"]:
                    suggestions.append(self._create_adherence_improvement_suggestion(
                        daily_performance, historical_performance
                    ))
                
                # 4. ドローダウン改善提案
                if daily_performance.max_drawdown > self.performance_thresholds["max_drawdown"]:
                    suggestions.append(self._create_drawdown_improvement_suggestion(
                        daily_performance, historical_performance
                    ))
                
                # 5. 保有時間改善提案
                if (daily_performance.average_hold_time_minutes < self.performance_thresholds["min_hold_time"] or
                    daily_performance.average_hold_time_minutes > self.performance_thresholds["max_hold_time"]):
                    suggestions.append(self._create_hold_time_improvement_suggestion(
                        daily_performance, historical_performance
                    ))
                
                # 6. 戦略別改善提案
                strategy_suggestions = self._create_strategy_improvement_suggestions(
                    daily_performance, historical_performance
                )
                suggestions.extend(strategy_suggestions)
                
                # 7. セッション改善提案
                session_suggestions = self._create_session_improvement_suggestions(
                    daily_performance, historical_performance
                )
                suggestions.extend(session_suggestions)
                
                self.logger.info(f"✅ 改善提案生成完了: {len(suggestions)}件")
                return suggestions
                
            except Exception as e:
                self.logger.error(f"❌ 改善提案生成エラー: {e}")
                return []

    def _create_win_rate_improvement_suggestion(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> ImprovementSuggestion:
        """勝率改善提案の作成"""
        return ImprovementSuggestion(
            category=ImprovementCategory.RULE_LOGIC,
            title="勝率改善のためのルール調整",
            description=f"現在の勝率{daily_performance.win_rate:.1%}が目標の{self.performance_thresholds['min_win_rate']:.1%}を下回っています。",
            current_value=daily_performance.win_rate,
            suggested_value=self.performance_thresholds["min_win_rate"],
            confidence=0.8,
            expected_impact="high",
            implementation_difficulty="medium",
            supporting_data={
                "daily_win_rate": daily_performance.win_rate,
                "target_win_rate": self.performance_thresholds["min_win_rate"],
                "violation_summary": daily_performance.violation_summary
            },
            created_at=datetime.now(timezone.utc)
        )

    def _create_profit_factor_improvement_suggestion(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> ImprovementSuggestion:
        """プロフィットファクター改善提案の作成"""
        return ImprovementSuggestion(
            category=ImprovementCategory.RISK_MANAGEMENT,
            title="プロフィットファクター改善のためのリスク管理調整",
            description=f"現在のプロフィットファクター{daily_performance.profit_factor:.2f}が目標の{self.performance_thresholds['min_profit_factor']}を下回っています。",
            current_value=daily_performance.profit_factor,
            suggested_value=self.performance_thresholds["min_profit_factor"],
            confidence=0.7,
            expected_impact="high",
            implementation_difficulty="medium",
            supporting_data={
                "daily_profit_factor": daily_performance.profit_factor,
                "target_profit_factor": self.performance_thresholds["min_profit_factor"],
                "total_profit_pips": daily_performance.total_profit_pips
            },
            created_at=datetime.now(timezone.utc)
        )

    def _create_adherence_improvement_suggestion(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> ImprovementSuggestion:
        """遵守スコア改善提案の作成"""
        return ImprovementSuggestion(
            category=ImprovementCategory.RULE_LOGIC,
            title="ルール遵守スコア改善",
            description=f"現在の遵守スコア{daily_performance.adherence_score_avg:.1f}点が目標の{self.performance_thresholds['min_adherence_score']}点を下回っています。",
            current_value=daily_performance.adherence_score_avg,
            suggested_value=self.performance_thresholds["min_adherence_score"],
            confidence=0.9,
            expected_impact="medium",
            implementation_difficulty="easy",
            supporting_data={
                "daily_adherence_score": daily_performance.adherence_score_avg,
                "target_adherence_score": self.performance_thresholds["min_adherence_score"],
                "violation_summary": daily_performance.violation_summary
            },
            created_at=datetime.now(timezone.utc)
        )

    def _create_drawdown_improvement_suggestion(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> ImprovementSuggestion:
        """ドローダウン改善提案の作成"""
        return ImprovementSuggestion(
            category=ImprovementCategory.RISK_MANAGEMENT,
            title="最大ドローダウン改善のためのリスク管理強化",
            description=f"現在の最大ドローダウン{daily_performance.max_drawdown:.1f}ピップスが目標の{self.performance_thresholds['max_drawdown']*100:.1f}%を上回っています。",
            current_value=daily_performance.max_drawdown,
            suggested_value=self.performance_thresholds["max_drawdown"] * 100,
            confidence=0.8,
            expected_impact="high",
            implementation_difficulty="medium",
            supporting_data={
                "daily_max_drawdown": daily_performance.max_drawdown,
                "target_max_drawdown": self.performance_thresholds["max_drawdown"] * 100,
                "total_trades": daily_performance.total_trades
            },
            created_at=datetime.now(timezone.utc)
        )

    def _create_hold_time_improvement_suggestion(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> ImprovementSuggestion:
        """保有時間改善提案の作成"""
        return ImprovementSuggestion(
            category=ImprovementCategory.TIMING,
            title="保有時間最適化",
            description=f"現在の平均保有時間{daily_performance.average_hold_time_minutes:.1f}分が推奨範囲外です。",
            current_value=daily_performance.average_hold_time_minutes,
            suggested_value=f"{self.performance_thresholds['min_hold_time']}-{self.performance_thresholds['max_hold_time']}分",
            confidence=0.6,
            expected_impact="medium",
            implementation_difficulty="easy",
            supporting_data={
                "daily_avg_hold_time": daily_performance.average_hold_time_minutes,
                "target_hold_time_range": f"{self.performance_thresholds['min_hold_time']}-{self.performance_thresholds['max_hold_time']}分"
            },
            created_at=datetime.now(timezone.utc)
        )

    def _create_strategy_improvement_suggestions(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> List[ImprovementSuggestion]:
        """戦略別改善提案の作成"""
        suggestions = []
        
        for strategy, performance in daily_performance.strategy_performance.items():
            if performance["win_rate"] < 0.6:  # 戦略別勝率が60%未満
                suggestions.append(ImprovementSuggestion(
                    category=ImprovementCategory.PARAMETER_TUNING,
                    title=f"{strategy}戦略のパラメータ調整",
                    description=f"{strategy}戦略の勝率{performance['win_rate']:.1%}が低いため、パラメータの調整を検討してください。",
                    current_value=performance["win_rate"],
                    suggested_value=0.7,
                    confidence=0.7,
                    expected_impact="medium",
                    implementation_difficulty="medium",
                    supporting_data={
                        "strategy": strategy,
                        "current_win_rate": performance["win_rate"],
                        "trades": performance["trades"],
                        "avg_adherence_score": performance.get("avg_adherence_score", 0)
                    },
                    created_at=datetime.now(timezone.utc)
                ))
        
        return suggestions

    def _create_session_improvement_suggestions(
        self,
        daily_performance: DailyPerformance,
        historical_performance: List[DailyPerformance]
    ) -> List[ImprovementSuggestion]:
        """セッション改善提案の作成"""
        suggestions = []
        
        for session, performance in daily_performance.session_performance.items():
            if performance["win_rate"] < 0.5:  # セッション別勝率が50%未満
                suggestions.append(ImprovementSuggestion(
                    category=ImprovementCategory.SESSION_OPTIMIZATION,
                    title=f"{session}セッションの最適化",
                    description=f"{session}セッションの勝率{performance['win_rate']:.1%}が低いため、このセッションでのトレードを制限することを検討してください。",
                    current_value=performance["win_rate"],
                    suggested_value=0.6,
                    confidence=0.6,
                    expected_impact="medium",
                    implementation_difficulty="easy",
                    supporting_data={
                        "session": session,
                        "current_win_rate": performance["win_rate"],
                        "trades": performance["trades"],
                        "avg_adherence_score": performance.get("avg_adherence_score", 0)
                    },
                    created_at=datetime.now(timezone.utc)
                ))
        
        return suggestions

    async def generate_weekly_report(
        self,
        trade_snapshots: List[TradeSnapshot],
        week_start: Optional[datetime] = None
    ) -> WeeklyReport:
        """
        週次レポートの生成
        
        Args:
            trade_snapshots: トレードスナップショットのリスト
            week_start: 週の開始日（指定しない場合は今週の月曜日）
        
        Returns:
            週次レポート
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            if week_start is None:
                today = datetime.now(timezone.utc).date()
                week_start = today - timedelta(days=today.weekday())
            else:
                week_start = week_start.date()
            
            week_end = week_start + timedelta(days=6)
            
            self.logger.info(f"📊 週次レポート生成開始: {week_start} - {week_end}")
            
            try:
                # 週間のトレードをフィルタリング
                weekly_trades = [
                    ts for ts in trade_snapshots
                    if ts.entry_time and week_start <= ts.entry_time.date() <= week_end
                ]
                
                # 日別パフォーマンスの計算
                daily_performances = []
                for i in range(7):
                    target_date = week_start + timedelta(days=i)
                    daily_performance = await self.evaluate_daily_performance(
                        weekly_trades, target_date
                    )
                    daily_performances.append(daily_performance)
                
                # 週間全体のパフォーマンス計算
                overall_performance = await self.evaluate_daily_performance(weekly_trades)
                
                # 改善提案の生成
                improvement_suggestions = await self.generate_improvement_suggestions(
                    overall_performance, daily_performances
                )
                
                # ルールパフォーマンス分析
                rule_performance_analysis = self._analyze_rule_performance(weekly_trades)
                
                # リスク分析
                risk_analysis = self._analyze_weekly_risk(weekly_trades)
                
                # 週次レポートの作成
                weekly_report = WeeklyReport(
                    week_start=datetime.combine(week_start, datetime.min.time()).replace(tzinfo=timezone.utc),
                    week_end=datetime.combine(week_end, datetime.min.time()).replace(tzinfo=timezone.utc),
                    total_trades=len(weekly_trades),
                    overall_performance=overall_performance,
                    daily_performances=daily_performances,
                    improvement_suggestions=improvement_suggestions,
                    rule_performance_analysis=rule_performance_analysis,
                    risk_analysis=risk_analysis,
                    generated_at=datetime.now(timezone.utc)
                )
                
                self.logger.info(f"✅ 週次レポート生成完了: {week_start} - {week_end}")
                return weekly_report
                
            except Exception as e:
                self.logger.error(f"❌ 週次レポート生成エラー: {e}")
                raise

    def _analyze_rule_performance(self, trades: List[TradeSnapshot]) -> Dict[str, Any]:
        """ルールパフォーマンス分析"""
        rule_analysis = {
            "total_rules_tested": 0,
            "successful_rules": 0,
            "failed_rules": 0,
            "rule_effectiveness": 0.0,
            "most_effective_strategy": None,
            "least_effective_strategy": None
        }
        
        if not trades:
            return rule_analysis
        
        # 戦略別の効果分析
        strategy_effectiveness = {}
        for trade in trades:
            strategy = trade.strategy
            if strategy not in strategy_effectiveness:
                strategy_effectiveness[strategy] = {
                    "trades": 0,
                    "wins": 0,
                    "total_profit": 0.0,
                    "adherence_scores": []
                }
            
            stats = strategy_effectiveness[strategy]
            stats["trades"] += 1
            if trade.profit_loss_pips and trade.profit_loss_pips > 0:
                stats["wins"] += 1
            stats["total_profit"] += trade.profit_loss_pips or 0
            if trade.adherence_score is not None:
                stats["adherence_scores"].append(trade.adherence_score)
        
        # 効果性の計算
        for strategy, stats in strategy_effectiveness.items():
            win_rate = stats["wins"] / stats["trades"] if stats["trades"] > 0 else 0
            avg_adherence = statistics.mean(stats["adherence_scores"]) if stats["adherence_scores"] else 0
            effectiveness = (win_rate * 0.6 + avg_adherence / 100 * 0.4)  # 重み付きスコア
            strategy_effectiveness[strategy]["effectiveness"] = effectiveness
        
        # 最も効果的・非効果的な戦略の特定
        if strategy_effectiveness:
            most_effective = max(strategy_effectiveness.items(), key=lambda x: x[1]["effectiveness"])
            least_effective = min(strategy_effectiveness.items(), key=lambda x: x[1]["effectiveness"])
            
            rule_analysis.update({
                "most_effective_strategy": {
                    "name": most_effective[0],
                    "effectiveness": most_effective[1]["effectiveness"],
                    "win_rate": most_effective[1]["wins"] / most_effective[1]["trades"],
                    "trades": most_effective[1]["trades"]
                },
                "least_effective_strategy": {
                    "name": least_effective[0],
                    "effectiveness": least_effective[1]["effectiveness"],
                    "win_rate": least_effective[1]["wins"] / least_effective[1]["trades"],
                    "trades": least_effective[1]["trades"]
                }
            })
        
        return rule_analysis

    def _analyze_weekly_risk(self, trades: List[TradeSnapshot]) -> Dict[str, Any]:
        """週間リスク分析"""
        risk_analysis = {
            "max_daily_trades": 0,
            "max_daily_drawdown": 0.0,
            "risk_concentration": 0.0,
            "correlation_risk": 0.0,
            "adherence_consistency": 0.0
        }
        
        if not trades:
            return risk_analysis
        
        # 日別トレード数の分析
        daily_trade_counts = {}
        daily_drawdowns = {}
        
        for trade in trades:
            if trade.entry_time:
                trade_date = trade.entry_time.date()
                daily_trade_counts[trade_date] = daily_trade_counts.get(trade_date, 0) + 1
                
                # 簡易ドローダウン計算
                if trade_date not in daily_drawdowns:
                    daily_drawdowns[trade_date] = 0
                daily_drawdowns[trade_date] = max(daily_drawdowns[trade_date], abs(trade.profit_loss_pips or 0))
        
        risk_analysis["max_daily_trades"] = max(daily_trade_counts.values()) if daily_trade_counts else 0
        risk_analysis["max_daily_drawdown"] = max(daily_drawdowns.values()) if daily_drawdowns else 0.0
        
        # 遵守スコアの一貫性
        adherence_scores = [t.adherence_score for t in trades if t.adherence_score is not None]
        if adherence_scores:
            adherence_std = statistics.stdev(adherence_scores)
            adherence_consistency = max(0, 100 - adherence_std)  # 標準偏差が小さいほど一貫性が高い
            risk_analysis["adherence_consistency"] = adherence_consistency
        
        return risk_analysis

    async def close(self):
        """リソースのクリーンアップ"""
        await self.adherence_evaluator.close()
        await self.scenario_manager.close()
        self.logger.info("DailyEvaluator closed")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from ..core.snapshot_manager import SnapshotManager
    from ..core.scenario_manager import ScenarioManager, TradeDirection, ExitReason
    from ..core.rule_engine import EntrySignal, RuleResult
    
    evaluator = DailyEvaluator()
    scenario_manager = ScenarioManager()
    snapshot_manager = SnapshotManager()
    
    try:
        print("🧪 日次評価・改善サイクルシステムテスト...")
        
        # ダミーのトレードスナップショットを作成
        from ..core.snapshot_manager import TradeSnapshot
        
        trade_snapshots = []
        for i in range(5):
            trade_snapshot = TradeSnapshot(
                id=f"trade_snapshot_{i}",
                trade_id=f"trade_{i}",
                scenario_id=f"scenario_{i}",
                entry_snapshot_id=f"entry_snapshot_{i}",
                exit_snapshot_id=f"exit_snapshot_{i}",
                direction=TradeDirection.BUY,
                strategy=f"strategy_{i % 2}",  # 2つの戦略に分散
                entry_price=147.123 + i * 0.001,
                exit_price=147.400 + i * 0.001,
                position_size=10000,
                stop_loss=146.800 + i * 0.001,
                take_profit_1=147.400 + i * 0.001,
                take_profit_2=147.600 + i * 0.001,
                take_profit_3=147.800 + i * 0.001,
                entry_time=datetime.now(timezone.utc) - timedelta(hours=i),
                exit_time=datetime.now(timezone.utc) - timedelta(hours=i-1),
                hold_time_minutes=60 + i * 30,
                exit_reason=ExitReason.TP1_HIT,
                profit_loss=100 + i * 50,
                profit_loss_pips=10 + i * 5,
                adherence_score=85 + i * 3,  # 85, 88, 91, 94, 97点
                violation_tags=[f"violation_{i}"] if i % 2 == 0 else [],
                metadata={}
            )
            trade_snapshots.append(trade_snapshot)
        
        # 日次パフォーマンス評価
        daily_performance = await evaluator.evaluate_daily_performance(trade_snapshots)
        
        print(f"✅ 日次パフォーマンス評価完了:")
        print(f"   総トレード数: {daily_performance.total_trades}")
        print(f"   勝率: {daily_performance.win_rate:.1%}")
        print(f"   総利益: {daily_performance.total_profit_pips:.1f}ピップス")
        print(f"   プロフィットファクター: {daily_performance.profit_factor:.2f}")
        print(f"   平均遵守スコア: {daily_performance.adherence_score_avg:.1f}点")
        
        # 改善提案の生成
        improvement_suggestions = await evaluator.generate_improvement_suggestions(
            daily_performance, []
        )
        
        print(f"✅ 改善提案生成完了: {len(improvement_suggestions)}件")
        for suggestion in improvement_suggestions:
            print(f"   - {suggestion.title}: {suggestion.description}")
        
        # 週次レポートの生成
        weekly_report = await evaluator.generate_weekly_report(trade_snapshots)
        
        print(f"✅ 週次レポート生成完了:")
        print(f"   週間総トレード数: {weekly_report.total_trades}")
        print(f"   週間勝率: {weekly_report.overall_performance.win_rate:.1%}")
        print(f"   改善提案数: {len(weekly_report.improvement_suggestions)}件")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await evaluator.close()
        await scenario_manager.close()
        await snapshot_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
