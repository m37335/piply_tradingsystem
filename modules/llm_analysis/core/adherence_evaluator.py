"""
ルール遵守判定システム

トレードがルールに従って実行されたかを100点満点で評価し、
違反箇所を特定・記録するシステム。
"""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json

from .scenario_manager import Trade, ExitReason, TradeDirection
from .rule_engine import RuleResult
from .snapshot_manager import TradeSnapshot, MarketSnapshot


class ViolationType(Enum):
    """違反タイプ"""
    RISK_MANAGEMENT = "risk_management"      # リスク管理違反
    TIMING = "timing"                        # タイミング違反
    POSITION_SIZING = "position_sizing"      # ポジションサイズ違反
    RULE_LOGIC = "rule_logic"                # ルールロジック違反
    SESSION = "session"                      # セッション違反
    CORRELATION = "correlation"              # 相関違反
    HOLD_TIME = "hold_time"                  # 保有時間違反


@dataclass
class Violation:
    """違反記録"""
    violation_type: ViolationType
    rule_name: str
    description: str
    expected_value: Any
    actual_value: Any
    penalty_points: int
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime


@dataclass
class AdherenceScore:
    """遵守スコア"""
    total_score: int  # 100点満点
    violations: List[Violation]
    violation_count: int
    critical_violations: int
    high_violations: int
    medium_violations: int
    low_violations: int
    
    # カテゴリ別スコア
    risk_management_score: int
    timing_score: int
    position_sizing_score: int
    rule_logic_score: int
    session_score: int
    correlation_score: int
    hold_time_score: int
    
    # メタデータ
    evaluation_timestamp: datetime
    trade_id: str
    max_score: int = 100
    evaluator_version: str = "1.0"


