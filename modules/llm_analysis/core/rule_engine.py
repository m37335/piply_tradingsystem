"""
ルールベース判定エンジン

数値ベースの厳格な売買条件判定を行う。
ルールベース中心のシステムで、LLMは補助的役割に限定。
"""

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import yaml
except ImportError:
    import PyYAML as yaml

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import numpy as np
except ImportError:
    np = None

from .data_preparator import LLMDataPreparator


class RuleStatus(Enum):
    """ルールステータス"""
    ENABLED = "enabled"
    DISABLED = "disabled"
    TESTING = "testing"


class TradeDirection(Enum):
    """トレード方向"""
    BUY = "buy"
    SELL = "sell"


class SessionType(Enum):
    """セッションタイプ"""
    TOKYO = "Tokyo"
    LONDON = "London"
    NEW_YORK = "NewYork"


@dataclass
class RuleCondition:
    """ルール条件"""
    name: str
    expression: str
    weight: float = 1.0
    required: bool = True


@dataclass
class RuleResult:
    """ルール判定結果"""
    rule_name: str
    passed: bool
    score: float
    message: str
    details: Dict[str, Any]
    required: bool = True
    weight: float = 1.0


@dataclass
class EntrySignal:
    """エントリーシグナル"""
    direction: TradeDirection
    strategy: str
    confidence: float
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    risk_reward_ratio: float
    max_hold_time: int  # 分
    rule_results: List[RuleResult]
    technical_summary: Dict[str, Any]
    created_at: datetime