class AdherenceEvaluator:
    """ルール遵守判定システム"""

    def __init__(self):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self._lock = None
        
        # スコア配分（100点満点）
        self.score_weights = {
            "risk_management": 25,    # リスク管理（25点）
            "timing": 20,            # タイミング（20点）
            "position_sizing": 15,   # ポジションサイズ（15点）
            "rule_logic": 20,        # ルールロジック（20点）
            "session": 10,           # セッション（10点）
            "correlation": 5,        # 相関（5点）
            "hold_time": 5           # 保有時間（5点）
        }
        
        # 違反ペナルティ
        self.penalty_weights = {
            "critical": 20,  # 重大違反：20点減点
            "high": 10,      # 高違反：10点減点
            "medium": 5,     # 中違反：5点減点
            "low": 2         # 低違反：2点減点
        }

    async def evaluate_trade_adherence(
        self,
        trade: Trade,
        entry_snapshot: MarketSnapshot,
        exit_snapshot: Optional[MarketSnapshot] = None,
        daily_trades: int = 0,
        daily_risk_percent: float = 0.0
    ) -> AdherenceScore:
        """
        トレードのルール遵守度を評価
        
        Args:
            trade: 評価対象のトレード
            entry_snapshot: エントリー時のスナップショット
            exit_snapshot: エグジット時のスナップショット（オプション）
            daily_trades: 日次トレード数
            daily_risk_percent: 日次リスク割合
        
        Returns:
            遵守スコア
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            self.logger.info(f"📊 トレード遵守度評価開始: {trade.id}")
            
            violations = []
            
            # 1. リスク管理評価
            risk_violations = await self._evaluate_risk_management(
                trade, entry_snapshot, daily_risk_percent
            )
            violations.extend(risk_violations)
            
            # 2. タイミング評価
            timing_violations = await self._evaluate_timing(
                trade, entry_snapshot, exit_snapshot
            )
            violations.extend(timing_violations)
            
            # 3. ポジションサイズ評価
            position_violations = await self._evaluate_position_sizing(
                trade, entry_snapshot
            )
            violations.extend(position_violations)
            
            # 4. ルールロジック評価
            rule_violations = await self._evaluate_rule_logic(
                trade, entry_snapshot
            )
            violations.extend(rule_violations)
            
            # 5. セッション評価
            session_violations = await self._evaluate_session(
                trade, entry_snapshot
            )
            violations.extend(session_violations)
            
            # 6. 相関評価
            correlation_violations = await self._evaluate_correlation(
                trade, daily_trades
            )
            violations.extend(correlation_violations)
            
            # 7. 保有時間評価
            hold_time_violations = await self._evaluate_hold_time(
                trade, exit_snapshot
            )
            violations.extend(hold_time_violations)
            
            # スコア計算
            score = self._calculate_score(violations)
            
            self.logger.info(f"✅ トレード遵守度評価完了: {trade.id}, スコア: {score.total_score}/100")
            
            return score

    async def _evaluate_risk_management(
        self,
        trade: Trade,
        entry_snapshot: MarketSnapshot,
        daily_risk_percent: float
    ) -> List[Violation]:
        """リスク管理の評価"""
        violations = []
        
        try:
            # 1. トレードあたりのリスク上限チェック（1%）
            if trade.stop_loss is None:
                return violations  # ストップロスが設定されていない場合はスキップ
            
            trade_risk = abs(trade.entry_price - trade.stop_loss) / trade.entry_price * 100
            if trade_risk > 1.0:
                violations.append(Violation(
                    violation_type=ViolationType.RISK_MANAGEMENT,
                    rule_name="max_risk_per_trade",
                    description=f"トレードあたりのリスクが上限を超過",
                    expected_value=1.0,
                    actual_value=trade_risk,
                    penalty_points=20,
                    severity="critical",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 2. 日次リスク上限チェック（3%）
            if daily_risk_percent > 3.0:
                violations.append(Violation(
                    violation_type=ViolationType.RISK_MANAGEMENT,
                    rule_name="max_risk_per_day",
                    description=f"日次リスクが上限を超過",
                    expected_value=3.0,
                    actual_value=daily_risk_percent,
                    penalty_points=20,
                    severity="critical",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 3. リスクリワード比チェック（最低1:1）
            # Tradeオブジェクトからrisk_reward_ratioを取得（シナリオから）
            risk_reward_ratio = getattr(trade, 'risk_reward_ratio', 2.0)  # デフォルト値
            if risk_reward_ratio < 1.0:
                violations.append(Violation(
                    violation_type=ViolationType.RISK_MANAGEMENT,
                    rule_name="min_risk_reward_ratio",
                    description=f"リスクリワード比が最低値を下回る",
                    expected_value=1.0,
                    actual_value=risk_reward_ratio,
                    penalty_points=10,
                    severity="high",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 4. ストップロス設定チェック
            if trade.direction == TradeDirection.BUY:
                if trade.stop_loss is not None and trade.stop_loss >= trade.entry_price:
                    violations.append(Violation(
                        violation_type=ViolationType.RISK_MANAGEMENT,
                        rule_name="stop_loss_direction",
                        description=f"買いポジションでストップロスがエントリー価格以上",
                        expected_value=f"< {trade.entry_price}",
                        actual_value=trade.stop_loss,
                        penalty_points=15,
                        severity="high",
                        timestamp=datetime.now(timezone.utc)
                    ))
            else:  # SELL
                if trade.stop_loss is not None and trade.stop_loss <= trade.entry_price:
                    violations.append(Violation(
                        violation_type=ViolationType.RISK_MANAGEMENT,
                        rule_name="stop_loss_direction",
                        description=f"売りポジションでストップロスがエントリー価格以下",
                        expected_value=f"> {trade.entry_price}",
                        actual_value=trade.stop_loss,
                        penalty_points=15,
                        severity="high",
                        timestamp=datetime.now(timezone.utc)
                    ))
            
        except Exception as e:
            self.logger.error(f"❌ リスク管理評価エラー: {e}")
        
        return violations

    async def _evaluate_timing(
        self,
        trade: Trade,
        entry_snapshot: MarketSnapshot,
        exit_snapshot: Optional[MarketSnapshot]
    ) -> List[Violation]:
        """タイミングの評価"""
        violations = []
        
        try:
            # 1. エントリータイミングの評価
            entry_time = trade.entry_time
            if entry_time:
                # セッション時間内かチェック
                session_info = entry_snapshot.session_info
                active_sessions = session_info.get("active_sessions", [])
                
                if not active_sessions:
                    violations.append(Violation(
                        violation_type=ViolationType.TIMING,
                        rule_name="session_timing",
                        description=f"非アクティブセッション時間でのエントリー",
                        expected_value="アクティブセッション",
                        actual_value="非アクティブセッション",
                        penalty_points=5,
                        severity="medium",
                        timestamp=datetime.now(timezone.utc)
                    ))
            
            # 2. エグジットタイミングの評価
            if exit_snapshot and trade.exit_time:
                exit_session_info = exit_snapshot.session_info
                exit_active_sessions = exit_session_info.get("active_sessions", [])
                
                # エグジットはセッション時間外でも許容（リスク管理のため）
                # ただし、意図的なセッション外エグジットは記録
                if not exit_active_sessions and trade.exit_reason not in [ExitReason.STOP_LOSS, ExitReason.TIME_EXIT]:
                    violations.append(Violation(
                        violation_type=ViolationType.TIMING,
                        rule_name="exit_session_timing",
                        description=f"非アクティブセッション時間での意図的エグジット",
                        expected_value="アクティブセッション",
                        actual_value="非アクティブセッション",
                        penalty_points=2,
                        severity="low",
                        timestamp=datetime.now(timezone.utc)
                    ))
            
        except Exception as e:
            self.logger.error(f"❌ タイミング評価エラー: {e}")
        
        return violations

    async def _evaluate_position_sizing(
        self,
        trade: Trade,
        entry_snapshot: MarketSnapshot
    ) -> List[Violation]:
        """ポジションサイズの評価"""
        violations = []
        
        try:
            # 1. ポジションサイズの妥当性チェック
            if trade.position_size <= 0:
                violations.append(Violation(
                    violation_type=ViolationType.POSITION_SIZING,
                    rule_name="position_size_positive",
                    description=f"ポジションサイズが0以下",
                    expected_value="> 0",
                    actual_value=trade.position_size,
                    penalty_points=15,
                    severity="high",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 2. 最大ポジションサイズチェック（仮の値）
            max_position_size = 100000  # 仮の上限
            if trade.position_size > max_position_size:
                violations.append(Violation(
                    violation_type=ViolationType.POSITION_SIZING,
                    rule_name="max_position_size",
                    description=f"ポジションサイズが上限を超過",
                    expected_value=f"<= {max_position_size}",
                    actual_value=trade.position_size,
                    penalty_points=10,
                    severity="high",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 3. アカウントバランスに対する比率チェック（仮の値）
            account_balance = 1000000  # 仮のアカウントバランス
            position_ratio = trade.position_size / account_balance * 100
            
            if position_ratio > 10:  # アカウントバランスの10%以上
                violations.append(Violation(
                    violation_type=ViolationType.POSITION_SIZING,
                    rule_name="position_balance_ratio",
                    description=f"アカウントバランスに対するポジション比率が過大",
                    expected_value="<= 10%",
                    actual_value=f"{position_ratio:.2f}%",
                    penalty_points=8,
                    severity="medium",
                    timestamp=datetime.now(timezone.utc)
                ))
            
        except Exception as e:
            self.logger.error(f"❌ ポジションサイズ評価エラー: {e}")
        
        return violations

    async def _evaluate_rule_logic(
        self,
        trade: Trade,
        entry_snapshot: MarketSnapshot
    ) -> List[Violation]:
        """ルールロジックの評価"""
        violations = []
        
        try:
            # 1. エントリー条件の妥当性チェック
            # 実際のルール結果はシナリオに含まれているため、ここでは基本的なチェック
            
            # 2. テクニカル指標の整合性チェック
            technical_indicators = entry_snapshot.technical_indicators
            
            # RSIの妥当性チェック
            for timeframe, indicators in technical_indicators.items():
                rsi_14 = indicators.get("rsi_14")
                if rsi_14 is not None:
                    if rsi_14 < 0 or rsi_14 > 100:
                        violations.append(Violation(
                            violation_type=ViolationType.RULE_LOGIC,
                            rule_name="rsi_range",
                            description=f"{timeframe}のRSI値が範囲外",
                            expected_value="0-100",
                            actual_value=rsi_14,
                            penalty_points=5,
                            severity="medium",
                            timestamp=datetime.now(timezone.utc)
                        ))
            
            # 3. 価格データの整合性チェック
            price_data = entry_snapshot.price_data
            for timeframe, prices in price_data.items():
                if prices.get("high", 0) < prices.get("low", 0):
                    violations.append(Violation(
                        violation_type=ViolationType.RULE_LOGIC,
                        rule_name="price_consistency",
                        description=f"{timeframe}の価格データが不整合",
                        expected_value="high >= low",
                        actual_value=f"high={prices.get('high')}, low={prices.get('low')}",
                        penalty_points=10,
                        severity="high",
                        timestamp=datetime.now(timezone.utc)
                    ))
            
        except Exception as e:
            self.logger.error(f"❌ ルールロジック評価エラー: {e}")
        
        return violations

    async def _evaluate_session(
        self,
        trade: Trade,
        entry_snapshot: MarketSnapshot
    ) -> List[Violation]:
        """セッションの評価"""
        violations = []
        
        try:
            # 1. セッション時間の妥当性チェック
            session_info = entry_snapshot.session_info
            active_sessions = session_info.get("active_sessions", [])
            
            # 推奨セッション（東京・ロンドン・ニューヨーク）
            recommended_sessions = ["Tokyo", "London", "NewYork"]
            
            if not any(session in active_sessions for session in recommended_sessions):
                violations.append(Violation(
                    violation_type=ViolationType.SESSION,
                    rule_name="recommended_session",
                    description=f"推奨セッション時間外でのトレード",
                    expected_value="Tokyo/London/NewYork",
                    actual_value=active_sessions,
                    penalty_points=3,
                    severity="low",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 2. セッション重複チェック
            if len(active_sessions) > 1:
                # セッション重複は通常は問題ないが、記録として残す
                violations.append(Violation(
                    violation_type=ViolationType.SESSION,
                    rule_name="session_overlap",
                    description=f"複数セッション重複時間でのトレード",
                    expected_value="単一セッション",
                    actual_value=active_sessions,
                    penalty_points=1,
                    severity="low",
                    timestamp=datetime.now(timezone.utc)
                ))
            
        except Exception as e:
            self.logger.error(f"❌ セッション評価エラー: {e}")
        
        return violations

    async def _evaluate_correlation(
        self,
        trade: Trade,
        daily_trades: int
    ) -> List[Violation]:
        """相関の評価"""
        violations = []
        
        try:
            # 1. 日次トレード数上限チェック（5回）
            max_daily_trades = 5
            if daily_trades > max_daily_trades:
                violations.append(Violation(
                    violation_type=ViolationType.CORRELATION,
                    rule_name="max_daily_trades",
                    description=f"日次トレード数が上限を超過",
                    expected_value=f"<= {max_daily_trades}",
                    actual_value=daily_trades,
                    penalty_points=8,
                    severity="medium",
                    timestamp=datetime.now(timezone.utc)
                ))
            
            # 2. 同一通貨ペアの連続トレードチェック（仮の実装）
            # 実際の実装では、過去のトレード履歴を参照する必要がある
            
        except Exception as e:
            self.logger.error(f"❌ 相関評価エラー: {e}")
        
        return violations

    async def _evaluate_hold_time(
        self,
        trade: Trade,
        exit_snapshot: Optional[MarketSnapshot]
    ) -> List[Violation]:
        """保有時間の評価"""
        violations = []
        
        try:
            if trade.hold_time_minutes is not None:
                # 1. 最小保有時間チェック（5分）
                min_hold_time = 5
                if trade.hold_time_minutes < min_hold_time:
                    violations.append(Violation(
                        violation_type=ViolationType.HOLD_TIME,
                        rule_name="min_hold_time",
                        description=f"保有時間が最小値を下回る",
                        expected_value=f">= {min_hold_time}分",
                        actual_value=f"{trade.hold_time_minutes}分",
                        penalty_points=5,
                        severity="medium",
                        timestamp=datetime.now(timezone.utc)
                    ))
                
                # 2. 最大保有時間チェック（240分）
                max_hold_time = 240
                if trade.hold_time_minutes > max_hold_time:
                    violations.append(Violation(
                        violation_type=ViolationType.HOLD_TIME,
                        rule_name="max_hold_time",
                        description=f"保有時間が最大値を超過",
                        expected_value=f"<= {max_hold_time}分",
                        actual_value=f"{trade.hold_time_minutes}分",
                        penalty_points=10,
                        severity="high",
                        timestamp=datetime.now(timezone.utc)
                    ))
            
        except Exception as e:
            self.logger.error(f"❌ 保有時間評価エラー: {e}")
        
        return violations

    def _calculate_score(self, violations: List[Violation]) -> AdherenceScore:
        """スコア計算"""
        # 初期スコア（100点満点）
        total_score = 100
        max_score = 100
        
        # 違反による減点計算
        for violation in violations:
            total_score -= violation.penalty_points
        
        # スコアを0以上に制限
        total_score = max(0, total_score)
        
        # 違反の分類
        critical_violations = len([v for v in violations if v.severity == "critical"])
        high_violations = len([v for v in violations if v.severity == "high"])
        medium_violations = len([v for v in violations if v.severity == "medium"])
        low_violations = len([v for v in violations if v.severity == "low"])
        
        # カテゴリ別スコア計算（簡易実装）
        category_scores = {}
        for category in self.score_weights.keys():
            category_violations = [v for v in violations if v.violation_type.value == category]
            category_penalty = sum(v.penalty_points for v in category_violations)
            category_scores[f"{category}_score"] = max(0, self.score_weights[category] - category_penalty)
        
        return AdherenceScore(
            total_score=total_score,
            max_score=max_score,
            violations=violations,
            violation_count=len(violations),
            critical_violations=critical_violations,
            high_violations=high_violations,
            medium_violations=medium_violations,
            low_violations=low_violations,
            risk_management_score=category_scores.get("risk_management_score", self.score_weights["risk_management"]),
            timing_score=category_scores.get("timing_score", self.score_weights["timing"]),
            position_sizing_score=category_scores.get("position_sizing_score", self.score_weights["position_sizing"]),
            rule_logic_score=category_scores.get("rule_logic_score", self.score_weights["rule_logic"]),
            session_score=category_scores.get("session_score", self.score_weights["session"]),
            correlation_score=category_scores.get("correlation_score", self.score_weights["correlation"]),
            hold_time_score=category_scores.get("hold_time_score", self.score_weights["hold_time"]),
            evaluation_timestamp=datetime.now(timezone.utc),
            trade_id="",  # 後で設定
            evaluator_version="1.0"
        )

    async def get_adherence_summary(
        self,
        trade_snapshots: List[TradeSnapshot],
        days: int = 30
    ) -> Dict[str, Any]:
        """
        遵守度サマリーの取得
        
        Args:
            trade_snapshots: トレードスナップショットのリスト
            days: 分析期間（日数）
        
        Returns:
            遵守度サマリー
        """
        if self._lock is None:
            self._lock = asyncio.Lock()
        
        async with self._lock:
            try:
                # 期間フィルタリング
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                recent_trades = [
                    ts for ts in trade_snapshots
                    if ts.entry_time and ts.entry_time >= cutoff_date
                ]
                
                if not recent_trades:
                    return {
                        "total_trades": 0,
                        "analysis": "No trades found in the specified period"
                    }
                
                # 基本統計
                total_trades = len(recent_trades)
                trades_with_scores = [ts for ts in recent_trades if ts.adherence_score is not None]
                
                if not trades_with_scores:
                    return {
                        "total_trades": total_trades,
                        "analysis": "No adherence scores available"
                    }
                
                # スコア統計
                scores = [ts.adherence_score for ts in trades_with_scores if ts.adherence_score is not None]
                if not scores:
                    return {
                        "total_trades": total_trades,
                        "analysis": "No valid adherence scores available"
                    }
                
                avg_score = sum(scores) / len(scores)
                min_score = min(scores)
                max_score = max(scores)
                
                # スコア分布
                score_distribution = {
                    "excellent": len([s for s in scores if s >= 90]),  # 90点以上
                    "good": len([s for s in scores if 80 <= s < 90]),   # 80-89点
                    "fair": len([s for s in scores if 70 <= s < 80]),   # 70-79点
                    "poor": len([s for s in scores if s < 70])          # 70点未満
                }
                
                # 違反統計
                all_violations = []
                for ts in trades_with_scores:
                    # 違反情報はTradeSnapshotに含まれていると仮定
                    if hasattr(ts, 'violation_tags'):
                        all_violations.extend(ts.violation_tags)
                
                violation_counts = {}
                for violation in all_violations:
                    violation_counts[violation] = violation_counts.get(violation, 0) + 1
                
                # 戦略別分析
                strategy_analysis = {}
                for ts in trades_with_scores:
                    strategy = ts.strategy
                    if strategy not in strategy_analysis:
                        strategy_analysis[strategy] = {
                            "trades": 0,
                            "avg_score": 0,
                            "scores": []
                        }
                    
                    analysis = strategy_analysis[strategy]
                    analysis["trades"] += 1
                    analysis["scores"].append(ts.adherence_score)
                
                # 戦略別平均スコア計算
                for strategy, analysis in strategy_analysis.items():
                    if analysis["scores"]:
                        analysis["avg_score"] = sum(analysis["scores"]) / len(analysis["scores"])
                
                return {
                    "total_trades": total_trades,
                    "trades_with_scores": len(trades_with_scores),
                    "score_statistics": {
                        "average": avg_score,
                        "minimum": min_score,
                        "maximum": max_score
                    },
                    "score_distribution": score_distribution,
                    "violation_summary": violation_counts,
                    "strategy_analysis": strategy_analysis,
                    "period_days": days,
                    "analysis_timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as e:
                self.logger.error(f"❌ 遵守度サマリー取得エラー: {e}")
                return {
                    "total_trades": 0,
                    "analysis": f"Error: {e}"
                }

    def to_dict(self) -> Dict[str, Any]:
        """遵守度評価器の状態を辞書に変換"""
        return {
            "score_weights": self.score_weights,
            "penalty_weights": self.penalty_weights,
            "evaluator_version": "1.0"
        }

    def from_dict(self, data: Dict[str, Any]) -> None:
        """辞書から遵守度評価器の状態を復元"""
        self.score_weights = data.get("score_weights", self.score_weights)
        self.penalty_weights = data.get("penalty_weights", self.penalty_weights)

    async def close(self):
        """リソースのクリーンアップ"""
        self.logger.info("AdherenceEvaluator closed")


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    from .scenario_manager import ScenarioManager, TradeDirection
    from .rule_engine import EntrySignal, RuleResult
    from .snapshot_manager import SnapshotManager
    
    evaluator = AdherenceEvaluator()
    scenario_manager = ScenarioManager()
    snapshot_manager = SnapshotManager()
    
    try:
        print("🧪 ルール遵守判定システムテスト...")
        
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
            entry_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
            entry_snapshot = entry_snapshots[0] if entry_snapshots else None
        else:
            entry_snapshot = None
        
        # エグジットの実行
        await scenario_manager.exit_scenario(scenario.id, 147.400, ExitReason.TP1_HIT)
        
        # エグジットスナップの保存
        if trade is not None:
            exit_snapshot_id = await snapshot_manager.save_exit_snapshot(trade, ExitReason.TP1_HIT)
            exit_snapshots = await snapshot_manager.get_snapshots_by_trade(trade.id)
            exit_snapshot = exit_snapshots[-1] if len(exit_snapshots) > 1 else None
        else:
            exit_snapshot = None
        
        # 遵守度評価
        if entry_snapshot and trade is not None:
            score = await evaluator.evaluate_trade_adherence(
                trade, entry_snapshot, exit_snapshot, daily_trades=1, daily_risk_percent=0.5
            )
            
            print(f"✅ 遵守度評価完了:")
            print(f"   総合スコア: {score.total_score}/100")
            print(f"   違反数: {score.violation_count}")
            print(f"   重大違反: {score.critical_violations}")
            print(f"   高違反: {score.high_violations}")
            print(f"   中違反: {score.medium_violations}")
            print(f"   低違反: {score.low_violations}")
            
            # 違反詳細
            for violation in score.violations:
                print(f"   - {violation.violation_type.value}: {violation.description} ({violation.penalty_points}点減点)")
        
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