class RuleBasedEngine:
    """ルールベース判定エンジン"""

    def __init__(self, config_path: Optional[str] = None):
        """初期化"""
        self.logger = logging.getLogger(__name__)
        self.data_preparator = LLMDataPreparator()
        
        # 設定ファイルの読み込み
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'rules.yaml')
        
        self.rules_config = self._load_rules_config(config_path)
        self.risk_constraints = self._load_risk_constraints()
        
        # セッション時間の定義（JST基準）
        self.session_times = {
            SessionType.TOKYO: {"start": "09:00", "end": "15:00"},
            SessionType.LONDON: {"start": "16:00", "end": "23:59"},
            SessionType.NEW_YORK: {"start": "22:00", "end": "05:59"}
        }
        
        # 初期化フラグ
        self._initialized = False

    async def initialize(self):
        """非同期初期化"""
        if not self._initialized:
            await self.data_preparator.initialize()
            self._initialized = True
            self.logger.info("✅ ルールベース判定エンジン初期化完了")

    def _load_rules_config(self, config_path: str) -> Dict:
        """ルール設定の読み込み"""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            else:
                # デフォルト設定
                return self._get_default_rules_config()
        except Exception as e:
            self.logger.error(f"❌ ルール設定読み込みエラー: {e}")
            return self._get_default_rules_config()

    def _get_default_rules_config(self) -> Dict:
        """デフォルトルール設定"""
        return {
            "active_rules": [
                {
                    "name": "pullback_buy",
                    "enabled": True,
                    "description": "押し目買い",
                    "conditions": [
                        "RSI_14 <= 40",
                        "price > EMA_200",
                        "MACD > MACD_Signal",
                        "price BETWEEN Fib_0.382 AND Fib_0.618",
                        "active_session = Tokyo OR London",
                        "daily_trades < 5",
                        "daily_risk < 3%"
                    ]
                },
                {
                    "name": "breakout_buy",
                    "enabled": False,
                    "description": "ブレイクアウト買い",
                    "conditions": [
                        "price > EMA_21",
                        "RSI_14 > 50",
                        "MACD > 0",
                        "price > Fib_1.272",
                        "Volume_Ratio > 1.5",
                        "active_session = London OR NewYork",
                        "daily_trades < 5",
                        "daily_risk < 3%"
                    ]
                },
                {
                    "name": "reversal_sell",
                    "enabled": True,
                    "description": "逆張り売り",
                    "conditions": [
                        "RSI_14 >= 70",
                        "price < EMA_200",
                        "MACD < MACD_Signal",
                        "price BETWEEN Fib_0.618 AND Fib_0.786",
                        "active_session = Tokyo OR London",
                        "daily_trades < 5",
                        "daily_risk < 3%"
                    ]
                },
                {
                    "name": "trend_follow_sell",
                    "enabled": True,
                    "description": "下降トレンドフォロー売り",
                    "conditions": [
                        "price < EMA_200",
                        "EMA_21 < EMA_55",
                        "MACD < 0",
                        "RSI_14 < 50",
                        "price < Fib_0.5",
                        "active_session = Tokyo OR London OR NewYork",
                        "daily_trades < 5",
                        "daily_risk < 3%"
                    ]
                }
            ],
            "exit_rules": {
                "profit_targets": {
                    "tp1": {
                        "condition": "price >= entry_price + (ATR * 1.5)",
                        "action": "close_50_percent"
                    },
                    "tp2": {
                        "condition": "price >= entry_price + (ATR * 2.5)",
                        "action": "close_30_percent"
                    },
                    "tp3": {
                        "condition": "price >= entry_price + (ATR * 4.0)",
                        "action": "close_remaining"
                    }
                },
                "stop_loss": {
                    "sl": {
                        "condition": "price <= entry_price - (ATR * 1.0)",
                        "action": "close_all"
                    }
                },
                "time_based": {
                    "max_hold": {
                        "condition": "hold_time >= 240 minutes",
                        "action": "close_all"
                    },
                    "min_hold": {
                        "condition": "hold_time >= 30 minutes",
                        "action": "allow_exit"
                    }
                }
            },
            "parameters": {
                "rsi_oversold": 40,
                "rsi_overbought": 70,
                "atr_stop_loss": 1.0,
                "atr_take_profit_1": 1.5,
                "atr_take_profit_2": 2.5,
                "atr_take_profit_3": 4.0,
                "ema_short": 21,
                "ema_medium": 55,
                "ema_long": 200
            }
        }

    def _load_risk_constraints(self) -> Dict:
        """リスク制約の読み込み"""
        return {
            "max_risk_per_trade": 1.0,  # %
            "max_risk_per_day": 3.0,    # %
            "max_trades_per_day": 5,
            "max_hold_time_minutes": 240,
            "min_hold_time_minutes": 30,
            "correlation_threshold": 0.7
        }

    async def evaluate_entry_conditions(
        self,
        symbol: str = 'USDJPY=X',
        analysis_type: str = 'trend_direction'
    ) -> List[EntrySignal]:
        """
        エントリー条件の評価
        
        Args:
            symbol: 通貨ペアシンボル
            analysis_type: 分析タイプ
        
        Returns:
            エントリーシグナルのリスト
        """
        # 初期化チェック
        if not self._initialized:
            await self.initialize()
        
        self.logger.info(f"🔍 エントリー条件評価開始: {symbol} ({analysis_type})")
        
        try:
            # データの準備
            data = await self.data_preparator.prepare_analysis_data(analysis_type, symbol)
            
            if not data['timeframes']:
                self.logger.warning("⚠️ 利用可能なデータがありません")
                return []
            
            # アクティブルールの評価
            signals = []
            for rule_config in self.rules_config['active_rules']:
                if not rule_config.get('enabled', False):
                    continue
                
                signal = await self._evaluate_rule(rule_config, data, symbol)
                if signal:
                    signals.append(signal)
            
            self.logger.info(f"✅ エントリー条件評価完了: {len(signals)}個のシグナル")
            return signals
            
        except Exception as e:
            self.logger.error(f"❌ エントリー条件評価エラー: {e}")
            return []

    async def _evaluate_rule(
        self,
        rule_config: Dict,
        data: Dict,
        symbol: str
    ) -> Optional[EntrySignal]:
        """
        個別ルールの評価
        
        Args:
            rule_config: ルール設定
            data: 分析データ
            symbol: 通貨ペアシンボル
        
        Returns:
            エントリーシグナル（条件を満たす場合）
        """
        rule_name = rule_config['name']
        self.logger.info(f"📋 ルール評価: {rule_name}")
        
        try:
            # ルール条件の評価
            rule_results = []
            all_passed = True
            total_score = 0.0
            total_weight = 0.0
            
            for condition_str in rule_config['conditions']:
                result = self._evaluate_condition(condition_str, data, symbol)
                rule_results.append(result)
                
                if result.required and not result.passed:
                    all_passed = False
                
                total_score += result.score * result.weight
                total_weight += result.weight
            
            # 総合スコアの計算
            overall_score = total_score / total_weight if total_weight > 0 else 0.0
            
            # リスク制約のチェック
            risk_check = self._check_risk_constraints(data, symbol)
            if not risk_check['passed']:
                self.logger.info(f"❌ リスク制約違反: {risk_check['reason']}")
                return None
            
            # 条件を満たす場合、エントリーシグナルを生成
            if all_passed and overall_score >= 0.7:  # 70%以上のスコア
                signal = self._generate_entry_signal(
                    rule_config, data, rule_results, overall_score, symbol
                )
                self.logger.info(f"✅ シグナル生成: {rule_name} (信頼度: {overall_score:.2f})")
                return signal
            else:
                self.logger.info(f"❌ 条件未満: {rule_name} (スコア: {overall_score:.2f})")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ ルール評価エラー ({rule_name}): {e}")
            return None

    def _evaluate_condition(
        self,
        condition_str: str,
        data: Dict,
        symbol: str
    ) -> RuleResult:
        """
        個別条件の評価
        
        Args:
            condition_str: 条件文字列
            data: 分析データ
            symbol: 通貨ペアシンボル
        
        Returns:
            ルール結果
        """
        try:
            # 条件の解析と評価
            if "RSI_14" in condition_str:
                return self._evaluate_rsi_condition(condition_str, data)
            elif "EMA" in condition_str:
                return self._evaluate_ema_condition(condition_str, data)
            elif "MACD" in condition_str:
                return self._evaluate_macd_condition(condition_str, data)
            elif "Fib_" in condition_str:
                return self._evaluate_fibonacci_condition(condition_str, data)
            elif "active_session" in condition_str:
                return self._evaluate_session_condition(condition_str)
            elif "daily_trades" in condition_str or "daily_risk" in condition_str:
                return self._evaluate_risk_condition(condition_str, data)
            elif "Volume_Ratio" in condition_str:
                return self._evaluate_volume_condition(condition_str, data)
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown condition",
                    details={}
                )
                
        except Exception as e:
            self.logger.error(f"❌ 条件評価エラー ({condition_str}): {e}")
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"Evaluation error: {e}",
                details={}
            )

    def _evaluate_rsi_condition(self, condition_str: str, data: Dict) -> RuleResult:
        """RSI条件の評価"""
        try:
            # 最新のRSI値を取得
            rsi_value = None
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame) and 'RSI_14' in df.columns:
                    rsi_value = df['RSI_14'].iloc[-1]
                    break
            
            if rsi_value is None or pd.isna(rsi_value):
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="RSI_14 data not available",
                    details={"rsi_value": None}
                )
            
            # 条件の解析
            if "RSI_14 <= 40" in condition_str:
                passed = rsi_value <= 40
                score = max(0.0, 1.0 - (rsi_value - 40) / 40) if rsi_value > 40 else 1.0
                message = f"RSI_14: {rsi_value:.2f} {'≤' if passed else '>'} 40"
            elif "RSI_14 >= 70" in condition_str:
                passed = rsi_value >= 70
                score = max(0.0, 1.0 - (70 - rsi_value) / 30) if rsi_value < 70 else 1.0
                message = f"RSI_14: {rsi_value:.2f} {'≥' if passed else '<'} 70"
            elif "RSI_14 > 50" in condition_str:
                passed = rsi_value > 50
                score = max(0.0, (rsi_value - 50) / 50) if rsi_value > 50 else 0.0
                message = f"RSI_14: {rsi_value:.2f} {'>' if passed else '≤'} 50"
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown RSI condition",
                    details={"rsi_value": rsi_value}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"rsi_value": rsi_value}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"RSI evaluation error: {e}",
                details={}
            )

    def _evaluate_ema_condition(self, condition_str: str, data: Dict) -> RuleResult:
        """EMA条件の評価"""
        try:
            # 最新の価格とEMA値を取得
            current_price = None
            ema_value = None
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame) and 'close' in df.columns:
                    current_price = df['close'].iloc[-1]
                    
                    if "EMA_200" in condition_str and 'EMA_200' in df.columns:
                        ema_value = df['EMA_200'].iloc[-1]
                    elif "EMA_21" in condition_str and 'EMA_21' in df.columns:
                        ema_value = df['EMA_21'].iloc[-1]
                    
                    if current_price is not None and ema_value is not None:
                        break
            
            if current_price is None or ema_value is None or pd.isna(ema_value):
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="EMA data not available",
                    details={"current_price": current_price, "ema_value": ema_value}
                )
            
            # 条件の解析
            if "price > EMA_200" in condition_str:
                passed = current_price > ema_value
                # スコアを0-1の範囲に正規化（価格差の割合を制限）
                price_diff_ratio = (current_price - ema_value) / ema_value
                score = min(1.0, max(0.0, price_diff_ratio * 10)) if current_price > ema_value else 0.0
                message = f"Price: {current_price:.5f} {'>' if passed else '≤'} EMA_200: {ema_value:.5f}"
            elif "price < EMA_200" in condition_str:
                passed = current_price < ema_value
                # スコアを0-1の範囲に正規化（価格差の割合を制限）
                price_diff_ratio = (ema_value - current_price) / ema_value
                score = min(1.0, max(0.0, price_diff_ratio * 10)) if current_price < ema_value else 0.0
                message = f"Price: {current_price:.5f} {'<' if passed else '≥'} EMA_200: {ema_value:.5f}"
            elif "price > EMA_21" in condition_str:
                passed = current_price > ema_value
                # スコアを0-1の範囲に正規化（価格差の割合を制限）
                price_diff_ratio = (current_price - ema_value) / ema_value
                score = min(1.0, max(0.0, price_diff_ratio * 10)) if current_price > ema_value else 0.0
                message = f"Price: {current_price:.5f} {'>' if passed else '≤'} EMA_21: {ema_value:.5f}"
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown EMA condition",
                    details={"current_price": current_price, "ema_value": ema_value}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"current_price": current_price, "ema_value": ema_value}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"EMA evaluation error: {e}",
                details={}
            )

    def _evaluate_macd_condition(self, condition_str: str, data: Dict) -> RuleResult:
        """MACD条件の評価"""
        try:
            # 最新のMACD値を取得
            macd_value = None
            macd_signal = None
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame):
                    if 'MACD' in df.columns:
                        macd_value = df['MACD'].iloc[-1]
                    if 'MACD_Signal' in df.columns:
                        macd_signal = df['MACD_Signal'].iloc[-1]
                
                if macd_value is not None and macd_signal is not None:
                    break
            
            if macd_value is None or pd.isna(macd_value):
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="MACD data not available",
                    details={"macd_value": macd_value, "macd_signal": macd_signal}
                )
            
            # 条件の解析
            if "MACD > MACD_Signal" in condition_str:
                if macd_signal is None or pd.isna(macd_signal):
                    return RuleResult(
                        rule_name=condition_str,
                        passed=False,
                        score=0.0,
                        message="MACD_Signal data not available",
                        details={"macd_value": macd_value, "macd_signal": macd_signal}
                    )
                
                passed = macd_value > macd_signal
                # スコアを0-1の範囲に正規化（MACD差の割合を制限）
                macd_diff_ratio = (macd_value - macd_signal) / abs(macd_signal) if macd_signal != 0 else 0
                score = min(1.0, max(0.0, macd_diff_ratio * 5)) if macd_value > macd_signal else 0.0
                message = f"MACD: {macd_value:.6f} {'>' if passed else '≤'} Signal: {macd_signal:.6f}"
            elif "MACD < MACD_Signal" in condition_str:
                if macd_signal is None or pd.isna(macd_signal):
                    return RuleResult(
                        rule_name=condition_str,
                        passed=False,
                        score=0.0,
                        message="MACD_Signal data not available",
                        details={"macd_value": macd_value, "macd_signal": macd_signal}
                    )
                
                passed = macd_value < macd_signal
                # スコアを0-1の範囲に正規化（MACD差の割合を制限）
                macd_diff_ratio = (macd_signal - macd_value) / abs(macd_signal) if macd_signal != 0 else 0
                score = min(1.0, max(0.0, macd_diff_ratio * 5)) if macd_value < macd_signal else 0.0
                message = f"MACD: {macd_value:.6f} {'<' if passed else '≥'} Signal: {macd_signal:.6f}"
            elif "MACD > 0" in condition_str:
                passed = macd_value > 0
                # スコアを0-1の範囲に正規化（MACD値を制限）
                score = min(1.0, max(0.0, macd_value * 100)) if macd_value > 0 else 0.0
                message = f"MACD: {macd_value:.6f} {'>' if passed else '≤'} 0"
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown MACD condition",
                    details={"macd_value": macd_value, "macd_signal": macd_signal}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"macd_value": macd_value, "macd_signal": macd_signal}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"MACD evaluation error: {e}",
                details={}
            )

    def _evaluate_fibonacci_condition(self, condition_str: str, data: Dict) -> RuleResult:
        """フィボナッチ条件の評価"""
        try:
            # 最新の価格とフィボナッチレベルを取得
            current_price = None
            fib_levels = {}
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame) and 'close' in df.columns:
                    current_price = df['close'].iloc[-1]
                
                    # フィボナッチレベルの取得
                    for col in df.columns:
                        if col.startswith('Fib_'):
                            level = col.replace('Fib_', '')
                            try:
                                fib_levels[level] = df[col].iloc[-1]
                            except:
                                continue
                
                if current_price is not None and fib_levels:
                    break
            
            if current_price is None or not fib_levels:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Fibonacci data not available",
                    details={"current_price": current_price, "fib_levels": fib_levels}
                )
            
            # 条件の解析
            if "price BETWEEN Fib_0.382 AND Fib_0.618" in condition_str:
                fib_382 = fib_levels.get('0.382')
                fib_618 = fib_levels.get('0.618')
                
                if fib_382 is None or fib_618 is None or pd.isna(fib_382) or pd.isna(fib_618):
                    return RuleResult(
                        rule_name=condition_str,
                        passed=False,
                        score=0.0,
                        message="Required Fibonacci levels not available",
                        details={"current_price": current_price, "fib_levels": fib_levels}
                    )
                
                passed = fib_382 <= current_price <= fib_618
                if passed:
                    # 中央値からの距離でスコア計算
                    center = (fib_382 + fib_618) / 2
                    distance = abs(current_price - center)
                    max_distance = (fib_618 - fib_382) / 2
                    score = max(0.0, 1.0 - distance / max_distance)
                else:
                    score = 0.0
                
                message = f"Price: {current_price:.5f} {'∈' if passed else '∉'} [Fib_0.382: {fib_382:.5f}, Fib_0.618: {fib_618:.5f}]"
                
            elif "price > Fib_1.272" in condition_str:
                fib_1272 = fib_levels.get('1.272')
                
                if fib_1272 is None or pd.isna(fib_1272):
                    return RuleResult(
                        rule_name=condition_str,
                        passed=False,
                        score=0.0,
                        message="Fib_1.272 not available",
                        details={"current_price": current_price, "fib_levels": fib_levels}
                    )
                
                passed = current_price > fib_1272
                score = max(0.0, (current_price - fib_1272) / fib_1272 * 100) if current_price > fib_1272 else 0.0
                message = f"Price: {current_price:.5f} {'>' if passed else '≤'} Fib_1.272: {fib_1272:.5f}"
                
            elif "price BETWEEN Fib_0.618 AND Fib_0.786" in condition_str:
                fib_618 = fib_levels.get('0.618')
                fib_786 = fib_levels.get('0.786')
                
                if fib_618 is None or fib_786 is None or pd.isna(fib_618) or pd.isna(fib_786):
                    return RuleResult(
                        rule_name=condition_str,
                        passed=False,
                        score=0.0,
                        message="Required Fibonacci levels not available",
                        details={"current_price": current_price, "fib_levels": fib_levels}
                    )
                
                passed = fib_618 <= current_price <= fib_786
                if passed:
                    # 中央値からの距離でスコア計算
                    center = (fib_618 + fib_786) / 2
                    distance = abs(current_price - center)
                    max_distance = (fib_786 - fib_618) / 2
                    score = max(0.0, 1.0 - distance / max_distance)
                else:
                    score = 0.0
                
                message = f"Price: {current_price:.5f} {'∈' if passed else '∉'} [Fib_0.618: {fib_618:.5f}, Fib_0.786: {fib_786:.5f}]"
                
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown Fibonacci condition",
                    details={"current_price": current_price, "fib_levels": fib_levels}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"current_price": current_price, "fib_levels": fib_levels}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"Fibonacci evaluation error: {e}",
                details={}
            )

    def _evaluate_session_condition(self, condition_str: str) -> RuleResult:
        """セッション条件の評価"""
        try:
            # 現在時刻の取得（JST）
            now_jst = datetime.now(timezone(timedelta(hours=9)))
            current_time = now_jst.time()
            
            # アクティブセッションの判定
            active_sessions = []
            
            for session_type, times in self.session_times.items():
                start_time = datetime.strptime(times["start"], "%H:%M").time()
                end_time = datetime.strptime(times["end"], "%H:%M").time()
                
                if start_time <= end_time:
                    # 同日内のセッション
                    if start_time <= current_time <= end_time:
                        active_sessions.append(session_type.value)
                else:
                    # 日をまたぐセッション（ニューヨーク）
                    if current_time >= start_time or current_time <= end_time:
                        active_sessions.append(session_type.value)
            
            # 条件の解析
            if "active_session = Tokyo OR London" in condition_str:
                required_sessions = ["Tokyo", "London"]
                passed = any(session in active_sessions for session in required_sessions)
                score = 1.0 if passed else 0.0
                message = f"Active sessions: {active_sessions} {'⊃' if passed else '⊅'} {required_sessions}"
                
            elif "active_session = London OR NewYork" in condition_str:
                required_sessions = ["London", "NewYork"]
                passed = any(session in active_sessions for session in required_sessions)
                score = 1.0 if passed else 0.0
                message = f"Active sessions: {active_sessions} {'⊃' if passed else '⊅'} {required_sessions}"
                
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown session condition",
                    details={"active_sessions": active_sessions}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"active_sessions": active_sessions, "current_time": current_time}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"Session evaluation error: {e}",
                details={}
            )

    def _evaluate_risk_condition(self, condition_str: str, data: Dict) -> RuleResult:
        """リスク条件の評価"""
        try:
            # 現在のリスク状況を取得（簡易実装）
            # 実際の実装では、データベースから日次統計を取得
            
            if "daily_trades < 5" in condition_str:
                # 仮の値（実際はデータベースから取得）
                daily_trades = 2  # 例
                passed = daily_trades < 5
                score = max(0.0, 1.0 - daily_trades / 5) if daily_trades < 5 else 0.0
                message = f"Daily trades: {daily_trades} {'<' if passed else '≥'} 5"
                
            elif "daily_risk < 3%" in condition_str:
                # 仮の値（実際はデータベースから取得）
                daily_risk = 1.2  # %
                passed = daily_risk < 3.0
                score = max(0.0, 1.0 - daily_risk / 3.0) if daily_risk < 3.0 else 0.0
                message = f"Daily risk: {daily_risk}% {'<' if passed else '≥'} 3%"
                
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown risk condition",
                    details={}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"daily_trades": daily_trades if "daily_trades" in condition_str else None,
                        "daily_risk": daily_risk if "daily_risk" in condition_str else None}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"Risk evaluation error: {e}",
                details={}
            )

    def _evaluate_volume_condition(self, condition_str: str, data: Dict) -> RuleResult:
        """ボリューム条件の評価"""
        try:
            # 最新のボリューム比率を取得
            volume_ratio = None
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame) and 'Volume_Ratio' in df.columns:
                    volume_ratio = df['Volume_Ratio'].iloc[-1]
                    break
            
            if volume_ratio is None or pd.isna(volume_ratio):
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Volume_Ratio data not available",
                    details={"volume_ratio": volume_ratio}
                )
            
            # 条件の解析
            if "Volume_Ratio > 1.5" in condition_str:
                passed = volume_ratio > 1.5
                score = max(0.0, (volume_ratio - 1.5) / 1.5) if volume_ratio > 1.5 else 0.0
                message = f"Volume_Ratio: {volume_ratio:.2f} {'>' if passed else '≤'} 1.5"
                
            else:
                return RuleResult(
                    rule_name=condition_str,
                    passed=False,
                    score=0.0,
                    message="Unknown volume condition",
                    details={"volume_ratio": volume_ratio}
                )
            
            return RuleResult(
                rule_name=condition_str,
                passed=passed,
                score=score,
                message=message,
                details={"volume_ratio": volume_ratio}
            )
            
        except Exception as e:
            return RuleResult(
                rule_name=condition_str,
                passed=False,
                score=0.0,
                message=f"Volume evaluation error: {e}",
                details={}
            )

    def _check_risk_constraints(self, data: Dict, symbol: str) -> Dict:
        """リスク制約のチェック"""
        try:
            # 簡易実装（実際はデータベースから取得）
            constraints_check = {
                "passed": True,
                "reason": None,
                "details": {}
            }
            
            # 日次トレード数チェック
            daily_trades = 2  # 仮の値
            if daily_trades >= self.risk_constraints["max_trades_per_day"]:
                constraints_check["passed"] = False
                constraints_check["reason"] = f"Daily trades limit exceeded: {daily_trades}/{self.risk_constraints['max_trades_per_day']}"
                return constraints_check
            
            # 日次リスクチェック
            daily_risk = 1.2  # 仮の値
            if daily_risk >= self.risk_constraints["max_risk_per_day"]:
                constraints_check["passed"] = False
                constraints_check["reason"] = f"Daily risk limit exceeded: {daily_risk}%/{self.risk_constraints['max_risk_per_day']}%"
                return constraints_check
            
            constraints_check["details"] = {
                "daily_trades": daily_trades,
                "daily_risk": daily_risk,
                "max_trades_per_day": self.risk_constraints["max_trades_per_day"],
                "max_risk_per_day": self.risk_constraints["max_risk_per_day"]
            }
            
            return constraints_check
            
        except Exception as e:
            return {
                "passed": False,
                "reason": f"Risk constraint check error: {e}",
                "details": {}
            }

    def _generate_entry_signal(
        self,
        rule_config: Dict,
        data: Dict,
        rule_results: List[RuleResult],
        confidence: float,
        symbol: str
    ) -> EntrySignal:
        """
        エントリーシグナルの生成
        
        Args:
            rule_config: ルール設定
            data: 分析データ
            rule_results: ルール結果
            confidence: 信頼度
            symbol: 通貨ペアシンボル
        
        Returns:
            エントリーシグナル
        """
        try:
            # 最新価格の取得
            current_price = None
            atr_value = None
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame):
                    if 'close' in df.columns:
                        current_price = df['close'].iloc[-1]
                    if 'ATR_14' in df.columns:
                        atr_value = df['ATR_14'].iloc[-1]
                
                if current_price is not None and atr_value is not None:
                    break
            
            if current_price is None or atr_value is None:
                raise ValueError("Required price data not available")
            
            # トレード方向の決定
            if "buy" in rule_config['name']:
                direction = TradeDirection.BUY
            elif "sell" in rule_config['name']:
                direction = TradeDirection.SELL
            else:
                direction = TradeDirection.BUY  # デフォルト
            
            # リスク管理パラメータの取得
            params = self.rules_config['parameters']
            
            # ストップロスとテイクプロフィットの計算
            if direction == TradeDirection.BUY:
                stop_loss = current_price - (atr_value * params['atr_stop_loss'])
                take_profit_1 = current_price + (atr_value * params['atr_take_profit_1'])
                take_profit_2 = current_price + (atr_value * params['atr_take_profit_2'])
                take_profit_3 = current_price + (atr_value * params['atr_take_profit_3'])
            else:
                stop_loss = current_price + (atr_value * params['atr_stop_loss'])
                take_profit_1 = current_price - (atr_value * params['atr_take_profit_1'])
                take_profit_2 = current_price - (atr_value * params['atr_take_profit_2'])
                take_profit_3 = current_price - (atr_value * params['atr_take_profit_3'])
            
            # リスクリワード比の計算
            risk = abs(current_price - stop_loss)
            reward = abs(take_profit_1 - current_price)
            risk_reward_ratio = reward / risk if risk > 0 else 0.0
            
            # テクニカルサマリーの作成
            technical_summary = self._create_technical_summary(data)
            
            return EntrySignal(
                direction=direction,
                strategy=rule_config['name'],
                confidence=confidence,
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit_1=take_profit_1,
                take_profit_2=take_profit_2,
                take_profit_3=take_profit_3,
                risk_reward_ratio=risk_reward_ratio,
                max_hold_time=self.risk_constraints["max_hold_time_minutes"],
                rule_results=rule_results,
                technical_summary=technical_summary,
                created_at=datetime.now(timezone.utc)
            )
            
        except Exception as e:
            self.logger.error(f"❌ エントリーシグナル生成エラー: {e}")
            raise

    def _create_technical_summary(self, data: Dict) -> Dict:
        """テクニカルサマリーの作成"""
        try:
            summary = {}
            
            for timeframe, tf_data in data['timeframes'].items():
                df = tf_data['data']
                if isinstance(df, pd.DataFrame):
                    latest = df.iloc[-1]
                    
                    timeframe_summary = {
                    "price": float(latest.get('close', 0)),
                    "rsi_14": float(latest.get('RSI_14', 0)) if not pd.isna(latest.get('RSI_14')) else None,
                    "ema_21": float(latest.get('EMA_21', 0)) if not pd.isna(latest.get('EMA_21')) else None,
                    "ema_200": float(latest.get('EMA_200', 0)) if not pd.isna(latest.get('EMA_200')) else None,
                    "macd": float(latest.get('MACD', 0)) if not pd.isna(latest.get('MACD')) else None,
                    "atr_14": float(latest.get('ATR_14', 0)) if not pd.isna(latest.get('ATR_14')) else None,
                    "volume_ratio": float(latest.get('Volume_Ratio', 0)) if not pd.isna(latest.get('Volume_Ratio')) else None
                }
                
                    # フィボナッチレベルの追加
                    fib_levels = {}
                    for col in df.columns:
                        if col.startswith('Fib_'):
                            level = col.replace('Fib_', '')
                            value = latest.get(col)
                            if not pd.isna(value):
                                fib_levels[level] = float(value)
                    
                    timeframe_summary["fibonacci_levels"] = fib_levels
                    summary[timeframe] = timeframe_summary
            
            return summary
            
        except Exception as e:
            self.logger.error(f"❌ テクニカルサマリー作成エラー: {e}")
            return {}

    async def close(self):
        """リソースのクリーンアップ"""
        await self.data_preparator.close()


# テスト用のメイン関数
async def main():
    """テスト用のメイン関数"""
    engine = RuleBasedEngine()
    
    try:
        # エントリー条件の評価
        print("🧪 ルールベース判定エンジンテスト...")
        signals = await engine.evaluate_entry_conditions()
        
        print(f"✅ 評価完了: {len(signals)}個のシグナル")
        
        for signal in signals:
            print(f"\n📊 シグナル: {signal.strategy}")
            print(f"   方向: {signal.direction.value}")
            print(f"   信頼度: {signal.confidence:.2f}")
            print(f"   エントリー価格: {signal.entry_price:.5f}")
            print(f"   ストップロス: {signal.stop_loss:.5f}")
            print(f"   テイクプロフィット1: {signal.take_profit_1:.5f}")
            print(f"   リスクリワード比: {signal.risk_reward_ratio:.2f}")
            print(f"   最大保有時間: {signal.max_hold_time}分")
            
            print("   ルール結果:")
            for result in signal.rule_results:
                status = "✅" if result.passed else "❌"
                print(f"     {status} {result.message} (スコア: {result.score:.2f})")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
